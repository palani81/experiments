#!/bin/bash
# Claude Code Hook: SessionEnd (command hook fallback)
# Fires when a Claude Code session ends.
# Reads native hook JSON from stdin, forwards to tracker backend.
#
# NOTE: Prefer using HTTP hooks via install_hooks.sh instead.

TRACKER_URL="${TRACKER_URL:-http://localhost:8420}"
HOOK_LOG="/tmp/claude-tracker-hooks.log"

log() { echo "$(date '+%H:%M:%S') [session_end] $1" >> "$HOOK_LOG"; }

HOOK_DATA=$(cat)
log "Hook fired. Raw data: ${HOOK_DATA:0:300}"

SESSION_ID=$(echo "$HOOK_DATA" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('session_id',''))" 2>/dev/null)

log "Parsed: session=$SESSION_ID"

if [ -n "$SESSION_ID" ]; then
  RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${TRACKER_URL}/hooks/session-end" \
    -H "Content-Type: application/json" \
    -d "$HOOK_DATA" \
    2>&1)
  HTTP_CODE=$(echo "$RESPONSE" | tail -1)
  log "POST ${TRACKER_URL}/hooks/session-end -> HTTP $HTTP_CODE"
else
  log "ERROR: No session_id found in hook data"
fi

exit 0
