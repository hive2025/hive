"""
Update Google Sheets with new column headers
Run this ONCE to add the new columns to your existing sheet
"""

import pickle
import gspread

def update_headers():
    print("Updating Google Sheets headers...")

    # Load credentials
    with open('token.pickle', 'rb') as token:
        creds = pickle.load(token)

    # Connect to sheets
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key('1A-rTshHRACRejTUDSvXuGfwzLzbddNqhm_w1e6SHXyY')

    # Get Events sheet
    events_sheet = spreadsheet.worksheet('Events')

    # Get current headers
    current_headers = events_sheet.row_values(1)
    print(f"Current columns: {len(current_headers)}")

    # New complete header structure
    new_headers = [
        'Event ID', 'User Email', 'Academic Year', 'Quarter', 'Program Name',
        'Program Type', 'Activity Lead By', 'Program Theme', 'Duration (Hrs)',
        'Event Level', 'Mode of Delivery', 'Start Date', 'End Date',
        'Student Participants', 'Faculty Participants', 'External Participants',
        'Expenditure Amount', 'Remark', 'Objective', 'Benefits', 'Brief Report',
        'Video URL', 'Geotag_Photo1_ID', 'Geotag_Photo2_ID', 'Geotag_Photo3_ID',
        'Normal_Photo1_ID', 'Normal_Photo2_ID', 'Normal_Photo3_ID',
        'Attendance_Report_ID', 'Feedback_Analysis_ID', 'Event_Agenda_ID',
        'Chief_Guest_Biodata_ID', 'Generated_PDF_ID',
        'Twitter URL', 'Facebook URL', 'Instagram URL', 'LinkedIn URL',
        'Created Date', 'Last Modified', 'Status', 'Admin_Approval_Status',
        'Approval_Date', 'Approved_By', 'Rejection_Reason', 'Drive Folder URL'
    ]

    print(f"New structure: {len(new_headers)} columns")

    # Update the header row
    print("\nUpdating headers...")
    # For 45 columns, we need A1:AS1
    # Use resize to add more columns if needed
    current_col_count = events_sheet.col_count
    if current_col_count < len(new_headers):
        print(f"Resizing sheet from {current_col_count} to {len(new_headers)} columns...")
        events_sheet.resize(cols=len(new_headers))

    # Update using simple range
    events_sheet.update('1:1', [new_headers], value_input_option='RAW')

    print("✓ Headers updated successfully!")
    print("\nNew columns added:")
    print("- Brief Report")
    print("- Geotag_Photo1_ID, Geotag_Photo2_ID, Geotag_Photo3_ID")
    print("- Normal_Photo1_ID, Normal_Photo2_ID, Normal_Photo3_ID")
    print("- Attendance_Report_ID")
    print("- Feedback_Analysis_ID")
    print("- Event_Agenda_ID")
    print("- Chief_Guest_Biodata_ID")
    print("- Generated_PDF_ID")
    print("- Admin_Approval_Status")
    print("- Approval_Date, Approved_By, Rejection_Reason")

    # Show the updated structure
    updated_headers = events_sheet.row_values(1)
    print(f"\nTotal columns now: {len(updated_headers)}")

    return True

if __name__ == "__main__":
    try:
        update_headers()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
