"""
Configuration file for IIC Event Submission Portal
Update these values for your deployment
"""

# Google Sheets Configuration
SPREADSHEET_ID = "1A-rTshHRACRejTUDSvXuGfwzLzbddNqhm_w1e6SHXyY"

# Google Drive Configuration
# Create a folder in Google Drive and paste its ID here
# To get folder ID: Open the folder in Drive, copy ID from URL
# Format: https://drive.google.com/drive/folders/FOLDER_ID_HERE
DRIVE_FOLDER_ID = "1RGsWkS_OgvJ82EoFnPTi81DX9RQ2wYvG"  # Replace with your Drive folder ID

# Authentication Method
# USE_OAUTH = True means OAuth2 (browser login) - tokens can be refreshed by admin
USE_OAUTH = True  # Using OAuth2 with admin refresh capability

# Service Account Credentials File (RECOMMENDED - never expires)
# Download from Google Cloud Console > IAM > Service Accounts > Keys > Add Key > JSON
CREDENTIALS_FILE = "credentials.json"

# OAuth2 Credentials File (only if USE_OAUTH = True - NOT recommended for hosting)
OAUTH_CLIENT_SECRET = "client_secret.json"

# ImgBB API Key for Image Hosting (Not needed if using OAuth!)
# Get your free API key from: https://api.imgbb.com/
IMGBB_API_KEY = ""  # Add your ImgBB API key here (optional)

# Application Settings
APP_TITLE = "SRIT IIC Portal"
APP_SUBTITLE = "Developed and Maintained by HIVE"
APP_ICON = "🎓"

# Academic Year Options
ACADEMIC_YEARS = ["2025-26", "2026-27", "2027-28", "2028-29"]

# Validation Rules
MIN_STUDENT_PARTICIPANTS = 40
MIN_EVENT_LEVEL = 2
MAX_OBJECTIVE_WORDS = 100
MAX_BENEFITS_WORDS = 150
MAX_FILE_SIZE_MB = 2
MIN_BRIEF_REPORT_WORDS = 1000  # Approximately 2 pages
MAX_PDF_FILE_SIZE_MB = 10  # Maximum PDF file size (10MB)

# Admin Configuration
ADMIN_EMAIL = "hive@sritcbe.ac.in"  # Admin email for approvals
ADMIN_PASSWORD = "Hive@srit"  # Admin password for authentication

# Allowed Email Domain - users with this domain are auto-registered
ALLOWED_EMAIL_DOMAIN = "sritcbe.ac.in"

# Event Type Configuration (Program Type)
EVENT_TYPES = [
    "Workshop",
    "Seminar",
    "Bootcamp",
    "Hackathon",
    "Competition",
    "Expert Talk",
    "Mentoring Session",
    "Demo Day",
    "Exhibition",
    "Conference",
    "Panel Discussion",
    "Exposure Visit",
    "Challenge",
    "Tech/E-Fest",
    "Outreach Program",
    "Others"
]

# Program Theme Configuration
PROGRAM_THEMES = [
    "IPR & Technology Transfer",
    "Innovation & Design Thinking",
    "Entrepreneurship & Startup",
    "Pre-Incubation & Incubation Management",
    "Safe and Trusted AI",
    "Human Capital",
    "Science",
    "Resilience, Innovation & Efficiency",
    "Inclusion for Social Empowerment",
    "Democratizing AI Resources",
    "Economic Growth & Social Good"
]

# Program Driven By
PROGRAM_DRIVEN_BY = [
    "IIC Calendar Activity",
    "MIC Activity",
    "Celebration Activity",
    "Self Driven Activity",
    "ATL School Activity",
    "R&D Activity",
    "Others"
]

# Activity Led By
ACTIVITY_LED_BY = [
    "Student Council",
    "Institute Council"
]

# Departments
DEPARTMENTS = [
    "MECH",
    "CSE",
    "AIDS",
    "EEE",
    "ECE",
    "IT"
]

# Mode of Session Delivery
MODE_OF_DELIVERY = [
    "Offline",
    "Online"
]

# UN Sustainable Development Goals (SDGs)
SDG_GOALS = [
    "SDG 1: No Poverty",
    "SDG 2: Zero Hunger",
    "SDG 3: Good Health and Well-being",
    "SDG 4: Quality Education",
    "SDG 5: Gender Equality",
    "SDG 6: Clean Water and Sanitation",
    "SDG 7: Affordable and Clean Energy",
    "SDG 8: Decent Work and Economic Growth",
    "SDG 9: Industry, Innovation and Infrastructure",
    "SDG 10: Reduced Inequalities",
    "SDG 11: Sustainable Cities and Communities",
    "SDG 12: Responsible Consumption and Production",
    "SDG 13: Climate Action",
    "SDG 14: Life Below Water",
    "SDG 15: Life on Land",
    "SDG 16: Peace, Justice and Strong Institutions",
    "SDG 17: Partnerships for the Goals"
]

# NBA Program Outcomes (POs) - 11 POs as per NBA
PROGRAM_OUTCOMES = [
    "PO1: Engineering Knowledge",
    "PO2: Problem Analysis",
    "PO3: Design/Development of Solutions",
    "PO4: Conduct Investigations of Complex Problems",
    "PO5: Engineering Tool Usage",
    "PO6: The Engineer and The World",
    "PO7: Ethics",
    "PO8: Individual and Collaborative Team Work",
    "PO9: Communication",
    "PO10: Project Management and Finance",
    "PO11: Life-Long Learning"
]
