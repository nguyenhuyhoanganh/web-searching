#!/bin/bash
# Setup cho skill web-research. Chạy 1 lần: bash setup.sh
set -e

SKILL_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== web-research skill setup ==="
if ! command -v python3 &> /dev/null; then
    echo "ERROR: chưa có Python 3. Cài Python 3.10+ trước."
    exit 1
fi
echo "Python: $(python3 --version)"

VENV_DIR="$SKILL_DIR/.venv"
[ -d "$VENV_DIR" ] || python3 -m venv "$VENV_DIR"

# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"
pip install --quiet --upgrade pip
pip install --quiet -r "$SKILL_DIR/requirements.txt"

echo ""
echo "Xong. Interpreter: $VENV_DIR/bin/python"
echo "Test:"
echo "  $VENV_DIR/bin/python $SKILL_DIR/scripts/web_search.py \"python 3.13 release date\" -n 3"
echo "  $VENV_DIR/bin/python $SKILL_DIR/scripts/web_read.py \"https://example.com\""
