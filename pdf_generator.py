"""
PDF Report Generator for IIC Event Submission Portal
Generates PDF reports matching the SRIT IIC format with embedded images and documents
All content is built directly into a single PDF - no merging required
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle, Paragraph,
                                 Spacer, Image, PageBreak, KeepTogether, Flowable)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.pdfgen import canvas
import os
from io import BytesIO

# For PDF reading (to extract pages from uploaded PDFs)
try:
    from PyPDF2 import PdfReader, PdfWriter
    PDF_MERGE_AVAILABLE = True
except ImportError:
    PDF_MERGE_AVAILABLE = False


class NumberedCanvas(canvas.Canvas):
    """Custom canvas for page numbers"""
    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_count):
        self.setFont("Helvetica", 9)
        self.drawCentredString(A4[0]/2, 0.4*inch, f"Page {self._pageNumber}")


class IICReportGenerator:
    def __init__(self, event_data, logo_path=None, drive_manager=None):
        self.event_data = event_data
        self.logo_base_path = logo_path or "logos"
        self.drive_manager = drive_manager
        self.styles = getSampleStyleSheet()
        self._setup_styles()
        self.page_width = A4[0] - 1*inch
        self.merge_status = []  # For debugging

    def _setup_styles(self):
        """Setup custom styles"""
        self.styles.add(ParagraphStyle(
            name='InstTitle', fontSize=14, fontName='Helvetica-Bold',
            alignment=TA_CENTER, spaceAfter=0, leading=16
        ))
        self.styles.add(ParagraphStyle(
            name='InstSubtitle', fontSize=11, fontName='Helvetica-Bold',
            alignment=TA_CENTER, textColor=colors.HexColor('#228B22'), spaceAfter=0
        ))
        self.styles.add(ParagraphStyle(
            name='Accred', fontSize=7, fontName='Helvetica',
            alignment=TA_CENTER, leading=9, spaceAfter=2
        ))
        self.styles.add(ParagraphStyle(
            name='RepTitle', fontSize=16, fontName='Helvetica-Bold',
            alignment=TA_CENTER, spaceAfter=12, spaceBefore=8
        ))
        self.styles.add(ParagraphStyle(
            name='SecHead', fontSize=12, fontName='Helvetica-Bold',
            alignment=TA_CENTER, backColor=colors.HexColor('#D8BFD8'),
            spaceAfter=8, spaceBefore=8, leading=18, textColor=colors.HexColor('#4B0082')
        ))
        self.styles.add(ParagraphStyle(
            name='TblLabel', fontSize=9, fontName='Helvetica-Bold', leading=11
        ))
        self.styles.add(ParagraphStyle(
            name='TblValue', fontSize=9, fontName='Helvetica', leading=11
        ))
        self.styles.add(ParagraphStyle(
            name='Body', fontSize=10, fontName='Helvetica',
            alignment=TA_JUSTIFY, leading=13, spaceAfter=6
        ))
        self.styles.add(ParagraphStyle(
            name='DocTitle', fontSize=14, fontName='Helvetica-Bold',
            alignment=TA_CENTER, spaceAfter=20, spaceBefore=20
        ))

    def generate_pdf(self, output_path):
        """Generate complete PDF with all content embedded"""
        self.merge_status = []
        self.merge_status.append("Starting PDF generation...")

        # Step 1: Build main report
        main_buffer = BytesIO()
        doc = SimpleDocTemplate(main_buffer, pagesize=A4,
            rightMargin=0.5*inch, leftMargin=0.5*inch,
            topMargin=0.3*inch, bottomMargin=0.6*inch)

        story = []

        # Page 1: Event Details
        story.extend(self._header())
        story.extend(self._details_table())
        story.append(PageBreak())

        # Page 2: Objectives and Benefits
        story.extend(self._header())
        story.extend(self._objectives())
        story.append(PageBreak())

        # Page 3+: Brief Report (may span multiple pages)
        story.extend(self._header())
        story.extend(self._brief_report())
        story.append(PageBreak())

        # Signatures Page
        story.extend(self._header())
        story.extend(self._signatures())
        story.append(PageBreak())

        # Photo Annexures (6 photos embedded directly)
        photo_elements = self._photo_annexures()
        story.extend(photo_elements)

        # Build main report first
        doc.build(story, canvasmaker=NumberedCanvas)
        self.merge_status.append(f"Main report built successfully")

        # Step 2: Now merge uploaded PDF documents
        if PDF_MERGE_AVAILABLE and self.drive_manager:
            self.merge_status.append("Starting document merge process...")
            final_buffer = self._merge_uploaded_documents(main_buffer)
            if final_buffer:
                final_buffer.seek(0)
                if isinstance(output_path, BytesIO):
                    output_path.write(final_buffer.getvalue())
                    output_path.seek(0)
                    return output_path
                return final_buffer
        else:
            if not PDF_MERGE_AVAILABLE:
                self.merge_status.append("PyPDF2 not available - documents will not be merged")
            if not self.drive_manager:
                self.merge_status.append("No drive_manager - documents will not be merged")

        # Return main buffer if merging failed or not available
        main_buffer.seek(0)
        if isinstance(output_path, BytesIO):
            output_path.write(main_buffer.getvalue())
            output_path.seek(0)
            return output_path
        return main_buffer

    def _header(self):
        """Create properly aligned header"""
        elements = []

        logo_col_width = 0.8*inch
        center_width = self.page_width - (2 * logo_col_width)

        # Load logos
        try:
            snr = Image(os.path.join(self.logo_base_path, "snr_logo.png"),
                       width=0.65*inch, height=0.65*inch)
        except:
            snr = ""

        try:
            srit = Image(os.path.join(self.logo_base_path, "srit_logo.png"),
                        width=0.65*inch, height=0.65*inch)
        except:
            srit = ""

        # Title block
        title_data = [
            [Paragraph("SRI RAMAKRISHNA INSTITUTE OF TECHNOLOGY", self.styles['InstTitle'])],
            [Paragraph("COIMBATORE-10", self.styles['InstSubtitle'])],
            [Paragraph("(An Autonomous Institution)", self.styles['InstSubtitle'])]
        ]
        title_table = Table(title_data, colWidths=[center_width])
        title_table.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 0),
            ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ]))

        header_data = [[snr, title_table, srit]]
        header_table = Table(header_data, colWidths=[logo_col_width, center_width, logo_col_width])
        header_table.setStyle(TableStyle([
            ('ALIGN', (0,0), (0,0), 'CENTER'),
            ('ALIGN', (1,0), (1,0), 'CENTER'),
            ('ALIGN', (2,0), (2,0), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        elements.append(header_table)
        elements.append(Spacer(1, 0.05*inch))

        # Accreditation
        accred = """Accredited by NAAC with an 'A' Grade and All eligible UG Engineering Programmes are Accredited by NBA<br/>
(Approved by AICTE, New Delhi - Affiliated to Anna University, Chennai)<br/>
Pachapalayam, Perur Chettipalayam, Coimbatore - 641 010. www.srit.org Phone - 0422-2605577"""
        elements.append(Paragraph(accred, self.styles['Accred']))
        elements.append(Spacer(1, 0.08*inch))

        # 7 Logos row
        logo_width = 0.45*inch
        logo_height = 0.45*inch
        col_width = self.page_width / 7

        try:
            logos = []
            logo_files = ["hive.png", "sish.png", "mic.png", "aicte.png",
                         "iic_logo.png", "idea_lab.png", "ecell.png"]
            for lf in logo_files:
                try:
                    img = Image(os.path.join(self.logo_base_path, lf),
                               width=logo_width, height=logo_height)
                    logos.append(img)
                except:
                    logos.append("")

            logo_table = Table([logos], colWidths=[col_width]*7)
            logo_table.setStyle(TableStyle([
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('LEFTPADDING', (0,0), (-1,-1), 2),
                ('RIGHTPADDING', (0,0), (-1,-1), 2),
            ]))
            elements.append(logo_table)
        except:
            pass

        elements.append(Spacer(1, 0.06*inch))

        # Purple line
        line = Table([['']], colWidths=[self.page_width], rowHeights=[3])
        line.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#8B008B')),
            ('LINEABOVE', (0,0), (-1,-1), 1, colors.HexColor('#8B008B')),
            ('LINEBELOW', (0,0), (-1,-1), 1, colors.HexColor('#8B008B')),
        ]))
        elements.append(line)
        elements.append(Spacer(1, 0.1*inch))

        return elements

    def _details_table(self):
        """Event details table"""
        elements = []
        name = self.event_data.get('Program Name', 'Event')
        elements.append(Paragraph(f"Report on {name}", self.styles['RepTitle']))

        data = [
            ["ACADEMIC YEAR:", self.event_data.get('Academic Year', '')],
            ["QUARTER:", self.event_data.get('Quarter', '')],
            ["ACTIVITY CATEGORY:", self.event_data.get('Activity Lead By', '')],
            ["PROGRAM TYPE:", f"Level {self.event_data.get('Event Level', '')} - {self.event_data.get('Program Type', '')}"],
            ["PROGRAM NAME:", self.event_data.get('Program Name', '')],
            ["PROGRAM THEME:", self.event_data.get('Program Theme', '')],
            ["DURATION:", f"{self.event_data.get('Duration (Hrs)', '')} Hours"],
            ["DATE:", f"{self.event_data.get('Start Date', '')} to {self.event_data.get('End Date', '')}"],
            ["PARTICIPANTS:", f"Students: {self.event_data.get('Student Participants', '')} | Faculty: {self.event_data.get('Faculty Participants', '')}"],
            ["EXPENDITURE:", f"Rs. {self.event_data.get('Expenditure Amount', '')}"],
            ["MODE OF DELIVERY:", self.event_data.get('Mode of Delivery', '')],
            ["SOCIAL MEDIA:", self.event_data.get('Video URL', 'N/A')],
        ]

        table_data = [[Paragraph(f"<b>{r[0]}</b>", self.styles['TblLabel']),
                       Paragraph(str(r[1]), self.styles['TblValue'])] for r in data]

        t = Table(table_data, colWidths=[1.8*inch, 5.2*inch])
        t.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 0.5, colors.black),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('LEFTPADDING', (0,0), (-1,-1), 6),
            ('RIGHTPADDING', (0,0), (-1,-1), 6),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ]))
        elements.append(t)
        return elements

    def _objectives(self):
        """Objectives and benefits"""
        elements = []
        elements.append(Paragraph("OBJECTIVE:", self.styles['SecHead']))
        elements.append(Spacer(1, 0.1*inch))
        elements.append(Paragraph(self.event_data.get('Objective', 'N/A'), self.styles['Body']))
        elements.append(Spacer(1, 0.3*inch))
        elements.append(Paragraph("BENEFITS:", self.styles['SecHead']))
        elements.append(Spacer(1, 0.1*inch))
        elements.append(Paragraph(self.event_data.get('Benefits', 'N/A'), self.styles['Body']))
        return elements

    def _brief_report(self):
        """Brief report section"""
        elements = []
        elements.append(Paragraph("EVENT REPORT SUMMARY", self.styles['SecHead']))
        elements.append(Spacer(1, 0.1*inch))
        report = self.event_data.get('Brief Report', 'No report provided.')
        for para in report.split('\n\n'):
            if para.strip():
                elements.append(Paragraph(para.strip(), self.styles['Body']))
        return elements

    def _signatures(self):
        """Signature section"""
        elements = []
        elements.append(Paragraph("AUTHORIZATION", self.styles['SecHead']))
        elements.append(Spacer(1, 2*inch))

        sig = Table([
            [Paragraph("<b>Event Coordinator</b>", self.styles['TblLabel']),
             Paragraph("<b>IIC President</b>", self.styles['TblLabel'])]
        ], colWidths=[3.5*inch, 3.5*inch])
        sig.setStyle(TableStyle([
            ('ALIGN', (0,0), (0,0), 'LEFT'),
            ('ALIGN', (1,0), (1,0), 'RIGHT'),
        ]))
        elements.append(sig)
        return elements

    def _download_file_safely(self, file_id):
        """Download file from Drive with error handling"""
        if not self.drive_manager:
            return None, "No drive manager"

        if not file_id or file_id == 'null' or file_id == '' or len(str(file_id).strip()) < 5:
            return None, "Invalid file ID"

        file_id = str(file_id).strip()

        try:
            data = self.drive_manager.download_file(file_id)
            if data and len(data) > 100:
                return data, None
            else:
                error = getattr(self.drive_manager, 'last_download_error', 'Download returned empty')
                return None, error
        except Exception as e:
            return None, str(e)[:100]

    def _is_pdf(self, data):
        """Check if data is a PDF"""
        return data and len(data) >= 5 and data[:5] == b'%PDF-'

    def _is_image(self, data):
        """Check if data is an image (JPEG or PNG)"""
        if not data or len(data) < 8:
            return False
        # JPEG
        if data[:3] == b'\xff\xd8\xff':
            return True
        # PNG
        if data[:8] == b'\x89PNG\r\n\x1a\n':
            return True
        return False

    def _photo_annexures(self):
        """Photo annexures with embedded images"""
        elements = []

        photos = [
            ('Geotag_Photo1_ID', 'Geotagged Photo 1'),
            ('Geotag_Photo2_ID', 'Geotagged Photo 2'),
            ('Geotag_Photo3_ID', 'Geotagged Photo 3'),
            ('Normal_Photo1_ID', 'Event Photo 1'),
            ('Normal_Photo2_ID', 'Event Photo 2'),
            ('Normal_Photo3_ID', 'Event Photo 3'),
        ]

        for field, title in photos:
            file_id = self.event_data.get(field, '')
            if file_id and file_id != 'null' and file_id != '':
                elements.extend(self._header())
                elements.append(Paragraph(f"ANNEXURE: {title}", self.styles['SecHead']))
                elements.append(Spacer(1, 0.3*inch))

                img_embedded = False
                if self.drive_manager:
                    try:
                        photo_bytes, error = self._download_file_safely(file_id)
                        if photo_bytes:
                            img = Image(BytesIO(photo_bytes), width=5*inch, height=4*inch)
                            img.hAlign = 'CENTER'
                            elements.append(img)
                            img_embedded = True
                            self.merge_status.append(f"Photo {title}: Embedded successfully")
                        else:
                            self.merge_status.append(f"Photo {title}: Failed - {error}")
                    except Exception as e:
                        self.merge_status.append(f"Photo {title}: Error - {str(e)[:50]}")

                if not img_embedded:
                    elements.append(Paragraph(f"<i>Photo could not be embedded</i>", self.styles['Body']))

                elements.append(PageBreak())

        return elements

    def _create_document_title_page(self, title):
        """Create a title page for a document annexure"""
        title_buffer = BytesIO()
        doc = SimpleDocTemplate(title_buffer, pagesize=A4,
            rightMargin=0.5*inch, leftMargin=0.5*inch,
            topMargin=0.3*inch, bottomMargin=0.6*inch)

        story = []
        story.extend(self._header())
        story.append(Spacer(1, 1.5*inch))
        story.append(Paragraph(f"ANNEXURE", self.styles['SecHead']))
        story.append(Spacer(1, 0.3*inch))
        story.append(Paragraph(f"<b>{title}</b>", self.styles['DocTitle']))
        story.append(Spacer(1, 0.5*inch))
        story.append(Paragraph(
            f"<i>The {title} document is attached on the following pages.</i>",
            self.styles['Body']
        ))

        doc.build(story)
        title_buffer.seek(0)
        return title_buffer

    def _create_image_as_pdf_page(self, image_bytes, title):
        """Convert an image to a PDF page with header"""
        try:
            img_buffer = BytesIO()
            doc = SimpleDocTemplate(img_buffer, pagesize=A4,
                rightMargin=0.5*inch, leftMargin=0.5*inch,
                topMargin=0.3*inch, bottomMargin=0.6*inch)

            story = []
            story.extend(self._header())
            story.append(Paragraph(f"ANNEXURE: {title}", self.styles['SecHead']))
            story.append(Spacer(1, 0.2*inch))

            try:
                # Try to embed image with proper sizing
                img = Image(BytesIO(image_bytes), width=6*inch, height=7*inch)
                img.hAlign = 'CENTER'
                story.append(img)
            except Exception as e:
                story.append(Paragraph(f"<i>Image could not be embedded: {str(e)[:50]}</i>", self.styles['Body']))

            doc.build(story)
            img_buffer.seek(0)
            return img_buffer
        except Exception as e:
            self.merge_status.append(f"Image conversion error: {str(e)[:50]}")
            return None

    def _merge_uploaded_documents(self, main_pdf_buffer):
        """Merge uploaded PDF/image documents into the final report"""
        if not PDF_MERGE_AVAILABLE:
            self.merge_status.append("ERROR: PyPDF2 not available")
            return None

        try:
            main_pdf_buffer.seek(0)
            writer = PdfWriter()

            # Add all pages from main report
            main_reader = PdfReader(main_pdf_buffer)
            main_pages = len(main_reader.pages)
            self.merge_status.append(f"Main report has {main_pages} pages")

            for page in main_reader.pages:
                writer.add_page(page)

            # Documents to merge
            documents = [
                ('Attendance_Report_ID', 'Attendance Report'),
                ('Feedback_Analysis_ID', 'Feedback Analysis Report'),
                ('Event_Agenda_ID', 'Event Agenda'),
                ('Chief_Guest_Biodata_ID', 'Chief Guest Biodata'),
                ('KPI_Report_ID', 'KPI Report'),
            ]

            merged_count = 0

            for field, title in documents:
                file_id = self.event_data.get(field, '')

                # Skip if no file ID
                if not file_id or file_id == 'null' or file_id == '' or len(str(file_id).strip()) < 5:
                    self.merge_status.append(f"{title}: SKIPPED (no file)")
                    continue

                file_id = str(file_id).strip()
                self.merge_status.append(f"{title}: Downloading ID={file_id[:30]}...")

                # Download the file
                doc_bytes, error = self._download_file_safely(file_id)

                if not doc_bytes:
                    self.merge_status.append(f"{title}: DOWNLOAD FAILED - {error}")
                    continue

                self.merge_status.append(f"{title}: Downloaded {len(doc_bytes)} bytes")

                # Process based on file type
                if self._is_pdf(doc_bytes):
                    # It's a PDF - add title page then merge pages
                    try:
                        # Create and add title page
                        title_pdf = self._create_document_title_page(title)
                        title_reader = PdfReader(title_pdf)
                        for page in title_reader.pages:
                            writer.add_page(page)

                        # Add document pages
                        doc_reader = PdfReader(BytesIO(doc_bytes))
                        doc_pages = len(doc_reader.pages)

                        if doc_pages > 0:
                            for page in doc_reader.pages:
                                writer.add_page(page)
                            merged_count += 1
                            self.merge_status.append(f"{title}: MERGED ({doc_pages} pages)")
                        else:
                            self.merge_status.append(f"{title}: FAILED - PDF has 0 pages")
                    except Exception as e:
                        self.merge_status.append(f"{title}: PDF ERROR - {str(e)[:50]}")

                elif self._is_image(doc_bytes):
                    # It's an image - convert to PDF page
                    try:
                        img_pdf = self._create_image_as_pdf_page(doc_bytes, title)
                        if img_pdf:
                            img_reader = PdfReader(img_pdf)
                            for page in img_reader.pages:
                                writer.add_page(page)
                            merged_count += 1
                            self.merge_status.append(f"{title}: MERGED as image (1 page)")
                        else:
                            self.merge_status.append(f"{title}: FAILED - Image conversion failed")
                    except Exception as e:
                        self.merge_status.append(f"{title}: IMAGE ERROR - {str(e)[:50]}")

                else:
                    # Unknown format - try as PDF anyway
                    self.merge_status.append(f"{title}: Unknown format, trying as PDF...")
                    try:
                        title_pdf = self._create_document_title_page(title)
                        title_reader = PdfReader(title_pdf)
                        for page in title_reader.pages:
                            writer.add_page(page)

                        doc_reader = PdfReader(BytesIO(doc_bytes))
                        doc_pages = len(doc_reader.pages)

                        if doc_pages > 0:
                            for page in doc_reader.pages:
                                writer.add_page(page)
                            merged_count += 1
                            self.merge_status.append(f"{title}: MERGED ({doc_pages} pages)")
                        else:
                            self.merge_status.append(f"{title}: FAILED - Invalid format")
                    except Exception as e:
                        self.merge_status.append(f"{title}: PARSE ERROR - {str(e)[:50]}")

            total_pages = len(writer.pages)
            self.merge_status.append(f"TOTAL: {merged_count} documents merged, {total_pages} total pages")

            # Write final PDF
            output = BytesIO()
            writer.write(output)
            output.seek(0)
            return output

        except Exception as e:
            self.merge_status.append(f"MERGE ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
