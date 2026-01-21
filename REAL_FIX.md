# 🔴 REAL FIX for Service Account Storage Quota Error

## The Problem

Service accounts **CANNOT** upload files to regular Google Drive folders because they don't have storage quota. Even with `supportsAllDrives=True`, it only works with **Shared Drives**, not regular folders.

Your folder `1RGsWkS_OgvJ82EoFnPTi81DX9RQ2wYvG` is a **regular folder**, NOT a Shared Drive.

---

## ✅ Solution: Use a Shared Drive (REQUIRED)

### You MUST follow these steps:

### Step 1: Check Google Workspace

1. Go to https://drive.google.com
2. Look at left sidebar
3. Do you see **"Shared drives"** option?

**If YES** ✅ → Continue to Step 2
**If NO** ❌ → Contact your college IT admin to enable Google Workspace Shared Drives

---

### Step 2: Create Shared Drive (Not a regular folder!)

**IMPORTANT:** Shared Drive ≠ Regular Folder!

1. **In Google Drive**, click **"Shared drives"** (left sidebar)
2. Click **"New"** button (with + icon)
3. Name it: `IIC Events 2025-26`
4. Click **"Create"**

You should now see it under "Shared drives" section (NOT under "My Drive")

---

### Step 3: Add Service Account to Shared Drive

1. **Click on the Shared Drive** you just created
2. Click the **⚙️ gear icon** → **"Manage members"**
3. Click **"Add members"**
4. **Paste your service account email**:
   - Open `credentials.json`
   - Find: `"client_email": "xxx@xxx.iam.gserviceaccount.com"`
   - Copy that email

5. **Set Role:** Select **"Content manager"** or **"Manager"**
6. **Uncheck** "Notify people"
7. Click **"Send"**

---

### Step 4: Get Shared Drive ID

1. **Open the Shared Drive** (click on it)
2. **Look at the URL**:
   ```
   https://drive.google.com/drive/folders/SHARED_DRIVE_ID_HERE
   ```
3. **Copy the ID** (the long string after `/folders/`)

---

### Step 5: Update config.py

Replace the current folder ID with your Shared Drive ID:

```python
DRIVE_FOLDER_ID = "your-shared-drive-id-here"  # NOT the regular folder ID!
```

---

### Step 6: Test

```bash
streamlit run app.py
```

Upload a test event with photos. It should work now!

---

## 🚫 Why Regular Folders Don't Work

| Feature | Regular Folder | Shared Drive |
|---------|----------------|--------------|
| **Service Account Upload** | ❌ NOT SUPPORTED | ✅ SUPPORTED |
| **Storage Quota** | Tied to user account | Shared quota |
| **Location** | Under "My Drive" | Under "Shared drives" |
| **API Support** | Limited for service accounts | Full support |

---

## 🔍 How to Know if You Have Shared Drives

### Visual Check:

**Look at your Google Drive sidebar:**

```
My Drive
├── Folders...

Shared with me
├── Files...

Shared drives  ← DO YOU SEE THIS?
├── Drive 1
├── Drive 2

Trash
```

**If you see "Shared drives"** → You have Google Workspace ✅
**If you DON'T see it** → You need Google Workspace ❌

---

## ❌ If You Don't Have Google Workspace

### Option 1: Get Google Workspace (Recommended)

Contact your college IT department:
- Most colleges have free Google Workspace for Education
- Ask them to enable "Shared Drives" feature
- This is the proper solution

### Option 2: Use OAuth2 Instead (Complex)

If you can't get Shared Drives, you need to switch from service account to OAuth2:

1. Create OAuth2 credentials (not service account)
2. Get user authorization
3. Use user's Drive storage
4. This requires code changes

**Not recommended** - Just get Shared Drives instead!

### Option 3: Store Files Locally (Temporary)

The app will automatically save files locally if Drive upload fails:
- Files saved to `uploaded_files_backup/` folder
- Links stored in sheets as `LOCAL:path/to/file`
- Not accessible via web
- Only works if running on local server

---

## 🎯 Quick Checklist

Before running the app, verify:

- [ ] Created a **Shared Drive** (not a regular folder!)
- [ ] Shared Drive is in "Shared drives" section of Google Drive
- [ ] Added service account email to Shared Drive
- [ ] Service account has "Content manager" role
- [ ] Copied Shared Drive ID (not regular folder ID!)
- [ ] Updated `DRIVE_FOLDER_ID` in config.py
- [ ] Restarted the app

---

## 📸 Visual Difference

### ❌ **Wrong:** Regular Folder
```
My Drive/
  └── IIC Events 2025-26/  ← Regular folder (won't work!)
```

### ✅ **Correct:** Shared Drive
```
Shared drives/
  └── IIC Events 2025-26  ← Shared Drive (will work!)
```

---

## 🐛 Still Getting the Error?

### Debug Steps:

1. **Verify it's a Shared Drive:**
   - Open Google Drive
   - Check if folder is under "Shared drives" (not "My Drive")

2. **Verify Service Account is Added:**
   - Open Shared Drive
   - Click ⚙️ → "Manage members"
   - Check if service account email is listed

3. **Verify Permission:**
   - Service account should have "Content manager" or "Manager" role
   - Not just "Viewer" or "Commenter"

4. **Check Folder ID:**
   - Make sure you copied the Shared Drive ID
   - Not a folder inside the Shared Drive
   - Not a regular folder ID

---

## 🎉 Success Indicators

When it works, you'll see:
- ✅ Files uploaded to Shared Drive
- ✅ Folders created automatically by event name
- ✅ No storage quota errors
- ✅ Files accessible via web links

---

## 💬 Need Help?

**Common mistake:** Creating a regular folder and calling it a "shared drive"

**How to tell:** Regular folders are under "My Drive", Shared Drives are under "Shared drives"

**Solution:** You MUST use the actual "Shared drives" feature in Google Workspace!

---

**Bottom line:** Service accounts + Regular folders = ❌ Won't work
**Bottom line:** Service accounts + Shared Drives = ✅ Will work

Make sure you're using a **Shared Drive**, not a regular folder that you shared!
