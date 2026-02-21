"""
E5 — Transfer Learning.

Question: Does M18 (application testing) improve knowledge transfer?
Design : Control uses traditional factual questions;
         treatment uses NeuroSync application-based questions.
"""

from neurosync.experiments.framework import ExperimentConfig

E5_CONFIG: dict[str, ExperimentConfig] = {
    "control": ExperimentConfig(
        experiment_id="E5",
        name="Transfer Learning — Control",
        hypothesis="Traditional factual questions baseline",
        condition="control",
        lesson_content="content/e5_transfer_topic.mp4",
        duration_minutes=25,
        metrics=[
            "quiz_score", "transfer_score", "explanation_quality",
        ],
        sample_size=40,
    ),
    "treatment": ExperimentConfig(
        experiment_id="E5",
        name="Transfer Learning — Treatment",
        hypothesis="M18 application questions improve transfer",
        condition="treatment",
        lesson_content="content/e5_transfer_topic.mp4",
        duration_minutes=25,
        metrics=[
            "quiz_score", "transfer_score", "explanation_quality",
            "moments_fired",
        ],
        sample_size=40,
    ),
}
