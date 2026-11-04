import { Color } from 'expo-router';
import { Platform } from 'react-native';

import type { Kind } from '@/data';

export const colors = {
  label: Platform.select({
    ios: Color.ios.label,
    android: Color.android.dynamic.onSurface,
    default: '#000000',
  })!,
  secondaryLabel: Platform.select({
    ios: Color.ios.secondaryLabel,
    android: Color.android.dynamic.onSurfaceVariant,
    default: '#3c3c43',
  })!,
  separator: Platform.select({
    ios: Color.ios.separator,
    android: Color.android.dynamic.outlineVariant,
    default: '#c6c6c8',
  })!,
  background: Platform.select({
    ios: Color.ios.systemGroupedBackground,
    android: Color.android.dynamic.surface,
    default: '#f2f2f7',
  })!,
  card: Platform.select({
    ios: Color.ios.secondarySystemGroupedBackground,
    android: Color.android.dynamic.surfaceContainer,
    default: '#ffffff',
  })!,
  tint: Platform.select({
    ios: Color.ios.systemBlue,
    android: Color.android.dynamic.primary,
    default: '#007aff',
  })!,
  deadline: Platform.select({
    ios: Color.ios.systemOrange,
    android: Color.android.dynamic.tertiary,
    default: '#ff9500',
  })!,
  warning: Platform.select({
    ios: Color.ios.systemRed,
    android: Color.android.dynamic.error,
    default: '#ff3b30',
  })!,
  fill: Platform.select({
    ios: Color.ios.tertiarySystemFill,
    android: Color.android.dynamic.surfaceContainerHighest,
    default: '#e5e5ea',
  })!,
};

// Fixed tints that read on both light and dark cards.
export const kindColors: Record<Kind, { background: string; text: string }> = {
  hearing: { background: 'rgba(255, 149, 0, 0.18)', text: '#c26a00' },
  grant: { background: 'rgba(52, 199, 89, 0.18)', text: '#1f8a3e' },
  plan: { background: 'rgba(0, 122, 255, 0.16)', text: '#1a6fd6' },
  decision: { background: 'rgba(142, 142, 147, 0.2)', text: '#6e6e73' },
  info: { background: 'rgba(175, 82, 222, 0.16)', text: '#9440c2' },
};
