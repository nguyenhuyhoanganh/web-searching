import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(HERE)
if SKILL_DIR not in sys.path:
    sys.path.insert(0, SKILL_DIR)

from lib import pdf  # noqa: E402


class TestLooksLikePdf(unittest.TestCase):
    def test_by_magic_bytes(self):
        self.assertTrue(pdf.looks_like_pdf("https://x.test/file", "", b"%PDF-1.7\n..."))

    def test_by_content_type(self):
        self.assertTrue(pdf.looks_like_pdf("https://x.test/file", "application/pdf", b""))

    def test_by_url_extension(self):
        self.assertTrue(pdf.looks_like_pdf("https://x.test/report.pdf", "", b""))

    def test_url_extension_ignores_query(self):
        self.assertTrue(pdf.looks_like_pdf("https://x.test/report.pdf?v=2", "", b""))

    def test_html_is_not_pdf(self):
        self.assertFalse(pdf.looks_like_pdf("https://x.test/", "text/html", b"<html>"))


if __name__ == "__main__":
    unittest.main()
