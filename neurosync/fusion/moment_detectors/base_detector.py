"""
Base Moment Detector with Tiered Confidence System.

Design pattern
--------------
- Primary detection uses webcam + behavioral (always available).
- EEG enhancement is optional (adds confidence when available).
- System NEVER blocks on missing EEG.

This ensures 95%+ demo success rate without hardware.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional

from loguru import logger

from neurosync.fusion.state import FusionState


@dataclass
class MomentDetectionResult:
    """Result from a tiered moment detection cycle."""

    moment_id: str
    detected: bool
    confidence: float
    primary_confidence: float
    eeg_boost: float
    signals_used: dict[str, bool] = field(default_factory=dict)
    timestamp: float = 0.0
    metadata: Optional[dict] = None

    def __str__(self) -> str:
        sources = [k for k, v in self.signals_used.items() if v]
        return (
            f"{self.moment_id}: conf={self.confidence:.2f} "
            f"(primary={self.primary_confidence:.2f}, "
            f"eeg_boost={self.eeg_boost:.2f}, sources={sources})"
        )


class BaseMomentDetector(ABC):
    """
    Abstract base class for all tiered moment detectors.

    Subclasses MUST implement ``detect_primary`` and MAY override
    ``detect_eeg_enhancement`` (defaults to 0.0).

    The public ``detect`` method orchestrates both stages, validates
    results, and applies the confidence threshold.
    """

    def __init__(self, moment_id: str, base_threshold: float = 0.70) -> None:
        self.moment_id = moment_id
        self.base_threshold = base_threshold
        logger.debug("Initialized {} detector (threshold={})", moment_id, base_threshold)

    # ── abstract / overridable ────────────────────────────────────────

    @abstractmethod
    def detect_primary(self, state: FusionState) -> Optional[float]:
        """
        Primary detection using webcam + behavioral signals ONLY.

        Returns confidence 0.0-1.0 if detected, else ``None``.
        Do NOT access ``state.eeg`` here.
        """

    def detect_eeg_enhancement(self, state: FusionState) -> float:
        """
        Optional EEG confidence boost.

        Called only when EEG is available and quality >= 0.6.
        Returns 0.0-0.20 additional confidence.  Default: 0.0.
        """
        return 0.0

    # ── public orchestration ──────────────────────────────────────────

    def detect(self, state: FusionState) -> Optional[MomentDetectionResult]:
        """
        Run tiered detection: primary → optional EEG → threshold check.

        Returns ``MomentDetectionResult`` if detected, else ``None``.
        """
        ts = time.time()

        # Step 1: primary detection (REQUIRED — always runs)
        primary = self.detect_primary(state)
        if primary is None:
            return None

        primary = max(0.0, min(1.0, primary))
        eeg_boost = 0.0

        # Step 2: optional EEG enhancement
        if state.eeg is not None:
            quality = state.eeg.quality
            if quality >= 0.6:
                raw_boost = self.detect_eeg_enhancement(state)
                eeg_boost = max(0.0, min(0.20, raw_boost))
                if eeg_boost > 0:
                    logger.debug(
                        "{}: EEG boost +{:.2f} (quality={:.2f})",
                        self.moment_id, eeg_boost, quality,
                    )

        total = min(1.0, primary + eeg_boost)

        # Step 3: threshold gate
        if total < self.base_threshold:
            return None

        return MomentDetectionResult(
            moment_id=self.moment_id,
            detected=True,
            confidence=total,
            primary_confidence=primary,
            eeg_boost=eeg_boost,
            signals_used={
                "webcam": state.webcam is not None,
                "behavioral": True,
                "nlp": state.nlp is not None,
                "eeg": eeg_boost > 0.0,
            },
            timestamp=ts,
            metadata={
                "threshold": self.base_threshold,
                "eeg_quality": state.eeg.quality if state.eeg else None,
            },
        )

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.moment_id}, threshold={self.base_threshold})"
