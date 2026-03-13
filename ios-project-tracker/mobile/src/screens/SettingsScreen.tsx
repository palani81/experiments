/**
 * Settings screen — configure backend connection and preferences.
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
} from 'react-native';
import { useSettingsStore } from '../stores/settingsStore';
import { checkHealth } from '../api/client';

export function SettingsScreen() {
  const { serverUrl, authToken, setServer, isConfigured } = useSettingsStore();
  const [url, setUrl] = useState(serverUrl);
  const [token, setToken] = useState(authToken);
  const [testing, setTesting] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'unknown' | 'ok' | 'error'>('unknown');

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

    // Temporarily set for testing
    await setServer(url.trim(), token.trim());

    setTesting(true);
    setConnectionStatus('unknown');
    try {
      const healthy = await checkHealth();
      setConnectionStatus(healthy ? 'ok' : 'error');
      if (healthy) {
        Alert.alert('Connected', 'Successfully connected to the backend.');
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

  return (
    <ScrollView style={styles.container}>
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
              {connectionStatus === 'ok' ? 'Connected' : 'Connection failed'}
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

      {/* Info Section */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Setup Guide</Text>
        <Text style={styles.infoText}>
          1. On your Mac mini, run the setup script:{'\n'}
          {'   '}cd ios-project-tracker/backend{'\n'}
          {'   '}bash scripts/setup.sh{'\n\n'}
          2. Start the backend:{'\n'}
          {'   '}python3 main.py{'\n\n'}
          3. Enter your Mac mini's IP address and the auth token shown during setup.{'\n\n'}
          4. For Pushover notifications, edit ~/.claude-tracker/config.json with your Pushover API
          keys.
        </Text>
      </View>

      {/* About */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>About</Text>
        <Text style={styles.infoText}>
          Claude Code Tracker v1.0.0{'\n'}
          Track and manage your Claude Code projects from your phone.
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
    fontSize: 13,
    fontWeight: '600',
    textAlign: 'center',
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
    fontFamily: 'monospace',
  },
});
