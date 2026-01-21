# 🚨 QUICK FIX for Storage Quota Error

## The Error You're Getting:
```
Service Accounts do not have storage quota
```

## ⚡ Quick Solution (2 Minutes)

### Do You Have Google Workspace?

Check: Go to https://drive.google.com → Look for "Shared drives" in left sidebar

---

## ✅ **YES - I have "Shared drives"** (Recommended)

1. **Create Shared Drive**
   - Click "Shared drives" → "New"
   - Name: `IIC Events 2025-26`

2. **Add Service Account**
   - Open shared drive → ⚙️ → "Manage members"
   - Add your service account email from credentials.json
   - Set role: "Content manager"
   - Uncheck "Notify people"

3. **Get Folder ID**
   - Copy from URL: `https://drive.google.com/drive/folders/FOLDER_ID`
   - Update in `config.py`:
   ```python
   DRIVE_FOLDER_ID = "your-folder-id-here"
   ```

4. **Run App**
   ```bash
   streamlit run app.py
   ```

✅ **DONE!** Your app will work now.

---

## ❌ **NO - I don't have "Shared drives"**

1. **Create Regular Folder as Yourself**
   - Go to https://drive.google.com
   - Create folder: `IIC Events 2025-26`

2. **Share with Service Account**
   - Right-click folder → "Share"
   - Add service account email (from credentials.json)
   - Set permission: "Editor"
   - Uncheck "Notify people"

3. **Get Folder ID**
   - Open folder
   - Copy from URL: `https://drive.google.com/drive/folders/FOLDER_ID`
   - Update in `config.py`:
   ```python
   DRIVE_FOLDER_ID = "your-folder-id-here"
   ```

4. **Run App**
   ```bash
   streamlit run app.py
   ```

✅ **DONE!** App is fixed.

---

## 🔍 Where to Find Service Account Email?

Open your `credentials.json` file and look for:
```json
"client_email": "iic-event-portal@project-123.iam.gserviceaccount.com"
```

Copy that email ☝️

---

## 📝 Your Current Settings

From your `config.py`:
```python
SPREADSHEET_ID = "1A-rTshHRACRejTUDSvXuGfwzLzbddNqhm_w1e6SHXyY"  ✅
DRIVE_FOLDER_ID = "1RGsWkS_OgvJ82EoFnPTi81DX9RQ2wYvG"  ✅
```

**Just make sure:**
- This Drive folder ID is shared with your service account
- Service account has "Editor" or "Content Manager" permission

---

## 🎯 That's It!

The app code is already updated with:
- ✅ `supportsAllDrives=True` parameter
- ✅ Shared drive compatibility
- ✅ Better error handling

**Just update the sharing settings and you're good to go!** 🚀
