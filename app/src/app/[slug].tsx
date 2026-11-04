import * as Haptics from 'expo-haptics';
import { useLocalSearchParams } from 'expo-router';
import * as WebBrowser from 'expo-web-browser';
import { useEffect, useState } from 'react';
import { Pressable, ScrollView, Share, StyleSheet, Text, View, useColorScheme } from 'react-native';

import { KindBadge } from '@/components/kind-badge';
import { daysLeft, formatDate, getNotice, hasOpenDeadline, summaryFor, type Notice } from '@/data';
import { useLanguage } from '@/i18n';
import { cancelReminder, hasReminder, reminderDate, scheduleReminder } from '@/reminders';
import { colors } from '@/theme';

export default function NoticeScreen() {
  useColorScheme();
  const { t, lang, locale } = useLanguage();
  const { slug } = useLocalSearchParams<{ slug: string }>();
  const notice = getNotice(slug);

  if (!notice) {
    return (
      <View style={[styles.screen, { padding: 24 }]}>
        <Text style={styles.body}>{t.notFound}</Text>
      </View>
    );
  }

  const { summary, fallback } = summaryFor(notice, lang);

  return (
    <ScrollView style={styles.screen} contentInsetAdjustmentBehavior="automatic" contentContainerStyle={styles.content}>
      <View style={{ gap: 10 }}>
        <KindBadge kind={notice.kind} />
        <Text style={styles.heading} selectable>
          {notice.title}
        </Text>
        <Text style={styles.subtle}>
          {t.published} {formatDate(notice.published, locale)}
        </Text>
      </View>

      {notice.deadline && <DeadlineCard notice={notice} />}

      {fallback && <Text style={styles.note}>{t.otherLanguageOnly}</Text>}
      {summary && !summary.passedCheck && (
        <Text style={[styles.note, { color: colors.warning }]} selectable>
          {t.failedCheck}
        </Text>
      )}
      {summary?.truncated && <Text style={styles.note}>{t.truncated}</Text>}

      {summary && (
        <View style={[styles.card, { gap: 14 }]}>
          {summary.bullets.map((b, i) => (
            <View key={i} style={{ gap: 6 }}>
              <View style={styles.bulletRow}>
                <Text style={styles.dot}>•</Text>
                <Text style={styles.body} selectable>
                  {b.text}
                </Text>
              </View>
              {b.children.map((c, j) => (
                <View key={j} style={[styles.bulletRow, { paddingLeft: 18 }]}>
                  <Text style={styles.dot}>◦</Text>
                  <Text style={[styles.body, { color: colors.secondaryLabel }]} selectable>
                    {c}
                  </Text>
                </View>
              ))}
            </View>
          ))}
        </View>
      )}

      <View style={{ gap: 10 }}>
        <Pressable
          style={({ pressed }) => [styles.primaryButton, pressed && { opacity: 0.7 }]}
          onPress={() => WebBrowser.openBrowserAsync(notice.url)}
        >
          <Text style={styles.primaryButtonText}>{t.readOriginal}</Text>
        </Pressable>
        <Pressable
          style={({ pressed }) => [styles.secondaryButton, pressed && { opacity: 0.7 }]}
          onPress={() => Share.share({ message: `${notice.title}\n${notice.url}` })}
        >
          <Text style={styles.secondaryButtonText}>{t.share}</Text>
        </Pressable>
      </View>

      <Text style={styles.footer}>
        {t.disclaimer}
        {summary ? ` (${summary.model})` : ''}
        {notice.expires ? `\n${t.pageExpires} ${formatDate(notice.expires, locale)}.` : ''}
      </Text>
    </ScrollView>
  );
}

function DeadlineCard({ notice }: { notice: Notice }) {
  const { t, locale } = useLanguage();
  const deadline = notice.deadline!;
  const open = hasOpenDeadline(notice);
  const left = daysLeft(deadline);
  const when = reminderDate(deadline);
  const [reminder, setReminder] = useState(false);
  const [blocked, setBlocked] = useState(false);

  useEffect(() => {
    hasReminder(notice.slug).then(setReminder);
  }, [notice.slug]);

  const toggle = async () => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    if (reminder) {
      await cancelReminder(notice.slug);
      setReminder(false);
      return;
    }
    const ok = await scheduleReminder(
      notice,
      t.reminderTitle,
      t.reminderBody(notice.title, formatDate(deadline, locale)),
    );
    setBlocked(!ok);
    setReminder(ok);
    if (ok) Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
  };

  const whenText =
    when && when.toLocaleString(locale, { weekday: 'short', day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' });

  return (
    <View style={[styles.card, styles.deadlineCard, !open && { opacity: 0.6 }]}>
      <Text style={styles.deadlineLabel}>{t.deadline}</Text>
      <Text style={styles.deadlineDate} selectable>
        {formatDate(deadline, locale)}
      </Text>
      <Text style={[styles.deadlineLeft, { color: open && left <= 7 ? colors.warning : colors.deadline }]}>
        {!open ? t.passed : left === 0 ? t.dueToday : t.daysLeft(left)}
      </Text>
      {open && when && (
        <Pressable
          onPress={toggle}
          accessibilityRole="switch"
          accessibilityState={{ checked: reminder }}
          style={({ pressed }) => [styles.reminderButton, reminder && styles.reminderOn, pressed && { opacity: 0.7 }]}
        >
          <Text style={[styles.reminderText, reminder && { color: colors.label }]}>
            {reminder ? `✓ ${t.reminderSet(whenText!)}` : `🔔 ${t.remindMe}`}
          </Text>
        </Pressable>
      )}
      {blocked && <Text style={[styles.note, { paddingHorizontal: 0 }]}>{t.notificationsOff}</Text>}
    </View>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.background },
  content: { padding: 16, gap: 18, paddingBottom: 48 },
  heading: { fontSize: 26, lineHeight: 32, fontWeight: '700', color: colors.label },
  subtle: { fontSize: 14, color: colors.secondaryLabel },
  card: { backgroundColor: colors.card, borderRadius: 14, borderCurve: 'continuous', padding: 16 },
  deadlineCard: { gap: 4, borderLeftWidth: 4, borderLeftColor: colors.deadline },
  deadlineLabel: { fontSize: 13, fontWeight: '600', textTransform: 'uppercase', color: colors.secondaryLabel },
  deadlineDate: { fontSize: 22, fontWeight: '700', color: colors.label },
  deadlineLeft: { fontSize: 15, fontWeight: '600', fontVariant: ['tabular-nums'] },
  reminderButton: {
    marginTop: 10,
    alignSelf: 'flex-start',
    borderRadius: 10,
    paddingHorizontal: 14,
    paddingVertical: 9,
    backgroundColor: colors.tint,
  },
  reminderOn: { backgroundColor: colors.fill },
  reminderText: { fontSize: 15, fontWeight: '600', color: '#ffffff' },
  bulletRow: { flexDirection: 'row', gap: 8 },
  dot: { fontSize: 16, lineHeight: 23, color: colors.secondaryLabel },
  body: { fontSize: 16, lineHeight: 23, color: colors.label, flexShrink: 1 },
  note: { fontSize: 14, lineHeight: 19, color: colors.secondaryLabel, paddingHorizontal: 4 },
  primaryButton: { backgroundColor: colors.tint, borderRadius: 12, borderCurve: 'continuous', padding: 14, alignItems: 'center' },
  primaryButtonText: { color: '#ffffff', fontSize: 17, fontWeight: '600' },
  secondaryButton: { backgroundColor: colors.fill, borderRadius: 12, borderCurve: 'continuous', padding: 14, alignItems: 'center' },
  secondaryButtonText: { color: colors.tint, fontSize: 17, fontWeight: '600' },
  footer: { fontSize: 12, lineHeight: 17, color: colors.secondaryLabel, textAlign: 'center' },
});
