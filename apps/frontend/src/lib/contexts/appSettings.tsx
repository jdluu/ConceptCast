import { createContext, useCallback, useContext, useMemo, useState } from 'react';

const STORAGE_KEY = 'conceptcast_app_settings';

export interface AppSettings {
  resolution: '720p' | '1080p';
  frameRate: 30 | 60;
  defaultAudience: string;
  enableNotifications: boolean;
  enableSound: boolean;
  reducedMotion: boolean;
}

const DEFAULT_SETTINGS: AppSettings = {
  resolution: '720p',
  frameRate: 30,
  defaultAudience: 'Undergraduate CS',
  enableNotifications: true,
  enableSound: true,
  reducedMotion: false,
};

function readStored(): AppSettings {
  if (typeof window === 'undefined' || !window.localStorage) return DEFAULT_SETTINGS;
  try {
    const stored = window.localStorage.getItem(STORAGE_KEY);
    if (!stored) return DEFAULT_SETTINGS;
    return { ...DEFAULT_SETTINGS, ...JSON.parse(stored) };
  } catch {
    return DEFAULT_SETTINGS;
  }
}

type AppSettingsContextValue = {
  settings: AppSettings;
  updateSettings: (newSettings: Partial<AppSettings>) => void;
};

/**
 * Context value for the application settings.
 */
const AppSettingsContext = createContext<AppSettingsContextValue | null>(null);

/**
 * Provider for application-wide settings such as resolution, framerate, and transparency.
 * Persists settings to localStorage.
 *
 * @param {Object} props - Component props.
 * @param {React.ReactNode} props.children - Child elements.
 */
export function AppSettingsProvider({ children }: { children: React.ReactNode }) {
  const [settings, setSettingsState] = useState<AppSettings>(readStored);

  const updateSettings = useCallback((newSettings: Partial<AppSettings>) => {
    setSettingsState((prev) => {
      const next = { ...prev, ...newSettings };
      if (typeof window !== 'undefined' && window.localStorage) {
        try {
          window.localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
        } catch (e) {
          console.warn('Failed to save app settings to localStorage:', e);
        }
      }
      return next;
    });
  }, []);

  const value = useMemo(() => ({ settings, updateSettings }), [settings, updateSettings]);

  return <AppSettingsContext.Provider value={value}>{children}</AppSettingsContext.Provider>;
}

/**
 * Custom hook to access application settings.
 *
 * @returns {AppSettingsContextValue} The current settings and update function.
 * @throws {Error} If used outside of an AppSettingsProvider.
 */
export function useAppSettings(): AppSettingsContextValue {
  const ctx = useContext(AppSettingsContext);
  if (!ctx) {
    throw new Error('useAppSettings must be used within AppSettingsProvider');
  }
  return ctx;
}
