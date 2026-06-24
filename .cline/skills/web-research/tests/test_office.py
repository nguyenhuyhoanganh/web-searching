import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(HERE)
if SKILL_DIR not in sys.path:
    sys.path.insert(0, SKILL_DIR)

from lib import office  # noqa: E402

DOCX_CT = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
XLSX_CT = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


class TestOfficeDetect(unittest.TestCase):
    def test_docx_by_extension(self):
        self.assertEqual(office.looks_like_office("https://x.test/f.docx", "", b""), "docx")

    def test_xlsx_by_extension(self):
        self.assertEqual(office.looks_like_office("https://x.test/f.xlsx", "", b""), "xlsx")

    def test_docx_by_content_type(self):
        self.assertEqual(office.looks_like_office("https://x.test/dl", DOCX_CT, b""), "docx")

    def test_xlsx_by_content_type(self):
        self.assertEqual(office.looks_like_office("https://x.test/dl", XLSX_CT, b""), "xlsx")

    def test_extension_ignores_query(self):
        self.assertEqual(office.looks_like_office("https://x.test/f.docx?v=1", "", b""), "docx")

    def test_html_is_none(self):
        self.assertIsNone(office.looks_like_office("https://x.test/", "text/html", b"<html>"))


if __name__ == "__main__":
    unittest.main()
