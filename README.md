# IIC Event Submission Portal

A comprehensive Streamlit-based event submission system for the Ministry of Education Innovation Cell (IIC) with automated validations, Google Sheets integration, and Google Drive storage.

## Features

### 🔐 Authentication System
- User login with email verification
- Email validation against Google Sheets user database
- Session management with automatic logout

### 📝 Smart Event Form
- **Automated Quarter Detection**: Automatically determines quarter based on event date
- **Level Auto-calculation**: Determines event level (1-4) based on duration and event type
- **Image Metadata Validation**: Checks if uploaded images match event date using EXIF data
- **Word Count Validation**:
  - Objective: Maximum 100 words
  - Benefits: Maximum 150 words
- **Participant Validation**: Minimum 40 students required
- **Level Validation**: Event level must be 2 or higher

### 📊 Dashboard
- View total events, completed events, and drafts
- Track total student participation
- Recent events overview
- Filter by status and quarter

### 💾 Data Management
- **Google Sheets Integration**: All data stored in Google Sheets
- **Google Drive Integration**: Photos and documents stored in Google Drive
- **Automatic Folder Creation**: Creates unique folder for each event
- **Edit Functionality**: Edit and update existing events
- **Draft System**: Save events as drafts before final submission

### 📱 Social Media Integration
- Track promotions on Twitter, Facebook, Instagram, and LinkedIn
- Store social media URLs with event data

## Installation

### Prerequisites
1. Python 3.8 or higher
2. Google Cloud Project with Sheets API and Drive API enabled
3. Service account credentials JSON file

### Step-by-Step Setup

#### 1. Clone or Download the Project
```bash
cd "c:\imman\2025_26 EVEN SEM\JESUS IIC\JESUS HIVE SOFTWARE"
```

#### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

#### 3. Set Up Google Cloud Project

##### A. Create a Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Note your Project ID

##### B. Enable Required APIs
1. Go to "APIs & Services" > "Library"
2. Search and enable:
   - **Google Sheets API**
   - **Google Drive API**

##### C. Create Service Account
1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "Service Account"
3. Fill in the details:
   - Service account name: `iic-event-portal`
   - Service account ID: `iic-event-portal`
   - Click "Create and Continue"
4. Grant roles:
   - Role: "Editor" (or custom roles for Sheets and Drive)
5. Click "Done"

##### D. Generate Service Account Key
1. Click on the created service account
2. Go to "Keys" tab
3. Click "Add Key" > "Create New Key"
4. Choose "JSON" format
5. Click "Create" - a JSON file will be downloaded
6. Rename this file to `credentials.json`
7. **Keep this file secure and never share it publicly**

#### 4. Set Up Google Sheets

##### A. Create a New Google Spreadsheet
1. Go to [Google Sheets](https://sheets.google.com)
2. Create a new spreadsheet
3. Name it "IIC Event Portal Database"
4. Copy the Spreadsheet ID from the URL:
   ```
   https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit
   ```

##### B. Share Spreadsheet with Service Account
1. Open your spreadsheet
2. Click "Share" button
3. Add the service account email (found in `credentials.json` - look for `client_email`)
4. Grant "Editor" access
5. Uncheck "Notify people"
6. Click "Share"

##### C. Add User Emails to Spreadsheet
1. The app will automatically create "Users" and "Events" sheets
2. Manually add authorized user emails to the "Users" sheet:
   - Column A: Email addresses of authorized users
   - Example:
     ```
     Email
     user1@example.com
     user2@example.com
     coordinator@college.edu
     ```

## Running the Application

### 1. Start the Application
```bash
streamlit run app.py
```

### 2. Configure in Browser
1. The app will open in your default browser (usually `http://localhost:8501`)
2. In the sidebar:
   - **Upload credentials.json**: Upload the service account credentials file
   - **Enter Spreadsheet ID**: Paste your Google Sheets ID

### 3. Login
1. Enter your registered email address (must be in the Users sheet)
2. Click "Login"

### 4. Use the Portal
- **Dashboard**: View your event statistics
- **Create Event**: Submit new events with automated validations
- **My Events**: View and edit your submitted events

## Google Sheets Structure

The application automatically creates two sheets:

### Users Sheet
| Email | Name | Registration Date | Last Login | Total Events |
|-------|------|-------------------|------------|--------------|
| user@example.com | | | 2025-01-18 | 5 |

### Events Sheet
Contains all event details including:
- Event ID, User Email, Academic Year, Quarter
- Program details (Name, Type, Theme, Level, Duration)
- Participation numbers
- Dates, URLs, and file links
- Status (Draft/Submitted)
- Drive Folder ID

## Google Drive Structure

The application creates folders with the naming format:
```
EventName_EventID/
├── photo1_EventID.jpg
├── photo2_EventID.jpg
└── report_EventID.pdf
```

## Features Explained

### 1. Automatic Quarter Detection
Based on event start date:
- **Quarter 1**: September 1 - November 30
- **Quarter 2**: December 1 - February 28
- **Quarter 3**: March 1 - May 31
- **Quarter 4**: June 1 - August 31

### 2. Automatic Level Detection
Based on duration:
- **Level 1**: 2-4 hours (Talks, Mentoring, Exposure)
- **Level 2**: 5-8 hours (Seminars, Workshops)
- **Level 3**: 9-18 hours (Bootcamps, Competitions)
- **Level 4**: >18 hours (Challenges, Hackathons)

### 3. Image Date Validation
- Extracts EXIF metadata from uploaded images
- Compares image date with event date
- Allows ±7 days tolerance
- Warns if dates don't match

### 4. Validations
- ✅ Minimum 40 student participants
- ✅ Event level ≥ 2
- ✅ Objective ≤ 100 words
- ✅ Benefits ≤ 150 words
- ✅ Required photographs and report for submission
- ✅ Image date matches event date

## Troubleshooting

### Common Issues

#### 1. "Error loading credentials"
- Ensure `credentials.json` is uploaded correctly
- Verify the JSON file is from a service account
- Check file permissions

#### 2. "Email not found in the system"
- Verify the email is added to the "Users" sheet
- Check for typos in the email address
- Ensure the spreadsheet is shared with the service account

#### 3. "Error setting up spreadsheet"
- Verify the Spreadsheet ID is correct
- Ensure the service account has "Editor" access
- Check that Google Sheets API is enabled

#### 4. "Error uploading file"
- Check file size (max 2MB for images and PDFs)
- Ensure Google Drive API is enabled
- Verify the service account has necessary permissions

#### 5. "Permission denied" errors
- Ensure both Sheets API and Drive API are enabled
- Verify service account has correct roles
- Check that the spreadsheet is shared with the service account email

### Getting Help
Contact the IIC Implementation Team:
- Email: dipan.sahu@aicte-india.org
- Phone: 011 2958 1226

## Security Best Practices

1. **Never commit `credentials.json` to version control**
   - Add to `.gitignore`
2. **Restrict service account permissions**
   - Only grant necessary API access
3. **Regularly rotate credentials**
   - Generate new keys periodically
4. **Limit user access**
   - Only add authorized emails to Users sheet
5. **Monitor usage**
   - Check Google Cloud Console for API usage

## IIC Calendar Activities

The portal supports all IIC 8.0 calendar activities across 4 quarters:

### Quarter 1 (Sep-Nov): Inspiration, Motivation, and Ideation
- Awareness Workshops
- Expert Sessions
- Bootcamps
- Hackathons
- Demo Days

### Quarter 2 (Dec-Feb): Validation and Concept Development
- Design Thinking Workshops
- Innovation Sprints
- Outreach Programs
- Innovation Competitions

### Quarter 3 (Mar-May): Prototype, Design, Business Model Development
- Product-Market Fit Workshops
- Business Model Canvas Sessions
- B-Plan Competitions
- IPR Workshops

### Quarter 4 (Jun-Aug): Start-up Ecosystem & Scale Up
- Investor Pitch Preparation
- Incubation Opportunities
- Funding Sessions
- Start-up Competitions

## Data Flow

```
User Login (Email)
    ↓
Authentication (Google Sheets - Users)
    ↓
Dashboard/Create Event
    ↓
Form Validation (Auto-checks)
    ↓
File Upload (Google Drive)
    ↓
Data Save (Google Sheets - Events)
    ↓
Confirmation & View Events
```

## Technical Stack

- **Frontend**: Streamlit
- **Backend**: Python 3.8+
- **Storage**: Google Sheets (Data), Google Drive (Files)
- **Authentication**: Email-based with Google Sheets verification
- **Image Processing**: Pillow (PIL)
- **Data Handling**: Pandas

## File Structure

```
JESUS HIVE SOFTWARE/
├── app.py                 # Main Streamlit application
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── credentials.json      # Google service account credentials (DO NOT COMMIT)
└── .gitignore           # Git ignore file
```

## Future Enhancements

- [ ] Email notifications on event submission
- [ ] Advanced analytics and reporting
- [ ] Export events to PDF
- [ ] Multi-language support
- [ ] Mobile-responsive design improvements
- [ ] Bulk event upload via CSV
- [ ] Event calendar view
- [ ] Approval workflow for coordinators

## License

This project is developed for the Ministry of Education Innovation Cell (MoE IIC) initiative.

## Support

For technical support or feature requests, please contact:
- **Dr. Dipan Sahu** - Assistant Innovation Director
- Email: dipan.sahu@aicte-india.org
- Phone: 011 2958 1226

---

**Developed for IIC 8.0 Academic Year 2025-26**

*Ministry of Education - Government of India*