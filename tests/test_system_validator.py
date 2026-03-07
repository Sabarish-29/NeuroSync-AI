"""Tests for the system validator."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from neurosync.utils.config_validator import SystemValidator


class TestSystemValidator:
    def test_returns_expected_keys(self) -> None:
        results = SystemValidator.validate_all()
        assert "core" in results
        assert "optional" in results
        assert "status" in results
        assert results["status"] in ("ready", "degraded", "broken")

    def test_behavioral_always_core(self) -> None:
        results = SystemValidator.validate_all()
        assert results["core"]["behavioral"] is True

    def test_eeg_is_optional(self) -> None:
        """EEG failure alone must not cause 'broken' — only missing core can."""
        with patch.dict("os.environ", {"GROQ_API_KEY": "gsk_test_key_placeholder"}):
            results = SystemValidator.validate_all()
            assert "eeg" in results["optional"]
            if not results["optional"]["eeg"]:
                assert results["status"] in ("ready", "degraded")

    def test_groq_check(self) -> None:
        results = SystemValidator.validate_all()
        assert "groq" in results["core"]

    def test_print_status_does_not_crash(self) -> None:
        ok = SystemValidator.print_status_report()
        assert isinstance(ok, bool)

    def test_broken_when_no_groq_key(self) -> None:
        env = {k: v for k, v in __import__("os").environ.items() if k != "GROQ_API_KEY"}
        with patch.dict("os.environ", env, clear=True):
            results = SystemValidator.validate_all()
            assert results["core"]["groq"] is False
            assert results["status"] == "broken"
