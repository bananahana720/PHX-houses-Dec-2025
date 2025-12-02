#!/bin/bash
# Claude Code PreToolUse Hook: Auto-activate Python venv on Windows/Git Bash
# Intercepts Bash tool calls and prepends venv activation for Python commands

# Read JSON input from stdin. Use 'jq .' to read exactly one JSON object
# from the stream, which avoids the hanging issue seen with 'cat'.
INPUT=$(jq '.')

# Extract the command from tool_input
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

# Exit if no command found
if [ -z "$COMMAND" ]; then
    echo '{"hookSpecificOutput": {"permissionDecision": "allow"}}'
    exit 0
fi

# Check if command involves Python execution
PYTHON_PATTERN='(^|[[:space:]]|&&|;|\||^)(python|python3|py|pip|pip3|pytest|poetry run)'
if ! echo "$COMMAND" | grep -qE "$PYTHON_PATTERN"; then
    # Not a Python command, allow without modification
    echo '{"hookSpecificOutput": {"permissionDecision": "allow"}}'
    exit 0
fi

# Determine venv path (Git Bash on Windows uses Unix-style paths)
PROJECT_DIR="${CLAUDE_PROJECT_DIR}"
if [ -z "$PROJECT_DIR" ]; then
    # Fallback to current directory if env var not set
    PROJECT_DIR="$(pwd)"
fi

# Check for venv existence (common names)
VENV_PATH=""
for venv_name in venv .venv env .env virtualenv; do
    if [ -d "$PROJECT_DIR/$venv_name/Scripts" ]; then
        VENV_PATH="$PROJECT_DIR/$venv_name"
        break
    fi
done

# If no venv found, allow original command
if [ -z "$VENV_PATH" ]; then
    echo '{"hookSpecificOutput": {"permissionDecision": "allow"}}'
    exit 0
fi

# Construct activation command for Git Bash on Windows
# Git Bash can source the activate script directly
ACTIVATION_CMD="source \"$VENV_PATH/Scripts/activate\""

# Prepend activation to original command
MODIFIED_COMMAND="$ACTIVATION_CMD && $COMMAND"

# Return JSON with updated input
cat <<EOF
{
    "hookSpecificOutput": {
        "permissionDecision": "allow",
        "updatedInput": {
            "command": $(echo "$MODIFIED_COMMAND" | jq -Rs .)
        }
    },
    "suppressOutput": true
}
EOF

exit 0
