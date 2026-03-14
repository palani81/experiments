/**
 * Full-screen chat interface for a Claude session.
 * Shows conversation history and allows sending replies when session is waiting.
 */

import React, { useEffect, useState, useRef, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  KeyboardAvoidingView,
  Platform,
  ActivityIndicator,
  RefreshControl,
  TouchableOpacity,
  Alert,
} from 'react-native';
import { useRoute, useNavigation } from '@react-navigation/native';
import { ConversationEntry } from '../models/types';
import { StatusBadge } from '../components/StatusBadge';
import { ReplyComposer } from '../components/ReplyComposer';
import { fetchSession, replyToSession, removeCloudSession } from '../api/client';
import { SessionStatus } from '../models/types';

function normalizeStatus(status: string | undefined): SessionStatus {
  if (!status) return 'active';
  const s = status.toLowerCase();
  if (s === 'waiting' || s === 'paused') return 'waiting';
  if (s === 'done' || s === 'completed' || s === 'finished') return 'done';
  return 'active';
}

function MessageBubble({ entry }: { entry: ConversationEntry }) {
  const isUser = entry.role === 'user';
  const isTool = entry.role === 'tool';

  return (
    <View style={[styles.bubble, isUser ? styles.userBubble : styles.assistantBubble]}>
      <View style={styles.bubbleHeader}>
        <Text style={styles.roleName}>
          {isUser ? 'You' : isTool ? 'Tool' : 'Claude'}
        </Text>
        {entry.tool_name && (
          <Text style={styles.toolName}>{entry.tool_name}</Text>
        )}
      </View>
      <Text style={styles.messageText} selectable>
        {entry.content}
      </Text>
    </View>
  );
}

export function SessionDetailScreen() {
  const route = useRoute<any>();
  const navigation = useNavigation();
  const sessionId: string = route.params?.sessionId;
  const [conversation, setConversation] = useState<ConversationEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [sessionStatus, setSessionStatus] = useState('');
  const [sessionSource, setSessionSource] = useState<'local' | 'cloud'>('local');
  const flatListRef = useRef<FlatList>(null);

  const loadSession = useCallback(async () => {
    try {
      const session = await fetchSession(sessionId);
      setConversation(session.conversation);
      setSessionStatus(session.status);
      setSessionSource(session.source);
    } catch {
      // session may not be available
    }
  }, [sessionId]);

  useEffect(() => {
    (async () => {
      await loadSession();
      setLoading(false);
    })();
  }, [loadSession]);

  // Auto-poll every 5s when session is active or waiting
  useEffect(() => {
    const n = normalizeStatus(sessionStatus);
    if (n !== 'active' && n !== 'waiting') return;
    const interval = setInterval(loadSession, 5000);
    return () => clearInterval(interval);
  }, [sessionStatus, loadSession]);

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadSession();
    setRefreshing(false);
  };

  const handleReply = async (message: string) => {
    await replyToSession(sessionId, message);
    setConversation((prev) => [
      ...prev,
      { role: 'user', content: message, type: 'message' },
    ]);
    setTimeout(loadSession, 2000);
  };

  const handleDelete = () => {
    Alert.alert('Remove Session', 'Remove this session from tracking?', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Remove',
        style: 'destructive',
        onPress: async () => {
          try {
            await removeCloudSession(sessionId);
          } catch {
            // May fail for local sessions — that's OK
          }
          navigation.goBack();
        },
      },
    ]);
  };

  if (loading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color="#3b82f6" />
      </View>
    );
  }

  const normalized = normalizeStatus(sessionStatus);
  const isWaiting = normalized === 'waiting';

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      keyboardVerticalOffset={Platform.OS === 'ios' ? 90 : 0}
    >
      {/* Status bar */}
      <View style={styles.statusBar}>
        <StatusBadge status={normalized} source={sessionSource} />
        <Text style={styles.messageCount}>{conversation.length} messages</Text>
        <TouchableOpacity onPress={handleDelete} style={styles.deleteLink}>
          <Text style={styles.deleteLinkText}>Remove</Text>
        </TouchableOpacity>
      </View>

      {/* Waiting alert */}
      {isWaiting && (
        <View style={styles.waitingAlert}>
          <Text style={styles.waitingAlertText}>
            Claude needs your input — reply below
          </Text>
        </View>
      )}

      {/* Conversation */}
      <FlatList
        ref={flatListRef}
        data={conversation}
        keyExtractor={(_, index) => String(index)}
        renderItem={({ item }) => <MessageBubble entry={item} />}
        contentContainerStyle={styles.messageList}
        onContentSizeChange={() => flatListRef.current?.scrollToEnd({ animated: true })}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={handleRefresh} tintColor="#3b82f6" />
        }
        ListEmptyComponent={
          <View style={styles.centered}>
            <Text style={styles.emptyText}>No messages yet</Text>
          </View>
        }
      />

      {/* Reply composer */}
      <ReplyComposer
        onSend={handleReply}
        disabled={!isWaiting}
        placeholder={isWaiting ? 'Reply to Claude...' : `Session is ${sessionStatus || 'not active'} — reply disabled`}
      />
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0a0a1a',
  },
  centered: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#0a0a1a',
  },
  statusBar: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#1e1e2e',
    gap: 8,
  },
  messageCount: {
    color: '#4b5563',
    fontSize: 12,
    marginLeft: 'auto',
  },
  deleteLink: {
    paddingHorizontal: 8,
    paddingVertical: 4,
  },
  deleteLinkText: {
    color: '#ef4444',
    fontSize: 12,
    fontWeight: '600',
  },
  waitingAlert: {
    backgroundColor: '#f59e0b20',
    borderBottomWidth: 1,
    borderBottomColor: '#f59e0b40',
    paddingHorizontal: 16,
    paddingVertical: 10,
  },
  waitingAlertText: {
    color: '#f59e0b',
    fontSize: 13,
    fontWeight: '700',
    textAlign: 'center',
  },
  messageList: {
    padding: 16,
    paddingBottom: 8,
  },
  bubble: {
    marginBottom: 12,
    padding: 12,
    borderRadius: 12,
    maxWidth: '85%',
    borderWidth: 1,
  },
  userBubble: {
    backgroundColor: '#3b82f620',
    borderColor: '#3b82f6',
    alignSelf: 'flex-end',
  },
  assistantBubble: {
    backgroundColor: '#1e1e2e',
    borderColor: '#2a2a3e',
    alignSelf: 'flex-start',
  },
  bubbleHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 4,
    gap: 8,
  },
  roleName: {
    color: '#9ca3af',
    fontSize: 11,
    fontWeight: '700',
    textTransform: 'uppercase',
  },
  toolName: {
    color: '#6b7280',
    fontSize: 11,
    fontFamily: 'monospace',
  },
  messageText: {
    color: '#e0e0e0',
    fontSize: 14,
    lineHeight: 20,
  },
  emptyText: {
    color: '#4b5563',
    fontSize: 14,
  },
});
