/**
 * TypeScript types for the Sessions-only Claude Tracker.
 */

export type SessionStatus = 'active' | 'waiting' | 'done';
export type SessionSource = 'local' | 'cloud';

export interface Session {
  id: string;
  project_path: string;
  status: SessionStatus;
  last_activity: string;
  conversation: ConversationEntry[];
  source: SessionSource;
}

export interface ConversationEntry {
  role: 'user' | 'assistant' | 'tool';
  content: string;
  timestamp?: string;
  type?: string;
  tool_name?: string;
}

export interface WebSocketMessage {
  type: 'session_updated' | 'session_created' | 'session_deleted' | 'pong';
  data: Record<string, unknown>;
}

export const SESSION_STATUSES: { key: SessionStatus; label: string; color: string }[] = [
  { key: 'waiting', label: 'Needs Reply', color: '#f59e0b' },
  { key: 'active', label: 'Active', color: '#10b981' },
  { key: 'done', label: 'Done', color: '#6b7280' },
];
