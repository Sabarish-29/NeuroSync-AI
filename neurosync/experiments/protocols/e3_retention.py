"""
E3 — Long-Term Retention.

Question: Does M17 (personalised spaced repetition) improve retention?
Design : Control uses fixed schedule (1d, 3d, 7d reviews);
         treatment uses NeuroSync adaptive forgetting curves.
"""

from neurosync.experiments.framework import ExperimentConfig

E3_CONFIG: dict[str, ExperimentConfig] = {
    "control": ExperimentConfig(
        experiment_id="E3",
        name="Retention — Control (Fixed Schedule)",
        hypothesis="Fixed review schedule baseline retention",
        condition="control",
        lesson_content="content/e3_retention_topic.mp4",
        duration_minutes=20,
        metrics=[
            "quiz_score", "retention_day_7", "retention_day_30",
            "review_count",
        ],
        sample_size=50,
    ),
    "treatment": ExperimentConfig(
        experiment_id="E3",
        name="Retention — Treatment (Adaptive)",
        hypothesis="M17 personalised curves improve long-term retention",
        condition="treatment",
        lesson_content="content/e3_retention_topic.mp4",
        duration_minutes=20,
        metrics=[
            "quiz_score", "retention_day_7", "retention_day_30",
            "review_count", "moments_fired",
        ],
        sample_size=50,
    ),
}
