/**
 * Task detail screen — shows info, conversation history, and reply composer.
 */

import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
  Linking,
  KeyboardAvoidingView,
  Platform,
  TextInput,
} from 'react-native';
import { useRoute, useNavigation } from '@react-navigation/native';
import { useCardStore } from '../stores/cardStore';
import { StatusBadge } from '../components/StatusBadge';
import { ConversationView } from '../components/ConversationView';
import { ReplyComposer } from '../components/ReplyComposer';
import { CardStatus, ConversationEntry, KANBAN_COLUMNS } from '../models/types';
import { fetchSession, replyToSession } from '../api/client';

export function CardDetailScreen() {
  const route = useRoute<any>();
  const navigation = useNavigation();
  const { cards, editCard, removeCard, moveCard } = useCardStore();
  const card = cards.find((c) => c.id === route.params?.cardId);
  const [conversation, setConversation] = useState<ConversationEntry[]>([]);
  const [loadingConversation, setLoadingConversation] = useState(false);
  const [notes, setNotes] = useState('');
  const [notesEdited, setNotesEdited] = useState(false);

  useEffect(() => {
    if (card?.conversation_summary) {
      setNotes(card.conversation_summary);
    }
  }, [card?.id]);

  useEffect(() => {
    if (card?.session_id) {
      loadConversation();
    }
  }, [card?.session_id]);

  const loadConversation = async () => {
    if (!card?.session_id) return;
    setLoadingConversation(true);
    try {
      const session = await fetchSession(card.session_id);
      setConversation(session.conversation);
    } catch {
      // Session may not be available
    } finally {
      setLoadingConversation(false);
    }
  };

  const handleReply = async (message: string) => {
    if (!card?.session_id) {
      Alert.alert('No Session', 'This card is not linked to a Claude session.');
      return;
    }
    await replyToSession(card.session_id, message);
    setConversation((prev) => [
      ...prev,
      { role: 'user', content: message, type: 'message' },
    ]);
  };

  const handleSaveNotes = () => {
    if (card && notesEdited) {
      editCard(card.id, { conversation_summary: notes });
      setNotesEdited(false);
    }
  };

  const handleMoveCard = (status: CardStatus) => {
    if (card) {
      moveCard(card.id, status);
    }
  };

  const handleDelete = () => {
    Alert.alert('Delete Card', 'Are you sure you want to delete this card?', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Delete',
        style: 'destructive',
        onPress: () => {
          if (card) {
            removeCard(card.id);
            navigation.goBack();
          }
        },
      },
    ]);
  };

  if (!card) {
    return (
      <View style={styles.centered}>
        <Text style={styles.notFound}>Card not found</Text>
      </View>
    );
  }

  const hasSession = !!card.session_id;
  const isWaiting = card.status === 'waiting';

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      keyboardVerticalOffset={Platform.OS === 'ios' ? 90 : 0}
    >
      <ScrollView style={styles.scrollContent} contentContainerStyle={styles.scrollInner}>
        {/* Card Header */}
        <View style={styles.header}>
          <Text style={styles.title}>{card.title}</Text>
          <StatusBadge status={card.status} source={card.source} />

          {card.project_path && (
            <Text style={styles.projectPath} numberOfLines={1}>
              {card.project_path}
            </Text>
          )}

          {card.branch && (
            <Text style={styles.branch} numberOfLines={1}>
              {card.branch}
            </Text>
          )}

          {card.pr_url && (
            <TouchableOpacity
              style={styles.prLink}
              onPress={() => Linking.openURL(card.pr_url!)}
            >
              <Text style={styles.prLinkText}>View Pull Request</Text>
            </TouchableOpacity>
          )}
        </View>

        {/* Status Actions */}
        <View style={styles.actionsSection}>
          <Text style={styles.sectionLabel}>Move to</Text>
          <ScrollView horizontal showsHorizontalScrollIndicator={false}>
            {KANBAN_COLUMNS.filter((col) => col.key !== card.status).map((col) => (
              <TouchableOpacity
                key={col.key}
                style={[styles.moveButton, { borderColor: col.color }]}
                onPress={() => handleMoveCard(col.key)}
              >
                <Text style={[styles.moveButtonText, { color: col.color }]}>
                  {col.label}
                </Text>
              </TouchableOpacity>
            ))}
          </ScrollView>
        </View>

        {/* Notes (for all cards) */}
        <View style={styles.notesSection}>
          <Text style={styles.sectionLabel}>Notes</Text>
          <TextInput
            style={styles.notesInput}
            value={notes}
            onChangeText={(text) => {
              setNotes(text);
              setNotesEdited(true);
            }}
            onBlur={handleSaveNotes}
            placeholder="Add notes about this task..."
            placeholderTextColor="#4b5563"
            multiline
            textAlignVertical="top"
          />
          {notesEdited && (
            <TouchableOpacity style={styles.saveNotesButton} onPress={handleSaveNotes}>
              <Text style={styles.saveNotesText}>Save</Text>
            </TouchableOpacity>
          )}
        </View>

        {/* Conversation (only if linked to a session) */}
        {hasSession && (
          <View style={styles.conversationSection}>
            <Text style={styles.sectionLabel}>Conversation</Text>
            {loadingConversation ? (
              <Text style={styles.loadingText}>Loading conversation...</Text>
            ) : conversation.length > 0 ? (
              <ConversationView conversation={conversation} />
            ) : (
              <Text style={styles.emptyText}>No messages yet</Text>
            )}
          </View>
        )}

        {!hasSession && (
          <View style={styles.noSessionInfo}>
            <Text style={styles.noSessionText}>
              This task is not linked to a Claude session.
              Sessions get linked automatically when created via hooks or the "New Claude Session" option.
            </Text>
          </View>
        )}

        {/* Delete */}
        <TouchableOpacity style={styles.deleteButton} onPress={handleDelete}>
          <Text style={styles.deleteButtonText}>Delete Task</Text>
        </TouchableOpacity>
      </ScrollView>

      {/* Reply Composer — show when linked to session and waiting */}
      {hasSession && isWaiting && (
        <ReplyComposer onSend={handleReply} />
      )}
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0a0a1a',
  },
  scrollContent: {
    flex: 1,
  },
  scrollInner: {
    paddingBottom: 30,
  },
  centered: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#0a0a1a',
  },
  notFound: {
    color: '#6b7280',
    fontSize: 16,
  },
  header: {
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#1e1e2e',
    gap: 8,
  },
  title: {
    color: '#fff',
    fontSize: 20,
    fontWeight: '700',
  },
  projectPath: {
    color: '#6b7280',
    fontSize: 12,
    fontFamily: 'monospace',
  },
  branch: {
    color: '#3b82f6',
    fontSize: 12,
    fontFamily: 'monospace',
  },
  prLink: {
    backgroundColor: '#8b5cf620',
    borderColor: '#8b5cf6',
    borderWidth: 1,
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 8,
    alignSelf: 'flex-start',
  },
  prLinkText: {
    color: '#8b5cf6',
    fontWeight: '600',
    fontSize: 13,
  },
  actionsSection: {
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#1e1e2e',
  },
  sectionLabel: {
    color: '#9ca3af',
    fontSize: 12,
    fontWeight: '600',
    textTransform: 'uppercase',
    marginBottom: 10,
  },
  moveButton: {
    borderWidth: 1,
    borderRadius: 8,
    paddingHorizontal: 14,
    paddingVertical: 7,
    marginRight: 8,
  },
  moveButtonText: {
    fontSize: 13,
    fontWeight: '600',
  },
  notesSection: {
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#1e1e2e',
  },
  notesInput: {
    backgroundColor: '#1e1e2e',
    borderRadius: 10,
    padding: 12,
    color: '#e0e0e0',
    fontSize: 14,
    minHeight: 80,
    borderWidth: 1,
    borderColor: '#2a2a3e',
    lineHeight: 20,
  },
  saveNotesButton: {
    alignSelf: 'flex-end',
    backgroundColor: '#3b82f6',
    paddingHorizontal: 14,
    paddingVertical: 6,
    borderRadius: 8,
    marginTop: 8,
  },
  saveNotesText: {
    color: '#fff',
    fontSize: 13,
    fontWeight: '600',
  },
  conversationSection: {
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#1e1e2e',
  },
  loadingText: {
    color: '#6b7280',
    fontSize: 14,
    textAlign: 'center',
    marginTop: 12,
  },
  emptyText: {
    color: '#4b5563',
    fontSize: 14,
    textAlign: 'center',
    marginTop: 12,
  },
  noSessionInfo: {
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#1e1e2e',
  },
  noSessionText: {
    color: '#4b5563',
    fontSize: 13,
    lineHeight: 20,
  },
  deleteButton: {
    margin: 16,
    borderWidth: 1,
    borderColor: '#ef444440',
    borderRadius: 10,
    padding: 12,
    alignItems: 'center',
  },
  deleteButtonText: {
    color: '#ef4444',
    fontSize: 14,
    fontWeight: '600',
  },
});
