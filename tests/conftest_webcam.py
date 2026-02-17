"""
NeuroSync AI — Webcam-specific test fixtures.

Provides synthetic frames and pre-computed landmark sets so that
NO real camera is required for any webcam test.
"""

from __future__ import annotations

import time
from typing import Optional

import numpy as np
import pytest

from neurosync.webcam.mediapipe_processor import (
    CHIN,
    FOREHEAD,
    FOREHEAD_ROI_INDICES,
    LEFT_CHEEK,
    LEFT_EAR_POINTS,
    LEFT_EYEBROW_INNER,
    LEFT_EYE_INDICES,
    LEFT_IRIS_INDICES,
    LOWER_LIP,
    NOSE_TIP,
    RIGHT_CHEEK,
    RIGHT_EAR_POINTS,
    RIGHT_EYEBROW_INNER,
    RIGHT_EYE_INDICES,
    RIGHT_IRIS_INDICES,
    UPPER_LIP,
    RawLandmarks,
)


# =====================================================================
# Helper: build a full 478-landmark face from key positions
# =====================================================================

def _default_landmarks() -> list[tuple[float, float, float]]:
    """
    Generate 478 face landmarks at a neutral expression with the face
    centered and looking at the screen.

    Landmark positions are in MediaPipe normalised coordinates (0–1).
    """
    # Start with every point at face-centre as a safe baseline
    base = [(0.5, 0.45, 0.0)] * 478

    lm = list(base)

    # -- Face boundary --
    lm[FOREHEAD] = (0.50, 0.20, 0.0)        # top of forehead
    lm[CHIN] = (0.50, 0.80, 0.0)            # chin
    lm[LEFT_CHEEK] = (0.25, 0.50, 0.0)      # left cheek
    lm[RIGHT_CHEEK] = (0.75, 0.50, 0.0)     # right cheek
    lm[NOSE_TIP] = (0.50, 0.50, 0.0)        # nose tip

    # -- Left eye (screen-right — MediaPipe mirror convention) --
    # Outer corners → horizontal span
    for i, (x, y) in zip(
        LEFT_EYE_INDICES,
        _eye_ring(cx=0.60, cy=0.40, rx=0.04, ry=0.015),
    ):
        lm[i] = (x, y, 0.0)

    # -- Right eye --
    for i, (x, y) in zip(
        RIGHT_EYE_INDICES,
        _eye_ring(cx=0.40, cy=0.40, rx=0.04, ry=0.015),
    ):
        lm[i] = (x, y, 0.0)

    # -- Left iris (centered in left eye → looking at screen) --
    for i in LEFT_IRIS_INDICES:
        lm[i] = (0.60, 0.40, 0.0)

    # -- Right iris (centered in right eye) --
    for i in RIGHT_IRIS_INDICES:
        lm[i] = (0.40, 0.40, 0.0)

    # -- EAR landmarks (used by blink detector) --
    # Left EAR points: p1(left corner) p2(upper-inner) p3(upper-outer)
    #                  p4(right corner) p5(lower-outer) p6(lower-inner)
    lm[LEFT_EAR_POINTS[0]] = (0.56, 0.40, 0.0)   # p1 left corner
    lm[LEFT_EAR_POINTS[1]] = (0.59, 0.385, 0.0)   # p2 upper inner
    lm[LEFT_EAR_POINTS[2]] = (0.61, 0.385, 0.0)   # p3 upper outer
    lm[LEFT_EAR_POINTS[3]] = (0.64, 0.40, 0.0)   # p4 right corner
    lm[LEFT_EAR_POINTS[4]] = (0.61, 0.415, 0.0)   # p5 lower outer
    lm[LEFT_EAR_POINTS[5]] = (0.59, 0.415, 0.0)   # p6 lower inner

    lm[RIGHT_EAR_POINTS[0]] = (0.36, 0.40, 0.0)
    lm[RIGHT_EAR_POINTS[1]] = (0.39, 0.385, 0.0)
    lm[RIGHT_EAR_POINTS[2]] = (0.41, 0.385, 0.0)
    lm[RIGHT_EAR_POINTS[3]] = (0.44, 0.40, 0.0)
    lm[RIGHT_EAR_POINTS[4]] = (0.41, 0.415, 0.0)
    lm[RIGHT_EAR_POINTS[5]] = (0.39, 0.415, 0.0)

    # -- Eyebrows --
    lm[LEFT_EYEBROW_INNER] = (0.55, 0.34, 0.0)
    lm[RIGHT_EYEBROW_INNER] = (0.45, 0.34, 0.0)

    # -- Lips --
    lm[UPPER_LIP] = (0.50, 0.63, 0.0)
    lm[LOWER_LIP] = (0.50, 0.67, 0.0)

    # Mouth corners (used by expression confusion detector)
    lm[61] = (0.44, 0.65, 0.0)   # left mouth corner
    lm[291] = (0.56, 0.65, 0.0)  # right mouth corner

    # Forehead ROI points (used by rPPG)
    forehead_pts = [
        (0.50, 0.20, 0.0), (0.55, 0.22, 0.0), (0.58, 0.24, 0.0),
        (0.42, 0.24, 0.0), (0.45, 0.22, 0.0), (0.48, 0.20, 0.0),
    ]
    for idx, pt in zip(FOREHEAD_ROI_INDICES, forehead_pts):
        lm[idx] = pt

    return lm


def _eye_ring(
    cx: float, cy: float, rx: float, ry: float, n: int = 16,
) -> list[tuple[float, float]]:
    """Generate *n* points on an ellipse centred at (cx, cy)."""
    angles = np.linspace(0, 2 * np.pi, n, endpoint=False)
    return [(cx + rx * np.cos(a), cy + ry * np.sin(a)) for a in angles]


def _shift_iris_left(lm: list[tuple[float, float, float]]) -> list[tuple[float, float, float]]:
    """Move iris landmarks strongly left (low horizontal ratio)."""
    lm = list(lm)
    for i in LEFT_IRIS_INDICES:
        x, y, z = lm[i]
        lm[i] = (x - 0.06, y, z)
    for i in RIGHT_IRIS_INDICES:
        x, y, z = lm[i]
        lm[i] = (x - 0.06, y, z)
    return lm


def _make_closed_eyes(lm: list[tuple[float, float, float]]) -> list[tuple[float, float, float]]:
    """Collapse eye vertical span to simulate closed eyes (low EAR)."""
    lm = list(lm)
    for pts in [LEFT_EAR_POINTS, RIGHT_EAR_POINTS]:
        # Move upper landmarks down and lower landmarks up
        p1_x, p1_y, _ = lm[pts[0]]
        mid_y = p1_y
        lm[pts[1]] = (lm[pts[1]][0], mid_y + 0.001, 0.0)
        lm[pts[2]] = (lm[pts[2]][0], mid_y + 0.001, 0.0)
        lm[pts[4]] = (lm[pts[4]][0], mid_y + 0.001, 0.0)
        lm[pts[5]] = (lm[pts[5]][0], mid_y + 0.001, 0.0)
    return lm


def _make_frustrated(lm: list[tuple[float, float, float]]) -> list[tuple[float, float, float]]:
    """Furrow brows and press lips to simulate frustration."""
    lm = list(lm)
    # Move inner brows closer together
    lm[LEFT_EYEBROW_INNER] = (0.52, 0.34, 0.0)
    lm[RIGHT_EYEBROW_INNER] = (0.48, 0.34, 0.0)
    # Press lips
    lm[UPPER_LIP] = (0.50, 0.645, 0.0)
    lm[LOWER_LIP] = (0.50, 0.655, 0.0)
    # Lower brows toward eyes
    lm[LEFT_EYEBROW_INNER] = (0.52, 0.375, 0.0)
    lm[RIGHT_EYEBROW_INNER] = (0.48, 0.375, 0.0)
    return lm


def _make_bored(lm: list[tuple[float, float, float]]) -> list[tuple[float, float, float]]:
    """Drop jaw and droop head to simulate boredom."""
    lm = list(lm)
    # Increase lip gap (jaw drop)
    lm[UPPER_LIP] = (0.50, 0.62, 0.0)
    lm[LOWER_LIP] = (0.50, 0.72, 0.0)
    # Droop chin
    lm[CHIN] = (0.50, 0.85, 0.0)
    # Heavy lids — reduce eye vertical span
    for pts in [LEFT_EYE_INDICES, RIGHT_EYE_INDICES]:
        for i in pts:
            x, y, z = lm[i]
            # Flatten vertical span
            cy = 0.40
            lm[i] = (x, cy + (y - cy) * 0.4, z)
    return lm


# =====================================================================
# Fixtures
# =====================================================================

@pytest.fixture
def mock_frame_face_centered() -> np.ndarray:
    """480×640 BGR frame (blank grey — face content irrelevant for unit tests)."""
    return np.full((480, 640, 3), 128, dtype=np.uint8)


@pytest.fixture
def mock_frame_no_face() -> np.ndarray:
    """Frame that produces no face detection."""
    return np.zeros((480, 640, 3), dtype=np.uint8)


@pytest.fixture
def mock_landmarks_neutral() -> RawLandmarks:
    """Pre-computed neutral landmark set — face centred, looking at screen."""
    return RawLandmarks(
        face_landmarks=_default_landmarks(),
        face_detected=True,
        frame_width=640,
        frame_height=480,
        frame_timestamp=time.time(),
    )


@pytest.fixture
def mock_landmarks_looking_left() -> RawLandmarks:
    """Face detected but iris shifted far left → off-screen."""
    lm = _shift_iris_left(_default_landmarks())
    return RawLandmarks(
        face_landmarks=lm,
        face_detected=True,
        frame_width=640,
        frame_height=480,
        frame_timestamp=time.time(),
    )


@pytest.fixture
def mock_landmarks_no_face() -> RawLandmarks:
    """No face detected."""
    return RawLandmarks(face_detected=False, frame_width=640, frame_height=480)


@pytest.fixture
def mock_landmarks_frustrated() -> RawLandmarks:
    """Pre-computed frustrated landmark set."""
    return RawLandmarks(
        face_landmarks=_make_frustrated(_default_landmarks()),
        face_detected=True,
        frame_width=640,
        frame_height=480,
        frame_timestamp=time.time(),
    )


@pytest.fixture
def mock_landmarks_bored() -> RawLandmarks:
    """Pre-computed bored landmark set."""
    return RawLandmarks(
        face_landmarks=_make_bored(_default_landmarks()),
        face_detected=True,
        frame_width=640,
        frame_height=480,
        frame_timestamp=time.time(),
    )


@pytest.fixture
def mock_landmarks_closed_eyes() -> RawLandmarks:
    """Closed eyes — low EAR → blink detection."""
    return RawLandmarks(
        face_landmarks=_make_closed_eyes(_default_landmarks()),
        face_detected=True,
        frame_width=640,
        frame_height=480,
        frame_timestamp=time.time(),
    )


# Helper functions re-exported for direct use in tests
def make_neutral_landmarks() -> RawLandmarks:
    return RawLandmarks(
        face_landmarks=_default_landmarks(),
        face_detected=True,
        frame_width=640,
        frame_height=480,
        frame_timestamp=time.time(),
    )


def make_looking_left_landmarks() -> RawLandmarks:
    return RawLandmarks(
        face_landmarks=_shift_iris_left(_default_landmarks()),
        face_detected=True,
        frame_width=640,
        frame_height=480,
        frame_timestamp=time.time(),
    )


def make_no_face_landmarks() -> RawLandmarks:
    return RawLandmarks(face_detected=False, frame_width=640, frame_height=480)


def make_closed_eyes_landmarks() -> RawLandmarks:
    return RawLandmarks(
        face_landmarks=_make_closed_eyes(_default_landmarks()),
        face_detected=True,
        frame_width=640,
        frame_height=480,
        frame_timestamp=time.time(),
    )


def make_frustrated_landmarks() -> RawLandmarks:
    return RawLandmarks(
        face_landmarks=_make_frustrated(_default_landmarks()),
        face_detected=True,
        frame_width=640,
        frame_height=480,
        frame_timestamp=time.time(),
    )


def make_bored_landmarks() -> RawLandmarks:
    return RawLandmarks(
        face_landmarks=_make_bored(_default_landmarks()),
        face_detected=True,
        frame_width=640,
        frame_height=480,
        frame_timestamp=time.time(),
    )
