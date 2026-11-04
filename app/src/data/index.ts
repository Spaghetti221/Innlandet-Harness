// summaries.json is written by `python -m harness.hamar_news.export` and git-ignored.
// `npm start` copies sample.json into place when it is missing.
import data from './summaries.json';

import type { Lang } from '@/i18n';

export type Kind = 'hearing' | 'grant' | 'plan' | 'decision' | 'info';

export type Bullet = { text: string; children: string[] };

export type LanguageSummary = {
  model: string;
  bullets: Bullet[];
  passedCheck: boolean;
  truncated: boolean;
};

export type Notice = {
  slug: string;
  title: string;
  kind: Kind;
  published: string;
  expires: string | null;
  deadline: string | null;
  url: string;
  summaries: Partial<Record<Lang, LanguageSummary>>;
};

export const notices = data as Notice[];

export const KINDS: Kind[] = ['hearing', 'grant', 'plan', 'decision', 'info'];

export function getNotice(slug: string): Notice | undefined {
  return notices.find((n) => n.slug === slug);
}

/** The summary in the chosen language, or the other one when it is missing. */
export function summaryFor(n: Notice, lang: Lang): { summary?: LanguageSummary; fallback: boolean } {
  const own = n.summaries[lang];
  if (own) return { summary: own, fallback: false };
  return { summary: n.summaries[lang === 'en' ? 'no' : 'en'], fallback: true };
}

export function today(): string {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
}

export function hasOpenDeadline(n: Notice): boolean {
  return !!n.deadline && n.deadline >= today();
}

export function localDate(iso: string, hour = 12): Date {
  const [y, m, d] = iso.split('-').map(Number);
  return new Date(y, m - 1, d, hour);
}

export function formatDate(iso: string, locale: string): string {
  return localDate(iso).toLocaleDateString(locale, { day: 'numeric', month: 'long', year: 'numeric' });
}

export function daysLeft(iso: string): number {
  return Math.round((localDate(iso).getTime() - localDate(today()).getTime()) / 86_400_000);
}
