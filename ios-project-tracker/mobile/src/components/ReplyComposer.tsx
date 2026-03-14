/**
 * Text input component for replying to Claude sessions.
 */

import React, { useRef, useState } from 'react';
import {
  View,
  TextInput,
  TouchableOpacity,
  Text,
  StyleSheet,
  ActivityIndicator,
  Keyboard,
} from 'react-native';

interface ReplyComposerProps {
  onSend: (message: string) => Promise<void>;
  placeholder?: string;
}

export function ReplyComposer({
  onSend,
  placeholder = 'Reply to Claude...',
}: ReplyComposerProps) {
  const [text, setText] = useState('');
  const [sending, setSending] = useState(false);
  const inputRef = useRef<TextInput>(null);

  const handleSend = async () => {
    const message = text.trim();
    if (!message || sending) return;

    Keyboard.dismiss();
    setSending(true);
    try {
      await onSend(message);
      setText('');
    } catch {
      // Error handling is done in the parent
    } finally {
      setSending(false);
    }
  };

  return (
    <View style={styles.container}>
      <View style={styles.inputRow}>
        <TextInput
          ref={inputRef}
          style={styles.input}
          value={text}
          onChangeText={setText}
          placeholder={placeholder}
          placeholderTextColor="#6b7280"
          multiline
          maxLength={5000}
          editable={!sending}
        />
        <TouchableOpacity
          style={[
            styles.sendButton,
            (!text.trim() || sending) && styles.sendButtonDisabled,
          ]}
          onPress={handleSend}
          disabled={!text.trim() || sending}
        >
          {sending ? (
            <ActivityIndicator size="small" color="#fff" />
          ) : (
            <Text style={styles.sendText}>Send</Text>
          )}
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    borderTopWidth: 1,
    borderTopColor: '#2a2a3e',
    backgroundColor: '#0d0d1a',
    padding: 12,
  },
  inputRow: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    gap: 10,
  },
  input: {
    flex: 1,
    backgroundColor: '#1e1e2e',
    borderRadius: 12,
    paddingHorizontal: 14,
    paddingVertical: 10,
    color: '#e0e0e0',
    fontSize: 15,
    maxHeight: 120,
    borderWidth: 1,
    borderColor: '#2a2a3e',
  },
  sendButton: {
    backgroundColor: '#3b82f6',
    borderRadius: 12,
    paddingHorizontal: 18,
    paddingVertical: 10,
    justifyContent: 'center',
    alignItems: 'center',
  },
  sendButtonDisabled: {
    backgroundColor: '#3b82f640',
  },
  sendText: {
    color: '#fff',
    fontWeight: '600',
    fontSize: 15,
  },
});
