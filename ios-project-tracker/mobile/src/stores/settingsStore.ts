/**
 * Settings store — persists backend URL and auth token.
 */

import { create } from 'zustand';
import AsyncStorage from '@react-native-async-storage/async-storage';

interface SettingsState {
  serverUrl: string;
  authToken: string;
  isConfigured: boolean;
  setServer: (url: string, token: string) => void;
  loadSettings: () => Promise<void>;
}

export const useSettingsStore = create<SettingsState>((set) => ({
  serverUrl: '',
  authToken: '',
  isConfigured: false,

  setServer: async (url: string, token: string) => {
    const serverUrl = url.replace(/\/+$/, ''); // Remove trailing slashes
    await AsyncStorage.setItem('serverUrl', serverUrl);
    await AsyncStorage.setItem('authToken', token);
    set({ serverUrl, authToken: token, isConfigured: true });
  },

  loadSettings: async () => {
    const serverUrl = await AsyncStorage.getItem('serverUrl');
    const authToken = await AsyncStorage.getItem('authToken');
    if (serverUrl && authToken) {
      set({ serverUrl, authToken, isConfigured: true });
    }
  },
}));
