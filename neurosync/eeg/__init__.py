"""
NeuroSync AI — EEG module (OPTIONAL signal enhancement).

100 % optional.  If EEG hardware is not available or disabled, all
moment detection still works via webcam and behavioral signals.
"""

from neurosync.eeg.coordinator import EEGCoordinator

__all__ = ["EEGCoordinator"]
