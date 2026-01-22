"""
Generate OAuth Token for Streamlit Cloud Deployment

Run this script locally to:
1. Authenticate with your Google account
2. Generate a new refresh token
3. Output the credentials for Streamlit secrets

Requirements:
- client_secret.json file in the same directory (OAuth2 credentials from Google Cloud Console)
"""

import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials

SCOPES = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/spreadsheets'
]

def generate_token():
    if not os.path.exists('client_secret.json'):
        print("❌ ERROR: client_secret.json not found!")
        print("\nTo create client_secret.json:")
        print("1. Go to https://console.cloud.google.com/")
        print("2. Select your project")
        print("3. Go to 'APIs & Services' > 'Credentials'")
        print("4. Click 'Create Credentials' > 'OAuth client ID'")
        print("5. Choose 'Desktop app' as application type")
        print("6. Download the JSON and rename it to 'client_secret.json'")
        return

    print("🔐 Starting OAuth authentication...")
    print("A browser window will open. Please sign in with your Google account.\n")

    flow = InstalledAppFlow.from_client_secrets_file('client_secret.json', SCOPES)
    creds = flow.run_local_server(port=0)

    # Load client_secret to get client_id and client_secret
    with open('client_secret.json', 'r') as f:
        client_data = json.load(f)

    # Handle both 'installed' and 'web' credential types
    if 'installed' in client_data:
        client_info = client_data['installed']
    elif 'web' in client_data:
        client_info = client_data['web']
    else:
        print("❌ Invalid client_secret.json format")
        return

    print("\n" + "="*60)
    print("✅ Authentication successful!")
    print("="*60)
    print("\nCopy the following to your Streamlit Cloud secrets:\n")
    print("[google_oauth]")
    print(f'refresh_token = "{creds.refresh_token}"')
    print(f'client_id = "{client_info["client_id"]}"')
    print(f'client_secret = "{client_info["client_secret"]}"')
    print(f'token_uri = "https://oauth2.googleapis.com/token"')
    print("\n" + "="*60)

    # Also save to token.pickle for local testing
    import pickle
    with open('token.pickle', 'wb') as token:
        pickle.dump(creds, token)
    print("\n✅ token.pickle also saved for local testing")

if __name__ == "__main__":
    generate_token()
