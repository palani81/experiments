/**
 * Card store — manages kanban board state with real-time WebSocket updates.
 * Pure React (useState + useEffect), zero external dependencies.
 */

import { useState, useEffect } from 'react';
import { Card, CardCreate, CardStatus, CardUpdate } from '../models/types';
import * as api from '../api/client';
import { wsClient } from '../api/websocket';

interface CardState {
  cards: Card[];
  isLoading: boolean;
  error: string | null;
}

// ── Module-level state ─────────────────────────────────────────
let state: CardState = { cards: [], isLoading: false, error: null };
const listeners = new Set<() => void>();

function notify() {
  listeners.forEach((l) => l());
}

function setState(partial: Partial<CardState> | ((prev: CardState) => Partial<CardState>)) {
  const next = typeof partial === 'function' ? partial(state) : partial;
  state = { ...state, ...next };
  notify();
}

// ── Actions ────────────────────────────────────────────────────
async function loadCards() {
  setState({ isLoading: true, error: null });
  try {
    const cards = await api.fetchCards();
    setState({ cards, isLoading: false });
  } catch (err: any) {
    setState({ error: err.message || 'Failed to load cards', isLoading: false });
  }
}

async function addCard(cardData: CardCreate) {
  try {
    const card = await api.createCard(cardData);
    setState((s) => ({ cards: [card, ...s.cards] }));
  } catch (err: any) {
    setState({ error: err.message || 'Failed to create card' });
  }
}

async function editCard(id: string, update: CardUpdate) {
  try {
    const updated = await api.updateCard(id, update);
    setState((s) => ({ cards: s.cards.map((c) => (c.id === id ? updated : c)) }));
  } catch (err: any) {
    setState({ error: err.message || 'Failed to update card' });
  }
}

async function removeCard(id: string) {
  try {
    await api.deleteCard(id);
    setState((s) => ({ cards: s.cards.filter((c) => c.id !== id) }));
  } catch (err: any) {
    setState({ error: err.message || 'Failed to delete card' });
  }
}

async function moveCard(id: string, status: CardStatus) {
  setState((s) => ({ cards: s.cards.map((c) => (c.id === id ? { ...c, status } : c)) }));
  try {
    await api.updateCard(id, { status });
  } catch {
    loadCards();
  }
}

function connectWebSocket() {
  wsClient.connect();
  wsClient.subscribe((msg) => {
    if (msg.type === 'card_created') {
      const card = msg.data as unknown as Card;
      setState((s) => {
        if (s.cards.find((c) => c.id === card.id)) return {};
        return { cards: [card, ...s.cards] };
      });
    } else if (msg.type === 'card_updated') {
      const card = msg.data as unknown as Card;
      setState((s) => ({ cards: s.cards.map((c) => (c.id === card.id ? card : c)) }));
    } else if (msg.type === 'card_deleted') {
      const { id } = msg.data as { id: string };
      setState((s) => ({ cards: s.cards.filter((c) => c.id !== id) }));
    }
  });
}

function disconnectWebSocket() {
  wsClient.disconnect();
}

function getCardsByStatus(status: CardStatus) {
  return state.cards.filter((c) => c.status === status);
}

// ── React hook ─────────────────────────────────────────────────
export function useCardStore() {
  const [, rerender] = useState(0);

  useEffect(() => {
    const listener = () => rerender((n) => n + 1);
    listeners.add(listener);
    return () => { listeners.delete(listener); };
  }, []);

  return {
    ...state,
    loadCards, addCard, editCard, removeCard, moveCard,
    connectWebSocket, disconnectWebSocket, getCardsByStatus,
  };
}
