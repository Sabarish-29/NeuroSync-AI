#!/usr/bin/env python
"""
NeuroSync AI — Live Webcam Demo (Step 2).

Opens the laptop webcam and shows a real-time overlay with:
  - Green bounding box around the detected face
  - Gaze direction (on/off screen)
  - Blink rate (blinks/min)
  - Dominant expression
  - Fidget score
  - Red border flash when gaze off-screen trigger fires
  - Yellow border flash when frustration_tension > 0.5

Press Q to quit.

Usage:
    python scripts/demo_webcam.py
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

# Ensure project root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import cv2
import numpy as np
from loguru import logger

from neurosync.webcam.capture import WebcamCapture
from neurosync.webcam.mediapipe_processor import MediaPipeProcessor
from neurosync.webcam.signals.blink import BlinkSignal
from neurosync.webcam.signals.expression import ExpressionSignal
from neurosync.webcam.signals.gaze import GazeSignal
from neurosync.webcam.signals.pose import PoseSignal
from neurosync.webcam.signals.rppg import RemotePPGSignal
from neurosync.webcam.fusion import WebcamFusionEngine


def main() -> None:
    print("=" * 60)
    print("  NeuroSync AI — Live Webcam Demo")
    print("=" * 60)
    print()
    print("Press Q to quit.")
    print()

    # Initialise components
    mp_proc = MediaPipeProcessor()
    gaze = GazeSignal()
    blink = BlinkSignal()
    expression = ExpressionSignal()
    pose = PoseSignal()
    rppg = RemotePPGSignal()
    fusion = WebcamFusionEngine(gaze, blink, expression, pose, rppg)

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("ERROR: Could not open webcam. Check camera permissions.")
        return

    # Stats
    total_frames = 0
    on_screen_frames = 0
    blink_rates: list[float] = []
    expression_counts: dict[str, int] = {}
    fidget_events = 0
    start_time = time.time()

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            total_frames += 1

            # Process landmarks
            landmarks = mp_proc.process_frame(frame)
            scores = fusion.compute(landmarks, frame=frame)

            # Gather individual results for overlay
            gaze_r = gaze.process(landmarks)
            blink_r = blink.process(landmarks)
            expr_r = expression.process(landmarks)
            pose_r = pose.process(landmarks)

            # Track stats
            if gaze_r.on_screen:
                on_screen_frames += 1
            blink_rates.append(blink_r.blink_rate_per_minute)
            expr_label = expr_r.dominant_expression
            expression_counts[expr_label] = expression_counts.get(expr_label, 0) + 1
            if pose_r.fidget_detected:
                fidget_events += 1

            # --- Draw overlay ---
            h, w = frame.shape[:2]

            # Border flash: red for off-screen, yellow for frustration
            border_colour = None
            if scores.off_screen_triggered:
                border_colour = (0, 0, 255)  # red
            elif scores.frustration_boost > 0.5:
                border_colour = (0, 255, 255)  # yellow

            if border_colour is not None:
                cv2.rectangle(frame, (0, 0), (w - 1, h - 1), border_colour, 6)

            # Face bounding box (green)
            if landmarks.face_detected and landmarks.face_landmarks:
                lm = landmarks.face_landmarks
                xs = [p[0] for p in lm]
                ys = [p[1] for p in lm]
                x1, y1 = int(min(xs) * w), int(min(ys) * h)
                x2, y2 = int(max(xs) * w), int(max(ys) * h)
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

            # Text overlay
            y_off = 30
            lines = [
                f"Gaze: {'ON SCREEN' if gaze_r.on_screen else gaze_r.gaze_direction.upper()}",
                f"Blink rate: {blink_r.blink_rate_per_minute:.0f}/min",
                f"Expression: {expr_r.dominant_expression}",
                f"Fidget: {'HIGH' if pose_r.fidget_detected else 'low'} ({pose_r.fidget_score:.2f})",
                f"Attention: {scores.attention_score:.2f}",
                f"Frustration: {scores.frustration_boost:.2f}",
            ]
            if scores.heart_rate_bpm is not None:
                lines.append(f"Heart rate: {scores.heart_rate_bpm:.0f} bpm")

            for line in lines:
                cv2.putText(
                    frame, line, (10, y_off),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2,
                )
                y_off += 28

            cv2.imshow("NeuroSync AI — Webcam Demo", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    except KeyboardInterrupt:
        pass
    finally:
        cap.release()
        cv2.destroyAllWindows()
        mp_proc.close()

    # Print summary
    elapsed = time.time() - start_time
    print()
    print("-" * 60)
    print("  Session Summary")
    print("-" * 60)
    pct = (on_screen_frames / total_frames * 100) if total_frames > 0 else 0
    print(f"  Duration: {elapsed:.1f}s ({total_frames} frames)")
    print(f"  Gaze: {pct:.0f}% on screen")
    avg_blink = sum(blink_rates) / len(blink_rates) if blink_rates else 0
    print(f"  Blink rate avg: {avg_blink:.1f}/min")
    dominant_expr = max(expression_counts, key=expression_counts.get) if expression_counts else "N/A"
    print(f"  Dominant expression: {dominant_expr}")
    print(f"  Fidget events: {fidget_events}")
    print("-" * 60)


if __name__ == "__main__":
    main()
