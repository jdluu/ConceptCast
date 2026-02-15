import React, { createContext, useContext, useEffect, useState } from 'react';

type Theme = 'dark' | 'light' | 'system';

interface ThemeContextType {
    theme: Theme;
    setTheme: (theme: Theme) => void;
}

/**
 * Context for managing the application's visual theme (light, dark, or system).
 */
const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

/**
 * Provides theme state and management functions to the application tree.
 * Automatically persists the choice to localStorage and synchronization with system preferences.
 * 
 * @param {Object} props - Component props.
 * @param {React.ReactNode} props.children - Child elements.
 */
export function ThemeProvider({ children }: { children: React.ReactNode }) {
    const [theme, setThemeState] = useState<Theme>(() => {
        const saved = localStorage.getItem('conceptcast_theme') as Theme;
        return saved || 'system';
    });

    const setTheme = (newTheme: Theme) => {
        setThemeState(newTheme);
        localStorage.setItem('conceptcast_theme', newTheme);
    };

    useEffect(() => {
        const root = window.document.documentElement;
        
        const applyTheme = (resolvedTheme: 'dark' | 'light') => {
            root.classList.remove('light', 'dark');
            root.classList.add(resolvedTheme);
            // Also set color-scheme for native elements
            root.style.setProperty('color-scheme', resolvedTheme);
        };

        if (theme === 'system') {
            const systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
            applyTheme(systemTheme);

            const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
            const handleChange = (e: MediaQueryListEvent) => {
                if (theme === 'system') {
                    applyTheme(e.matches ? 'dark' : 'light');
                }
            };
            
            mediaQuery.addEventListener('change', handleChange);
            return () => mediaQuery.removeEventListener('change', handleChange);
        } else {
            applyTheme(theme);
        }
    }, [theme]);

    return (
        <ThemeContext.Provider value={{ theme, setTheme }}>
            {children}
        </ThemeContext.Provider>
    );
}

/**
 * Custom hook to access the theme context.
 * 
 * @returns {ThemeContextType} The current theme state and setter.
 * @throws {Error} If used outside of a ThemeProvider.
 */
export function useTheme() {
    const context = useContext(ThemeContext);
    if (!context) {
        throw new Error('useTheme must be used within a ThemeProvider');
    }
    return context;
}
