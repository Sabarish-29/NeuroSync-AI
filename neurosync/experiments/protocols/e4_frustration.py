"""
E4 — Frustration & Dropout Prevention.

Question: Does M07 (frustration rescue) reduce dropouts?
Design : Control faces difficult content with no intervention;
         treatment gets NeuroSync rescue on frustration detection.
"""

from neurosync.experiments.framework import ExperimentConfig

E4_CONFIG: dict[str, ExperimentConfig] = {
    "control": ExperimentConfig(
        experiment_id="E4",
        name="Dropout Prevention — Control",
        hypothesis="Difficult content, no frustration rescue",
        condition="control",
        lesson_content="content/e4_difficult_lesson.mp4",
        duration_minutes=30,
        metrics=[
            "completion_rate", "self_report", "dropout_rate",
        ],
        sample_size=60,
    ),
    "treatment": ExperimentConfig(
        experiment_id="E4",
        name="Dropout Prevention — Treatment",
        hypothesis="M07 frustration rescue reduces dropout",
        condition="treatment",
        lesson_content="content/e4_difficult_lesson.mp4",
        duration_minutes=30,
        metrics=[
            "completion_rate", "self_report", "dropout_rate",
            "moments_fired",
        ],
        sample_size=60,
    ),
}
