#!/bin/bash
# Setup the MCP server for Cline
# Run: bash setup_mcp.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== MCP server setup ==="

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

VENV_DIR="$SCRIPT_DIR/.venv"
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    "$PYTHON_CMD" -m venv "$VENV_DIR"
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
