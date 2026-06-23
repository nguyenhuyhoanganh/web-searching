#!/usr/bin/env python3
"""Print the skill location, Python version, and dependency status with exact install commands.

Run this after locating the skill dir. It self-reports its own directory via __file__, so it works
regardless of the current working directory.
"""
import os
import sys

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if SKILL_DIR not in sys.path:
    sys.path.insert(0, SKILL_DIR)

from lib import env  # noqa: E402

# pip command per group, in the order a user would install them.
GROUP_HINTS = {
    "core": "pip install requests beautifulsoup4 lxml",
    "search": "pip install ddgs",
    "extract": "pip install trafilatura markdownify",
    "render": "pip install playwright   (then: playwright install chromium)",
    "pdf": "pip install pypdf",
}


def main():
    print(f"Skill directory : {SKILL_DIR}")
    print(f"Python          : {sys.version.split()[0]}  (executable: {sys.executable})")
    ok_py = sys.version_info >= (3, 10)
    print(f"Python >= 3.10  : {'yes' if ok_py else 'NO — please use Python 3.10+'}")
    print("")
    status = env.check_deps()
    for group, members in status.items():
        present = [pip for pip, ok in members.items() if ok]
        missing = [pip for pip, ok in members.items() if not ok]
        label = "OK " if not missing else "MISSING"
        print(f"[{label}] {group:8s} present={present or '-'} missing={missing or '-'}")
        if missing:
            print(f"          install:  {GROUP_HINTS[group]}")
    print("")
    print("Note: only the 'core' group is required. Others are optional and used on demand.")


if __name__ == "__main__":
    main()
