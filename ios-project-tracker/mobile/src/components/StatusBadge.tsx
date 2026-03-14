/**
 * Visual status indicator badge for sessions.
 */

import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { SessionSource, SessionStatus, SESSION_STATUSES } from '../models/types';

interface StatusBadgeProps {
  status: SessionStatus;
  source?: SessionSource;
}

export function StatusBadge({ status, source }: StatusBadgeProps) {
  const info = SESSION_STATUSES.find((s) => s.key === status);
  const color = info?.color || '#6b7280';
  const label = info?.label || status;

  return (
    <View style={styles.container}>
      <View style={[styles.badge, { backgroundColor: color + '20', borderColor: color }]}>
        <View style={[styles.dot, { backgroundColor: color }]} />
        <Text style={[styles.text, { color }]}>{label}</Text>
      </View>
      {source === 'cloud' && (
        <View style={styles.cloudBadge}>
          <Text style={styles.cloudText}>Cloud</Text>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  badge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
    borderWidth: 1,
    gap: 5,
  },
  dot: {
    width: 6,
    height: 6,
    borderRadius: 3,
  },
  text: {
    fontSize: 12,
    fontWeight: '600',
  },
  cloudBadge: {
    backgroundColor: '#0ea5e920',
    borderColor: '#0ea5e9',
    borderWidth: 1,
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 8,
  },
  cloudText: {
    fontSize: 10,
    color: '#0ea5e9',
    fontWeight: '600',
  },
});
