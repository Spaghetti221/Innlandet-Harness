import * as Notifications from 'expo-notifications';
import { router } from 'expo-router';
import { DarkTheme, DefaultTheme, ThemeProvider } from 'expo-router/react-navigation';
import { Stack } from 'expo-router/stack';
import { useEffect } from 'react';
import { useColorScheme } from 'react-native';

import { LanguageToggle } from '@/components/language-toggle';
import { LanguageProvider, useLanguage } from '@/i18n';

Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldPlaySound: false,
    shouldSetBadge: false,
    shouldShowBanner: true,
    shouldShowList: true,
  }),
});

export default function RootLayout() {
  const colorScheme = useColorScheme();
  return (
    <ThemeProvider value={colorScheme === 'dark' ? DarkTheme : DefaultTheme}>
      <LanguageProvider>
        <AppStack />
      </LanguageProvider>
    </ThemeProvider>
  );
}

function AppStack() {
  const { t } = useLanguage();
  const response = Notifications.useLastNotificationResponse();

  // Tapping a deadline reminder opens that notice.
  useEffect(() => {
    const slug = response?.notification.request.content.data?.slug;
    if (typeof slug === 'string') router.push({ pathname: '/[slug]', params: { slug } });
  }, [response]);

  return (
    <Stack screenOptions={{ headerBackButtonDisplayMode: 'minimal', headerRight: () => <LanguageToggle /> }}>
      <Stack.Screen name="index" options={{ title: t.appTitle, headerLargeTitleEnabled: true }} />
      <Stack.Screen name="[slug]" options={{ title: '' }} />
    </Stack>
  );
}
