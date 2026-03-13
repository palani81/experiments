#!/bin/bash
# Install Claude Code hooks for the tracker.
# This script adds tracker hooks to ~/.claude/settings.json
# without overwriting existing hooks.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SETTINGS_FILE="$HOME/.claude/settings.json"
TRACKER_HOOKS_DIR="$HOME/.claude-tracker/hooks"

echo "Installing Claude Code Tracker hooks..."

# Create hooks directory
mkdir -p "$TRACKER_HOOKS_DIR"

# Copy hook scripts
cp "$SCRIPT_DIR/on_stop.sh" "$TRACKER_HOOKS_DIR/"
cp "$SCRIPT_DIR/on_session_start.sh" "$TRACKER_HOOKS_DIR/"
cp "$SCRIPT_DIR/on_session_end.sh" "$TRACKER_HOOKS_DIR/"
cp "$SCRIPT_DIR/on_notification.sh" "$TRACKER_HOOKS_DIR/"
chmod +x "$TRACKER_HOOKS_DIR"/*.sh

echo "Hook scripts installed to $TRACKER_HOOKS_DIR"

# Create settings.json if it doesn't exist
mkdir -p "$(dirname "$SETTINGS_FILE")"
if [ ! -f "$SETTINGS_FILE" ]; then
    echo '{}' > "$SETTINGS_FILE"
fi

# Merge hooks into settings.json using Python
python3 << 'PYEOF'
import json
import os

settings_path = os.path.expanduser("~/.claude/settings.json")
hooks_dir = os.path.expanduser("~/.claude-tracker/hooks")

with open(settings_path) as f:
    settings = json.load(f)

if "hooks" not in settings:
    settings["hooks"] = {}

hook_configs = {
    "Stop": f"{hooks_dir}/on_stop.sh",
    "SessionStart": f"{hooks_dir}/on_session_start.sh",
    "SessionEnd": f"{hooks_dir}/on_session_end.sh",
    "Notification": f"{hooks_dir}/on_notification.sh",
}

for event, script in hook_configs.items():
    if event not in settings["hooks"]:
        settings["hooks"][event] = []

    # Check if our hook is already installed
    tracker_hook = {"type": "command", "command": script}
    existing = [h for h in settings["hooks"][event] if h.get("command") == script]
    if not existing:
        settings["hooks"][event].append(tracker_hook)
        print(f"  Added {event} hook")
    else:
        print(f"  {event} hook already installed")

with open(settings_path, "w") as f:
    json.dump(settings, f, indent=2)

print(f"\nSettings updated: {settings_path}")
PYEOF

echo ""
echo "Installation complete!"
echo "Restart any active Claude Code sessions for hooks to take effect."
