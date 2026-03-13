"""JSON file-based persistence for cards and state."""

from __future__ import annotations

import json
import os
from pathlib import Path

from config import settings
from models import Card


class Storage:
    def __init__(self):
        self._state_path = Path(settings.tracker_data_dir) / "state.json"
        self._cards: dict[str, Card] = {}
        self._load()

    def _load(self):
        """Load state from disk."""
        if self._state_path.exists():
            with open(self._state_path) as f:
                data = json.load(f)
            for card_data in data.get("cards", []):
                card = Card(**card_data)
                self._cards[card.id] = card

    def _save(self):
        """Persist state to disk."""
        os.makedirs(self._state_path.parent, exist_ok=True)
        data = {"cards": [card.model_dump(mode="json") for card in self._cards.values()]}
        tmp = self._state_path.with_suffix(".tmp")
        with open(tmp, "w") as f:
            json.dump(data, f, indent=2, default=str)
        tmp.replace(self._state_path)

    def get_cards(self) -> list[Card]:
        """Return all cards sorted by last_activity descending."""
        return sorted(self._cards.values(), key=lambda c: c.last_activity, reverse=True)

    def get_card(self, card_id: str) -> Card | None:
        return self._cards.get(card_id)

    def get_card_by_session(self, session_id: str) -> Card | None:
        """Find a card linked to a specific session."""
        for card in self._cards.values():
            if card.session_id == session_id:
                return card
        return None

    def create_card(self, card: Card) -> Card:
        self._cards[card.id] = card
        self._save()
        return card

    def update_card(self, card_id: str, **kwargs) -> Card | None:
        card = self._cards.get(card_id)
        if not card:
            return None
        for key, value in kwargs.items():
            if value is not None and hasattr(card, key):
                setattr(card, key, value)
        from datetime import datetime, timezone
        card.last_activity = datetime.now(timezone.utc)
        self._save()
        return card

    def delete_card(self, card_id: str) -> bool:
        if card_id in self._cards:
            del self._cards[card_id]
            self._save()
            return True
        return False


# Singleton
storage = Storage()
