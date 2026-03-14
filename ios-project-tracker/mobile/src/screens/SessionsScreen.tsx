/**
 * Main screen — all sessions grouped by status.
 * "Needs Reply" sessions are shown first with alert styling.
 */

import React, { useEffect, useState, useCallback, useRef } from 'react';
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
  Linking,
  AppState,
} from 'react-native';
import { useNavigation, useFocusEffect } from '@react-navigation/native';
import { Session, SessionStatus, SESSION_STATUSES } from '../models/types';
import { useSessionStore } from '../stores/sessionStore';
import { useSettingsStore } from '../stores/settingsStore';
import { StatusBadge } from '../components/StatusBadge';
import { createSession, addCloudSession } from '../api/client';

type AddMode = null | 'choose' | 'local' | 'cloud';

// Status display order: waiting first (needs attention), then active, then done
const STATUS_ORDER: SessionStatus[] = ['waiting', 'active', 'done'];

// Map backend status strings to our display statuses
function normalizeStatus(status: string | undefined): SessionStatus {
  if (!status) return 'active';
  const s = status.toLowerCase();
  if (s === 'waiting' || s === 'paused') return 'waiting';
  if (s === 'done' || s === 'completed' || s === 'finished') return 'done';
  return 'active'; // active, running, unknown — all show as active
}

function getTimeAgo(dateStr: string): string {
  const now = Date.now();
  const then = new Date(dateStr).getTime();
  const diff = Math.floor((now - then) / 1000);
  if (diff < 60) return 'just now';
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return `${Math.floor(diff / 86400)}d ago`;
}

function getLastMessage(session: Session): string | null {
  const messages = session.conversation;
  if (!messages || messages.length === 0) return null;
  const last = messages[messages.length - 1];
  if (!last?.content) return null;
  const content = last.content.slice(0, 80);
  return content + (last.content.length > 80 ? '...' : '');
}

export function SessionsScreen() {
  const navigation = useNavigation<any>();
  const { sessions, isLoading, error, loadSessions, connectWebSocket } = useSessionStore();
  const { isConfigured } = useSettingsStore();

  // Add modal state
  const [addMode, setAddMode] = useState<AddMode>(null);
  const [newName, setNewName] = useState('');
  const [newUrl, setNewUrl] = useState('');
  const [submitting, setSubmitting] = useState(false);

  // Done section collapsed by default
  const [doneCollapsed, setDoneCollapsed] = useState(true);

  // How far back to fetch sessions (days). 7 = recent, 0 = all time.
  const [showAllSessions, setShowAllSessions] = useState(false);
  const filterDays = showAllSessions ? 0 : 7;

  useEffect(() => {
    if (isConfigured) {
      loadSessions(filterDays);
      connectWebSocket();
    }
  }, [isConfigured, filterDays]);

  // Reload when screen comes into focus (returning from detail, switching tabs)
  useFocusEffect(
    useCallback(() => {
      if (isConfigured) loadSessions(filterDays);
    }, [isConfigured, filterDays])
  );

  // Auto-poll every 10s so new/updated sessions appear
  useEffect(() => {
    if (!isConfigured) return;
    const interval = setInterval(() => loadSessions(filterDays), 10000);
    return () => clearInterval(interval);
  }, [isConfigured, filterDays]);

  // Reload when app comes back to foreground
  useEffect(() => {
    const sub = AppState.addEventListener('change', (state) => {
      if (state === 'active' && isConfigured) loadSessions(filterDays);
    });
    return () => sub.remove();
  }, [isConfigured]);

  const resetModal = () => {
    setAddMode(null);
    setNewName('');
    setNewUrl('');
    Keyboard.dismiss();
  };

  const handleCreateLocal = async () => {
    const name = newName.trim() || 'New Session';
    setSubmitting(true);
    try {
      await createSession(name);
      resetModal();
      Alert.alert('Session Started', `"${name}" is running. It will appear here shortly.`);
      loadSessions(filterDays);
      setTimeout(() => loadSessions(filterDays), 3000);
      setTimeout(() => loadSessions(filterDays), 8000);
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
    const title = newName.trim() || 'Claude Conversation';
    const url = newUrl.trim();
    const urlParts = url.split('/');
    const sessionId = urlParts[urlParts.length - 1] || `conv-${Date.now()}`;

    setSubmitting(true);
    try {
      await addCloudSession(sessionId, title, url);
      resetModal();
      loadSessions(filterDays);
    } catch (e: any) {
      Alert.alert('Error', e?.response?.data?.detail || 'Failed to link conversation.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleSessionPress = (session: Session) => {
    if (session.source === 'cloud' && session.project_path?.startsWith('http')) {
      Linking.openURL(session.project_path);
      return;
    }
    navigation.navigate('SessionDetail', { sessionId: session.id, title: session.project_path });
  };

  // Build sections from sessions, normalizing backend statuses
  const sections = STATUS_ORDER.map((status) => {
    const statusInfo = SESSION_STATUSES.find((s) => s.key === status);
    const sectionSessions = sessions.filter((s) => normalizeStatus(s.status) === status);
    return {
      status,
      title: statusInfo?.label ?? status,
      color: statusInfo?.color ?? '#6b7280',
      data: status === 'done' && doneCollapsed ? [] : sectionSessions,
      count: sectionSessions.length,
      collapsed: status === 'done' && doneCollapsed,
    };
  }).filter((s) => s.count > 0);

  const waitingCount = sessions.filter((s) => normalizeStatus(s.status) === 'waiting').length;

  const renderSession = ({ item }: { item: Session }) => {
    const normalized = normalizeStatus(item.status);
    const isWaiting = normalized === 'waiting';
    const lastMsg = getLastMessage(item);

    return (
      <TouchableOpacity
        style={[styles.card, isWaiting && styles.cardWaiting]}
        onPress={() => handleSessionPress(item)}
        activeOpacity={0.7}
      >
        <View style={styles.cardTop}>
          <Text style={styles.cardTitle} numberOfLines={1}>
            {(item.id || 'unknown').slice(0, 16)}
          </Text>
          <StatusBadge status={normalized} source={item.source} />
        </View>
        <Text style={styles.cardPath} numberOfLines={1}>
          {item.project_path || ''}
        </Text>
        {lastMsg && (
          <Text style={styles.cardPreview} numberOfLines={2}>
            {lastMsg}
          </Text>
        )}
        {isWaiting && (
          <View style={styles.waitingBanner}>
            <Text style={styles.waitingBannerText}>Claude is waiting for your reply</Text>
          </View>
        )}
        <View style={styles.cardBottom}>
          <Text style={styles.cardMeta}>
            {(item.conversation?.length || 0)} messages
          </Text>
          <Text style={styles.cardTime}>{getTimeAgo(item.last_activity)}</Text>
        </View>
      </TouchableOpacity>
    );
  };

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
        <View style={styles.headerLeft}>
          <Text style={styles.title}>Sessions</Text>
          {waitingCount > 0 && (
            <View style={styles.waitingBadge}>
              <Text style={styles.waitingBadgeText}>{waitingCount}</Text>
            </View>
          )}
        </View>
        <TouchableOpacity style={styles.addButton} onPress={() => setAddMode('choose')}>
          <Text style={styles.addButtonText}>+ New</Text>
        </TouchableOpacity>
      </View>

      {/* Filter toggle */}
      <TouchableOpacity
        style={styles.filterToggle}
        onPress={() => setShowAllSessions((v) => !v)}
      >
        <Text style={styles.filterToggleText}>
          {showAllSessions ? 'Showing all sessions' : 'Last 7 days'}
        </Text>
        <Text style={styles.filterToggleAction}>
          {showAllSessions ? 'Show recent only' : 'Show all'}
        </Text>
      </TouchableOpacity>

      {error && (
        <View style={styles.errorBanner}>
          <Text style={styles.errorText}>{error}</Text>
        </View>
      )}

      {/* Session List */}
      <SectionList
        sections={sections}
        keyExtractor={(item) => item.id}
        renderItem={renderSession}
        renderSectionHeader={renderSectionHeader}
        refreshControl={
          <RefreshControl refreshing={isLoading} onRefresh={() => loadSessions(filterDays)} tintColor="#3b82f6" />
        }
        contentContainerStyle={[styles.listContent, sections.length === 0 && { flexGrow: 1 }]}
        stickySectionHeadersEnabled={false}
        ListEmptyComponent={
          <View style={styles.emptyContainer}>
            <Text style={styles.emptyTitle}>No sessions yet</Text>
            <Text style={styles.emptyText}>
              Tap "+ New" to start a Claude session or link a cloud conversation.
            </Text>
            <TouchableOpacity style={styles.refreshButton} onPress={() => loadSessions(filterDays)}>
              <Text style={styles.refreshButtonText}>
                {isLoading ? 'Loading...' : 'Refresh'}
              </Text>
            </TouchableOpacity>
          </View>
        }
      />

      {/* Choose Action Modal */}
      <Modal visible={addMode === 'choose'} transparent animationType="fade">
        <TouchableOpacity style={styles.modalOverlay} activeOpacity={1} onPress={resetModal}>
          <View style={styles.chooseSheet}>
            <Text style={styles.chooseTitle}>New Session</Text>
            <TouchableOpacity style={styles.chooseOption} onPress={() => setAddMode('local')}>
              <Text style={styles.chooseOptionTitle}>Start Local Session</Text>
              <Text style={styles.chooseOptionDesc}>Launch Claude Code on a local project</Text>
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

      {/* New Local Session Modal — just a name! */}
      <Modal visible={addMode === 'local'} transparent animationType="slide">
        <KeyboardAvoidingView
          style={styles.modalOverlay}
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        >
          <View style={styles.formSheet}>
            <Text style={styles.formTitle}>New Session</Text>
            <Text style={styles.formSubtitle}>
              Just give it a name. A project directory and prompt will be set up automatically.
            </Text>

            <TextInput
              style={styles.formInput}
              value={newName}
              onChangeText={setNewName}
              placeholder="e.g. Fix auth bug"
              placeholderTextColor="#6b7280"
              autoFocus
              returnKeyType="go"
              onSubmitEditing={handleCreateLocal}
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

            <Text style={styles.fieldLabel}>Name (optional)</Text>
            <TextInput
              style={styles.formInput}
              value={newName}
              onChangeText={setNewName}
              placeholder="e.g. iOS tracker session"
              placeholderTextColor="#6b7280"
            />

            <Text style={styles.fieldLabel}>Claude URL</Text>
            <TextInput
              style={styles.formInput}
              value={newUrl}
              onChangeText={setNewUrl}
              placeholder="https://claude.ai/chat/..."
              placeholderTextColor="#6b7280"
              autoCapitalize="none"
              autoCorrect={false}
              keyboardType="url"
              autoFocus
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
  headerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  title: {
    color: '#fff',
    fontSize: 24,
    fontWeight: '800',
  },
  waitingBadge: {
    backgroundColor: '#f59e0b',
    borderRadius: 12,
    minWidth: 24,
    height: 24,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 8,
  },
  waitingBadgeText: {
    color: '#000',
    fontSize: 13,
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

  // Session cards
  card: {
    backgroundColor: '#1e1e2e',
    borderRadius: 12,
    padding: 14,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: '#2a2a3e',
  },
  cardWaiting: {
    borderColor: '#f59e0b',
    borderWidth: 1.5,
    backgroundColor: '#f59e0b08',
  },
  cardTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 4,
  },
  cardTitle: {
    color: '#e0e0e0',
    fontSize: 14,
    fontWeight: '600',
    fontFamily: 'monospace',
    flex: 1,
    marginRight: 8,
  },
  cardPath: {
    color: '#6b7280',
    fontSize: 12,
    fontFamily: 'monospace',
    marginBottom: 4,
  },
  cardPreview: {
    color: '#9ca3af',
    fontSize: 13,
    lineHeight: 18,
    marginBottom: 4,
  },
  waitingBanner: {
    backgroundColor: '#f59e0b20',
    borderRadius: 6,
    paddingHorizontal: 10,
    paddingVertical: 6,
    marginBottom: 6,
    marginTop: 2,
  },
  waitingBannerText: {
    color: '#f59e0b',
    fontSize: 12,
    fontWeight: '700',
  },
  cardBottom: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 4,
  },
  cardMeta: {
    color: '#4b5563',
    fontSize: 12,
  },
  cardTime: {
    color: '#6b7280',
    fontSize: 12,
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
  refreshButton: {
    marginTop: 20,
    backgroundColor: '#1e1e2e',
    paddingHorizontal: 24,
    paddingVertical: 10,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#2a2a3e',
  },
  refreshButtonText: {
    color: '#3b82f6',
    fontWeight: '600',
    fontSize: 14,
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

  // Filter toggle
  filterToggle: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginHorizontal: 16,
    marginBottom: 8,
    paddingHorizontal: 12,
    paddingVertical: 8,
    backgroundColor: '#1e1e2e',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#2a2a3e',
  },
  filterToggleText: {
    color: '#6b7280',
    fontSize: 12,
  },
  filterToggleAction: {
    color: '#3b82f6',
    fontSize: 12,
    fontWeight: '600',
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
    marginBottom: 4,
  },
  formSubtitle: {
    color: '#6b7280',
    fontSize: 13,
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
