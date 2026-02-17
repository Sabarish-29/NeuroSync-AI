"""
NeuroSync AI — Webcam signal processors (Step 2).

Each processor takes raw landmarks and produces a structured result
following the same SignalProcessor protocol as Step 1.
"""

from neurosync.webcam.signals.gaze import GazeSignal, GazeResult
from neurosync.webcam.signals.blink import BlinkSignal, BlinkResult
from neurosync.webcam.signals.expression import ExpressionSignal, ExpressionResult
from neurosync.webcam.signals.pose import PoseSignal, PoseResult
from neurosync.webcam.signals.rppg import RemotePPGSignal, RPPGResult

__all__ = [
    "GazeSignal", "GazeResult",
    "BlinkSignal", "BlinkResult",
    "ExpressionSignal", "ExpressionResult",
    "PoseSignal", "PoseResult",
    "RemotePPGSignal", "RPPGResult",
]
