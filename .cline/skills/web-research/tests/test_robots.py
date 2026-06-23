import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(HERE)
if SKILL_DIR not in sys.path:
    sys.path.insert(0, SKILL_DIR)

from lib import robots  # noqa: E402


class TestRobots(unittest.TestCase):
    def test_disallow_blocks_path(self):
        allowed = robots.make_checker("User-agent: *\nDisallow: /private\n")
        self.assertFalse(allowed("https://x.test/private/page"))
        self.assertTrue(allowed("https://x.test/public/page"))

    def test_empty_robots_allows_all(self):
        allowed = robots.make_checker("")
        self.assertTrue(allowed("https://x.test/anything"))

    def test_allow_all_when_only_comments(self):
        allowed = robots.make_checker("# just a comment\n")
        self.assertTrue(allowed("https://x.test/x"))


if __name__ == "__main__":
    unittest.main()
