"""
OAuth2 Google Drive Integration
Uses browser-based authentication instead of service accounts

TOKEN VALIDITY:
- Access token: ~1 hour (auto-refreshes using refresh token)
- Refresh token: ~6 months OR until user revokes access
- To extend: Admin can upload new token.pickle from Streamlit secrets
"""

import os
import pickle
import base64
import json
from datetime import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import streamlit as st

# Full Drive access needed for downloading uploaded files
SCOPES = [
    'https://www.googleapis.com/auth/drive',  # Full Drive access
    'https://www.googleapis.com/auth/spreadsheets'
]

def get_token_info():
    """Get information about current token status"""
    if not os.path.exists('token.pickle'):
        return None

    try:
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

        return {
            'valid': creds.valid,
            'expired': creds.expired if hasattr(creds, 'expired') else False,
            'has_refresh_token': bool(creds.refresh_token) if hasattr(creds, 'refresh_token') else False,
            'expiry': str(creds.expiry) if hasattr(creds, 'expiry') and creds.expiry else 'Unknown'
        }
    except:
        return None

def get_oauth_credentials(force_reauth=False):
    """
    Get OAuth2 credentials using browser-based authentication.
    This stores credentials in token.pickle for reuse.

    Token auto-refreshes as long as refresh_token is valid (~6 months)
    """
    creds = None

    # Method 1: Try environment variable (for Render/Vercel/Railway hosting)
    try:
        token_base64 = os.environ.get('TOKEN_PICKLE_BASE64')
        if token_base64:
            token_data = base64.b64decode(token_base64)
            creds = pickle.loads(token_data)

            # Try to refresh if expired
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except:
                    creds = None
    except:
        pass

    # Method 2: Try Streamlit secrets (for Streamlit Cloud hosting)
    if not creds:
        try:
            if hasattr(st, 'secrets') and 'token_pickle_base64' in st.secrets:
                token_data = base64.b64decode(st.secrets['token_pickle_base64'])
                creds = pickle.loads(token_data)

                # Try to refresh if expired
                if creds and creds.expired and creds.refresh_token:
                    try:
                        creds.refresh(Request())
                    except:
                        creds = None
        except:
            pass

    # Method 3: Try local token.pickle file
    if not creds and os.path.exists('token.pickle') and not force_reauth:
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

        # Check if token has the required scopes (full Drive access)
        # If old token only has drive.file, we need to re-authenticate
        if creds and hasattr(creds, 'scopes') and creds.scopes:
            required_scope = 'https://www.googleapis.com/auth/drive'
            if required_scope not in creds.scopes:
                st.warning("⚠️ Token needs upgrade for full Drive access. Re-authenticating...")
                creds = None  # Force re-authentication

    # If no valid credentials, try to refresh or re-authenticate
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                # Save refreshed credentials
                with open('token.pickle', 'wb') as token:
                    pickle.dump(creds, token)
            except Exception as e:
                print(f"Token refresh failed: {e}")
                creds = None

        if not creds:
            if not os.path.exists('client_secret.json'):
                st.error("❌ client_secret.json not found!")
                st.info("Please download OAuth2 credentials from Google Cloud Console")
                return None

            flow = InstalledAppFlow.from_client_secrets_file(
                'client_secret.json', SCOPES)

            # Use local server for authentication
            creds = flow.run_local_server(port=0)

        # Save credentials for next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return creds

def generate_token_for_secrets():
    """
    Generate base64 encoded token.pickle for Streamlit secrets.
    Run this locally after authenticating, then paste the output into Streamlit secrets.
    """
    if not os.path.exists('token.pickle'):
        return None

    with open('token.pickle', 'rb') as f:
        token_data = f.read()

    return base64.b64encode(token_data).decode('utf-8')

def get_google_services_oauth(force_reauth=False):
    """
    Initialize Google Drive and Sheets services using OAuth2.
    Returns (drive_service, sheets_service)
    """
    try:
        creds = get_oauth_credentials(force_reauth)

        if not creds:
            return None, None

        drive_service = build('drive', 'v3', credentials=creds)
        sheets_service = build('sheets', 'v4', credentials=creds)

        return drive_service, sheets_service

    except Exception as e:
        st.error(f"Authentication error: {str(e)}")
        return None, None

def create_drive_folder_oauth(drive_service, folder_name, parent_folder_id=None):
    """Create folder in Google Drive using OAuth2"""
    try:
        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }

        if parent_folder_id:
            file_metadata['parents'] = [parent_folder_id]

        folder = drive_service.files().create(
            body=file_metadata,
            fields='id'
        ).execute()

        return folder.get('id')

    except Exception as e:
        st.error(f"Error creating folder: {str(e)}")
        return None

def upload_to_drive_oauth(drive_service, file_data, file_name, folder_id):
    """Upload file to Google Drive using OAuth2"""
    try:
        file_metadata = {
            'name': file_name,
            'parents': [folder_id]
        }

        # Determine mime type
        if file_name.lower().endswith(('.jpg', '.jpeg', '.png')):
            mime_type = 'image/jpeg'
        elif file_name.lower().endswith('.pdf'):
            mime_type = 'application/pdf'
        else:
            mime_type = 'application/octet-stream'

        media = MediaIoBaseUpload(
            file_data,
            mimetype=mime_type,
            resumable=True
        )

        file = drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink'
        ).execute()

        # Make file publicly viewable (optional)
        try:
            drive_service.permissions().create(
                fileId=file.get('id'),
                body={'type': 'anyone', 'role': 'reader'}
            ).execute()
        except:
            pass

        # Return the file ID directly (not the webViewLink)
        # This makes downloading easier and more reliable
        file_id = file.get('id')
        print(f"Uploaded {file_name} with ID: {file_id}")
        return file_id

    except Exception as e:
        st.error(f"Upload error: {str(e)}")
        return None
