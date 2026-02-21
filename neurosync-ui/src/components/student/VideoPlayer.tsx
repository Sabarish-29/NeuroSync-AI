import React, { useRef, useState, useCallback } from 'react';
import { Play, Pause, Volume2, VolumeX, Maximize } from 'lucide-react';
import type { LearningEvent } from '../../types/electron';

interface VideoPlayerProps {
  url: string;
  sessionId: string;
  onEvent: (event: Omit<LearningEvent, 'session_id'>) => void;
}

export const VideoPlayer: React.FC<VideoPlayerProps> = ({ url, sessionId, onEvent }) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [playing, setPlaying] = useState(false);
  const [muted, setMuted] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const lastProgressReport = useRef(0);

  const togglePlay = useCallback(() => {
    const video = videoRef.current;
    if (!video) return;

    if (video.paused) {
      video.play();
      setPlaying(true);
      onEvent({
        event_type: 'video_play',
        playback_position_ms: video.currentTime * 1000,
        timestamp: Date.now(),
      });
    } else {
      video.pause();
      setPlaying(false);
      onEvent({
        event_type: 'video_pause',
        playback_position_ms: video.currentTime * 1000,
        timestamp: Date.now(),
      });
    }
  }, [onEvent]);

  const handleTimeUpdate = useCallback(() => {
    const video = videoRef.current;
    if (!video) return;

    setCurrentTime(video.currentTime);

    // Send progress events every 5 seconds
    const currentSecond = Math.floor(video.currentTime);
    if (currentSecond > 0 && currentSecond % 5 === 0 && currentSecond !== lastProgressReport.current) {
      lastProgressReport.current = currentSecond;
      onEvent({
        event_type: 'video_progress',
        playback_position_ms: video.currentTime * 1000,
        timestamp: Date.now(),
      });
    }
  }, [onEvent]);

  const handleSeeked = useCallback(() => {
    const video = videoRef.current;
    if (!video) return;

    onEvent({
      event_type: 'video_seek',
      seek_from_ms: currentTime * 1000,
      seek_to_ms: video.currentTime * 1000,
      timestamp: Date.now(),
    });
  }, [onEvent, currentTime]);

  const handleLoadedMetadata = useCallback(() => {
    const video = videoRef.current;
    if (video) setDuration(video.duration);
  }, []);

  const toggleMute = useCallback(() => {
    const video = videoRef.current;
    if (video) {
      video.muted = !video.muted;
      setMuted(video.muted);
    }
  }, []);

  const toggleFullscreen = useCallback(() => {
    const video = videoRef.current;
    if (video) {
      if (document.fullscreenElement) {
        document.exitFullscreen();
      } else {
        video.parentElement?.requestFullscreen();
      }
    }
  }, []);

  const formatTime = (seconds: number) => {
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    return `${m}:${s.toString().padStart(2, '0')}`;
  };

  const handleSeekBar = (e: React.ChangeEvent<HTMLInputElement>) => {
    const video = videoRef.current;
    if (video) {
      video.currentTime = Number(e.target.value);
    }
  };

  return (
    <div className="video-player-container h-full bg-black flex flex-col" data-testid="video-player">
      {/* Video element */}
      <div className="flex-1 relative flex items-center justify-center">
        <video
          ref={videoRef}
          src={url}
          className="max-h-full max-w-full"
          onTimeUpdate={handleTimeUpdate}
          onSeeked={handleSeeked}
          onLoadedMetadata={handleLoadedMetadata}
          onPlay={() => setPlaying(true)}
          onPause={() => setPlaying(false)}
          onClick={togglePlay}
          data-testid="video-element"
        />

        {/* Play overlay when paused */}
        {!playing && (
          <button
            onClick={togglePlay}
            className="absolute inset-0 flex items-center justify-center bg-black/30 transition-opacity hover:bg-black/40"
          >
            <Play className="w-20 h-20 text-white/80" />
          </button>
        )}
      </div>

      {/* Controls bar */}
      <div className="h-14 bg-gray-900/95 backdrop-blur flex items-center gap-3 px-4">
        <button onClick={togglePlay} className="p-2 hover:bg-gray-800 rounded-lg transition-colors">
          {playing ? <Pause className="w-5 h-5" /> : <Play className="w-5 h-5" />}
        </button>

        <span className="text-xs text-gray-400 font-mono min-w-[80px]">
          {formatTime(currentTime)} / {formatTime(duration)}
        </span>

        {/* Seek bar */}
        <input
          type="range"
          min={0}
          max={duration || 0}
          value={currentTime}
          onChange={handleSeekBar}
          className="flex-1 h-1 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-neurosync-500"
          data-testid="seek-bar"
        />

        <button onClick={toggleMute} className="p-2 hover:bg-gray-800 rounded-lg transition-colors">
          {muted ? <VolumeX className="w-5 h-5" /> : <Volume2 className="w-5 h-5" />}
        </button>

        <button onClick={toggleFullscreen} className="p-2 hover:bg-gray-800 rounded-lg transition-colors">
          <Maximize className="w-5 h-5" />
        </button>
      </div>
    </div>
  );
};
