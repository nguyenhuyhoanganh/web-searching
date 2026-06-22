#!/bin/bash
# Setup script cho Web Skills
# Chạy: bash skills/setup.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== Web Skills Setup ==="

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 chưa được cài đặt."
    echo "Vui lòng cài Python 3.10+ trước khi chạy script này."
    exit 1
fi

PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "Python version: $PYTHON_VERSION"

# Create virtual environment
VENV_DIR="$SCRIPT_DIR/../.venv"
if [ ! -d "$VENV_DIR" ]; then
    echo "Tạo virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

# Activate and install
echo "Cài đặt dependencies..."
source "$VENV_DIR/bin/activate"
pip install --quiet --upgrade pip
pip install --quiet -r "$SCRIPT_DIR/requirements.txt"

echo ""
echo "=== Setup hoàn tất ==="
echo ""
echo "Sử dụng CLI:"
echo "  source $VENV_DIR/bin/activate"
echo "  python $SCRIPT_DIR/web_search.py \"your query\""
echo "  python $SCRIPT_DIR/web_read.py \"https://example.com\""
echo ""
echo "Sử dụng MCP Server (cho Cline):"
echo "  pip install -r $SCRIPT_DIR/../mcp-server/requirements.txt"
echo "  python $SCRIPT_DIR/../mcp-server/server.py"
