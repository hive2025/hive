# Google Drive Setup Guide - Fixing Storage Quota Error

## 🔴 The Problem

Service accounts **cannot upload files to personal Drive folders** because they don't have storage quota. You'll get this error:

```
Service Accounts do not have storage quota.
```

## ✅ The Solution: Use Shared Drive (Recommended)

### What is a Shared Drive?
A Shared Drive (formerly Team Drive) is a special type of Drive that:
- Has its own storage quota (not tied to any individual account)
- Can be accessed by multiple users
- Perfect for service accounts
- **Free with Google Workspace** (if your college has it)

---

## 📋 Setup Options

You have **2 options**:

### **Option 1: Shared Drive (Best Solution)** ⭐ RECOMMENDED

### **Option 2: Regular Folder with Delegation** (Alternative)

---

## 🚀 Option 1: Shared Drive Setup (RECOMMENDED)

### Step 1: Check if You Have Google Workspace

1. Go to https://drive.google.com
2. Look at the left sidebar
3. Do you see "Shared drives" option?
   - **YES** → You have Google Workspace! Proceed below ✅
   - **NO** → Use Option 2 instead ⬇️

### Step 2: Create Shared Drive

1. **Go to Google Drive**
   - Visit: https://drive.google.com

2. **Create Shared Drive**
   - Click "Shared drives" in left sidebar
   - Click "New" button
   - Name it: `IIC Events 2025-26`
   - Click "Create"

### Step 3: Add Service Account

1. **Open the Shared Drive**
   - Click on the shared drive you just created

2. **Add Member**
   - Click the ⚙️ (gear icon) → "Manage members"
   - Click "Add members"
   - Paste your **service account email** from credentials.json
   - Example: `iic-event-portal@project-id.iam.gserviceaccount.com`

3. **Set Permission**
   - Select role: **Content manager** or **Manager**
   - Uncheck "Notify people"
   - Click "Send"

### Step 4: Get Shared Drive Folder ID

1. **Open the Shared Drive**
   - You're already in it from Step 3

2. **Copy the Folder ID from URL**
   ```
   https://drive.google.com/drive/folders/FOLDER_ID_HERE
                                          ^^^^^^^^^^^^^^^^
                                          Copy this part
   ```

3. **Update config.py**
   ```python
   DRIVE_FOLDER_ID = "paste-your-shared-drive-id-here"
   ```

### ✅ Done! Test the App

```bash
streamlit run app.py
```

Upload a test event with photos. It should work now! 🎉

---

## 🔧 Option 2: Regular Folder (If No Shared Drive)

If you don't have Google Workspace, you need to use **domain-wide delegation**.

### Step 1: Enable Domain-Wide Delegation

1. **Go to Google Cloud Console**
   - Visit: https://console.cloud.google.com/

2. **Go to Service Account**
   - Navigate to "IAM & Admin" → "Service Accounts"
   - Click on your service account email

3. **Enable Delegation**
   - Click "Show Domain-Wide Delegation"
   - Click "Enable Google Workspace Domain-wide Delegation"
   - Save

4. **Add OAuth Scopes** (if required by admin)
   - OAuth scopes needed:
   ```
   https://www.googleapis.com/auth/drive.file
   https://www.googleapis.com/auth/spreadsheets
   ```

### Step 2: Use a Real User's Folder

Instead of service account creating folders, have it upload to a **regular user's folder**:

1. **Create folder as yourself**
   - Go to https://drive.google.com
   - Create folder: "IIC Events 2025-26"

2. **Share with Service Account**
   - Right-click folder → "Share"
   - Add service account email
   - Grant "Editor" access
   - Uncheck "Notify people"
   - Click "Share"

3. **Get Folder ID**
   - Open the folder
   - Copy ID from URL:
   ```
   https://drive.google.com/drive/folders/FOLDER_ID_HERE
   ```

4. **Update config.py**
   ```python
   DRIVE_FOLDER_ID = "your-folder-id"
   ```

5. **Modify app.py** (already done in latest version)
   - The app now includes `supportsAllDrives=True` parameter
   - This allows uploading to shared folders

### ✅ Test the App

```bash
streamlit run app.py
```

---

## 🎯 Quick Comparison

| Feature | Shared Drive | Regular Folder |
|---------|--------------|----------------|
| **Setup Difficulty** | Easy | Medium |
| **Storage Quota** | Unlimited (org quota) | Limited to user |
| **Reliability** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Requirements** | Google Workspace | Any Gmail account |
| **Best For** | Colleges/Organizations | Personal projects |
| **Service Account Access** | Native | Requires delegation |

---

## 🔍 How to Check Which Option to Use

Run this simple test:

1. **Go to Google Drive** → https://drive.google.com
2. **Look at left sidebar**
3. **Find "Shared drives"**
   - **Found it?** → Use Option 1 (Shared Drive) ⭐
   - **Not there?** → Use Option 2 (Regular Folder)

---

## ✅ Verify Everything is Working

### Test Checklist:

1. **Service Account Access**
   - [ ] Service account email added to Drive/Shared Drive
   - [ ] Permission set to "Content Manager" or "Manager"

2. **Config File**
   - [ ] `DRIVE_FOLDER_ID` updated in config.py
   - [ ] ID is correct (test by opening in browser)

3. **App Settings**
   - [ ] `credentials.json` placed in project folder
   - [ ] Spreadsheet ID configured
   - [ ] Users added to Users sheet

4. **Test Upload**
   - [ ] Run app: `streamlit run app.py`
   - [ ] Login with test email
   - [ ] Create test event
   - [ ] Upload test photos
   - [ ] Check if files appear in Drive folder

---

## 🐛 Troubleshooting

### Error: "Service Accounts do not have storage quota"

**Solution:**
- You're using a regular folder with a service account
- Switch to Shared Drive (Option 1)
- OR ensure domain-wide delegation is enabled (Option 2)

### Error: "Insufficient Permission"

**Solution:**
- Check service account has "Content Manager" or "Manager" role
- Ensure you added the correct service account email
- Try removing and re-adding the service account

### Error: "File not found" or "Folder not found"

**Solution:**
- Verify the DRIVE_FOLDER_ID in config.py is correct
- Open the folder in browser using the ID
- Ensure service account has access to the folder

### Files Upload But Can't Be Viewed

**Solution:**
- Check public sharing permissions
- App tries to make files public automatically
- Manually share the folder/files if needed

---

## 📞 Still Having Issues?

### Debug Steps:

1. **Verify Service Account Email**
   ```python
   # Open credentials.json
   # Find: "client_email": "xxx@xxx.iam.gserviceaccount.com"
   # Copy this exact email
   ```

2. **Test Drive Access Manually**
   - Open Drive folder in browser
   - Check "Manage access"
   - Verify service account email is listed
   - Verify permission level

3. **Check API Quotas**
   - Go to Google Cloud Console
   - "APIs & Services" → "Dashboard"
   - Check Drive API quota usage
   - Ensure you haven't exceeded limits

4. **Enable Detailed Logging**
   - Check Streamlit logs for detailed error messages
   - Look for specific permission errors

---

## 🎉 Success!

Once configured correctly, your app will:
- ✅ Create event folders automatically
- ✅ Upload photos and documents
- ✅ Store everything in Google Drive
- ✅ Generate shareable links
- ✅ Work forever without issues

**Your IIC Event Portal is now fully operational!** 🚀

---

## 📚 Additional Resources

- [Google Shared Drives Guide](https://support.google.com/a/answer/7212025)
- [Service Account Documentation](https://cloud.google.com/iam/docs/service-accounts)
- [Drive API Shared Drives](https://developers.google.com/drive/api/guides/about-shareddrives)
- [Domain-Wide Delegation](https://developers.google.com/identity/protocols/oauth2/service-account#delegatingauthority)
