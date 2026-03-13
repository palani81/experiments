/**
 * Card preview component shown in kanban columns.
 */

import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { Card } from '../models/types';
import { StatusBadge } from './StatusBadge';

interface CardItemProps {
  card: Card;
  onPress: (card: Card) => void;
}

export function CardItem({ card, onPress }: CardItemProps) {
  const timeAgo = getTimeAgo(card.last_activity);

  return (
    <TouchableOpacity
      style={styles.container}
      onPress={() => onPress(card)}
      activeOpacity={0.7}
    >
      <View style={styles.header}>
        <Text style={styles.title} numberOfLines={2}>
          {card.title}
        </Text>
        <StatusBadge status={card.status} source={card.source} />
      </View>

      {card.conversation_summary && (
        <Text style={styles.summary} numberOfLines={2}>
          {card.conversation_summary}
        </Text>
      )}

      <View style={styles.footer}>
        {card.branch && (
          <Text style={styles.branch} numberOfLines={1}>
            {card.branch}
          </Text>
        )}
        <Text style={styles.time}>{timeAgo}</Text>
      </View>

      {card.pr_url && (
        <View style={styles.prBadge}>
          <Text style={styles.prText}>PR Open</Text>
        </View>
      )}
    </TouchableOpacity>
  );
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

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#1e1e2e',
    borderRadius: 12,
    padding: 14,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: '#2a2a3e',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 8,
    gap: 8,
  },
  title: {
    color: '#e0e0e0',
    fontSize: 15,
    fontWeight: '600',
    flex: 1,
  },
  summary: {
    color: '#9ca3af',
    fontSize: 13,
    marginBottom: 8,
    lineHeight: 18,
  },
  footer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  branch: {
    color: '#6b7280',
    fontSize: 12,
    fontFamily: 'monospace',
    flex: 1,
  },
  time: {
    color: '#6b7280',
    fontSize: 12,
  },
  prBadge: {
    marginTop: 8,
    backgroundColor: '#8b5cf620',
    borderColor: '#8b5cf6',
    borderWidth: 1,
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 8,
    alignSelf: 'flex-start',
  },
  prText: {
    color: '#8b5cf6',
    fontSize: 11,
    fontWeight: '600',
  },
});
