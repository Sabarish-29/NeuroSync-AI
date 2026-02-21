import React from 'react';
import {
  AlertCircle,
  Brain,
  Lightbulb,
  Coffee,
  BookOpen,
  Eye,
  Clock,
  Zap,
  Heart,
  Target,
  TrendingDown,
  TrendingUp,
  Pause,
  FastForward,
  HelpCircle,
  Smile,
  Frown,
  Meh,
  Award,
  RefreshCw,
  Volume2,
  MessageCircle,
} from 'lucide-react';

const MOMENT_CONFIG: Record<string, { icon: React.ElementType; label: string; color: string }> = {
  M01: { icon: Eye, label: 'Attention Drop', color: 'text-red-400 bg-red-900/30' },
  M02: { icon: Brain, label: 'Cognitive Overload', color: 'text-orange-400 bg-orange-900/30' },
  M03: { icon: Meh, label: 'Boredom', color: 'text-yellow-400 bg-yellow-900/30' },
  M04: { icon: TrendingDown, label: 'Confusion', color: 'text-purple-400 bg-purple-900/30' },
  M05: { icon: Clock, label: 'Response Slowdown', color: 'text-blue-400 bg-blue-900/30' },
  M06: { icon: FastForward, label: 'Guessing', color: 'text-pink-400 bg-pink-900/30' },
  M07: { icon: Frown, label: 'Frustration', color: 'text-red-400 bg-red-900/30' },
  M08: { icon: Lightbulb, label: 'Insight Moment', color: 'text-green-400 bg-green-900/30' },
  M09: { icon: Coffee, label: 'Fatigue', color: 'text-amber-400 bg-amber-900/30' },
  M10: { icon: RefreshCw, label: 'Rewind Burst', color: 'text-cyan-400 bg-cyan-900/30' },
  M11: { icon: Pause, label: 'Idle', color: 'text-gray-400 bg-gray-900/30' },
  M12: { icon: TrendingUp, label: 'Mastery Ready', color: 'text-emerald-400 bg-emerald-900/30' },
  M13: { icon: Award, label: 'Achievement', color: 'text-yellow-400 bg-yellow-900/30' },
  M14: { icon: Target, label: 'Zone of Proximal Dev', color: 'text-indigo-400 bg-indigo-900/30' },
  M15: { icon: Heart, label: 'Emotional Spike', color: 'text-rose-400 bg-rose-900/30' },
  M16: { icon: HelpCircle, label: 'Help Seeking', color: 'text-sky-400 bg-sky-900/30' },
  M17: { icon: Smile, label: 'Engagement Peak', color: 'text-lime-400 bg-lime-900/30' },
  M18: { icon: Volume2, label: 'Distraction', color: 'text-orange-400 bg-orange-900/30' },
  M19: { icon: MessageCircle, label: 'Misconception', color: 'text-violet-400 bg-violet-900/30' },
  M20: { icon: Zap, label: 'Plateau', color: 'text-teal-400 bg-teal-900/30' },
  M21: { icon: BookOpen, label: 'Review Needed', color: 'text-blue-400 bg-blue-900/30' },
  M22: { icon: AlertCircle, label: 'Discomfort', color: 'text-red-400 bg-red-900/30' },
};

interface MomentBadgeProps {
  momentId: string;
  showLabel?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

export const MomentBadge: React.FC<MomentBadgeProps> = ({
  momentId,
  showLabel = true,
  size = 'md',
}) => {
  const config = MOMENT_CONFIG[momentId] || {
    icon: AlertCircle,
    label: momentId,
    color: 'text-gray-400 bg-gray-900/30',
  };
  const Icon = config.icon;

  const sizeClasses = {
    sm: 'px-2 py-0.5 text-xs gap-1',
    md: 'px-3 py-1.5 text-sm gap-1.5',
    lg: 'px-4 py-2 text-base gap-2',
  };

  const iconSizes = { sm: 'w-3 h-3', md: 'w-4 h-4', lg: 'w-5 h-5' };

  return (
    <span
      className={`inline-flex items-center rounded-full font-medium border border-current/10 ${config.color} ${sizeClasses[size]}`}
      title={`${momentId}: ${config.label}`}
    >
      <Icon className={iconSizes[size]} />
      {showLabel && <span>{config.label}</span>}
    </span>
  );
};

export { MOMENT_CONFIG };
