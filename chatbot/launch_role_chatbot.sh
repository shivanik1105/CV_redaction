#!/bin/bash
# Bash script to launch role chatbots
# Usage: ./launch_role_chatbot.sh senior_python_developer --share

ROLE=$1
SHARE_FLAG=""
PORT=7860

if [ -z "$ROLE" ]; then
    echo "❌ Error: Role name required"
    echo ""
    echo "Usage: ./launch_role_chatbot.sh <role_name> [--share] [--port PORT]"
    echo ""
    echo "Example: ./launch_role_chatbot.sh senior_python_developer --share"
    exit 1
fi

# Parse additional arguments
shift
while [[ $# -gt 0 ]]; do
    case $1 in
        --share)
            SHARE_FLAG="--share"
            shift
            ;;
        --port)
            PORT="$2"
            shift 2
            ;;
        *)
            shift
            ;;
    esac
done

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PYTHON_SCRIPT="$SCRIPT_DIR/role_chatbot_template.py"
ROLE_FOLDER="$SCRIPT_DIR/roles/$ROLE"

if [ ! -f "$PYTHON_SCRIPT" ]; then
    echo "❌ Error: role_chatbot_template.py not found"
    exit 1
fi

if [ ! -d "$ROLE_FOLDER" ]; then
    echo "❌ Error: Role folder not found: $ROLE_FOLDER"
    echo ""
    echo "Available roles:"
    ls -1 "$SCRIPT_DIR/roles" 2>/dev/null | sed 's/^/  - /'
    echo ""
    echo "Create a new role with:"
    echo "  python chatbot/create_role_chatbot.py --name \"Your Role Name\""
    exit 1
fi

echo "🚀 Launching Role Chatbot: $ROLE"
echo "📁 Role folder: $ROLE_FOLDER"
echo "🌐 Port: $PORT"

if [ -n "$SHARE_FLAG" ]; then
    echo "🔗 Creating shareable link..."
fi

echo ""

python "$PYTHON_SCRIPT" --role "$ROLE" --port "$PORT" $SHARE_FLAG
