"""Reconciles sessions with cards — auto-matches and auto-creates cards."""

from datetime import datetime, timezone

from models import Card, CardSource, CardStatus, Session
from storage import storage


class CardReconciler:
    """Matches discovered sessions to existing cards or creates new ones."""

    async def reconcile(self, sessions: list[Session]) -> list[Card]:
        """Match sessions to cards. Returns list of newly created/updated cards."""
        changes: list[Card] = []

        for session in sessions:
            card = self._find_matching_card(session)

            if card:
                # Update existing card if session activity is newer
                if session.last_activity > card.last_activity:
                    updated = storage.update_card(
                        card.id,
                        last_activity=session.last_activity,
                    )
                    if updated:
                        changes.append(updated)
            else:
                # Auto-create card for unmatched sessions
                new_card = Card(
                    title=self._derive_title(session),
                    status=self._map_status(session.status),
                    session_id=session.id,
                    project_path=session.project_path,
                    source=session.source,
                    last_activity=session.last_activity,
                )
                storage.create_card(new_card)
                changes.append(new_card)

        return changes

    def _find_matching_card(self, session: Session) -> Card | None:
        """Find an existing card that matches this session.

        Match priority:
        1. Exact session ID match
        2. Same project path (if no session linked yet)
        """
        # Priority 1: Session ID
        card = storage.get_card_by_session(session.id)
        if card:
            return card

        # Priority 2: Project path match (only if card has no session)
        for card in storage.get_cards():
            if (
                card.project_path == session.project_path
                and card.session_id is None
                and card.status != CardStatus.DONE
            ):
                # Link the session to this card
                storage.update_card(card.id, session_id=session.id)
                return storage.get_card(card.id)

        return None

    def _derive_title(self, session: Session) -> str:
        """Create a human-readable title from session metadata."""
        if session.project_path:
            # Use the last directory component
            parts = session.project_path.rstrip("/").split("/")
            return parts[-1] if parts else f"Session {session.id[:8]}"
        return f"Session {session.id[:8]}"

    def _map_status(self, session_status: str) -> CardStatus:
        """Map session status to card status."""
        mapping = {
            "active": CardStatus.IN_PROGRESS,
            "waiting": CardStatus.WAITING,
            "unknown": CardStatus.BACKLOG,
        }
        return mapping.get(session_status, CardStatus.BACKLOG)
