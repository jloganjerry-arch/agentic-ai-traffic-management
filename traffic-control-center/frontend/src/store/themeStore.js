import { create } from 'zustand';

/**
 * Zustand themeStore managing Light ☀️ / Dark 🌙 mode toggle state.
 * Persists user preference in localStorage and toggles 'dark' / 'light' class on document.documentElement.
 */
const getInitialTheme = () => {
  if (typeof window !== 'undefined' && window.localStorage) {
    const storedTheme = window.localStorage.getItem('theme');
    if (storedTheme === 'light' || storedTheme === 'dark') {
      return storedTheme;
    }
  }
  return 'dark'; // Default theme mode
};

const applyThemeToDocument = (theme) => {
  if (typeof document !== 'undefined') {
    const root = document.documentElement;
    if (theme === 'light') {
      root.classList.remove('dark');
      root.classList.add('light');
    } else {
      root.classList.remove('light');
      root.classList.add('dark');
    }
  }
};

// Initial sync
const initialTheme = getInitialTheme();
applyThemeToDocument(initialTheme);

export const useThemeStore = create((set) => ({
  theme: initialTheme,
  setTheme: (newTheme) => {
    if (typeof window !== 'undefined' && window.localStorage) {
      window.localStorage.setItem('theme', newTheme);
    }
    applyThemeToDocument(newTheme);
    set({ theme: newTheme });
  },
  toggleTheme: () => {
    set((state) => {
      const nextTheme = state.theme === 'dark' ? 'light' : 'dark';
      if (typeof window !== 'undefined' && window.localStorage) {
        window.localStorage.setItem('theme', nextTheme);
      }
      applyThemeToDocument(nextTheme);
      return { theme: nextTheme };
    });
  }
}));
