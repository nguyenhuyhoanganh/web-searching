#!/bin/bash
# Setup MCP Server cho Cline
# Chạy: bash setup_mcp.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== MCP Server Setup ==="

if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 chưa được cài đặt."
    exit 1
fi

VENV_DIR="$SCRIPT_DIR/.venv"
if [ ! -d "$VENV_DIR" ]; then
    echo "Tạo virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

echo "Cài đặt dependencies..."
source "$VENV_DIR/bin/activate"
pip install --quiet --upgrade pip
pip install --quiet -r "$SCRIPT_DIR/mcp-server/requirements.txt"

PYTHON_PATH="$VENV_DIR/bin/python"
SERVER_PATH="$SCRIPT_DIR/mcp-server/server.py"

echo ""
echo "=== Setup hoàn tất ==="
echo ""
echo "Để cấu hình cho Cline, thêm vào MCP settings:"
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
echo "File cấu hình Cline MCP settings thường nằm tại:"
echo "  - VS Code: Ctrl+Shift+P → 'Cline: MCP Settings'"
echo "  - Hoặc: ~/.config/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json"
echo ""
echo "Test MCP server:"
echo "  $PYTHON_PATH $SERVER_PATH"
