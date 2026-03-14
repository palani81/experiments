/**
 * TypeScript types matching the backend Pydantic models.
 */

export type CardStatus = 'backlog' | 'in_progress' | 'waiting' | 'in_review' | 'done';
export type CardSource = 'local' | 'cloud';

export interface Card {
  id: string;
  title: string;
  status: CardStatus;
  session_id: string | null;
  branch: string | null;
  pr_url: string | null;
  project_path: string | null;
  source: CardSource;
  last_activity: string;
  conversation_summary: string | null;
  created_at: string;
}

export interface Session {
  id: string;
  project_path: string;
  status: string;
  last_activity: string;
  conversation: ConversationEntry[];
  source: CardSource;
}

export interface ConversationEntry {
  role: 'user' | 'assistant' | 'tool';
  content: string;
  timestamp?: string;
  type?: string;
  tool_name?: string;
}

export interface WebSocketMessage {
  type: 'card_created' | 'card_updated' | 'card_deleted' | 'session_updated' | 'pong';
  data: Record<string, unknown>;
}

export interface CardCreate {
  title: string;
  status?: CardStatus;
  session_id?: string;
  branch?: string;
  pr_url?: string;
  project_path?: string;
  source?: CardSource;
}

export interface CardUpdate {
  title?: string;
  status?: CardStatus;
  session_id?: string;
  branch?: string;
  pr_url?: string;
  project_path?: string;
  conversation_summary?: string;
}

export const KANBAN_COLUMNS: { key: CardStatus; label: string; color: string }[] = [
  { key: 'backlog', label: 'Backlog', color: '#6b7280' },
  { key: 'in_progress', label: 'In Progress', color: '#3b82f6' },
  { key: 'waiting', label: 'Waiting', color: '#f59e0b' },
  { key: 'in_review', label: 'In Review', color: '#8b5cf6' },
  { key: 'done', label: 'Done', color: '#10b981' },
];
