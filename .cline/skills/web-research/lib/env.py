"""Environment helpers: dependency groups, dependency checks, skill-dir discovery."""
import importlib.util
import os
import sys

SKILL_NAME = "web-research"

# group -> list of (import_name, pip_package_name)
DEP_GROUPS = {
    "core":    [("requests", "requests"), ("bs4", "beautifulsoup4"), ("lxml", "lxml")],
    "search":  [("ddgs", "ddgs")],
    "extract": [("trafilatura", "trafilatura"), ("markdownify", "markdownify")],
    "render":  [("playwright", "playwright")],
    "pdf":     [("pypdf", "pypdf")],
    "office":  [("mammoth", "mammoth"), ("openpyxl", "openpyxl")],
    "impersonate": [("curl_cffi", "curl_cffi")],
}

# Project- and home-level roots Cline scans for skills (incl. cross-agent .agent).
_PROJECT_ROOTS = (".cline", ".clinerules", ".claude", ".agent")
_HOME_ROOTS = (".cline", ".agent", ".claude")


def _candidate_dirs():
    cwd = os.getcwd()
    home = os.path.expanduser("~")
    dirs = [os.path.join(cwd, r, "skills", SKILL_NAME) for r in _PROJECT_ROOTS]
    dirs += [os.path.join(home, r, "skills", SKILL_NAME) for r in _HOME_ROOTS]
    return dirs


def find_skill_dir():
    """Return the absolute path of the installed skill dir, or None if not found."""
    for d in _candidate_dirs():
        if os.path.isdir(d):
            return d
    return None


def _is_installed(import_name):
    return importlib.util.find_spec(import_name) is not None


def check_deps():
    """Return {group: {pip_name: installed_bool}} for every group."""
    return {
        group: {pip: _is_installed(imp) for imp, pip in members}
        for group, members in DEP_GROUPS.items()
    }


def missing_pip_packages(groups=None):
    """Return the pip package names that are not importable for the given groups."""
    groups = groups or list(DEP_GROUPS)
    missing = []
    for group in groups:
        for imp, pip in DEP_GROUPS[group]:
            if not _is_installed(imp):
                missing.append(pip)
    return missing


def force_utf8():
    """Emit UTF-8 on stdout/stderr.

    On Windows, when output is piped (as agents capture it) Python encodes with the ANSI code page
    (e.g. cp1252/cp1258), so printing non-ASCII web content raises UnicodeEncodeError. Reconfiguring
    to UTF-8 prevents that. No-op where the streams cannot be reconfigured.
    """
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
