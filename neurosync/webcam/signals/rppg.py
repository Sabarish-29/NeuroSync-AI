"""
NeuroSync AI — Remote PPG (rPPG) heart-rate estimator.

Estimates heart rate from subtle colour changes in the forehead ROI.
This is RESEARCH QUALITY (~±10 bpm).  Used as a secondary signal only;
never the sole basis for an intervention.

Method:
1. Extract forehead ROI via face landmarks.
2. Extract mean green-channel value per frame.
3. Every 10 s buffer: detrend → bandpass (0.7–3.5 Hz) → FFT → peak.
4. Low SNR → mark as unreliable.
"""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass
from typing import Optional

import numpy as np
from loguru import logger
from scipy import signal as sp_signal

from neurosync.config.settings import WEBCAM_THRESHOLDS
from neurosync.webcam.mediapipe_processor import FOREHEAD_ROI_INDICES, RawLandmarks


@dataclass
class RPPGResult:
    """Output of the remote PPG signal processor."""

    heart_rate_bpm: Optional[float] = None
    signal_quality: float = 0.0
    reliable: bool = False
    stress_indicator: bool = False
    confidence: float = 0.0


class RemotePPGSignal:
    """
    Green-channel forehead rPPG estimator.

    Requires ~10 seconds of data and consistent lighting for reliable
    readings.  Returns ``reliable=False`` during the warm-up phase.
    """

    def __init__(self, fps: float = 30.0) -> None:
        self._buffer_seconds: int = int(WEBCAM_THRESHOLDS["RPPG_BUFFER_SECONDS"])
        self._bp_low: float = float(WEBCAM_THRESHOLDS["RPPG_BANDPASS_LOW"])
        self._bp_high: float = float(WEBCAM_THRESHOLDS["RPPG_BANDPASS_HIGH"])
        self._quality_threshold: float = float(WEBCAM_THRESHOLDS["RPPG_QUALITY_THRESHOLD"])
        self._stress_hr: float = float(WEBCAM_THRESHOLDS["RPPG_STRESS_HR_THRESHOLD"])
        self._fps: float = fps

        max_samples = int(self._buffer_seconds * fps * 1.5)  # some slack
        self._green_buffer: deque[float] = deque(maxlen=max_samples)
        self._time_buffer: deque[float] = deque(maxlen=max_samples)

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def process(
        self,
        landmarks: RawLandmarks,
        frame: Optional[np.ndarray] = None,
    ) -> RPPGResult:
        """
        Extract forehead green channel and estimate HR when buffer is full.

        Parameters
        ----------
        landmarks:
            Face landmarks from ``MediaPipeProcessor``.
        frame:
            Raw BGR frame.  Required to extract the green channel from
            the forehead ROI.  If *None*, only the buffered data is used.
        """
        if not landmarks.face_detected or landmarks.face_landmarks is None or frame is None:
            return RPPGResult(confidence=0.0)

        lm = landmarks.face_landmarks
        try:
            green_mean = self._extract_forehead_green(lm, frame)
        except (IndexError, ValueError):
            return RPPGResult(confidence=0.0)

        now = time.time()
        self._green_buffer.append(green_mean)
        self._time_buffer.append(now)

        # Need at least buffer_seconds of data
        duration = self._time_buffer[-1] - self._time_buffer[0] if len(self._time_buffer) > 1 else 0.0
        if duration < self._buffer_seconds:
            return RPPGResult(
                confidence=round(min(1.0, duration / self._buffer_seconds), 2),
                reliable=False,
            )

        # Estimate heart rate from buffer
        hr, quality = self._estimate_hr()
        reliable = quality >= self._quality_threshold
        stress = reliable and hr is not None and hr > self._stress_hr

        return RPPGResult(
            heart_rate_bpm=round(hr, 1) if hr is not None else None,
            signal_quality=round(quality, 3),
            reliable=reliable,
            stress_indicator=stress,
            confidence=round(quality, 2),
        )

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _extract_forehead_green(
        self,
        lm: list[tuple[float, float, float]],
        frame: np.ndarray,
    ) -> float:
        """Extract mean green-channel value from the forehead polygon."""
        h, w = frame.shape[:2]
        pts = np.array(
            [[int(lm[i][0] * w), int(lm[i][1] * h)] for i in FOREHEAD_ROI_INDICES],
            dtype=np.int32,
        )

        # Bounding rectangle for efficiency
        x_min = max(0, pts[:, 0].min())
        x_max = min(w, pts[:, 0].max())
        y_min = max(0, pts[:, 1].min())
        y_max = min(h, pts[:, 1].max())

        if x_max <= x_min or y_max <= y_min:
            return 0.0

        roi = frame[y_min:y_max, x_min:x_max]
        return float(np.mean(roi[:, :, 1]))  # green channel (BGR index 1)

    def _estimate_hr(self) -> tuple[Optional[float], float]:
        """Run FFT on the green-channel buffer → heart rate + quality."""
        sig = np.array(self._green_buffer, dtype=np.float64)

        # Effective sample rate from timestamps
        times = np.array(self._time_buffer)
        duration = times[-1] - times[0]
        if duration <= 0:
            return None, 0.0
        fs = len(sig) / duration

        # Detrend
        sig = sp_signal.detrend(sig)

        # Normalise
        std = sig.std()
        if std < 1e-6:
            return None, 0.0
        sig = sig / std

        # Bandpass filter (0.7–3.5 Hz)
        nyq = fs / 2.0
        low = self._bp_low / nyq
        high = min(self._bp_high / nyq, 0.99)
        if low >= high or low <= 0:
            return None, 0.0

        try:
            b, a = sp_signal.butter(3, [low, high], btype="band")
            filtered = sp_signal.filtfilt(b, a, sig)
        except ValueError:
            return None, 0.0

        # FFT
        n = len(filtered)
        freqs = np.fft.rfftfreq(n, d=1.0 / fs)
        fft_mag = np.abs(np.fft.rfft(filtered))

        # Only consider physiological range
        mask = (freqs >= self._bp_low) & (freqs <= self._bp_high)
        if not mask.any():
            return None, 0.0

        masked_freqs = freqs[mask]
        masked_mag = fft_mag[mask]

        peak_idx = np.argmax(masked_mag)
        peak_freq = masked_freqs[peak_idx]
        peak_power = masked_mag[peak_idx]

        # SNR: peak / mean of rest
        total_power = masked_mag.sum()
        if total_power < 1e-9:
            return None, 0.0
        snr = float(peak_power / (total_power / len(masked_mag)))
        quality = min(1.0, max(0.0, (snr - 1.0) / 4.0))  # map 1..5 → 0..1

        hr = float(peak_freq * 60.0)
        return hr, quality
