# Claude Code Tracker — Sessions-Only Design

## Concept
One entity: **Sessions**. No more Tasks/Cards.

Sessions are Claude conversations (local or cloud). When a session needs your
input (status = "waiting"), it surfaces prominently so you can reply.

## Screen Layout

### Sessions (main screen)
Grouped by status — **Needs Reply** at top:

```
┌─────────────────────────────┐
│  Sessions         [+ New]   │
│                      [2]    │  ← waiting count badge
├─────────────────────────────┤
│  ● NEEDS REPLY (2)          │
│  ┌───────────────────────┐  │
│  │ abc123def456          │  │
│  │ ~/projects/my-app     │  │
│  │ "Claude is waiting..." │  │
│  │ 3 messages • 2m ago   │  │
│  └───────────────────────┘  │
│                             │
│  ● ACTIVE (1)               │
│  ┌───────────────────────┐  │
│  │ 789xyz012345          │  │
│  │ ~/projects/backend    │  │
│  │ 12 messages • 5m ago  │  │
│  └───────────────────────┘  │
│                             │
│  ● DONE (3)       [show ▸]  │
│  (collapsed)                │
├─────────────────────────────┤
│  [Sessions]     [Settings]  │
└─────────────────────────────┘
```

### Session Detail
Full chat interface. "Waiting" sessions show alert banner + enabled reply composer.

## Architecture
- 2 tabs: Sessions + Settings
- Types: Session, ConversationEntry (no Card)
- Store: sessionStore (replaces cardStore)
- Screens: SessionsScreen (list), SessionDetailScreen (chat)
