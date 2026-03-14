/**
 * Handle incoming push notifications and deep linking.
 *
 * Pushover handles the actual push delivery.
 * This module provides in-app notification handling when the app is open.
 */

import { wsClient } from '../api/websocket';
import { WebSocketMessage } from '../models/types';

type NotificationCallback = (title: string, message: string, cardId?: string) => void;

let _callback: NotificationCallback | null = null;

/**
 * Register a callback to receive in-app notifications from WebSocket events.
 */
export function onNotification(callback: NotificationCallback) {
  _callback = callback;
}

/**
 * Start listening for WebSocket messages that should trigger in-app alerts.
 */
export function startNotificationListener() {
  wsClient.subscribe((msg: WebSocketMessage) => {
    if (!_callback) return;

    if (msg.type === 'card_updated') {
      const data = msg.data as any;
      if (data && data.status === 'waiting') {
        _callback(
          'Claude needs input',
          `${data.title || 'A session'} is waiting for your response.`,
          data.id
        );
      }
    }
  });
}
