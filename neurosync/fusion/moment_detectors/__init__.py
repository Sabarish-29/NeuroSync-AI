"""
NeuroSync AI — Tiered moment detectors (Phase 2).

Each detector follows the tiered confidence pattern:
  1. ``detect_primary()``  — webcam + behavioral (always runs)
  2. ``detect_eeg_enhancement()`` — optional EEG boost
  3. ``detect()``  — orchestrates both, checks threshold
"""

from neurosync.fusion.moment_detectors.base_detector import (
    BaseMomentDetector,
    MomentDetectionResult,
)

__all__ = [
    "BaseMomentDetector",
    "MomentDetectionResult",
]
