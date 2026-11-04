import * as Haptics from 'expo-haptics';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { useLanguage, type Lang } from '@/i18n';
import { colors } from '@/theme';

const OPTIONS: { lang: Lang; label: string }[] = [
  { lang: 'en', label: 'EN' },
  { lang: 'no', label: 'NO' },
];

/** Two-letter segmented switch in the header. */
export function LanguageToggle() {
  const { lang, setLang, t } = useLanguage();
  return (
    <View style={styles.track} accessibilityRole="radiogroup" accessibilityLabel={t.switchTo}>
      {OPTIONS.map((o) => {
        const active = o.lang === lang;
        return (
          <Pressable
            key={o.lang}
            accessibilityRole="radio"
            accessibilityState={{ selected: active }}
            hitSlop={6}
            onPress={() => {
              if (active) return;
              Haptics.selectionAsync();
              setLang(o.lang);
            }}
            style={[styles.segment, active && { backgroundColor: colors.tint }]}
          >
            <Text style={[styles.label, { color: active ? '#ffffff' : colors.secondaryLabel }]}>{o.label}</Text>
          </Pressable>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  track: { flexDirection: 'row', borderRadius: 8, padding: 2, gap: 2, backgroundColor: colors.fill },
  segment: { borderRadius: 6, paddingHorizontal: 9, paddingVertical: 4 },
  label: { fontSize: 13, fontWeight: '700' },
});
