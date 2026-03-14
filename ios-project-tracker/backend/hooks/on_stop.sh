#!/bin/bash
# Claude Code Hook: Stop
# Fires when Claude stops and needs user input.
# Reads JSON from stdin, forwards to tracker backend.

TRACKER_URL="${TRACKER_URL:-http://localhost:8420}"

HOOK_DATA=$(cat)

SESSION_ID=$(echo "$HOOK_DATA" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('session_id',''))" 2>/dev/null)
PROJECT_PATH=$(echo "$HOOK_DATA" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('cwd',''))" 2>/dev/null)

if [ -n "$SESSION_ID" ]; then
  curl -s -X POST "${TRACKER_URL}/hooks/stop" \
    -H "Content-Type: application/json" \
    -d "{\"event_type\":\"stop\",\"session_id\":\"${SESSION_ID}\",\"project_path\":\"${PROJECT_PATH}\",\"payload\":{}}" \
    > /dev/null 2>&1 &
fi

exit 0
