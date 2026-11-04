import { getLocales } from 'expo-localization';
import Storage from 'expo-sqlite/kv-store';
import { createContext, useContext, useState, type ReactNode } from 'react';

import type { Kind } from '@/data';

export type Lang = 'en' | 'no';

const strings = {
  en: {
    appTitle: 'Hamar',
    search: 'Search notices',
    openDeadlines: 'Open deadlines',
    otherNotices: 'Other notices',
    noMatches: 'No notices match.',
    all: 'All',
    kinds: {
      hearing: 'Have your say',
      grant: 'Grant',
      plan: 'New plan',
      decision: 'Decision',
      info: 'Information',
    } as Record<Kind, string>,
    deadline: 'Deadline',
    dueToday: 'Due today',
    daysLeft: (n: number) => (n === 1 ? '1 day left' : `${n} days left`),
    passed: 'Passed',
    published: 'Published',
    pageExpires: 'Page expires',
    summary: 'Summary',
    remindMe: 'Remind me',
    reminderSet: (when: string) => `Reminder set · ${when}`,
    reminderTitle: 'Deadline soon',
    reminderBody: (title: string, when: string) => `${title} – deadline ${when}`,
    notificationsOff: 'Notifications are turned off for this app. Turn them on in Settings to get reminders.',
    unchecked: 'Unchecked',
    failedCheck: 'This summary did not pass the output check. Read the original before relying on it.',
    truncated: 'The article was too long and was shortened before summarising.',
    otherLanguageOnly: 'No English summary yet. Showing the Norwegian one.',
    disclaimer: 'Machine summary by a local model. The original article is authoritative.',
    readOriginal: 'Read the original on hamar.kommune.no',
    share: 'Share',
    notFound: 'Summary not found.',
    switchTo: 'Bytt til norsk',
  },
  no: {
    appTitle: 'Hamar',
    search: 'Søk i saker',
    openDeadlines: 'Åpne frister',
    otherNotices: 'Andre saker',
    noMatches: 'Ingen saker passer søket.',
    all: 'Alle',
    kinds: {
      hearing: 'Si din mening',
      grant: 'Tilskudd',
      plan: 'Ny plan',
      decision: 'Vedtak',
      info: 'Informasjon',
    } as Record<Kind, string>,
    deadline: 'Frist',
    dueToday: 'Frist i dag',
    daysLeft: (n: number) => (n === 1 ? '1 dag igjen' : `${n} dager igjen`),
    passed: 'Utløpt',
    published: 'Publisert',
    pageExpires: 'Siden utløper',
    summary: 'Sammendrag',
    remindMe: 'Påminn meg',
    reminderSet: (when: string) => `Påminnelse satt · ${when}`,
    reminderTitle: 'Frist snart',
    reminderBody: (title: string, when: string) => `${title} – frist ${when}`,
    notificationsOff: 'Varsler er slått av for appen. Slå dem på i Innstillinger for å få påminnelser.',
    unchecked: 'Ikke kontrollert',
    failedCheck: 'Sammendraget besto ikke kontrollen. Les originalen før du stoler på det.',
    truncated: 'Artikkelen var for lang og ble forkortet før oppsummering.',
    otherLanguageOnly: 'Ingen norsk oppsummering ennå. Viser den engelske.',
    disclaimer: 'Maskinlaget sammendrag fra en lokal modell. Den opprinnelige saken gjelder.',
    readOriginal: 'Les originalen på hamar.kommune.no',
    share: 'Del',
    notFound: 'Fant ikke sammendraget.',
    switchTo: 'Switch to English',
  },
};

export type Strings = (typeof strings)['en'];

const KEY = 'language';

function initialLang(): Lang {
  try {
    const saved = Storage.getItemSync(KEY);
    if (saved === 'en' || saved === 'no') return saved;
  } catch {}
  const code = getLocales()[0]?.languageCode;
  return code === 'nb' || code === 'nn' || code === 'no' ? 'no' : 'en';
}

type LanguageContext = { lang: Lang; t: Strings; locale: string; setLang: (lang: Lang) => void };

const Context = createContext<LanguageContext | null>(null);

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Lang>(initialLang);
  const setLang = (next: Lang) => {
    setLangState(next);
    try {
      Storage.setItemSync(KEY, next);
    } catch {}
  };
  return (
    <Context.Provider value={{ lang, t: strings[lang], locale: lang === 'no' ? 'nb-NO' : 'en-GB', setLang }}>
      {children}
    </Context.Provider>
  );
}

export function useLanguage(): LanguageContext {
  const ctx = useContext(Context);
  if (!ctx) throw new Error('useLanguage must be used inside LanguageProvider');
  return ctx;
}
