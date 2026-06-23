import os
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(HERE)
if SKILL_DIR not in sys.path:
    sys.path.insert(0, SKILL_DIR)

from lib import env  # noqa: E402


class TestDepGroups(unittest.TestCase):
    def test_core_group_maps_bs4_to_beautifulsoup4(self):
        names = dict(env.DEP_GROUPS["core"])
        self.assertEqual(names["bs4"], "beautifulsoup4")

    def test_missing_pip_packages_returns_pip_names(self):
        with mock.patch.object(env, "_is_installed", return_value=False):
            missing = env.missing_pip_packages(["core"])
        self.assertIn("beautifulsoup4", missing)
        self.assertNotIn("bs4", missing)

    def test_check_deps_reports_all_groups(self):
        result = env.check_deps()
        self.assertEqual(set(result), set(env.DEP_GROUPS))


class TestFindSkillDir(unittest.TestCase):
    def test_finds_project_cline_skills(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = os.path.join(tmp, ".cline", "skills", env.SKILL_NAME)
            os.makedirs(target)
            with mock.patch("os.getcwd", return_value=tmp), \
                 mock.patch("os.path.expanduser", return_value=os.path.join(tmp, "nohome")):
                self.assertEqual(env.find_skill_dir(), target)

    def test_returns_none_when_absent(self):
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch("os.getcwd", return_value=tmp), \
                 mock.patch("os.path.expanduser", return_value=os.path.join(tmp, "nohome")):
                self.assertIsNone(env.find_skill_dir())


class TestForceUtf8(unittest.TestCase):
    def test_unicode_prints_under_legacy_codepage(self):
        # Simulates a Windows ANSI code page (cp1252) with piped (captured) output, where
        # printing non-ASCII would raise UnicodeEncodeError without force_utf8().
        code = (
            f"import sys; sys.path.insert(0, {SKILL_DIR!r});"
            "from lib import env; env.force_utf8();"
            "print('Tiếng Việt 日本語')"
        )
        result = subprocess.run(
            [sys.executable, "-c", code], capture_output=True,
            env=dict(os.environ, PYTHONIOENCODING="cp1252"), text=True, encoding="utf-8",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Tiếng Việt", result.stdout)


if __name__ == "__main__":
    unittest.main()
