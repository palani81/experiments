/**
 * Session store — manages all sessions with real-time WebSocket updates.
 * Sessions are the single primary entity. "Waiting" sessions need your attention.
 */

import { useState, useEffect } from 'react';
import { Session, SessionStatus } from '../models/types';
import * as api from '../api/client';
import { wsClient } from '../api/websocket';

interface SessionState {
  sessions: Session[];
  isLoading: boolean;
  error: string | null;
}

// ── Module-level state ─────────────────────────────────────────
let state: SessionState = { sessions: [], isLoading: false, error: null };
const listeners = new Set<() => void>();

function notify() {
  listeners.forEach((l) => l());
}

function setState(partial: Partial<SessionState> | ((prev: SessionState) => Partial<SessionState>)) {
  const next = typeof partial === 'function' ? partial(state) : partial;
  state = { ...state, ...next };
  notify();
}

// ── Actions ────────────────────────────────────────────────────
async function loadSessions(days: number = 7) {
  setState({ isLoading: true, error: null });
  try {
    const sessions = await api.fetchSessions(days);
    setState({ sessions, isLoading: false });
  } catch (err: any) {
    setState({ error: err.message || 'Failed to load sessions', isLoading: false });
  }
}

async function removeSession(id: string) {
  try {
    await api.removeCloudSession(id);
    setState((s) => ({ sessions: s.sessions.filter((sess) => sess.id !== id) }));
  } catch (err: any) {
    setState({ error: err.message || 'Failed to remove session' });
  }
}

function getSessionsByStatus(status: SessionStatus) {
  return state.sessions.filter((s) => s.status === status);
}

function getWaitingCount() {
  return state.sessions.filter((s) => s.status === 'waiting').length;
}

function connectWebSocket() {
  wsClient.connect();
  wsClient.subscribe((msg) => {
    if (msg.type === 'session_updated' || msg.type === 'session_created') {
      const session = msg.data as unknown as Session;
      setState((s) => {
        const existing = s.sessions.findIndex((sess) => sess.id === session.id);
        if (existing >= 0) {
          const updated = [...s.sessions];
          updated[existing] = session;
          return { sessions: updated };
        }
        return { sessions: [session, ...s.sessions] };
      });
    } else if (msg.type === 'session_deleted') {
      const { id } = msg.data as { id: string };
      setState((s) => ({ sessions: s.sessions.filter((sess) => sess.id !== id) }));
    }
  });
}

function disconnectWebSocket() {
  wsClient.disconnect();
}

// ── React hook ─────────────────────────────────────────────────
export function useSessionStore() {
  const [, rerender] = useState(0);

  useEffect(() => {
    const listener = () => rerender((n) => n + 1);
    listeners.add(listener);
    return () => { listeners.delete(listener); };
  }, []);

  return {
    ...state,
    loadSessions,
    removeSession,
    getSessionsByStatus,
    getWaitingCount,
    connectWebSocket,
    disconnectWebSocket,
  };
}
