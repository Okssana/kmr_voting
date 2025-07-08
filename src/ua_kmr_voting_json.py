import json
import os
import sqlite3
import re
from datetime import datetime



def normalize_deputy_name(name):
    """
    Normalize deputy names by removing extra whitespace and standardizing format.
    Returns None for invalid names (like ". ...." or ". .. ..")
    """
    if not name or name == "":
        return None
        
    # Check for invalid patterns (ex-deputies)
    if re.match(r'^\.\s+\.+\s*$', name) or name.strip() in [". ....", ". .. .."]:
        return None
        
    # Remove all whitespace between initials
    # For example, "Ємець Л. О." becomes "Ємець Л.О."
    normalized = re.sub(r'(\w\.)\s+(\w\.)', r'\1\2', name)
    
    # Remove any double spaces
    normalized = re.sub(r'\s+', ' ', normalized)
    
    # Trim whitespace
    normalized = normalized.strip()
    
    return normalized

def initialize_db(db_path):
    """Initialize the SQLite database and create necessary tables"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create table for storing document data with deputy_id
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS documents (
        id TEXT PRIMARY KEY,
        file_name TEXT,
        GLTime TEXT,
        PD_NPP TEXT, 

        GL_Text TEXT,
        DocTime TEXT,
        DPName TEXT,
        DPName_normalized TEXT,
        DPGolos TEXT,
        RESULT TEXT,
        YESCnt TEXT,
        deputy_id INTEGER
    )
    ''')
    
    # Create table for deputy mapping
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS deputies (
        deputy_id INTEGER PRIMARY KEY,
        normalized_name TEXT UNIQUE,
        original_names TEXT,  
        first_appearance TEXT 
    )
    ''')
    
    conn.commit()
    return conn

def get_or_create_deputy_id(cursor, dp_name, pd_npp, file_name):
    """
    Get or create a deputy ID for the given name.
    Uses normalized names to handle whitespace variations.
    """
    normalized_name = normalize_deputy_name(dp_name)
    
    # If name is invalid or None after normalization, return None
    if normalized_name is None:
        return None
    
    # Try to get existing deputy ID
    cursor.execute("SELECT deputy_id, original_names FROM deputies WHERE normalized_name = ?", 
                  (normalized_name,))
    result = cursor.fetchone()
    
    if result:
        deputy_id, original_names = result
        
        # Check if this specific variation is already recorded
        original_names_list = original_names.split(',')
        if dp_name not in original_names_list:
            # Add this variation to the list
            original_names_list.append(dp_name)
            updated_names = ','.join(original_names_list)
            cursor.execute("UPDATE deputies SET original_names = ? WHERE deputy_id = ?", 
                         (updated_names, deputy_id))
        
        return deputy_id
    else:
        # Get all existing deputies
        cursor.execute("SELECT deputy_id FROM deputies ORDER BY deputy_id")
        existing_ids = [row[0] for row in cursor.fetchall()]
        
        # Find the next available ID in sequence
        next_id = 1
        while next_id in existing_ids:
            next_id += 1
        
        # Insert the new deputy
        cursor.execute(
            "INSERT INTO deputies (deputy_id, normalized_name, original_names, first_appearance) VALUES (?, ?, ?, ?)", 
            (next_id, normalized_name, dp_name, f"{pd_npp} ({file_name})")
        )
        
        return next_id

def store_data(doc_data, dp_list):
    """Store document data and DP list entries in the SQLite database"""
    # Establish connection to SQLite database
    db_conn = initialize_db('documents.db')
    cursor = db_conn.cursor()
    
    # Process and combine DPList entries with main document data
    combined_data = []
    
    pd_npp = doc_data.get('PD_NPP')
    file_name = doc_data.get('file_name')
    
    if dp_list:
        for dp_entry in dp_list:
            combined_entry = doc_data.copy()
            dp_name = dp_entry.get('DPName', '')
            dp_golos = 'Відсутній' if dp_entry.get('DPGolos') == '.........' else dp_entry.get('DPGolos', '')
            
            # Get normalized name
            normalized_name = normalize_deputy_name(dp_name)
            
            # Get or create deputy ID
            deputy_id = get_or_create_deputy_id(cursor, dp_name, pd_npp, file_name)
            
            # Generate a unique ID for this record
            record_id = f"{pd_npp}_{file_name}_{dp_name}".replace(" ", "_")
            
            combined_entry.update({
                'id': record_id,
                'DPName': dp_name,
                'DPName_normalized': normalized_name,
                'DPGolos': dp_golos,
                'deputy_id': deputy_id
            })
            combined_data.append(combined_entry)
    else:
        # If no DP list, just use the document data
        record_id = f"{pd_npp}_{file_name}_nodp"
        doc_data.update({
            'id': record_id,
            'DPName': '',
            'DPName_normalized': None,
            'DPGolos': '',
            'deputy_id': None
        })
        combined_data.append(doc_data)
    
    # Insert combined data into the documents table
    for entry in combined_data:
        # Convert None values to empty strings to avoid SQL issues
        for key, value in entry.items():
            if value is None:
                entry[key] = ""
        
        try:
            cursor.execute('''
            INSERT OR REPLACE INTO documents 
            (id, file_name, GLTime, PD_NPP,  GL_Text, RESULT, YESCnt, DocTime, DPName, 
             DPName_normalized, DPGolos, deputy_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                entry['id'], 
                entry['file_name'], 
                entry['GLTime'], 
                entry['PD_NPP'], 

                entry['GL_Text'], 
                entry['RESULT'],
                entry['YESCnt'],
                entry['DocTime'],
                entry['DPName'],
                entry['DPName_normalized'],
                entry['DPGolos'],
                entry['deputy_id']
            ))
        except sqlite3.Error as e:
            print(f"SQLite error: {e} for entry: {entry}")
    
    db_conn.commit()
    db_conn.close()

def process_files(processed_files):
    """Process all JSON files and assign consistent deputy IDs"""
    print(f"Processing {len(processed_files)} JSON files")
    
    # First, create a database backup
    try:
        if os.path.exists('documents.db'):
            backup_name = f"documents_backup_{datetime.now().strftime('%Y%m%d%H%M%S')}.db"
            with open('documents.db', 'rb') as src, open(backup_name, 'wb') as dst:
                dst.write(src.read())
            print(f"Created database backup: {backup_name}")
    except Exception as e:
        print(f"Warning: Could not create database backup: {e}")
    
    # Process files
    for json_file in sorted(list(processed_files)):
        print(f"Processing {json_file}")
        
        # Read and parse JSON file
        try:
            with open(json_file, 'r', encoding='utf-8') as file:
                corrected_json = file.read()
            
            json_data = json.loads(corrected_json)
        except (IOError, json.JSONDecodeError) as e:
            print(f"Error with file {json_file}: {e}")
            continue
        
        # Extract main document data
        file_name = os.path.basename(json_file)
        doc_data = {
            'file_name': file_name,
            'orgName': json_data.get('OrgName'),        
            'GLTime': json_data.get('GLTime'),
            'PD_NPP': json_data.get('PD_NPP'),

            'GL_Text': json_data.get('GL_Text'),
            'DocTime': json_data.get('DocTime'),
            'RESULT': json_data.get('RESULT'),
            'YESCnt': json_data.get('YESCnt')
        }
        
        # Store data
        store_data(doc_data, json_data.get('DPList', []))
    
    # Print summary statistics
    db_conn = sqlite3.connect('documents.db')
    cursor = db_conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM documents")
    doc_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM deputies")
    deputy_count = cursor.fetchone()[0]
    
    print(f"Total records processed: {doc_count}")
    print(f"Total unique deputies (after normalization): {deputy_count}")
    
    # Display some examples of name normalization
    cursor.execute('''
    SELECT deputy_id, normalized_name, original_names 
    FROM deputies 
    WHERE original_names LIKE '%,%'
    LIMIT 10
    ''')
    
    print("\nExamples of normalized deputy names:")
    for deputy_id, normalized_name, original_names in cursor.fetchall():
        variations = original_names.split(',')
        print(f"Deputy ID {deputy_id}: '{normalized_name}' - Variations: {variations}")
    
    db_conn.close()

# If directly running this script
if __name__ == "__main__":
    # Get all processed JSON files
    processed_files = {os.path.join(root, file) for root, dirs, files in os.walk("/Users/Oksana/Documents/PERSONAL_PRJCTS/ua_kmr_voting/src/extracted_files") 
                        for file in files if file.endswith(".json")}
    print("Found", len(processed_files), "JSON files")
    
    process_files(processed_files)