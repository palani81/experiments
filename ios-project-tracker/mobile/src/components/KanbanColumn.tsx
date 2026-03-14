/**
 * Single kanban column displaying cards of a specific status.
 */

import React from 'react';
import { View, Text, StyleSheet, ScrollView } from 'react-native';
import { Card, CardStatus, KANBAN_COLUMNS } from '../models/types';
import { CardItem } from './CardItem';

interface KanbanColumnProps {
  status: CardStatus;
  cards: Card[];
  onCardPress: (card: Card) => void;
}

export function KanbanColumn({ status, cards, onCardPress }: KanbanColumnProps) {
  const column = KANBAN_COLUMNS.find((c) => c.key === status);
  const color = column?.color || '#6b7280';
  const label = column?.label || status;

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <View style={[styles.headerDot, { backgroundColor: color }]} />
        <Text style={styles.headerTitle}>{label}</Text>
        <View style={styles.countBadge}>
          <Text style={styles.countText}>{cards.length}</Text>
        </View>
      </View>

      <ScrollView style={styles.cardList} showsVerticalScrollIndicator={false}>
        {cards.length === 0 ? (
          <View style={styles.empty}>
            <Text style={styles.emptyText}>No cards</Text>
          </View>
        ) : (
          cards.map((card) => (
            <CardItem key={card.id} card={card} onPress={onCardPress} />
          ))
        )}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    width: 300,
    marginRight: 14,
    backgroundColor: '#13131f',
    borderRadius: 14,
    padding: 12,
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
    gap: 8,
  },
  headerDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
  },
  headerTitle: {
    color: '#e0e0e0',
    fontSize: 16,
    fontWeight: '700',
    flex: 1,
  },
  countBadge: {
    backgroundColor: '#2a2a3e',
    borderRadius: 10,
    paddingHorizontal: 8,
    paddingVertical: 2,
  },
  countText: {
    color: '#9ca3af',
    fontSize: 12,
    fontWeight: '600',
  },
  cardList: {
    flex: 1,
  },
  empty: {
    padding: 20,
    alignItems: 'center',
  },
  emptyText: {
    color: '#4b5563',
    fontSize: 14,
  },
});
