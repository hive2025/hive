# 🎯 OAuth2 Setup - The Solution That Works!

Your existing app works because it uses **OAuth2 (browser login)** instead of service accounts!

## ✅ How to Set Up OAuth2 for IIC App

### Step 1: Create OAuth2 Credentials

1. **Go to Google Cloud Console**
   - Visit: https://console.cloud.google.com/

2. **Navigate to Credentials**
   - "APIs & Services" → "Credentials"

3. **Create OAuth Client ID**
   - Click "+ CREATE CREDENTIALS"
   - Select **"OAuth client ID"** (NOT Service Account!)

4. **Configure OAuth Consent Screen** (if prompted)
   - User Type: **External**
   - App name: `IIC Event Portal`
   - User support email: Your email
   - Developer contact: Your email
   - Click "Save and Continue"
   - Scopes: Skip this step
   - Test users: Add your email
   - Click "Save and Continue"

5. **Create OAuth Client**
   - Application type: **Desktop app**
   - Name: `IIC Portal Desktop`
   - Click "Create"

6. **Download JSON**
   - Click "Download JSON" button
   - Save as `client_secret.json`
   - Place in your project folder

### Step 2: Update Your Code

Replace the `init_google_services()` function to use OAuth2 instead of service accounts.

I've created `oauth_drive.py` with all the OAuth2 functions you need!

### Step 3: First Time Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py
```

**First time running:**
1. App will open browser for Google login
2. Login with your Google account
3. Grant permissions to access Drive and Sheets
4. Credentials saved in `token.pickle`
5. Next time, no login needed!

---

## 🎯 Quick Integration

Add this to your existing `app.py`:

```python
import oauth_drive

# Replace the init_google_services function
def init_google_services():
    """Initialize using OAuth2"""
    return oauth_drive.get_google_services_oauth()

# Add re-authenticate button in sidebar
if st.sidebar.button("🔄 Re-Authenticate"):
    if os.path.exists('token.pickle'):
        os.remove('token.pickle')
    st.sidebar.info("Please wait for browser login...")
    drive_service, sheets_service = oauth_drive.get_google_services_oauth(force_reauth=True)
    if drive_service:
        st.sidebar.success("✅ Authentication successful!")
```

---

## 💡 Why This Works

| Method | Works? | Why |
|--------|--------|-----|
| **Service Account** | ❌ | No storage quota, can't write to personal Drive |
| **OAuth2 (Browser Login)** | ✅ | Uses YOUR Google account storage |

**OAuth2 = Your account = Your storage = Works perfectly!**

---

## 📝 Complete Steps

1. ✅ Create OAuth2 credentials → Download `client_secret.json`
2. ✅ Place `client_secret.json` in project folder
3. ✅ Use `oauth_drive.py` functions (already created!)
4. ✅ Run app → Browser login → Done!

---

## 🔐 Files You Need

```
Your Project/
├── app.py                    # Your main app
├── oauth_drive.py            # OAuth2 functions (CREATED!)
├── client_secret.json        # Download from Google Cloud
├── token.pickle             # Auto-created after first login
├── config.py                # Your config
└── requirements.txt         # Dependencies
```

---

## 🚀 Benefits of OAuth2

- ✅ Works with regular Drive folders (no Shared Drive needed!)
- ✅ Uses YOUR storage quota
- ✅ No service account limitations
- ✅ One-time browser login
- ✅ Credentials cached forever
- ✅ Works exactly like your existing app!

---

## 🔄 To Switch Your IIC App

1. Download OAuth2 credentials as `client_secret.json`
2. The `oauth_drive.py` file is already created
3. Update config.py to add OAuth flag
4. Run the app!

That's it! No Shared Drives, no ImgBB, no workarounds needed!

---

## 📞 Need the Updated app.py?

I can update your entire `app.py` to use OAuth2 just like your working app!

Just say "update app.py to use OAuth2" and I'll do it! 🚀
