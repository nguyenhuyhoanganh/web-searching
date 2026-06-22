#!/bin/bash
# Setup script for the CLI web skills
# Run: bash skills/setup.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== Web skills setup ==="

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

# Create virtual environment
VENV_DIR="$SCRIPT_DIR/../.venv"
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    "$PYTHON_CMD" -m venv "$VENV_DIR"
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
echo "Or use the venv interpreter directly:"
echo "  $VENV_DIR/bin/python $SCRIPT_DIR/web_search.py \"your query\""
echo ""
echo "MCP server (for Cline):"
echo "  pip install -r $SCRIPT_DIR/../mcp-server/requirements.txt"
echo "  python $SCRIPT_DIR/../mcp-server/server.py"
