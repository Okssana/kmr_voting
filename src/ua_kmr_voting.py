
from pprint import pprint
from urllib.parse import urljoin
from requests.exceptions import RequestException

from datetime import datetime
import lxml.html
import requests
import time
import csv
import os
import zipfile
from memorious.operations.extract import extract_zip
import pathlib

import hashlib
import json
import re 

zipfile_paths = []
#URL = 'https://kmr.gov.ua/uk/result_golosuvanya' 
#URL = 'https://kmr.gov.ua/uk/result_golosuvanya?start=0'
URL_FULL = "https://kmr.gov.ua/uk/result_golosuvanya?title=&field_start_date_n_h_value%5Bmin%5D=&field_start_date_n_h_value%5Bmax%5D=&page="
URL = 'https://kmr.gov.ua/uk/result_golosuvanya?title=&field_start_date_n_h_value[min]&field_start_date_n_h_value[max]&page=0&start=0'

import openpyxl
from openpyxl import load_workbook, Workbook
HEADERS_XLSX = ["id",  "time", "question", "status", "short_name", "result"]



def request_page(context, url):

    for attempt in range(1, 5):
        try:
            response = context.http.get(url)
            break 
        except RequestException as e:
            context.log.error(f"Failed to request page: {e}")
            time.sleep(5 * attempt)
    return response

def count_non_empty_columns(sheet, row=1):
    """Function to count the number of non-empty columns in the specified row."""
    max_col = sheet.max_column
    non_empty_cols = 0
    for col in range(1, max_col + 1):
        if sheet.cell(row=row, column=col).value:
            non_empty_cols += 1
    return non_empty_cols

# Function to find the last non-empty row
def find_last_row(sheet):
    for row in range(sheet.max_row, 0, -1):
        if any(sheet.cell(row=row, column=col).value for col in range(1, sheet.max_column + 1)):
            return row
    return 0


def init(context, data):

    #response_main_page = request_page(context, URL)
    response_last_page = request_page(context, URL)
    doc_last_page = lxml.html.fromstring(response_last_page.text)
    ### get the last page number
    last_page = doc_last_page.xpath('//a[@class="field-content"][@title="До останньої сторінки"]/@href')
    # last page number after =
    last_page = last_page[0]
    print("Last page number:", last_page)
    last_page = last_page.split('&')[-2].split('=')[-1]
    print("Last page number:", last_page)

    last_page = int(last_page)

    for i in range(15, 17): # pages last_page
        context.log.info(f"Processing page: {i}")   
        response_main_page = request_page(context, URL_FULL + str(i))
        print("URL:", URL_FULL + str(i))
        doc = lxml.html.fromstring(response_main_page.text)

        
        #
        block = doc.xpath('//div[@class="view-content"]')

        for i in block:
            for j in i.getchildren():
                if 'zip' in j.text_content():

                    link = j.xpath('.//a/@href')[1]

                    # download the file
                    response = request_page(context, link)
                    file_name = link.split('/')[-1]

                    zipfile_path = pathlib.Path(response.file_path)  
                    zipfile_paths.append(zipfile_path) 
                    extract_to = pathlib.Path(context.work_path)
                    context.log.info(f"Downloaded and stored ZIP file: {file_name}")


                    # Extract the ZIP file immediately
                    with zipfile.ZipFile(zipfile_path, "r") as zf:
                        zf.extractall(extract_to)

                    context.log.info(f"ZIP file {zipfile_path} was extracted to {extract_to}")

                    # read JSON files in the extracted folder
                    process_extracted_files(context, extract_to)

                    # with open(file_name, 'wb') as f:
                    #     f.write(response.text)
                    
                    # extract the file
                    # extract_zip(context, file_name)
                    # os.remove(file_name)
                    # break

                elif 'xlsx' in j.text_content():
                    link_xlsx = j.xpath('.//a/@href')[1]
                    print("Link XLSX:", link_xlsx)
                    # download the file
                    response = request_page(context, link_xlsx)
                    #response = requests.get(link_xlsx)

                    if response:
                        path = pathlib.Path(response.file_path)
                        print("Path:", path)

                        file_name = link_xlsx.split('/')[-1]

                        # file_path = os.path.join(context.work_path, file_name)
                        # files_path = pathlib.Path(file_path)
                        print("File path MIS:", file_name)


                        # Read .xlsx file from path
                        with open(path, 'rb') as f:
                            file_content = f.read()
                            
                        new_path = path.with_suffix('.xlsx')
                        print("New path:", new_path)
                        # Rewrite the file with .xlsx extension
                        with open(new_path, 'wb') as f:
                            f.write(file_content)

                        # process the XLSX file
                        process_xlsx(context, new_path)
                        context.log.info(f"Processed XLSX file: {file_name}")

                    else:
                        context.log.info(f"Skipping file:")


def process_xlsx(context, data):

    # Create a new workbook for the combined long table
    combined_wb = Workbook()
    combined_sheet = combined_wb.active
    combined_sheet.append(HEADERS_XLSX)

    xlsx_files = [file for file in os.listdir(context.work_path) if file.endswith('.xlsx')]

    context.log.info(f"Number of XLSX files: {len(xlsx_files)}")

    for xlsx_file in xlsx_files:
        print("XLSX file:", xlsx_file)
        context.log.info(f"Processing file: {xlsx_file}")
        file_path = os.path.join(context.work_path, xlsx_file)

        wb = load_workbook(file_path)
        ws = wb.active

        # Select the active sheet
        sheet = wb.active
        
        # Get the last non-empty row count
        max_row = find_last_row(sheet)
        print(f"Last non-empty row: {max_row}")

        # Count the number of non-empty columns
        non_empty_col_count = count_non_empty_columns(sheet)
        print(f"Number of non-empty columns: {non_empty_col_count} for a file {xlsx_file}")


        # Determine the starting column based on the number of columns
        start_col = 5 if non_empty_col_count == 124 else 6 if non_empty_col_count == 125 else None # 5 or 6
        
        fixed_cols_range = range(2, start_col) if non_empty_col_count == 125 else range(1, start_col)


        # Iterate over rows starting from the second row (assuming the first row is headers)
        for row in range(2, max_row + 1):
            fixed_data = [sheet.cell(row=row, column=col).value for col in fixed_cols_range]

            # Iterate over the next 121 columns 
            for col in range(start_col, start_col + 121):
                #print(f"Processing column: {col}")

                # Extract the entity name from the header row (assuming the first row has headers)
                entity_name = sheet.cell(row=1, column=col).value
                #print(f"---- Entity name: {entity_name}")

                # Extract the result for this entity
                result = sheet.cell(row=row, column=col).value
                #print(f"---- Result: {result}")

                # Combine fixed data with entity name and result
                new_row = fixed_data + [entity_name, result]
                #print(f"New row: {new_row}")

                #Append the new row to the combined sheet
                combined_sheet.append(new_row)
        

        combined_path = "/Users/Oksana/Documents/PERSONAL_PRJCTS/ua_kmr_voting/excel/combined_long_table2.xlsx"
        print("Combined path:", combined_path)
        combined_wb.save(combined_path)
        print("Combined file saved")
        
            




def read_xlsx(file_path):
    wb = load_workbook(file_path)
    ws = wb.active

    # Select the active sheet
    sheet = wb.active
    
    # Get the last non-empty row count
    max_row = find_last_row(sheet)
    print(f"Last non-empty row: {max_row}")

    # Count the number of non-empty columns
    non_empty_col_count = count_non_empty_columns(sheet)
    print(f"Number of non-empty columns: {non_empty_col_count}")


def store_exel(context, data):
    # id	time	question	status	short_name result
    print("Data:", data)
    context.log.info(f"Storing data excel: ")

    doc_data = {
        'id': data.get('id'),
        'time': data.get('time'),
        'question': data.get('question'),
        'status': data.get('status'),
        'short_name': data.get('short_name'),
        'result': data.get('result')

    }
    print("Doc data:", doc_data)
    # # Insert combined data into a single table
    # #table_name = context.params.get('dataset')
    # table = context.datastore['ua_kmr_voting_xlsx']
    # #table = context.datastore[table_name]

    # table.upsert(doc_data, ['id', 'time', 'question', 'status', 'short_name', 'result'])




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
            #print("JSON DATA type:", type(json_data))
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




def store(context, data):
    # Extract main document data
    context.log.info(f"Storing data: {data.get('file_name')}")
    doc_data = {
        'id': data.get('id'),
        'file_name': data.get('file_name'),

        'source_url': data.get('source_url'),
        'orgName': data.get('OrgName'),
        'SName': data.get('SName'),
        'GLType': data.get('GLType'),
        'GLTime': data.get('GLTime'),
        'PD_NPP': data.get('PD_NPP'),
        'GL_Text': data.get('GL_Text'),
        'DocTime': data.get('DocTime')
    }

    # Process and combine DPList entries with main document data
    combined_data = []
    dp_list = data.get('DPList', [])
    for dp_entry in dp_list:
        combined_entry = doc_data.copy()
        combined_entry.update({
            'DPName': dp_entry.get('DPName'),
            'DPGolos': 'Відсутній' if dp_entry.get('DPGolos') == '.........' else dp_entry.get('DPGolos')
        })
        #print("Combined entry:", combined_entry)
        combined_data.append(combined_entry)
    
    if not dp_list:
        combined_data.append(doc_data)
    
    # Insert combined data into a single table
    table_name = context.params.get('dataset')
    table = context.datastore[table_name]
    for entry in combined_data:
        #print("Entry:", entry, "\n")
        table.upsert(entry, ['id', 'file_name', 
                             'SName', 'GLType', 'GLTime', 'PD_NPP', 'GL_Text', 'DocTime', 'DPName', 'DPGolos'])


