import os
import uuid
from datetime import datetime
from io import BytesIO
from typing import Any, Dict, Optional

import gspread
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Image, KeepInFrame, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


DEFAULT_FEEDBACK_FORM_URL = "https://forms.gle/jEda5QosvhTiUpgL8"


def _safe_value(data: Dict[str, Any], key: str, default: str = "") -> str:
    value = data.get(key, "")
    return str(value).strip() if value is not None else default


class SOPGenerator:
    def __init__(self, event_data: Dict[str, Any]):
        self.event_data = event_data or {}
        self.styles = getSampleStyleSheet()
        self._setup_styles()

    def _setup_styles(self) -> None:
        style_names = {style.name for style in self.styles.byName.values()} if hasattr(self.styles, "byName") else set()
        if "Title" not in style_names:
            self.styles.add(ParagraphStyle(name="Title", fontName="Helvetica-Bold", fontSize=16, alignment=TA_CENTER, spaceAfter=12))
        if "SubTitle" not in style_names:
            self.styles.add(ParagraphStyle(name="SubTitle", fontName="Helvetica-Bold", fontSize=12, alignment=TA_CENTER, spaceAfter=8, textColor=colors.HexColor("#2E7D32")))
        if "Body" not in style_names:
            self.styles.add(ParagraphStyle(name="Body", fontName="Helvetica", fontSize=10, alignment=TA_JUSTIFY, leading=13, spaceAfter=6))
        if "Label" not in style_names:
            self.styles.add(ParagraphStyle(name="Label", fontName="Helvetica-Bold", fontSize=10, alignment=TA_LEFT, spaceAfter=4))
        if "Small" not in style_names:
            self.styles.add(ParagraphStyle(name="Small", fontName="Helvetica", fontSize=9, alignment=TA_LEFT, leading=11))
        if "InstTitle" not in style_names:
            self.styles.add(ParagraphStyle(name="InstTitle", fontName="Helvetica-Bold", fontSize=14, alignment=TA_CENTER, spaceAfter=0, leading=16))
        if "InstSubtitle" not in style_names:
            self.styles.add(ParagraphStyle(name="InstSubtitle", fontName="Helvetica-Bold", fontSize=11, alignment=TA_CENTER, textColor=colors.HexColor("#228B22"), spaceAfter=0))
        if "Accred" not in style_names:
            self.styles.add(ParagraphStyle(name="Accred", fontName="Helvetica", fontSize=7, alignment=TA_CENTER, leading=9, spaceAfter=2))
        if "QuestionLabel" not in style_names:
            self.styles.add(ParagraphStyle(name="QuestionLabel", fontName="Helvetica-Bold", fontSize=10, alignment=TA_LEFT, leading=12, spaceAfter=3))
        if "AnswerText" not in style_names:
            self.styles.add(ParagraphStyle(name="AnswerText", fontName="Helvetica", fontSize=10, alignment=TA_LEFT, leading=12, spaceAfter=8))
        if "ChecklistItem" not in style_names:
            self.styles.add(ParagraphStyle(name="ChecklistItem", fontName="Helvetica", fontSize=10, alignment=TA_LEFT, leading=14, leftIndent=12, spaceAfter=4))
        if "SOPDocTitle" not in style_names:
            self.styles.add(ParagraphStyle(name="SOPDocTitle", fontName="Helvetica-Bold", fontSize=13, alignment=TA_CENTER, spaceAfter=2))
        if "SOPDate" not in style_names:
            self.styles.add(ParagraphStyle(name="SOPDate", fontName="Helvetica-Bold", fontSize=10, alignment=TA_RIGHT, spaceAfter=8))
        if "TblNum" not in style_names:
            self.styles.add(ParagraphStyle(name="TblNum", fontName="Helvetica", fontSize=9, alignment=TA_LEFT, leading=12))
        if "TblLabel" not in style_names:
            self.styles.add(ParagraphStyle(name="TblLabel", fontName="Helvetica", fontSize=9, alignment=TA_LEFT, leading=12))
        if "TblValue" not in style_names:
            self.styles.add(ParagraphStyle(name="TblValue", fontName="Helvetica", fontSize=9, alignment=TA_LEFT, leading=12))
        if "TblLabelBold" not in style_names:
            self.styles.add(ParagraphStyle(name="TblLabelBold", fontName="Helvetica-Bold", fontSize=9, alignment=TA_LEFT, leading=12, spaceAfter=3))
        if "AttEventTitle" not in style_names:
            self.styles.add(ParagraphStyle(name="AttEventTitle", fontName="Helvetica-Bold", fontSize=13, alignment=TA_CENTER, spaceAfter=4, underlineWidth=0.6))
        if "AttSheetTitle" not in style_names:
            self.styles.add(ParagraphStyle(name="AttSheetTitle", fontName="Helvetica-Bold", fontSize=12, alignment=TA_CENTER, spaceAfter=6))
        if "AttDate" not in style_names:
            self.styles.add(ParagraphStyle(name="AttDate", fontName="Helvetica-Bold", fontSize=10, alignment=TA_LEFT, spaceAfter=6))
        if "AttFooterLabel" not in style_names:
            self.styles.add(ParagraphStyle(name="AttFooterLabel", fontName="Helvetica-Bold", fontSize=10, alignment=TA_LEFT, spaceAfter=2))
        if "AttFooterName" not in style_names:
            self.styles.add(ParagraphStyle(name="AttFooterName", fontName="Helvetica", fontSize=10, alignment=TA_LEFT, leftIndent=18))

    def _build_header(self):
        """Institution header matching the event report submission PDF."""
        elements = []
        logo_dir = os.path.join(os.path.dirname(__file__), "logos")
        page_width = A4[0] - 1.2 * inch

        logo_col_width = 0.8 * inch
        center_width = page_width - (2 * logo_col_width)

        try:
            snr = Image(os.path.join(logo_dir, "snr_logo.png"), width=0.65 * inch, height=0.65 * inch)
        except Exception:
            snr = ""

        try:
            srit = Image(os.path.join(logo_dir, "srit_logo.png"), width=0.65 * inch, height=0.65 * inch)
        except Exception:
            srit = ""

        title_data = [
            [Paragraph("SRI RAMAKRISHNA INSTITUTE OF TECHNOLOGY", self.styles["InstTitle"])],
            [Paragraph("COIMBATORE-10", self.styles["InstSubtitle"])],
            [Paragraph("(An Autonomous Institution)", self.styles["InstSubtitle"])],
        ]
        title_table = Table(title_data, colWidths=[center_width])
        title_table.setStyle(TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))

        header_table = Table([[snr, title_table, srit]], colWidths=[logo_col_width, center_width, logo_col_width])
        header_table.setStyle(TableStyle([
            ("ALIGN", (0, 0), (0, 0), "CENTER"),
            ("ALIGN", (1, 0), (1, 0), "CENTER"),
            ("ALIGN", (2, 0), (2, 0), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        elements.append(header_table)
        elements.append(Spacer(1, 0.05 * inch))

        accred = (
            "(Approved by AICTE, New Delhi - Affiliated to Anna University, Chennai)<br/>"
            "Pachapalayam, Perur Chettipalayam, Coimbatore - 641 010. www.srit.org Phone - 0422-2605577"
        )
        elements.append(Paragraph(accred, self.styles["Accred"]))
        elements.append(Spacer(1, 0.08 * inch))

        preferred_logos = ["hive.png", "sish.png", "iic_logo.png", "idea_lab.png", "ecell.png"]
        logo_images = []
        for file_name in preferred_logos:
            path = os.path.join(logo_dir, file_name)
            if not os.path.isfile(path):
                continue
            try:
                logo_images.append(Image(path, width=0.45 * inch, height=0.45 * inch))
            except Exception:
                continue

        if logo_images:
            logo_table = Table([logo_images], colWidths=[page_width / len(logo_images)] * len(logo_images))
            logo_table.setStyle(TableStyle([
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 2),
                ("RIGHTPADDING", (0, 0), (-1, -1), 2),
            ]))
            elements.append(logo_table)

        elements.append(Spacer(1, 0.06 * inch))

        line = Table([[""]], colWidths=[page_width], rowHeights=[3])
        line.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#8B008B")),
        ]))
        elements.append(line)
        elements.append(Spacer(1, 0.1 * inch))

        return elements

    def _get_question_flow(self):
        return [
            ("1", "Department, Association, Club", "department_association_club", False),
            ("2", "Nature of Programme", "nature_of_programme", False),
            ("3", "Title of the Programme", "title_of_programme", False),
            ("4", "Name of the Faculty Coordinator(s)", "faculty_coordinators", False),
            ("5", "Date and Day", "date_day", False),
            ("6", "Time", "time", False),
            ("7", "Venue", "venue", False),
            ("8", "Participants", "participants", False),
            ("9", "Total Audience expected within and outside the Institute", "total_audience_expected", False),
            ("10", "Details of Resource Person:\n(Name, Designation, Organization, Address, Phone No., E-mail ID)", "resource_person_details", False),
            ("11", "Estimated Expenditure", "estimated_expenditure", False),
            ("12", "Sources & Application of Fund\n(Budget to be given as Annexure)", "sources_application_of_fund", False),
            ("13", "What is the objective of conducting the programme?", "objective", True),
            ("14", "How will it contribute to student development?", "student_development", True),
            ("15", "How will it contribute to Institution Development/ Brand Building?", "institution_development", True),
        ]

    def _build_sop_table(self):
        page_width = A4[0] - 1.2 * inch
        num_width = 0.35 * inch
        label_width = 2.0 * inch
        value_width = page_width - num_width - label_width

        rows = []
        span_commands = []

        for idx, (number, label, key, merged) in enumerate(self._get_question_flow()):
            answer = _safe_value(self.event_data, key, "") or "-"
            answer_html = answer.replace("\n", "<br/>")
            label_html = label.replace("\n", "<br/>")

            if merged:
                combined = f'<b>{label_html}</b><br/>{answer_html}'
                rows.append([
                    Paragraph(number, self.styles["TblNum"]),
                    Paragraph(combined, self.styles["TblValue"]),
                    "",
                ])
                span_commands.append(("SPAN", (1, idx), (2, idx)))
            else:
                rows.append([
                    Paragraph(number, self.styles["TblNum"]),
                    Paragraph(label_html, self.styles["TblLabel"]),
                    Paragraph(answer_html, self.styles["TblValue"]),
                ])

        table = Table(rows, colWidths=[num_width, label_width, value_width])
        style_commands = [
            ("GRID", (0, 0), (-1, -1), 0.6, colors.black),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]
        style_commands.extend(span_commands)
        table.setStyle(TableStyle(style_commands))
        return table

    def generate_sop_pdf(self) -> bytes:
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=0.6 * inch,
            leftMargin=0.6 * inch,
            topMargin=0.6 * inch,
            bottomMargin=0.6 * inch,
        )
        story = []
        story.extend(self._build_header())

        story.append(Paragraph("Application for Organizing Programme", self.styles["SOPDocTitle"]))
        story.append(Paragraph(f"Date: {datetime.now().strftime('%d.%m.%Y')}", self.styles["SOPDate"]))
        story.append(Spacer(1, 0.06 * inch))

        story.append(self._build_sop_table())
        story.append(Spacer(1, 0.2 * inch))

        story.append(Paragraph("Signature of Faculty Coordinator: __________________________", self.styles["QuestionLabel"]))
        story.append(Spacer(1, 0.04 * inch))
        story.append(Paragraph("Recommendation of HOD: Recommended / Not Recommended: __________________________", self.styles["QuestionLabel"]))
        story.append(Spacer(1, 0.04 * inch))
        story.append(Paragraph("Approval of Principal: Permitted / Not Permitted: __________________________", self.styles["QuestionLabel"]))

        story.append(PageBreak())
        story.extend(self._build_header())
        story.append(Paragraph("Event Checklist", self.styles["Title"]))
        story.append(Paragraph("Use this checklist to ensure all event preparations and post-event steps are completed.", self.styles["Body"]))
        story.append(Spacer(1, 0.1 * inch))

        checklist_items = [
            "Confirm programme theme and obtain necessary approvals.",
            "Finalize resource person details and share itinerary.",
            "Reserve venue/equipment and arrange seating.",
            "Prepare publicity materials and notify participants.",
            "Arrange attendance sheet and registration process.",
            "Set up audio/visual support and any demo equipment.",
            "Collect participant feedback and distribute any materials.",
            "Capture event photographs and document the session.",
            "Review expenses and attach budget annexure.",
            "Submit the final report and related documents after the programme."
        ]

        for item in checklist_items:
            story.append(Paragraph(f"[&nbsp;&nbsp;] {item}", self.styles["ChecklistItem"]))

        doc.build(story)
        return buffer.getvalue()

    def generate_attendance_pdf(self) -> bytes:
        """Single-page attendance sheet matching the SRIT attendance template, using the SOP header."""
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=0.6 * inch,
            leftMargin=0.6 * inch,
            topMargin=0.6 * inch,
            bottomMargin=0.6 * inch,
        )

        # SimpleDocTemplate's default Frame carries 6pt padding on every side that
        # is not reflected in doc.width/doc.height, so the true usable area is smaller.
        frame_pad = 12  # 6pt top + 6pt bottom (and left + right)
        usable_width = doc.width - frame_pad
        usable_height = doc.height - frame_pad

        event_title = _safe_value(self.event_data, "event_title", _safe_value(self.event_data, "title_of_programme", "Event"))
        date_value = _safe_value(self.event_data, "event_date", _safe_value(self.event_data, "date_day", ""))
        coordinator = _safe_value(self.event_data, "coordinator_name", _safe_value(self.event_data, "faculty_coordinators", ""))

        header_elements = self._build_header()
        header_height = 0.0
        for element in header_elements:
            _, h = element.wrap(usable_width, usable_height)
            header_height += h

        title_para = Paragraph(f"<u>{event_title}</u>", self.styles["AttEventTitle"])
        subtitle_para = Paragraph("<u>Attendance Sheet</u>", self.styles["AttSheetTitle"])
        date_para = Paragraph(f"<u>Date: {date_value or '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'}</u>", self.styles["AttDate"])
        footer_elements = [
            Spacer(1, 0.18 * inch),
            Paragraph("Signature of the Faculty Incharge", self.styles["AttFooterLabel"]),
            Paragraph(coordinator, self.styles["AttFooterName"]) if coordinator else Spacer(1, 0.15 * inch),
        ]

        # Fixed at 25 rows so each row stays comfortably large and readable on
        # a single page, regardless of the expected audience count.
        row_count = 25
        total_table_rows = row_count + 1
        row_height = 0.26 * inch
        data_font_size = 10

        header_style = ParagraphStyle(name="AttHeader", fontName="Helvetica-Bold", fontSize=data_font_size, alignment=TA_LEFT, leading=data_font_size + 1)

        rows = [[
            Paragraph("S NO", header_style),
            Paragraph("ROLL NUMBER", header_style),
            Paragraph("NAME", header_style),
            Paragraph("SIGN", header_style),
        ]]
        for _ in range(row_count):
            rows.append(["", "", "", ""])

        col_widths = [0.6 * inch, 1.5 * inch, usable_width - (0.6 + 1.5 + 1.6) * inch, 1.6 * inch]

        attendance_table = Table(rows, colWidths=col_widths, rowHeights=[row_height] * total_table_rows)
        attendance_table.setStyle(
            TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F1F8E9")),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 4),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                    ("TOPPADDING", (0, 0), (-1, -1), 1),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
                ]
            )
        )

        body = [
            title_para,
            Spacer(1, 0.04 * inch),
            subtitle_para,
            Spacer(1, 0.08 * inch),
            date_para,
            Spacer(1, 0.06 * inch),
            attendance_table,
        ] + footer_elements

        # Guarantees the title/date/table/footer block always fits below the
        # header on a single page, shrinking proportionally only if needed.
        body_frame = KeepInFrame(
            usable_width,
            max(usable_height - header_height - 0.05 * inch, 1 * inch),
            body,
            mode="shrink",
            hAlign="CENTER",
        )

        story = header_elements + [body_frame]

        doc.build(story)
        return buffer.getvalue()


def create_feedback_form_link(event_data: Dict[str, Any], creds: Optional[Any] = None) -> str:
    title = _safe_value(event_data, "event_title", "Event Feedback")
    description = (
        "Please share your feedback about the event. "
        f"Event: {title}."
    )

    if not creds:
        return DEFAULT_FEEDBACK_FORM_URL

    try:
        service = build("forms", "v1", credentials=creds)
        form = service.forms().create(
            body={
                "info": {
                    "title": f"Feedback - {title}",
                    "documentTitle": f"Feedback - {title}",
                    "description": description,
                }
            }
        ).execute()

        form_id = form.get("formId")
        if not form_id:
            raise ValueError("No form ID returned")

        requests = [
            {
                "createItem": {
                    "item": {
                        "title": "Full Name",
                        "questionItem": {
                            "question": {
                                "required": True,
                                "textQuestion": {},
                            }
                        },
                    },
                    "location": {"index": 0},
                }
            },
            {
                "createItem": {
                    "item": {
                        "title": "Department / Class",
                        "questionItem": {
                            "question": {
                                "required": True,
                                "textQuestion": {},
                            }
                        },
                    },
                    "location": {"index": 1},
                }
            },
            {
                "createItem": {
                    "item": {
                        "title": "How would you rate this event?",
                        "questionItem": {
                            "question": {
                                "required": True,
                                "scaleQuestion": {
                                    "low": 1,
                                    "high": 5,
                                    "lowLabel": "Poor",
                                    "highLabel": "Excellent",
                                },
                            }
                        },
                    },
                    "location": {"index": 2},
                }
            },
            {
                "createItem": {
                    "item": {
                        "title": "What did you like most about this event?",
                        "questionItem": {
                            "question": {
                                "required": False,
                                "textQuestion": {"paragraph": True},
                            }
                        },
                    },
                    "location": {"index": 3},
                }
            },
            {
                "createItem": {
                    "item": {
                        "title": "Any suggestions for improvement?",
                        "questionItem": {
                            "question": {
                                "required": False,
                                "textQuestion": {"paragraph": True},
                            }
                        },
                    },
                    "location": {"index": 4},
                }
            },
        ]
        service.forms().batchUpdate(formId=form_id, body={"requests": requests}).execute()
        metadata = service.forms().get(formId=form_id).execute()
        return metadata.get("responderUri") or f"https://docs.google.com/forms/d/e/{form_id}/viewform"
    except Exception:
        return DEFAULT_FEEDBACK_FORM_URL


def generate_feedback_pdf(event_data: Dict[str, Any]) -> bytes:
    """Generate a printable feedback form as PDF (local-only fallback)."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=0.6 * inch,
        leftMargin=0.6 * inch,
        topMargin=0.6 * inch,
        bottomMargin=0.6 * inch,
    )
    story = []

    title = _safe_value(event_data, "event_title", "Event Feedback Form")
    story.append(Paragraph(title, ParagraphStyle(name="FTitle", fontSize=14, alignment=TA_CENTER, fontName="Helvetica-Bold")))
    story.append(Spacer(1, 0.12 * inch))
    story.append(Paragraph("Please provide your honest feedback below:", ParagraphStyle(name="FIntro", fontSize=10, alignment=TA_LEFT)))
    story.append(Spacer(1, 0.12 * inch))

    # Basic metadata
    meta_table = Table([
        [Paragraph("Event Date:", ParagraphStyle(name="Lbl", fontName="Helvetica-Bold", fontSize=9)), Paragraph(_safe_value(event_data, "event_date", ""))],
        [Paragraph("Venue:", ParagraphStyle(name="Lbl", fontName="Helvetica-Bold", fontSize=9)), Paragraph(_safe_value(event_data, "venue", ""))],
        [Paragraph("Coordinator:", ParagraphStyle(name="Lbl", fontName="Helvetica-Bold", fontSize=9)), Paragraph(_safe_value(event_data, "coordinator_name", ""))],
    ], colWidths=[1.2 * inch, 5.6 * inch])
    meta_table.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'MIDDLE')]))
    story.append(meta_table)
    story.append(Spacer(1, 0.12 * inch))

    # Questions
    q_style = ParagraphStyle(name="Q", fontSize=10, leading=14)
    story.append(Paragraph("1. Your Name:", q_style))
    story.append(Spacer(1, 0.08 * inch))
    story.append(Paragraph("__________________________________________", ParagraphStyle(name="Line", fontSize=10)))
    story.append(Spacer(1, 0.12 * inch))

    story.append(Paragraph("2. Department / Class:", q_style))
    story.append(Spacer(1, 0.08 * inch))
    story.append(Paragraph("__________________________________________", ParagraphStyle(name="Line2", fontSize=10)))
    story.append(Spacer(1, 0.12 * inch))

    story.append(Paragraph("3. How would you rate this event? (1 - Poor, 5 - Excellent)", q_style))
    story.append(Spacer(1, 0.06 * inch))
    story.append(Paragraph("[ ] 1    [ ] 2    [ ] 3    [ ] 4    [ ] 5", ParagraphStyle(name="Choices", fontSize=11)))
    story.append(Spacer(1, 0.12 * inch))

    story.append(Paragraph("4. What did you like most about this event?", q_style))
    story.append(Spacer(1, 0.06 * inch))
    for _ in range(3):
        story.append(Paragraph("________________________________________________________________________________", ParagraphStyle(name="LinePara", fontSize=10)))
        story.append(Spacer(1, 0.06 * inch))

    story.append(Paragraph("5. Suggestions for improvement:", q_style))
    story.append(Spacer(1, 0.06 * inch))
    for _ in range(3):
        story.append(Paragraph("________________________________________________________________________________", ParagraphStyle(name="LinePara2", fontSize=10)))
        story.append(Spacer(1, 0.06 * inch))

    doc.build(story)
    return buffer.getvalue()


def generate_sop_documents_local(event_data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate the SOP and Attendance PDFs locally without any Google storage."""
    generator = SOPGenerator(event_data)
    sop_bytes = generator.generate_sop_pdf()
    attendance_bytes = generator.generate_attendance_pdf()

    event_title = _safe_value(event_data, "title_of_programme", _safe_value(event_data, "event_title", "Event"))
    record_id = f"LOCAL-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:4].upper()}"
    sop_filename = f"{event_title.replace(' ', '_')}_{record_id}_SOP.pdf"
    attendance_filename = f"{event_title.replace(' ', '_')}_{record_id}_Attendance.pdf"

    return {
        "record_id": record_id,
        "sop_pdf": sop_bytes,
        "sop_filename": sop_filename,
        "attendance_pdf": attendance_bytes,
        "attendance_filename": attendance_filename,
    }


def upload_to_drive(drive_service: Optional[Any], folder_id: Optional[str], filename: str, content: bytes) -> Optional[Dict[str, str]]:
    if not drive_service:
        return None

    try:
        file_metadata = {"name": filename, "parents": [folder_id] if folder_id else []}
        media = MediaIoBaseUpload(BytesIO(content), mimetype="application/pdf", resumable=True)
        file = drive_service.files().create(body=file_metadata, media_body=media, fields="id,webViewLink,webContentLink").execute()
        return {
            "id": file.get("id", ""),
            "webViewLink": file.get("webViewLink", ""),
            "webContentLink": file.get("webContentLink", ""),
        }
    except Exception:
        return None


def ensure_sop_sheet(sheets_client: Any, spreadsheet_id: str) -> Any:
    spreadsheet = sheets_client.open_by_key(spreadsheet_id)
    try:
        return spreadsheet.worksheet("SOP_Generations")
    except gspread.exceptions.WorksheetNotFound:
        sheet = spreadsheet.add_worksheet(title="SOP_Generations", rows=1000, cols=20)
        sheet.append_row([
            "Record ID",
            "Event Title",
            "Event Date",
            "Venue",
            "Department",
            "Audience Count",
            "Coordinator",
            "Contact Person",
            "SOP File Link",
            "Attendance File Link",
            "Feedback Form Link",
            "Generated At",
        ])
        return sheet


def append_sop_record(
    sheets_client: Any,
    spreadsheet_id: str,
    record: Dict[str, Any],
) -> None:
    sheet = ensure_sop_sheet(sheets_client, spreadsheet_id)
    row = [
        record.get("record_id", ""),
        record.get("event_title", ""),
        record.get("event_date", ""),
        record.get("venue", ""),
        record.get("department", ""),
        record.get("audience_count", ""),
        record.get("coordinator_name", ""),
        record.get("contact_person", ""),
        record.get("sop_link", ""),
        record.get("attendance_link", ""),
        record.get("feedback_link", ""),
        record.get("generated_at", ""),
    ]
    sheet.append_row(row)


def generate_sop_documents(
    event_data: Dict[str, Any],
    sheets_client: Optional[Any] = None,
    spreadsheet_id: Optional[str] = None,
    drive_service: Optional[Any] = None,
    drive_folder_id: Optional[str] = None,
    creds: Optional[Any] = None,
) -> Dict[str, Any]:
    generator = SOPGenerator(event_data)
    sop_bytes = generator.generate_sop_pdf()
    attendance_bytes = generator.generate_attendance_pdf()
    form_link = create_feedback_form_link(event_data, creds=creds)

    event_title = _safe_value(event_data, "event_title", "Event")
    event_date = _safe_value(event_data, "event_date", datetime.now().strftime("%Y-%m-%d"))
    record_id = f"SOP-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:4].upper()}"

    sop_filename = f"{event_title.replace(' ', '_')}_{record_id}_SOP.pdf"
    attendance_filename = f"{event_title.replace(' ', '_')}_{record_id}_Attendance.pdf"

    sop_upload = upload_to_drive(drive_service, drive_folder_id, sop_filename, sop_bytes) if drive_service else None
    attendance_upload = upload_to_drive(drive_service, drive_folder_id, attendance_filename, attendance_bytes) if drive_service else None

    sop_link = sop_upload.get("webViewLink") if sop_upload else ""
    attendance_link = attendance_upload.get("webViewLink") if attendance_upload else ""

    if sheets_client and spreadsheet_id:
        append_sop_record(
            sheets_client,
            spreadsheet_id,
            {
                "record_id": record_id,
                "event_title": event_title,
                "event_date": event_date,
                "venue": _safe_value(event_data, "venue", ""),
                "department": _safe_value(event_data, "department", ""),
                "audience_count": _safe_value(event_data, "audience_count", "0"),
                "coordinator_name": _safe_value(event_data, "coordinator_name", ""),
                "contact_person": _safe_value(event_data, "contact_person", ""),
                "sop_link": sop_link,
                "attendance_link": attendance_link,
                "feedback_link": form_link,
                "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            },
        )

    return {
        "record_id": record_id,
        "sop_pdf": sop_bytes,
        "attendance_pdf": attendance_bytes,
        "sop_filename": sop_filename,
        "attendance_filename": attendance_filename,
        "feedback_form_link": form_link,
        "sop_link": sop_link,
        "attendance_link": attendance_link,
    }
