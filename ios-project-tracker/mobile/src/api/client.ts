/**
 * REST API client for the Claude Code Tracker backend.
 */

import axios, { AxiosInstance } from 'axios';
import { useSettingsStore } from '../stores/settingsStore';
import { Card, CardCreate, CardUpdate, Session } from '../models/types';

function getClient(): AxiosInstance {
  const { serverUrl, authToken } = useSettingsStore.getState();
  return axios.create({
    baseURL: serverUrl,
    headers: {
      Authorization: `Bearer ${authToken}`,
      'Content-Type': 'application/json',
    },
    timeout: 10000,
  });
}

// Cards API
export async function fetchCards(status?: string): Promise<Card[]> {
  const params = status ? { status } : {};
  const { data } = await getClient().get('/api/cards', { params });
  return data.cards;
}

export async function createCard(card: CardCreate): Promise<Card> {
  const { data } = await getClient().post('/api/cards', card);
  return data;
}

export async function updateCard(id: string, update: CardUpdate): Promise<Card> {
  const { data } = await getClient().patch(`/api/cards/${id}`, update);
  return data;
}

export async function deleteCard(id: string): Promise<void> {
  await getClient().delete(`/api/cards/${id}`);
}

// Sessions API
export async function fetchSessions(): Promise<Session[]> {
  const { data } = await getClient().get('/api/sessions');
  return data.sessions;
}

export async function fetchSession(id: string): Promise<Session> {
  const { data } = await getClient().get(`/api/sessions/${id}`);
  return data;
}

export async function replyToSession(sessionId: string, message: string): Promise<void> {
  await getClient().post(`/api/sessions/${sessionId}/reply`, { message });
}

// Health check
export async function checkHealth(): Promise<boolean> {
  try {
    const { data } = await getClient().get('/health');
    return data.status === 'ok';
  } catch {
    return false;
  }
}
