#!/bin/bash
# Claude Code Hook: Notification
# Fires when Claude needs attention (permission prompt, idle, etc).
# Reads JSON from stdin, forwards to tracker backend.

TRACKER_URL="${TRACKER_URL:-http://localhost:8420}"

HOOK_DATA=$(cat)

SESSION_ID=$(echo "$HOOK_DATA" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('session_id',''))" 2>/dev/null)
PROJECT_PATH=$(echo "$HOOK_DATA" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('cwd',''))" 2>/dev/null)
MESSAGE=$(echo "$HOOK_DATA" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('message',''))" 2>/dev/null)

if [ -n "$SESSION_ID" ]; then
  curl -s -X POST "${TRACKER_URL}/hooks/notification" \
    -H "Content-Type: application/json" \
    -d "{\"event_type\":\"notification\",\"session_id\":\"${SESSION_ID}\",\"project_path\":\"${PROJECT_PATH}\",\"payload\":{\"message\":\"${MESSAGE}\"}}" \
    > /dev/null 2>&1 &
fi

exit 0
