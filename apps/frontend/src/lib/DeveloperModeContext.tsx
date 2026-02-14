import { createContext, useCallback, useContext, useMemo, useState } from 'react';

const STORAGE_KEY = 'conceptcast_developer_mode';

function readStored(): boolean {
    if (typeof window === 'undefined' || !window.localStorage) return false;
    try {
        return window.localStorage.getItem(STORAGE_KEY) === 'true';
    } catch {
        return false;
    }
}

type DeveloperModeContextValue = {
    developerMode: boolean;
    setDeveloperMode: (value: boolean) => void;
};

const DeveloperModeContext = createContext<DeveloperModeContextValue | null>(null);

export function DeveloperModeProvider({ children }: { children: React.ReactNode }) {
    const [developerMode, setDeveloperModeState] = useState(readStored);

    const setDeveloperMode = useCallback((value: boolean) => {
        setDeveloperModeState(value);
        if (typeof window !== 'undefined' && window.localStorage) {
            try {
                window.localStorage.setItem(STORAGE_KEY, value ? 'true' : 'false');
            } catch (e) {
                console.warn('Failed to save developer mode to localStorage:', e);
            }
        }
    }, []);

    const value = useMemo(
        () => ({ developerMode, setDeveloperMode }),
        [developerMode, setDeveloperMode]
    );

    return (
        <DeveloperModeContext.Provider value={value}>
            {children}
        </DeveloperModeContext.Provider>
    );
}

export function useDeveloperMode(): DeveloperModeContextValue {
    const ctx = useContext(DeveloperModeContext);
    if (!ctx) {
        throw new Error('useDeveloperMode must be used within DeveloperModeProvider');
    }
    return ctx;
}
