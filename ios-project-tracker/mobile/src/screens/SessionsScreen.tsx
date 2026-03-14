/**
 * Browse all discovered Claude Code sessions (local + cloud).
 * Supports creating new local sessions and adding cloud sessions.
 */

import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  RefreshControl,
  TextInput,
  Modal,
  Alert,
  KeyboardAvoidingView,
  Platform,
  Keyboard,
  Linking,
} from 'react-native';
import { Session } from '../models/types';
import { fetchSessions, createSession, addCloudSession, createCard } from '../api/client';
import { StatusBadge } from '../components/StatusBadge';
import { useSettingsStore } from '../stores/settingsStore';

type ModalType = null | 'local' | 'cloud';

export function SessionsScreen() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState('');
  const { isConfigured } = useSettingsStore();

  // Modal state
  const [modalType, setModalType] = useState<ModalType>(null);
  const [newTitle, setNewTitle] = useState('');
  const [newProjectPath, setNewProjectPath] = useState('');
  const [newPrompt, setNewPrompt] = useState('');
  const [newSessionId, setNewSessionId] = useState('');
  const [newUrl, setNewUrl] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const loadSessions = async () => {
    if (!isConfigured) return;
    setLoading(true);
    try {
      const data = await fetchSessions();
      setSessions(data);
    } catch {
      // Handle error silently
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSessions();
  }, [isConfigured]);

  const resetModal = () => {
    setModalType(null);
    setNewTitle('');
    setNewProjectPath('');
    setNewPrompt('');
    setNewSessionId('');
    setNewUrl('');
    Keyboard.dismiss();
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
      Alert.alert('Session Started', 'A new Claude session has been kicked off. It will appear here shortly.');
      // Refresh after a short delay to give the monitor time to pick it up
      setTimeout(loadSessions, 5000);
    } catch (e: any) {
      Alert.alert('Error', e?.response?.data?.detail || 'Failed to start session.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleAddConversation = async () => {
    if (!newUrl.trim()) {
      Alert.alert('Missing fields', 'Please paste the Claude conversation URL.');
      return;
    }
    const title = newTitle.trim() || 'Claude Conversation';
    const url = newUrl.trim();

    // Try to extract a session/conversation ID from the URL
    const urlParts = url.split('/');
    const sessionId = newSessionId.trim() || urlParts[urlParts.length - 1] || `conv-${Date.now()}`;

    setSubmitting(true);
    try {
      // Register as a cloud session so it shows in the sessions list
      await addCloudSession(sessionId, title, url);
      // Also create a card on the board with a link to open the conversation
      await createCard({ title, status: 'in_progress', source: 'cloud', pr_url: url });
      resetModal();
      loadSessions();
    } catch (e: any) {
      Alert.alert('Error', e?.response?.data?.detail || 'Failed to add conversation.');
    } finally {
      setSubmitting(false);
    }
  };

  const filteredSessions = sessions.filter((s) => {
    const term = search.toLowerCase();
    return (
      s.id.toLowerCase().includes(term) ||
      s.project_path.toLowerCase().includes(term) ||
      s.status.toLowerCase().includes(term)
    );
  });

  const handleSessionPress = (item: Session) => {
    // Cloud sessions with a URL open in the browser
    if (item.source === 'cloud' && item.project_path.startsWith('http')) {
      Linking.openURL(item.project_path);
    }
  };

  const renderSession = ({ item }: { item: Session }) => (
    <TouchableOpacity style={styles.sessionItem} onPress={() => handleSessionPress(item)}>
      <View style={styles.sessionHeader}>
        <Text style={styles.sessionId} numberOfLines={1}>
          {item.id.slice(0, 12)}...
        </Text>
        <View style={styles.badgeRow}>
          <StatusBadge
            status={item.status === 'active' ? 'in_progress' : item.status === 'waiting' ? 'waiting' : 'backlog'}
            source={item.source}
          />
          {item.source === 'cloud' && (
            <View style={styles.cloudBadge}>
              <Text style={styles.cloudBadgeText}>Cloud</Text>
            </View>
          )}
        </View>
      </View>
      <Text style={styles.projectPath} numberOfLines={1}>
        {item.source === 'cloud' && item.project_path.startsWith('http')
          ? item.project_path
          : item.project_path}
      </Text>
      <View style={styles.sessionFooter}>
        <Text style={styles.messageCount}>
          {item.conversation.length} messages
        </Text>
        <Text style={styles.lastActivity}>
          {new Date(item.last_activity).toLocaleDateString()}
        </Text>
      </View>
    </TouchableOpacity>
  );

  if (!isConfigured) {
    return (
      <View style={styles.centered}>
        <Text style={styles.notConfigured}>Configure your server in Settings first.</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Sessions</Text>
        <View style={styles.headerButtons}>
          <TouchableOpacity
            style={styles.addButton}
            onPress={() => setModalType('local')}
          >
            <Text style={styles.addButtonText}>+ Local</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.addButton, styles.cloudButton]}
            onPress={() => setModalType('cloud')}
          >
            <Text style={styles.addButtonText}>+ Link</Text>
          </TouchableOpacity>
        </View>
      </View>

      <TextInput
        style={styles.searchInput}
        value={search}
        onChangeText={setSearch}
        placeholder="Search sessions..."
        placeholderTextColor="#6b7280"
      />

      <FlatList
        data={filteredSessions}
        keyExtractor={(item) => item.id}
        renderItem={renderSession}
        refreshControl={
          <RefreshControl refreshing={loading} onRefresh={loadSessions} tintColor="#3b82f6" />
        }
        contentContainerStyle={styles.list}
        ListEmptyComponent={
          <Text style={styles.emptyText}>
            {loading ? 'Loading sessions...' : 'No sessions found. Tap + to start one.'}
          </Text>
        }
      />

      {/* New Local Session Modal */}
      <Modal visible={modalType === 'local'} animationType="slide" transparent>
        <KeyboardAvoidingView
          style={styles.modalOverlay}
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        >
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>New Local Session</Text>

            <Text style={styles.fieldLabel}>Name (optional)</Text>
            <TextInput
              style={styles.modalInput}
              value={newTitle}
              onChangeText={setNewTitle}
              placeholder="e.g. Fix auth bug"
              placeholderTextColor="#6b7280"
            />

            <Text style={styles.fieldLabel}>Project Path</Text>
            <TextInput
              style={styles.modalInput}
              value={newProjectPath}
              onChangeText={setNewProjectPath}
              placeholder="e.g. ~/projects/my-app"
              placeholderTextColor="#6b7280"
              autoCapitalize="none"
              autoCorrect={false}
            />

            <Text style={styles.fieldLabel}>Prompt</Text>
            <TextInput
              style={[styles.modalInput, styles.promptInput]}
              value={newPrompt}
              onChangeText={setNewPrompt}
              placeholder="What should Claude work on?"
              placeholderTextColor="#6b7280"
              multiline
            />

            <View style={styles.modalActions}>
              <TouchableOpacity style={styles.cancelButton} onPress={resetModal}>
                <Text style={styles.cancelText}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.submitButton, submitting && styles.submitDisabled]}
                onPress={handleCreateLocal}
                disabled={submitting}
              >
                <Text style={styles.submitText}>{submitting ? 'Starting...' : 'Start Session'}</Text>
              </TouchableOpacity>
            </View>
          </View>
        </KeyboardAvoidingView>
      </Modal>

      {/* Add Conversation Link Modal */}
      <Modal visible={modalType === 'cloud'} animationType="slide" transparent>
        <KeyboardAvoidingView
          style={styles.modalOverlay}
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        >
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>Link Claude Conversation</Text>
            <Text style={styles.modalSubtitle}>
              Paste a claude.ai conversation or code session URL to track it on your board.
            </Text>

            <Text style={styles.fieldLabel}>Name</Text>
            <TextInput
              style={styles.modalInput}
              value={newTitle}
              onChangeText={setNewTitle}
              placeholder="e.g. iOS tracker app session"
              placeholderTextColor="#6b7280"
            />

            <Text style={styles.fieldLabel}>Claude URL</Text>
            <TextInput
              style={styles.modalInput}
              value={newUrl}
              onChangeText={setNewUrl}
              placeholder="https://claude.ai/chat/... or /code/..."
              placeholderTextColor="#6b7280"
              autoCapitalize="none"
              autoCorrect={false}
              keyboardType="url"
            />

            <View style={styles.modalActions}>
              <TouchableOpacity style={styles.cancelButton} onPress={resetModal}>
                <Text style={styles.cancelText}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.submitButton, styles.cloudSubmitButton, submitting && styles.submitDisabled]}
                onPress={handleAddConversation}
                disabled={submitting}
              >
                <Text style={styles.submitText}>{submitting ? 'Adding...' : 'Link'}</Text>
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
    paddingHorizontal: 16,
    paddingTop: 60,
    paddingBottom: 12,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  title: {
    color: '#fff',
    fontSize: 22,
    fontWeight: '800',
  },
  headerButtons: {
    flexDirection: 'row',
    gap: 8,
  },
  addButton: {
    backgroundColor: '#3b82f6',
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 6,
  },
  cloudButton: {
    backgroundColor: '#8b5cf6',
  },
  addButtonText: {
    color: '#fff',
    fontWeight: '700',
    fontSize: 13,
  },
  searchInput: {
    backgroundColor: '#1e1e2e',
    borderRadius: 10,
    paddingHorizontal: 14,
    paddingVertical: 10,
    marginHorizontal: 16,
    marginBottom: 12,
    color: '#e0e0e0',
    fontSize: 15,
    borderWidth: 1,
    borderColor: '#2a2a3e',
  },
  list: {
    paddingHorizontal: 16,
    paddingBottom: 20,
  },
  sessionItem: {
    backgroundColor: '#1e1e2e',
    borderRadius: 12,
    padding: 14,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: '#2a2a3e',
  },
  sessionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 6,
  },
  sessionId: {
    color: '#e0e0e0',
    fontSize: 14,
    fontFamily: 'monospace',
    fontWeight: '600',
    flex: 1,
    marginRight: 8,
  },
  projectPath: {
    color: '#6b7280',
    fontSize: 12,
    fontFamily: 'monospace',
    marginBottom: 8,
  },
  badgeRow: {
    flexDirection: 'row',
    gap: 6,
    alignItems: 'center',
  },
  sessionFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  messageCount: {
    color: '#9ca3af',
    fontSize: 12,
  },
  lastActivity: {
    color: '#6b7280',
    fontSize: 12,
  },
  cloudBadge: {
    backgroundColor: '#8b5cf620',
    borderColor: '#8b5cf6',
    borderWidth: 1,
    borderRadius: 6,
    paddingHorizontal: 6,
    paddingVertical: 2,
  },
  cloudBadgeText: {
    color: '#8b5cf6',
    fontSize: 10,
    fontWeight: '700',
  },
  centered: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#0a0a1a',
  },
  notConfigured: {
    color: '#6b7280',
    fontSize: 14,
  },
  emptyText: {
    color: '#6b7280',
    fontSize: 14,
    textAlign: 'center',
    marginTop: 40,
  },
  // Modal styles
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.7)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: '#1a1a2e',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    padding: 20,
    paddingBottom: 40,
  },
  modalTitle: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '700',
    marginBottom: 4,
  },
  modalSubtitle: {
    color: '#6b7280',
    fontSize: 13,
    marginBottom: 12,
  },
  fieldLabel: {
    color: '#9ca3af',
    fontSize: 13,
    fontWeight: '600',
    marginBottom: 6,
    marginTop: 8,
  },
  modalInput: {
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
  modalActions: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    gap: 10,
    marginTop: 20,
  },
  cancelButton: {
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#6b7280',
  },
  cancelText: {
    color: '#9ca3af',
    fontWeight: '600',
    fontSize: 15,
  },
  submitButton: {
    backgroundColor: '#3b82f6',
    borderRadius: 10,
    paddingHorizontal: 18,
    paddingVertical: 10,
  },
  cloudSubmitButton: {
    backgroundColor: '#8b5cf6',
  },
  submitDisabled: {
    backgroundColor: '#3b82f640',
  },
  submitText: {
    color: '#fff',
    fontWeight: '700',
    fontSize: 15,
  },
});
