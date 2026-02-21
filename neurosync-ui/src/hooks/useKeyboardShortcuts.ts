import { useEffect } from 'react';

export interface KeyboardShortcut {
  key: string;
  description: string;
  action: () => void;
  ctrl?: boolean;
  alt?: boolean;
  shift?: boolean;
}

export const useKeyboardShortcuts = (shortcuts: KeyboardShortcut[]) => {
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      // Don't trigger shortcuts when typing in inputs
      const target = e.target as HTMLElement;
      if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable) {
        return;
      }

      // Find matching shortcut
      const shortcut = shortcuts.find(s => {
        const keyMatches = e.key.toLowerCase() === s.key.toLowerCase();
        const ctrlMatches = s.ctrl ? (e.ctrlKey || e.metaKey) : !(e.ctrlKey || e.metaKey);
        const altMatches = s.alt ? e.altKey : !e.altKey;
        const shiftMatches = s.shift ? e.shiftKey : !e.shiftKey;

        return keyMatches && ctrlMatches && altMatches && shiftMatches;
      });

      if (shortcut) {
        e.preventDefault();
        shortcut.action();
      }
    };

    window.addEventListener('keydown', handleKeyPress);

    return () => {
      window.removeEventListener('keydown', handleKeyPress);
    };
  }, [shortcuts]);

  return shortcuts;
};
