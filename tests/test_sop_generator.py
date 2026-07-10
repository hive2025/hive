import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sop_generator import SOPGenerator, create_feedback_form_link, generate_sop_documents_local


class SOPGeneratorTests(unittest.TestCase):
    def test_generate_sop_pdf_creates_bytes(self):
        generator = SOPGenerator({
            "event_title": "ASME Event",
            "event_date": "2026-07-15",
            "venue": "Main Hall",
            "department": "MECH",
            "coordinator_name": "Dr. Ravi",
            "contact_person": "Mr. Kumar",
            "audience_count": "120",
            "objective": "To create awareness on engineering design principles.",
        })
        pdf_bytes = generator.generate_sop_pdf()
        self.assertTrue(len(pdf_bytes) > 1000)

    def test_generate_attendance_pdf_creates_bytes(self):
        generator = SOPGenerator({
            "event_title": "ASME Event",
            "event_date": "2026-07-15",
            "venue": "Main Hall",
            "department": "MECH",
            "coordinator_name": "Dr. Ravi",
            "audience_count": "45",
        })
        pdf_bytes = generator.generate_attendance_pdf()
        self.assertTrue(len(pdf_bytes) > 1000)

    def test_feedback_form_link_returns_fallback_when_no_creds(self):
        link = create_feedback_form_link({"event_title": "ASME Event"})
        self.assertTrue(link.startswith("https"))

    def test_generate_sop_documents_local_returns_sop_and_attendance_payload(self):
        result = generate_sop_documents_local({
            "event_title": "ASME Event",
            "event_date": "2026-07-15",
            "venue": "Main Hall",
        })
        self.assertIn("sop_pdf", result)
        self.assertIn("attendance_pdf", result)
        self.assertNotIn("feedback_pdf", result)
        self.assertTrue(len(result["sop_pdf"]) > 1000)
        self.assertTrue(len(result["attendance_pdf"]) > 1000)


if __name__ == "__main__":
    unittest.main()
