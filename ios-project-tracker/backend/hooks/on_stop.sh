#!/bin/bash
# Claude Code Hook: Stop
# Fires when Claude stops and needs user input.
# Reads JSON from stdin, forwards to tracker backend.

TRACKER_URL="${TRACKER_URL:-http://localhost:8420}"
HOOK_LOG="/tmp/claude-tracker-hooks.log"

log() { echo "$(date '+%H:%M:%S') [stop] $1" >> "$HOOK_LOG"; }

HOOK_DATA=$(cat)
log "Hook fired. Raw data: ${HOOK_DATA:0:200}"

SESSION_ID=$(echo "$HOOK_DATA" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('session_id',''))" 2>/dev/null)
PROJECT_PATH=$(echo "$HOOK_DATA" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('cwd',''))" 2>/dev/null)

log "Parsed: session=$SESSION_ID project=$PROJECT_PATH"

if [ -n "$SESSION_ID" ]; then
  RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${TRACKER_URL}/hooks/stop" \
    -H "Content-Type: application/json" \
    -d "{\"event_type\":\"stop\",\"session_id\":\"${SESSION_ID}\",\"project_path\":\"${PROJECT_PATH}\",\"payload\":{}}" \
    2>&1)
  HTTP_CODE=$(echo "$RESPONSE" | tail -1)
  log "POST ${TRACKER_URL}/hooks/stop -> HTTP $HTTP_CODE"
else
  log "ERROR: No session_id found in hook data"
fi

exit 0
