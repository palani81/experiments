# Claude Code Tracker - Simplified UI Plan

## Problems
1. **Board is empty/useless** — Horizontal kanban with 5 columns doesn't work on mobile. Too much swiping, columns are narrow, and it's empty because nothing auto-populates
2. **Board + Sessions are separate** — Confusing split. Users want ONE view: "what are my Claude tasks doing?"
3. **Sessions don't show up** — Session monitor scans server-side `~/.claude/projects/` every 30s. If server ≠ dev machine, nothing appears. Even when same machine, slow discovery
4. **Cloud links open browser** — Tapping a cloud session just opens claude.ai. No in-app value

## Simplified Design

### Kill the Kanban. Use a Task List.

**One primary screen: Tasks** — a vertical scrollable list of all tasks/sessions grouped by status.

**Layout:**
```
┌─────────────────────────────┐
│  Claude Tracker    [+ Add]  │
├─────────────────────────────┤
│                             │
│  ● IN PROGRESS (2)          │
│  ┌───────────────────────┐  │
│  │ Fix auth bug          │  │
│  │ ~/projects/my-app     │  │
│  │ local • 3 min ago     │  │
│  └───────────────────────┘  │
│  ┌───────────────────────┐  │
│  │ Add dark mode         │  │
│  │ cloud • 12 min ago    │  │
│  └───────────────────────┘  │
│                             │
│  ● WAITING (1)              │
│  ┌───────────────────────┐  │
│  │ Refactor DB layer     │  │
│  │ ~/projects/backend    │  │
│  │ local • 5 min ago     │  │
│  └───────────────────────┘  │
│                             │
│  ● DONE (3)        [show ▼] │
│  (collapsed by default)     │
│                             │
├─────────────────────────────┤
│  [Tasks]        [Settings]  │
└─────────────────────────────┘
```

### Changes

1. **Merge Board + Sessions into one "Tasks" tab**
   - Single vertical list, grouped by status sections
   - Status sections: In Progress, Waiting, In Review, Backlog, Done
   - Done section collapsed by default
   - Each task card shows: title, project path, source badge (local/cloud), relative time
   - Pull to refresh

2. **Remove the Sessions tab entirely**
   - The "+ Add" button on Tasks screen handles both creating new local sessions AND linking cloud conversations
   - Single modal with two options: "New Local Session" or "Link Cloud Session"

3. **Two tabs only: Tasks + Settings**
   - Simpler navigation
   - Less confusion

4. **Card Detail stays mostly the same** but cleaner:
   - Title + status badge at top
   - Status picker (horizontal chips to move between statuses)
   - Conversation view
   - Reply composer when status is "waiting"
   - Delete at bottom

5. **Fix session discovery reliability**
   - On Tasks screen load, force a session refresh from the server
   - Add a "last synced" indicator so user knows data freshness
   - Show connection status indicator (green dot / red dot) in header

## Files to Change

### Mobile
- `App.tsx` — Remove Sessions tab, rename Board to Tasks, 2-tab layout
- `BoardScreen.tsx` → Rewrite as `TaskListScreen.tsx` — grouped vertical list replacing kanban
- `SessionsScreen.tsx` — DELETE (merge add-session modals into TaskListScreen)
- `CardDetailScreen.tsx` — Minor cleanup
- `KanbanColumn.tsx` — DELETE (no longer needed)
- `CardItem.tsx` — Rewrite as simpler task row component
- `models/types.ts` — Keep as-is
- `stores/cardStore.ts` — Keep as-is (already works)
- `api/client.ts` — Keep as-is

### Backend
- No changes needed — API is fine, it's the UI that's the problem
