import gzip
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(HERE)
for p in (SKILL_DIR, os.path.join(SKILL_DIR, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

import web_map  # noqa: E402


class TestSitemapDiscovery(unittest.TestCase):
    def test_sitemaps_from_robots(self):
        text = (
            "User-agent: *\nDisallow: /private\n"
            "Sitemap: https://x.test/sitemap.xml\n"
            "sitemap: https://x.test/news.xml.gz\n"
        )
        out = web_map._sitemaps_from_robots(text)
        self.assertIn("https://x.test/sitemap.xml", out)
        self.assertIn("https://x.test/news.xml.gz", out)

    def test_sitemaps_from_robots_empty(self):
        self.assertEqual(web_map._sitemaps_from_robots("User-agent: *\nDisallow: /"), [])

    def test_decode_sitemap_plain(self):
        raw = b"<urlset><loc>https://x.test/a</loc></urlset>"
        self.assertIn("https://x.test/a", web_map._decode_sitemap(raw, "https://x.test/sitemap.xml"))

    def test_decode_sitemap_gz(self):
        raw = b"<urlset><loc>https://x.test/a</loc></urlset>"
        gz = gzip.compress(raw)
        self.assertIn("https://x.test/a", web_map._decode_sitemap(gz, "https://x.test/s.xml.gz"))


if __name__ == "__main__":
    unittest.main()
