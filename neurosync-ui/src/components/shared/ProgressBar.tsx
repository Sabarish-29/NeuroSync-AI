import React from 'react';

interface ProgressBarProps {
  value: number; // 0-100
  label?: string;
  color?: 'blue' | 'green' | 'yellow' | 'red' | 'purple';
  size?: 'sm' | 'md' | 'lg';
  showPercentage?: boolean;
}

const COLOR_MAP = {
  blue: 'bg-blue-600',
  green: 'bg-green-600',
  yellow: 'bg-yellow-500',
  red: 'bg-red-600',
  purple: 'bg-neurosync-600',
};

const SIZE_MAP = {
  sm: 'h-1.5',
  md: 'h-3',
  lg: 'h-5',
};

export const ProgressBar: React.FC<ProgressBarProps> = ({
  value,
  label,
  color = 'purple',
  size = 'md',
  showPercentage = true,
}) => {
  const clampedValue = Math.min(100, Math.max(0, value));

  return (
    <div className="w-full">
      {(label || showPercentage) && (
        <div className="flex justify-between items-center mb-1">
          {label && <span className="text-sm text-gray-400">{label}</span>}
          {showPercentage && (
            <span className="text-sm font-medium text-gray-300">
              {Math.round(clampedValue)}%
            </span>
          )}
        </div>
      )}
      <div className={`w-full bg-gray-800 rounded-full ${SIZE_MAP[size]} overflow-hidden`}>
        <div
          className={`${COLOR_MAP[color]} ${SIZE_MAP[size]} rounded-full transition-all duration-500 ease-out`}
          style={{ width: `${clampedValue}%` }}
          role="progressbar"
          aria-valuenow={clampedValue}
          aria-valuemin={0}
          aria-valuemax={100}
        />
      </div>
    </div>
  );
};
