"""
NeuroSync AI — Desktop notification reminders for reviews.

Uses ``plyer`` for cross-platform notifications.  Degrades gracefully
if ``plyer`` is not installed.
"""

from __future__ import annotations

from loguru import logger

from neurosync.config.settings import SPACED_REPETITION_CONFIG as CFG


class ReviewReminder:
    """Sends desktop notifications when reviews are due."""

    def __init__(self) -> None:
        self._available = False
        try:
            from plyer import notification  # type: ignore[import-untyped]

            self._notification = notification
            self._available = True
        except ImportError:
            logger.debug("plyer not installed — notifications disabled")

    @property
    def available(self) -> bool:
        return self._available

    def notify(self, concept_id: str, message: str | None = None) -> bool:
        """
        Send a desktop notification.

        Returns ``True`` if the notification was sent, ``False`` otherwise.
        """
        if not self._available:
            return False

        title = str(CFG["NOTIFICATION_TITLE"])
        body = message or f"Time to review: {concept_id}"
        timeout = int(CFG["NOTIFICATION_TIMEOUT_SECONDS"])

        try:
            self._notification.notify(
                title=title,
                message=body,
                timeout=timeout,
            )
            logger.info("Notification sent for {}", concept_id)
            return True
        except Exception as exc:  # noqa: BLE001
            logger.warning("Notification failed: {}", exc)
            return False
