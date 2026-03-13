/**
 * Card detail screen — shows conversation history and reply composer.
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
    // Add the reply to the local conversation
    setConversation((prev) => [
      ...prev,
      { role: 'user', content: message, type: 'message' },
    ]);
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

  return (
    <View style={styles.container}>
      {/* Card Header */}
      <View style={styles.header}>
        <Text style={styles.title}>{card.title}</Text>
        <StatusBadge status={card.status} source={card.source} />

        {card.project_path && (
          <Text style={styles.projectPath} numberOfLines={1}>
            {card.project_path}
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

      {/* Move Card Actions */}
      <ScrollView horizontal style={styles.actions} showsHorizontalScrollIndicator={false}>
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
        <TouchableOpacity style={styles.deleteButton} onPress={handleDelete}>
          <Text style={styles.deleteButtonText}>Delete</Text>
        </TouchableOpacity>
      </ScrollView>

      {/* Conversation */}
      <View style={styles.conversationContainer}>
        <Text style={styles.sectionTitle}>Conversation</Text>
        {loadingConversation ? (
          <Text style={styles.loadingText}>Loading conversation...</Text>
        ) : (
          <ConversationView conversation={conversation} />
        )}
      </View>

      {/* Reply Composer */}
      {card.session_id && card.status === 'waiting' && (
        <ReplyComposer onSend={handleReply} />
      )}
    </View>
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
  actions: {
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#1e1e2e',
    maxHeight: 55,
  },
  moveButton: {
    borderWidth: 1,
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 6,
    marginRight: 8,
  },
  moveButtonText: {
    fontSize: 13,
    fontWeight: '600',
  },
  deleteButton: {
    borderWidth: 1,
    borderColor: '#ef4444',
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 6,
  },
  deleteButtonText: {
    color: '#ef4444',
    fontSize: 13,
    fontWeight: '600',
  },
  conversationContainer: {
    flex: 1,
    padding: 16,
  },
  sectionTitle: {
    color: '#9ca3af',
    fontSize: 13,
    fontWeight: '600',
    textTransform: 'uppercase',
    marginBottom: 12,
  },
  loadingText: {
    color: '#6b7280',
    fontSize: 14,
    textAlign: 'center',
    marginTop: 20,
  },
});
