/**
 * Main task list screen — vertical list grouped by status.
 * Replaces the old horizontal kanban board + separate sessions screen.
 */

import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  SectionList,
  TouchableOpacity,
  RefreshControl,
  TextInput,
  Modal,
  Alert,
  KeyboardAvoidingView,
  Platform,
  Keyboard,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { useCardStore } from '../stores/cardStore';
import { useSettingsStore } from '../stores/settingsStore';
import { Card, CardStatus, KANBAN_COLUMNS } from '../models/types';
import { StatusBadge } from '../components/StatusBadge';
import { createSession, addCloudSession } from '../api/client';

type AddMode = null | 'choose' | 'manual' | 'local' | 'cloud';

// Status display order: active stuff first, done last
const STATUS_ORDER: CardStatus[] = ['in_progress', 'waiting', 'in_review', 'backlog', 'done'];

function getTimeAgo(dateStr: string): string {
  const now = Date.now();
  const then = new Date(dateStr).getTime();
  const diff = Math.floor((now - then) / 1000);
  if (diff < 60) return 'just now';
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return `${Math.floor(diff / 86400)}d ago`;
}

export function TaskListScreen() {
  const navigation = useNavigation<any>();
  const { cards, isLoading, error, loadCards, connectWebSocket, addCard } = useCardStore();
  const { isConfigured } = useSettingsStore();

  // Add modal state
  const [addMode, setAddMode] = useState<AddMode>(null);
  const [newTitle, setNewTitle] = useState('');
  const [newProjectPath, setNewProjectPath] = useState('');
  const [newPrompt, setNewPrompt] = useState('');
  const [newUrl, setNewUrl] = useState('');
  const [submitting, setSubmitting] = useState(false);

  // Done section collapsed by default
  const [doneCollapsed, setDoneCollapsed] = useState(true);

  useEffect(() => {
    if (isConfigured) {
      loadCards();
      connectWebSocket();
    }
  }, [isConfigured]);

  const resetModal = () => {
    setAddMode(null);
    setNewTitle('');
    setNewProjectPath('');
    setNewPrompt('');
    setNewUrl('');
    Keyboard.dismiss();
  };

  const handleAddManualCard = async () => {
    if (!newTitle.trim()) return;
    await addCard({ title: newTitle.trim() });
    resetModal();
  };

  const handleCreateLocal = async () => {
    if (!newProjectPath.trim() || !newPrompt.trim()) {
      Alert.alert('Missing fields', 'Project path and prompt are required.');
      return;
    }
    setSubmitting(true);
    try {
      await createSession(newProjectPath.trim(), newPrompt.trim(), newTitle.trim());
      resetModal();
      Alert.alert('Session Started', 'A new Claude session has been kicked off.');
      setTimeout(loadCards, 3000);
    } catch (e: any) {
      Alert.alert('Error', e?.response?.data?.detail || 'Failed to start session.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleLinkCloud = async () => {
    if (!newUrl.trim()) {
      Alert.alert('Missing URL', 'Please paste the Claude conversation URL.');
      return;
    }
    const title = newTitle.trim() || 'Claude Conversation';
    const url = newUrl.trim();
    const urlParts = url.split('/');
    const sessionId = urlParts[urlParts.length - 1] || `conv-${Date.now()}`;

    setSubmitting(true);
    try {
      await addCloudSession(sessionId, title, url);
      await addCard({ title, status: 'in_progress', source: 'cloud', pr_url: url });
      resetModal();
      loadCards();
    } catch (e: any) {
      Alert.alert('Error', e?.response?.data?.detail || 'Failed to link conversation.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleCardPress = (card: Card) => {
    navigation.navigate('CardDetail', { cardId: card.id });
  };

  // Build sections from cards
  const sections = STATUS_ORDER.map((status) => {
    const col = KANBAN_COLUMNS.find((c) => c.key === status)!;
    const sectionCards = cards.filter((c) => c.status === status);
    return {
      status,
      title: col.label,
      color: col.color,
      data: status === 'done' && doneCollapsed ? [] : sectionCards,
      count: sectionCards.length,
      collapsed: status === 'done' && doneCollapsed,
    };
  }).filter((s) => s.count > 0); // Hide empty sections

  const renderCard = ({ item }: { item: Card }) => (
    <TouchableOpacity
      style={styles.card}
      onPress={() => handleCardPress(item)}
      activeOpacity={0.7}
    >
      <View style={styles.cardTop}>
        <Text style={styles.cardTitle} numberOfLines={2}>{item.title}</Text>
      </View>
      {item.project_path && (
        <Text style={styles.cardPath} numberOfLines={1}>{item.project_path}</Text>
      )}
      {item.conversation_summary && (
        <Text style={styles.cardSummary} numberOfLines={2}>{item.conversation_summary}</Text>
      )}
      <View style={styles.cardBottom}>
        <View style={styles.cardMeta}>
          <Text style={styles.cardSource}>{item.source}</Text>
          {item.branch && <Text style={styles.cardBranch} numberOfLines={1}>{item.branch}</Text>}
        </View>
        <Text style={styles.cardTime}>{getTimeAgo(item.last_activity)}</Text>
      </View>
      {item.pr_url && item.source !== 'cloud' && (
        <View style={styles.prTag}>
          <Text style={styles.prTagText}>PR</Text>
        </View>
      )}
    </TouchableOpacity>
  );

  const renderSectionHeader = ({ section }: { section: any }) => (
    <TouchableOpacity
      style={styles.sectionHeader}
      onPress={() => {
        if (section.status === 'done') setDoneCollapsed((v) => !v);
      }}
      activeOpacity={section.status === 'done' ? 0.6 : 1}
    >
      <View style={[styles.sectionDot, { backgroundColor: section.color }]} />
      <Text style={styles.sectionTitle}>{section.title}</Text>
      <View style={styles.sectionCount}>
        <Text style={styles.sectionCountText}>{section.count}</Text>
      </View>
      {section.status === 'done' && (
        <Text style={styles.collapseArrow}>{section.collapsed ? '▸' : '▾'}</Text>
      )}
    </TouchableOpacity>
  );

  if (!isConfigured) {
    return (
      <View style={styles.centered}>
        <Text style={styles.setupTitle}>Claude Tracker</Text>
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
        <Text style={styles.title}>Tasks</Text>
        <TouchableOpacity style={styles.addButton} onPress={() => setAddMode('choose')}>
          <Text style={styles.addButtonText}>+ Add</Text>
        </TouchableOpacity>
      </View>

      {error && (
        <View style={styles.errorBanner}>
          <Text style={styles.errorText}>{error}</Text>
        </View>
      )}

      {/* Task List */}
      <SectionList
        sections={sections}
        keyExtractor={(item) => item.id}
        renderItem={renderCard}
        renderSectionHeader={renderSectionHeader}
        refreshControl={
          <RefreshControl refreshing={isLoading} onRefresh={loadCards} tintColor="#3b82f6" />
        }
        contentContainerStyle={styles.listContent}
        stickySectionHeadersEnabled={false}
        ListEmptyComponent={
          <View style={styles.emptyContainer}>
            <Text style={styles.emptyTitle}>No tasks yet</Text>
            <Text style={styles.emptyText}>
              Tap "+ Add" to create a task, start a Claude session, or link a cloud conversation.
            </Text>
          </View>
        }
      />

      {/* Choose Action Modal */}
      <Modal visible={addMode === 'choose'} transparent animationType="fade">
        <TouchableOpacity style={styles.modalOverlay} activeOpacity={1} onPress={resetModal}>
          <View style={styles.chooseSheet}>
            <Text style={styles.chooseTitle}>Add Task</Text>
            <TouchableOpacity style={styles.chooseOption} onPress={() => setAddMode('manual')}>
              <Text style={styles.chooseOptionTitle}>Quick Task</Text>
              <Text style={styles.chooseOptionDesc}>Add a card to track manually</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.chooseOption} onPress={() => setAddMode('local')}>
              <Text style={styles.chooseOptionTitle}>New Claude Session</Text>
              <Text style={styles.chooseOptionDesc}>Start a local Claude Code session</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.chooseOption} onPress={() => setAddMode('cloud')}>
              <Text style={styles.chooseOptionTitle}>Link Cloud Session</Text>
              <Text style={styles.chooseOptionDesc}>Track a claude.ai conversation</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.cancelButton} onPress={resetModal}>
              <Text style={styles.cancelText}>Cancel</Text>
            </TouchableOpacity>
          </View>
        </TouchableOpacity>
      </Modal>

      {/* Quick Task Modal */}
      <Modal visible={addMode === 'manual'} transparent animationType="slide">
        <KeyboardAvoidingView
          style={styles.modalOverlay}
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        >
          <View style={styles.formSheet}>
            <Text style={styles.formTitle}>Quick Task</Text>
            <TextInput
              style={styles.formInput}
              value={newTitle}
              onChangeText={setNewTitle}
              placeholder="Task title..."
              placeholderTextColor="#6b7280"
              autoFocus
            />
            <View style={styles.formActions}>
              <TouchableOpacity style={styles.formCancel} onPress={resetModal}>
                <Text style={styles.cancelText}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.formSubmit, !newTitle.trim() && styles.formSubmitDisabled]}
                onPress={handleAddManualCard}
                disabled={!newTitle.trim()}
              >
                <Text style={styles.formSubmitText}>Create</Text>
              </TouchableOpacity>
            </View>
          </View>
        </KeyboardAvoidingView>
      </Modal>

      {/* New Local Session Modal */}
      <Modal visible={addMode === 'local'} transparent animationType="slide">
        <KeyboardAvoidingView
          style={styles.modalOverlay}
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        >
          <View style={styles.formSheet}>
            <Text style={styles.formTitle}>New Claude Session</Text>

            <Text style={styles.fieldLabel}>Name (optional)</Text>
            <TextInput
              style={styles.formInput}
              value={newTitle}
              onChangeText={setNewTitle}
              placeholder="e.g. Fix auth bug"
              placeholderTextColor="#6b7280"
            />

            <Text style={styles.fieldLabel}>Project Path</Text>
            <TextInput
              style={styles.formInput}
              value={newProjectPath}
              onChangeText={setNewProjectPath}
              placeholder="e.g. ~/projects/my-app"
              placeholderTextColor="#6b7280"
              autoCapitalize="none"
              autoCorrect={false}
            />

            <Text style={styles.fieldLabel}>Prompt</Text>
            <TextInput
              style={[styles.formInput, styles.promptInput]}
              value={newPrompt}
              onChangeText={setNewPrompt}
              placeholder="What should Claude work on?"
              placeholderTextColor="#6b7280"
              multiline
            />

            <View style={styles.formActions}>
              <TouchableOpacity style={styles.formCancel} onPress={resetModal}>
                <Text style={styles.cancelText}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.formSubmit, submitting && styles.formSubmitDisabled]}
                onPress={handleCreateLocal}
                disabled={submitting}
              >
                <Text style={styles.formSubmitText}>
                  {submitting ? 'Starting...' : 'Start'}
                </Text>
              </TouchableOpacity>
            </View>
          </View>
        </KeyboardAvoidingView>
      </Modal>

      {/* Link Cloud Session Modal */}
      <Modal visible={addMode === 'cloud'} transparent animationType="slide">
        <KeyboardAvoidingView
          style={styles.modalOverlay}
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        >
          <View style={styles.formSheet}>
            <Text style={styles.formTitle}>Link Cloud Session</Text>

            <Text style={styles.fieldLabel}>Name</Text>
            <TextInput
              style={styles.formInput}
              value={newTitle}
              onChangeText={setNewTitle}
              placeholder="e.g. iOS tracker session"
              placeholderTextColor="#6b7280"
            />

            <Text style={styles.fieldLabel}>Claude URL</Text>
            <TextInput
              style={styles.formInput}
              value={newUrl}
              onChangeText={setNewUrl}
              placeholder="https://claude.ai/chat/... or /code/..."
              placeholderTextColor="#6b7280"
              autoCapitalize="none"
              autoCorrect={false}
              keyboardType="url"
            />

            <View style={styles.formActions}>
              <TouchableOpacity style={styles.formCancel} onPress={resetModal}>
                <Text style={styles.cancelText}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.formSubmit, styles.cloudSubmit, submitting && styles.formSubmitDisabled]}
                onPress={handleLinkCloud}
                disabled={submitting}
              >
                <Text style={styles.formSubmitText}>
                  {submitting ? 'Linking...' : 'Link'}
                </Text>
              </TouchableOpacity>
            </View>
          </View>
        </KeyboardAvoidingView>
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
    fontSize: 24,
    fontWeight: '800',
  },
  addButton: {
    backgroundColor: '#3b82f6',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 10,
  },
  addButtonText: {
    color: '#fff',
    fontWeight: '700',
    fontSize: 14,
  },
  listContent: {
    paddingHorizontal: 16,
    paddingBottom: 30,
  },

  // Section headers
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    paddingHorizontal: 4,
    gap: 8,
    marginTop: 8,
  },
  sectionDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
  },
  sectionTitle: {
    color: '#e0e0e0',
    fontSize: 15,
    fontWeight: '700',
    flex: 1,
  },
  sectionCount: {
    backgroundColor: '#2a2a3e',
    borderRadius: 10,
    paddingHorizontal: 8,
    paddingVertical: 2,
  },
  sectionCountText: {
    color: '#9ca3af',
    fontSize: 12,
    fontWeight: '600',
  },
  collapseArrow: {
    color: '#6b7280',
    fontSize: 14,
    marginLeft: 4,
  },

  // Task cards
  card: {
    backgroundColor: '#1e1e2e',
    borderRadius: 12,
    padding: 14,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: '#2a2a3e',
  },
  cardTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 4,
  },
  cardTitle: {
    color: '#e0e0e0',
    fontSize: 15,
    fontWeight: '600',
    flex: 1,
  },
  cardPath: {
    color: '#6b7280',
    fontSize: 12,
    fontFamily: 'monospace',
    marginBottom: 4,
  },
  cardSummary: {
    color: '#9ca3af',
    fontSize: 13,
    lineHeight: 18,
    marginBottom: 4,
  },
  cardBottom: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 4,
  },
  cardMeta: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    flex: 1,
  },
  cardSource: {
    color: '#4b5563',
    fontSize: 11,
    textTransform: 'uppercase',
    fontWeight: '600',
  },
  cardBranch: {
    color: '#6b7280',
    fontSize: 11,
    fontFamily: 'monospace',
    flex: 1,
  },
  cardTime: {
    color: '#6b7280',
    fontSize: 12,
  },
  prTag: {
    marginTop: 6,
    backgroundColor: '#8b5cf620',
    borderColor: '#8b5cf6',
    borderWidth: 1,
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 6,
    alignSelf: 'flex-start',
  },
  prTagText: {
    color: '#8b5cf6',
    fontSize: 11,
    fontWeight: '700',
  },

  // Empty state
  emptyContainer: {
    padding: 40,
    alignItems: 'center',
  },
  emptyTitle: {
    color: '#9ca3af',
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 8,
  },
  emptyText: {
    color: '#6b7280',
    fontSize: 14,
    textAlign: 'center',
    lineHeight: 20,
  },

  // Setup state
  centered: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#0a0a1a',
    padding: 32,
  },
  setupTitle: {
    color: '#fff',
    fontSize: 24,
    fontWeight: '800',
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

  // Error banner
  errorBanner: {
    backgroundColor: '#ef444420',
    borderColor: '#ef4444',
    borderWidth: 1,
    marginHorizontal: 16,
    marginBottom: 10,
    padding: 10,
    borderRadius: 8,
  },
  errorText: {
    color: '#ef4444',
    fontSize: 13,
  },

  // Modal shared
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.7)',
    justifyContent: 'flex-end',
  },

  // Choose action sheet
  chooseSheet: {
    backgroundColor: '#1a1a2e',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    padding: 20,
    paddingBottom: 40,
  },
  chooseTitle: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '700',
    marginBottom: 16,
  },
  chooseOption: {
    backgroundColor: '#0d0d1a',
    borderRadius: 12,
    padding: 16,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: '#2a2a3e',
  },
  chooseOptionTitle: {
    color: '#e0e0e0',
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 4,
  },
  chooseOptionDesc: {
    color: '#6b7280',
    fontSize: 13,
  },

  // Form sheets
  formSheet: {
    backgroundColor: '#1a1a2e',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    padding: 20,
    paddingBottom: 40,
  },
  formTitle: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '700',
    marginBottom: 16,
  },
  fieldLabel: {
    color: '#9ca3af',
    fontSize: 13,
    fontWeight: '600',
    marginBottom: 6,
    marginTop: 8,
  },
  formInput: {
    backgroundColor: '#0d0d1a',
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#2a2a3e',
    paddingHorizontal: 14,
    paddingVertical: 10,
    color: '#e0e0e0',
    fontSize: 15,
  },
  promptInput: {
    minHeight: 80,
    textAlignVertical: 'top',
  },
  formActions: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    gap: 10,
    marginTop: 20,
  },
  formCancel: {
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#6b7280',
  },
  cancelButton: {
    alignItems: 'center',
    paddingVertical: 14,
    marginTop: 4,
  },
  cancelText: {
    color: '#9ca3af',
    fontWeight: '600',
    fontSize: 15,
  },
  formSubmit: {
    backgroundColor: '#3b82f6',
    borderRadius: 10,
    paddingHorizontal: 18,
    paddingVertical: 10,
  },
  cloudSubmit: {
    backgroundColor: '#8b5cf6',
  },
  formSubmitDisabled: {
    opacity: 0.4,
  },
  formSubmitText: {
    color: '#fff',
    fontWeight: '700',
    fontSize: 15,
  },
});
