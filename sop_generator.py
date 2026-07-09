import os
import uuid
from datetime import datetime
from io import BytesIO
from typing import Any, Dict, Optional

import gspread
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


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

        title = _safe_value(self.event_data, "event_title", "SOP for Event")
        story.append(Paragraph(title, self.styles["Title"]))
        story.append(Paragraph("Standard Operating Procedure (SOP) for Event Conduct", self.styles["SubTitle"]))
        story.append(Spacer(1, 0.15 * inch))

        details = [
            ("Event Date", _safe_value(self.event_data, "event_date", "To be finalized")),
            ("Venue / Platform", _safe_value(self.event_data, "venue", "To be finalized")),
            ("Organizing Department", _safe_value(self.event_data, "department", "Department")),
            ("Coordinator", _safe_value(self.event_data, "coordinator_name", "Coordinator")),
            ("Contact Person", _safe_value(self.event_data, "contact_person", "Contact Person")),
            ("Expected Audience", _safe_value(self.event_data, "audience_count", "0")),
        ]
        table = Table(
            [[Paragraph(col1, self.styles["Label"]), Paragraph(col2, self.styles["Body"])] for col1, col2 in details],
            colWidths=[2.0 * inch, 4.8 * inch],
        )
        table.setStyle(
            TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8F5E9")),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        story.append(table)
        story.append(Spacer(1, 0.2 * inch))

        story.append(Paragraph("1. Purpose", self.styles["Label"]))
        story.append(Paragraph(_safe_value(self.event_data, "objective", "To conduct the event smoothly and achieve the planned learning outcomes."), self.styles["Body"]))
        story.append(Spacer(1, 0.1 * inch))

        story.append(Paragraph("2. Scope", self.styles["Label"]))
        story.append(Paragraph("This SOP covers planning, execution, attendance monitoring, feedback collection and follow-up activities for the event.", self.styles["Body"]))
        story.append(Spacer(1, 0.1 * inch))

        story.append(Paragraph("3. Responsibilities", self.styles["Label"]))
        story.append(Paragraph("The organizer, faculty coordinator and student volunteers will coordinate the event, manage the audience, collect feedback, and maintain the attendance record.", self.styles["Body"]))
        story.append(Spacer(1, 0.1 * inch))

        story.append(Paragraph("4. Event Flow", self.styles["Label"]))
        story.append(Paragraph("- Welcome the audience and introduce the purpose of the session.\n- Share the agenda and conduct the event as per the planned schedule.\n- Record attendance and collect feedback using the generated feedback form.\n- Close with a summary and thank the participants.", self.styles["Body"]))
        story.append(Spacer(1, 0.2 * inch))

        story.append(Paragraph("Prepared By", self.styles["Label"]))
        story.append(Paragraph(_safe_value(self.event_data, "coordinator_name", "Coordinator Name"), self.styles["Body"]))
        story.append(Spacer(1, 0.3 * inch))
        story.append(Paragraph("Signature: __________________________", self.styles["Body"]))

        doc.build(story)
        return buffer.getvalue()

    def generate_attendance_pdf(self) -> bytes:
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

        title = _safe_value(self.event_data, "event_title", "Attendance Sheet")
        story.append(Paragraph(title, self.styles["Title"]))
        story.append(Paragraph("Attendance Sheet for Event Participants", self.styles["SubTitle"]))
        story.append(Spacer(1, 0.15 * inch))

        meta = [
            ("Date", _safe_value(self.event_data, "event_date", "To be finalized")),
            ("Venue / Platform", _safe_value(self.event_data, "venue", "To be finalized")),
            ("Department", _safe_value(self.event_data, "department", "Department")),
            ("Coordinator", _safe_value(self.event_data, "coordinator_name", "Coordinator")),
        ]
        table = Table(
            [[Paragraph(col1, self.styles["Label"]), Paragraph(col2, self.styles["Body"])] for col1, col2 in meta],
            colWidths=[1.8 * inch, 4.8 * inch],
        )
        table.setStyle(
            TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#FFF3E0")),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        story.append(table)
        story.append(Spacer(1, 0.2 * inch))

        try:
            audience_count = int(_safe_value(self.event_data, "audience_count", "0"))
        except Exception:
            audience_count = 0

        rows = [[Paragraph("Sl. No.", self.styles["Label"]), Paragraph("Name", self.styles["Label"]), Paragraph("Department", self.styles["Label"]), Paragraph("Signature", self.styles["Label"] )]]
        for idx in range(1, max(1, audience_count) + 1):
            rows.append([str(idx), "", "", ""])

        attendance_table = Table(rows, colWidths=[0.7 * inch, 2.2 * inch, 1.7 * inch, 2.0 * inch])
        attendance_table.setStyle(
            TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F1F8E9")),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#FAFAFA")]),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("HEIGHT", (0, 0), (-1, -1), 0.32 * inch),
                    ("LEFTPADDING", (0, 0), (-1, -1), 4),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        story.append(attendance_table)
        story.append(Spacer(1, 0.25 * inch))
        story.append(Paragraph("Note: This attendance sheet will be used for signing purposes and should be verified by the coordinator.", self.styles["Small"]))

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
    """Generate SOP, Attendance and Feedback PDFs locally without any Google storage."""
    generator = SOPGenerator(event_data)
    sop_bytes = generator.generate_sop_pdf()
    attendance_bytes = generator.generate_attendance_pdf()
    feedback_bytes = generate_feedback_pdf(event_data)

    event_title = _safe_value(event_data, "event_title", "Event")
    record_id = f"LOCAL-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:4].upper()}"
    sop_filename = f"{event_title.replace(' ', '_')}_{record_id}_SOP.pdf"
    attendance_filename = f"{event_title.replace(' ', '_')}_{record_id}_Attendance.pdf"
    feedback_filename = f"{event_title.replace(' ', '_')}_{record_id}_Feedback.pdf"

    return {
        "record_id": record_id,
        "sop_pdf": sop_bytes,
        "attendance_pdf": attendance_bytes,
        "feedback_pdf": feedback_bytes,
        "sop_filename": sop_filename,
        "attendance_filename": attendance_filename,
        "feedback_filename": feedback_filename,
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
