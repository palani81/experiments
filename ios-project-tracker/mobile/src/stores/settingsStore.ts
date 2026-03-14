/**
 * Settings store — persists backend URL and auth token.
 * Pure React (useState + useEffect), zero external dependencies.
 */

import { useState, useEffect, useCallback } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';

interface SettingsState {
  serverUrl: string;
  authToken: string;
  isConfigured: boolean;
}

// ── Module-level state (shared across all hook consumers) ──────
let state: SettingsState = { serverUrl: '', authToken: '', isConfigured: false };
const listeners = new Set<() => void>();

function notify() {
  listeners.forEach((l) => l());
}

async function setServer(url: string, token: string) {
  const serverUrl = url.replace(/\/+$/, '');
  await AsyncStorage.setItem('serverUrl', serverUrl);
  await AsyncStorage.setItem('authToken', token);
  state = { serverUrl, authToken: token, isConfigured: true };
  notify();
}

async function loadSettings() {
  const serverUrl = await AsyncStorage.getItem('serverUrl');
  const authToken = await AsyncStorage.getItem('authToken');
  if (serverUrl && authToken) {
    state = { serverUrl, authToken, isConfigured: true };
    notify();
  }
}

// ── React hook ─────────────────────────────────────────────────
export function useSettingsStore() {
  const [, rerender] = useState(0);

  useEffect(() => {
    const listener = () => rerender((n) => n + 1);
    listeners.add(listener);
    return () => { listeners.delete(listener); };
  }, []);

  return {
    ...state,
    setServer: useCallback(setServer, []),
    loadSettings: useCallback(loadSettings, []),
  };
}

// Non-React access (used by client.ts, websocket.ts)
useSettingsStore.getState = () => ({
  ...state,
  setServer,
  loadSettings,
});
