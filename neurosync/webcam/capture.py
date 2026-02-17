"""
NeuroSync AI — Thread-safe webcam frame provider.

Runs in a background daemon thread.  Continuously captures frames from
the laptop webcam and provides thread-safe access to the latest frame.
If the webcam is unavailable the system continues gracefully — this
module NEVER blocks the main thread.
"""

from __future__ import annotations

import threading
import time
from typing import Optional

import cv2
import numpy as np
from loguru import logger


class WebcamCapture:
    """Thread-safe latest-frame provider backed by ``cv2.VideoCapture``."""

    def __init__(self, device_index: int = 0, target_fps: int = 30) -> None:
        self._device_index = device_index
        self._target_fps = target_fps
        self._frame: Optional[np.ndarray] = None
        self._lock = threading.Lock()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._fps: float = 0.0
        self._frame_count: int = 0
        self._start_time: float = 0.0
        logger.debug("WebcamCapture created (device={})", device_index)

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Start capturing in a background daemon thread."""
        if self._running:
            return
        self._running = True
        self._start_time = time.monotonic()
        self._frame_count = 0
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()
        logger.info("WebcamCapture started (device={})", self._device_index)

    def stop(self) -> None:
        """Signal the capture thread to stop and wait for it."""
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=3.0)
            self._thread = None
        logger.info("WebcamCapture stopped")

    def get_latest_frame(self) -> Optional[np.ndarray]:
        """Return a *copy* of the most recent BGR frame, or ``None``."""
        with self._lock:
            if self._frame is None:
                return None
            return self._frame.copy()

    def get_fps(self) -> float:
        """Return the measured capture FPS."""
        return self._fps

    @property
    def is_running(self) -> bool:  # noqa: D401
        """``True`` while the capture thread is alive."""
        return self._running

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    def _capture_loop(self) -> None:
        """Background capture loop — runs in daemon thread."""
        cap: Optional[cv2.VideoCapture] = None
        try:
            cap = cv2.VideoCapture(self._device_index)
            if not cap.isOpened():
                logger.warning("Webcam device {} could not be opened", self._device_index)
                self._running = False
                return

            delay = 1.0 / self._target_fps
            while self._running:
                ret, frame = cap.read()
                if not ret or frame is None:
                    logger.debug("Webcam read failed — skipping frame")
                    time.sleep(delay)
                    continue

                with self._lock:
                    self._frame = frame  # store latest (drop old)

                self._frame_count += 1
                elapsed = time.monotonic() - self._start_time
                if elapsed > 0:
                    self._fps = self._frame_count / elapsed

                time.sleep(delay)
        except Exception as exc:
            logger.error("Webcam capture error: {}", exc)
        finally:
            if cap is not None:
                cap.release()
            self._running = False
            logger.debug("Webcam capture loop exited")
