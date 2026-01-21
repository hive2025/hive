"""
Simple authentication script to set up OAuth2 credentials
Run this BEFORE running the main Streamlit app
"""

import os
import pickle
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = [
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/spreadsheets'
]

def authenticate():
    """Authenticate with Google OAuth2"""
    creds = None

    # Check if token already exists
    if os.path.exists('token.pickle'):
        print("Found existing token.pickle")
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
        print(f"Token valid: {creds.valid}")
        print(f"Token expired: {creds.expired if creds else 'N/A'}")

    # If no valid credentials, authenticate
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Refreshing expired token...")
            try:
                creds.refresh(Request())
                print("✅ Token refreshed successfully!")
            except Exception as e:
                print(f"❌ Token refresh failed: {e}")
                creds = None

        if not creds:
            if not os.path.exists('client_secret.json'):
                print("❌ ERROR: client_secret.json not found!")
                print("Please download OAuth2 credentials from Google Cloud Console")
                return False

            print("Starting OAuth2 authentication flow...")
            print("Your browser will open for Google login...")

            flow = InstalledAppFlow.from_client_secrets_file(
                'client_secret.json', SCOPES)

            creds = flow.run_local_server(port=0)
            print("✅ Authentication successful!")

        # Save credentials
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
        print("✅ Credentials saved to token.pickle")

    # Test the credentials
    try:
        print("\nTesting credentials...")
        drive_service = build('drive', 'v3', credentials=creds)
        sheets_service = build('sheets', 'v4', credentials=creds)

        # Test Drive access
        print("Testing Google Drive access...")
        about = drive_service.about().get(fields="user").execute()
        print(f"✅ Drive connected as: {about['user']['emailAddress']}")

        # Test Sheets access
        print("Testing Google Sheets access...")
        import config
        spreadsheet = sheets_service.spreadsheets().get(
            spreadsheetId=config.SPREADSHEET_ID
        ).execute()
        print(f"✅ Sheets connected: {spreadsheet['properties']['title']}")

        print("\n🎉 All tests passed! You can now run the Streamlit app.")
        return True

    except Exception as e:
        print(f"❌ Error testing credentials: {e}")
        return False

if __name__ == "__main__":
    print("="*60)
    print("IIC Event Portal - OAuth2 Authentication Setup")
    print("="*60)
    authenticate()
