/**
 * REST API client for the Claude Code Tracker backend.
 * Sessions-only — no more cards.
 */

import axios, { AxiosInstance } from 'axios';
import { useSettingsStore } from '../stores/settingsStore';
import { Session } from '../models/types';

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

// Sessions API
export async function fetchSessions(days: number = 7): Promise<Session[]> {
  const { data } = await getClient().get('/api/sessions', { params: { days } });
  return data.sessions || [];
}

export async function fetchSession(id: string): Promise<Session> {
  const { data } = await getClient().get(`/api/sessions/${id}`);
  return data;
}

export async function createSession(name: string): Promise<void> {
  await getClient().post('/api/sessions', { name });
}

export async function addCloudSession(sessionId: string, title: string, url?: string): Promise<void> {
  await getClient().post('/api/sessions/cloud', { session_id: sessionId, title, url: url || '' });
}

export async function removeCloudSession(sessionId: string): Promise<void> {
  await getClient().delete(`/api/sessions/cloud/${sessionId}`);
}

export async function replyToSession(sessionId: string, message: string): Promise<void> {
  await getClient().post(`/api/sessions/${sessionId}/reply`, { message });
}

// Health check
export async function checkHealth(): Promise<{ ok: boolean; info?: any }> {
  try {
    const { data } = await getClient().get('/health');
    return { ok: data.status === 'ok', info: data };
  } catch {
    return { ok: false };
  }
}

// Server logs
export interface LogEntry {
  ts: string;
  level: string;
  logger: string;
  message: string;
}

export async function fetchLogs(limit: number = 100): Promise<LogEntry[]> {
  const { data } = await getClient().get('/api/logs', { params: { limit } });
  return data.logs || [];
}
