"""
NeuroSync AI — Knowledge Graph Demo Script.

Walks through Arjun learning photosynthesis, demonstrating all 6
knowledge-graph moment detectors firing in sequence.

Usage:
    python -m scripts.demo_graph

This script does NOT require Neo4j — it uses MockGraphManager.
"""

from __future__ import annotations

import time
import sys

from loguru import logger


def main() -> int:
    # Use MockGraphManager so the demo runs without Neo4j
    from tests.conftest_graph import MockGraphManager
    from neurosync.knowledge.repositories.concepts import ConceptRepository
    from neurosync.knowledge.repositories.students import StudentRepository
    from neurosync.knowledge.repositories.misconceptions import MisconceptionRepository
    from neurosync.knowledge.repositories.mastery import MasteryRepository
    from neurosync.knowledge.detectors.gap_detector import GapDetector
    from neurosync.knowledge.detectors.misconception_detector import MisconceptionDetector
    from neurosync.knowledge.detectors.mastery_checker import MasteryChecker
    from neurosync.knowledge.detectors.plateau_detector import PlateauDetector
    from neurosync.knowledge.detectors.mirror import ConfidenceCollapseMirror
    from neurosync.knowledge.detectors.chunk_tracker import ChunkTracker

    logger.remove()
    logger.add(sys.stderr, level="INFO", format="{message}")

    print("=" * 70)
    print("  NeuroSync AI — Knowledge Graph Demo")
    print("  Arjun Learning Photosynthesis")
    print("=" * 70)

    # --- Setup ---
    gm = MockGraphManager()
    gm.connect()

    concept_repo = ConceptRepository(gm)
    student_repo = StudentRepository(gm)
    mc_repo = MisconceptionRepository(gm)
    mastery_repo = MasteryRepository(gm)

    # Seed concepts
    concepts = [
        ("bio_cells", "Cells", "prerequisite", 0.2, "biology"),
        ("bio_organelles", "Organelles", "prerequisite", 0.25, "biology"),
        ("bio_chloroplast", "Chloroplast", "prerequisite", 0.35, "biology"),
        ("bio_atp", "ATP", "prerequisite", 0.4, "biology"),
        ("bio_enzymes", "Enzymes", "prerequisite", 0.4, "biology"),
        ("bio_photosynthesis", "Photosynthesis", "core", 0.5, "biology"),
        ("bio_light_reactions", "Light Reactions", "core", 0.55, "biology"),
        ("bio_calvin_cycle", "Calvin Cycle", "core", 0.6, "biology"),
    ]
    for cid, name, cat, diff, subj in concepts:
        concept_repo.create_concept(cid, name, cat, diff, subject=subj)

    # Prerequisites
    for cid, pid in [
        ("bio_organelles", "bio_cells"),
        ("bio_chloroplast", "bio_organelles"),
        ("bio_photosynthesis", "bio_chloroplast"),
        ("bio_photosynthesis", "bio_atp"),
        ("bio_photosynthesis", "bio_enzymes"),
        ("bio_light_reactions", "bio_photosynthesis"),
        ("bio_calvin_cycle", "bio_photosynthesis"),
    ]:
        concept_repo.add_prerequisite(cid, pid)

    concept_repo.add_next_concept("bio_photosynthesis", "bio_light_reactions", 1)
    concept_repo.add_next_concept("bio_photosynthesis", "bio_calvin_cycle", 2)

    # Misconceptions
    mc_repo.create_misconception(
        "mc_photo_food", "bio_photosynthesis",
        "Plants get food from soil",
        common_wrong_answer="soil nutrients",
        correction="Plants make their own food using sunlight, CO2, and water",
        severity=0.7,
    )

    # Student
    student_repo.create_student("arjun", "Arjun")
    print("\n[Setup] Seeded 8 concepts, 7 prerequisites, 1 misconception")
    print("[Setup] Student: Arjun\n")

    # Initialise detectors
    gap_det = GapDetector(gm)
    mc_det = MisconceptionDetector(gm)
    mastery_check = MasteryChecker(gm)
    plateau_det = PlateauDetector(gm)
    mirror = ConfidenceCollapseMirror(gm)
    chunk = ChunkTracker(gm)

    # ================================================================
    # Step 1: Arjun starts photosynthesis without prerequisites
    # → M03 Knowledge Gap fires
    # ================================================================
    print("-" * 70)
    print("STEP 1: Arjun attempts Photosynthesis (no prerequisite mastery)")
    print("-" * 70)

    student_repo.record_study("arjun", "bio_photosynthesis", correct=False)
    gap_det.record_attempt("bio_photosynthesis", correct=False)

    prereqs = mastery_repo.get_prerequisite_mastery("arjun", "bio_photosynthesis")
    gap_result = gap_det.detect("arjun", "bio_photosynthesis", prereqs)
    print(f"  M03 Gap Detected: {gap_result.gap_detected}")
    print(f"  Weak Prerequisites: {[p.get('concept_id') for p in gap_result.weak_prerequisites]}")
    print(f"  Strongest Gap: {gap_result.strongest_gap}")
    print(f"  Action: {gap_result.recommended_action}")
    print()

    # ================================================================
    # Step 2: Arjun gives a misconception answer
    # → M15 Misconception fires
    # ================================================================
    print("-" * 70)
    print("STEP 2: Arjun answers 'soil nutrients' (misconception)")
    print("-" * 70)

    known_mc = mc_repo.get_misconceptions_for_concept("bio_photosynthesis")
    mc_result = mc_det.detect("arjun", "bio_photosynthesis", "soil nutrients",
                              student_confidence=4, known_misconceptions=known_mc)
    print(f"  M15 Misconception Detected: {mc_result.misconception_detected}")
    print(f"  Pattern: {mc_result.description}")
    print(f"  Correction: {mc_result.correction}")
    print(f"  Action: {mc_result.recommended_action}")
    print()

    # ================================================================
    # Step 3: Arjun encounters too many new concepts at once
    # → M16 Working Memory Overflow fires
    # ================================================================
    print("-" * 70)
    print("STEP 3: Arjun encounters 5 new concepts rapidly")
    print("-" * 70)

    now = time.time()
    for i, cid in enumerate([
        "bio_cells", "bio_organelles", "bio_chloroplast", "bio_atp", "bio_enzymes",
    ]):
        chunk.record_encounter("arjun", cid, mastery_score=0.1, timestamp=now + i)
        mastery_check.record_encounter("arjun", cid)

    chunk_result = chunk.detect("arjun")
    print(f"  M16 Overflow Detected: {chunk_result.overflow_detected}")
    print(f"  New Concepts: {chunk_result.new_concepts_count} (max {chunk_result.max_allowed})")
    print(f"  Action: {chunk_result.recommended_action}")
    print()

    # ================================================================
    # Step 4: Arjun plateaus on cells
    # → M22 Plateau fires
    # ================================================================
    print("-" * 70)
    print("STEP 4: Arjun plateaus on Cells (score ~0.50, 10 attempts)")
    print("-" * 70)

    for i in range(10):
        plateau_det.record_score("arjun", "bio_cells", 0.50 + (i % 2) * 0.01,
                                 timestamp=now - 1200 + i * 60)
        student_repo.record_study("arjun", "bio_cells", correct=(i % 2 == 0))

    plateau_result = plateau_det.detect("arjun", "bio_cells",
                                        current_score=0.50, attempts=10,
                                        first_seen=now - 1200)
    print(f"  M22 Plateau Detected: {plateau_result.plateau_detected}")
    print(f"  Score: {plateau_result.current_score}, Attempts: {plateau_result.attempts}")
    print(f"  Variance: {plateau_result.score_variance:.4f}")
    print(f"  Action: {plateau_result.recommended_action}")
    print()

    # ================================================================
    # Step 5: Arjun's confidence collapses
    # → M09 Confidence Collapse fires
    # ================================================================
    print("-" * 70)
    print("STEP 5: Arjun's score drops from 0.75 to 0.35 (confidence collapse)")
    print("-" * 70)

    mirror.record_score("arjun", "bio_photosynthesis", 0.80, timestamp=now - 120)
    mirror.record_score("arjun", "bio_photosynthesis", 0.75, timestamp=now - 60)

    collapse_result = mirror.detect("arjun", "bio_photosynthesis",
                                     previous_score=0.75, current_score=0.35)
    print(f"  M09 Collapse Detected: {collapse_result.collapse_detected}")
    print(f"  Score Drop: {collapse_result.score_drop:.2f}")
    print(f"  Recovery Target: {collapse_result.recovery_target:.2f}")
    print(f"  Action: {collapse_result.recommended_action}")
    print()

    # ================================================================
    # Step 6: Arjun masters Cells → M06 Stealth Boredom fires
    # ================================================================
    print("-" * 70)
    print("STEP 6: Arjun masters Cells but keeps seeing it (stealth boredom)")
    print("-" * 70)

    # He already has 10 encounters from step 4, add one more
    mastery_check.record_encounter("arjun", "bio_cells")

    boredom_result = mastery_check.detect(
        "arjun", "bio_cells", mastery_score=0.95,
        next_concepts=[{"concept_id": "bio_organelles", "name": "Organelles"}],
    )
    print(f"  M06 Boredom Detected: {boredom_result.boredom_detected}")
    print(f"  Mastery: {boredom_result.mastery_score}, Repeats: {boredom_result.repeat_count}")
    print(f"  Next Concepts: {boredom_result.recommended_next_concepts}")
    print(f"  Action: {boredom_result.recommended_action}")

    print("\n" + "=" * 70)
    print("  Demo complete — all 6 knowledge graph moments demonstrated!")
    print("=" * 70)

    gm.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
