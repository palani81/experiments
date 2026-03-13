/**
 * Claude Code Tracker — Root App with bottom tab navigation.
 */

import React, { useEffect } from 'react';
import { StatusBar } from 'expo-status-bar';
import { NavigationContainer, DefaultTheme } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { Text } from 'react-native';

import { BoardScreen } from './src/screens/BoardScreen';
import { SessionsScreen } from './src/screens/SessionsScreen';
import { SettingsScreen } from './src/screens/SettingsScreen';
import { CardDetailScreen } from './src/screens/CardDetailScreen';
import { useSettingsStore } from './src/stores/settingsStore';

const Tab = createBottomTabNavigator();
const Stack = createNativeStackNavigator();

const DarkTheme = {
  ...DefaultTheme,
  colors: {
    ...DefaultTheme.colors,
    primary: '#3b82f6',
    background: '#0a0a1a',
    card: '#13131f',
    text: '#e0e0e0',
    border: '#2a2a3e',
    notification: '#ef4444',
  },
};

function TabIcon({ label, focused }: { label: string; focused: boolean }) {
  const icons: Record<string, string> = {
    Board: 'B',
    Sessions: 'S',
    Settings: 'G',
  };
  return (
    <Text
      style={{
        color: focused ? '#3b82f6' : '#6b7280',
        fontSize: 18,
        fontWeight: focused ? '800' : '400',
      }}
    >
      {icons[label] || label[0]}
    </Text>
  );
}

function BoardStack() {
  return (
    <Stack.Navigator
      screenOptions={{
        headerShown: false,
        contentStyle: { backgroundColor: '#0a0a1a' },
      }}
    >
      <Stack.Screen name="BoardMain" component={BoardScreen} />
      <Stack.Screen
        name="CardDetail"
        component={CardDetailScreen}
        options={{
          headerShown: true,
          headerTitle: 'Card Detail',
          headerStyle: { backgroundColor: '#13131f' },
          headerTintColor: '#e0e0e0',
        }}
      />
    </Stack.Navigator>
  );
}

export default function App() {
  const { loadSettings } = useSettingsStore();

  useEffect(() => {
    loadSettings();
  }, []);

  return (
    <NavigationContainer theme={DarkTheme}>
      <StatusBar style="light" />
      <Tab.Navigator
        screenOptions={({ route }) => ({
          headerShown: false,
          tabBarStyle: {
            backgroundColor: '#13131f',
            borderTopColor: '#2a2a3e',
            paddingBottom: 6,
            height: 56,
          },
          tabBarActiveTintColor: '#3b82f6',
          tabBarInactiveTintColor: '#6b7280',
          tabBarIcon: ({ focused }) => <TabIcon label={route.name} focused={focused} />,
        })}
      >
        <Tab.Screen name="Board" component={BoardStack} />
        <Tab.Screen name="Sessions" component={SessionsScreen} />
        <Tab.Screen name="Settings" component={SettingsScreen} />
      </Tab.Navigator>
    </NavigationContainer>
  );
}
