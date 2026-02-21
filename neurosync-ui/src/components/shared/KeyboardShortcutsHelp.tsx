import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Keyboard } from 'lucide-react';

export interface KeyboardShortcutsHelpProps {
  shortcuts: Array<{
    key: string;
    description: string;
    ctrl?: boolean;
    alt?: boolean;
  }>;
}

export const KeyboardShortcutsHelp: React.FC<KeyboardShortcutsHelpProps> = ({
  shortcuts,
}) => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      {/* Help Button */}
      <button
        onClick={() => setIsOpen(true)}
        className="fixed bottom-4 right-4 p-3 bg-gray-800 text-white rounded-full shadow-lg hover:bg-gray-700 transition-colors z-40"
        title="Keyboard shortcuts (Press ?)"
      >
        <Keyboard className="w-5 h-5" />
      </button>

      {/* Modal */}
      <AnimatePresence>
        {isOpen && (
          <>
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setIsOpen(false)}
              className="fixed inset-0 bg-black/50 z-50"
            />

            {/* Modal Content */}
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              className="fixed inset-0 flex items-center justify-center z-50 p-4"
            >
              <div className="bg-surface-dark border border-gray-700 rounded-lg shadow-xl max-w-md w-full p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-xl font-bold text-white">Keyboard Shortcuts</h3>
                  <button
                    onClick={() => setIsOpen(false)}
                    className="text-gray-400 hover:text-gray-200"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>

                <div className="space-y-2">
                  {shortcuts.map((shortcut, index) => (
                    <div
                      key={index}
                      className="flex items-center justify-between py-2 border-b border-gray-700 last:border-0"
                    >
                      <span className="text-gray-300">{shortcut.description}</span>
                      <div className="flex items-center gap-1">
                        {shortcut.ctrl && (
                          <kbd className="px-2 py-1 bg-gray-800 border border-gray-600 rounded text-sm font-mono text-gray-300">
                            Ctrl
                          </kbd>
                        )}
                        {shortcut.alt && (
                          <kbd className="px-2 py-1 bg-gray-800 border border-gray-600 rounded text-sm font-mono text-gray-300">
                            Alt
                          </kbd>
                        )}
                        <kbd className="px-2 py-1 bg-gray-800 border border-gray-600 rounded text-sm font-mono text-gray-300">
                          {shortcut.key.toUpperCase()}
                        </kbd>
                      </div>
                    </div>
                  ))}
                </div>

                <p className="mt-4 text-sm text-gray-500 text-center">
                  Press <kbd className="px-1 bg-gray-800 border border-gray-600 rounded font-mono text-gray-300">?</kbd> to toggle this help
                </p>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </>
  );
};
