"""
SRIT IIC Portal — User Guide & Event Checklist PDF Generator
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus import Flowable
from io import BytesIO

# ── Brand colours ────────────────────────────────────────────────────────────
GREEN_DARK   = colors.HexColor("#1b5e20")
GREEN_MED    = colors.HexColor("#388e3c")
GREEN_LIGHT  = colors.HexColor("#c8e6c9")
GREEN_PALE   = colors.HexColor("#f1f8e9")
BLUE_DARK    = colors.HexColor("#1565c0")
BLUE_LIGHT   = colors.HexColor("#e3f2fd")
ORANGE       = colors.HexColor("#e65100")
ORANGE_LIGHT = colors.HexColor("#fff3e0")
GREY_TEXT    = colors.HexColor("#333333")
GREY_LIGHT   = colors.HexColor("#f5f5f5")
WHITE        = colors.white


# ── Custom Flowables ─────────────────────────────────────────────────────────
class ColorBar(Flowable):
    """A coloured horizontal bar (section header background)."""
    def __init__(self, text, bg=GREEN_DARK, fg=WHITE, font_size=13, height=10*mm):
        super().__init__()
        self.text = text
        self.bg = bg
        self.fg = fg
        self.font_size = font_size
        self.bar_height = height

    def wrap(self, avail_w, avail_h):
        self.width = avail_w
        return avail_w, self.bar_height

    def draw(self):
        c = self.canv
        c.setFillColor(self.bg)
        c.rect(0, 0, self.width, self.bar_height, fill=1, stroke=0)
        c.setFillColor(self.fg)
        c.setFont("Helvetica-Bold", self.font_size)
        c.drawString(6*mm, (self.bar_height - self.font_size * 0.8) / 2 + 1, self.text)


class CheckItem(Flowable):
    """A single checklist row with a checkbox square."""
    def __init__(self, text, sub=None, indent=0, bold=False):
        super().__init__()
        self.text = text
        self.sub = sub          # optional grey sub-text
        self.indent = indent
        self.bold = bold
        self.row_h = 7.5*mm if not sub else 11*mm

    def wrap(self, avail_w, avail_h):
        self.width = avail_w
        return avail_w, self.row_h

    def draw(self):
        c = self.canv
        x = self.indent * mm
        box_x = x + 1*mm
        box_y = self.row_h - 5.5*mm
        box_s = 4.2*mm

        # checkbox
        c.setStrokeColor(GREEN_MED)
        c.setFillColor(WHITE)
        c.setLineWidth(0.8)
        c.rect(box_x, box_y, box_s, box_s, fill=1, stroke=1)

        # label
        c.setFillColor(GREY_TEXT)
        font = "Helvetica-Bold" if self.bold else "Helvetica"
        c.setFont(font, 9)
        c.drawString(box_x + box_s + 2*mm, box_y + 1.2*mm, self.text)

        if self.sub:
            c.setFont("Helvetica-Oblique", 7.5)
            c.setFillColor(colors.HexColor("#777777"))
            c.drawString(box_x + box_s + 2*mm, box_y - 3.5*mm, self.sub)


# ── Style helpers ─────────────────────────────────────────────────────────────
def _styles():
    base = getSampleStyleSheet()
    s = {}

    s['title'] = ParagraphStyle(
        'GuideTitle', parent=base['Title'],
        fontSize=22, textColor=WHITE, alignment=TA_CENTER,
        spaceAfter=4, fontName='Helvetica-Bold'
    )
    s['subtitle'] = ParagraphStyle(
        'GuideSubtitle', parent=base['Normal'],
        fontSize=11, textColor=colors.HexColor("#c8e6c9"),
        alignment=TA_CENTER, spaceAfter=2
    )
    s['body'] = ParagraphStyle(
        'GuideBody', parent=base['Normal'],
        fontSize=9, textColor=GREY_TEXT, leading=14,
        spaceAfter=4
    )
    s['bold'] = ParagraphStyle(
        'GuideBold', parent=s['body'],
        fontName='Helvetica-Bold'
    )
    s['note'] = ParagraphStyle(
        'GuideNote', parent=s['body'],
        fontSize=8, textColor=colors.HexColor("#555555"),
        fontName='Helvetica-Oblique', leftIndent=4
    )
    s['step_num'] = ParagraphStyle(
        'StepNum', parent=base['Normal'],
        fontSize=18, textColor=GREEN_DARK, fontName='Helvetica-Bold',
        alignment=TA_CENTER
    )
    s['step_title'] = ParagraphStyle(
        'StepTitle', parent=base['Normal'],
        fontSize=10, textColor=GREEN_DARK, fontName='Helvetica-Bold',
        spaceBefore=0, spaceAfter=2
    )
    s['step_body'] = ParagraphStyle(
        'StepBody', parent=s['body'],
        fontSize=8.5, leading=13
    )
    return s


# ── Page template (header/footer) ─────────────────────────────────────────────
def _page_header_footer(canvas, doc):
    canvas.saveState()
    w, h = A4

    # top stripe
    canvas.setFillColor(GREEN_DARK)
    canvas.rect(0, h - 12*mm, w, 12*mm, fill=1, stroke=0)
    canvas.setFillColor(WHITE)
    canvas.setFont("Helvetica-Bold", 9)
    canvas.drawString(15*mm, h - 8*mm, "SRIT IIC Portal  |  User Guide & Event Checklist")
    canvas.setFont("Helvetica", 8)
    canvas.drawRightString(w - 15*mm, h - 8*mm, "Developed & Maintained by HIVE")

    # bottom stripe
    canvas.setFillColor(GREEN_DARK)
    canvas.rect(0, 0, w, 8*mm, fill=1, stroke=0)
    canvas.setFillColor(WHITE)
    canvas.setFont("Helvetica", 7.5)
    canvas.drawString(15*mm, 2.5*mm, "Sri Ramakrishna Institute of Technology, Coimbatore  |  hive@sritcbe.ac.in")
    canvas.drawRightString(w - 15*mm, 2.5*mm, f"Page {doc.page}")

    canvas.restoreState()


# ── Section builder helpers ───────────────────────────────────────────────────
def _section_bar(title, bg=GREEN_DARK):
    return ColorBar(title, bg=bg, fg=WHITE, font_size=12, height=9*mm)


def _step_card(num, title, bullets, s):
    """Returns a KeepTogether block for one numbered step."""
    header_data = [[
        Paragraph(str(num), s['step_num']),
        Paragraph(f"<b>{title}</b>", s['step_title'])
    ]]
    header_tbl = Table(header_data, colWidths=[12*mm, None])
    header_tbl.setStyle(TableStyle([
        ('VALIGN',   (0, 0), (-1, -1), 'MIDDLE'),
        ('BACKGROUND', (0, 0), (0, 0), GREEN_PALE),
        ('BACKGROUND', (1, 0), (1, 0), WHITE),
        ('BOX',      (0, 0), (-1, -1), 0.5, GREEN_LIGHT),
        ('LEFTPADDING',  (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING',   (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING',(0, 0), (-1, -1), 1),
    ]))

    bullet_rows = []
    for b in bullets:
        bullet_rows.append([
            Paragraph("•", s['body']),
            Paragraph(b, s['step_body'])
        ])
    b_tbl = Table(bullet_rows, colWidths=[5*mm, None])
    b_tbl.setStyle(TableStyle([
        ('VALIGN',  (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING',   (0, 0), (-1, -1), 1),
        ('BOTTOMPADDING',(0, 0), (-1, -1), 1),
        ('LEFTPADDING',  (0, 0), (-1, -1), 2),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('BACKGROUND', (0, 0), (-1, -1), GREY_LIGHT),
        ('BOX', (0, 0), (-1, -1), 0.3, GREEN_LIGHT),
    ]))

    return KeepTogether([header_tbl, b_tbl, Spacer(1, 3*mm)])


def _checklist_section(title, bg, items, s):
    """Returns elements for one colour-coded checklist section."""
    elems = [Spacer(1, 4*mm), _section_bar(title, bg=bg)]
    for item in items:
        if isinstance(item, str) and item.startswith("##"):
            # sub-heading row
            elems.append(Spacer(1, 1.5*mm))
            elems.append(Paragraph(f"<b>{item[2:].strip()}</b>", s['bold']))
            elems.append(Spacer(1, 0.5*mm))
        elif isinstance(item, tuple):
            text, sub = item
            elems.append(CheckItem(text, sub=sub, indent=4))
        else:
            elems.append(CheckItem(item, indent=4))
    return elems


# ── Main generator ────────────────────────────────────────────────────────────
def generate_guidelines_pdf() -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=15*mm, rightMargin=15*mm,
        topMargin=18*mm, bottomMargin=14*mm,
        title="SRIT IIC Portal — User Guide & Event Checklist",
        author="HIVE, SRIT Coimbatore"
    )

    s = _styles()
    story = []

    # ── COVER ────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 20*mm))

    cover_data = [[
        Paragraph("SRIT IIC Portal", s['title']),
        Paragraph("User Guide &amp; Event Checklist", s['subtitle']),
        Paragraph("Institution's Innovation Council  |  Academic Year 2025–26", s['subtitle']),
        Spacer(1, 6*mm),
        Paragraph("Developed &amp; Maintained by <b>HIVE</b> — Hub for Innovation, Ventures &amp; Entrepreneurship", s['subtitle']),
        Paragraph("Sri Ramakrishna Institute of Technology, Coimbatore", s['subtitle']),
    ]]
    cover_tbl = Table([[c] for c in cover_data[0]], colWidths=[170*mm])
    cover_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), GREEN_DARK),
        ('TOPPADDING',    (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING',   (0, 0), (-1, -1), 8),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 8),
        ('ROUNDEDCORNERS', [4]),
    ]))
    story.append(cover_tbl)
    story.append(Spacer(1, 10*mm))

    # what's inside
    toc_items = [
        ["Section 1", "How to Use the SRIT IIC Portal", "Step-by-step login, form filling and submission guide"],
        ["Section 2", "Before Event Checklist", "Everything to prepare before conducting the activity"],
        ["Section 3", "During Event Checklist", "What to capture and collect while the activity is happening"],
        ["Section 4", "After Event Checklist", "Documents, uploads and final submission on the portal"],
    ]
    toc_data = [[Paragraph("<b>Section</b>", s['bold']),
                 Paragraph("<b>Title</b>", s['bold']),
                 Paragraph("<b>Description</b>", s['bold'])]]
    for row in toc_items:
        toc_data.append([Paragraph(row[0], s['body']),
                         Paragraph(f"<b>{row[1]}</b>", s['bold']),
                         Paragraph(row[2], s['body'])])
    toc_tbl = Table(toc_data, colWidths=[25*mm, 55*mm, 90*mm])
    toc_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), GREEN_DARK),
        ('TEXTCOLOR',  (0, 0), (-1, 0), WHITE),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, GREEN_PALE]),
        ('BOX',    (0, 0), (-1, -1), 0.5, GREEN_MED),
        ('INNERGRID', (0, 0), (-1, -1), 0.3, GREEN_LIGHT),
        ('TOPPADDING',    (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING',   (0, 0), (-1, -1), 5),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(Paragraph("<b>Contents of this Guide</b>", s['step_title']))
    story.append(Spacer(1, 2*mm))
    story.append(toc_tbl)
    story.append(PageBreak())

    # ── SECTION 1 — HOW TO USE ───────────────────────────────────────────────
    story.append(_section_bar("Section 1 — How to Use the SRIT IIC Portal"))
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph(
        "The SRIT IIC Portal allows Innovation Ambassadors (IAs) to submit, manage and track IIC event "
        "reports online. Follow the steps below to submit an event report successfully.",
        s['body']
    ))
    story.append(Spacer(1, 4*mm))

    steps = [
        ("1", "Login to the Portal",
         ["Open the portal URL in your browser.",
          "Click the <b>Login as IA</b> tab on the home page.",
          "Enter your <b>@sritcbe.ac.in</b> email address and click Login.",
          "First-time users are automatically registered — no separate sign-up needed.",
          "Admin login (HIVE) requires email + password."]),

        ("2", "Navigate the Portal",
         ["<b>📊 Dashboard</b> — Overview of your submitted events, drafts and approval status.",
          "<b>📝 Submit Event</b> — Create a new event report or continue editing a saved draft.",
          "<b>📁 My Events</b> — View all your events, check approval status and download signed PDF."]),

        ("3", "Fill in Event Details",
         ["Academic Year and Program/Activity Name are required first.",
          "Start & End Date auto-calculates the IIC Quarter (Q1–Q4).",
          "Select Program Type (Workshop, Seminar, Hackathon, etc.).",
          "Select Program Driven By (IIC Calendar, Self Driven, Club Activity, ATL, etc.) — up to 2.",
          "Choose Professional Society / Club Name(s) if applicable.",
          "Fill Venue / Platform, Mode of Delivery, Duration, and Participant counts.",
          "Select SDG Goals and Program Outcomes (PO) mapping."]),

        ("4", "Objective, Speaker & Report",
         ["<b>Objective:</b> (a) Purpose of the activity and (b) Why it was organised — max 100 words.",
          "<b>Benefits:</b> Learning / Skill / Knowledge gained — max 150 words.",
          "<b>Speaker Details:</b> Name, Designation, Organisation, and a brief bio.",
          "<b>Brief Report:</b> 150–200 words describing how the session was conducted.",
          "<b>Key Highlights:</b> 5–8 bullet points of important moments.",
          "<b>Outcome:</b> What participants gained — aligned with IIC KPIs.",
          "<b>Feedback / Reflection:</b> 2–3 participant quotes or reflections."]),

        ("5", "Upload Photographs",
         ["Upload <b>at least 1 geotagged photo</b> (taken with phone location ON).",
          "Photo 1 — <b>Banner</b>: Print/soft copy of the activity banner.",
          "Photo 2 — <b>Speaker/Dais</b> with the banner visible in the background.",
          "Photo 3 — <b>Student &amp; Staff Participation</b> (front and back of hall if possible).",
          "Photo 4 — <b>Unique/Activity Moment</b>: candid engagement photo.",
          "Photo 5 — Additional moment (optional).",
          "Max 2MB per photo. JPEG/PNG formats accepted."]),

        ("6", "Upload Screenshots",
         ["<b>Pre-Activity Social Media Post</b> — screenshot of the event announcement.",
          "<b>Post-Activity Social Media Post</b> — screenshot of the post-event update.",
          "<b>Media Coverage</b> — screenshot of newspaper/online news/newsletter (if available).",
          "These are optional but strongly recommended for IIC records."]),

        ("7", "Upload Required Documents",
         ["<b>Attendance Report *</b> — Signed attendance sheet (PDF or image).",
          "<b>Feedback Analysis Report *</b> — Google Form responses with graphs (PDF).",
          "<b>Event Agenda *</b> — Programme schedule (PDF).",
          "<b>Chief Guest Biodata *</b> — Speaker's bio (PDF). (Optional for ATL School Activity)",
          "<b>Permission SOP *</b> — Signed permission letter with Principal's signature.",
          "<b>Invitation / Brochure *</b> — Event invitation or promotional material.",
          "<b>UC / Bill Documents</b> — Required only if expenditure > ₹0.",
          "Fields marked * are mandatory before you can Submit the event."]),

        ("8", "Save as Draft or Submit",
         ["Click <b>💾 Save as Draft</b> at any time — only the event name is required.",
          "Drafts are private and not visible to admin until submitted.",
          "The <b>📋 Submission Readiness</b> checklist shows which files are still missing (❌).",
          "Once all required files are uploaded, the <b>✅ Submit Event</b> button becomes active.",
          "After submission, admin will review and approve/reject the report."]),

        ("9", "Track Your Submission",
         ["Go to <b>📁 My Events</b> to see the status of all your submissions.",
          "<b>🟡 Pending</b> — Submitted, waiting for admin review.",
          "<b>🟢 Approved</b> — Event approved. Download the signed PDF if uploaded by admin.",
          "<b>🔴 Rejected</b> — See the rejection reason, edit your report and resubmit.",
          "Approved events are locked for editing."]),
    ]

    for num, title, bullets in steps:
        story.append(_step_card(num, title, bullets, s))

    story.append(Spacer(1, 3*mm))
    note_data = [[
        Paragraph(
            "⚠️  <b>Important:</b> The PDF report is generated automatically by the system when you submit. "
            "Admin will print it, obtain required signatures, and upload the signed PDF back for you to download. "
            "Never submit incomplete or incorrect information — rejected events must be corrected and resubmitted.",
            s['note']
        )
    ]]
    note_tbl = Table(note_data, colWidths=[170*mm])
    note_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), ORANGE_LIGHT),
        ('BOX', (0, 0), (-1, -1), 0.8, ORANGE),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(note_tbl)
    story.append(PageBreak())

    # ── SECTION 2 — BEFORE EVENT ─────────────────────────────────────────────
    before_items = [
        "## Planning & Approval",
        ("Identify the event topic, type, speaker/resource person, and target audience",
         "e.g. Workshop on Design Thinking for 2nd year students"),
        ("Fix the date, time, and venue / online platform", "Confirm room booking or Zoom/Google Meet link"),
        ("Get written permission from the Principal (Permission SOP)",
         "Must have Principal's signature — upload later to the portal"),
        ("Prepare and print the Event Banner",
         "Soft copy also needed — photo of banner is mandatory on portal"),

        "## Speaker / Chief Guest",
        ("Confirm the Speaker / Chief Guest and collect their biodata (PDF)",
         "Biodata must be uploaded to the portal after the event"),
        ("Send formal invitation to the speaker with event details",
         "Keep a copy of the email or letter for records"),
        ("Prepare a brief introduction for the speaker",
         "Also enter this in the portal under 'Brief about Expert/Speaker'"),

        "## Promotional Material",
        ("Design and print the Invitation / Brochure for the activity",
         "Scan/photograph and upload to the portal"),
        ("Post a <b>Pre-Activity announcement</b> on institute social media",
         "Instagram, LinkedIn, Twitter, Facebook — take screenshot before posting!"),
        ("Share event details via WhatsApp groups, Notice Boards, and Email",
         "Keep evidence of announcements"),

        "## Logistics & Documentation Prep",
        ("Prepare the Attendance Sheet with student and faculty name columns",
         "Must be signed by participants — scan after event"),
        ("Set up a Google Form for <b>Feedback Collection</b> from participants",
         "After event: download responses as PDF with graphs"),
        ("Prepare the Event Agenda / Programme Schedule",
         "Include time slots for each session — PDF required on portal"),
        ("Arrange projector, mic, seating, refreshments if needed", ""),
        ("Enable <b>Location/GPS</b> on your phone camera before the event",
         "At least 1 geotagged photo is mandatory on the portal"),
        ("Start a new event as Draft on the portal — fill known details now",
         "You can save draft with only the event name filled in"),
    ]

    story += _checklist_section(
        "Section 2 — BEFORE EVENT Checklist",
        bg=GREEN_DARK, items=before_items, s=s
    )
    story.append(PageBreak())

    # ── SECTION 3 — DURING EVENT ─────────────────────────────────────────────
    during_items = [
        "## Photography (IIC Guidelines — 4 to 5 Photos Required)",
        ("📍 Take at least <b>1 Geotagged Photo</b> with phone GPS/location enabled",
         "Must show location data in EXIF — do NOT crop the photo"),
        ("📸 Photo 1 — <b>Banner / Print Material</b>: Photograph the event banner clearly",
         "Shows the event title, date, venue and speaker details"),
        ("📸 Photo 2 — <b>Speaker / Dais Photo</b> with the banner visible in the background",
         "Clear shot of the speaker at the podium or dais"),
        ("📸 Photo 3 — <b>Student & Staff Participation</b>: Cover front and back of the hall",
         "Should show students, teaching and non-teaching staff clearly"),
        ("📸 Photo 4 — <b>Unique / Activity Moment</b>: Candid engagement moments",
         "e.g. Q&A, group activity, ideation session, demonstration"),
        ("📸 Photo 5 — Any additional highlight moment (Optional)", ""),

        "## Attendance",
        ("Circulate the <b>Attendance Sheet</b> — collect signatures from all participants", ""),
        ("Note down the exact count of Students, Faculty, and External participants",
         "You will enter these numbers on the portal"),

        "## Session Delivery",
        ("Ensure the session runs as per the Event Agenda", ""),
        ("Administer the <b>Google Form Feedback</b> to participants at the end",
         "Minimum 30–40 responses required for meaningful analysis"),
        ("If possible, <b>record the session video</b>",
         "Upload to YouTube/Google Drive and paste the link on the portal"),
        ("Note 5–8 <b>Key Highlights</b> from the session as bullet points",
         "e.g. topics discussed, notable interactions, demonstrations"),
        ("Note the <b>Outcome</b> — what did participants learn or gain?",
         "Align with IIC KPIs mentioned on the IIC portal"),
        ("Collect 2–3 <b>Participant Feedback Quotes</b> (verbal or written)",
         "Enter under 'Feedback / Reflection' on the portal"),
        ("Note names and roles of the <b>Organising Team Members</b>",
         "Enter under 'Organising Team Members' on the portal"),
    ]

    story += _checklist_section(
        "Section 3 — DURING EVENT Checklist",
        bg=BLUE_DARK, items=during_items, s=s
    )
    story.append(PageBreak())

    # ── SECTION 4 — AFTER EVENT ──────────────────────────────────────────────
    after_items = [
        "## Immediately After the Event",
        ("Collect the fully <b>signed Attendance Sheet</b>",
         "Scan/photograph — upload as PDF or image to the portal"),
        ("Download the <b>Feedback Analysis</b> from Google Form",
         "Responses → Download as PDF — must include charts/graphs"),
        ("Post a <b>Post-Activity update</b> on institute social media with photos",
         "Take a screenshot of the post — upload to portal under 'Screenshots'"),
        ("Collect the <b>Chief Guest Biodata</b> if not already received",
         "PDF format — upload to portal"),
        ("Collect all <b>bills, vouchers, or UC documents</b> if any expenditure occurred",
         "Mandatory upload if expenditure amount > ₹0"),
        ("Scan/photograph the <b>Event Banner</b> and any printed material",
         "You will need the banner photo for the portal"),

        "## Portal Submission",
        ("Open the portal and go to <b>📝 Submit Event</b> (or continue your saved Draft)",
         "URL: SRIT IIC Portal — hive@sritcbe.ac.in for access issues"),
        ("Fill or verify all event details: dates, participants, speaker info", ""),
        ("Write the <b>Brief Report</b> (150–200 words exactly)",
         "Describe how session started, key topics, interactions, Q&A, activities"),
        ("Enter <b>Key Highlights</b> (5–8 bullet points)", ""),
        ("Enter <b>Outcome of the Activity</b>",
         "Align with the KPIs shown on the IIC portal for this activity type"),
        ("Enter <b>Feedback / Reflection</b> — 2–3 participant quotes", ""),
        ("Enter <b>Organising Team Members</b> with their roles", ""),

        "## File Uploads — Check All Before Submitting",
        ("✅ Geotagged Photo (at least 1) — with location data", ""),
        ("✅ Photo 1 — Banner / Print Material", ""),
        ("✅ Photo 2 — Speaker/Dais with Banner", ""),
        ("✅ Photo 3 — Student & Staff Participation", ""),
        ("✅ Photo 4 — Unique/Activity Moment", ""),
        ("✅ Attendance Report (PDF or image)", ""),
        ("✅ Feedback Analysis Report (PDF with graphs)", ""),
        ("✅ Event Agenda (PDF)", ""),
        ("✅ Chief Guest Biodata (PDF)", "Skip if ATL School Activity"),
        ("✅ Permission SOP with Principal's Signature", ""),
        ("✅ Invitation / Brochure", ""),
        ("🔵 Pre & Post Activity Social Media Screenshots", "Recommended — optional"),
        ("🔵 Media Coverage Screenshot", "If available — optional"),
        ("🔵 UC / Bill Documents", "Required only if expenditure > ₹0"),

        "## Final Steps",
        ("Check the <b>📋 Submission Readiness</b> panel — all ❌ must turn ✅ before submitting", ""),
        ("Click <b>✅ Submit Event</b>",
         "Button activates only when all required files are uploaded"),
        ("Note: the system auto-generates a PDF report upon submission", ""),
        ("Admin (HIVE) will review, approve/reject your submission",
         "Go to 📁 My Events to track status"),
        ("If <b>Rejected</b>: read the rejection reason, correct and resubmit", ""),
        ("If <b>Approved</b>: download the signed PDF from 📁 My Events",
         "Keep it for department records — submit to HOD if required"),
        ("Also record the event details on the <b>MIC / IIC portal</b> online",
         "The SRIT IIC Portal submission is separate from the national IIC portal"),
    ]

    story += _checklist_section(
        "Section 4 — AFTER EVENT Checklist",
        bg=ORANGE, items=after_items, s=s
    )

    # quick-ref box
    story.append(Spacer(1, 6*mm))
    story.append(_section_bar("Quick Reference — File Size Limits & Formats", bg=GREEN_MED))
    story.append(Spacer(1, 1*mm))
    qr_data = [
        [Paragraph("<b>File Type</b>", s['bold']),
         Paragraph("<b>Accepted Formats</b>", s['bold']),
         Paragraph("<b>Max Size</b>", s['bold']),
         Paragraph("<b>Notes</b>", s['bold'])],
        [Paragraph("Photographs", s['body']), Paragraph("JPG, JPEG, PNG", s['body']),
         Paragraph("2 MB", s['body']), Paragraph("Enable GPS location for geotagged photo", s['body'])],
        [Paragraph("Screenshots", s['body']), Paragraph("JPG, JPEG, PNG, PDF", s['body']),
         Paragraph("10 MB", s['body']), Paragraph("Social media posts, media coverage", s['body'])],
        [Paragraph("Documents (PDF)", s['body']), Paragraph("PDF only", s['body']),
         Paragraph("10 MB", s['body']), Paragraph("Attendance, Feedback, Agenda, Biodata, SOP", s['body'])],
        [Paragraph("Mixed (PDF/Image)", s['body']), Paragraph("PDF, JPG, PNG", s['body']),
         Paragraph("10 MB", s['body']), Paragraph("Invitation, Brochure, UC/Bills", s['body'])],
    ]
    qr_tbl = Table(qr_data, colWidths=[32*mm, 40*mm, 22*mm, 76*mm])
    qr_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), GREEN_MED),
        ('TEXTCOLOR',  (0, 0), (-1, 0), WHITE),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, GREEN_PALE]),
        ('BOX',      (0, 0), (-1, -1), 0.5, GREEN_MED),
        ('INNERGRID', (0, 0), (-1, -1), 0.3, GREEN_LIGHT),
        ('TOPPADDING',    (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING',   (0, 0), (-1, -1), 4),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(qr_tbl)

    story.append(Spacer(1, 4*mm))
    contact_data = [[
        Paragraph(
            "For support, contact <b>HIVE</b> at <b>hive@sritcbe.ac.in</b> or visit the portal. "
            "This guide is maintained by HIVE — Hub for Innovation, Ventures &amp; Entrepreneurship, SRIT Coimbatore.",
            s['note']
        )
    ]]
    contact_tbl = Table(contact_data, colWidths=[170*mm])
    contact_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), GREEN_PALE),
        ('BOX', (0, 0), (-1, -1), 0.5, GREEN_MED),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(contact_tbl)

    # build
    doc.build(story, onFirstPage=_page_header_footer, onLaterPages=_page_header_footer)
    return buf.getvalue()


if __name__ == "__main__":
    pdf_bytes = generate_guidelines_pdf()
    with open("SRIT_IIC_Portal_Guidelines.pdf", "wb") as f:
        f.write(pdf_bytes)
    print(f"Generated: SRIT_IIC_Portal_Guidelines.pdf  ({len(pdf_bytes)//1024} KB)")
