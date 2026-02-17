"""
NeuroSync AI — Webcam sensing layer (Step 2).

Provides real-time facial landmark extraction, gaze tracking,
blink detection, micro-expression classification, body pose analysis,
and remote PPG heart-rate estimation.
"""

from neurosync.webcam.capture import WebcamCapture
from neurosync.webcam.mediapipe_processor import MediaPipeProcessor, RawLandmarks

__all__ = [
    "WebcamCapture",
    "MediaPipeProcessor",
    "RawLandmarks",
]
