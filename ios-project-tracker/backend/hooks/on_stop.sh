#!/bin/bash
# Claude Code Hook: Stop event
# Triggered when Claude stops working and needs user input.
# Reads hook data from stdin and forwards to the tracker backend.

TRACKER_URL="${TRACKER_URL:-http://localhost:8420}"
TRACKER_TOKEN="${TRACKER_TOKEN:-changeme}"

# Read hook data from stdin
HOOK_DATA=$(cat)

# Extract session ID from hook data (Claude passes JSON via stdin)
SESSION_ID=$(echo "$HOOK_DATA" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('session_id', d.get('sessionId', '')))" 2>/dev/null)
PROJECT_PATH=$(echo "$HOOK_DATA" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('cwd', d.get('project_path', '')))" 2>/dev/null)
STOP_REASON=$(echo "$HOOK_DATA" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('stop_hook_active_reason', d.get('reason', 'stopped')))" 2>/dev/null)

curl -s -X POST "${TRACKER_URL}/hooks/stop" \
  -H "Content-Type: application/json" \
  -d "{
    \"event_type\": \"stop\",
    \"session_id\": \"${SESSION_ID}\",
    \"project_path\": \"${PROJECT_PATH}\",
    \"payload\": {\"reason\": \"${STOP_REASON}\", \"raw\": $(echo "$HOOK_DATA" | head -c 2000)}
  }" > /dev/null 2>&1 &
