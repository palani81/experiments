/**
 * Main kanban board screen — horizontal scrolling columns.
 */

import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  RefreshControl,
  TouchableOpacity,
  TextInput,
  Modal,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { useCardStore } from '../stores/cardStore';
import { useSettingsStore } from '../stores/settingsStore';
import { KanbanColumn } from '../components/KanbanColumn';
import { Card, CardStatus, KANBAN_COLUMNS } from '../models/types';

export function BoardScreen() {
  const navigation = useNavigation<any>();
  const { cards, isLoading, error, loadCards, connectWebSocket, addCard } = useCardStore();
  const { isConfigured } = useSettingsStore();
  const [showAddModal, setShowAddModal] = useState(false);
  const [newTitle, setNewTitle] = useState('');

  useEffect(() => {
    if (isConfigured) {
      loadCards();
      connectWebSocket();
    }
  }, [isConfigured]);

  const handleCardPress = (card: Card) => {
    navigation.navigate('CardDetail', { cardId: card.id });
  };

  const handleAddCard = async () => {
    if (!newTitle.trim()) return;
    await addCard({ title: newTitle.trim() });
    setNewTitle('');
    setShowAddModal(false);
  };

  if (!isConfigured) {
    return (
      <View style={styles.centered}>
        <Text style={styles.setupTitle}>Welcome to Claude Code Tracker</Text>
        <Text style={styles.setupText}>
          Configure your backend server in Settings to get started.
        </Text>
        <TouchableOpacity
          style={styles.setupButton}
          onPress={() => navigation.navigate('Settings')}
        >
          <Text style={styles.setupButtonText}>Go to Settings</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.title}>Claude Code Tracker</Text>
        <TouchableOpacity style={styles.addButton} onPress={() => setShowAddModal(true)}>
          <Text style={styles.addButtonText}>+ New</Text>
        </TouchableOpacity>
      </View>

      {error && (
        <View style={styles.errorBanner}>
          <Text style={styles.errorText}>{error}</Text>
        </View>
      )}

      {/* Kanban Board — horizontal scroll */}
      <ScrollView
        horizontal
        style={styles.board}
        contentContainerStyle={styles.boardContent}
        showsHorizontalScrollIndicator={false}
        refreshControl={
          <RefreshControl refreshing={isLoading} onRefresh={loadCards} tintColor="#3b82f6" />
        }
      >
        {KANBAN_COLUMNS.map((col) => (
          <KanbanColumn
            key={col.key}
            status={col.key}
            cards={cards.filter((c) => c.status === col.key)}
            onCardPress={handleCardPress}
          />
        ))}
      </ScrollView>

      {/* Add Card Modal */}
      <Modal visible={showAddModal} transparent animationType="slide">
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>New Card</Text>
            <TextInput
              style={styles.modalInput}
              value={newTitle}
              onChangeText={setNewTitle}
              placeholder="Card title..."
              placeholderTextColor="#6b7280"
              autoFocus
            />
            <View style={styles.modalButtons}>
              <TouchableOpacity
                style={styles.cancelButton}
                onPress={() => {
                  setShowAddModal(false);
                  setNewTitle('');
                }}
              >
                <Text style={styles.cancelButtonText}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.createButton, !newTitle.trim() && styles.createButtonDisabled]}
                onPress={handleAddCard}
                disabled={!newTitle.trim()}
              >
                <Text style={styles.createButtonText}>Create</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0a0a1a',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingTop: 60,
    paddingBottom: 12,
  },
  title: {
    color: '#fff',
    fontSize: 22,
    fontWeight: '800',
  },
  addButton: {
    backgroundColor: '#3b82f6',
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 10,
  },
  addButtonText: {
    color: '#fff',
    fontWeight: '600',
    fontSize: 14,
  },
  board: {
    flex: 1,
  },
  boardContent: {
    paddingHorizontal: 14,
    paddingBottom: 20,
  },
  centered: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#0a0a1a',
    padding: 32,
  },
  setupTitle: {
    color: '#fff',
    fontSize: 22,
    fontWeight: '700',
    marginBottom: 12,
    textAlign: 'center',
  },
  setupText: {
    color: '#9ca3af',
    fontSize: 15,
    textAlign: 'center',
    marginBottom: 24,
    lineHeight: 22,
  },
  setupButton: {
    backgroundColor: '#3b82f6',
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 12,
  },
  setupButtonText: {
    color: '#fff',
    fontWeight: '600',
    fontSize: 16,
  },
  errorBanner: {
    backgroundColor: '#ef444420',
    borderColor: '#ef4444',
    borderWidth: 1,
    marginHorizontal: 14,
    marginBottom: 10,
    padding: 10,
    borderRadius: 8,
  },
  errorText: {
    color: '#ef4444',
    fontSize: 13,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: '#00000080',
    justifyContent: 'center',
    padding: 24,
  },
  modalContent: {
    backgroundColor: '#1e1e2e',
    borderRadius: 16,
    padding: 20,
  },
  modalTitle: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '700',
    marginBottom: 16,
  },
  modalInput: {
    backgroundColor: '#0d0d1a',
    borderRadius: 10,
    padding: 14,
    color: '#e0e0e0',
    fontSize: 15,
    borderWidth: 1,
    borderColor: '#2a2a3e',
    marginBottom: 16,
  },
  modalButtons: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    gap: 10,
  },
  cancelButton: {
    paddingHorizontal: 16,
    paddingVertical: 10,
  },
  cancelButtonText: {
    color: '#9ca3af',
    fontSize: 15,
  },
  createButton: {
    backgroundColor: '#3b82f6',
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 10,
  },
  createButtonDisabled: {
    backgroundColor: '#3b82f640',
  },
  createButtonText: {
    color: '#fff',
    fontWeight: '600',
    fontSize: 15,
  },
});
