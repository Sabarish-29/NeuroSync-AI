"""
NeuroSync AI — Prerequisites Seeder.

Defines prerequisite relationships between concepts.
"""

from __future__ import annotations

from typing import Any

from loguru import logger


# =============================================================================
# Prerequisite edges: (concept_id, prerequisite_id, weight, description)
# =============================================================================
BIOLOGY_PREREQUISITES: list[tuple[str, str, float, str]] = [
    ("bio_organelles", "bio_cells", 1.0, "Must understand cells before organelles"),
    ("bio_cell_membrane", "bio_cells", 1.0, "Membrane is part of cell"),
    ("bio_osmosis", "bio_diffusion", 0.9, "Osmosis is special diffusion"),
    ("bio_osmosis", "bio_cell_membrane", 0.8, "Osmosis occurs across membranes"),
    ("bio_chloroplast", "bio_organelles", 0.8, "Chloroplast is an organelle"),
    ("bio_photosynthesis", "bio_chloroplast", 1.0, "Occurs in chloroplasts"),
    ("bio_photosynthesis", "bio_atp", 0.9, "Produces ATP"),
    ("bio_photosynthesis", "bio_enzymes", 0.7, "Enzyme-catalysed reactions"),
    ("bio_light_reactions", "bio_photosynthesis", 1.0, "Part of photosynthesis"),
    ("bio_calvin_cycle", "bio_photosynthesis", 1.0, "Part of photosynthesis"),
    ("bio_calvin_cycle", "bio_light_reactions", 0.8, "Uses products of light reactions"),
    ("bio_cellular_respiration", "bio_atp", 1.0, "Produces ATP"),
    ("bio_cellular_respiration", "bio_enzymes", 0.7, "Enzyme-catalysed"),
    ("bio_glycolysis", "bio_cellular_respiration", 1.0, "First stage of respiration"),
    ("bio_krebs_cycle", "bio_glycolysis", 0.9, "Follows glycolysis"),
    ("bio_electron_transport", "bio_krebs_cycle", 0.9, "Follows Krebs cycle"),
    ("bio_rna", "bio_dna", 0.9, "Transcribed from DNA"),
    ("bio_transcription", "bio_dna", 1.0, "Requires DNA understanding"),
    ("bio_transcription", "bio_rna", 0.9, "Produces RNA"),
    ("bio_translation", "bio_rna", 1.0, "Uses mRNA"),
    ("bio_translation", "bio_transcription", 0.9, "Must understand transcription first"),
    ("bio_protein_synthesis", "bio_transcription", 1.0, "Includes transcription"),
    ("bio_protein_synthesis", "bio_translation", 1.0, "Includes translation"),
    ("bio_meiosis", "bio_mitosis", 0.9, "Builds on mitosis concepts"),
    ("bio_genetics", "bio_dna", 0.9, "DNA is the genetic material"),
    ("bio_punnett_square", "bio_genetics", 1.0, "Tool for genetics"),
    ("bio_natural_selection", "bio_genetics", 0.8, "Acts on genetic variation"),
    ("bio_evolution", "bio_natural_selection", 0.9, "Mechanism of evolution"),
    ("bio_food_chains", "bio_ecology", 0.8, "Part of ecology"),
    ("bio_ecosystems", "bio_ecology", 0.9, "Ecosystem study"),
    ("bio_ecosystems", "bio_food_chains", 0.7, "Food chains in ecosystems"),
    ("bio_carbon_cycle", "bio_ecosystems", 0.7, "Carbon moves through ecosystems"),
    ("bio_carbon_cycle", "bio_photosynthesis", 0.8, "Photosynthesis fixes carbon"),
    ("bio_carbon_cycle", "bio_cellular_respiration", 0.8, "Respiration releases carbon"),
]

MATH_PREREQUISITES: list[tuple[str, str, float, str]] = [
    ("math_fractions", "math_arithmetic", 1.0, "Fractions use arithmetic"),
    ("math_decimals", "math_arithmetic", 1.0, "Decimals use arithmetic"),
    ("math_percentages", "math_fractions", 0.8, "Percentages are fractions of 100"),
    ("math_percentages", "math_decimals", 0.8, "Converting decimals to %"),
    ("math_ratios", "math_fractions", 0.9, "Ratios compare like fractions"),
    ("math_exponents", "math_arithmetic", 0.9, "Powers use multiplication"),
    ("math_variables", "math_arithmetic", 0.8, "Variables represent numbers"),
    ("math_linear_eq", "math_variables", 1.0, "Equations use variables"),
    ("math_linear_eq", "math_order_ops", 0.8, "Order matters in solving"),
    ("math_inequalities", "math_linear_eq", 0.9, "Similar to equations"),
    ("math_quadratic_eq", "math_linear_eq", 0.9, "Extension of equations"),
    ("math_quadratic_eq", "math_exponents", 0.8, "Uses squared terms"),
    ("math_factoring", "math_quadratic_eq", 0.9, "Factoring solves quadratics"),
    ("math_functions", "math_variables", 1.0, "Functions map inputs to outputs"),
    ("math_graphing", "math_functions", 0.8, "Graphing functions"),
    ("math_slope", "math_graphing", 0.9, "Slope is a graph property"),
    ("math_slope", "math_linear_eq", 0.8, "Slope in linear equations"),
    ("math_systems_eq", "math_linear_eq", 1.0, "Multiple linear equations"),
    ("math_polynomials", "math_quadratic_eq", 0.8, "Generalization of quadratics"),
    ("math_trig_basics", "math_ratios", 0.7, "Trig ratios"),
    ("math_trig_identities", "math_trig_basics", 1.0, "Build on trig basics"),
    ("math_logarithms", "math_exponents", 1.0, "Inverse of exponents"),
    ("math_sequences", "math_functions", 0.7, "Special function patterns"),
    ("math_series", "math_sequences", 1.0, "Summing sequences"),
    ("math_limits", "math_functions", 0.9, "Limits of functions"),
    ("math_derivatives", "math_limits", 1.0, "Defined via limits"),
    ("math_integrals", "math_derivatives", 0.9, "Inverse of differentiation"),
    ("math_combinations", "math_factoring", 0.6, "Uses factorial"),
    ("math_permutations", "math_combinations", 0.8, "Related to combinations"),
    ("math_probability", "math_ratios", 0.8, "Probability as ratios"),
    ("math_statistics", "math_arithmetic", 0.7, "Averages use arithmetic"),
    ("math_matrices", "math_systems_eq", 0.7, "Matrix methods for systems"),
]

PHYSICS_PREREQUISITES: list[tuple[str, str, float, str]] = [
    ("phys_vectors", "phys_units", 0.8, "Vectors have units"),
    ("phys_kinematics", "phys_vectors", 0.9, "Motion uses vectors"),
    ("phys_kinematics", "phys_units", 1.0, "Requires proper units"),
    ("phys_newtons_laws", "phys_kinematics", 0.9, "Laws describe motion"),
    ("phys_friction", "phys_newtons_laws", 0.9, "Friction is a force"),
    ("phys_work_energy", "phys_newtons_laws", 1.0, "Work = Force × distance"),
    ("phys_momentum", "phys_newtons_laws", 0.9, "F = dp/dt"),
    ("phys_gravity", "phys_newtons_laws", 0.8, "Gravity is a force"),
    ("phys_projectile", "phys_kinematics", 1.0, "2D motion"),
    ("phys_projectile", "phys_gravity", 0.9, "Gravity affects trajectory"),
    ("phys_circular_motion", "phys_newtons_laws", 0.9, "Centripetal force"),
    ("phys_waves", "phys_kinematics", 0.6, "Wave motion"),
    ("phys_sound", "phys_waves", 1.0, "Sound is a wave"),
    ("phys_light", "phys_waves", 0.9, "Light is EM wave"),
    ("phys_reflection", "phys_light", 0.9, "Light reflects"),
    ("phys_refraction", "phys_light", 0.9, "Light refracts"),
    ("phys_electricity", "phys_units", 0.8, "Electrical units"),
    ("phys_circuits", "phys_electricity", 1.0, "Circuits use electricity"),
    ("phys_magnetism", "phys_electricity", 0.7, "EM relationship"),
    ("phys_em_induction", "phys_magnetism", 1.0, "Changing B field"),
    ("phys_em_induction", "phys_electricity", 0.9, "Generates current"),
    ("phys_thermodynamics", "phys_work_energy", 0.7, "Energy and heat"),
    ("phys_heat_transfer", "phys_thermodynamics", 0.9, "Modes of heat transfer"),
    ("phys_pressure", "phys_newtons_laws", 0.7, "F/A"),
    ("phys_fluids", "phys_pressure", 1.0, "Fluid pressure"),
    ("phys_nuclear", "phys_work_energy", 0.6, "Nuclear energy"),
]

ALL_PREREQUISITES: list[tuple[str, str, float, str]] = (
    BIOLOGY_PREREQUISITES + MATH_PREREQUISITES + PHYSICS_PREREQUISITES
)


def seed_prerequisites(graph_manager: Any) -> int:
    """
    Seed prerequisite relationships into the knowledge graph.

    Returns the number of relationships created.
    """
    from neurosync.knowledge.repositories.concepts import ConceptRepository

    repo = ConceptRepository(graph_manager)
    count = 0

    for concept_id, prerequisite_id, weight, description in ALL_PREREQUISITES:
        success = repo.add_prerequisite(
            concept_id=concept_id,
            prerequisite_id=prerequisite_id,
            weight=weight,
            description=description,
        )
        if success:
            count += 1

    logger.info("Seeded {} prerequisite relationships", count)
    return count


def seed_all(graph_manager: Any) -> dict[str, int]:
    """Seed both concepts and prerequisites. Returns counts."""
    from neurosync.knowledge.seeders.base_concepts import seed_concepts

    concept_count = seed_concepts(graph_manager)
    prereq_count = seed_prerequisites(graph_manager)
    return {"concepts": concept_count, "prerequisites": prereq_count}
