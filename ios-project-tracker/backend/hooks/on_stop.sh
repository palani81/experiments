#!/bin/bash
# Claude Code Hook: Stop (command hook fallback)
# Fires when Claude stops and needs user input.
# Reads native hook JSON from stdin, forwards to tracker backend.
#
# NOTE: Prefer using HTTP hooks via install_hooks.sh instead.
# This script is a fallback for environments where HTTP hooks aren't supported.

TRACKER_URL="${TRACKER_URL:-http://localhost:8420}"
HOOK_LOG="/tmp/claude-tracker-hooks.log"

log() { echo "$(date '+%H:%M:%S') [stop] $1" >> "$HOOK_LOG"; }

HOOK_DATA=$(cat)
log "Hook fired. Raw data: ${HOOK_DATA:0:300}"

SESSION_ID=$(echo "$HOOK_DATA" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('session_id',''))" 2>/dev/null)
PROJECT_PATH=$(echo "$HOOK_DATA" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('cwd',''))" 2>/dev/null)

log "Parsed: session=$SESSION_ID project=$PROJECT_PATH"

if [ -n "$SESSION_ID" ]; then
  # Forward the native hook JSON directly — backend handles both formats
  RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${TRACKER_URL}/hooks/stop" \
    -H "Content-Type: application/json" \
    -d "$HOOK_DATA" \
    2>&1)
  HTTP_CODE=$(echo "$RESPONSE" | tail -1)
  log "POST ${TRACKER_URL}/hooks/stop -> HTTP $HTTP_CODE"
else
  log "ERROR: No session_id found in hook data"
fi

exit 0
