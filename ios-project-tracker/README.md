# Claude Code Tracker

A mobile app (iOS + Android) for tracking and managing your Claude Code projects from your phone. Works like a kanban board — see all your Claude sessions flowing through Backlog, In Progress, Waiting, In Review, and Done.

## Architecture

```
┌─────────────────┐     WebSocket/REST      ┌──────────────────────┐
│  React Native    │ ◄──────────────────────► │  Python FastAPI       │
│  Mobile App      │                          │  (Mac mini, 24/7)     │
│  (iOS + Android) │     Pushover             │                       │
│                  │ ◄─────────────────────── │  Monitors sessions    │
└─────────────────┘                          │  Receives hooks       │
                                              │  Sends notifications  │
                                              └──────┬───────────────┘
                                                     │ Claude Code Hooks
                                                     ▼
                                              ┌──────────────────────┐
                                              │  Claude Code Sessions │
                                              │  ~/.claude/projects/  │
                                              │  + claude.ai/code     │
                                              └──────────────────────┘
```

## Features

- **Kanban Board** — Visual board with drag cards between columns
- **Real-time Updates** — WebSocket connection for instant status changes
- **Two-way Communication** — Reply to Claude from your phone
- **Push Notifications** — Get notified via Pushover when Claude needs input
- **Session Browser** — View all Claude Code sessions and conversation history
- **Cloud Support** — Track both local Mac mini and claude.ai/code projects
- **Auto-discovery** — Automatically finds sessions from `~/.claude/projects/`
- **Hook Integration** — Claude Code hooks trigger card state transitions

## Quick Start

### 1. Backend (Mac mini)

```bash
cd backend
bash scripts/setup.sh    # Install deps, configure, install hooks
python3 main.py           # Start the server
```

The setup script will:
- Create `~/.claude-tracker/config.json` with a generated auth token
- Install Python dependencies
- Install Claude Code hooks into `~/.claude/settings.json`

### 2. Mobile App

```bash
cd mobile
npm install
npx expo start
```

Scan the QR code with Expo Go on your phone, then:
1. Go to **Settings**
2. Enter your Mac mini's IP: `http://<ip>:8420`
3. Enter the auth token from step 1
4. Tap **Test Connection**

### 3. Pushover Notifications (Optional)

1. Create a [Pushover](https://pushover.net/) account ($5 one-time)
2. Create an application to get an API token
3. Edit `~/.claude-tracker/config.json`:
   ```json
   {
     "pushover_app_token": "your-app-token",
     "pushover_user_key": "your-user-key"
   }
   ```
4. Restart the backend

### 4. Auto-start on Boot (macOS)

```bash
launchctl load ~/Library/LaunchAgents/com.claude-tracker.backend.plist
```

## How It Works

### Hook State Machine

| Claude Code Event | Card Status Change | Notification |
|---|---|---|
| Session starts | → In Progress | No |
| Claude stops | → Waiting | Yes |
| User replies | → In Progress | No |
| Session ends + PR | → In Review | Yes |
| Session ends | → Done | Yes |

### Two-Way Communication

When a card is in "Waiting" status, you can reply from the app. The backend uses `claude --resume <session_id> -p "your reply"` to send your message back to the Claude session.

## API Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Health check |
| GET | `/api/cards` | List all cards |
| POST | `/api/cards` | Create a card |
| PATCH | `/api/cards/:id` | Update a card |
| DELETE | `/api/cards/:id` | Delete a card |
| GET | `/api/sessions` | List sessions |
| GET | `/api/sessions/:id` | Session detail |
| POST | `/api/sessions/:id/reply` | Reply to session |
| POST | `/hooks/stop` | Stop hook receiver |
| POST | `/hooks/session-start` | Session start hook |
| POST | `/hooks/session-end` | Session end hook |
| POST | `/hooks/notification` | Notification hook |
| WS | `/ws?token=...` | Real-time updates |

## Tech Stack

- **Backend:** Python 3.11+, FastAPI, Pydantic, httpx
- **Mobile:** React Native (Expo), TypeScript, Zustand, Axios
- **Notifications:** Pushover
- **Communication:** WebSocket + REST API
