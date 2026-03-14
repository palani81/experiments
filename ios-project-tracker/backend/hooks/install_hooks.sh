#!/bin/bash
# Install Claude Code hooks for the tracker.
#
# Uses the new hooks format with matchers and HTTP hook type,
# so Claude Code POSTs directly to the tracker backend — no shell scripts needed.
#
# Usage:
#   ./install_hooks.sh                     # defaults to http://localhost:8420
#   TRACKER_URL=http://192.168.1.50:8420 ./install_hooks.sh

set -e

TRACKER_URL="${TRACKER_URL:-http://localhost:8420}"
SETTINGS_FILE="$HOME/.claude/settings.json"

echo "Installing Claude Code Tracker hooks..."
echo "Backend URL: $TRACKER_URL"

# Create settings.json if it doesn't exist
mkdir -p "$(dirname "$SETTINGS_FILE")"
if [ ! -f "$SETTINGS_FILE" ]; then
    echo '{}' > "$SETTINGS_FILE"
fi

# Merge hooks into settings.json using Python
python3 - "$TRACKER_URL" "$SETTINGS_FILE" << 'PYEOF'
import json
import sys

tracker_url = sys.argv[1]
settings_path = sys.argv[2]

with open(settings_path) as f:
    settings = json.load(f)

if "hooks" not in settings:
    settings["hooks"] = {}

# New format: each event has a list of {matcher, hooks} objects.
# HTTP hooks POST the native hook JSON directly to our backend.
hook_configs = {
    "Stop": {
        "url": f"{tracker_url}/hooks/stop",
    },
    "SessionStart": {
        "url": f"{tracker_url}/hooks/session-start",
    },
    "SessionEnd": {
        "url": f"{tracker_url}/hooks/session-end",
    },
    "Notification": {
        "url": f"{tracker_url}/hooks/notification",
    },
    "UserPromptSubmit": {
        "url": f"{tracker_url}/hooks/prompt-submit",
    },
}

for event, config in hook_configs.items():
    http_hook = {
        "type": "http",
        "url": config["url"],
        "timeout": 10,
    }
    hook_entry = {
        "hooks": [http_hook],
    }

    if event not in settings["hooks"]:
        settings["hooks"][event] = []

    # Check if our hook URL is already installed
    already_installed = False
    for entry in settings["hooks"][event]:
        # New format: entry has "hooks" list
        if "hooks" in entry:
            for h in entry["hooks"]:
                if h.get("url", "").startswith(tracker_url):
                    already_installed = True
                    # Update URL in case it changed
                    h["url"] = config["url"]
                    break
        # Old format: entry is a flat hook object
        elif entry.get("command", "").find("claude-tracker") >= 0:
            # Remove old shell-script-based hook
            settings["hooks"][event].remove(entry)
            print(f"  Removed old shell-script hook for {event}")
            break

    if not already_installed:
        settings["hooks"][event].append(hook_entry)
        print(f"  Added {event} hook -> {config['url']}")
    else:
        print(f"  {event} hook already installed (updated URL)")

with open(settings_path, "w") as f:
    json.dump(settings, f, indent=2)

print(f"\nSettings updated: {settings_path}")
PYEOF

echo ""
echo "Installation complete!"
echo ""
echo "Hooks are configured as HTTP hooks — Claude Code will POST"
echo "directly to your tracker backend at $TRACKER_URL."
echo ""
echo "Restart any active Claude Code sessions for hooks to take effect."
