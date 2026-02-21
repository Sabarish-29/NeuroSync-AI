import React from 'react';
import { AlertCircle, X, RefreshCw } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export interface ErrorAlertProps {
  error: string | null;
  onDismiss: () => void;
  onRetry?: () => void;
  type?: 'error' | 'warning' | 'info';
}

export const ErrorAlert: React.FC<ErrorAlertProps> = ({
  error,
  onDismiss,
  onRetry,
  type = 'error',
}) => {
  if (!error) return null;

  const bgColor = {
    error: 'bg-red-900/50 border-red-700',
    warning: 'bg-yellow-900/50 border-yellow-700',
    info: 'bg-blue-900/50 border-blue-700',
  }[type];

  const textColor = {
    error: 'text-red-200',
    warning: 'text-yellow-200',
    info: 'text-blue-200',
  }[type];

  const iconColor = {
    error: 'text-red-400',
    warning: 'text-yellow-400',
    info: 'text-blue-400',
  }[type];

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -20 }}
        className={`fixed top-4 right-4 max-w-md ${bgColor} border-2 rounded-lg shadow-lg z-50`}
      >
        <div className="p-4">
          <div className="flex items-start gap-3">
            <AlertCircle className={`w-5 h-5 ${iconColor} flex-shrink-0 mt-0.5`} />

            <div className="flex-1">
              <h4 className={`font-semibold ${textColor} mb-1`}>
                {type === 'error' ? 'Error' : type === 'warning' ? 'Warning' : 'Info'}
              </h4>
              <p className={`text-sm ${textColor}`}>
                {error}
              </p>

              {onRetry && (
                <button
                  onClick={onRetry}
                  className={`mt-3 flex items-center gap-2 px-3 py-1 ${textColor} hover:opacity-75 transition-opacity text-sm font-medium`}
                >
                  <RefreshCw className="w-4 h-4" />
                  Try Again
                </button>
              )}
            </div>

            <button
              onClick={onDismiss}
              className={`${iconColor} hover:opacity-75 transition-opacity`}
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>
      </motion.div>
    </AnimatePresence>
  );
};
