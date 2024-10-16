 
from pprint import pprint
from urllib.parse import urljoin
from requests.exceptions import RequestException

from datetime import datetime
import lxml.html
import time
import os
import zipfile
from memorious.operations.extract import extract_zip
import pathlib
from openpyxl import load_workbook, Workbook
import hashlib
import json
import re 

from concurrent.futures import ThreadPoolExecutor
# Adjust this as needed, depending on the number of threads you want to use
MAX_WORKERS = 4

zipfile_paths = []
CHUNK_SIZE = 100 
URL_FULL = "https://kmr.gov.ua/uk/result_golosuvanya?title=&field_start_date_n_h_value%5Bmin%5D=&field_start_date_n_h_value%5Bmax%5D=&page="
URL = 'https://kmr.gov.ua/uk/result_golosuvanya?title=&field_start_date_n_h_value[min]&field_start_date_n_h_value[max]&page=0&start=0'



HEADERS_XLSX = ["id",  "time", "question", "status", "short_name", "result", "file_name", "source_url"]

# Counter to ensure uniqueness
counter = 0

import time
timestamp = int(time.time())  # Add a timestamp for uniqueness

def request_page(context, url):

    for attempt in range(1, 5):
        try:
            response = context.http.get(url)
            break 
        except RequestException as e:
            context.log.error(f"Failed to request page: {e}")
            time.sleep(5 * attempt)
    return response


def count_non_empty_columns(sheet, row=2):
    """Function to count the number of non-empty columns in the specified row."""
    max_col = sheet.max_column
    non_empty_cols = 0
    for col in range(1, max_col + 1):
        if sheet.cell(row=row, column=col).value:
            non_empty_cols += 1
    return non_empty_cols

# Function to find the last non-empty row in the sheet
def find_last_row(sheet):
    for row in range(sheet.max_row, 0, -1):
        if any(sheet.cell(row=row, column=col).value for col in range(1, sheet.max_column + 1)):
            return row
    return 0

def transform_results(row):
    """Function to transform the results column.
    If the result is '...', return 'Відсутній'.
    """
    if row == '...':
        return 'Відсутній'
    else:
        return row # return unchanged result if not '...'


def download_and_process(context, link, is_zip):
    """Download and process files in parallel."""
    response = request_page(context, link)
    
    if response:
        file_name = link.split('/')[-1]
        print("\n")
        print("Link in download_and_process: ", link)
        print("File name in download_and_process: ", file_name)

        file_path = pathlib.Path(response.file_path)

        print("File path in download_and_process: ", file_path)
        
        if is_zip:  # Process ZIP files
            extract_to = pathlib.Path(context.work_path)
            with zipfile.ZipFile(file_path, "r") as zf:
                zf.extractall(extract_to)
        else:  # Process XLSX files
            process_xlsx_file(context, file_path)
    else:
        context.log.info(f"Skipping file: {link}")


def process_xlsx_file(context, path):
    """Process a single XLSX file."""

    new_path = path.with_suffix('.xlsx')
    
    print("Path: ", path)
    print("New path: ", new_path)

    # Read and save the file with .xlsx extension
    with open(path, 'rb') as f:
        file_content = f.read()

    with open(new_path, 'wb') as f:
        f.write(file_content)

    # Process the XLSX file
    file_name = new_path.name
    
    process_xlsx(context, new_path, path)

    context.log.info(f"Processed XLSX file: {file_name}")


def init(context, data):
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        for i in range(16, 17):
            URL_FULL_PAGE = URL_FULL + str(i)
            response_main_page = request_page(context, URL_FULL_PAGE)
            doc = lxml.html.fromstring(response_main_page.text)
            block = doc.xpath('//div[@class="view-content"]')

            for item in block[:1]:
                for j in item.getchildren():
                    if 'zip' in j.text_content():  # ZIP files
                        link = j.xpath('.//a/@href')[1]
                        executor.submit(download_and_process, context, link, True)

                    elif 'xlsx' in j.text_content():  # XLSX files
                        link_xlsx = j.xpath('.//a/@href')[1]
                        context.log.info(f"Processing XLSX file: {link_xlsx}")
                        executor.submit(download_and_process, context, link_xlsx, False)



def process_xlsx(context, file_path):
    """Process the XLSX files and emit rows."""
    combined_wb = Workbook()
    combined_sheet = combined_wb.active
    combined_sheet.append(HEADERS_XLSX)

    xlsx_files = [file for file in os.listdir(context.work_path) if file.endswith('.xlsx')]

    for xlsx_file in xlsx_files:
        context.log.info(f"Processing XLSX file: {xlsx_file}")

        file_path = os.path.join(context.work_path, xlsx_file)
        wb = load_workbook(file_path, read_only=True)
        ws = wb[wb.sheetnames[0]]

        max_row = find_last_row(ws)
        non_empty_col_count = count_non_empty_columns(ws)
        
        start_col = 5 if non_empty_col_count == 125 else 6 # Adjust start column based on the number of columns
        print("Start column: ", start_col)
        print("Max row: ", max_row)
        fixed_cols_range = range(1, start_col)
        print("Fixed cols range: ", fixed_cols_range)

        # Iterate through rows and emit data as a dictionary
        for row in ws.iter_rows(min_row=2, max_row=max_row, values_only=True):
            fixed_data = {f"fixed_col_{col}": row[col - 1] for col in fixed_cols_range}
            
            for col in range(start_col, start_col + 122):
                entity_name = ws.cell(row=1, column=col).value
                result = row[col - 1]

                # Create a dictionary for the row
                new_row = {
                    **fixed_data,
                    "entity_name": entity_name,
                    "result": result,
                    "xlsx_file": xlsx_file # hash
                }

                # Emit the dictionary to the next stage
                context.emit(data=new_row)



def store_exel(context, data):

    #context.log.info(f"Storing data: {data.get('fixed_col_2')}")

    global counter # Counter is global. Defined outside the function in the main script
    counter += 1 # Increment counter to ensure uniqueness

    unique_string = str(int(data.get('fixed_col_1')) + int(counter))
    unique_id = hashlib.md5(unique_string.encode()).hexdigest()

    doc_data = {
        #'id': unique_id,  # Ensure id is always a string
        'id_original': data.get('fixed_col_1'), # Keep original ID for reference
        "unique_id": unique_id,
        'time': str(data.get('fixed_col_2')), 
        'question': data.get('fixed_col_3') or "", 
        'status': data.get('fixed_col_4') or "",  
        'short_name': data.get('entity_name') or "",  
        'result': data.get('result') or "", 
        "file_original": data.get('xlsx_file'),
        'retrieved_at': datetime.now().isoformat(),
        'source_url': data.get('source_url') or None  
    }

    table = context.datastore['ua_kmr_voting_xlsx']
    table.upsert(doc_data, [#'id', # id is present by default, no need to specify
                            'id_original', 'unique_id',
                            'time', 'question', 'status', 'short_name', 'result',
                            #'source_file', 
                            'file_original',
                            'retrieved_at', 'source_url'])

    #context.log.info(f"Stored for the day: {data.get('time')}")


# Function to preprocess JSON data
def preprocess_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Correct invalid newline characters within strings
    corrected_content = re.sub(r'(?<!\\)"\s*\n\s*"', r'\"', content)
    
    return corrected_content

def process_extracted_files(context, extract_to):
    json_files = [file for file in os.listdir(extract_to) if file.endswith('.json')]
    context.log.info(f"Number of JSON files: {len(json_files)} - {json_files[:1]} ")

    for json_file in json_files[:5]:
        context.log.info(f"Processing file: {json_file} with a length of {len(json_file)}")

        file_path = os.path.join(extract_to, json_file)

        # Preprocess and read the JSON file
        corrected_json = preprocess_json(file_path)

        # Parse the JSON data
        try:
            json_data = json.loads(corrected_json)
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
            return

        # Extract and store data in the dict
        dict_d = {
            'file_name': json_file,
            'json_data': json_data,
            'file_path': file_path,
            'DocTime': json_data['DocTime'],

            'source_file': json_file,
            'orgName': json_data['OrgName'],
            'SName': json_data['SName'],
            'GLType': json_data['GLType'],
            'GLTime': json_data['GLTime'],
            'PD_NPP': json_data['PD_NPP'],
            'GL_Text': json_data['GL_Text'],
            'DPList': json_data['DPList']
        }
        print("*******************")
        context.emit(data=dict_d)
        context.log.info(f"Extracted data emitted: {json_file}")


# def store(context, data):
#     # Extract main document data
#     context.log.info(f"Storing data: {data.get('file_name')}")
#     doc_data = {
#         'id': data.get('id'),
#         'file_name': data.get('file_name'),

#         'source_url': data.get('source_url'),
#         'orgName': data.get('OrgName'),
#         'SName': data.get('SName'),
#         'GLType': data.get('GLType'),
#         'GLTime': data.get('GLTime'),
#         'PD_NPP': data.get('PD_NPP'),
#         'GL_Text': data.get('GL_Text'),
#         'DocTime': data.get('DocTime')
#     }

#     # Process and combine DPList entries with main document data
#     combined_data = []
#     dp_list = data.get('DPList', [])
#     for dp_entry in dp_list:
#         combined_entry = doc_data.copy()
#         combined_entry.update({
#             'DPName': dp_entry.get('DPName'),
#             'DPGolos': 'Відсутній' if dp_entry.get('DPGolos') == '.........' else dp_entry.get('DPGolos')
#         })
#         #print("Combined entry:", combined_entry)
#         combined_data.append(combined_entry)
    
#     if not dp_list:
#         combined_data.append(doc_data)
    
#     # Insert combined data into a single table
#     table_name = context.params.get('dataset')
#     table = context.datastore[table_name]
#     for entry in combined_data:
#         #print("Entry:", entry, "\n")
#         table.upsert(entry, ['id', 'file_name', 
#                              'SName', 'GLType', 'GLTime', 'PD_NPP', 'GL_Text', 
#                              'DocTime', 'DPName', 'DPGolos'])


