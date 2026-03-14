/**
 * Card store — manages kanban board state with real-time WebSocket updates.
 */

import { create } from 'zustand';
import { Card, CardCreate, CardStatus, CardUpdate } from '../models/types';
import * as api from '../api/client';
import { wsClient } from '../api/websocket';

interface CardState {
  cards: Card[];
  isLoading: boolean;
  error: string | null;

  // Actions
  loadCards: () => Promise<void>;
  addCard: (card: CardCreate) => Promise<void>;
  editCard: (id: string, update: CardUpdate) => Promise<void>;
  removeCard: (id: string) => Promise<void>;
  moveCard: (id: string, status: CardStatus) => Promise<void>;

  // WebSocket
  connectWebSocket: () => void;
  disconnectWebSocket: () => void;

  // Helpers
  getCardsByStatus: (status: CardStatus) => Card[];
}

export const useCardStore = create<CardState>()((set, get) => ({
  cards: [],
  isLoading: false,
  error: null,

  loadCards: async () => {
    set({ isLoading: true, error: null });
    try {
      const cards = await api.fetchCards();
      set({ cards, isLoading: false });
    } catch (err: any) {
      set({ error: err.message || 'Failed to load cards', isLoading: false });
    }
  },

  addCard: async (cardData: CardCreate) => {
    try {
      const card = await api.createCard(cardData);
      set((state) => ({ cards: [card, ...state.cards] }));
    } catch (err: any) {
      set({ error: err.message || 'Failed to create card' });
    }
  },

  editCard: async (id: string, update: CardUpdate) => {
    try {
      const updated = await api.updateCard(id, update);
      set((state) => ({
        cards: state.cards.map((c) => (c.id === id ? updated : c)),
      }));
    } catch (err: any) {
      set({ error: err.message || 'Failed to update card' });
    }
  },

  removeCard: async (id: string) => {
    try {
      await api.deleteCard(id);
      set((state) => ({
        cards: state.cards.filter((c) => c.id !== id),
      }));
    } catch (err: any) {
      set({ error: err.message || 'Failed to delete card' });
    }
  },

  moveCard: async (id: string, status: CardStatus) => {
    // Optimistic update
    set((state) => ({
      cards: state.cards.map((c) => (c.id === id ? { ...c, status } : c)),
    }));
    try {
      await api.updateCard(id, { status });
    } catch {
      // Revert on failure
      get().loadCards();
    }
  },

  connectWebSocket: () => {
    wsClient.connect();
    wsClient.subscribe((msg) => {
      if (msg.type === 'card_created') {
        const card = msg.data as unknown as Card;
        set((state) => {
          if (state.cards.find((c) => c.id === card.id)) return state;
          return { cards: [card, ...state.cards] };
        });
      } else if (msg.type === 'card_updated') {
        const card = msg.data as unknown as Card;
        set((state) => ({
          cards: state.cards.map((c) => (c.id === card.id ? card : c)),
        }));
      } else if (msg.type === 'card_deleted') {
        const { id } = msg.data as { id: string };
        set((state) => ({
          cards: state.cards.filter((c) => c.id !== id),
        }));
      }
    });
  },

  disconnectWebSocket: () => {
    wsClient.disconnect();
  },

  getCardsByStatus: (status: CardStatus) => {
    return get().cards.filter((c) => c.status === status);
  },
}));
