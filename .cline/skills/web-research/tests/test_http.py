import os
import sys
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(HERE)
if SKILL_DIR not in sys.path:
    sys.path.insert(0, SKILL_DIR)

from lib import http  # noqa: E402


class TestProxy(unittest.TestCase):
    def setUp(self):
        http.set_proxy(None)

    def tearDown(self):
        http.set_proxy(None)

    def test_override_takes_precedence(self):
        with mock.patch.dict(os.environ, {"HTTPS_PROXY": "http://env:1"}, clear=True):
            http.set_proxy("http://cli:2")
            self.assertEqual(http.current_proxy(), "http://cli:2")

    def test_env_used_when_no_override(self):
        with mock.patch.dict(os.environ, {"WEB_RESEARCH_PROXY": "http://envproxy:8080"}, clear=True):
            self.assertEqual(http.current_proxy(), "http://envproxy:8080")

    def test_no_proxy_returns_none(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertIsNone(http.current_proxy())
            self.assertIsNone(http.playwright_proxy())

    def test_playwright_proxy_with_auth(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            http.set_proxy("http://user:pass@1.2.3.4:8080")
            cfg = http.playwright_proxy()
        self.assertEqual(cfg["server"], "http://1.2.3.4:8080")
        self.assertEqual(cfg["username"], "user")
        self.assertEqual(cfg["password"], "pass")

    def test_playwright_proxy_no_scheme(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            http.set_proxy("1.2.3.4:3128")
            cfg = http.playwright_proxy()
        self.assertEqual(cfg["server"], "http://1.2.3.4:3128")
        self.assertNotIn("username", cfg)


class TestSSRF(unittest.TestCase):
    def setUp(self):
        http.set_allow_local(False)

    def tearDown(self):
        http.set_allow_local(False)

    def test_blocks_loopback(self):
        with self.assertRaises(http.BlockedURLError):
            http.assert_allowed("http://127.0.0.1/x")

    def test_blocks_cloud_metadata_ip(self):
        with self.assertRaises(http.BlockedURLError):
            http.assert_allowed("http://169.254.169.254/latest/meta-data/")

    def test_blocks_private_range(self):
        with self.assertRaises(http.BlockedURLError):
            http.assert_allowed("http://10.0.0.5/")

    def test_public_literal_ip_allowed(self):
        http.assert_allowed("http://8.8.8.8/")  # public, must not raise

    def test_allow_local_override(self):
        http.set_allow_local(True)
        http.assert_allowed("http://127.0.0.1/")  # must not raise when allowed


if __name__ == "__main__":
    unittest.main()
