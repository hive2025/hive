import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io
from PIL import Image
from PIL.ExifTags import TAGS
import hashlib
import os
import logging
import config

# Configure logging to show in console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Page configuration
st.set_page_config(
    page_title=config.APP_TITLE,
    page_icon=config.APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional green theme (HIVE branding)
st.markdown("""
    <style>
    /* Main app background */
    .stApp {
        background-color: #f5f5f5;
    }
    .main .block-container {
        padding-top: 2rem;
        max-width: 1200px;
    }
    /* Form containers */
    .form-container {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.08);
        border: 1px solid #e0e0e0;
    }
    /* Main content area text colors - more specific selectors */
    .main h1, .main h2, .main h3, .main h4, .main h5, .main h6,
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4, .stMarkdown h5, .stMarkdown h6,
    [data-testid="stMarkdownContainer"] h1, [data-testid="stMarkdownContainer"] h2,
    [data-testid="stMarkdownContainer"] h3, [data-testid="stMarkdownContainer"] h4,
    [data-testid="stMarkdownContainer"] h5, [data-testid="stMarkdownContainer"] h6 {
        color: #1b5e20 !important;
    }
    .main p, .main li, .main span,
    .stMarkdown p, .stMarkdown li, .stMarkdown span,
    [data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] li {
        color: #333 !important;
    }
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1b5e20 0%, #2e7d32 100%);
    }
    section[data-testid="stSidebar"] * {
        color: white !important;
    }
    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] .stMarkdown span,
    section[data-testid="stSidebar"] .stCaption p {
        color: #c8e6c9 !important;
    }
    /* Tabs - Fix overlap issue with proper display */
    .stTabs [data-baseweb="tab-list"] {
        display: flex !important;
        flex-wrap: wrap !important;
        gap: 8px !important;
        background-color: #ffffff !important;
        padding: 12px !important;
        border-radius: 10px !important;
        border: 2px solid #c8e6c9 !important;
        margin-bottom: 1rem !important;
    }
    .stTabs [data-baseweb="tab"] {
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        background-color: #e8f5e9 !important;
        border-radius: 8px !important;
        color: #2e7d32 !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        padding: 10px 20px !important;
        border: 2px solid #a5d6a7 !important;
        min-height: 42px !important;
        white-space: nowrap !important;
        margin: 2px !important;
    }
    .stTabs [data-baseweb="tab"]:hover {
        background-color: #c8e6c9 !important;
        border-color: #66bb6a !important;
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background-color: #2e7d32 !important;
        color: #ffffff !important;
        border-color: #1b5e20 !important;
    }
    /* Tab panel styling */
    .stTabs [data-baseweb="tab-panel"] {
        padding-top: 1rem !important;
    }
    /* Buttons */
    .stButton > button {
        background-color: #2e7d32;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 0.5rem 1rem;
        font-weight: 500;
    }
    .stButton > button:hover {
        background-color: #1b5e20;
    }
    .stButton > button:focus {
        box-shadow: 0 0 0 2px #4caf50;
    }
    /* Info/Success/Warning boxes */
    .stAlert {
        border-radius: 8px;
    }
    /* Expanders */
    .streamlit-expanderHeader {
        background-color: #f1f8e9;
        border-radius: 8px;
        color: #1b5e20 !important;
    }
    /* Input fields */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > div {
        border-color: #c8e6c9;
    }
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #4caf50;
        box-shadow: 0 0 0 1px #4caf50;
    }
    </style>
""", unsafe_allow_html=True)

# Session state initialization
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'is_admin' not in st.session_state:
    st.session_state.is_admin = False
if 'user_email' not in st.session_state:
    st.session_state.user_email = None
if 'edit_mode' not in st.session_state:
    st.session_state.edit_mode = False
if 'edit_event_data' not in st.session_state:
    st.session_state.edit_event_data = None
if 'ia_portal_mode' not in st.session_state:
    st.session_state.ia_portal_mode = False

# Initialize Google API connection (cached)
@st.cache_resource
def init_google_services():
    """Initialize and cache Google API services"""
    try:
        SCOPES = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]

        creds = None

        # Method 1: Try OAuth from refresh token in Streamlit secrets (BEST - uses YOUR storage quota)
        try:
            if hasattr(st, 'secrets') and 'google_oauth' in st.secrets:
                from google.oauth2.credentials import Credentials as OAuthCredentials
                from google.auth.transport.requests import Request

                oauth_info = st.secrets['google_oauth']
                creds = OAuthCredentials(
                    token=None,
                    refresh_token=oauth_info['refresh_token'],
                    token_uri=oauth_info['token_uri'],
                    client_id=oauth_info['client_id'],
                    client_secret=oauth_info['client_secret'],
                    scopes=SCOPES
                )
                # Refresh to get valid access token
                creds.refresh(Request())
                print("Using OAuth refresh token from Streamlit secrets")
        except Exception as e:
            print(f"OAuth from secrets failed: {e}")

        # Method 2: Try Streamlit secrets service account (fallback - may have storage quota issues)
        if not creds:
            try:
                if hasattr(st, 'secrets') and 'gcp_service_account' in st.secrets:
                    creds = Credentials.from_service_account_info(
                        dict(st.secrets['gcp_service_account']),
                        scopes=SCOPES
                    )
                    print("Using service account from Streamlit secrets")
            except Exception as e:
                print(f"Service account from secrets failed: {e}")

        # Method 3: Try OAuth2 (for local development with USE_OAUTH=True)
        if not creds and config.USE_OAUTH:
            import oauth_drive

            drive_service, sheets_service_api = oauth_drive.get_google_services_oauth()

            if drive_service and sheets_service_api:
                # Get credentials for gspread
                import pickle
                if os.path.exists('token.pickle'):
                    with open('token.pickle', 'rb') as token:
                        creds = pickle.load(token)
                        sheets_client = gspread.authorize(creds)
                        return sheets_client, drive_service, creds

        # Method 3: Try local credentials.json file (service account)
        if not creds and os.path.exists(config.CREDENTIALS_FILE):
            try:
                creds = Credentials.from_service_account_file(
                    config.CREDENTIALS_FILE,
                    scopes=SCOPES
                )
                print("Using service account from local file")
            except Exception as e:
                print(f"Service account from file failed: {e}")

        # Method 4: Try environment variable (for Vercel/other hosts)
        if not creds:
            try:
                import json
                google_creds = os.environ.get('GOOGLE_CREDENTIALS')
                if google_creds:
                    creds_dict = json.loads(google_creds)
                    creds = Credentials.from_service_account_info(
                        creds_dict,
                        scopes=SCOPES
                    )
                    print("Using service account from environment variable")
            except Exception as e:
                print(f"Environment variable credentials failed: {e}")

        # If we have credentials, create services
        if creds:
            sheets_client = gspread.authorize(creds)
            drive_service = build('drive', 'v3', credentials=creds)
            return sheets_client, drive_service, creds

        # No credentials found
        st.error("❌ No valid credentials found!")
        st.info("""
        **For Streamlit Cloud:** Add gcp_service_account to your secrets.
        **For local development:** Use credentials.json or token.pickle.
        """)
        return None, None, None

    except Exception as e:
        st.error(f"❌ Error initializing Google services: {str(e)}")
        return None, None, None

# Google Sheets Manager
class GoogleSheetsManager:
    def __init__(self, client):
        self.client = client

    def setup_spreadsheet(self):
        """Setup spreadsheet with required sheets and headers"""
        try:
            spreadsheet = self.client.open_by_key(config.SPREADSHEET_ID)

            # Check if 'Users' sheet exists
            try:
                users_sheet = spreadsheet.worksheet('Users')
            except:
                users_sheet = spreadsheet.add_worksheet(title='Users', rows=1000, cols=10)
                users_sheet.append_row([
                    'Email', 'Name', 'Registration Date', 'Last Login', 'Total Events'
                ])

            # All required column headers (add new ones at end to avoid breaking existing rows)
            REQUIRED_HEADERS = [
                'Event ID', 'User Email', 'Academic Year', 'Quarter', 'Program Name',
                'Program Type', 'Program Driven By', 'Activity Led By', 'Program Theme',
                'Organizing Departments', 'Professional Society Club',
                'SDG Goals', 'Program Outcomes',
                'Duration (Hrs)', 'Event Level', 'Mode of Delivery', 'Venue Platform', 'Start Date', 'End Date',
                'Student Participants', 'Faculty Participants', 'External Participants',
                'Expenditure Amount', 'Remark', 'Objective', 'Benefits',
                'Speaker Names', 'Speaker Designation', 'Speaker Organization', 'Speaker Brief',
                'Session Video URL',
                'Brief Report', 'Key Highlights', 'Outcome', 'Feedback Reflection', 'Organizing Team',
                'Geotag_Photo1_ID', 'Geotag_Photo2_ID', 'Geotag_Photo3_ID',
                'Normal_Photo1_ID', 'Normal_Photo2_ID', 'Normal_Photo3_ID',
                'Attendance_Report_ID', 'Feedback_Analysis_ID', 'Event_Agenda_ID',
                'Chief_Guest_Biodata_ID', 'Permission_SOP_ID', 'Invitation_Brochure_ID',
                'Other_Documents_ID', 'KPI_Report_ID', 'Generated_PDF_ID', 'Signed_PDF_ID',
                'Twitter URL', 'Facebook URL', 'Instagram URL', 'LinkedIn URL',
                'Created Date', 'Last Modified', 'Status', 'Admin_Approval_Status',
                'Approval_Date', 'Approved_By', 'Rejection_Reason', 'Drive Folder URL'
            ]

            # Check if 'Events' sheet exists
            try:
                events_sheet = spreadsheet.worksheet('Events')
                # Auto-add any missing headers to existing sheet
                current_headers = events_sheet.row_values(1)
                missing = [h for h in REQUIRED_HEADERS if h not in current_headers]
                if missing:
                    for h in missing:
                        current_headers.append(h)
                        events_sheet.update_cell(1, len(current_headers), h)
            except:
                events_sheet = spreadsheet.add_worksheet(title='Events', rows=1000, cols=70)
                events_sheet.append_row(REQUIRED_HEADERS)

            return spreadsheet, users_sheet, events_sheet
        except Exception as e:
            st.error(f"Error setting up spreadsheet:")
            st.error(f"Details: {str(e)}")
            st.info("Try refreshing the page or re-authenticating")
            return None, None, None

    def verify_user(self, email, is_admin_login=False):
        """Verify if user exists in the Users sheet or auto-register if from allowed domain"""
        try:
            email = email.lower().strip()

            # Check if admin email (admin login is handled separately)
            if email == config.ADMIN_EMAIL.lower() and not is_admin_login:
                # Admin must use admin login with password
                return False, False

            spreadsheet, users_sheet, _ = self.setup_spreadsheet()
            if users_sheet:
                emails = [e.lower() for e in users_sheet.col_values(1)[1:]]  # Skip header, lowercase

                if email in emails:
                    # User exists - update last login
                    row_index = emails.index(email) + 2
                    users_sheet.update_cell(row_index, 4, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                    return True, False  # Valid user, not admin

                # Check if email is from allowed domain - auto-register
                if hasattr(config, 'ALLOWED_EMAIL_DOMAIN') and config.ALLOWED_EMAIL_DOMAIN:
                    if email.endswith(f"@{config.ALLOWED_EMAIL_DOMAIN}"):
                        # Auto-register new user
                        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        users_sheet.append_row([email, now, 'Active', now])
                        st.success(f"Welcome! Your account has been automatically created.")
                        return True, False  # New user registered

            return False, False
        except Exception as e:
            st.error(f"Error verifying user: {str(e)}")
            return False, False

    def verify_admin(self, email, password):
        """Verify admin credentials"""
        try:
            email = email.lower().strip()
            if email == config.ADMIN_EMAIL.lower() and password == config.ADMIN_PASSWORD:
                return True
            return False
        except:
            return False

    def get_all_events(self):
        """Get all events (for admin)"""
        try:
            spreadsheet, _, events_sheet = self.setup_spreadsheet()
            if events_sheet:
                all_values = events_sheet.get_all_values()
                if len(all_values) < 2:
                    return []

                headers = all_values[0]
                all_events = []
                for row_values in all_values[1:]:
                    event_dict = dict(zip(headers, row_values))
                    all_events.append(event_dict)

                return all_events
            return []
        except Exception as e:
            st.error(f"Error loading all events: {str(e)}")
            return []

    def get_user_events(self, email):
        """Get all events for a specific user"""
        try:
            spreadsheet, _, events_sheet = self.setup_spreadsheet()
            if events_sheet:
                all_values = events_sheet.get_all_values()
                if len(all_values) < 2:
                    return []

                headers = all_values[0]
                user_email_col = headers.index('User Email') if 'User Email' in headers else 1

                user_events = []
                for row_values in all_values[1:]:
                    if len(row_values) > user_email_col and row_values[user_email_col] == email:
                        event_dict = dict(zip(headers, row_values))
                        user_events.append(event_dict)

                return user_events
            return []
        except Exception as e:
            st.error(f"Error fetching user events: {str(e)}")
            return []

    def get_event_by_id(self, event_id):
        """Get specific event by ID"""
        try:
            spreadsheet, _, events_sheet = self.setup_spreadsheet()
            if events_sheet:
                all_values = events_sheet.get_all_values()
                if len(all_values) < 2:
                    return None, None

                headers = all_values[0]
                event_id_col = headers.index('Event ID') if 'Event ID' in headers else 0

                for idx, row_values in enumerate(all_values[1:], start=2):
                    if len(row_values) > event_id_col and row_values[event_id_col] == event_id:
                        event_dict = dict(zip(headers, row_values))
                        return event_dict, idx  # Return event and row number

            return None, None
        except Exception as e:
            st.error(f"Error fetching event: {str(e)}")
            return None, None

    def save_event(self, event_data):
        """Save event data to Google Sheets"""
        try:
            spreadsheet, _, events_sheet = self.setup_spreadsheet()
            if events_sheet:
                event_id = event_data.get('Event ID')

                # Get all values instead of records to avoid duplicate header issue
                all_values = events_sheet.get_all_values()

                if len(all_values) < 1:
                    return False

                headers = list(all_values[0])

                # Auto-add any new column headers that don't exist yet
                new_keys = [k for k in event_data.keys() if k not in headers]
                if new_keys:
                    for key in new_keys:
                        headers.append(key)
                        events_sheet.update_cell(1, len(headers), key)

                # Check if event exists (for updates)
                event_id_col = headers.index('Event ID') if 'Event ID' in headers else 0

                for idx, row_values in enumerate(all_values[1:], start=2):  # Start from row 2
                    if len(row_values) > event_id_col and row_values[event_id_col] == event_id:
                        # Update existing event
                        values = [event_data.get(header, '') for header in headers]

                        # Update the entire row - use row notation
                        events_sheet.update(f'{idx}:{idx}', [values], value_input_option='RAW')
                        return True

                # Add new event - ensure values match header order
                values = [event_data.get(header, '') for header in headers]
                events_sheet.append_row(values, value_input_option='RAW')
                return True
            return False
        except Exception as e:
            st.error(f"Error saving event: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

    def delete_event(self, event_id):
        """Delete an event"""
        try:
            spreadsheet, _, events_sheet = self.setup_spreadsheet()
            if events_sheet:
                all_data = events_sheet.get_all_records()
                for idx, row in enumerate(all_data):
                    if row.get('Event ID') == event_id:
                        row_index = idx + 2
                        events_sheet.delete_rows(row_index)
                        return True
            return False
        except Exception as e:
            st.error(f"Error deleting event: {str(e)}")
            return False

    def update_event_pdf_id(self, event_id, pdf_id):
        """Update the PDF ID for an event (used for regeneration)"""
        try:
            spreadsheet, _, events_sheet = self.setup_spreadsheet()
            if events_sheet:
                headers = events_sheet.row_values(1)
                pdf_col_idx = headers.index('Generated_PDF_ID') + 1 if 'Generated_PDF_ID' in headers else None

                if not pdf_col_idx:
                    return False

                all_data = events_sheet.get_all_values()
                for idx, row in enumerate(all_data[1:], start=2):
                    event_id_col = headers.index('Event ID') if 'Event ID' in headers else 0
                    if row[event_id_col] == event_id:
                        events_sheet.update_cell(idx, pdf_col_idx, pdf_id)
                        return True
            return False
        except Exception as e:
            st.error(f"Error updating PDF ID: {str(e)}")
            return False

    def update_approval_status(self, event_id, status, approval_date, approved_by, rejection_reason=''):
        """Update the approval status for an event"""
        try:
            spreadsheet, _, events_sheet = self.setup_spreadsheet()
            if events_sheet:
                headers = events_sheet.row_values(1)

                # Get column indices
                status_col = headers.index('Admin_Approval_Status') + 1 if 'Admin_Approval_Status' in headers else None
                date_col = headers.index('Approval_Date') + 1 if 'Approval_Date' in headers else None
                by_col = headers.index('Approved_By') + 1 if 'Approved_By' in headers else None
                reason_col = headers.index('Rejection_Reason') + 1 if 'Rejection_Reason' in headers else None

                if not status_col:
                    return False

                all_data = events_sheet.get_all_values()
                for idx, row in enumerate(all_data[1:], start=2):
                    event_id_col = headers.index('Event ID') if 'Event ID' in headers else 0
                    if row[event_id_col] == event_id:
                        events_sheet.update_cell(idx, status_col, status)
                        if date_col:
                            events_sheet.update_cell(idx, date_col, approval_date)
                        if by_col:
                            events_sheet.update_cell(idx, by_col, approved_by)
                        if reason_col:
                            events_sheet.update_cell(idx, reason_col, rejection_reason)
                        return True
            return False
        except Exception as e:
            st.error(f"Error updating approval status: {str(e)}")
            return False

    def update_signed_pdf_id(self, event_id, signed_pdf_id):
        """Update the signed PDF ID for an event"""
        try:
            spreadsheet, _, events_sheet = self.setup_spreadsheet()
            if events_sheet:
                headers = events_sheet.row_values(1)

                # Check if Signed_PDF_ID column exists, if not add it
                if 'Signed_PDF_ID' not in headers:
                    # Add the column header
                    next_col = len(headers) + 1
                    events_sheet.update_cell(1, next_col, 'Signed_PDF_ID')
                    headers.append('Signed_PDF_ID')

                signed_col = headers.index('Signed_PDF_ID') + 1

                all_data = events_sheet.get_all_values()
                for idx, row in enumerate(all_data[1:], start=2):
                    event_id_col = headers.index('Event ID') if 'Event ID' in headers else 0
                    if row[event_id_col] == event_id:
                        events_sheet.update_cell(idx, signed_col, signed_pdf_id)
                        return True
            return False
        except Exception as e:
            st.error(f"Error updating signed PDF ID: {str(e)}")
            return False

# Google Drive Manager
class GoogleDriveManager:
    def __init__(self, service):
        self.service = service

    def create_event_folder(self, event_name, parent_folder_id=None):
        """Create a folder for the event in Google Drive"""
        try:
            folder_metadata = {
                'name': event_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }

            # If parent folder ID is provided, nest the folder
            if parent_folder_id and parent_folder_id != "YOUR_DRIVE_FOLDER_ID_HERE":
                folder_metadata['parents'] = [parent_folder_id]

            folder = self.service.files().create(
                body=folder_metadata,
                fields='id, webViewLink',
                supportsAllDrives=True
            ).execute()

            # Make folder publicly viewable
            try:
                self.service.permissions().create(
                    fileId=folder.get('id'),
                    body={'type': 'anyone', 'role': 'reader'},
                    supportsAllDrives=True
                ).execute()
            except:
                # If permission setting fails, folder is still created
                pass

            return folder.get('id'), folder.get('webViewLink')
        except Exception as e:
            st.error(f"Error creating folder: {str(e)}")
            return None, None

    def upload_to_imgbb(self, file_data, file_name):
        """Upload image to ImgBB (free image hosting - no Drive needed!)"""
        try:
            import requests
            import base64

            if not config.IMGBB_API_KEY:
                return None

            # Convert to base64
            image_base64 = base64.b64encode(file_data).decode('utf-8')

            # Upload to ImgBB
            url = "https://api.imgbb.com/1/upload"
            payload = {
                "key": config.IMGBB_API_KEY,
                "image": image_base64,
                "name": file_name
            }

            response = requests.post(url, data=payload, timeout=30)

            if response.status_code == 200:
                result = response.json()
                return result['data']['url']
            else:
                return None

        except Exception as e:
            return None

    def upload_file(self, file_data, file_name, folder_id, mime_type):
        """Upload file to Google Drive (works with OAuth2!)"""
        try:
            # If OAuth is enabled, upload directly to Google Drive
            if config.USE_OAUTH:
                import oauth_drive
                from io import BytesIO

                file_stream = BytesIO(file_data)
                drive_url = oauth_drive.upload_to_drive_oauth(
                    self.service,
                    file_stream,
                    file_name,
                    folder_id
                )

                if drive_url:
                    st.success(f"✅ {file_name} uploaded to Google Drive!")
                    return drive_url
                else:
                    st.error(f"❌ Failed to upload {file_name} to Drive")
                    return None

            # Fallback: Try ImgBB for images if API key is configured
            elif mime_type.startswith('image/') and config.IMGBB_API_KEY:
                imgbb_url = self.upload_to_imgbb(file_data, file_name)
                if imgbb_url:
                    st.success(f"✅ {file_name} uploaded to ImgBB!")
                    return imgbb_url

            # Last resort: Store locally
            import os
            backup_folder = "uploaded_files_backup"
            if not os.path.exists(backup_folder):
                os.makedirs(backup_folder)

            file_path = os.path.join(backup_folder, file_name)
            with open(file_path, 'wb') as f:
                f.write(file_data)

            st.warning(f"📁 {file_name} saved locally (accessible on server)")
            return f"LOCAL:{file_path}"

        except Exception as e:
            st.error(f"Error uploading {file_name}: {str(e)}")
            return None

    def find_file_id_by_name_prefix(self, name_prefix, folder_id):
        """Search a Drive folder for a file whose name starts with name_prefix. Returns file ID or None."""
        try:
            query = f"'{folder_id}' in parents and name contains '{name_prefix}' and trashed = false"
            result = self.service.files().list(
                q=query,
                fields="files(id, name)",
                supportsAllDrives=True,
                includeItemsFromAllDrives=True
            ).execute()
            files = result.get('files', [])
            if files:
                return files[0]['id']
            return None
        except Exception:
            return None

    def download_file(self, file_id_or_url):
        """Download file from Google Drive by file ID or URL"""
        import re
        import requests
        import logging
        from io import BytesIO
        from googleapiclient.http import MediaIoBaseDownload

        logger = logging.getLogger(__name__)

        # Store last error for debugging
        self.last_download_error = None

        try:
            if not file_id_or_url or file_id_or_url == '' or file_id_or_url == 'null':
                self.last_download_error = "Empty file ID"
                logger.warning(f"Download failed: Empty file ID")
                return None

            original_input = str(file_id_or_url).strip()
            file_id = original_input
            logger.info(f"Attempting to download: {original_input[:60]}")

            # Check if it's a Drive URL and extract the ID
            if 'drive.google.com' in file_id or 'docs.google.com' in file_id:
                # Try multiple patterns for Google Drive URLs
                patterns = [
                    r'/file/d/([a-zA-Z0-9_-]+)',   # /file/d/FILE_ID/view
                    r'/d/([a-zA-Z0-9_-]+)',         # /d/FILE_ID
                    r'id=([a-zA-Z0-9_-]+)',         # id=FILE_ID
                    r'open\?id=([a-zA-Z0-9_-]+)',   # open?id=FILE_ID
                ]

                extracted = False
                for pattern in patterns:
                    match = re.search(pattern, file_id)
                    if match:
                        file_id = match.group(1)
                        extracted = True
                        logger.info(f"Extracted file ID from URL: {file_id}")
                        break

                if not extracted:
                    self.last_download_error = f"Could not extract ID from URL"
                    logger.warning(f"Could not extract ID from URL: {original_input}")
                    return None

            # Clean the file_id - remove any extra characters
            if '/' in file_id:
                file_id = file_id.split('/')[0]
            if '?' in file_id:
                file_id = file_id.split('?')[0]
            file_id = file_id.strip()

            if not file_id or len(file_id) < 10:
                self.last_download_error = f"Invalid file ID (too short): {file_id}"
                logger.warning(f"Invalid file ID: {file_id}")
                return None

            logger.info(f"Using file ID: {file_id}")

            # Method 1: Try Google Drive API
            api_error_msg = None
            try:
                logger.info(f"Trying Drive API download for: {file_id}")
                request = self.service.files().get_media(fileId=file_id)
                file_data = BytesIO()
                downloader = MediaIoBaseDownload(file_data, request)

                done = False
                while not done:
                    status, done = downloader.next_chunk()

                file_data.seek(0)
                content = file_data.read()

                if content and len(content) > 0:
                    logger.info(f"Drive API success: {len(content)} bytes downloaded")
                    return content
                else:
                    api_error_msg = "API returned empty content"
                    logger.warning(f"API returned empty content for: {file_id}")
            except Exception as api_error:
                api_error_msg = str(api_error)[:100]
                logger.warning(f"Drive API error: {api_error_msg}")

            # Method 2: Try direct download URL (for public files)
            try:
                download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
                logger.info(f"Trying direct URL download: {download_url}")
                response = requests.get(download_url, timeout=30)
                if response.status_code == 200 and len(response.content) > 100:
                    # Check if it's HTML (error page) instead of actual file
                    if not response.content[:20].startswith(b'<!'):
                        logger.info(f"Direct URL success: {len(response.content)} bytes")
                        return response.content
                    else:
                        logger.warning(f"Direct URL returned HTML instead of file")
                else:
                    logger.warning(f"Direct URL failed: status={response.status_code}, size={len(response.content)}")
            except Exception as req_error:
                logger.warning(f"Direct URL error: {str(req_error)[:50]}")

            self.last_download_error = f"API: {api_error_msg}"
            logger.error(f"All download methods failed for: {file_id}")
            return None

        except Exception as e:
            self.last_download_error = str(e)[:100]
            logger.error(f"Download exception: {str(e)[:100]}")
            return None

    def get_or_create_event_folder(self, event_name, event_id, parent_folder_id=None):
        """Get existing folder or create new one"""
        import time

        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Search for existing folder by name
                query = f"name='{event_name}' and mimeType='application/vnd.google-apps.folder'"
                if parent_folder_id and parent_folder_id != "YOUR_DRIVE_FOLDER_ID_HERE":
                    query += f" and '{parent_folder_id}' in parents"

                results = self.service.files().list(
                    q=query,
                    spaces='drive',
                    fields='files(id, webViewLink)',
                    supportsAllDrives=True,
                    includeItemsFromAllDrives=True
                ).execute()

                folders = results.get('files', [])

                if folders:
                    # Return existing folder
                    return folders[0]['id'], folders[0].get('webViewLink', '')
                else:
                    # Create new folder
                    return self.create_event_folder(event_name, parent_folder_id)

            except Exception as e:
                if attempt < max_retries - 1:
                    st.warning(f"Retry {attempt + 1}/{max_retries} - Connection issue, retrying...")
                    time.sleep(2)  # Wait 2 seconds before retry
                else:
                    st.error(f"Error with folder after {max_retries} attempts: {str(e)}")
                    # Last resort - try to create folder
                    try:
                        return self.create_event_folder(event_name, parent_folder_id)
                    except:
                        # If all fails, return None
                        return None, None

# Utility Functions
class ValidationUtils:
    @staticmethod
    def get_quarter_from_date(date):
        """Automatically determine quarter from date"""
        month = date.month
        if 9 <= month <= 11:
            return "Quarter 1 (1st September - 30th November)"
        elif 12 <= month or month <= 2:
            return "Quarter 2 (1st December - 28th February)"
        elif 3 <= month <= 5:
            return "Quarter 3 (1st March - 31st May)"
        else:
            return "Quarter 4 (1st June - 31st August)"

    @staticmethod
    def get_level_from_duration(duration):
        """Automatically determine level based on duration"""
        if duration >= 18:
            return "Level 4", 4
        elif duration >= 9:
            return "Level 3", 3
        elif duration >= 5:
            return "Level 2", 2
        else:
            return "Level 1", 1

    @staticmethod
    def extract_image_date(image_file):
        """Extract date from image EXIF metadata"""
        try:
            image = Image.open(image_file)
            exif_data = image._getexif()

            if exif_data:
                for tag_id, value in exif_data.items():
                    tag = TAGS.get(tag_id, tag_id)
                    if tag == "DateTimeOriginal":
                        return datetime.strptime(value, '%Y:%m:%d %H:%M:%S')
            return None
        except:
            return None

    @staticmethod
    def validate_image_date(image_file, event_date, tolerance_days=7):
        """Validate if image date matches event date"""
        image_date = ValidationUtils.extract_image_date(image_file)
        if image_date:
            diff = abs((image_date.date() - event_date).days)
            return diff <= tolerance_days, image_date
        return True, None  # If no EXIF data, skip validation

    @staticmethod
    def count_words(text):
        """Count words in text"""
        return len(text.split())

    @staticmethod
    def generate_event_id(email, event_name):
        """Generate unique event ID"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        hash_input = f"{email}_{event_name}_{timestamp}"
        return hashlib.md5(hash_input.encode()).hexdigest()[:12].upper()

# Main Application
def main():
    # Initialize Google services
    sheets_client, drive_service, creds = init_google_services()

    if not sheets_client or not drive_service:
        st.error("Failed to initialize Google services. Please check your credentials.")
        st.stop()

    # Sidebar
    with st.sidebar:
        # Display HIVE logo
        if os.path.exists("logos/hive.png"):
            st.image("logos/hive.png", width=120)
        st.markdown("### SRIT IIC Portal")
        st.caption("Developed & Maintained by HIVE")

        st.markdown("---")

        st.markdown("**Ministry of Education**")
        st.markdown("Institution's Innovation Council")
        st.markdown("*Academic Year 2025-26*")

        st.markdown("---")

        if st.session_state.authenticated:
            if st.session_state.is_admin:
                st.success("Admin Access")
            else:
                st.success("Logged In")
            st.markdown(f"**{st.session_state.user_email}**")

            st.markdown("---")

            if st.button("Logout", use_container_width=True):
                st.session_state.authenticated = False
                st.session_state.user_email = None
                st.session_state.is_admin = False
                st.session_state.edit_mode = False
                st.session_state.edit_event_data = None
                st.session_state.ia_portal_mode = False
                st.rerun()

            # Admin Token Management - Only for admin
            if st.session_state.is_admin and config.USE_OAUTH:
                st.markdown("---")
                st.markdown("**Admin Tools**")

                # Show token status
                try:
                    import oauth_drive
                    token_info = oauth_drive.get_token_info()
                    if token_info:
                        if token_info['valid']:
                            st.success("Token: Valid")
                        elif token_info['has_refresh_token']:
                            st.warning("Token: Will auto-refresh")
                        else:
                            st.error("Token: Expired")
                        st.caption(f"Expiry: {token_info['expiry']}")
                except:
                    pass

                # Generate token for Streamlit secrets
                with st.expander("Token Management"):
                    if st.button("Generate Token for Secrets", use_container_width=True):
                        try:
                            import oauth_drive
                            token_b64 = oauth_drive.generate_token_for_secrets()
                            if token_b64:
                                st.code(f"token_pickle_base64 = \"{token_b64}\"", language="toml")
                                st.info("Copy the above and paste in Streamlit Cloud Secrets")
                            else:
                                st.error("No token.pickle file found")
                        except Exception as e:
                            st.error(f"Error: {str(e)}")

                    # Upload new token
                    uploaded_token = st.file_uploader("Upload new token.pickle", type=['pickle'], key="token_upload")
                    if uploaded_token:
                        try:
                            with open('token.pickle', 'wb') as f:
                                f.write(uploaded_token.read())
                            st.success("Token updated! Clearing cache...")
                            st.cache_resource.clear()
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {str(e)}")

                    if st.button("Clear Cache & Re-auth", use_container_width=True):
                        st.cache_resource.clear()
                        if os.path.exists('token.pickle'):
                            os.remove('token.pickle')
                        st.success("Cache cleared! Refresh page to re-authenticate.")
                        st.stop()

    # Main content - Public landing page with tabs
    main_page(sheets_client, drive_service)

def main_page(sheets_client, drive_service):
    """Main page with public tabs and IA Portal access"""

    # Check if we need to redirect to edit mode (only if authenticated)
    if st.session_state.get('edit_mode', False) and st.session_state.get('edit_event_data') and st.session_state.authenticated:
        st.info("Editing Event - Make your changes below and save.")
        col1, col2 = st.columns([6, 1])
        with col2:
            if st.button("Cancel Edit", use_container_width=True):
                st.session_state.edit_mode = False
                st.session_state.edit_event_data = None
                st.rerun()
        create_event_form(sheets_client, drive_service)
        return

    # Check if user is in IA Portal mode (logged in and wants to access IA features)
    if st.session_state.get('ia_portal_mode', False) and st.session_state.authenticated:
        show_ia_portal(sheets_client, drive_service)
        return

    # Main Public Tabs - visible to everyone
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Home",
        "Upcoming Events",
        "Contact Us",
        "HIVE Ecosystem Enablers",
        "Login as IA"
    ])

    with tab1:
        show_hive_home()

    with tab2:
        show_upcoming_events()

    with tab3:
        show_contact_us()

    with tab4:
        show_hive_ecosystem()

    with tab5:
        show_ia_login(sheets_client, drive_service)


def show_ia_portal(sheets_client, drive_service):
    """IA Portal - accessible after login with My Events and IIC Event Report Submission"""
    # Header with back button
    col1, col2 = st.columns([6, 1])
    with col1:
        st.markdown("""
            <div style="background: linear-gradient(135deg, #1b5e20 0%, #388e3c 100%);
                        color: white; padding: 1.5rem; border-radius: 15px; margin-bottom: 1rem;">
                <h2 style="color: white; margin: 0;">IA Portal</h2>
                <p style="color: #e8f5e9; margin: 0.5rem 0 0 0;">Welcome, {}</p>
            </div>
        """.format(st.session_state.user_email), unsafe_allow_html=True)
    with col2:
        if st.button("Back to Main", use_container_width=True):
            st.session_state.ia_portal_mode = False
            st.rerun()

    # IA Portal Tabs
    if st.session_state.is_admin:
        # Admin has additional tabs
        ia_tab1, ia_tab2, ia_tab3, ia_tab4 = st.tabs([
            "📊 Dashboard",
            "📝 Submit Event",
            "📁 My Events",
            "🔧 All Reports (Admin)"
        ])

        with ia_tab1:
            show_admin_dashboard(sheets_client)

        with ia_tab2:
            create_event_form(sheets_client, drive_service)

        with ia_tab3:
            show_user_events(sheets_client)

        with ia_tab4:
            show_all_events_admin(sheets_client, drive_service)
    else:
        # Regular IA user
        ia_tab1, ia_tab2, ia_tab3 = st.tabs([
            "📊 Dashboard",
            "📝 Submit Event",
            "📁 My Events"
        ])

        with ia_tab1:
            show_dashboard(sheets_client)

        with ia_tab2:
            create_event_form(sheets_client, drive_service)

        with ia_tab3:
            show_user_events(sheets_client)


def show_ia_login(sheets_client, drive_service):
    """Show IA Login page with login form or redirect to IA Portal"""
    if st.session_state.authenticated:
        # Already logged in - show entry to IA Portal
        st.markdown("""
            <div style="background: linear-gradient(135deg, #1b5e20 0%, #388e3c 100%);
                        color: white; padding: 2rem; border-radius: 15px; text-align: center; margin-bottom: 1.5rem;">
                <h2 style="color: white; margin-bottom: 0.5rem;">Welcome, Innovation Ambassador!</h2>
                <p style="color: #e8f5e9;">You are logged in as: {}</p>
            </div>
        """.format(st.session_state.user_email), unsafe_allow_html=True)

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("""
                <div style="background: white; padding: 1.5rem; border-radius: 10px; border: 2px solid #c8e6c9; text-align: center;">
                    <h4 style="color: #2e7d32; margin-bottom: 1rem;">Access IA Portal</h4>
                    <p style="color: #333;">Submit IIC Event Reports and manage your events</p>
                </div>
            """, unsafe_allow_html=True)

            if st.button("Enter IA Portal", type="primary", use_container_width=True):
                st.session_state.ia_portal_mode = True
                st.rerun()

            st.markdown("---")
            st.info("As an Innovation Ambassador, you can submit event reports and track your submissions.")
    else:
        # Not logged in - show login form
        st.markdown("""
            <div style="background: linear-gradient(135deg, #1b5e20 0%, #388e3c 100%);
                        color: white; padding: 2rem; border-radius: 15px; text-align: center; margin-bottom: 1.5rem;">
                <h2 style="color: white; margin-bottom: 0.5rem;">Login as Innovation Ambassador</h2>
                <p style="color: #e8f5e9;">Access IIC Event Report Submission and manage your events</p>
            </div>
        """, unsafe_allow_html=True)

        col1, col2, col3 = st.columns([1, 2, 1])

        with col2:
            # Create tabs for User and Admin login
            login_tab1, login_tab2 = st.tabs(["IA Login", "Admin Login"])

            with login_tab1:
                st.markdown("#### Innovation Ambassador Login")
                st.info(f"Users with @{config.ALLOWED_EMAIL_DOMAIN} email are automatically registered")

                user_email = st.text_input(
                    "Email Address",
                    placeholder=f"yourname@{config.ALLOWED_EMAIL_DOMAIN}",
                    key="ia_user_login_email"
                )

                if st.button("Login", type="primary", use_container_width=True, key="ia_user_login_btn"):
                    if user_email:
                        # Validate email domain
                        if not user_email.lower().endswith(f"@{config.ALLOWED_EMAIL_DOMAIN}"):
                            st.error(f"Please use your @{config.ALLOWED_EMAIL_DOMAIN} email address")
                        else:
                            try:
                                sheets_manager = GoogleSheetsManager(sheets_client)
                                is_valid, _ = sheets_manager.verify_user(user_email)
                                if is_valid:
                                    st.session_state.authenticated = True
                                    st.session_state.user_email = user_email.lower()
                                    st.session_state.is_admin = False
                                    st.session_state.ia_portal_mode = True
                                    st.success("Login successful! Redirecting to IA Portal...")
                                    st.rerun()
                                else:
                                    st.error("Login failed. Please try again.")
                            except Exception as e:
                                st.error(f"Login failed: {str(e)}")
                    else:
                        st.warning("Please enter your email address.")

            with login_tab2:
                st.markdown("#### Admin Login")
                st.warning("Admin access only - requires password")

                admin_email = st.text_input(
                    "Admin Email",
                    placeholder="hive@sritcbe.ac.in",
                    key="ia_admin_login_email"
                )

                admin_password = st.text_input(
                    "Password",
                    type="password",
                    placeholder="Enter admin password",
                    key="ia_admin_login_password"
                )

                if st.button("Login as Admin", type="primary", use_container_width=True, key="ia_admin_login_btn"):
                    if admin_email and admin_password:
                        try:
                            sheets_manager = GoogleSheetsManager(sheets_client)
                            if sheets_manager.verify_admin(admin_email, admin_password):
                                st.session_state.authenticated = True
                                st.session_state.user_email = admin_email.lower()
                                st.session_state.is_admin = True
                                st.session_state.ia_portal_mode = True
                                st.success("Admin login successful! Redirecting to IA Portal...")
                                st.rerun()
                            else:
                                st.error("Invalid admin credentials")
                        except Exception as e:
                            st.error(f"Login failed: {str(e)}")
                    else:
                        st.warning("Please enter both email and password.")

            st.markdown("---")
            st.markdown("""
                <div style="background: #f1f8e9; padding: 1rem; border-radius: 8px; text-align: center;">
                    <p style="color: #333; margin: 0;"><strong style="color: #2e7d32;">What is an Innovation Ambassador?</strong></p>
                    <p style="color: #666; font-size: 0.9rem; margin: 0.5rem 0 0 0;">
                        IAs are faculty members who coordinate and report IIC activities for their departments.
                    </p>
                </div>
            """, unsafe_allow_html=True)


def show_upcoming_events():
    """Display upcoming events page"""
    st.markdown("""
        <div style="background: linear-gradient(135deg, #1b5e20 0%, #388e3c 100%);
                    color: white; padding: 2rem; border-radius: 15px; text-align: center; margin-bottom: 1.5rem;">
            <h2 style="color: white; margin-bottom: 0.5rem;">Upcoming Events</h2>
            <p style="color: #e8f5e9;">Stay updated with HIVE's upcoming innovation activities</p>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div style="background: #fff8e1; border: 1px solid #ffe082; border-radius: 12px; padding: 1.5rem; margin-bottom: 1.5rem; text-align: center;">
            <p style="color: #f57f17; font-size: 1.1rem; margin: 0;">
                📅 Upcoming event announcements are shared through the HIVE newsletter and social media channels.
                Check back here for updates, or contact us directly.
            </p>
        </div>
    """, unsafe_allow_html=True)

    # IIC Activity categories for 2026-27
    st.markdown("""
        <h4 style="color: #1b5e20; font-size: 1.3rem; font-weight: 600; margin: 1.5rem 0 1rem 0;
                   border-left: 4px solid #4caf50; padding-left: 12px;">IIC Activity Plan – Academic Year 2026-27</h4>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div style="background: #e8f5e9; border-radius: 10px; padding: 1rem; margin: 0.5rem 0;">
            <h5 style="color: #2e7d32; margin-bottom: 0.8rem;">Quarter 1 (Jul–Sep)</h5>
            <p style="color:#333; font-size:0.9rem; margin:0.3rem 0;">• Orientation &amp; Onboarding Workshop</p>
            <p style="color:#333; font-size:0.9rem; margin:0.3rem 0;">• Design Thinking Session</p>
            <p style="color:#333; font-size:0.9rem; margin:0.3rem 0;">• Club Induction Programs</p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div style="background: #e3f2fd; border-radius: 10px; padding: 1rem; margin: 0.5rem 0;">
            <h5 style="color: #1565c0; margin-bottom: 0.8rem;">Quarter 2 (Oct–Dec)</h5>
            <p style="color:#333; font-size:0.9rem; margin:0.3rem 0;">• Innovation Challenge / Hackathon</p>
            <p style="color:#333; font-size:0.9rem; margin:0.3rem 0;">• Expert Talks &amp; Alumni Sessions</p>
            <p style="color:#333; font-size:0.9rem; margin:0.3rem 0;">• IPR &amp; Patent Awareness</p>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div style="background: #fff3e0; border-radius: 10px; padding: 1rem; margin: 0.5rem 0;">
            <h5 style="color: #e65100; margin-bottom: 0.8rem;">Quarter 3 (Jan–Mar)</h5>
            <p style="color:#333; font-size:0.9rem; margin:0.3rem 0;">• Startup Bootcamp</p>
            <p style="color:#333; font-size:0.9rem; margin:0.3rem 0;">• Mentoring Sessions</p>
            <p style="color:#333; font-size:0.9rem; margin:0.3rem 0;">• ATL School Outreach</p>
        </div>
        """, unsafe_allow_html=True)

    # Call to action
    st.markdown("---")
    st.markdown("""
        <div style="background: #f1f8e9; padding: 1.5rem; border-radius: 10px; text-align: center;">
            <h4 style="color: #2e7d32; margin-bottom: 0.5rem;">Organising an event?</h4>
            <p style="color: #333; margin-bottom: 0.5rem;">Login as an Innovation Ambassador to submit your IIC event report.</p>
            <p style="color: #555; font-size: 0.9rem;">For announcements and registrations, contact: <strong>hive@sritcbe.ac.in</strong></p>
        </div>
    """, unsafe_allow_html=True)


def show_contact_us():
    """Display Contact Us page"""
    st.markdown("""
        <div style="background: linear-gradient(135deg, #1b5e20 0%, #388e3c 100%);
                    color: white; padding: 2rem; border-radius: 15px; text-align: center; margin-bottom: 1.5rem;">
            <h2 style="color: white; margin-bottom: 0.5rem;">Contact Us</h2>
            <p style="color: #e8f5e9;">Get in touch with HIVE team</p>
        </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
            <h4 style="color: #1b5e20; font-size: 1.3rem; font-weight: 600; margin: 1rem 0;
                       border-left: 4px solid #4caf50; padding-left: 12px;">HIVE Office</h4>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div style="background: white; border: 1px solid #c8e6c9; border-radius: 10px; padding: 1.5rem;">
            <p style="color: #333; margin: 0 0 0.5rem 0;"><strong style="color: #2e7d32;">Address:</strong></p>
            <p style="color: #333; margin: 0 0 1rem 0;">
                HIVE - Hub for Innovation, Ventures & Entrepreneurship<br>
                Sri Ramakrishna Institute of Technology<br>
                Pachapalayam, Perur Chettipalayam<br>
                Coimbatore - 641 010<br>
                Tamil Nadu, India
            </p>
            <p style="color: #333; margin: 0 0 0.5rem 0;"><strong style="color: #2e7d32;">Email:</strong> hive@sritcbe.ac.in</p>
            <p style="color: #333; margin: 0 0 0.5rem 0;"><strong style="color: #2e7d32;">Phone:</strong> 0422-2605577</p>
            <p style="color: #333; margin: 0;"><strong style="color: #2e7d32;">Working Hours:</strong> Mon-Sat, 9:00 AM - 5:00 PM</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
            <h4 style="color: #1b5e20; font-size: 1.3rem; font-weight: 600; margin: 1.5rem 0 1rem 0;
                       border-left: 4px solid #4caf50; padding-left: 12px;">Key Contacts</h4>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div style="background: white; border: 1px solid #c8e6c9; border-radius: 10px; padding: 1rem; margin-bottom: 0.5rem;">
            <p style="color: #333; margin: 0;"><strong style="color: #2e7d32;">IIC Coordinator</strong></p>
            <p style="color: #666; font-size: 0.9rem; margin: 0;">iic@sritcbe.ac.in</p>
        </div>
        <div style="background: white; border: 1px solid #c8e6c9; border-radius: 10px; padding: 1rem; margin-bottom: 0.5rem;">
            <p style="color: #333; margin: 0;"><strong style="color: #2e7d32;">SISH - Incubation</strong></p>
            <p style="color: #666; font-size: 0.9rem; margin: 0;">sish@sritcbe.ac.in</p>
        </div>
        <div style="background: white; border: 1px solid #c8e6c9; border-radius: 10px; padding: 1rem;">
            <p style="color: #333; margin: 0;"><strong style="color: #2e7d32;">E-Cell</strong></p>
            <p style="color: #666; font-size: 0.9rem; margin: 0;">ecell@sritcbe.ac.in</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
            <h4 style="color: #1b5e20; font-size: 1.3rem; font-weight: 600; margin: 1rem 0;
                       border-left: 4px solid #4caf50; padding-left: 12px;">Send us a Message</h4>
        """, unsafe_allow_html=True)

        with st.form("contact_form"):
            name = st.text_input("Your Name *")
            email = st.text_input("Your Email *")
            subject = st.selectbox("Subject", [
                "General Inquiry",
                "Event Registration",
                "Startup Incubation",
                "Collaboration Proposal",
                "Technical Support",
                "Other"
            ])
            message = st.text_area("Your Message *", height=150)

            submitted = st.form_submit_button("Send Message", type="primary", use_container_width=True)
            if submitted:
                if name and email and message:
                    st.success("Thank you for your message! We will get back to you soon.")
                else:
                    st.warning("Please fill in all required fields.")

        st.markdown("""
            <h4 style="color: #1b5e20; font-size: 1.3rem; font-weight: 600; margin: 1.5rem 0 1rem 0;
                       border-left: 4px solid #4caf50; padding-left: 12px;">Follow Us</h4>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div style="background: white; border: 1px solid #c8e6c9; border-radius: 10px; padding: 1rem; text-align: center;">
            <p style="color: #333; margin: 0 0 0.5rem 0;">Connect with us on social media</p>
            <p style="color: #2e7d32; font-size: 1.5rem; margin: 0;">
                <a href="#" style="color: #2e7d32; margin: 0 10px; text-decoration: none;">LinkedIn</a> |
                <a href="#" style="color: #2e7d32; margin: 0 10px; text-decoration: none;">Twitter</a> |
                <a href="#" style="color: #2e7d32; margin: 0 10px; text-decoration: none;">Instagram</a>
            </p>
        </div>
        """, unsafe_allow_html=True)


def show_hive_ecosystem():
    """Display HIVE Ecosystem Enablers page"""
    st.markdown("""
        <div style="background: linear-gradient(135deg, #1b5e20 0%, #388e3c 100%);
                    color: white; padding: 2rem; border-radius: 15px; text-align: center; margin-bottom: 1.5rem;">
            <h2 style="color: white; margin-bottom: 0.5rem;">HIVE Ecosystem Enablers</h2>
            <p style="color: #e8f5e9;">Our partners and enablers driving innovation excellence</p>
        </div>
    """, unsafe_allow_html=True)

    # Government Bodies
    st.markdown("""
        <h4 style="color: #1b5e20; font-size: 1.3rem; font-weight: 600; margin: 1.5rem 0 1rem 0;
                   border-left: 4px solid #4caf50; padding-left: 12px;">Government Bodies & Initiatives</h4>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div style="background: white; border: 1px solid #c8e6c9; border-radius: 10px; padding: 1.2rem; text-align: center; height: 180px;">
            <h5 style="color: #2e7d32; margin-bottom: 0.5rem;">Ministry of Education</h5>
            <p style="color: #333; font-size: 0.85rem;">Institution's Innovation Council (IIC) under MoE's Innovation Cell</p>
            <span style="background: #e8f5e9; color: #2e7d32; padding: 4px 12px; border-radius: 15px; font-size: 0.75rem;">IIC Membership</span>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div style="background: white; border: 1px solid #c8e6c9; border-radius: 10px; padding: 1.2rem; text-align: center; height: 180px;">
            <h5 style="color: #2e7d32; margin-bottom: 0.5rem;">AICTE</h5>
            <p style="color: #333; font-size: 0.85rem;">All India Council for Technical Education - Supporting innovation programs</p>
            <span style="background: #e8f5e9; color: #2e7d32; padding: 4px 12px; border-radius: 15px; font-size: 0.75rem;">AICTE Approved</span>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div style="background: white; border: 1px solid #c8e6c9; border-radius: 10px; padding: 1.2rem; text-align: center; height: 180px;">
            <h5 style="color: #2e7d32; margin-bottom: 0.5rem;">Startup India</h5>
            <p style="color: #333; font-size: 0.85rem;">Government of India's flagship initiative for startup ecosystem</p>
            <span style="background: #e8f5e9; color: #2e7d32; padding: 4px 12px; border-radius: 15px; font-size: 0.75rem;">Registered Hub</span>
        </div>
        """, unsafe_allow_html=True)

    # Industry Partners
    st.markdown("""
        <h4 style="color: #1b5e20; font-size: 1.3rem; font-weight: 600; margin: 1.5rem 0 1rem 0;
                   border-left: 4px solid #4caf50; padding-left: 12px;">Industry Partners</h4>
    """, unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("""
        <div style="background: #f1f8e9; border-radius: 10px; padding: 1rem; text-align: center;">
            <h6 style="color: #2e7d32; margin: 0;">Tech Companies</h6>
            <p style="color: #333; font-size: 0.8rem; margin: 0.5rem 0 0 0;">Software & IT Partners</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div style="background: #f1f8e9; border-radius: 10px; padding: 1rem; text-align: center;">
            <h6 style="color: #2e7d32; margin: 0;">Manufacturing</h6>
            <p style="color: #333; font-size: 0.8rem; margin: 0.5rem 0 0 0;">Industry 4.0 Partners</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div style="background: #f1f8e9; border-radius: 10px; padding: 1rem; text-align: center;">
            <h6 style="color: #2e7d32; margin: 0;">Startups</h6>
            <p style="color: #333; font-size: 0.8rem; margin: 0.5rem 0 0 0;">Alumni Ventures</p>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown("""
        <div style="background: #f1f8e9; border-radius: 10px; padding: 1rem; text-align: center;">
            <h6 style="color: #2e7d32; margin: 0;">Investors</h6>
            <p style="color: #333; font-size: 0.8rem; margin: 0.5rem 0 0 0;">Angel & VC Networks</p>
        </div>
        """, unsafe_allow_html=True)

    # Support Infrastructure
    st.markdown("""
        <h4 style="color: #1b5e20; font-size: 1.3rem; font-weight: 600; margin: 1.5rem 0 1rem 0;
                   border-left: 4px solid #4caf50; padding-left: 12px;">Support Infrastructure</h4>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div style="background: white; border: 1px solid #c8e6c9; border-radius: 10px; padding: 1.2rem;">
            <h5 style="color: #2e7d32; margin-bottom: 0.5rem;">Incubation Facilities</h5>
            <ul style="color: #333; font-size: 0.9rem; margin: 0; padding-left: 1.2rem;">
                <li>Co-working Spaces</li>
                <li>Prototyping Labs</li>
                <li>Meeting Rooms</li>
                <li>High-speed Internet</li>
                <li>24/7 Access for Startups</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div style="background: white; border: 1px solid #c8e6c9; border-radius: 10px; padding: 1.2rem;">
            <h5 style="color: #2e7d32; margin-bottom: 0.5rem;">Mentorship Network</h5>
            <ul style="color: #333; font-size: 0.9rem; margin: 0; padding-left: 1.2rem;">
                <li>Industry Experts</li>
                <li>Successful Entrepreneurs</li>
                <li>Academic Advisors</li>
                <li>Legal & IP Consultants</li>
                <li>Financial Advisors</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    # Funding Support
    st.markdown("""
        <h4 style="color: #1b5e20; font-size: 1.3rem; font-weight: 600; margin: 1.5rem 0 1rem 0;
                   border-left: 4px solid #4caf50; padding-left: 12px;">Funding Support</h4>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="display: flex; gap: 1rem; flex-wrap: wrap; margin: 1rem 0;">
        <div style="flex: 1; min-width: 200px; background: linear-gradient(135deg, #2e7d32 0%, #4caf50 100%);
                    color: white; padding: 1.2rem; border-radius: 10px; text-align: center;">
            <div style="font-size: 1.5rem; font-weight: bold;">Seed Funding</div>
            <div style="font-size: 0.9rem; opacity: 0.9;">Up to Rs. 5 Lakhs</div>
        </div>
        <div style="flex: 1; min-width: 200px; background: linear-gradient(135deg, #2e7d32 0%, #4caf50 100%);
                    color: white; padding: 1.2rem; border-radius: 10px; text-align: center;">
            <div style="font-size: 1.5rem; font-weight: bold;">Pre-Incubation</div>
            <div style="font-size: 0.9rem; opacity: 0.9;">Up to Rs. 1 Lakh</div>
        </div>
        <div style="flex: 1; min-width: 200px; background: linear-gradient(135deg, #2e7d32 0%, #4caf50 100%);
                    color: white; padding: 1.2rem; border-radius: 10px; text-align: center;">
            <div style="font-size: 1.5rem; font-weight: bold;">Innovation Grants</div>
            <div style="font-size: 0.9rem; opacity: 0.9;">Project-based</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Call to action
    st.markdown("---")
    st.markdown("""
        <div style="background: #e8f5e9; padding: 1.5rem; border-radius: 10px; text-align: center;">
            <h4 style="color: #2e7d32; margin-bottom: 0.5rem;">Become an Ecosystem Partner</h4>
            <p style="color: #333; margin-bottom: 0;">Interested in collaborating with HIVE? Contact us at <strong>hive@sritcbe.ac.in</strong></p>
        </div>
    """, unsafe_allow_html=True)

def show_hive_home():
    """Display HIVE Home page with information about HIVE"""
    # Hero Section
    st.markdown("""
        <div style="background: linear-gradient(135deg, #1b5e20 0%, #388e3c 50%, #4caf50 100%);
                    color: white; padding: 2.5rem; border-radius: 15px; text-align: center; margin-bottom: 1.5rem;">
            <h1 style="color: white; font-size: 2.5rem; margin-bottom: 0.5rem;">Welcome to HIVE</h1>
            <p style="color: #e8f5e9; font-size: 1.2rem; margin-bottom: 0.3rem;">Hub for Innovation, Ventures & Entrepreneurship</p>
            <p style="color: #c8e6c9; font-size: 1rem;">Sri Ramakrishna Institute of Technology, Coimbatore</p>
        </div>
    """, unsafe_allow_html=True)

    # About HIVE Section
    st.markdown("""
        <h4 style="color: #1b5e20; font-size: 1.3rem; font-weight: 600; margin: 1.5rem 0 1rem 0;
                   border-left: 4px solid #4caf50; padding-left: 12px;">About HIVE</h4>
    """, unsafe_allow_html=True)
    st.markdown("""
        <div style="background: white; padding: 1.2rem; border-radius: 10px; border: 1px solid #e0e0e0; margin-bottom: 1rem;">
            <p style="color: #333; font-size: 1rem; line-height: 1.6; margin: 0;">
                <strong style="color: #2e7d32;">HIVE (Hub for Innovation, Ventures & Entrepreneurship)</strong> is the central innovation ecosystem at
                Sri Ramakrishna Institute of Technology (SRIT), established to foster creativity, entrepreneurship,
                and technological advancement among students and faculty.
            </p>
            <p style="color: #333; font-size: 1rem; line-height: 1.6; margin: 1rem 0 0 0;">
                HIVE serves as a comprehensive platform that integrates various innovation initiatives including
                the Institution's Innovation Council (IIC), SRIT Innovation & Start-up Hub (SISH), and other
                entrepreneurship development programs under one umbrella.
            </p>
        </div>
    """, unsafe_allow_html=True)

    # Key Functions
    st.markdown("""
        <h4 style="color: #1b5e20; font-size: 1.3rem; font-weight: 600; margin: 1.5rem 0 1rem 0;
                   border-left: 4px solid #4caf50; padding-left: 12px;">Key Functions</h4>
    """, unsafe_allow_html=True)
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div style="background: white; border: 1px solid #c8e6c9; border-radius: 10px; padding: 1rem;
                    margin: 0.5rem 0; border-left: 4px solid #4caf50;">
            <h4 style="color: #2e7d32; margin-bottom: 0.5rem; font-size: 1rem;">Innovation & Ideation</h4>
            <p style="color: #333; font-size: 0.9rem; margin: 0;">Nurturing creative ideas through workshops, hackathons, and mentoring sessions.</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div style="background: white; border: 1px solid #c8e6c9; border-radius: 10px; padding: 1rem;
                    margin: 0.5rem 0; border-left: 4px solid #4caf50;">
            <h4 style="color: #2e7d32; margin-bottom: 0.5rem; font-size: 1rem;">Startup Incubation</h4>
            <p style="color: #333; font-size: 0.9rem; margin: 0;">Providing infrastructure, mentorship, and funding support through SISH.</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div style="background: white; border: 1px solid #c8e6c9; border-radius: 10px; padding: 1rem;
                    margin: 0.5rem 0; border-left: 4px solid #4caf50;">
            <h4 style="color: #2e7d32; margin-bottom: 0.5rem; font-size: 1rem;">Industry Collaboration</h4>
            <p style="color: #333; font-size: 0.9rem; margin: 0;">Facilitating partnerships with industries for real-world problem solving.</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div style="background: white; border: 1px solid #c8e6c9; border-radius: 10px; padding: 1rem;
                    margin: 0.5rem 0; border-left: 4px solid #4caf50;">
            <h4 style="color: #2e7d32; margin-bottom: 0.5rem; font-size: 1rem;">IPR & Technology Transfer</h4>
            <p style="color: #333; font-size: 0.9rem; margin: 0;">Supporting patent filing, copyright registration, and commercialization.</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div style="background: white; border: 1px solid #c8e6c9; border-radius: 10px; padding: 1rem;
                    margin: 0.5rem 0; border-left: 4px solid #4caf50;">
            <h4 style="color: #2e7d32; margin-bottom: 0.5rem; font-size: 1rem;">Skill Development</h4>
            <p style="color: #333; font-size: 0.9rem; margin: 0;">Conducting training programs on design thinking and emerging technologies.</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div style="background: white; border: 1px solid #c8e6c9; border-radius: 10px; padding: 1rem;
                    margin: 0.5rem 0; border-left: 4px solid #4caf50;">
            <h4 style="color: #2e7d32; margin-bottom: 0.5rem; font-size: 1rem;">IIC Activities</h4>
            <p style="color: #333; font-size: 0.9rem; margin: 0;">Implementing MoE's Innovation Cell initiatives and organizing quarterly events.</p>
        </div>
        """, unsafe_allow_html=True)

    # Statistics Section
    st.markdown("""
        <h4 style="color: #1b5e20; font-size: 1.3rem; font-weight: 600; margin: 1.5rem 0 1rem 0;
                   border-left: 4px solid #4caf50; padding-left: 12px;">Our Impact</h4>
    """, unsafe_allow_html=True)
    st.markdown("""
    <div style="display: flex; gap: 1rem; flex-wrap: wrap; margin: 1rem 0;">
        <div style="flex: 1; min-width: 150px; background: linear-gradient(135deg, #2e7d32 0%, #4caf50 100%);
                    color: white; padding: 1.2rem; border-radius: 10px; text-align: center;">
            <div style="font-size: 2rem; font-weight: bold;">150+</div>
            <div style="font-size: 0.9rem; opacity: 0.9;">Events Conducted</div>
        </div>
        <div style="flex: 1; min-width: 150px; background: linear-gradient(135deg, #2e7d32 0%, #4caf50 100%);
                    color: white; padding: 1.2rem; border-radius: 10px; text-align: center;">
            <div style="font-size: 2rem; font-weight: bold;">5000+</div>
            <div style="font-size: 0.9rem; opacity: 0.9;">Students Benefited</div>
        </div>
        <div style="flex: 1; min-width: 150px; background: linear-gradient(135deg, #2e7d32 0%, #4caf50 100%);
                    color: white; padding: 1.2rem; border-radius: 10px; text-align: center;">
            <div style="font-size: 2rem; font-weight: bold;">25+</div>
            <div style="font-size: 0.9rem; opacity: 0.9;">Startups Incubated</div>
        </div>
        <div style="flex: 1; min-width: 150px; background: linear-gradient(135deg, #2e7d32 0%, #4caf50 100%);
                    color: white; padding: 1.2rem; border-radius: 10px; text-align: center;">
            <div style="font-size: 2rem; font-weight: bold;">15+</div>
            <div style="font-size: 0.9rem; opacity: 0.9;">Patents Filed</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Initiatives under HIVE
    st.markdown("""
        <h4 style="color: #1b5e20; font-size: 1.3rem; font-weight: 600; margin: 1.5rem 0 1rem 0;
                   border-left: 4px solid #4caf50; padding-left: 12px;">Initiatives Under HIVE</h4>
    """, unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div style="background: #f1f8e9; padding: 1rem; border-radius: 8px; height: 100%;">
            <h5 style="color: #2e7d32; margin-bottom: 0.5rem;">Institution's Innovation Council (IIC)</h5>
            <ul style="color: #333; font-size: 0.85rem; margin: 0; padding-left: 1.2rem;">
                <li>MoE's Innovation Cell Initiative</li>
                <li>Quarterly Innovation Activities</li>
                <li>Star Rating Performance</li>
                <li>National Level Competitions</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div style="background: #f1f8e9; padding: 1rem; border-radius: 8px; height: 100%;">
            <h5 style="color: #2e7d32; margin-bottom: 0.5rem;">SRIT Innovation & Startup Hub (SISH)</h5>
            <ul style="color: #333; font-size: 0.85rem; margin: 0; padding-left: 1.2rem;">
                <li>Pre-incubation Support</li>
                <li>Seed Funding Assistance</li>
                <li>Mentorship Programs</li>
                <li>Industry Connect</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div style="background: #f1f8e9; padding: 1rem; border-radius: 8px; height: 100%;">
            <h5 style="color: #2e7d32; margin-bottom: 0.5rem;">E-Cell & IDEALab</h5>
            <ul style="color: #333; font-size: 0.85rem; margin: 0; padding-left: 1.2rem;">
                <li>Entrepreneurship Awareness</li>
                <li>Business Plan Competitions</li>
                <li>Prototype Development</li>
                <li>Product Design Support</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    # Contact Information
    st.markdown("---")
    st.markdown("#### Contact Us")
    st.markdown("""
    <div style="background: #e8f5e9; padding: 1rem; border-radius: 8px; color: #333;">
        <strong style="color: #2e7d32;">HIVE - Hub for Innovation, Ventures & Entrepreneurship</strong><br>
        Sri Ramakrishna Institute of Technology<br>
        Pachapalayam, Perur Chettipalayam, Coimbatore - 641 010<br>
        <span style="color: #2e7d32;">Email:</span> hive@sritcbe.ac.in | <span style="color: #2e7d32;">Phone:</span> 0422-2605577
    </div>
    """, unsafe_allow_html=True)

def show_dashboard(sheets_client):
    """Display dashboard with statistics"""
    st.markdown('<div class="form-container">', unsafe_allow_html=True)

    try:
        sheets_manager = GoogleSheetsManager(sheets_client)
        user_events = sheets_manager.get_user_events(st.session_state.user_email)

        # Statistics
        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("Total Events", len(user_events))
            st.markdown('</div>', unsafe_allow_html=True)

        with col2:
            completed = len([e for e in user_events if e.get('Status') == 'Submitted'])
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("Submitted", completed)
            st.markdown('</div>', unsafe_allow_html=True)

        with col3:
            draft = len([e for e in user_events if e.get('Status') == 'Draft'])
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("Drafts", draft)
            st.markdown('</div>', unsafe_allow_html=True)

        with col4:
            approved = len([e for e in user_events if e.get('Admin_Approval_Status') == 'Approved'])
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("✅ Approved", approved)
            st.markdown('</div>', unsafe_allow_html=True)

        with col5:
            total_participants = sum([int(e.get('Student Participants', 0) or 0) for e in user_events])
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("Total Participants", total_participants)
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("---")

        # Recent events
        st.subheader("📅 Recent Events")
        if user_events:
            # Sort by date
            user_events_sorted = sorted(user_events, key=lambda x: x.get('Created Date', ''), reverse=True)[:10]
            df = pd.DataFrame(user_events_sorted)
            display_cols = ['Program Name', 'Start Date', 'Quarter', 'Event Level', 'Student Participants', 'Status', 'Admin_Approval_Status']
            available_cols = [col for col in display_cols if col in df.columns]
            st.dataframe(df[available_cols], use_container_width=True)
        else:
            st.info("No events found. Create your first event!")

    except Exception as e:
        st.error(f"Error loading dashboard: {str(e)}")

    st.markdown('</div>', unsafe_allow_html=True)

def show_admin_dashboard(sheets_client):
    """Display admin dashboard with all events statistics"""
    st.markdown('<div class="form-container">', unsafe_allow_html=True)

    try:
        sheets_manager = GoogleSheetsManager(sheets_client)
        all_events = sheets_manager.get_all_events()

        # Statistics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("Total Events", len(all_events))
            st.markdown('</div>', unsafe_allow_html=True)

        with col2:
            completed = len([e for e in all_events if e.get('Status') == 'Submitted'])
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("Submitted", completed)
            st.markdown('</div>', unsafe_allow_html=True)

        with col3:
            draft = len([e for e in all_events if e.get('Status') == 'Draft'])
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("Drafts", draft)
            st.markdown('</div>', unsafe_allow_html=True)

        with col4:
            total_participants = sum([int(e.get('Student Participants', 0) or 0) for e in all_events])
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("Total Participants", total_participants)
            st.markdown('</div>', unsafe_allow_html=True)

        # Additional admin stats
        st.markdown("---")
        col5, col6, col7, col8 = st.columns(4)

        with col5:
            unique_users = len(set([e.get('User Email', '') for e in all_events]))
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("Unique Users", unique_users)
            st.markdown('</div>', unsafe_allow_html=True)

        with col6:
            approved_count = len([e for e in all_events if e.get('Admin_Approval_Status') == 'Approved'])
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("✅ Approved", approved_count)
            st.markdown('</div>', unsafe_allow_html=True)

        with col7:
            pending_count = len([e for e in all_events if e.get('Status') == 'Submitted' and e.get('Admin_Approval_Status', 'Pending') not in ('Approved', 'Rejected')])
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("⏳ Pending Approval", pending_count)
            st.markdown('</div>', unsafe_allow_html=True)

        with col8:
            with_pdf = len([e for e in all_events if e.get('Generated_PDF_ID', '')])
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("Reports Generated", with_pdf)
            st.markdown('</div>', unsafe_allow_html=True)

        # Charts
        if all_events:
            st.markdown("---")
            chart_col1, chart_col2 = st.columns(2)

            with chart_col1:
                st.subheader("📊 Events by Quarter")
                quarter_short = {
                    'Quarter 1 (1st September - 30th November)': 'Q1 Sep-Nov',
                    'Quarter 2 (1st December - 28th February)': 'Q2 Dec-Feb',
                    'Quarter 3 (1st March - 31st May)': 'Q3 Mar-May',
                    'Quarter 4 (1st June - 31st August)': 'Q4 Jun-Aug',
                }
                q_counts = {}
                for e in all_events:
                    q = e.get('Quarter', 'Unknown')
                    q_label = quarter_short.get(q, q)
                    q_counts[q_label] = q_counts.get(q_label, 0) + 1
                if q_counts:
                    q_df = pd.DataFrame({'Events': q_counts})
                    st.bar_chart(q_df)

            with chart_col2:
                st.subheader("📊 Events by Program Type")
                pt_counts = {}
                for e in all_events:
                    pt = e.get('Program Type', 'Unknown') or 'Unknown'
                    pt_counts[pt] = pt_counts.get(pt, 0) + 1
                if pt_counts:
                    pt_sorted = dict(sorted(pt_counts.items(), key=lambda x: x[1], reverse=True)[:10])
                    pt_df = pd.DataFrame({'Events': pt_sorted})
                    st.bar_chart(pt_df)

            chart_col3, chart_col4 = st.columns(2)

            with chart_col3:
                st.subheader("📊 Events by Program Driven By")
                pd_counts = {}
                for e in all_events:
                    driven_by_str = e.get('Program Driven By', '') or ''
                    for d in driven_by_str.split(','):
                        d = d.strip()
                        if d:
                            pd_counts[d] = pd_counts.get(d, 0) + 1
                if pd_counts:
                    pd_df = pd.DataFrame({'Events': pd_counts})
                    st.bar_chart(pd_df)

            with chart_col4:
                st.subheader("📊 Approval Status")
                appr_counts = {
                    'Approved': len([e for e in all_events if e.get('Admin_Approval_Status') == 'Approved']),
                    'Pending': len([e for e in all_events if e.get('Admin_Approval_Status', 'Pending') not in ('Approved', 'Rejected')]),
                    'Rejected': len([e for e in all_events if e.get('Admin_Approval_Status') == 'Rejected']),
                }
                appr_df = pd.DataFrame({'Events': appr_counts})
                st.bar_chart(appr_df)

        st.markdown("---")

        # Recent events table
        st.subheader("📅 All Recent Events")
        if all_events:
            all_events_sorted = sorted(all_events, key=lambda x: x.get('Created Date', ''), reverse=True)[:20]
            df = pd.DataFrame(all_events_sorted)
            display_cols = ['Program Name', 'User Email', 'Start Date', 'Quarter', 'Event Level', 'Student Participants', 'Status', 'Admin_Approval_Status']
            available_cols = [col for col in display_cols if col in df.columns]
            st.dataframe(df[available_cols], use_container_width=True)
        else:
            st.info("No events found in the system.")

        # Export section
        st.markdown("---")
        st.subheader("📤 Export Events Data")
        export_col1, export_col2, export_col3 = st.columns(3)

        with export_col1:
            export_status = st.selectbox("Export by Status", ["All", "Submitted", "Draft"], key="export_status")
        with export_col2:
            export_approval = st.selectbox("Export by Approval", ["All", "Approved", "Pending", "Rejected"], key="export_approval")
        with export_col3:
            export_quarter = st.selectbox("Export by Quarter", ["All", "Quarter 1", "Quarter 2", "Quarter 3", "Quarter 4"], key="export_quarter")

        export_events = all_events
        if export_status != "All":
            export_events = [e for e in export_events if e.get('Status') == export_status]
        if export_approval != "All":
            if export_approval == "Pending":
                export_events = [e for e in export_events if e.get('Admin_Approval_Status', 'Pending') not in ('Approved', 'Rejected')]
            else:
                export_events = [e for e in export_events if e.get('Admin_Approval_Status') == export_approval]
        if export_quarter != "All":
            export_events = [e for e in export_events if export_quarter in str(e.get('Quarter', ''))]

        st.write(f"**{len(export_events)} events** will be exported")

        if export_events:
            export_cols = [
                'Event ID', 'Program Name', 'User Email', 'Academic Year', 'Quarter',
                'Start Date', 'End Date', 'Program Type', 'Program Driven By',
                'Professional Society Club', 'Venue Platform', 'Mode of Delivery',
                'Student Participants', 'Faculty Participants', 'External Participants',
                'Event Level', 'Duration (Hrs)', 'Expenditure Amount',
                'Speaker Names', 'Speaker Designation', 'Speaker Organization',
                'Objective', 'Brief Report', 'Key Highlights', 'Outcome',
                'Feedback Reflection', 'Organizing Team',
                'Status', 'Admin_Approval_Status', 'Approval_Date', 'Approved_By',
                'Created Date', 'Last Modified'
            ]
            export_df = pd.DataFrame(export_events)
            avail_export_cols = [c for c in export_cols if c in export_df.columns]
            export_df = export_df[avail_export_cols]

            csv_data = export_df.to_csv(index=False).encode('utf-8')
            from datetime import datetime as _dt2
            fname = f"IIC_Events_Export_{_dt2.now().strftime('%Y%m%d_%H%M')}.csv"
            st.download_button(
                label="⬇️ Download CSV",
                data=csv_data,
                file_name=fname,
                mime="text/csv",
                use_container_width=False
            )

    except Exception as e:
        st.error(f"Error loading admin dashboard: {str(e)}")

    st.markdown('</div>', unsafe_allow_html=True)

def show_all_events_admin(sheets_client, drive_service):
    """Display all submitted reports for admin to view, edit, and regenerate"""
    st.markdown('<div class="form-container">', unsafe_allow_html=True)
    st.markdown("#### All Submitted Reports")
    st.info("Admin Access: View, edit, and regenerate PDF reports for any event.")

    try:
        sheets_manager = GoogleSheetsManager(sheets_client)
        all_events = sheets_manager.get_all_events()

        # Filter options
        col_filter1, col_filter2, col_filter3, col_filter4 = st.columns(4)
        with col_filter1:
            status_filter = st.selectbox("Filter by Status", ["All", "Submitted", "Draft"])
        with col_filter2:
            approval_filter = st.selectbox("Filter by Approval", ["All", "Pending", "Approved", "Rejected"])
        with col_filter3:
            activity_filter = st.selectbox("Filter by Activity", ["All"] + config.PROGRAM_DRIVEN_BY)
        with col_filter4:
            search_term = st.text_input("Search by Event Name or Email", "")

        # Apply filters
        filtered_events = all_events
        if status_filter != "All":
            filtered_events = [e for e in filtered_events if e.get('Status') == status_filter]
        if approval_filter != "All":
            if approval_filter == "Pending":
                filtered_events = [e for e in filtered_events if e.get('Admin_Approval_Status', 'Pending') not in ('Approved', 'Rejected')]
            else:
                filtered_events = [e for e in filtered_events if e.get('Admin_Approval_Status') == approval_filter]
        if activity_filter != "All":
            filtered_events = [e for e in filtered_events if activity_filter in str(e.get('Program Driven By', ''))]
        if search_term:
            search_lower = search_term.lower()
            filtered_events = [e for e in filtered_events if
                              search_lower in e.get('Program Name', '').lower() or
                              search_lower in e.get('User Email', '').lower()]

        # Sort by date
        filtered_events = sorted(filtered_events, key=lambda x: x.get('Created Date', ''), reverse=True)

        st.write(f"**Showing {len(filtered_events)} events**")
        st.markdown("---")

        if filtered_events:
            for i, event in enumerate(filtered_events):
                with st.expander(f"📌 {event.get('Program Name', 'Unnamed Event')} - {event.get('User Email', 'Unknown')} ({event.get('Status', 'Unknown')})"):
                    # Event details
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.write(f"**Event ID:** {event.get('Event ID', 'N/A')}")
                        st.write(f"**User:** {event.get('User Email', 'N/A')}")
                        st.write(f"**Date:** {event.get('Start Date', 'N/A')} - {event.get('End Date', 'N/A')}")
                    with col2:
                        st.write(f"**Quarter:** {event.get('Quarter', 'N/A')}")
                        st.write(f"**Activity:** {event.get('Program Driven By', 'N/A')}")
                        st.write(f"**Level:** {event.get('Event Level', 'N/A')}")
                    with col3:
                        st.write(f"**Participants:** {event.get('Student Participants', 'N/A')}")
                        st.write(f"**Status:** {event.get('Status', 'N/A')}")
                        pdf_id = event.get('Generated_PDF_ID', '')
                        if pdf_id:
                            st.write("✅ PDF Generated")
                        else:
                            st.write("❌ No PDF")

                    # Second row of details
                    detail_col1, detail_col2, detail_col3 = st.columns(3)
                    with detail_col1:
                        st.write(f"**Program Type:** {event.get('Program Type', 'N/A')}")
                        st.write(f"**Venue/Platform:** {event.get('Venue Platform', 'N/A')}")
                    with detail_col2:
                        st.write(f"**Mode:** {event.get('Mode of Delivery', 'N/A')}")
                        st.write(f"**Duration:** {event.get('Duration (Hrs)', 'N/A')} hrs")
                    with detail_col3:
                        highlights = event.get('Key Highlights', '')
                        if highlights:
                            preview = highlights[:120] + '…' if len(highlights) > 120 else highlights
                            st.write(f"**Highlights:** {preview}")
                        outcome = event.get('Outcome', '')
                        if outcome:
                            out_preview = outcome[:80] + '…' if len(outcome) > 80 else outcome
                            st.write(f"**Outcome:** {out_preview}")

                    # Links
                    st.markdown("---")
                    link_col1, link_col2, link_col3, link_col4 = st.columns(4)
                    with link_col1:
                        if event.get('Drive Folder URL'):
                            st.markdown(f"[📁 Drive Folder]({event.get('Drive Folder URL')})")
                    with link_col2:
                        if pdf_id:
                            pdf_url = f"https://drive.google.com/file/d/{pdf_id}/view"
                            st.markdown(f"[📄 View PDF]({pdf_url})")
                    with link_col3:
                        if event.get('Photo1 URL'):
                            st.markdown(f"[📷 Photos]({event.get('Photo1 URL')})")

                    # Admin action buttons
                    st.markdown("---")

                    # Show current approval status
                    current_approval = event.get('Admin_Approval_Status', 'Pending')
                    if current_approval == 'Approved':
                        st.success(f"✅ Approved on {event.get('Approval_Date', 'N/A')} by {event.get('Approved_By', 'Admin')}")
                    elif current_approval == 'Rejected':
                        st.error(f"❌ Rejected - Reason: {event.get('Rejection_Reason', 'N/A')}")
                    else:
                        st.warning("⏳ Pending Approval")

                    btn_col1, btn_col2, btn_col3, btn_col4, btn_col5 = st.columns([1, 1, 1, 1, 1])

                    with btn_col1:
                        if st.button(f"✏️ Edit", key=f"admin_edit_{event.get('Event ID')}_{i}", use_container_width=True):
                            st.session_state.edit_mode = True
                            st.session_state.edit_event_data = event
                            st.success("Loading event for editing...")
                            st.rerun()

                    with btn_col2:
                        if st.button(f"🔄 Regen PDF", key=f"admin_regen_{event.get('Event ID')}_{i}", use_container_width=True):
                            # Regenerate PDF
                            with st.spinner("Regenerating PDF report..."):
                                try:
                                    drive_manager = GoogleDriveManager(drive_service)

                                    # Get folder ID
                                    folder_id = event.get('Drive Folder ID', '')
                                    if not folder_id:
                                        folder_id, _ = drive_manager.get_or_create_event_folder(
                                            event.get('Program Name', 'Event'),
                                            event.get('Event ID'),
                                            config.DRIVE_FOLDER_ID if config.DRIVE_FOLDER_ID != "YOUR_DRIVE_FOLDER_ID_HERE" else None
                                        )

                                    # Generate PDF
                                    from pdf_generator import IICReportGenerator
                                    pdf_event_data = {
                                        'Program Name': event.get('Program Name', ''),
                                        'Academic Year': event.get('Academic Year', ''),
                                        'Quarter': event.get('Quarter', ''),
                                        'Start Date': event.get('Start Date', ''),
                                        'End Date': event.get('End Date', ''),
                                        'Program Theme': event.get('Program Theme', ''),
                                        'Program Driven By': event.get('Program Driven By', ''),
                                        'Activity Led By': event.get('Activity Led By', ''),
                                        'Organizing Departments': event.get('Organizing Departments', ''),
                                        'Professional Society Club': event.get('Professional Society Club', ''),
                                        'SDG Goals': event.get('SDG Goals', ''),
                                        'Program Outcomes': event.get('Program Outcomes', ''),
                                        'Program Type': event.get('Program Type', ''),
                                        'Mode of Delivery': event.get('Mode of Delivery', ''),
                                        'Venue Platform': event.get('Venue Platform', ''),
                                        'Student Participants': event.get('Student Participants', ''),
                                        'Faculty Participants': event.get('Faculty Participants', ''),
                                        'External Participants': event.get('External Participants', ''),
                                        'Event Level': event.get('Event Level', ''),
                                        'Duration (Hrs)': event.get('Duration (Hrs)', ''),
                                        'Expenditure Amount': event.get('Expenditure Amount', ''),
                                        'Session Video URL': event.get('Session Video URL', ''),
                                        'Twitter URL': event.get('Twitter URL', ''),
                                        'Facebook URL': event.get('Facebook URL', ''),
                                        'Instagram URL': event.get('Instagram URL', ''),
                                        'LinkedIn URL': event.get('LinkedIn URL', ''),
                                        'Speaker Names': event.get('Speaker Names', ''),
                                        'Speaker Designation': event.get('Speaker Designation', ''),
                                        'Speaker Organization': event.get('Speaker Organization', ''),
                                        'Speaker Brief': event.get('Speaker Brief', ''),
                                        'Objective': event.get('Objective', ''),
                                        'Benefits': event.get('Benefits', ''),
                                        'Brief Report': event.get('Brief Report', ''),
                                        'Key Highlights': event.get('Key Highlights', ''),
                                        'Outcome': event.get('Outcome', ''),
                                        'Feedback Reflection': event.get('Feedback Reflection', ''),
                                        'Organizing Team': event.get('Organizing Team', ''),
                                        'Geotag_Photo1_ID': event.get('Geotag_Photo1_ID', ''),
                                        'Geotag_Photo2_ID': event.get('Geotag_Photo2_ID', ''),
                                        'Geotag_Photo3_ID': event.get('Geotag_Photo3_ID', ''),
                                        'Normal_Photo1_ID': event.get('Normal_Photo1_ID', ''),
                                        'Normal_Photo2_ID': event.get('Normal_Photo2_ID', ''),
                                        'Normal_Photo3_ID': event.get('Normal_Photo3_ID', ''),
                                        'Attendance_Report_ID': event.get('Attendance_Report_ID', ''),
                                        'Feedback_Analysis_ID': event.get('Feedback_Analysis_ID', ''),
                                        'Event_Agenda_ID': event.get('Event_Agenda_ID', ''),
                                        'Chief_Guest_Biodata_ID': event.get('Chief_Guest_Biodata_ID', ''),
                                        'Permission_SOP_ID': event.get('Permission_SOP_ID', ''),
                                        'Invitation_Brochure_ID': event.get('Invitation_Brochure_ID', ''),
                                        'Other_Documents_ID': event.get('Other_Documents_ID', ''),
                                        'KPI_Report_ID': event.get('KPI_Report_ID', ''),
                                    }

                                    # Fallback: if IDs missing from sheet, search Drive folder by filename
                                    eid = event.get('Event ID', '')
                                    if folder_id and eid:
                                        if not pdf_event_data['Permission_SOP_ID']:
                                            found = drive_manager.find_file_id_by_name_prefix(f"permission_sop_{eid}", folder_id)
                                            if found:
                                                pdf_event_data['Permission_SOP_ID'] = found
                                        if not pdf_event_data['Invitation_Brochure_ID']:
                                            found = drive_manager.find_file_id_by_name_prefix(f"invitation_brochure_{eid}", folder_id)
                                            if found:
                                                pdf_event_data['Invitation_Brochure_ID'] = found
                                        if not pdf_event_data['Other_Documents_ID']:
                                            found = drive_manager.find_file_id_by_name_prefix(f"other_documents_{eid}", folder_id)
                                            if found:
                                                pdf_event_data['Other_Documents_ID'] = found

                                    pdf_generator = IICReportGenerator(pdf_event_data, logo_path="logos", drive_manager=drive_manager)
                                    pdf_buffer = io.BytesIO()
                                    pdf_generator.generate_pdf(pdf_buffer)

                                    # Show merge status for debugging
                                    if hasattr(pdf_generator, 'merge_status') and pdf_generator.merge_status:
                                        with st.expander("PDF Merge Details", expanded=True):
                                            for status in pdf_generator.merge_status:
                                                if "MERGED" in status or "TOTAL" in status:
                                                    st.success(status)
                                                elif "FAILED" in status or "ERROR" in status:
                                                    st.error(status)
                                                elif "SKIPPED" in status:
                                                    st.warning(status)
                                                else:
                                                    st.info(status)

                                    pdf_buffer.seek(0)

                                    # Upload to Drive
                                    pdf_filename = f"IICReport_{event.get('Event ID')}-IC201912089.pdf"
                                    pdf_report_id = drive_manager.upload_file(
                                        pdf_buffer.read(),
                                        pdf_filename,
                                        folder_id,
                                        'application/pdf'
                                    )

                                    # Update Google Sheets with new PDF ID
                                    if pdf_report_id:
                                        sheets_manager.update_event_pdf_id(event.get('Event ID'), pdf_report_id)
                                        st.success(f"✅ PDF regenerated successfully!")
                                        st.rerun()
                                    else:
                                        st.error("Failed to upload regenerated PDF")

                                except Exception as e:
                                    st.error(f"Error regenerating PDF: {str(e)}")

                    with btn_col3:
                        if current_approval != 'Approved':
                            if st.button(f"✅ Approve", key=f"admin_approve_{event.get('Event ID')}_{i}", use_container_width=True, type="primary"):
                                from datetime import datetime as _dt
                                _now = _dt.now().strftime("%Y-%m-%d %H:%M")
                                if sheets_manager.update_approval_status(event.get('Event ID'), 'Approved', _now, st.session_state.user_email, ''):
                                    st.success("✅ Event approved!")
                                    st.rerun()
                                else:
                                    st.error("Failed to approve event")

                    with btn_col4:
                        if current_approval != 'Rejected':
                            if st.button(f"❌ Reject", key=f"admin_reject_{event.get('Event ID')}_{i}", use_container_width=True):
                                st.session_state[f'show_reject_{event.get("Event ID")}'] = True

                    with btn_col5:
                        # View Generated PDF link
                        if pdf_id:
                            pdf_url = f"https://drive.google.com/file/d/{pdf_id}/view"
                            st.markdown(f"[📄 View PDF]({pdf_url})")

                    # Rejection reason input
                    if st.session_state.get(f'show_reject_{event.get("Event ID")}', False):
                        reject_reason = st.text_area("Rejection Reason:", key=f"reject_reason_{event.get('Event ID')}_{i}")
                        if st.button("Submit Rejection", key=f"submit_reject_{event.get('Event ID')}_{i}"):
                            from datetime import datetime
                            now = datetime.now().strftime("%Y-%m-%d %H:%M")
                            if sheets_manager.update_approval_status(event.get('Event ID'), 'Rejected', now, st.session_state.user_email, reject_reason):
                                st.session_state[f'show_reject_{event.get("Event ID")}'] = False
                                st.success("Event rejected!")
                                st.rerun()
                            else:
                                st.error("Failed to reject event")

                    # Generate Merged PDF for Download Section
                    st.markdown("---")
                    st.markdown("**📥 Generate Merged PDF Report:**")
                    st.info("Generate and download the complete merged PDF with all uploaded documents (Attendance, Feedback, Agenda, Biodata, KPI) for printing and signing.")

                    if st.button(f"📄 Generate & Download Merged PDF", key=f"merge_download_{event.get('Event ID')}_{i}", use_container_width=True):
                        with st.spinner("Generating merged PDF report with all documents..."):
                            try:
                                drive_manager = GoogleDriveManager(drive_service)

                                # Get folder ID
                                folder_id = event.get('Drive Folder ID', '')
                                if not folder_id:
                                    folder_id, _ = drive_manager.get_or_create_event_folder(
                                        event.get('Program Name', 'Event'),
                                        event.get('Event ID'),
                                        config.DRIVE_FOLDER_ID if config.DRIVE_FOLDER_ID != "YOUR_DRIVE_FOLDER_ID_HERE" else None
                                    )

                                # Prepare event data for PDF generation
                                from pdf_generator import IICReportGenerator
                                pdf_event_data = {
                                    'Program Name': event.get('Program Name', ''),
                                    'Academic Year': event.get('Academic Year', ''),
                                    'Quarter': event.get('Quarter', ''),
                                    'Start Date': event.get('Start Date', ''),
                                    'End Date': event.get('End Date', ''),
                                    'Program Theme': event.get('Program Theme', ''),
                                    'Program Driven By': event.get('Program Driven By', ''),
                                    'Activity Led By': event.get('Activity Led By', ''),
                                    'Organizing Departments': event.get('Organizing Departments', ''),
                                    'Professional Society Club': event.get('Professional Society Club', ''),
                                    'SDG Goals': event.get('SDG Goals', ''),
                                    'Program Outcomes': event.get('Program Outcomes', ''),
                                    'Program Type': event.get('Program Type', ''),
                                    'Mode of Delivery': event.get('Mode of Delivery', ''),
                                    'Venue Platform': event.get('Venue Platform', ''),
                                    'Student Participants': event.get('Student Participants', ''),
                                    'Faculty Participants': event.get('Faculty Participants', ''),
                                    'External Participants': event.get('External Participants', ''),
                                    'Event Level': event.get('Event Level', ''),
                                    'Duration (Hrs)': event.get('Duration (Hrs)', ''),
                                    'Expenditure Amount': event.get('Expenditure Amount', ''),
                                    'Session Video URL': event.get('Session Video URL', ''),
                                    'Twitter URL': event.get('Twitter URL', ''),
                                    'Facebook URL': event.get('Facebook URL', ''),
                                    'Instagram URL': event.get('Instagram URL', ''),
                                    'LinkedIn URL': event.get('LinkedIn URL', ''),
                                    'Speaker Names': event.get('Speaker Names', ''),
                                    'Speaker Designation': event.get('Speaker Designation', ''),
                                    'Speaker Organization': event.get('Speaker Organization', ''),
                                    'Speaker Brief': event.get('Speaker Brief', ''),
                                    'Objective': event.get('Objective', ''),
                                    'Benefits': event.get('Benefits', ''),
                                    'Brief Report': event.get('Brief Report', ''),
                                    'Key Highlights': event.get('Key Highlights', ''),
                                    'Outcome': event.get('Outcome', ''),
                                    'Feedback Reflection': event.get('Feedback Reflection', ''),
                                    'Organizing Team': event.get('Organizing Team', ''),
                                    'Geotag_Photo1_ID': event.get('Geotag_Photo1_ID', ''),
                                    'Geotag_Photo2_ID': event.get('Geotag_Photo2_ID', ''),
                                    'Geotag_Photo3_ID': event.get('Geotag_Photo3_ID', ''),
                                    'Normal_Photo1_ID': event.get('Normal_Photo1_ID', ''),
                                    'Normal_Photo2_ID': event.get('Normal_Photo2_ID', ''),
                                    'Normal_Photo3_ID': event.get('Normal_Photo3_ID', ''),
                                    'Attendance_Report_ID': event.get('Attendance_Report_ID', ''),
                                    'Feedback_Analysis_ID': event.get('Feedback_Analysis_ID', ''),
                                    'Event_Agenda_ID': event.get('Event_Agenda_ID', ''),
                                    'Chief_Guest_Biodata_ID': event.get('Chief_Guest_Biodata_ID', ''),
                                    'Permission_SOP_ID': event.get('Permission_SOP_ID', ''),
                                    'Invitation_Brochure_ID': event.get('Invitation_Brochure_ID', ''),
                                    'Other_Documents_ID': event.get('Other_Documents_ID', ''),
                                    'KPI_Report_ID': event.get('KPI_Report_ID', ''),
                                }

                                # Fallback: if IDs missing from sheet, search Drive folder by filename
                                eid = event.get('Event ID', '')
                                if folder_id and eid:
                                    if not pdf_event_data['Permission_SOP_ID']:
                                        found = drive_manager.find_file_id_by_name_prefix(f"permission_sop_{eid}", folder_id)
                                        if found:
                                            pdf_event_data['Permission_SOP_ID'] = found
                                    if not pdf_event_data['Invitation_Brochure_ID']:
                                        found = drive_manager.find_file_id_by_name_prefix(f"invitation_brochure_{eid}", folder_id)
                                        if found:
                                            pdf_event_data['Invitation_Brochure_ID'] = found
                                    if not pdf_event_data['Other_Documents_ID']:
                                        found = drive_manager.find_file_id_by_name_prefix(f"other_documents_{eid}", folder_id)
                                        if found:
                                            pdf_event_data['Other_Documents_ID'] = found

                                # Generate the merged PDF
                                pdf_generator = IICReportGenerator(pdf_event_data, logo_path="logos", drive_manager=drive_manager)
                                pdf_buffer = io.BytesIO()
                                pdf_generator.generate_pdf(pdf_buffer)

                                # Show merge status
                                if hasattr(pdf_generator, 'merge_status') and pdf_generator.merge_status:
                                    with st.expander("📋 PDF Merge Details", expanded=True):
                                        for status in pdf_generator.merge_status:
                                            if "MERGED" in status or "TOTAL" in status:
                                                st.success(status)
                                            elif "FAILED" in status or "ERROR" in status:
                                                st.error(status)
                                            elif "SKIPPED" in status:
                                                st.warning(status)
                                            else:
                                                st.info(status)

                                pdf_buffer.seek(0)

                                # Provide download button
                                pdf_filename = f"IICReport_MERGED_{event.get('Event ID')}.pdf"
                                st.download_button(
                                    label="⬇️ Download Merged PDF",
                                    data=pdf_buffer.getvalue(),
                                    file_name=pdf_filename,
                                    mime="application/pdf",
                                    key=f"download_merged_{event.get('Event ID')}_{i}",
                                    use_container_width=True
                                )
                                st.success("✅ Merged PDF generated! Click the download button above to save it.")
                                st.info("Print this PDF, get required signatures, scan it, and upload as signed PDF below.")

                            except Exception as e:
                                st.error(f"Error generating merged PDF: {str(e)}")

                    # Signed PDF Upload and Approval Section
                    st.markdown("---")
                    existing_signed_pdf = event.get('Signed_PDF_ID', '')

                    if current_approval == 'Approved':
                        # Already approved - show signed PDF
                        if existing_signed_pdf:
                            signed_url = f"https://drive.google.com/file/d/{existing_signed_pdf}/view"
                            st.success(f"✅ Approved with Signed PDF: [View Signed PDF]({signed_url})")
                        else:
                            st.warning("Approved but no signed PDF uploaded yet")
                            # Allow uploading signed PDF even after approval
                            signed_pdf = st.file_uploader(
                                "Upload signed PDF report",
                                type=['pdf'],
                                key=f"signed_pdf_{event.get('Event ID')}_{i}",
                                help="Upload the printed and signed PDF report"
                            )
                            if signed_pdf:
                                if st.button(f"📤 Upload Signed PDF", key=f"upload_signed_{event.get('Event ID')}_{i}"):
                                    with st.spinner("Uploading signed PDF..."):
                                        try:
                                            drive_manager = GoogleDriveManager(drive_service)
                                            folder_id = event.get('Drive Folder ID', '')
                                            if not folder_id:
                                                folder_id, _ = drive_manager.get_or_create_event_folder(
                                                    event.get('Program Name', 'Event'),
                                                    event.get('Event ID'),
                                                    config.DRIVE_FOLDER_ID if config.DRIVE_FOLDER_ID != "YOUR_DRIVE_FOLDER_ID_HERE" else None
                                                )

                                            signed_pdf_id = drive_manager.upload_file(
                                                signed_pdf.read(),
                                                f"IICReport_SIGNED_{event.get('Event ID')}.pdf",
                                                folder_id,
                                                'application/pdf'
                                            )

                                            if signed_pdf_id:
                                                sheets_manager.update_signed_pdf_id(event.get('Event ID'), signed_pdf_id)
                                                st.success("✅ Signed PDF uploaded! User can now download it.")
                                                st.rerun()
                                            else:
                                                st.error("Failed to upload signed PDF")
                                        except Exception as e:
                                            st.error(f"Error uploading signed PDF: {str(e)}")

                    elif current_approval != 'Approved':
                        # Not yet approved - require signed PDF upload to approve
                        st.markdown("**📝 Upload Signed PDF to Approve:**")
                        st.info("You must upload the signed PDF report to approve this event. The signed PDF will be made available to the user after approval.")

                        signed_pdf = st.file_uploader(
                            "Upload signed PDF report *",
                            type=['pdf'],
                            key=f"signed_pdf_{event.get('Event ID')}_{i}",
                            help="Print the generated PDF, get signatures, scan/upload it here"
                        )

                        if signed_pdf:
                            st.success(f"Signed PDF selected: {signed_pdf.name}")
                            if st.button(f"✅ Upload & Approve Event", key=f"approve_with_pdf_{event.get('Event ID')}_{i}", type="primary", use_container_width=True):
                                with st.spinner("Uploading signed PDF and approving event..."):
                                    try:
                                        drive_manager = GoogleDriveManager(drive_service)
                                        folder_id = event.get('Drive Folder ID', '')
                                        if not folder_id:
                                            folder_id, _ = drive_manager.get_or_create_event_folder(
                                                event.get('Program Name', 'Event'),
                                                event.get('Event ID'),
                                                config.DRIVE_FOLDER_ID if config.DRIVE_FOLDER_ID != "YOUR_DRIVE_FOLDER_ID_HERE" else None
                                            )

                                        # Upload signed PDF
                                        signed_pdf_id = drive_manager.upload_file(
                                            signed_pdf.read(),
                                            f"IICReport_SIGNED_{event.get('Event ID')}.pdf",
                                            folder_id,
                                            'application/pdf'
                                        )

                                        if signed_pdf_id:
                                            # Update signed PDF ID
                                            sheets_manager.update_signed_pdf_id(event.get('Event ID'), signed_pdf_id)

                                            # Approve the event
                                            from datetime import datetime
                                            now = datetime.now().strftime("%Y-%m-%d %H:%M")
                                            if sheets_manager.update_approval_status(event.get('Event ID'), 'Approved', now, st.session_state.user_email, ''):
                                                st.success("✅ Event approved and signed PDF uploaded! User can now download it.")
                                                st.balloons()
                                                st.rerun()
                                            else:
                                                st.error("Signed PDF uploaded but failed to approve event")
                                        else:
                                            st.error("Failed to upload signed PDF")
                                    except Exception as e:
                                        st.error(f"Error: {str(e)}")
                        else:
                            st.warning("Please upload the signed PDF to approve this event.")

        else:
            st.info("No events found matching the filters.")

    except Exception as e:
        st.error(f"Error loading events: {str(e)}")

    st.markdown('</div>', unsafe_allow_html=True)

def create_event_form(sheets_client, drive_service):
    """Create/Edit event form"""
    st.markdown('<div class="form-container">', unsafe_allow_html=True)

    # Check if in edit mode
    if st.session_state.edit_mode and st.session_state.edit_event_data:
        st.markdown("#### Edit Event")
        event_data = st.session_state.edit_event_data
        event_id = event_data.get('Event ID')
    else:
        st.markdown("#### Create New Event")
        event_data = {}
        event_id = None

    # Academic Year
    col1, col2 = st.columns(2)
    with col1:
        academic_year = st.selectbox(
            "Academic Year *",
            config.ACADEMIC_YEARS,
            index=config.ACADEMIC_YEARS.index(event_data.get('Academic Year', config.ACADEMIC_YEARS[0])) if event_data.get('Academic Year') in config.ACADEMIC_YEARS else 0
        )

    # Event Name
    event_name = st.text_input(
        "Program/Activity Name *",
        value=event_data.get('Program Name', ''),
        placeholder="Enter the program or activity name",
        help="Provide a descriptive name for your event"
    )

    # Generate or use existing event ID
    if not event_id and event_name:
        event_id = ValidationUtils.generate_event_id(st.session_state.user_email, event_name)

    if event_id:
        st.info(f"**Event ID:** {event_id}")

    # Date Selection with validation
    col1, col2 = st.columns(2)
    with col1:
        # Parse start date if editing
        default_start = datetime.today()
        if event_data.get('Start Date'):
            try:
                default_start = datetime.strptime(event_data.get('Start Date'), '%Y-%m-%d')
            except:
                pass

        start_date = st.date_input(
            "Start Date *",
            value=default_start,
            help="Select the start date of the event"
        )

    with col2:
        # Set minimum end date to start date
        default_end = start_date
        if event_data.get('End Date'):
            try:
                default_end = datetime.strptime(event_data.get('End Date'), '%Y-%m-%d')
            except:
                default_end = start_date

        end_date = st.date_input(
            "End Date *",
            value=default_end,
            min_value=start_date,  # Ensure end date is not before start date
            help="Select the end date of the event (must be same or after start date)"
        )

    # Validate dates
    if end_date < start_date:
        st.error("❌ End date cannot be before start date!")

    # Auto-calculate quarter
    quarter = ""
    if start_date:
        quarter = ValidationUtils.get_quarter_from_date(start_date)
        st.info(f"**Auto-detected Quarter:** {quarter}")

    # Event Type and Duration
    col1, col2 = st.columns(2)
    with col1:
        program_type = st.selectbox(
            "Program Type *",
            config.EVENT_TYPES,
            index=config.EVENT_TYPES.index(event_data.get('Program Type')) if event_data.get('Program Type') in config.EVENT_TYPES else 0
        )

    with col2:
        duration = st.number_input(
            "Duration of the activity (In Hrs) *",
            min_value=1.0,
            max_value=100.0,
            step=0.5,
            value=float(event_data.get('Duration (Hrs)', 2.0)),
            help="Enter the duration in hours"
        )

    # Auto-calculate level
    event_level = ""
    level_number = 0
    if duration:
        event_level, level_number = ValidationUtils.get_level_from_duration(duration)

        if level_number >= config.MIN_EVENT_LEVEL:
            st.success(f"**Auto-detected Level:** {event_level} ✓ (Meets minimum requirement)")
        else:
            st.error(f"**Auto-detected Level:** {event_level} ✗ (Event level must be {config.MIN_EVENT_LEVEL} or higher)")

    # Program Driven By and Activity Led By
    col1, col2 = st.columns(2)
    with col1:
        existing_driven_by = [v.strip() for v in event_data.get('Program Driven By', '').split(',') if v.strip() in config.PROGRAM_DRIVEN_BY] if event_data.get('Program Driven By') else []
        program_driven_by = st.multiselect(
            "Program Driven By * (Select 1 or 2)",
            config.PROGRAM_DRIVEN_BY,
            default=existing_driven_by,
            help="Select one or two options — e.g. IIC Calendar Activity and Club Activity"
        )
        if len(program_driven_by) > 2:
            st.error("⚠️ Please select a maximum of 2 options for Program Driven By")

    with col2:
        activity_led_by = st.selectbox(
            "Activity Led By *",
            config.ACTIVITY_LED_BY,
            index=config.ACTIVITY_LED_BY.index(event_data.get('Activity Led By')) if event_data.get('Activity Led By') in config.ACTIVITY_LED_BY else 0
        )

    # Program Theme
    program_theme = st.selectbox(
        "Program Theme *",
        config.PROGRAM_THEMES,
        index=config.PROGRAM_THEMES.index(event_data.get('Program Theme')) if event_data.get('Program Theme') in config.PROGRAM_THEMES else 0
    )

    # Department and Professional Society/Club
    st.markdown("#### Organizing Details")

    col1, col2 = st.columns(2)
    with col1:
        organizing_departments = st.multiselect(
            "Organized by Department(s) *",
            config.DEPARTMENTS,
            default=[d for d in event_data.get('Organizing Departments', '').split(',') if d.strip() in config.DEPARTMENTS] if event_data.get('Organizing Departments') else [],
            help="Select one or more departments that organized this event"
        )

    with col2:
        existing_clubs = [c.strip() for c in event_data.get('Professional Society Club', '').split(',') if c.strip() in config.CLUBS] if event_data.get('Professional Society Club') else []
        professional_society_club_list = st.multiselect(
            "Professional Society / Club Name(s)",
            config.CLUBS,
            default=existing_clubs,
            help="Select the club(s) or professional society involved in this event"
        )
        professional_society_club = ','.join(professional_society_club_list)

    # Mode of Session Delivery and Venue/Platform
    col1, col2 = st.columns(2)
    with col1:
        mode_delivery = st.selectbox(
            "Mode of Session Delivery *",
            config.MODE_OF_DELIVERY,
            index=config.MODE_OF_DELIVERY.index(event_data.get('Mode of Delivery')) if event_data.get('Mode of Delivery') in config.MODE_OF_DELIVERY else 0
        )
    with col2:
        venue_platform = st.text_input(
            "Venue / Platform *",
            value=event_data.get('Venue Platform', ''),
            placeholder="e.g., Seminar Hall A / Google Meet / Zoom",
            help="Name of the physical venue or virtual platform used for the session"
        )

    # SDG Goals and Program Outcomes Mapping
    st.markdown("#### SDG & PO Mapping")

    # SDG Goals (max 4)
    existing_sdgs = [s.strip() for s in event_data.get('SDG Goals', '').split(',') if s.strip() in config.SDG_GOALS] if event_data.get('SDG Goals') else []
    sdg_goals = st.multiselect(
        "SDG Goals Mapping (Select up to 4) *",
        config.SDG_GOALS,
        default=existing_sdgs,
        help="Select the UN Sustainable Development Goals that this event aligns with (maximum 4)"
    )
    if len(sdg_goals) > 4:
        st.error("⚠️ Please select a maximum of 4 SDG Goals")

    # Program Outcomes (max 11)
    existing_pos = [p.strip() for p in event_data.get('Program Outcomes', '').split(',') if p.strip() in config.PROGRAM_OUTCOMES] if event_data.get('Program Outcomes') else []
    program_outcomes = st.multiselect(
        "Program Outcomes (PO) Mapping (Select applicable POs)",
        config.PROGRAM_OUTCOMES,
        default=existing_pos,
        help="Select the NBA Program Outcomes that this event addresses"
    )

    st.markdown("#### Participation Details")

    # Participants
    col1, col2, col3 = st.columns(3)
    with col1:
        student_participants = st.number_input(
            "Number of Student Participants *",
            min_value=0,
            step=1,
            value=int(event_data.get('Student Participants', 0)),
            help="Enter the number of student participants"
        )
        if student_participants > 0 and student_participants < config.MIN_STUDENT_PARTICIPANTS:
            st.error(f"⚠️ Minimum {config.MIN_STUDENT_PARTICIPANTS} students required (Current: {student_participants})")
        elif student_participants >= config.MIN_STUDENT_PARTICIPANTS:
            st.success(f"✓ Meets minimum requirement")

    with col2:
        faculty_participants = st.number_input(
            "Number of Faculty Participants *",
            min_value=0,
            step=1,
            value=int(event_data.get('Faculty Participants', 0)),
            help="Enter the number of faculty participants"
        )

    with col3:
        external_participants = st.number_input(
            "Number of External Participants",
            min_value=0,
            step=1,
            value=int(event_data.get('External Participants', 0)),
            help="Enter the number of external participants (if any)"
        )

    # Expenditure and Remark
    col1, col2 = st.columns(2)
    with col1:
        expenditure = st.number_input(
            "Expenditure Amount (₹)",
            min_value=0.0,
            step=100.0,
            value=float(event_data.get('Expenditure Amount', 0.0)),
            help="Enter the expenditure amount (if any)"
        )

    with col2:
        remark = st.text_input(
            "Remark",
            value=event_data.get('Remark', ''),
            placeholder="Any additional remarks",
            help="Optional remarks about the event"
        )

    st.markdown("#### Objectives & Benefits")

    # Objective
    objective = st.text_area(
        "Objective *",
        value=event_data.get('Objective', ''),
        placeholder="Enter the objective of the event (Max 100 words)",
        help="Describe the objective in 100 words or less",
        max_chars=700
    )

    if objective:
        word_count = ValidationUtils.count_words(objective)
        if word_count > config.MAX_OBJECTIVE_WORDS:
            st.error(f"⚠️ Objective exceeds {config.MAX_OBJECTIVE_WORDS} words (Current: {word_count} words)")
        else:
            st.info(f"Word count: {word_count}/{config.MAX_OBJECTIVE_WORDS}")

    # Benefits
    benefits = st.text_area(
        "Benefit in terms of learning/Skill/Knowledge obtained *",
        value=event_data.get('Benefits', ''),
        placeholder="Enter the benefits (Max 150 words)",
        help="Describe the benefits in 150 words or less",
        max_chars=1000
    )

    if benefits:
        word_count = ValidationUtils.count_words(benefits)
        if word_count > config.MAX_BENEFITS_WORDS:
            st.error(f"⚠️ Benefits exceed {config.MAX_BENEFITS_WORDS} words (Current: {word_count} words)")
        else:
            st.info(f"Word count: {word_count}/{config.MAX_BENEFITS_WORDS}")

    # Speaker Details Section
    _no_speaker_types = {"Club Activity", "Competition", "Hackathon", "Exhibition", "Tech/E-Fest", "Outreach Program", "Challenge"}
    _speaker_optional = program_type in _no_speaker_types
    _spk_suffix = " (Optional)" if _speaker_optional else " *"

    st.markdown("#### Speaker / Expert Details")
    if _speaker_optional:
        st.info(f"Speaker details are optional for **{program_type}** events.")

    speaker_names = st.text_input(
        f"Speaker / Organiser Name(s){_spk_suffix}",
        value=event_data.get('Speaker Names', ''),
        placeholder="Enter speaker names (separate multiple names with comma)",
        help="For multiple speakers, separate names with comma (e.g., Dr. John, Prof. Smith)"
    )

    col1, col2 = st.columns(2)
    with col1:
        speaker_designation = st.text_input(
            f"Speaker Designation(s){_spk_suffix}",
            value=event_data.get('Speaker Designation', ''),
            placeholder="Enter designation(s) (separate with comma for multiple)",
            help="For multiple speakers, separate designations with comma"
        )

    with col2:
        speaker_organization = st.text_input(
            f"Speaker Organization(s){_spk_suffix}",
            value=event_data.get('Speaker Organization', ''),
            placeholder="Enter organization(s) (separate with comma for multiple)",
            help="For multiple speakers, separate organizations with comma"
        )

    speaker_brief = st.text_area(
        "Brief about Expert/Speaker",
        value=event_data.get('Speaker Brief', ''),
        placeholder="Brief background, expertise, and achievements of the speaker/expert...",
        help="Short bio of the expert or speaker",
        height=100
    )

    session_video_url = st.text_input(
        "Video URL of the Session",
        value=event_data.get('Session Video URL', ''),
        placeholder="https://youtube.com/... or https://drive.google.com/...",
        help="Recommended: Provide the video recording URL of the session if available"
    )

    # Brief Report Section
    st.markdown("#### Brief Description of the Activity")
    st.info("Write a brief description of the activity (150–200 words). Include: how the session started, key topics covered, key interaction points, demonstrations/examples, Q&A session, any activities conducted.")

    brief_report = st.text_area(
        "Brief Description of the Activity *",
        value=event_data.get('Brief Report', ''),
        placeholder="(a) How the session started\n(b) Key topics covered\n(c) Key points during interaction\n(d) Demonstrations / examples shared\n(e) Q&A session\n(f) Any activity conducted (quiz, brainstorming, ideation etc.)",
        help="150–200 words as per IIC Activity Format",
        height=250
    )

    if brief_report:
        word_count = ValidationUtils.count_words(brief_report)
        if word_count < config.MIN_BRIEF_REPORT_WORDS:
            st.warning(f"⚠️ {word_count} words — needs at least {config.MIN_BRIEF_REPORT_WORDS} words")
        elif word_count > config.MAX_BRIEF_REPORT_WORDS:
            st.error(f"⚠️ {word_count} words — must not exceed {config.MAX_BRIEF_REPORT_WORDS} words")
        else:
            st.success(f"✓ Word count: {word_count} words (within 150–200 range)")

    # Key Highlights
    st.markdown("#### Key Highlights")
    st.info("Briefly mention the most important moments, insights, and engagement points in 5–8 short bullet points.")

    key_highlights = st.text_area(
        "Key Highlights *",
        value=event_data.get('Key Highlights', ''),
        placeholder="• \n• \n• \n• \n• ",
        help="5–8 bullet points highlighting what made the session meaningful",
        height=200
    )

    # Outcome of Activity
    outcome = st.text_area(
        "Outcome of the Activity *",
        value=event_data.get('Outcome', ''),
        placeholder="Clearly mention what participants gained. The outcome should align with and reflect the KPIs mentioned in the activity details on the IIC portal.",
        help="What did participants gain from this activity?",
        height=120
    )

    # Feedback / Reflection
    feedback_reflection = st.text_area(
        "Feedback / Reflection",
        value=event_data.get('Feedback Reflection', ''),
        placeholder="1. \"Participant feedback here...\"\n2. \"Another participant's reflection...\"\n3. \"Third participant's feedback...\"",
        help="Include 2–3 participant feedbacks or reflections",
        height=120
    )

    # Organizing Team Members
    organizing_team = st.text_area(
        "Organizing Team Members",
        value=event_data.get('Organizing Team', ''),
        placeholder="Name — Role\nName — Role",
        help="Mention all important team members involved and their roles",
        height=100
    )

    st.markdown("#### Attachments & Documents")

    # Show existing files if editing
    if st.session_state.edit_mode:
        st.info("**Current Files:** Upload new files to replace existing ones")

    # Geotagged Photos Section
    st.markdown("### 📍 Geotagged Photographs")
    st.info("Upload 3 photos with geotag/location data. Only upload new files if you want to replace existing ones.")

    col1, col2, col3 = st.columns(3)
    with col1:
        if event_data.get('Geotag_Photo1_ID'):
            st.success("✓ Already uploaded")
        geotag_photo1 = st.file_uploader(
            "Geotagged Photo 1 *",
            type=['jpg', 'jpeg', 'png'],
            help="Upload geotagged photograph (max 2MB)",
            key="geotag_photo1"
        )
    with col2:
        if event_data.get('Geotag_Photo2_ID'):
            st.success("✓ Already uploaded")
        geotag_photo2 = st.file_uploader(
            "Geotagged Photo 2 *",
            type=['jpg', 'jpeg', 'png'],
            help="Upload geotagged photograph (max 2MB)",
            key="geotag_photo2"
        )
    with col3:
        if event_data.get('Geotag_Photo3_ID'):
            st.success("✓ Already uploaded")
        geotag_photo3 = st.file_uploader(
            "Geotagged Photo 3 *",
            type=['jpg', 'jpeg', 'png'],
            help="Upload geotagged photograph (max 2MB)",
            key="geotag_photo3"
        )

    # Normal Photos Section
    st.markdown("### 📷 Normal Photographs")
    st.info("Upload 3 regular event photos. Only upload new files if you want to replace existing ones.")

    col1, col2, col3 = st.columns(3)
    with col1:
        if event_data.get('Normal_Photo1_ID'):
            st.success("✓ Already uploaded")
        normal_photo1 = st.file_uploader(
            "Normal Photo 1 *",
            type=['jpg', 'jpeg', 'png'],
            help="Upload event photograph (max 2MB)",
            key="normal_photo1"
        )
    with col2:
        if event_data.get('Normal_Photo2_ID'):
            st.success("✓ Already uploaded")
        normal_photo2 = st.file_uploader(
            "Normal Photo 2 *",
            type=['jpg', 'jpeg', 'png'],
            help="Upload event photograph (max 2MB)",
            key="normal_photo2"
        )
    with col3:
        if event_data.get('Normal_Photo3_ID'):
            st.success("✓ Already uploaded")
        normal_photo3 = st.file_uploader(
            "Normal Photo 3 *",
            type=['jpg', 'jpeg', 'png'],
            help="Upload event photograph (max 2MB)",
            key="normal_photo3"
        )

    # Document Uploads Section
    st.markdown("### 📄 Required Documents")
    st.info("Only upload new documents if you want to replace existing ones.")

    col1, col2 = st.columns(2)
    with col1:
        if event_data.get('Attendance_Report_ID'):
            st.success("✓ Attendance Report already uploaded")
        attendance_report = st.file_uploader(
            "Attendance Report *",
            type=['pdf', 'jpg', 'jpeg', 'png'],
            help="Upload attendance report (Image or PDF, max 5MB, A4 size)",
            key="attendance_report"
        )
        if attendance_report:
            file_size_mb = len(attendance_report.getvalue()) / (1024 * 1024)
            if file_size_mb > config.MAX_PDF_FILE_SIZE_MB:
                st.error(f"⚠️ File size ({file_size_mb:.2f}MB) exceeds {config.MAX_PDF_FILE_SIZE_MB}MB limit")
            else:
                st.info(f"New file: {file_size_mb:.2f}MB - will replace existing")

    with col2:
        if event_data.get('Feedback_Analysis_ID'):
            st.success("✓ Feedback Analysis already uploaded")
        is_atl = 'ATL School Activity' in program_driven_by
        feedback_label = "Feedback Analysis Report (Optional for ATL)" if is_atl else "Feedback Analysis Report *"
        feedback_analysis = st.file_uploader(
            feedback_label,
            type=['pdf'],
            help="Upload feedback analysis from Google Form with graphs (PDF only, max 5MB)",
            key="feedback_analysis"
        )
        if feedback_analysis:
            file_size_mb = len(feedback_analysis.getvalue()) / (1024 * 1024)
            if file_size_mb > config.MAX_PDF_FILE_SIZE_MB:
                st.error(f"⚠️ File size ({file_size_mb:.2f}MB) exceeds {config.MAX_PDF_FILE_SIZE_MB}MB limit")
            else:
                st.info(f"New file: {file_size_mb:.2f}MB - will replace existing")

    col1, col2 = st.columns(2)
    with col1:
        if event_data.get('Event_Agenda_ID'):
            st.success("✓ Event Agenda already uploaded")
        agenda_label = "Event Agenda (Optional for ATL)" if is_atl else "Event Agenda *"
        event_agenda = st.file_uploader(
            agenda_label,
            type=['pdf'],
            help="Upload event agenda (PDF only, max 5MB)",
            key="event_agenda"
        )
        if event_agenda:
            file_size_mb = len(event_agenda.getvalue()) / (1024 * 1024)
            if file_size_mb > config.MAX_PDF_FILE_SIZE_MB:
                st.error(f"⚠️ File size ({file_size_mb:.2f}MB) exceeds {config.MAX_PDF_FILE_SIZE_MB}MB limit")
            else:
                st.info(f"New file: {file_size_mb:.2f}MB - will replace existing")

    with col2:
        if event_data.get('Chief_Guest_Biodata_ID'):
            st.success("✓ Chief Guest Biodata already uploaded")
        biodata_label = "Chief Guest Biodata (Optional for ATL)" if is_atl else "Chief Guest Biodata *"
        chief_guest_biodata = st.file_uploader(
            biodata_label,
            type=['pdf'],
            help="Upload brief biodata of chief guest (PDF only, max 10MB)",
            key="chief_guest_biodata"
        )
        if chief_guest_biodata:
            file_size_mb = len(chief_guest_biodata.getvalue()) / (1024 * 1024)
            if file_size_mb > config.MAX_PDF_FILE_SIZE_MB:
                st.error(f"⚠️ File size ({file_size_mb:.2f}MB) exceeds {config.MAX_PDF_FILE_SIZE_MB}MB limit")
            else:
                st.success(f"✓ File size: {file_size_mb:.2f}MB")

    # Permission SOP with Principal Signature
    st.markdown("### 📋 Permission SOP")
    col1, col2 = st.columns(2)
    with col1:
        if event_data.get('Permission_SOP_ID'):
            st.success("✓ Permission SOP already uploaded")
        permission_sop = st.file_uploader(
            "Permission SOP with Principal Signature *",
            type=['pdf', 'jpg', 'jpeg', 'png'],
            help="Upload Permission SOP document with Principal's signature (PDF or Image, max 10MB)",
            key="permission_sop"
        )
        if permission_sop:
            file_size_mb = len(permission_sop.getvalue()) / (1024 * 1024)
            if file_size_mb > config.MAX_PDF_FILE_SIZE_MB:
                st.error(f"⚠️ File size ({file_size_mb:.2f}MB) exceeds {config.MAX_PDF_FILE_SIZE_MB}MB limit")
            else:
                st.success(f"✓ File size: {file_size_mb:.2f}MB")

    with col2:
        if event_data.get('Invitation_Brochure_ID'):
            st.success("✓ Invitation/Brochure already uploaded")
        invitation_brochure = st.file_uploader(
            "Invitation / Brochure *",
            type=['pdf', 'jpg', 'jpeg', 'png'],
            help="Upload event invitation or brochure (PDF or Image, max 10MB) - At least one is mandatory",
            key="invitation_brochure"
        )
        if invitation_brochure:
            file_size_mb = len(invitation_brochure.getvalue()) / (1024 * 1024)
            if file_size_mb > config.MAX_PDF_FILE_SIZE_MB:
                st.error(f"⚠️ File size ({file_size_mb:.2f}MB) exceeds {config.MAX_PDF_FILE_SIZE_MB}MB limit")
            else:
                st.success(f"✓ File size: {file_size_mb:.2f}MB")

    # Other Documents (UC, Bills, etc.) - Mandatory if finance involved
    st.markdown("### 📁 Other Documents (Finance Related)")
    st.info("If the event has finance involved (expenditure > 0), uploading UC/Bill documents is mandatory")

    if event_data.get('Other_Documents_ID'):
        st.success("✓ Other documents already uploaded")
    other_documents = st.file_uploader(
        f"Other Documents (UC/Bills) {'*' if expenditure > 0 else ''}",
        type=['pdf', 'jpg', 'jpeg', 'png'],
        help="Upload UC, bill documents or any other supporting documents (PDF or Image, max 10MB)",
        key="other_documents"
    )
    if other_documents:
        file_size_mb = len(other_documents.getvalue()) / (1024 * 1024)
        if file_size_mb > config.MAX_PDF_FILE_SIZE_MB:
            st.error(f"⚠️ File size ({file_size_mb:.2f}MB) exceeds {config.MAX_PDF_FILE_SIZE_MB}MB limit")
        else:
            st.success(f"✓ File size: {file_size_mb:.2f}MB")

    if expenditure > 0 and not other_documents and not event_data.get('Other_Documents_ID'):
        st.warning("⚠️ Since expenditure is involved, uploading UC/Bill documents is mandatory")

    # KPI Report - Only for IIC Calendar Activity (legacy support)
    kpi_report = None
    kpi_report_id = event_data.get('KPI_Report_ID', '')

    st.markdown("#### Social Media Promotion")

    st.info("Provide links if promoted on any social media platform")

    col1, col2 = st.columns(2)
    with col1:
        twitter_url = st.text_input("Twitter URL", value=event_data.get('Twitter URL', ''), placeholder="https://twitter.com/...")
        facebook_url = st.text_input("Facebook URL", value=event_data.get('Facebook URL', ''), placeholder="https://facebook.com/...")

    with col2:
        instagram_url = st.text_input("Instagram URL", value=event_data.get('Instagram URL', ''), placeholder="https://instagram.com/...")
        linkedin_url = st.text_input("LinkedIn URL", value=event_data.get('LinkedIn URL', ''), placeholder="https://linkedin.com/...")

    st.markdown("---")

    # Option to regenerate PDF for existing events
    regenerate_pdf = False
    if st.session_state.edit_mode:
        existing_pdf_id = event_data.get('Generated_PDF_ID', '')
        if existing_pdf_id:
            st.info("📄 This event has an existing PDF report. Check below to regenerate with the new template.")
            regenerate_pdf = st.checkbox(
                "🔄 Regenerate PDF Report with New Template",
                help="Check this to regenerate the PDF report using the updated professional template with all logos and embedded photos"
            )
            st.markdown("---")

    # File readiness checklist - shown before buttons so user knows what's still needed
    st.markdown("---")
    st.markdown("#### 📋 Submission Readiness")

    _atl = 'ATL School Activity' in program_driven_by
    file_checks = [
        ("Geotagged Photo 1", bool(geotag_photo1 or event_data.get('Geotag_Photo1_ID')), True),
        ("Geotagged Photo 2", bool(geotag_photo2 or event_data.get('Geotag_Photo2_ID')), True),
        ("Geotagged Photo 3", bool(geotag_photo3 or event_data.get('Geotag_Photo3_ID')), True),
        ("Normal Photo 1", bool(normal_photo1 or event_data.get('Normal_Photo1_ID')), True),
        ("Normal Photo 2", bool(normal_photo2 or event_data.get('Normal_Photo2_ID')), True),
        ("Normal Photo 3", bool(normal_photo3 or event_data.get('Normal_Photo3_ID')), True),
        ("Attendance Report", bool(attendance_report or event_data.get('Attendance_Report_ID')), True),
        ("Feedback Analysis", bool(feedback_analysis or event_data.get('Feedback_Analysis_ID')), not _atl),
        ("Event Agenda", bool(event_agenda or event_data.get('Event_Agenda_ID')), not _atl),
        ("Chief Guest Biodata", bool(chief_guest_biodata or event_data.get('Chief_Guest_Biodata_ID')), not _atl),
        ("Permission SOP", bool(permission_sop or event_data.get('Permission_SOP_ID')), True),
        ("Invitation/Brochure", bool(invitation_brochure or event_data.get('Invitation_Brochure_ID')), True),
    ]
    if expenditure > 0:
        file_checks.append(("UC/Bill Documents", bool(other_documents or event_data.get('Other_Documents_ID')), True))

    all_files_ready = all(ok for _, ok, required in file_checks if required)
    missing_count = sum(1 for _, ok, required in file_checks if required and not ok)

    if all_files_ready:
        st.success("✅ All required files uploaded — you can Save as Draft or Submit.")
    else:
        st.info(f"💾 You can **Save as Draft** now. Upload {missing_count} more required file(s) to enable Submit.")
    check_cols = st.columns(3)
    for i, (name, ok, required) in enumerate(file_checks):
        with check_cols[i % 3]:
            if ok:
                st.markdown(f"✅ {name}")
            elif not required:
                st.markdown(f"🔵 {name} *(optional)*")
            else:
                st.markdown(f"❌ {name}")

    st.markdown("---")

    # Submit buttons
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])

    with col2:
        if st.session_state.edit_mode:
            cancel_edit = st.button("❌ Cancel", use_container_width=True)
            if cancel_edit:
                st.session_state.edit_mode = False
                st.session_state.edit_event_data = None
                st.rerun()

    with col3:
        save_draft = st.button("💾 Save as Draft", use_container_width=True)

    with col4:
        submit_event = st.button(
            "✅ Submit Event",
            type="primary",
            use_container_width=True,
            disabled=not all_files_ready,
            help="Upload all required files to enable submission" if not all_files_ready else "Submit this event for admin review"
        )

    # Form validation and submission
    if save_draft or submit_event:
        errors = []

        if save_draft:
            # Minimal validation for draft — only the event name is required
            if not event_name:
                errors.append("Program/Activity Name is required to save a draft")

        if submit_event:
            # Full validation for final submission
            if not event_name:
                errors.append("Program/Activity Name is required")
            if not start_date or not end_date:
                errors.append("Start and End dates are required")
            if end_date < start_date:
                errors.append("End date must be same or after start date")
            if not objective:
                errors.append("Objective is required")
            if not benefits:
                errors.append("Benefits are required")
            if not brief_report:
                errors.append("Brief Description of the Activity is required")
            elif ValidationUtils.count_words(brief_report) < config.MIN_BRIEF_REPORT_WORDS:
                errors.append(f"Brief description must be at least {config.MIN_BRIEF_REPORT_WORDS} words")
            elif ValidationUtils.count_words(brief_report) > config.MAX_BRIEF_REPORT_WORDS:
                errors.append(f"Brief description must not exceed {config.MAX_BRIEF_REPORT_WORDS} words")
            if not venue_platform:
                errors.append("Venue / Platform is required")
            if not key_highlights:
                errors.append("Key Highlights are required")
            if not outcome:
                errors.append("Outcome of the Activity is required")

            if student_participants < config.MIN_STUDENT_PARTICIPANTS:
                errors.append(f"Minimum {config.MIN_STUDENT_PARTICIPANTS} student participants required")
            if level_number < config.MIN_EVENT_LEVEL:
                errors.append(f"Event level must be {config.MIN_EVENT_LEVEL} or higher")
            if ValidationUtils.count_words(objective) > config.MAX_OBJECTIVE_WORDS:
                errors.append(f"Objective must not exceed {config.MAX_OBJECTIVE_WORDS} words")
            if ValidationUtils.count_words(benefits) > config.MAX_BENEFITS_WORDS:
                errors.append(f"Benefits must not exceed {config.MAX_BENEFITS_WORDS} words")

            _no_spk = {"Club Activity", "Competition", "Hackathon", "Exhibition", "Tech/E-Fest", "Outreach Program", "Challenge"}
            if program_type not in _no_spk:
                if not speaker_names:
                    errors.append("Speaker Name(s) is required")
                if not speaker_designation:
                    errors.append("Speaker Designation(s) is required")
                if not speaker_organization:
                    errors.append("Speaker Organization(s) is required")
            if not program_driven_by:
                errors.append("Program Driven By is required (select 1 or 2 options)")
            if len(program_driven_by) > 2:
                errors.append("Program Driven By: maximum 2 options allowed")
            if len(sdg_goals) == 0:
                errors.append("At least one SDG Goal must be selected")
            if len(sdg_goals) > 4:
                errors.append("Maximum 4 SDG Goals can be selected")
            if not organizing_departments:
                errors.append("At least one Organizing Department must be selected")

            # All required files must exist — new upload OR previously stored from draft
            if not geotag_photo1 and not event_data.get('Geotag_Photo1_ID'):
                errors.append("Geotagged Photo 1 is required")
            if not geotag_photo2 and not event_data.get('Geotag_Photo2_ID'):
                errors.append("Geotagged Photo 2 is required")
            if not geotag_photo3 and not event_data.get('Geotag_Photo3_ID'):
                errors.append("Geotagged Photo 3 is required")
            if not normal_photo1 and not event_data.get('Normal_Photo1_ID'):
                errors.append("Normal Photo 1 is required")
            if not normal_photo2 and not event_data.get('Normal_Photo2_ID'):
                errors.append("Normal Photo 2 is required")
            if not normal_photo3 and not event_data.get('Normal_Photo3_ID'):
                errors.append("Normal Photo 3 is required")
            if not attendance_report and not event_data.get('Attendance_Report_ID'):
                errors.append("Attendance Report is required")
            atl_event = 'ATL School Activity' in program_driven_by
            if not atl_event:
                if not feedback_analysis and not event_data.get('Feedback_Analysis_ID'):
                    errors.append("Feedback Analysis Report is required")
                if not event_agenda and not event_data.get('Event_Agenda_ID'):
                    errors.append("Event Agenda is required")
                if not chief_guest_biodata and not event_data.get('Chief_Guest_Biodata_ID'):
                    errors.append("Chief Guest Biodata is required")
            if not permission_sop and not event_data.get('Permission_SOP_ID'):
                errors.append("Permission SOP with Principal Signature is required")
            if not invitation_brochure and not event_data.get('Invitation_Brochure_ID'):
                errors.append("Invitation/Brochure is required")
            if expenditure > 0 and not other_documents and not event_data.get('Other_Documents_ID'):
                errors.append("UC/Bill documents are required when expenditure is involved")

        if errors:
            for error in errors:
                st.error(f"❌ {error}")
        else:
            # Process submission
            try:
                sheets_manager = GoogleSheetsManager(sheets_client)
                drive_manager = GoogleDriveManager(drive_service)

                # Get or create drive folder
                with st.spinner("Creating Drive folder..."):
                    folder_id, folder_url = drive_manager.get_or_create_event_folder(
                        event_name,
                        event_id,
                        config.DRIVE_FOLDER_ID if config.DRIVE_FOLDER_ID != "YOUR_DRIVE_FOLDER_ID_HERE" else None
                    )

                # Initialize file IDs - keep existing IDs if already uploaded
                geotag_photo1_id = event_data.get('Geotag_Photo1_ID', '')
                geotag_photo2_id = event_data.get('Geotag_Photo2_ID', '')
                geotag_photo3_id = event_data.get('Geotag_Photo3_ID', '')
                normal_photo1_id = event_data.get('Normal_Photo1_ID', '')
                normal_photo2_id = event_data.get('Normal_Photo2_ID', '')
                normal_photo3_id = event_data.get('Normal_Photo3_ID', '')
                attendance_report_id = event_data.get('Attendance_Report_ID', '')
                feedback_analysis_id = event_data.get('Feedback_Analysis_ID', '')
                event_agenda_id = event_data.get('Event_Agenda_ID', '')
                chief_guest_biodata_id = event_data.get('Chief_Guest_Biodata_ID', '')
                permission_sop_id = event_data.get('Permission_SOP_ID', '')
                invitation_brochure_id = event_data.get('Invitation_Brochure_ID', '')
                other_documents_id = event_data.get('Other_Documents_ID', '')

                # Upload files to Drive - SMART UPLOAD: only upload NEW files
                # If file already exists (has ID), keep it unless user provides a new file
                with st.spinner("Uploading new files to Google Drive..."):
                    upload_count = 0

                    # Upload geotagged photos (only if NEW file provided by user)
                    if geotag_photo1:
                        new_id = drive_manager.upload_file(
                            geotag_photo1.read(),
                            f"geotag_photo1_{event_id}.jpg",
                            folder_id,
                            'image/jpeg'
                        )
                        if new_id:
                            geotag_photo1_id = new_id
                            upload_count += 1

                    if geotag_photo2:
                        new_id = drive_manager.upload_file(
                            geotag_photo2.read(),
                            f"geotag_photo2_{event_id}.jpg",
                            folder_id,
                            'image/jpeg'
                        )
                        if new_id:
                            geotag_photo2_id = new_id
                            upload_count += 1

                    if geotag_photo3:
                        new_id = drive_manager.upload_file(
                            geotag_photo3.read(),
                            f"geotag_photo3_{event_id}.jpg",
                            folder_id,
                            'image/jpeg'
                        )
                        if new_id:
                            geotag_photo3_id = new_id
                            upload_count += 1

                    # Upload normal photos (only if NEW file provided)
                    if normal_photo1:
                        new_id = drive_manager.upload_file(
                            normal_photo1.read(),
                            f"normal_photo1_{event_id}.jpg",
                            folder_id,
                            'image/jpeg'
                        )
                        if new_id:
                            normal_photo1_id = new_id
                            upload_count += 1

                    if normal_photo2:
                        new_id = drive_manager.upload_file(
                            normal_photo2.read(),
                            f"normal_photo2_{event_id}.jpg",
                            folder_id,
                            'image/jpeg'
                        )
                        if new_id:
                            normal_photo2_id = new_id
                            upload_count += 1

                    if normal_photo3:
                        new_id = drive_manager.upload_file(
                            normal_photo3.read(),
                            f"normal_photo3_{event_id}.jpg",
                            folder_id,
                            'image/jpeg'
                        )
                        if new_id:
                            normal_photo3_id = new_id
                            upload_count += 1

                    # Upload documents (only if NEW file provided)
                    if attendance_report:
                        file_ext = 'pdf' if attendance_report.name.endswith('.pdf') else 'jpg'
                        mime_type = 'application/pdf' if file_ext == 'pdf' else 'image/jpeg'
                        new_id = drive_manager.upload_file(
                            attendance_report.read(),
                            f"attendance_report_{event_id}.{file_ext}",
                            folder_id,
                            mime_type
                        )
                        if new_id:
                            attendance_report_id = new_id
                            upload_count += 1

                    if feedback_analysis:
                        new_id = drive_manager.upload_file(
                            feedback_analysis.read(),
                            f"feedback_analysis_{event_id}.pdf",
                            folder_id,
                            'application/pdf'
                        )
                        if new_id:
                            feedback_analysis_id = new_id
                            upload_count += 1

                    if event_agenda:
                        new_id = drive_manager.upload_file(
                            event_agenda.read(),
                            f"event_agenda_{event_id}.pdf",
                            folder_id,
                            'application/pdf'
                        )
                        if new_id:
                            event_agenda_id = new_id
                            upload_count += 1

                    if chief_guest_biodata:
                        new_id = drive_manager.upload_file(
                            chief_guest_biodata.read(),
                            f"chief_guest_biodata_{event_id}.pdf",
                            folder_id,
                            'application/pdf'
                        )
                        if new_id:
                            chief_guest_biodata_id = new_id
                            upload_count += 1

                    # Upload KPI Report if provided (for Calendar Activity - legacy support)
                    if kpi_report:
                        new_id = drive_manager.upload_file(
                            kpi_report.read(),
                            f"kpi_report_{event_id}.pdf",
                            folder_id,
                            'application/pdf'
                        )
                        if new_id:
                            kpi_report_id = new_id
                            upload_count += 1

                    # Upload Permission SOP with Principal Signature
                    if permission_sop:
                        file_ext = 'pdf' if permission_sop.name.endswith('.pdf') else 'jpg'
                        mime_type = 'application/pdf' if file_ext == 'pdf' else 'image/jpeg'
                        new_id = drive_manager.upload_file(
                            permission_sop.read(),
                            f"permission_sop_{event_id}.{file_ext}",
                            folder_id,
                            mime_type
                        )
                        if new_id:
                            permission_sop_id = new_id
                            upload_count += 1

                    # Upload Invitation/Brochure
                    if invitation_brochure:
                        file_ext = 'pdf' if invitation_brochure.name.endswith('.pdf') else 'jpg'
                        mime_type = 'application/pdf' if file_ext == 'pdf' else 'image/jpeg'
                        new_id = drive_manager.upload_file(
                            invitation_brochure.read(),
                            f"invitation_brochure_{event_id}.{file_ext}",
                            folder_id,
                            mime_type
                        )
                        if new_id:
                            invitation_brochure_id = new_id
                            upload_count += 1

                    # Upload Other Documents (UC/Bills)
                    if other_documents:
                        file_ext = 'pdf' if other_documents.name.endswith('.pdf') else 'jpg'
                        mime_type = 'application/pdf' if file_ext == 'pdf' else 'image/jpeg'
                        new_id = drive_manager.upload_file(
                            other_documents.read(),
                            f"other_documents_{event_id}.{file_ext}",
                            folder_id,
                            mime_type
                        )
                        if new_id:
                            other_documents_id = new_id
                            upload_count += 1

                    if upload_count > 0:
                        st.success(f"Uploaded {upload_count} new file(s)")

                # Generate PDF on submit or explicit regenerate — skip on draft saves (photos may be incomplete)
                pdf_report_id = event_data.get('Generated_PDF_ID', '')
                if (submit_event or regenerate_pdf) and (not pdf_report_id or regenerate_pdf):
                    spinner_message = "Regenerating PDF report with new template..." if regenerate_pdf else "Generating PDF report..."
                    with st.spinner(spinner_message):
                        try:
                            from pdf_generator import IICReportGenerator
                            from io import BytesIO

                            # Debug: show what document IDs we have
                            st.info(f"Merging documents: Attendance={bool(attendance_report_id)}, Feedback={bool(feedback_analysis_id)}, Agenda={bool(event_agenda_id)}, Biodata={bool(chief_guest_biodata_id)}, SOP={bool(permission_sop_id)}, Brochure={bool(invitation_brochure_id)}, Other={bool(other_documents_id)}, KPI={bool(kpi_report_id)}")

                            # Prepare data for PDF with all fields
                            pdf_event_data = {
                                'Event ID': event_id,
                                'Program Name': event_name,
                                'Academic Year': academic_year,
                                'Quarter': quarter,
                                'Program Driven By': ','.join(program_driven_by) if program_driven_by else '',
                                'Activity Led By': activity_led_by,
                                'Organizing Departments': ','.join(organizing_departments) if organizing_departments else '',
                                'Professional Society Club': professional_society_club,
                                'SDG Goals': ','.join(sdg_goals) if sdg_goals else '',
                                'Program Outcomes': ','.join(program_outcomes) if program_outcomes else '',
                                'Program Type': program_type,
                                'Program Theme': program_theme,
                                'Objective': objective,
                                'Benefits': benefits,
                                'Brief Report': brief_report,
                                'Key Highlights': key_highlights,
                                'Outcome': outcome,
                                'Feedback Reflection': feedback_reflection,
                                'Organizing Team': organizing_team,
                                'Venue Platform': venue_platform,
                                'Start Date': start_date.strftime('%Y-%m-%d'),
                                'End Date': end_date.strftime('%Y-%m-%d'),
                                'Duration (Hrs)': duration,
                                'Event Level': level_number,
                                'Mode of Delivery': mode_delivery,
                                'Student Participants': student_participants,
                                'Faculty Participants': faculty_participants,
                                'External Participants': external_participants,
                                'Expenditure Amount': expenditure,
                                'Remark': remark or 'N/A',
                                'Session Video URL': session_video_url or '',
                                'Twitter URL': twitter_url or '',
                                'Facebook URL': facebook_url or '',
                                'Instagram URL': instagram_url or '',
                                'LinkedIn URL': linkedin_url or '',
                                'Speaker Names': speaker_names,
                                'Speaker Designation': speaker_designation,
                                'Speaker Organization': speaker_organization,
                                'Speaker Brief': speaker_brief,
                                # Photo IDs
                                'Geotag_Photo1_ID': geotag_photo1_id,
                                'Geotag_Photo2_ID': geotag_photo2_id,
                                'Geotag_Photo3_ID': geotag_photo3_id,
                                'Normal_Photo1_ID': normal_photo1_id,
                                'Normal_Photo2_ID': normal_photo2_id,
                                'Normal_Photo3_ID': normal_photo3_id,
                                # Document IDs
                                'Attendance_Report_ID': attendance_report_id,
                                'Feedback_Analysis_ID': feedback_analysis_id,
                                'Event_Agenda_ID': event_agenda_id,
                                'Chief_Guest_Biodata_ID': chief_guest_biodata_id,
                                'Permission_SOP_ID': permission_sop_id or '',
                                'Invitation_Brochure_ID': invitation_brochure_id or '',
                                'Other_Documents_ID': other_documents_id or '',
                                'KPI_Report_ID': kpi_report_id or ''
                            }

                            # Generate PDF with drive_manager for embedding photos
                            pdf_buffer = BytesIO()

                            # Show which documents will be merged
                            doc_info = []
                            if attendance_report_id:
                                doc_info.append(f"Attendance: {str(attendance_report_id)[:40]}")
                            if feedback_analysis_id:
                                doc_info.append(f"Feedback: {str(feedback_analysis_id)[:40]}")
                            if event_agenda_id:
                                doc_info.append(f"Agenda: {str(event_agenda_id)[:40]}")
                            if chief_guest_biodata_id:
                                doc_info.append(f"Biodata: {str(chief_guest_biodata_id)[:40]}")
                            if permission_sop_id:
                                doc_info.append(f"SOP: {str(permission_sop_id)[:40]}")
                            if invitation_brochure_id:
                                doc_info.append(f"Brochure: {str(invitation_brochure_id)[:40]}")
                            if other_documents_id:
                                doc_info.append(f"Other: {str(other_documents_id)[:40]}")
                            if kpi_report_id:
                                doc_info.append(f"KPI: {str(kpi_report_id)[:40]}")

                            if doc_info:
                                st.info(f"Documents to merge: {len(doc_info)} files")
                                for d in doc_info:
                                    st.caption(d)
                            else:
                                st.warning("No document IDs found to merge")

                            generator = IICReportGenerator(pdf_event_data, logo_path="logos", drive_manager=drive_manager)

                            # TEST: Try downloading one file to check if it works
                            test_file_id = attendance_report_id or feedback_analysis_id or event_agenda_id
                            if test_file_id:
                                st.info(f"Testing download of: {test_file_id}")
                                test_content = drive_manager.download_file(test_file_id)
                                if test_content:
                                    st.success(f"Download SUCCESS: {len(test_content)} bytes")
                                else:
                                    st.error(f"Download FAILED: {drive_manager.last_download_error}")

                            generator.generate_pdf(pdf_buffer)

                            # Show merge status - ALWAYS show to debug
                            st.markdown("---")
                            st.markdown("### PDF Merge Status:")
                            if hasattr(generator, 'merge_status') and generator.merge_status:
                                for status in generator.merge_status:
                                    if "MERGED" in status or "TOTAL" in status:
                                        st.success(status)
                                    elif "FAILED" in status or "ERROR" in status:
                                        st.error(status)
                                    elif "SKIPPED" in status:
                                        st.warning(status)
                                    else:
                                        st.info(status)
                            else:
                                st.error("No merge status available - merge may have been skipped")

                            # Upload PDF to Drive
                            pdf_buffer.seek(0)
                            pdf_report_id = drive_manager.upload_file(
                                pdf_buffer.read(),
                                f"IICReport_{event_id}-IC201912089.pdf",
                                folder_id,
                                'application/pdf'
                            )
                        except Exception as pdf_error:
                            st.warning(f"PDF generation skipped: {str(pdf_error)}")
                            pdf_report_id = ''

                # Prepare event data
                now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                new_event_data = {
                    'Event ID': event_id,
                    'User Email': st.session_state.user_email,
                    'Academic Year': academic_year,
                    'Quarter': quarter,
                    'Program Name': event_name,
                    'Program Type': program_type,
                    'Program Driven By': ','.join(program_driven_by) if program_driven_by else '',
                    'Activity Led By': activity_led_by,
                    'Program Theme': program_theme,
                    'Organizing Departments': ','.join(organizing_departments) if organizing_departments else '',
                    'Professional Society Club': professional_society_club,
                    'SDG Goals': ','.join(sdg_goals) if sdg_goals else '',
                    'Program Outcomes': ','.join(program_outcomes) if program_outcomes else '',
                    'Duration (Hrs)': duration,
                    'Event Level': event_level,
                    'Mode of Delivery': mode_delivery,
                    'Start Date': start_date.strftime('%Y-%m-%d'),
                    'End Date': end_date.strftime('%Y-%m-%d'),
                    'Student Participants': student_participants,
                    'Faculty Participants': faculty_participants,
                    'External Participants': external_participants,
                    'Expenditure Amount': expenditure,
                    'Remark': remark,
                    'Objective': objective,
                    'Benefits': benefits,
                    'Speaker Names': speaker_names,
                    'Speaker Designation': speaker_designation,
                    'Speaker Organization': speaker_organization,
                    'Speaker Brief': speaker_brief,
                    'Session Video URL': session_video_url,
                    'Venue Platform': venue_platform,
                    'Brief Report': brief_report,
                    'Key Highlights': key_highlights,
                    'Outcome': outcome,
                    'Feedback Reflection': feedback_reflection,
                    'Organizing Team': organizing_team,
                    'Geotag_Photo1_ID': geotag_photo1_id or '',
                    'Geotag_Photo2_ID': geotag_photo2_id or '',
                    'Geotag_Photo3_ID': geotag_photo3_id or '',
                    'Normal_Photo1_ID': normal_photo1_id or '',
                    'Normal_Photo2_ID': normal_photo2_id or '',
                    'Normal_Photo3_ID': normal_photo3_id or '',
                    'Attendance_Report_ID': attendance_report_id or '',
                    'Feedback_Analysis_ID': feedback_analysis_id or '',
                    'Event_Agenda_ID': event_agenda_id or '',
                    'Chief_Guest_Biodata_ID': chief_guest_biodata_id or '',
                    'Permission_SOP_ID': permission_sop_id or '',
                    'Invitation_Brochure_ID': invitation_brochure_id or '',
                    'Other_Documents_ID': other_documents_id or '',
                    'KPI_Report_ID': kpi_report_id or '',
                    'Generated_PDF_ID': pdf_report_id or '',
                    'Signed_PDF_ID': event_data.get('Signed_PDF_ID', ''),
                    'Twitter URL': twitter_url,
                    'Facebook URL': facebook_url,
                    'Instagram URL': instagram_url,
                    'LinkedIn URL': linkedin_url,
                    'Created Date': event_data.get('Created Date', now),
                    'Last Modified': now,
                    'Status': 'Submitted' if submit_event else 'Draft',
                    'Admin_Approval_Status': event_data.get('Admin_Approval_Status', 'Pending'),
                    'Drive Folder URL': folder_url or ''
                }

                # Save to Google Sheets
                with st.spinner("Saving event data..."):
                    success = sheets_manager.save_event(new_event_data)

                if success:
                    st.success(f"✅ Event {'updated' if st.session_state.edit_mode else 'created'} and {'submitted' if submit_event else 'saved as draft'} successfully!")

                    # Show PDF regeneration message if applicable
                    if regenerate_pdf and pdf_report_id:
                        st.success("📄 PDF report regenerated with new professional template including all logos and embedded photos!")
                    elif pdf_report_id and not regenerate_pdf:
                        st.success("📄 PDF report generated and uploaded to Google Drive!")

                    st.balloons()

                    # Reset form
                    st.session_state.edit_mode = False
                    st.session_state.edit_event_data = None

                    st.info("You can view your event in the 'My Events' tab.")

                    # Show pending approval message instead of Drive folder link
                    if submit_event:
                        st.warning("⏳ Your event has been submitted and is pending admin approval. You will be notified once approved.")
                else:
                    st.error("Failed to save event. Please try again.")

            except Exception as e:
                st.error(f"Error submitting event: {str(e)}")

    st.markdown('</div>', unsafe_allow_html=True)

def show_user_events(sheets_client):
    """Display user's events with approval status and signed PDF download"""
    st.markdown('<div class="form-container">', unsafe_allow_html=True)

    st.markdown("#### My Events")

    try:
        sheets_manager = GoogleSheetsManager(sheets_client)
        user_events = sheets_manager.get_user_events(st.session_state.user_email)

        if user_events:
            # Filter options
            col1, col2, col3 = st.columns(3)
            with col1:
                status_filter = st.selectbox(
                    "Filter by Status",
                    ["All", "Submitted", "Draft", "Approved", "Rejected"]
                )

            with col2:
                quarter_filter = st.selectbox(
                    "Filter by Quarter",
                    ["All", "Quarter 1", "Quarter 2", "Quarter 3", "Quarter 4"]
                )

            with col3:
                search_term = st.text_input("Search by name", placeholder="Event name...")

            # Apply filters
            filtered_events = user_events
            if status_filter != "All":
                if status_filter in ["Approved", "Rejected"]:
                    filtered_events = [e for e in filtered_events if e.get('Admin_Approval_Status') == status_filter]
                else:
                    filtered_events = [e for e in filtered_events if e.get('Status') == status_filter]
            if quarter_filter != "All":
                filtered_events = [e for e in filtered_events if quarter_filter in str(e.get('Quarter', ''))]
            if search_term:
                filtered_events = [e for e in filtered_events if search_term.lower() in str(e.get('Program Name', '')).lower()]

            st.write(f"**Showing {len(filtered_events)} event(s)**")

            # Display events
            for event in filtered_events:
                approval_status = event.get('Admin_Approval_Status', 'Pending')
                status_icon = "🟡" if approval_status == "Pending" else ("🟢" if approval_status == "Approved" else "🔴")

                with st.expander(f"📌 {event.get('Program Name')} - {event.get('Start Date')} - {status_icon} {approval_status}"):
                    col1, col2 = st.columns(2)

                    with col1:
                        st.write(f"**Event ID:** {event.get('Event ID')}")
                        st.write(f"**Academic Year:** {event.get('Academic Year')}")
                        st.write(f"**Quarter:** {event.get('Quarter')}")
                        st.write(f"**Program Type:** {event.get('Program Type')}")
                        st.write(f"**Level:** {event.get('Event Level')}")
                        st.write(f"**Duration:** {event.get('Duration (Hrs)')} hrs")
                        st.write(f"**Mode:** {event.get('Mode of Delivery')}")
                        st.write(f"**Venue/Platform:** {event.get('Venue Platform', 'N/A')}")

                    with col2:
                        st.write(f"**Start Date:** {event.get('Start Date')}")
                        st.write(f"**End Date:** {event.get('End Date')}")
                        st.write(f"**Student Participants:** {event.get('Student Participants')}")
                        st.write(f"**Faculty Participants:** {event.get('Faculty Participants')}")
                        st.write(f"**Program Driven By:** {event.get('Program Driven By', 'N/A')}")
                        st.write(f"**Submission Status:** {event.get('Status')}")
                        st.write(f"**Last Modified:** {event.get('Last Modified')}")

                    st.write("---")
                    st.write(f"**Objective:** {event.get('Objective')}")
                    if event.get('Benefits'):
                        st.write(f"**Benefits:** {event.get('Benefits')}")
                    if event.get('Key Highlights'):
                        st.write(f"**Key Highlights:** {event.get('Key Highlights')}")
                    if event.get('Outcome'):
                        st.write(f"**Outcome:** {event.get('Outcome')}")

                    # Approval Status Section
                    st.write("---")
                    st.markdown("**📋 Approval Status:**")

                    if approval_status == "Pending":
                        st.warning("⏳ Your event is pending admin approval. Please wait for the admin to review and approve your submission.")

                    elif approval_status == "Approved":
                        st.success("✅ Your event has been approved!")
                        approval_date = event.get('Approval_Date', '')
                        approved_by = event.get('Approved_By', '')
                        if approval_date:
                            st.write(f"**Approved on:** {approval_date}")
                        if approved_by:
                            st.write(f"**Approved by:** {approved_by}")

                        # Show Signed PDF download if available
                        signed_pdf_id = event.get('Signed_PDF_ID', '')
                        if signed_pdf_id:
                            st.markdown("---")
                            st.markdown("**📄 Signed Report (Final):**")
                            signed_pdf_url = f"https://drive.google.com/file/d/{signed_pdf_id}/view"
                            st.markdown(f"### [📥 Download Signed PDF Report]({signed_pdf_url})")
                            st.info("This is the final signed report. Please download and keep for your records.")
                        else:
                            st.info("Signed PDF will be available soon after admin uploads it.")

                    elif approval_status == "Rejected":
                        st.error("❌ Your event has been rejected.")
                        rejection_reason = event.get('Rejection_Reason', '')
                        if rejection_reason:
                            st.write(f"**Reason:** {rejection_reason}")
                        st.info("Please edit and resubmit your event after making the necessary corrections.")

                    # Action buttons - only show Edit for Draft or Rejected events
                    st.write("---")
                    btn_col1, btn_col2, btn_col3 = st.columns([3, 1, 1])

                    # Only allow editing if not approved
                    if approval_status != "Approved":
                        with btn_col2:
                            if st.button(f"✏️ Edit", key=f"edit_{event.get('Event ID')}", use_container_width=True):
                                st.session_state.edit_mode = True
                                st.session_state.edit_event_data = event
                                st.success("Loading event for editing...")
                                st.rerun()

                        with btn_col3:
                            if event.get('Status') == 'Draft':
                                if st.button(f"🗑️ Delete", key=f"delete_{event.get('Event ID')}", use_container_width=True):
                                    if sheets_manager.delete_event(event.get('Event ID')):
                                        st.success("Event deleted successfully!")
                                        st.rerun()
                                    else:
                                        st.error("Failed to delete event.")
                    else:
                        st.info("This event has been approved and cannot be edited.")

        else:
            st.info("No events found. Create your first event!")

    except Exception as e:
        st.error(f"Error loading events: {str(e)}")

    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
