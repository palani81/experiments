/**
 * Settings screen — configure backend connection + view server logs.
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  Alert,
  ScrollView,
  RefreshControl,
} from 'react-native';
import { useSettingsStore } from '../stores/settingsStore';
import { checkHealth, fetchLogs, LogEntry } from '../api/client';

export function SettingsScreen() {
  const { serverUrl, authToken, setServer, isConfigured } = useSettingsStore();
  const [url, setUrl] = useState(serverUrl);
  const [token, setToken] = useState(authToken);
  const [testing, setTesting] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'unknown' | 'ok' | 'error'>('unknown');
  const [serverInfo, setServerInfo] = useState<any>(null);

  // Logs
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [logsLoading, setLogsLoading] = useState(false);
  const [showLogs, setShowLogs] = useState(false);

  useEffect(() => {
    setUrl(serverUrl);
    setToken(authToken);
  }, [serverUrl, authToken]);

  const handleSave = async () => {
    if (!url.trim() || !token.trim()) {
      Alert.alert('Error', 'Both server URL and auth token are required.');
      return;
    }
    await setServer(url.trim(), token.trim());
    Alert.alert('Saved', 'Settings saved successfully.');
  };

  const handleTestConnection = async () => {
    if (!url.trim() || !token.trim()) {
      Alert.alert('Error', 'Enter server URL and auth token first.');
      return;
    }

    await setServer(url.trim(), token.trim());

    setTesting(true);
    setConnectionStatus('unknown');
    try {
      const { ok, info } = await checkHealth();
      setConnectionStatus(ok ? 'ok' : 'error');
      setServerInfo(info || null);
      if (ok) {
        Alert.alert('Connected', `Backend v${info?.version || '?'} — ${info?.sessions || 0} sessions tracked.`);
      } else {
        Alert.alert('Failed', 'Could not connect to the backend. Check the URL and token.');
      }
    } catch {
      setConnectionStatus('error');
      Alert.alert('Error', 'Connection failed. Ensure the backend is running.');
    } finally {
      setTesting(false);
    }
  };

  const loadLogs = async () => {
    setLogsLoading(true);
    try {
      const data = await fetchLogs(200);
      setLogs(data);
    } catch {
      setLogs([]);
    } finally {
      setLogsLoading(false);
    }
  };

  const handleToggleLogs = () => {
    if (!showLogs) {
      loadLogs();
    }
    setShowLogs(!showLogs);
  };

  const getLevelColor = (level: string) => {
    switch (level) {
      case 'ERROR': return '#ef4444';
      case 'WARNING': return '#f59e0b';
      case 'INFO': return '#3b82f6';
      default: return '#6b7280';
    }
  };

  return (
    <ScrollView
      style={styles.container}
      refreshControl={
        showLogs ? (
          <RefreshControl refreshing={logsLoading} onRefresh={loadLogs} tintColor="#3b82f6" />
        ) : undefined
      }
    >
      <View style={styles.header}>
        <Text style={styles.title}>Settings</Text>
      </View>

      {/* Connection Section */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Backend Connection</Text>

        <Text style={styles.label}>Server URL</Text>
        <TextInput
          style={styles.input}
          value={url}
          onChangeText={setUrl}
          placeholder="http://192.168.1.100:8420"
          placeholderTextColor="#6b7280"
          autoCapitalize="none"
          autoCorrect={false}
          keyboardType="url"
        />

        <Text style={styles.label}>Auth Token</Text>
        <TextInput
          style={styles.input}
          value={token}
          onChangeText={setToken}
          placeholder="Your auth token from config.json"
          placeholderTextColor="#6b7280"
          autoCapitalize="none"
          autoCorrect={false}
          secureTextEntry
        />

        {connectionStatus !== 'unknown' && (
          <View
            style={[
              styles.statusBar,
              connectionStatus === 'ok' ? styles.statusOk : styles.statusError,
            ]}
          >
            <Text
              style={[
                styles.statusText,
                { color: connectionStatus === 'ok' ? '#10b981' : '#ef4444' },
              ]}
            >
              {connectionStatus === 'ok'
                ? `Connected${serverInfo ? ` — ${serverInfo.sessions || 0} sessions, dir: ${serverInfo.projects_dir || '?'}` : ''}`
                : 'Connection failed'}
            </Text>
          </View>
        )}

        <View style={styles.buttonRow}>
          <TouchableOpacity
            style={styles.testButton}
            onPress={handleTestConnection}
            disabled={testing}
          >
            <Text style={styles.testButtonText}>
              {testing ? 'Testing...' : 'Test Connection'}
            </Text>
          </TouchableOpacity>

          <TouchableOpacity style={styles.saveButton} onPress={handleSave}>
            <Text style={styles.saveButtonText}>Save</Text>
          </TouchableOpacity>
        </View>
      </View>

      {/* Server Logs Section */}
      <View style={styles.section}>
        <TouchableOpacity style={styles.logHeader} onPress={handleToggleLogs}>
          <Text style={styles.sectionTitle}>Server Logs</Text>
          <Text style={styles.logToggle}>{showLogs ? '▾ Hide' : '▸ Show'}</Text>
        </TouchableOpacity>

        {showLogs && (
          <View>
            <TouchableOpacity style={styles.refreshLogsButton} onPress={loadLogs}>
              <Text style={styles.refreshLogsText}>
                {logsLoading ? 'Loading...' : `Refresh (${logs.length} entries)`}
              </Text>
            </TouchableOpacity>

            {logs.length === 0 && !logsLoading && (
              <Text style={styles.noLogsText}>
                No logs available. Make sure the backend is running.
              </Text>
            )}

            {logs.slice().reverse().map((entry, i) => (
              <View key={i} style={styles.logEntry}>
                <View style={styles.logMeta}>
                  <Text style={[styles.logLevel, { color: getLevelColor(entry.level) }]}>
                    {entry.level}
                  </Text>
                  <Text style={styles.logTime}>
                    {new Date(entry.ts).toLocaleTimeString()}
                  </Text>
                </View>
                <Text style={styles.logMessage} selectable>
                  {entry.message}
                </Text>
              </View>
            ))}
          </View>
        )}
      </View>

      {/* About */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>About</Text>
        <Text style={styles.infoText}>
          Claude Code Tracker v1.0.0{'\n'}
          Track and manage your Claude Code sessions from your phone.
        </Text>
      </View>
    </ScrollView>
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
  section: {
    backgroundColor: '#1e1e2e',
    marginHorizontal: 16,
    marginBottom: 16,
    borderRadius: 14,
    padding: 16,
    borderWidth: 1,
    borderColor: '#2a2a3e',
  },
  sectionTitle: {
    color: '#e0e0e0',
    fontSize: 16,
    fontWeight: '700',
    marginBottom: 14,
  },
  label: {
    color: '#9ca3af',
    fontSize: 13,
    fontWeight: '600',
    marginBottom: 6,
  },
  input: {
    backgroundColor: '#0d0d1a',
    borderRadius: 10,
    padding: 12,
    color: '#e0e0e0',
    fontSize: 15,
    borderWidth: 1,
    borderColor: '#2a2a3e',
    marginBottom: 14,
  },
  statusBar: {
    padding: 8,
    borderRadius: 8,
    marginBottom: 14,
  },
  statusOk: {
    backgroundColor: '#10b98120',
    borderColor: '#10b981',
    borderWidth: 1,
  },
  statusError: {
    backgroundColor: '#ef444420',
    borderColor: '#ef4444',
    borderWidth: 1,
  },
  statusText: {
    fontSize: 12,
    fontWeight: '600',
  },
  buttonRow: {
    flexDirection: 'row',
    gap: 10,
  },
  testButton: {
    flex: 1,
    backgroundColor: '#2a2a3e',
    paddingVertical: 12,
    borderRadius: 10,
    alignItems: 'center',
  },
  testButtonText: {
    color: '#e0e0e0',
    fontWeight: '600',
    fontSize: 15,
  },
  saveButton: {
    flex: 1,
    backgroundColor: '#3b82f6',
    paddingVertical: 12,
    borderRadius: 10,
    alignItems: 'center',
  },
  saveButtonText: {
    color: '#fff',
    fontWeight: '600',
    fontSize: 15,
  },
  infoText: {
    color: '#9ca3af',
    fontSize: 13,
    lineHeight: 20,
  },

  // Logs
  logHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  logToggle: {
    color: '#3b82f6',
    fontSize: 13,
    fontWeight: '600',
    marginBottom: 14,
  },
  refreshLogsButton: {
    backgroundColor: '#0d0d1a',
    borderRadius: 8,
    padding: 10,
    marginBottom: 12,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#2a2a3e',
  },
  refreshLogsText: {
    color: '#3b82f6',
    fontSize: 13,
    fontWeight: '600',
  },
  noLogsText: {
    color: '#6b7280',
    fontSize: 13,
    textAlign: 'center',
    paddingVertical: 20,
  },
  logEntry: {
    marginBottom: 8,
    paddingBottom: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#0d0d1a',
  },
  logMeta: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 2,
  },
  logLevel: {
    fontSize: 10,
    fontWeight: '800',
    fontFamily: 'monospace',
  },
  logTime: {
    color: '#4b5563',
    fontSize: 10,
    fontFamily: 'monospace',
  },
  logMessage: {
    color: '#9ca3af',
    fontSize: 12,
    fontFamily: 'monospace',
    lineHeight: 16,
  },
});
