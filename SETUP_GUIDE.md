# Complete Setup Guide for IIC Event Submission Portal

## Table of Contents
1. [Google Cloud Setup](#google-cloud-setup)
2. [Google Sheets Setup](#google-sheets-setup)
3. [Google Drive Setup](#google-drive-setup)
4. [Application Installation](#application-installation)
5. [Running the Application](#running-the-application)
6. [Troubleshooting](#troubleshooting)

---

## Google Cloud Setup

### Step 1: Create Google Cloud Project

1. **Go to Google Cloud Console**
   - Visit: https://console.cloud.google.com/
   - Sign in with your Google account

2. **Create New Project**
   - Click on project dropdown (top left)
   - Click "New Project"
   - Enter project name: `IIC-Event-Portal`
   - Click "Create"
   - Wait for project creation (1-2 minutes)

### Step 2: Enable Required APIs

1. **Navigate to APIs & Services**
   - From left menu: "APIs & Services" > "Library"

2. **Enable Google Sheets API**
   - Search for "Google Sheets API"
   - Click on it
   - Click "Enable"
   - Wait for confirmation

3. **Enable Google Drive API**
   - Click "Go back" or return to Library
   - Search for "Google Drive API"
   - Click on it
   - Click "Enable"
   - Wait for confirmation

### Step 3: Create Service Account

1. **Go to Credentials**
   - From left menu: "APIs & Services" > "Credentials"

2. **Create Service Account**
   - Click "+ CREATE CREDENTIALS"
   - Select "Service Account"

3. **Service Account Details**
   - Service account name: `iic-event-portal`
   - Service account ID: `iic-event-portal` (auto-generated)
   - Description: `Service account for IIC Event Portal`
   - Click "CREATE AND CONTINUE"

4. **Grant Permissions**
   - Select role: "Editor"
   - Click "CONTINUE"
   - Skip optional steps
   - Click "DONE"

### Step 4: Generate Credentials JSON

1. **Find Your Service Account**
   - In Credentials page, find your service account in the list
   - Click on the service account email

2. **Create Key**
   - Go to "KEYS" tab
   - Click "ADD KEY"
   - Select "Create new key"
   - Choose "JSON" format
   - Click "CREATE"

3. **Save the JSON File**
   - A file will be downloaded automatically
   - Rename it to `credentials.json`
   - Save it in your project folder
   - **IMPORTANT**: Keep this file secure, never share it

4. **Copy Service Account Email**
   - From the Keys page, copy the service account email
   - Format: `iic-event-portal@project-id.iam.gserviceaccount.com`
   - You'll need this for the next step

---

## Google Sheets Setup

### Step 1: Create Spreadsheet

1. **Create New Spreadsheet**
   - Go to: https://sheets.google.com
   - Click "Blank" to create new spreadsheet
   - Rename it: "IIC Event Portal Database"

2. **Get Spreadsheet ID**
   - Look at the URL in your browser
   - Format: `https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit`
   - Copy the `SPREADSHEET_ID` part
   - Save it - you'll need this later

### Step 2: Share with Service Account

1. **Open Sharing Settings**
   - Click "Share" button (top right)

2. **Add Service Account**
   - Paste the service account email you copied earlier
   - Format: `iic-event-portal@project-id.iam.gserviceaccount.com`
   - Change permission to "Editor"
   - **UNCHECK** "Notify people"
   - Click "Share"

### Step 3: Add Users

The application will auto-create "Users" and "Events" sheets, but you need to add authorized users:

1. **Wait for First Run**
   - Run the application once (it will create the sheets)
   - OR manually create a sheet named "Users"

2. **Add User Emails**
   - Go to the "Users" sheet
   - In cell A1, type: `Email`
   - Starting from A2, add user emails:
   ```
   Row 1: Email
   Row 2: coordinator@college.edu
   Row 3: faculty1@college.edu
   Row 4: faculty2@college.edu
   ```

3. **Important Notes**
   - Only emails in this list can login
   - Emails are case-sensitive
   - No spaces before or after email addresses

---

## Google Drive Setup

### Step 1: Verify Drive API

1. **Check API Status**
   - Go to: https://console.cloud.google.com/
   - Navigate to "APIs & Services" > "Dashboard"
   - Verify "Google Drive API" is listed and enabled

### Step 2: Test Drive Access

The application will automatically:
- Create folders for each event
- Upload photos and reports to these folders
- Generate public viewing links

**No manual Drive setup required!**

---

## Application Installation

### Step 1: Install Python

1. **Check Python Version**
   ```bash
   python --version
   ```
   - Should be 3.8 or higher
   - If not installed, download from: https://www.python.org/downloads/

2. **Verify pip**
   ```bash
   pip --version
   ```

### Step 2: Install Dependencies

1. **Open Command Prompt/Terminal**
   ```bash
   cd "c:\imman\2025_26 EVEN SEM\JESUS IIC\JESUS HIVE SOFTWARE"
   ```

2. **Install Requirements**
   ```bash
   pip install -r requirements.txt
   ```

3. **Wait for Installation**
   - This may take 2-5 minutes
   - All required packages will be installed

### Step 3: Place Credentials File

1. **Move credentials.json**
   - Copy the `credentials.json` file you downloaded earlier
   - Place it in the project folder:
   ```
   c:\imman\2025_26 EVEN SEM\JESUS IIC\JESUS HIVE SOFTWARE\credentials.json
   ```

2. **Verify File Location**
   - The file should be in the same folder as `app.py`

---

## Running the Application

### Step 1: Start Streamlit

1. **Open Command Prompt**
   ```bash
   cd "c:\imman\2025_26 EVEN SEM\JESUS IIC\JESUS HIVE SOFTWARE"
   ```

2. **Run the App**
   ```bash
   streamlit run app.py
   ```

3. **Wait for Browser**
   - Application will automatically open in browser
   - Default URL: http://localhost:8501
   - If not, manually open the URL shown in terminal

### Step 2: Configure Application

1. **Upload Credentials**
   - In the sidebar, click "Upload credentials.json"
   - Select your `credentials.json` file
   - Wait for "Credentials loaded successfully!" message

2. **Enter Spreadsheet ID**
   - In the sidebar, paste your Google Sheets ID
   - The ID you copied earlier from the spreadsheet URL

### Step 3: Login

1. **Enter Email**
   - Type your registered email address
   - Must be in the "Users" sheet of your spreadsheet

2. **Click Login**
   - If successful, you'll see the dashboard
   - If error, verify email is in Users sheet

### Step 4: Create First Event

1. **Go to "Create Event" Tab**
   - Fill in all required fields (marked with *)
   - Watch for automated validations

2. **Upload Files**
   - Photograph 1 (required)
   - Photograph 2 (optional)
   - Report PDF (required for submission)

3. **Submit**
   - Click "Save as Draft" to save without submitting
   - Click "Submit Event" for final submission

---

## Troubleshooting

### Issue 1: "Error loading credentials"

**Solution:**
1. Verify `credentials.json` is in the correct folder
2. Check file is valid JSON (open in text editor)
3. Re-download from Google Cloud Console if corrupted

### Issue 2: "Email not found in the system"

**Solution:**
1. Open your Google Spreadsheet
2. Go to "Users" sheet
3. Verify email is listed (check for typos)
4. Add email if missing
5. Ensure no extra spaces

### Issue 3: "Error setting up spreadsheet"

**Solution:**
1. Verify Spreadsheet ID is correct
2. Check spreadsheet is shared with service account email
3. Ensure service account has "Editor" permission
4. Verify Google Sheets API is enabled

### Issue 4: "Permission denied" for Drive

**Solution:**
1. Go to Google Cloud Console
2. Check Google Drive API is enabled
3. Verify service account has correct roles
4. Re-create service account key if needed

### Issue 5: Application won't start

**Solution:**
1. Check Python version: `python --version`
2. Reinstall dependencies: `pip install -r requirements.txt`
3. Check for error messages in terminal
4. Verify all files are in correct location

### Issue 6: Images not uploading

**Solution:**
1. Check image size (max 2MB)
2. Verify format (JPG, JPEG, PNG only)
3. Check Google Drive API is enabled
4. Check internet connection

---

## Quick Reference

### File Structure
```
JESUS HIVE SOFTWARE/
├── app.py                    # Main application
├── requirements.txt          # Dependencies
├── credentials.json          # YOUR credentials (don't share)
├── README.md                # Main documentation
├── SETUP_GUIDE.md           # This file
└── .gitignore               # Git ignore rules
```

### Important URLs
- Google Cloud Console: https://console.cloud.google.com/
- Google Sheets: https://sheets.google.com
- Google Drive: https://drive.google.com

### Key Commands
```bash
# Install dependencies
pip install -r requirements.txt

# Run application
streamlit run app.py

# Check Python version
python --version

# Check pip version
pip --version
```

### Service Account Email Format
```
iic-event-portal@your-project-id.iam.gserviceaccount.com
```

### Spreadsheet ID Location
```
https://docs.google.com/spreadsheets/d/SPREADSHEET_ID_HERE/edit
                                        ^^^^^^^^^^^^^^^^^^^
                                        Copy this part
```

---

## Post-Setup Checklist

- [ ] Google Cloud project created
- [ ] Google Sheets API enabled
- [ ] Google Drive API enabled
- [ ] Service account created
- [ ] credentials.json downloaded and placed in project folder
- [ ] Google Spreadsheet created
- [ ] Spreadsheet shared with service account email
- [ ] User emails added to Users sheet
- [ ] Python 3.8+ installed
- [ ] Dependencies installed (requirements.txt)
- [ ] Application runs successfully
- [ ] Can login with registered email
- [ ] Can create and submit events
- [ ] Files upload to Google Drive
- [ ] Data saves to Google Sheets

---

## Next Steps After Setup

1. **Add More Users**
   - Update the "Users" sheet with all coordinator emails

2. **Test the System**
   - Create a test event
   - Upload sample files
   - Verify data in Google Sheets
   - Check files in Google Drive

3. **Train Users**
   - Share user credentials
   - Provide training on form filling
   - Explain validation rules

4. **Monitor Usage**
   - Check Google Cloud Console for API usage
   - Review events in Google Sheets
   - Monitor Drive storage

5. **Backup**
   - Regularly download Google Sheets as backup
   - Keep credentials.json in secure location

---

## Support Contacts

**Technical Issues:**
- Dr. Dipan Sahu
- Email: dipan.sahu@aicte-india.org
- Phone: 011 2958 1226

**IIC Regional Coordinators:**
- Check page 9 of the IIC document for zone-wise contacts

---

**Setup Complete! 🎉**

You're now ready to use the IIC Event Submission Portal.
