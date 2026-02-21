"""
E1 — Attention Capture Effectiveness.

Question: Does M01 (attention detection) actually improve focus?
Design : Control watches video with no monitoring; treatment gets
         NeuroSync pausing on attention drops.
"""

from neurosync.experiments.framework import ExperimentConfig

E1_CONFIG: dict[str, ExperimentConfig] = {
    "control": ExperimentConfig(
        experiment_id="E1",
        name="Attention Capture — Control",
        hypothesis="Baseline: no attention monitoring",
        condition="control",
        lesson_content="content/e1_attention_video.mp4",
        duration_minutes=15,
        metrics=["quiz_score", "off_screen_time", "self_report"],
        sample_size=30,
    ),
    "treatment": ExperimentConfig(
        experiment_id="E1",
        name="Attention Capture — Treatment",
        hypothesis="M01 attention detection improves focus",
        condition="treatment",
        lesson_content="content/e1_attention_video.mp4",
        duration_minutes=15,
        metrics=[
            "quiz_score", "off_screen_time", "self_report",
            "moments_fired",
        ],
        sample_size=30,
    ),
}

E1_QUIZ = [
    {
        "question": "What is the main function of mitochondria?",
        "options": [
            "Energy production",
            "Protein synthesis",
            "Lipid storage",
            "DNA replication",
        ],
        "correct": 0,
    },
    {
        "question": "Which organelle is responsible for photosynthesis?",
        "options": ["Nucleus", "Chloroplast", "Ribosome", "Golgi apparatus"],
        "correct": 1,
    },
    {
        "question": "What molecule carries genetic information?",
        "options": ["RNA", "Protein", "DNA", "Lipid"],
        "correct": 2,
    },
    {
        "question": "Which process converts glucose to ATP?",
        "options": [
            "Photosynthesis",
            "Fermentation",
            "Cellular respiration",
            "Osmosis",
        ],
        "correct": 2,
    },
    {
        "question": "What is the function of ribosomes?",
        "options": [
            "Lipid synthesis",
            "Protein synthesis",
            "DNA replication",
            "Ion transport",
        ],
        "correct": 1,
    },
    {
        "question": "Which membrane surrounds the nucleus?",
        "options": [
            "Plasma membrane",
            "Nuclear envelope",
            "Cell wall",
            "Thylakoid membrane",
        ],
        "correct": 1,
    },
    {
        "question": "What is the role of the Golgi apparatus?",
        "options": [
            "Protein modification and packaging",
            "Energy production",
            "DNA storage",
            "Cell division",
        ],
        "correct": 0,
    },
    {
        "question": "Which structure maintains cell shape and movement?",
        "options": [
            "Nucleus",
            "Cytoskeleton",
            "Vacuole",
            "Endoplasmic reticulum",
        ],
        "correct": 1,
    },
    {
        "question": "What is osmosis?",
        "options": [
            "Movement of solute across a membrane",
            "Movement of water across a semipermeable membrane",
            "Active transport of ions",
            "Diffusion of gases",
        ],
        "correct": 1,
    },
    {
        "question": "Which organelle degrades cellular waste?",
        "options": ["Lysosome", "Mitochondria", "Ribosome", "Centrosome"],
        "correct": 0,
    },
]
