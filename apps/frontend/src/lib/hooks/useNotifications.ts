import { useCallback } from 'react';
import { useAppSettings } from '@/lib/contexts/appSettings';

export function useNotifications() {
  const { settings } = useAppSettings();

  const sendNotification = useCallback(
    (title: string, body: string) => {
      if (!settings.enableNotifications) return;

      if (Notification.permission === 'granted') {
        void new Notification(title, { body, icon: '/favicon.ico' });
      } else if (Notification.permission !== 'denied') {
        Notification.requestPermission().then((permission) => {
          if (permission === 'granted') {
            void new Notification(title, { body, icon: '/favicon.ico' });
          }
        });
      }
    },
    [settings.enableNotifications],
  );

  return { sendNotification };
}
