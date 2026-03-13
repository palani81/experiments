#!/bin/bash
# Claude Code Hook: SessionStart event
# Triggered when a new Claude Code session begins.

TRACKER_URL="${TRACKER_URL:-http://localhost:8420}"
TRACKER_TOKEN="${TRACKER_TOKEN:-changeme}"

HOOK_DATA=$(cat)

SESSION_ID=$(echo "$HOOK_DATA" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('session_id', d.get('sessionId', '')))" 2>/dev/null)
PROJECT_PATH=$(echo "$HOOK_DATA" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('cwd', d.get('project_path', '')))" 2>/dev/null)

curl -s -X POST "${TRACKER_URL}/hooks/session-start" \
  -H "Content-Type: application/json" \
  -d "{
    \"event_type\": \"session_start\",
    \"session_id\": \"${SESSION_ID}\",
    \"project_path\": \"${PROJECT_PATH}\",
    \"payload\": {}
  }" > /dev/null 2>&1 &
