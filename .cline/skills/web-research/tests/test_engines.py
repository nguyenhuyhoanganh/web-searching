import os
import sys
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(HERE)
if SKILL_DIR not in sys.path:
    sys.path.insert(0, SKILL_DIR)

from lib import engines  # noqa: E402


class TestImpersonate(unittest.TestCase):
    def test_raises_when_curl_cffi_missing(self):
        with mock.patch.object(engines, "_curl_cffi_installed", return_value=False):
            with self.assertRaises(engines.ImpersonateUnavailable):
                engines.fetch_html("https://example.com", impersonate=True)

    def test_uses_curl_when_requested_and_available(self):
        sentinel = {"engine_used": "curl_cffi", "html": "ok"}
        with mock.patch.object(engines, "_curl_cffi_installed", return_value=True), \
             mock.patch.object(engines, "_fetch_with_curl", return_value=sentinel) as fake:
            result = engines.fetch_html("https://example.com", impersonate=True)
        fake.assert_called_once()
        self.assertEqual(result["engine_used"], "curl_cffi")


if __name__ == "__main__":
    unittest.main()
