"""
Script to update Google Sheets headers with new fields.
Run this script locally to add the new columns to your existing spreadsheet.
"""

import gspread
from google.oauth2.service_account import Credentials
import os

# Configuration
SPREADSHEET_ID = "1A-rTshHRACRejTUDSvXuGfwzLzbddNqhm_w1e6SHXyY"

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

# New headers in the correct order
NEW_HEADERS = [
    'Event ID', 'User Email', 'Academic Year', 'Quarter', 'Program Name',
    'Program Type', 'Program Driven By', 'Activity Led By', 'Program Theme',
    'Organizing Departments', 'Professional Society Club',
    'Duration (Hrs)', 'Event Level', 'Mode of Delivery', 'Start Date', 'End Date',
    'Student Participants', 'Faculty Participants', 'External Participants',
    'Expenditure Amount', 'Remark', 'Objective', 'Benefits',
    'Speaker Names', 'Speaker Designation', 'Speaker Organization', 'Session Video URL',
    'Brief Report', 'Geotag_Photo1_ID', 'Geotag_Photo2_ID', 'Geotag_Photo3_ID',
    'Normal_Photo1_ID', 'Normal_Photo2_ID', 'Normal_Photo3_ID',
    'Attendance_Report_ID', 'Feedback_Analysis_ID', 'Event_Agenda_ID',
    'Chief_Guest_Biodata_ID', 'Permission_SOP_ID', 'Invitation_Brochure_ID',
    'Other_Documents_ID', 'KPI_Report_ID', 'Generated_PDF_ID', 'Signed_PDF_ID',
    'Twitter URL', 'Facebook URL', 'Instagram URL', 'LinkedIn URL',
    'Created Date', 'Last Modified', 'Status', 'Admin_Approval_Status',
    'Approval_Date', 'Approved_By', 'Rejection_Reason', 'Drive Folder URL'
]

def get_credentials():
    """Get credentials from local file"""
    if os.path.exists('credentials.json'):
        try:
            creds = Credentials.from_service_account_file(
                'credentials.json',
                scopes=SCOPES
            )
            return creds
        except Exception as e:
            print(f"Service account failed: {e}")

    # Try OAuth token.pickle
    if os.path.exists('token.pickle'):
        import pickle
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
            return creds

    return None

def update_headers():
    """Update the spreadsheet headers"""
    print("Getting credentials...")
    creds = get_credentials()

    if not creds:
        print("[ERROR] No credentials found!")
        print("Please ensure you have either:")
        print("  - credentials.json (service account)")
        print("  - token.pickle (OAuth token)")
        return False

    print("[OK] Credentials loaded")

    # Connect to Google Sheets
    print("Connecting to Google Sheets...")
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(SPREADSHEET_ID)

    # Get the Events sheet
    try:
        events_sheet = spreadsheet.worksheet('Events')
        print("[OK] Found Events sheet")
    except:
        print("[ERROR] Events sheet not found!")
        return False

    # Resize sheet to accommodate more columns
    print("Resizing sheet to accommodate new columns...")
    try:
        events_sheet.resize(rows=1000, cols=60)
        print("[OK] Sheet resized to 60 columns")
    except Exception as e:
        print(f"Warning: Could not resize sheet: {e}")

    # Get current headers
    current_headers = events_sheet.row_values(1)
    print(f"\nCurrent headers: {len(current_headers)} columns")

    # Find new columns to add
    columns_to_add = []
    for h in NEW_HEADERS:
        if h not in current_headers:
            columns_to_add.append(h)

    print(f"Columns to add: {columns_to_add}")

    if not columns_to_add:
        print("\n[OK] All headers already exist!")
        return True

    # Add new columns at the end
    next_col = len(current_headers) + 1
    for col_name in columns_to_add:
        try:
            events_sheet.update_cell(1, next_col, col_name)
            print(f"[OK] Added '{col_name}' at column {next_col}")
            next_col += 1
        except Exception as e:
            print(f"[ERROR] Failed to add '{col_name}': {e}")

    print("\n" + "="*50)
    print("[SUCCESS] Headers updated!")
    print("="*50)

    # Show final headers
    final_headers = events_sheet.row_values(1)
    print(f"\nFinal headers ({len(final_headers)} columns):")
    for i, h in enumerate(final_headers, 1):
        print(f"  {i}. {h}")

    return True

if __name__ == "__main__":
    print("="*50)
    print("Google Sheets Header Update Script")
    print("="*50)
    print()
    update_headers()
