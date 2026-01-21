# IIC Event Portal - Simple Deployment Guide

## 🚀 One-Time Setup (5 Minutes)

This guide will help you deploy the IIC Event Submission Portal with a permanent configuration that runs forever without needing repeated setup.

---

## Step 1: Google Cloud Setup (One Time)

### Create Service Account

1. **Go to Google Cloud Console**
   - Visit: https://console.cloud.google.com/
   - Create project: "IIC-Event-Portal"

2. **Enable APIs**
   - Enable "Google Sheets API"
   - Enable "Google Drive API"

3. **Create Service Account**
   - Go to "APIs & Services" → "Credentials"
   - Create service account: `iic-event-portal`
   - Grant role: "Editor"

4. **Download credentials.json**
   - Create JSON key
   - Download and save as `credentials.json`
   - Place in your project folder
   - **Copy the service account email** (e.g., `iic-event-portal@...iam.gserviceaccount.com`)

---

## Step 2: Google Sheets Setup (One Time)

### Create and Configure Spreadsheet

1. **Create Spreadsheet**
   - Go to: https://sheets.google.com
   - Create new sheet: "IIC Event Portal Database"
   - Note the Spreadsheet ID from URL:
     ```
     https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit
     ```

2. **Share with Service Account**
   - Click "Share"
   - Add service account email
   - Grant "Editor" access
   - Uncheck "Notify people"

3. **Your Spreadsheet ID**
   ```
   1A-rTshHRACRejTUDSvXuGfwzLzbddNqhm_w1e6SHXyY
   ```
   ✅ Already configured in [config.py](config.py)

---

## Step 3: Google Drive Setup (One Time)

### Create Main Events Folder

1. **Create Folder in Drive**
   - Go to: https://drive.google.com
   - Create a folder named: "IIC Events 2025-26"
   - Open the folder

2. **Get Folder ID**
   - Copy the folder ID from URL:
     ```
     https://drive.google.com/drive/folders/FOLDER_ID_HERE
     ```

3. **Share with Service Account**
   - Click "Share" on the folder
   - Add service account email
   - Grant "Editor" access

4. **Update config.py**
   - Open `config.py`
   - Replace `YOUR_DRIVE_FOLDER_ID_HERE` with your folder ID
   - Save the file

**How it works:**
- The app will automatically create subfolders for each event inside this main folder
- Folder structure will be: `IIC Events 2025-26 > Event Name > files`

---

## Step 4: Add Users (One Time)

### Add Authorized Emails

1. **Run the app once** (it will create the sheets)
   ```bash
   streamlit run app.py
   ```

2. **Add user emails to Google Sheets**
   - Open your spreadsheet
   - Go to "Users" sheet
   - Add emails starting from row 2:
     ```
     Row 1: Email
     Row 2: coordinator@college.edu
     Row 3: faculty1@college.edu
     Row 4: faculty2@college.edu
     ```

---

## Step 5: Deploy Permanently

### Option A: Deploy on Streamlit Cloud (Recommended)

**Free, permanent hosting with automatic restarts**

1. **Push to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git push origin main
   ```

2. **Deploy on Streamlit Cloud**
   - Go to: https://share.streamlit.io
   - Sign in with GitHub
   - Click "New app"
   - Select your repository
   - Set main file: `app.py`
   - Click "Deploy"

3. **Add Secrets**
   - In Streamlit Cloud dashboard, go to app settings
   - Add secrets (paste your `credentials.json` content):
   ```toml
   # .streamlit/secrets.toml format
   [gcp_service_account]
   type = "service_account"
   project_id = "your-project-id"
   private_key_id = "key-id"
   private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
   client_email = "your-service-account@project.iam.gserviceaccount.com"
   client_id = "123456789"
   auth_uri = "https://accounts.google.com/o/oauth2/auth"
   token_uri = "https://oauth2.googleapis.com/token"
   auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
   client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/..."
   ```

4. **Your app is live!** 🎉
   - URL: `https://your-app-name.streamlit.app`
   - Runs 24/7 automatically
   - No maintenance required

### Option B: Deploy on Local Server

**For college servers or local hosting**

1. **Install as Service (Windows)**

   Create `run_iic_portal.bat`:
   ```batch
   @echo off
   cd "c:\imman\2025_26 EVEN SEM\JESUS IIC\JESUS HIVE SOFTWARE"
   streamlit run app.py --server.port 8501 --server.headless true
   ```

   Create Windows Task:
   - Open Task Scheduler
   - Create Basic Task: "IIC Portal"
   - Trigger: "At startup"
   - Action: Start program `run_iic_portal.bat`
   - ✅ Done! Runs automatically on boot

2. **Install as Service (Linux)**

   Create `/etc/systemd/system/iic-portal.service`:
   ```ini
   [Unit]
   Description=IIC Event Submission Portal
   After=network.target

   [Service]
   Type=simple
   User=your-user
   WorkingDirectory=/path/to/JESUS HIVE SOFTWARE
   ExecStart=/usr/local/bin/streamlit run app.py --server.port 8501 --server.headless true
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

   Enable and start:
   ```bash
   sudo systemctl enable iic-portal
   sudo systemctl start iic-portal
   sudo systemctl status iic-portal
   ```

---

## ✅ Configuration Checklist

Before deploying, verify:

- [ ] `credentials.json` placed in project folder
- [ ] `config.py` updated with:
  - [x] `SPREADSHEET_ID = "1A-rTshHRACRejTUDSvXuGfwzLzbddNqhm_w1e6SHXyY"` ✓
  - [ ] `DRIVE_FOLDER_ID = "your-drive-folder-id"` (update this!)
- [ ] Google Sheets shared with service account
- [ ] Google Drive folder shared with service account
- [ ] User emails added to "Users" sheet
- [ ] App tested locally with `streamlit run app.py`

---

## 🎯 What's Fixed in This Version

### 1. ✅ No More Credential Uploads
- Credentials loaded automatically from `credentials.json`
- File stays in server, no need to upload every time

### 2. ✅ Fixed Google Sheets ID
- Hardcoded in `config.py`
- Never needs to be entered again

### 3. ✅ Event-Based Drive Folders
- Creates folder by event name (not event ID)
- Example: "Workshop on AI Tools" becomes a folder
- All event files stored in that folder
- Nested under main Drive folder

### 4. ✅ Date Validation Fixed
- End date automatically set to minimum of start date
- Cannot select end date before start date
- Visual error if dates are invalid

### 5. ✅ Edit Function Fixed
- Click "Edit" loads all event data into form
- Shows existing files with links
- Upload new files to replace old ones
- Cancel button to exit edit mode
- Properly saves updates to same event ID

### 6. ✅ Persistent Storage
- Uses `@st.cache_resource` for Google API connections
- Connections cached and reused
- No pickle files needed
- Runs forever without issues

---

## 📝 config.py File

Update this file with your values:

```python
# Google Sheets Configuration
SPREADSHEET_ID = "1A-rTshHRACRejTUDSvXuGfwzLzbddNqhm_w1e6SHXyY"  # ✅ Already set

# Google Drive Configuration
DRIVE_FOLDER_ID = "YOUR_DRIVE_FOLDER_ID_HERE"  # ⚠️ UPDATE THIS!

# Service Account Credentials File
CREDENTIALS_FILE = "credentials.json"  # ✅ Make sure file exists
```

---

## 🔄 How File Upload Works Now

1. **User creates event** → Enters event name "AI Workshop"
2. **App creates folder** → `IIC Events 2025-26/AI Workshop/`
3. **User uploads files** → Saved to that folder
4. **User edits event** → Same folder reused
5. **New files uploaded** → Replace old files in same folder
6. **Result** → Clean organization by event name

---

## 🌐 Access the App

After deployment:

### Local Server:
```
http://localhost:8501
```

### Streamlit Cloud:
```
https://your-app-name.streamlit.app
```

### College Network:
```
http://server-ip:8501
```

---

## 📞 Support

If you encounter issues:

1. **Check credentials.json** - Make sure it's in the right folder
2. **Check config.py** - Verify DRIVE_FOLDER_ID is updated
3. **Check Google Sheets** - Ensure service account has access
4. **Check Google Drive** - Ensure service account has access to main folder
5. **Check Users sheet** - Ensure emails are added correctly

---

## 🎉 You're Done!

Your IIC Event Portal is now:
- ✅ Permanently configured
- ✅ No repeated setup needed
- ✅ Runs 24/7 automatically
- ✅ All data in Google Sheets
- ✅ All files in Google Drive
- ✅ Edit functionality working
- ✅ Date validation working

**Just share the URL with your coordinators and they're ready to submit events!**
