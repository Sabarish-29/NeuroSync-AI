"""
EEG Coordinator — Optional Signal Enhancement.

Manages EEG hardware lifecycle with graceful degradation.
The system works perfectly without EEG (webcam + behavioral).
"""

from __future__ import annotations

import os
from typing import Any, Optional

from loguru import logger

from neurosync.config.settings import EEG_CONFIG
from neurosync.fusion.state import EEGSignals


class EEGCoordinator:
    """
    Manages optional EEG hardware.

    Design principles (v5.1):
      - EEG is 100 % optional.
      - System works perfectly without it.
      - Graceful degradation if hardware fails.
      - Never crashes the main application.
    """

    def __init__(self, enabled: Optional[bool] = None) -> None:
        self.enabled: bool = enabled if enabled is not None else bool(EEG_CONFIG["ENABLED"])
        self.device: Any = None
        self.is_connected: bool = False
        self.last_quality: float = 0.0

        if not self.enabled:
            logger.info("EEG disabled (normal — system works without it)")

    # ── lifecycle ─────────────────────────────────────────────────────

    def initialize(self) -> bool:
        """
        Initialize EEG hardware if enabled.

        Returns ``True`` only when hardware is connected and streaming.
        Never raises — returns ``False`` gracefully on any failure.
        """
        if not self.enabled:
            logger.info("EEG initialization skipped (disabled)")
            return False

        logger.info("Attempting EEG initialization…")
        device_type = str(EEG_CONFIG.get("DEVICE_TYPE", "mock"))

        try:
            if device_type == "mock":
                self.device = _MockEEGDevice()
            else:
                logger.warning("Unknown EEG device type: {}", device_type)
                return False

            if self.device.connect():
                self.is_connected = True
                logger.info("EEG hardware connected")
                return True

            logger.warning("EEG device did not produce a signal")
            return False

        except Exception as exc:
            logger.warning("EEG hardware not available: {}. Continuing without EEG.", exc)
            return False

    def get_signals(self) -> Optional[EEGSignals]:
        """
        Return latest EEG signals, or ``None`` if unavailable.

        Never raises — always degrades gracefully.
        """
        if not self.is_connected or self.device is None:
            return None

        try:
            data: dict = self.device.read_latest()
            quality = float(data.get("quality", 0.0))
            min_quality = float(EEG_CONFIG.get("MIN_QUALITY", 0.6))

            if quality < min_quality:
                logger.debug("EEG quality too low ({:.2f}), skipping", quality)
                return None

            self.last_quality = quality
            return EEGSignals(
                quality=quality,
                alpha_power=float(data.get("alpha_power", 0.0)),
                beta_power=float(data.get("beta_power", 0.0)),
                theta_power=float(data.get("theta_power", 0.0)),
                gamma_power=float(data.get("gamma_power", 0.0)),
                frontal_asymmetry=float(data.get("frontal_asymmetry", 0.0)),
            )
        except Exception as exc:
            logger.warning("EEG read error: {}, continuing without EEG", exc)
            return None

    def shutdown(self) -> None:
        """Clean shutdown of EEG hardware."""
        if self.device is not None:
            try:
                self.device.disconnect()
                logger.info("EEG hardware disconnected")
            except Exception:
                pass
        self.is_connected = False


# ── built-in mock device (for testing / demos) ───────────────────────


class _MockEEGDevice:
    """Simple deterministic mock for tests and demos."""

    def __init__(self) -> None:
        self._connected = False

    def connect(self) -> bool:
        self._connected = True
        return True

    def read_latest(self) -> dict:
        return {
            "quality": 0.85,
            "alpha_power": 0.40,
            "beta_power": 0.55,
            "theta_power": 0.25,
            "gamma_power": 0.10,
            "frontal_asymmetry": 0.05,
        }

    def disconnect(self) -> None:
        self._connected = False
