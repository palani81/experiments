/**
 * Chat-style conversation display for session transcripts.
 */

import React, { useRef, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView } from 'react-native';
import { ConversationEntry } from '../models/types';

interface ConversationViewProps {
  conversation: ConversationEntry[];
}

export function ConversationView({ conversation }: ConversationViewProps) {
  const scrollRef = useRef<ScrollView>(null);

  useEffect(() => {
    // Auto-scroll to bottom on new messages
    setTimeout(() => scrollRef.current?.scrollToEnd({ animated: true }), 100);
  }, [conversation.length]);

  if (conversation.length === 0) {
    return (
      <View style={styles.empty}>
        <Text style={styles.emptyText}>No conversation history</Text>
      </View>
    );
  }

  return (
    <ScrollView ref={scrollRef} style={styles.container} showsVerticalScrollIndicator={false}>
      {conversation.map((entry, index) => (
        <View
          key={index}
          style={[
            styles.message,
            entry.role === 'user' ? styles.userMessage : styles.assistantMessage,
          ]}
        >
          <View style={styles.messageHeader}>
            <Text style={styles.role}>
              {entry.role === 'user' ? 'You' : entry.role === 'tool' ? 'Tool' : 'Claude'}
            </Text>
            {entry.tool_name && (
              <Text style={styles.toolName}>{entry.tool_name}</Text>
            )}
          </View>
          <Text style={styles.content} selectable>
            {truncateContent(entry.content)}
          </Text>
        </View>
      ))}
    </ScrollView>
  );
}

function truncateContent(content: string, maxLen = 500): string {
  if (content.length <= maxLen) return content;
  return content.slice(0, maxLen) + '...';
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  empty: {
    padding: 40,
    alignItems: 'center',
  },
  emptyText: {
    color: '#6b7280',
    fontSize: 14,
  },
  message: {
    marginBottom: 12,
    padding: 12,
    borderRadius: 12,
    width: 280,
  },
  userMessage: {
    backgroundColor: '#3b82f620',
    borderColor: '#3b82f6',
    borderWidth: 1,
    alignSelf: 'flex-end',
  },
  assistantMessage: {
    backgroundColor: '#1e1e2e',
    borderColor: '#2a2a3e',
    borderWidth: 1,
    alignSelf: 'flex-start',
  },
  messageHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 4,
    gap: 8,
  },
  role: {
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
  content: {
    color: '#e0e0e0',
    fontSize: 14,
    lineHeight: 20,
  },
});
