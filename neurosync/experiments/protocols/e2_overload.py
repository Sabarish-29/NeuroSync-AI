"""
E2 — Cognitive Load Management.

Question: Does M02 (overload detection) improve comprehension?
Design : Control gets dense content with no simplification;
         treatment gets NeuroSync simplifying on overload.
"""

from neurosync.experiments.framework import ExperimentConfig

E2_CONFIG: dict[str, ExperimentConfig] = {
    "control": ExperimentConfig(
        experiment_id="E2",
        name="Cognitive Load — Control",
        hypothesis="Dense content, no AI simplification",
        condition="control",
        lesson_content="content/e2_complex_topic.mp4",
        duration_minutes=20,
        metrics=[
            "quiz_score", "rewind_count", "completion_rate",
            "self_report",
        ],
        sample_size=40,
    ),
    "treatment": ExperimentConfig(
        experiment_id="E2",
        name="Cognitive Load — Treatment",
        hypothesis="M02 overload detection improves comprehension",
        condition="treatment",
        lesson_content="content/e2_complex_topic.mp4",
        duration_minutes=20,
        metrics=[
            "quiz_score", "rewind_count", "completion_rate",
            "self_report", "moments_fired",
        ],
        sample_size=40,
    ),
}
