import importlib.util
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(HERE)
if SKILL_DIR not in sys.path:
    sys.path.insert(0, SKILL_DIR)

from lib import extract  # noqa: E402

HAS_BS4 = importlib.util.find_spec("bs4") is not None
HAS_TRAFILATURA = importlib.util.find_spec("trafilatura") is not None

# A document large enough to pass trafilatura's minimum-extraction thresholds.
ARTICLE = "<html><head><title>My Title</title><meta name='author' content='Jane Doe'></head><body><article><h1>Main Heading</h1>" + "".join(
    f"<h2>Section {i}</h2><p>Paragraph {i} with enough words and a "
    f"<a href='https://example.com/s{i}'>link</a> to pass the minimum extraction "
    f"thresholds in trafilatura nicely today.</p>" for i in range(1, 5)
) + "</article></body></html>"

SAMPLE = """
<html><head><title>Hello Title</title></head>
<body>
  <nav>menu</nav>
  <article><h1>Heading</h1><p>First paragraph.</p>
  <a href="/docs">Docs</a><a href="https://x.test/page">External</a></article>
  <footer>footer</footer>
</body></html>
"""


class TestTruncate(unittest.TestCase):
    def test_truncate_marks_cut(self):
        out, cut = extract.truncate("abcdef", 3)
        self.assertTrue(cut)
        self.assertTrue(out.startswith("abc"))

    def test_truncate_noop_when_short(self):
        out, cut = extract.truncate("abc", 10)
        self.assertFalse(cut)
        self.assertEqual(out, "abc")


@unittest.skipUnless(HAS_BS4, "beautifulsoup4 not installed")
class TestLinksAndText(unittest.TestCase):
    def test_extract_links_absolutizes(self):
        links = extract.extract_links(SAMPLE, "https://x.test/")
        urls = [l["url"] for l in links]
        self.assertIn("https://x.test/docs", urls)
        self.assertIn("https://x.test/page", urls)

    def test_to_document_text_drops_nav_footer(self):
        doc = extract.to_document(SAMPLE, "https://x.test/", fmt="text")
        self.assertIn("First paragraph", doc["content"])
        self.assertNotIn("menu", doc["content"])
        self.assertEqual(doc["title"], "Hello Title")


@unittest.skipUnless(HAS_TRAFILATURA, "trafilatura not installed")
class TestMarkdown(unittest.TestCase):
    def test_markdown_has_structure_and_metadata(self):
        doc = extract.to_document(ARTICLE, "https://x.test/post", fmt="markdown")
        self.assertEqual(doc["method"], "trafilatura")
        self.assertIn("# Main Heading", doc["content"])
        self.assertIn("[link](https://example.com/s1)", doc["content"])
        self.assertEqual(doc["author"], "Jane Doe")
        self.assertTrue(doc["title"])


class TestStripBase64Images(unittest.TestCase):
    def test_replaces_base64_image(self):
        md = "Before ![pic](data:image/png;base64,AAAABBBBCCCCDDDD) after"
        out = extract.strip_base64_images(md)
        self.assertNotIn("base64,", out)
        self.assertIn("<base64-image-removed>", out)
        self.assertIn("Before", out)
        self.assertIn("after", out)

    def test_keeps_normal_images(self):
        md = "![pic](https://x.test/a.png)"
        self.assertEqual(extract.strip_base64_images(md), md)


@unittest.skipUnless(HAS_BS4, "beautifulsoup4 not installed")
class TestNoiseRemoval(unittest.TestCase):
    def test_removes_cookie_and_ad_blocks(self):
        html = ("<html><body>"
                "<div class='cookie-banner'>Accept all cookies</div>"
                "<p>Real article content that is sufficiently long to keep.</p>"
                "<div class='ad'>Buy now advertisement</div>"
                "</body></html>")
        doc = extract.to_document(html, "https://x.test/", fmt="text")
        self.assertIn("Real article content", doc["content"])
        self.assertNotIn("Accept all cookies", doc["content"])
        self.assertNotIn("Buy now advertisement", doc["content"])


@unittest.skipUnless(HAS_BS4, "beautifulsoup4 not installed")
class TestMetadata(unittest.TestCase):
    def test_extract_metadata_reads_og_article_keywords_lang(self):
        html = ("<html lang='en'><head><title>T</title>"
                "<meta name='description' content='Desc here'>"
                "<meta property='og:site_name' content='ACME'>"
                "<meta property='article:published_time' content='2024-01-02'>"
                "<meta name='keywords' content='a, b, c'></head><body><p>x</p></body></html>")
        m = extract.extract_metadata(html)
        self.assertEqual(m["description"], "Desc here")
        self.assertEqual(m["sitename"], "ACME")
        self.assertEqual(m["date"], "2024-01-02")
        self.assertEqual(m["keywords"], "a, b, c")
        self.assertEqual(m["language"], "en")

    def test_to_document_fills_metadata_in_text_path(self):
        html = ("<html lang='fr'><head><title>T</title>"
                "<meta property='og:site_name' content='SiteX'></head>"
                "<body><p>Some sufficiently long body content here to keep.</p></body></html>")
        doc = extract.to_document(html, "https://x.test/", fmt="text")
        self.assertEqual(doc["sitename"], "SiteX")
        self.assertEqual(doc["language"], "fr")


@unittest.skipUnless(HAS_BS4, "beautifulsoup4 not installed")
class TestJsonLd(unittest.TestCase):
    def test_extracts_jsonld_blocks(self):
        html = ('<html><head>'
                '<script type="application/ld+json">{"@type":"Article","headline":"Hello"}</script>'
                '<script type="application/ld+json">[{"@type":"Person","name":"A"}]</script>'
                '</head><body><p>x</p></body></html>')
        blocks = extract.extract_jsonld(html)
        self.assertEqual(len(blocks), 2)
        types = {b.get("@type") for b in blocks}
        self.assertEqual(types, {"Article", "Person"})

    def test_ignores_invalid_jsonld(self):
        html = '<script type="application/ld+json">not json {</script>'
        self.assertEqual(extract.extract_jsonld(html), [])


if __name__ == "__main__":
    unittest.main()
