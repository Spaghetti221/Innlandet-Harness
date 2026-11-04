import { StyleSheet, Text, View } from 'react-native';

import type { Kind } from '@/data';
import { useLanguage } from '@/i18n';
import { kindColors } from '@/theme';

export function KindBadge({ kind }: { kind: Kind }) {
  const { t } = useLanguage();
  return (
    <View style={[styles.badge, { backgroundColor: kindColors[kind].background }]}>
      <Text style={[styles.text, { color: kindColors[kind].text }]}>{t.kinds[kind]}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  badge: { alignSelf: 'flex-start', borderRadius: 6, paddingHorizontal: 8, paddingVertical: 3 },
  text: { fontSize: 12, fontWeight: '600' },
});
