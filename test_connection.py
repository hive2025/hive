"""
Test if Google Sheets and Drive connection works with current credentials
"""

import pickle
import os
import gspread
from googleapiclient.discovery import build

def test_connection():
    print("Testing Google API connection...")

    # Load credentials
    if not os.path.exists('token.pickle'):
        print("ERROR: token.pickle not found!")
        return False

    with open('token.pickle', 'rb') as token:
        creds = pickle.load(token)

    print(f"Credentials loaded")
    print(f"Valid: {creds.valid}")
    print(f"Expired: {creds.expired}")
    print(f"Token: {creds.token[:20]}..." if creds.token else "No token")

    # Test Sheets with gspread
    try:
        print("\nTesting gspread (Google Sheets)...")
        sheets_client = gspread.authorize(creds)
        print("gspread client created")

        # Try to open the spreadsheet
        import config
        spreadsheet = sheets_client.open_by_key(config.SPREADSHEET_ID)
        print(f"SUCCESS: Connected to spreadsheet: {spreadsheet.title}")

        # Try to get Users sheet
        try:
            users_sheet = spreadsheet.worksheet('Users')
            print(f"SUCCESS: Found Users sheet with {users_sheet.row_count} rows")

            # Get emails
            emails = users_sheet.col_values(1)
            print(f"Emails in sheet: {emails[:3]}")  # First 3 rows

        except Exception as e:
            print(f"ERROR accessing Users sheet: {e}")

    except Exception as e:
        print(f"ERROR with gspread: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Test Drive
    try:
        print("\nTesting Google Drive API...")
        drive_service = build('drive', 'v3', credentials=creds)
        about = drive_service.about().get(fields="user").execute()
        print(f"SUCCESS: Drive connected as: {about['user']['emailAddress']}")

    except Exception as e:
        print(f"ERROR with Drive: {e}")
        return False

    print("\nAll tests PASSED!")
    return True

if __name__ == "__main__":
    test_connection()
