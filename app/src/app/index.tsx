import * as Haptics from 'expo-haptics';
import { Link, Stack } from 'expo-router';
import { useMemo, useState } from 'react';
import { Pressable, ScrollView, SectionList, StyleSheet, Text, View, useColorScheme } from 'react-native';

import { KindBadge } from '@/components/kind-badge';
import { KINDS, daysLeft, formatDate, hasOpenDeadline, notices, summaryFor, type Kind, type Notice } from '@/data';
import { useLanguage } from '@/i18n';
import { colors } from '@/theme';

export default function HomeScreen() {
  useColorScheme();
  const { t, lang } = useLanguage();
  const [query, setQuery] = useState('');
  const [kind, setKind] = useState<Kind | null>(null);

  // Only offer the types that actually occur.
  const kinds = KINDS.filter((k) => notices.some((n) => n.kind === k));

  const sections = useMemo(() => {
    const q = query.trim().toLowerCase();
    const hits = notices.filter((n) => {
      if (kind && n.kind !== kind) return false;
      if (!q) return true;
      const bullets = summaryFor(n, lang).summary?.bullets ?? [];
      return (
        n.title.toLowerCase().includes(q) ||
        t.kinds[n.kind].toLowerCase().includes(q) ||
        bullets.some((b) => [b.text, ...b.children].some((s) => s.toLowerCase().includes(q)))
      );
    });
    const open = hits.filter(hasOpenDeadline).sort((a, b) => a.deadline!.localeCompare(b.deadline!));
    const rest = hits.filter((n) => !hasOpenDeadline(n));
    return [
      { title: t.openDeadlines, data: open },
      { title: t.otherNotices, data: rest },
    ].filter((s) => s.data.length);
  }, [query, kind, lang, t]);

  return (
    <>
      <Stack.SearchBar placeholder={t.search} onChangeText={(e) => setQuery(e.nativeEvent.text)} />
      <SectionList
        style={{ backgroundColor: colors.background }}
        contentInsetAdjustmentBehavior="automatic"
        contentContainerStyle={styles.content}
        sections={sections}
        keyExtractor={(n) => n.slug}
        stickySectionHeadersEnabled={false}
        ListHeaderComponent={
          <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.chips}>
            {[null, ...kinds].map((k) => (
              <Chip
                key={k ?? 'all'}
                label={k ? t.kinds[k] : t.all}
                active={kind === k}
                onPress={() => {
                  Haptics.selectionAsync();
                  setKind(k);
                }}
              />
            ))}
          </ScrollView>
        }
        renderSectionHeader={({ section }) => <Text style={styles.sectionHeader}>{section.title}</Text>}
        renderItem={({ item }) => <Row notice={item} />}
        ItemSeparatorComponent={() => <View style={{ height: 10 }} />}
        ListEmptyComponent={<Text style={styles.empty}>{t.noMatches}</Text>}
      />
    </>
  );
}

function Chip({ label, active, onPress }: { label: string; active: boolean; onPress: () => void }) {
  return (
    <Pressable
      onPress={onPress}
      accessibilityRole="button"
      accessibilityState={{ selected: active }}
      style={[styles.chip, active && { backgroundColor: colors.tint }]}
    >
      <Text style={[styles.chipText, active && { color: '#ffffff' }]}>{label}</Text>
    </Pressable>
  );
}

function Row({ notice }: { notice: Notice }) {
  const { t, lang, locale } = useLanguage();
  const { summary } = summaryFor(notice, lang);
  const open = hasOpenDeadline(notice);
  const left = open ? daysLeft(notice.deadline!) : 0;
  const urgent = open && left <= 7;

  return (
    <Link href={{ pathname: '/[slug]', params: { slug: notice.slug } }}>
      <Link.Trigger>
        <Pressable style={({ pressed }) => [styles.card, pressed && { opacity: 0.7 }]}>
          <View style={styles.cardTop}>
            <KindBadge kind={notice.kind} />
            {open && (
              <Text style={[styles.countdown, { color: urgent ? colors.warning : colors.deadline }]}>
                {left === 0 ? t.dueToday : t.daysLeft(left)}
              </Text>
            )}
          </View>
          <Text style={styles.title} numberOfLines={3}>
            {notice.title}
          </Text>
          {summary?.bullets[0] && (
            <Text style={styles.preview} numberOfLines={2}>
              {summary.bullets[0].text}
            </Text>
          )}
          <View style={styles.meta}>
            <Text style={styles.metaText}>
              {open ? `${t.deadline} ${formatDate(notice.deadline!, locale)}` : formatDate(notice.published, locale)}
            </Text>
            {summary && !summary.passedCheck && (
              <Text style={[styles.metaText, { color: colors.warning }]}>{t.unchecked}</Text>
            )}
          </View>
        </Pressable>
      </Link.Trigger>
      <Link.Preview />
    </Link>
  );
}

const styles = StyleSheet.create({
  content: { paddingHorizontal: 16, paddingBottom: 40 },
  chips: { gap: 8, paddingVertical: 8 },
  chip: { borderRadius: 16, paddingHorizontal: 14, paddingVertical: 7, backgroundColor: colors.fill },
  chipText: { fontSize: 14, fontWeight: '600', color: colors.label },
  sectionHeader: {
    fontSize: 13,
    fontWeight: '600',
    textTransform: 'uppercase',
    color: colors.secondaryLabel,
    marginTop: 18,
    marginBottom: 8,
    marginLeft: 4,
  },
  card: { backgroundColor: colors.card, borderRadius: 14, borderCurve: 'continuous', padding: 14, gap: 8 },
  cardTop: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  countdown: { fontSize: 13, fontWeight: '700', fontVariant: ['tabular-nums'] },
  title: { fontSize: 17, fontWeight: '600', color: colors.label },
  preview: { fontSize: 15, lineHeight: 20, color: colors.secondaryLabel },
  meta: { flexDirection: 'row', gap: 12 },
  metaText: { fontSize: 13, color: colors.secondaryLabel, fontVariant: ['tabular-nums'] },
  empty: { textAlign: 'center', marginTop: 40, color: colors.secondaryLabel },
});
