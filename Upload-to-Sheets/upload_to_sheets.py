#!/usr/bin/env python3
"""
Script to upload CSV files to Google Sheets.

Usage:
    python upload_to_sheets.py SPREADSHEET_ID SHEET_NAME file_path
"""

import os
import sys
import csv
import argparse
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import pickle

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']


def get_credentials():
    """Get valid user credentials from storage or prompt for authorization."""
    creds = None
    token_file = 'token.pickle'
    
    # The file token.pickle stores the user's access and refresh tokens.
    if os.path.exists(token_file):
        with open(token_file, 'rb') as token:
            creds = pickle.load(token)
    
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open(token_file, 'wb') as token:
            pickle.dump(creds, token)
    
    return creds


def read_csv_file(file_path):
    """Read the sparkler-subscriptions.csv file and parse it into rows."""
    rows = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        csv_reader = csv.reader(f)
        for row in csv_reader:
            rows.append(row)
    
    return rows

#Neil's original function using sheet_rows parameter
#def upload_to_sheets(data, spreadsheet_id, sheet_name, sheet_rows):
#    """Upload data to Google Sheets."""
#    try:
#        creds = get_credentials()
#        service = build('sheets', 'v4', credentials=creds)
#        
#        # Clear existing data in the sheet (optional - comment out if you want to append)
#        try:
#            # First, try to get the sheet ID by name
#            sheet_metadata = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
#            sheets = sheet_metadata.get('sheets', [])
#            sheet_id = None
#            for sheet in sheets:
#                if sheet['properties']['title'] == sheet_name:
#                    sheet_id = sheet['properties']['sheetId']
#                    break
#            
#            if sheet_id is None:
#                # Sheet doesn't exist, create it
#                requests = [{
#                    'addSheet': {
#                        'properties': {
#                            'title': sheet_name
#                        }
#                    }
#                }]
#                body = {'requests': requests}
#                service.spreadsheets().batchUpdate(
#                    spreadsheetId=spreadsheet_id, body=body).execute()
#                print(f"Created new sheet: {sheet_name}")
#            else:
#                # Clear existing data
#                range_name = f"{sheet_name}!A1:Z10000000"
#                service.spreadsheets().values().clear(
#                    spreadsheetId=spreadsheet_id,
#                    range=range_name
##                ).execute()
#                print(f"Cleared existing data in sheet: {sheet_name}")
#        except HttpError as e:
#            print(f"Note: Could not clear sheet (this is okay if sheet doesn't exist): {e}")
#        
#        # Clear unneccessary columns (to save cells)
#        try:
#            # Get sheet ID by name, if it was created above.
#            sheet_metadata = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
#            sheets = sheet_metadata.get('sheets', [])
#            sheet_id = None
#            for sheet in sheets:
#                if sheet['properties']['title'] == sheet_name:
#                    sheet_id = sheet['properties']['sheetId']
#                    break
#
#            # Delete the columns
#            requests = [{
#                "deleteDimension": {
#                    "range": {
#                        "sheetId": sheet_id,
#                        "dimension": "COLUMNS",
#                        "startIndex": sheet_rows, # inclusive (0 = column A)
#                        "endIndex": 99999         # exclusive
#                    }
#                }
#            }]
#
#            body = {"requests": requests}
#
#            service.spreadsheets().batchUpdate(
#                spreadsheetId=spreadsheet_id, body=body).execute()
#            print(f"Deleted unnecessary columns: {sheet_name}")
#        except HttpError as e:
#            print(f"Note: Could not delete columns: {e}")
#        
#        # Prepare the range
#        range_name = f"{sheet_name}!A1"
#        
#        # Upload the data
#        body = {
#            'values': data
#        }
#        
#        result = service.spreadsheets().values().update(
#            spreadsheetId=spreadsheet_id,
#            range=range_name,
##            valueInputOption='RAW',
#            valueInputOption='USER_ENTERED',
#            body=body
#        ).execute()
#        
#        print(f"Successfully uploaded {result.get('updatedCells')} cells to Google Sheets!")
#        print(f"Updated range: {result.get('updatedRange')}")
#        
#        return True
#        
#    except HttpError as error:
#        print(f"An error occurred: {error}")
#        return False
#

#Updated to not need sheet_rows, gets # of cols from the csv.
#Uploads the sparkler bundle points correctly some of the time but always outputs socket.timeout: The read operation timed out
#def upload_to_sheets(data, spreadsheet_id, sheet_name):
#    """Upload data to Google Sheets."""
#    try:
#        if not data or not data[0]:
##            print("ERROR: No data to upload")
#            return False
##
#        # Determine number of columns from CSV
#        num_cols = max(len(row) for row in data)
#
#        creds = get_credentials()
#        service = build('sheets', 'v4', credentials=creds)
#
#        # Get spreadsheet metadata
#        sheet_metadata = service.spreadsheets().get(
#            spreadsheetId=spreadsheet_id
#        ).execute()
#
#        sheets = sheet_metadata.get('sheets', [])
#        sheet_id = None
#
#        for sheet in sheets:
##            if sheet['properties']['title'] == sheet_name:
#                sheet_id = sheet['properties']['sheetId']
#                break
#
#        # Create sheet if it doesn't exist
#        if sheet_id is None:
#            service.spreadsheets().batchUpdate(
#                spreadsheetId=spreadsheet_id,
#                body={
#                    "requests": [{
#                        "addSheet": {
#                            "properties": {
#                                "title": sheet_name
#                            }
#                        }
#                    }]
#                }
#            ).execute()
#            print(f"Created new sheet: {sheet_name}")
#
#            # Re-fetch to get the new sheet ID
#            sheet_metadata = service.spreadsheets().get(
#                spreadsheetId=spreadsheet_id
#            ).execute()
#
#            for sheet in sheet_metadata.get('sheets', []):
#                if sheet['properties']['title'] == sheet_name:
#                    sheet_id = sheet['properties']['sheetId']
#                    break
#        else:
#            # Clear existing data (values only)
#            service.spreadsheets().values().clear(
#                spreadsheetId=spreadsheet_id,
#                range=f"{sheet_name}!A1:ZZ"
#            ).execute()
#            print(f"Cleared existing data in sheet: {sheet_name}")
#
#        # Upload data starting at A1
#        result = service.spreadsheets().values().update(
#            spreadsheetId=spreadsheet_id,
#            range=f"{sheet_name}!A1",
#            valueInputOption='USER_ENTERED',
#            body={'values': data}
#        ).execute()
#
#        print(f"Successfully uploaded {result.get('updatedCells')} cells")
#        print(f"Updated range: {result.get('updatedRange')}")
#
#        # Trim unnecessary columns beyond CSV width
#        try:
#            service.spreadsheets().batchUpdate(
#                spreadsheetId=spreadsheet_id,
#                body={
#                    "requests": [{
#                        "deleteDimension": {
#                            "range": {
#                                "sheetId": sheet_id,
#                                "dimension": "COLUMNS",
#                                "startIndex": num_cols,  # 0-based
#                                "endIndex": 99999
#                            }
#                        }
#                    }]
#                }
#            ).execute()
#            print(f"Trimmed sheet to {num_cols} columns")
#        except HttpError as e:
#            print(f"Note: Could not trim columns: {e}")
#
#        return True
#
#    except HttpError as error:
#        print(f"An error occurred: {error}")
#        return False



# Version that batches uploads in order to get the max rows (1500000) to sheet. 
# Note only 60 batch calls can be made right after another
def upload_to_sheets(data, spreadsheet_id, sheet_name, batch_size=50000):
    """
    Upload data to Google Sheets in batches, automatically trimming columns based on CSV.
    
    Args:
        data (list): 2D list of rows to upload.
        spreadsheet_id (str): Google Sheets spreadsheet ID.
        sheet_name (str): Name of the sheet/tab.
        batch_size (int): Number of rows per batch.
    """

    try:
        if not data or not data[0]:
            print("ERROR: No data to upload")
            return False

        # Determine number of columns from CSV
        num_cols = max(len(row) for row in data)

        # Get credentials and build service
        creds = get_credentials()
        service = build('sheets', 'v4', credentials=creds)

        # Get spreadsheet metadata
        sheet_metadata = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        sheets = sheet_metadata.get('sheets', [])
        sheet_id = None

        # Find the sheet ID if it exists
        for sheet in sheets:
            if sheet['properties']['title'] == sheet_name:
                sheet_id = sheet['properties']['sheetId']
                break

        # Create sheet if it doesn't exist
        if sheet_id is None:
            service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body={"requests": [{
                    "addSheet": {"properties": {"title": sheet_name}}
                }]}
            ).execute()
            print(f"Created new sheet: {sheet_name}")

            # Re-fetch metadata to get the new sheet ID
            sheet_metadata = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
            for sheet in sheet_metadata.get('sheets', []):
                if sheet['properties']['title'] == sheet_name:
                    sheet_id = sheet['properties']['sheetId']
                    break
        else:
            # Clear existing data
            service.spreadsheets().values().clear(
                spreadsheetId=spreadsheet_id,
                range=f"{sheet_name}!A1:ZZ"
            ).execute()
            print(f"Cleared existing data in sheet: {sheet_name}")

        # ---- Upload in batches ----
        total_rows = len(data)
        print(f"Uploading {total_rows} rows in batches of {batch_size}...")

        range_start = 1  # Google Sheets rows start at 1
        for start in range(0, total_rows, batch_size):
            end = min(start + batch_size, total_rows)
            batch = data[start:end]
            batch_range = f"{sheet_name}!A{range_start}"
            body = {'values': batch}

            service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=batch_range,
                valueInputOption='USER_ENTERED',
                body=body
            ).execute()

            range_start += len(batch)
            print(f"Uploaded rows {start + 1} to {end}")

        # ---- Trim unnecessary columns ----
        try:
            service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body={"requests": [{
                    "deleteDimension": {
                        "range": {
                            "sheetId": sheet_id,
                            "dimension": "COLUMNS",
                            "startIndex": num_cols,
                            "endIndex": 99999
                        }
                    }
                }]}
            ).execute()
            print(f"Trimmed sheet to {num_cols} columns")
        except HttpError as e:
            print(f"Note: Could not trim columns: {e}")

        print(f"Successfully uploaded {total_rows} rows to Google Sheets!")
        return True

    except HttpError as error:
        print(f"An error occurred: {error}")
        return False






#Jan 29th - updated to remove sheet_rows param
def main():
    """Main function."""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description='Upload CSV file to Google Sheets'
    )
    parser.add_argument(
        'spreadsheet_id',
        help='The ID of the Google Spreadsheet'
    )
    parser.add_argument(
        'sheet_name',
        help='The name of the sheet/tab where data will be written'
    )
#    parser.add_argument(
#       'sheet_rows',
#       help='The number of rows in the spreadsheet'
#    )
    parser.add_argument(
        'file_path',
        help='Path to the CSV file to upload'
    )
    
    args = parser.parse_args()
    
    spreadsheet_id = args.spreadsheet_id
    sheet_name = args.sheet_name
    #sheet_rows = args.sheet_rows
    file_path = args.file_path
    
    # Check if credentials file exists (using relative path since script runs in this directory)
    if not os.path.exists('credentials.json'):
        print("ERROR: credentials.json not found!")
        print("Please download it from Google Cloud Console (see setup instructions)")
        sys.exit(1)
    
    # Check if CSV file exists
    if not os.path.exists(file_path):
        print(f"ERROR: {file_path} not found!")
        sys.exit(1)
    
    print(f"Reading {file_path}...")
    data = read_csv_file(file_path)
    print(f"Read {len(data)} rows (including header)")
    
    # Upload to Google Sheets
    print("Uploading to Google Sheets...")
    #success = upload_to_sheets(data, spreadsheet_id, sheet_name, sheet_rows)
    success = upload_to_sheets(data, spreadsheet_id, sheet_name)
    
    if success:
        print("Upload completed successfully!")
    else:
        print("Upload failed!")
        sys.exit(1)


if __name__ == '__main__':
    main()
