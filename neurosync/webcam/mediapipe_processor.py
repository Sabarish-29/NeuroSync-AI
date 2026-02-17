"""
NeuroSync AI — MediaPipe raw landmark extractor.

Wraps ``mediapipe.solutions.face_mesh`` and ``mediapipe.solutions.pose``
to extract 478 face landmarks and 33 body landmarks from a single BGR
frame.  Returns a ``RawLandmarks`` dataclass consumed by downstream
signal processors.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional

import cv2
import mediapipe as mp
import numpy as np
from loguru import logger


# =============================================================================
# Landmark index maps (MediaPipe FaceMesh 478-point model)
# =============================================================================

LEFT_EYE_INDICES: list[int] = [
    362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398,
]
RIGHT_EYE_INDICES: list[int] = [
    33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246,
]
LEFT_IRIS_INDICES: list[int] = [468, 469, 470, 471, 472]
RIGHT_IRIS_INDICES: list[int] = [473, 474, 475, 476, 477]

NOSE_TIP: int = 4
FOREHEAD: int = 10
CHIN: int = 152
LEFT_CHEEK: int = 234
RIGHT_CHEEK: int = 454
LEFT_EYEBROW_INNER: int = 336
RIGHT_EYEBROW_INNER: int = 107
UPPER_LIP: int = 13
LOWER_LIP: int = 14

# EAR landmarks (6 points per eye)
LEFT_EAR_POINTS: list[int] = [362, 385, 387, 263, 373, 380]
RIGHT_EAR_POINTS: list[int] = [33, 160, 158, 133, 153, 144]

# Forehead ROI for rPPG
FOREHEAD_ROI_INDICES: list[int] = [10, 338, 297, 332, 284, 251]


# =============================================================================
# Output dataclass
# =============================================================================

@dataclass
class RawLandmarks:
    """Structured output from a single frame processed by MediaPipe."""

    face_landmarks: Optional[list[tuple[float, float, float]]] = None
    pose_landmarks: Optional[list[tuple[float, float, float]]] = None
    frame_timestamp: float = field(default_factory=time.time)
    face_detected: bool = False
    pose_detected: bool = False
    frame_width: int = 0
    frame_height: int = 0


# =============================================================================
# Processor
# =============================================================================

class MediaPipeProcessor:
    """
    Wraps MediaPipe FaceMesh + Pose for single-frame processing.

    Usage::

        mp_proc = MediaPipeProcessor()
        landmarks = mp_proc.process_frame(bgr_frame)
    """

    def __init__(self) -> None:
        self._face_mesh = mp.solutions.face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.5,
        )
        self._pose = mp.solutions.pose.Pose(
            model_complexity=0,
            enable_segmentation=False,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        logger.debug("MediaPipeProcessor initialised (FaceMesh + Pose)")

    # ------------------------------------------------------------------

    def process_frame(self, frame: np.ndarray) -> RawLandmarks:
        """
        Process a single BGR frame and return extracted landmarks.

        Parameters
        ----------
        frame:
            Raw BGR image (H × W × 3) from OpenCV.

        Returns
        -------
        RawLandmarks
            Containing face (478 points) and pose (33 points) if detected.
        """
        h, w = frame.shape[:2]
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        result = RawLandmarks(
            frame_timestamp=time.time(),
            frame_width=w,
            frame_height=h,
        )

        # --- Face mesh ---
        face_result = self._face_mesh.process(rgb)
        if face_result.multi_face_landmarks:  # type: ignore[union-attr]
            lm = face_result.multi_face_landmarks[0]  # type: ignore[union-attr]
            result.face_landmarks = [(p.x, p.y, p.z) for p in lm.landmark]
            result.face_detected = True

        # --- Pose ---
        pose_result = self._pose.process(rgb)
        if pose_result.pose_landmarks:  # type: ignore[union-attr]
            result.pose_landmarks = [
                (p.x, p.y, p.z) for p in pose_result.pose_landmarks.landmark  # type: ignore[union-attr]
            ]
            result.pose_detected = True

        return result

    def close(self) -> None:
        """Release MediaPipe resources."""
        self._face_mesh.close()
        self._pose.close()
        logger.debug("MediaPipeProcessor closed")
