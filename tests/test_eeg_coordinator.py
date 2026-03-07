"""Tests for the EEG coordinator."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from neurosync.eeg.coordinator import EEGCoordinator
from neurosync.fusion.state import EEGSignals


class TestEEGCoordinator:
    def test_disabled_by_default(self) -> None:
        coord = EEGCoordinator(enabled=False)
        assert coord.enabled is False
        assert coord.initialize() is False
        assert coord.get_signals() is None

    def test_initialize_with_mock_device(self) -> None:
        coord = EEGCoordinator(enabled=True)
        assert coord.initialize() is True
        assert coord.is_connected is True
        coord.shutdown()
        assert coord.is_connected is False

    def test_get_signals_returns_eeg_signals(self) -> None:
        coord = EEGCoordinator(enabled=True)
        coord.initialize()

        signals = coord.get_signals()
        assert signals is not None
        assert isinstance(signals, EEGSignals)
        assert signals.quality > 0.6
        assert signals.alpha_power > 0
        coord.shutdown()

    def test_get_signals_returns_none_when_disconnected(self) -> None:
        coord = EEGCoordinator(enabled=True)
        # Not initialized → not connected
        assert coord.get_signals() is None

    def test_shutdown_is_idempotent(self) -> None:
        coord = EEGCoordinator(enabled=False)
        coord.shutdown()  # should not raise
        coord.shutdown()

    def test_env_default_is_disabled(self) -> None:
        with patch.dict("os.environ", {"EEG_ENABLED": "false"}):
            coord = EEGCoordinator()
            assert coord.enabled is False
