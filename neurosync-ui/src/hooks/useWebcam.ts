import { useState, useEffect, useCallback, useRef } from 'react';

interface UseWebcamOptions {
  enabled: boolean;
  fps?: number;
}

interface WebcamState {
  stream: MediaStream | null;
  isActive: boolean;
  error: string | null;
  videoRef: React.RefObject<HTMLVideoElement>;
  start: () => Promise<void>;
  stop: () => void;
}

/**
 * Hook for managing webcam access for expression/gaze detection.
 */
export function useWebcam({ enabled, fps = 4 }: UseWebcamOptions): WebcamState {
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [isActive, setIsActive] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const videoRef = useRef<HTMLVideoElement>(null);

  const start = useCallback(async () => {
    if (!enabled) return;

    try {
      // Request permission via Electron API if available
      await window.electronAPI?.requestWebcamPermission();

      const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: { width: 640, height: 480, frameRate: fps },
        audio: false,
      });

      setStream(mediaStream);
      setIsActive(true);
      setError(null);

      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream;
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Webcam access denied');
      setIsActive(false);
    }
  }, [enabled, fps]);

  const stop = useCallback(() => {
    if (stream) {
      stream.getTracks().forEach((track) => track.stop());
      setStream(null);
      setIsActive(false);
    }
  }, [stream]);

  useEffect(() => {
    return () => {
      stop();
    };
  }, []);

  return { stream, isActive, error, videoRef: videoRef as React.RefObject<HTMLVideoElement>, start, stop };
}
