#!/bin/bash
# Setup script for the CLI web skills
# Run: bash skills/setup.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== Web skills setup ==="

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 not found."
    echo "Please install Python 3.10+ before running this script."
    exit 1
fi

PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "Python version: $PYTHON_VERSION"

# Create virtual environment
VENV_DIR="$SCRIPT_DIR/../.venv"
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

# Activate and install
echo "Installing dependencies..."
source "$VENV_DIR/bin/activate"
pip install --quiet --upgrade pip
pip install --quiet -r "$SCRIPT_DIR/requirements.txt"

echo ""
echo "=== Setup complete ==="
echo ""
echo "CLI usage:"
echo "  source $VENV_DIR/bin/activate"
echo "  python $SCRIPT_DIR/web_search.py \"your query\""
echo "  python $SCRIPT_DIR/web_read.py \"https://example.com\""
echo ""
echo "MCP server (for Cline):"
echo "  pip install -r $SCRIPT_DIR/../mcp-server/requirements.txt"
echo "  python $SCRIPT_DIR/../mcp-server/server.py"
