#!/bin/bash
# Setup cho Web Search & Read Skill (KHÔNG cần MCP)
# Chạy 1 lần: bash skills/setup.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "=== Web Skill Setup (no MCP) ==="

if ! command -v python3 &> /dev/null; then
    echo "ERROR: Chưa có Python 3. Cài Python 3.10+ trước."
    exit 1
fi

echo "Python: $(python3 --version)"

VENV_DIR="$ROOT_DIR/.venv"
if [ ! -d "$VENV_DIR" ]; then
    echo "Tạo virtual environment tại $VENV_DIR ..."
    python3 -m venv "$VENV_DIR"
fi

echo "Cài dependencies..."
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"
pip install --quiet --upgrade pip
pip install --quiet -r "$SCRIPT_DIR/requirements.txt"

echo ""
echo "=== Xong ==="
echo ""
echo "Python interpreter cho skill:"
echo "  $VENV_DIR/bin/python"
echo ""
echo "Test thử:"
echo "  $VENV_DIR/bin/python $SCRIPT_DIR/web_search.py \"python 3.13 release date\" -n 3"
echo "  $VENV_DIR/bin/python $SCRIPT_DIR/web_read.py \"https://example.com\""
