/**
 * Browse all discovered Claude Code sessions.
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
} from 'react-native';
import { Session } from '../models/types';
import { fetchSessions } from '../api/client';
import { StatusBadge } from '../components/StatusBadge';
import { useSettingsStore } from '../stores/settingsStore';

export function SessionsScreen() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState('');
  const { isConfigured } = useSettingsStore();

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

  const filteredSessions = sessions.filter((s) => {
    const term = search.toLowerCase();
    return (
      s.id.toLowerCase().includes(term) ||
      s.project_path.toLowerCase().includes(term) ||
      s.status.toLowerCase().includes(term)
    );
  });

  const renderSession = ({ item }: { item: Session }) => (
    <TouchableOpacity style={styles.sessionItem}>
      <View style={styles.sessionHeader}>
        <Text style={styles.sessionId} numberOfLines={1}>
          {item.id.slice(0, 12)}...
        </Text>
        <StatusBadge
          status={item.status === 'active' ? 'in_progress' : item.status === 'waiting' ? 'waiting' : 'backlog'}
          source={item.source}
        />
      </View>
      <Text style={styles.projectPath} numberOfLines={1}>
        {item.project_path}
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
            {loading ? 'Loading sessions...' : 'No sessions found'}
          </Text>
        }
      />
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
  },
  title: {
    color: '#fff',
    fontSize: 22,
    fontWeight: '800',
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
  sessionFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  messageCount: {
    color: '#9ca3af',
    fontSize: 12,
  },
  lastActivity: {
    color: '#6b7280',
    fontSize: 12,
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
});
