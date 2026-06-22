#!/bin/bash
# Setup the MCP server for Cline
# Run: bash setup_mcp.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== MCP server setup ==="

if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 not found."
    exit 1
fi

VENV_DIR="$SCRIPT_DIR/.venv"
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

echo "Installing dependencies..."
source "$VENV_DIR/bin/activate"
pip install --quiet --upgrade pip
pip install --quiet -r "$SCRIPT_DIR/mcp-server/requirements.txt"

PYTHON_PATH="$VENV_DIR/bin/python"
SERVER_PATH="$SCRIPT_DIR/mcp-server/server.py"

echo ""
echo "=== Setup complete ==="
echo ""
echo "To configure Cline, add this to your MCP settings:"
echo ""
cat << JSONEOF
{
    "mcpServers": {
        "web-skills": {
            "command": "$PYTHON_PATH",
            "args": ["$SERVER_PATH"],
            "disabled": false
        }
    }
}
JSONEOF
echo ""
echo "The Cline MCP settings file is usually at:"
echo "  - VS Code: Ctrl+Shift+P -> 'Cline: MCP Settings'"
echo "  - Or: ~/.config/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json"
echo ""
echo "Test the MCP server:"
echo "  $PYTHON_PATH $SERVER_PATH"
