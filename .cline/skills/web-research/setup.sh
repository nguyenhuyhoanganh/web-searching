#!/bin/bash
# Setup for the web-research skill. Run once: bash setup.sh
set -e

SKILL_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== web-research skill setup ==="

# Detect Python command
PYTHON_CMD=""
for cmd in python3 python py; do
    if command -v "$cmd" &> /dev/null; then
        version=$("$cmd" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null)
        if [ -n "$version" ]; then
            major=$("$cmd" -c "import sys; print(sys.version_info.major)" 2>/dev/null)
            minor=$("$cmd" -c "import sys; print(sys.version_info.minor)" 2>/dev/null)
            if [ "$major" -ge 3 ] && [ "$minor" -ge 10 ]; then
                PYTHON_CMD="$cmd"
                echo "Python command: $PYTHON_CMD (version $version)"
                break
            else
                echo "Skipping $cmd (version $version < 3.10)"
            fi
        fi
    fi
done

if [ -z "$PYTHON_CMD" ]; then
    echo "ERROR: No suitable Python found (need 3.10+)."
    echo "Tried: python3, python, py"
    exit 1
fi

VENV_DIR="$SKILL_DIR/.venv"
[ -d "$VENV_DIR" ] || "$PYTHON_CMD" -m venv "$VENV_DIR"

# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"
pip install --quiet --upgrade pip
pip install --quiet -r "$SKILL_DIR/requirements.txt"

echo ""
echo "=== Setup complete ==="
echo ""
echo "Interpreter: $VENV_DIR/bin/python"
echo "Test:"
echo "  $VENV_DIR/bin/python $SKILL_DIR/scripts/web_search.py \"python 3.13 release date\" -n 3"
echo "  $VENV_DIR/bin/python $SKILL_DIR/scripts/web_read.py \"https://example.com\""
