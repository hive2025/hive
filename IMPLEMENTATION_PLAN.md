# Complete Implementation Plan for Enhanced IIC Portal

## Summary of Changes Requested

### 1. **Photo Upload Changes**
- Remove EXIF date validation
- Add 3 geotagged photos (separate upload)
- Add 3 normal photos (separate upload)
- Total: 6 photo uploads

### 2. **New Document Uploads**
1. **Attendance Report** (Image or PDF, A4 size limit ≤5MB)
2. **Feedback Analysis Report** (PDF only with graphs, A4 size)
3. **Event Agenda** (PDF)
4. **Chief Guest Biodata** (PDF, brief format)

### 3. **Brief Report**
- Text area for complete event report
- Minimum 1000 words (≈2 pages)
- Copy-paste format

### 4. **PDF Generation**
- Generate PDF after "Save as Draft"
- Store PDF in Google Drive
- Format matching sample: `IICReport_S25-262586960-IC201912089.pdf`
- Include all event data and attachments

### 5. **Google Sheets Updates**
- Store all file IDs in separate columns
- Add columns for:
  - Geotagged Photo 1-3 IDs
  - Normal Photo 1-3 IDs
  - Attendance Report ID
  - Feedback Analysis ID
  - Event Agenda ID
  - Chief Guest Biodata ID
  - Brief Report Text
  - Generated PDF ID
  - Admin Approval Status
  - Approval Date

### 6. **Admin Features**
- Admin email: `hive@sritcbe.ac.in`
- Admin can view ALL submissions
- Admin can edit any submission
- Admin approval system
- Users can only print after admin approval

### 7. **User Experience**
- Users see only their own events
- After admin approval, "Download Final Report" button appears
- Status indicators: Draft, Submitted, Approved, Rejected

---

## Updated Google Sheets Structure

### Columns to Add:
```
... (existing columns) ...
Geotagged_Photo1_ID
Geotagged_Photo2_ID
Geotagged_Photo3_ID
Normal_Photo1_ID
Normal_Photo2_ID
Normal_Photo3_ID
Attendance_Report_ID
Feedback_Analysis_ID
Event_Agenda_ID
Chief_Guest_Biodata_ID
Brief_Report_Text
Generated_PDF_ID
Admin_Approval_Status (Draft/Submitted/Approved/Rejected)
Approval_Date
Approved_By
Rejection_Reason
```

---

## File Upload Validations

### Photos (All 6):
- Format: JPG, JPEG, PNG
- Max size: 2MB per photo
- No EXIF validation

### PDFs:
- Attendance Report: PDF or Image, ≤5MB
- Feedback Analysis: PDF only, ≤5MB
- Event Agenda: PDF only, ≤5MB
- Chief Guest Biodata: PDF only, ≤5MB

### Brief Report:
- Minimum: 1000 words
- Text area (no file upload)

---

## PDF Generation Details

### Template Structure:
```
Page 1:
- Header with logos (left and right)
- MOE'S INNOVATION CELL
- INSTITUTION'S INNOVATION COUNCIL
- SRI RAMAKRISHNA INSTITUTE OF TECHNOLOGY, COIMBATORE (IC201912089)
- Event Name (Title)
- OVERVIEW section:
  - Objective (left) | Benefits (right)
  - Academic Year | Program driven by
  - Month | Program/Activity Name

Page 2:
- Program Type | Other
- Program Theme | Other
- Date & Duration | External Participants
- Student Participants | Faculty Participants
- Expenditure Amount | Remark
- ATTACHMENTS section:
  - Video URL
  - Photograph1 (embedded)
  - Photograph2 (embedded)
  - Session plan link
- Footer: "This report is electronically generated..."
```

---

## Admin Dashboard Features

### For Admin (hive@sritcbe.ac.in):
1. **View All Events** tab
   - Table showing all submissions
   - Filters: Status, Date, User
   - Search by event name, user email

2. **Approval Actions**
   - Approve button (with confirmation)
   - Reject button (with reason field)
   - Edit button (opens event in edit mode)

3. **Analytics Dashboard**
   - Total submissions
   - Pending approvals
   - Approved count
   - Rejected count
   - Charts by month, type, theme

### For Regular Users:
1. **My Events** tab (existing)
   - Only their submissions
   - Status badges
   - Edit button (only if Draft or Rejected)
   - Download Final Report button (only if Approved)

2. **Status Workflow**:
   ```
   Draft → Submitted → (Admin reviews) → Approved/Rejected
   ```

---

## Implementation Steps

### Phase 1: Database & Config
1. ✅ Update `config.py` with new constants
2. Update Google Sheets structure (add new columns)
3. Update `GoogleSheetsManager.save_event()` to handle all file IDs

### Phase 2: File Upload UI
1. Update form to show 6 separate photo uploads
2. Add 4 new PDF upload sections
3. Add brief report text area with word counter
4. Remove EXIF validation code

### Phase 3: PDF Generation
1. ✅ Created `pdf_generator.py`
2. Integrate PDF generation after save
3. Upload generated PDF to Drive
4. Store PDF ID in sheets

### Phase 4: Admin Features
1. Add admin check in authentication
2. Create admin dashboard
3. Add approval/reject actions
4. Update status workflow

### Phase 5: Final Report Download
1. Add "Download Final Report" button
2. Show only after approval
3. Fetch PDF from Drive
4. Provide download link

---

## Next Steps

Run this command to install required PDF library:
```bash
pip install reportlab
```

Then update `requirements.txt`:
```
reportlab==4.0.7
```

Would you like me to proceed with implementing these changes step by step?
