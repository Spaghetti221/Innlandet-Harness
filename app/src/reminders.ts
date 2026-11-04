// Local deadline reminders. They stay on the phone; nothing is sent anywhere.
import * as Notifications from 'expo-notifications';
import { AndroidImportance } from 'expo-notifications';
import { Platform } from 'react-native';

import { localDate, type Notice } from '@/data';

const DAYS_BEFORE = 3;
const HOUR = 9;

const idFor = (slug: string) => `deadline-${slug}`;

/** 09:00 three days before the deadline, or 09:00 on the day itself when that is too late. */
export function reminderDate(deadline: string): Date | null {
  const day = localDate(deadline, HOUR);
  const early = new Date(day);
  early.setDate(early.getDate() - DAYS_BEFORE);
  const now = new Date();
  if (early > now) return early;
  return day > now ? day : null;
}

export async function hasReminder(slug: string): Promise<boolean> {
  const all = await Notifications.getAllScheduledNotificationsAsync();
  return all.some((r) => r.identifier === idFor(slug));
}

/** Returns false when the user has not allowed notifications. */
export async function scheduleReminder(notice: Notice, title: string, body: string): Promise<boolean> {
  const date = notice.deadline && reminderDate(notice.deadline);
  if (!date) return false;
  const { granted } = await Notifications.requestPermissionsAsync();
  if (!granted) return false;
  if (Platform.OS === 'android') {
    await Notifications.setNotificationChannelAsync('deadlines', {
      name: 'Deadlines',
      importance: AndroidImportance.DEFAULT,
    });
  }
  await Notifications.scheduleNotificationAsync({
    identifier: idFor(notice.slug),
    content: { title, body, data: { slug: notice.slug } },
    trigger: { type: Notifications.SchedulableTriggerInputTypes.DATE, date, channelId: 'deadlines' },
  });
  return true;
}

export function cancelReminder(slug: string): Promise<void> {
  return Notifications.cancelScheduledNotificationAsync(idFor(slug));
}
