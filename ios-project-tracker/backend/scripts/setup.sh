#!/bin/bash
# Setup script for Claude Code Tracker backend.
# Run this on your Mac mini to install and configure the backend.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"
DATA_DIR="$HOME/.claude-tracker"

echo "=== Claude Code Tracker Setup ==="
echo ""

# Create data directory
mkdir -p "$DATA_DIR"
chmod 700 "$DATA_DIR"

# Create default config if it doesn't exist
if [ ! -f "$DATA_DIR/config.json" ]; then
    # Generate a random auth token
    AUTH_TOKEN=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

    cat > "$DATA_DIR/config.json" << EOF
{
  "auth_token": "$AUTH_TOKEN",
  "host": "0.0.0.0",
  "port": 8420,
  "pushover_app_token": "",
  "pushover_user_key": "",
  "monitor_interval_seconds": 30
}
EOF
    chmod 600 "$DATA_DIR/config.json"
    echo "Created config at $DATA_DIR/config.json"
    echo "  Auth token: $AUTH_TOKEN"
    echo "  (Save this token — you'll need it in the mobile app)"
    echo ""
    echo "  To enable Pushover notifications, edit the config and add:"
    echo "    pushover_app_token: <your Pushover app token>"
    echo "    pushover_user_key: <your Pushover user key>"
else
    echo "Config already exists at $DATA_DIR/config.json"
fi

echo ""

# Install Python dependencies
echo "Installing Python dependencies..."
cd "$BACKEND_DIR"
pip3 install -r requirements.txt

echo ""

# Install Claude Code hooks
echo "Installing Claude Code hooks..."
bash "$BACKEND_DIR/hooks/install_hooks.sh"

echo ""

# Install launchd service (macOS only)
if [[ "$OSTYPE" == "darwin"* ]]; then
    PLIST_NAME="com.claude-tracker.backend"
    PLIST_SRC="$SCRIPT_DIR/$PLIST_NAME.plist"
    PLIST_DST="$HOME/Library/LaunchAgents/$PLIST_NAME.plist"

    if [ -f "$PLIST_SRC" ]; then
        # Update paths in plist
        sed "s|__BACKEND_DIR__|$BACKEND_DIR|g; s|__USER__|$USER|g" "$PLIST_SRC" > "$PLIST_DST"
        echo "Installed launchd service: $PLIST_DST"
        echo "  To start: launchctl load $PLIST_DST"
        echo "  To stop:  launchctl unload $PLIST_DST"
    fi
fi

echo ""
echo "=== Setup Complete ==="
echo ""
echo "To start the backend manually:"
echo "  cd $BACKEND_DIR && python3 main.py"
echo ""
echo "The backend will run on http://0.0.0.0:8420"
echo "Configure your mobile app with:"
echo "  Server URL: http://<mac-mini-ip>:8420"
echo "  Auth Token: (from $DATA_DIR/config.json)"
