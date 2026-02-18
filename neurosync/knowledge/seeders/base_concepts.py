"""
NeuroSync AI — Base Concepts Seeder.

Seeds the knowledge graph with ~150 foundational concepts across
multiple subjects. These form the backbone of the learning graph.
"""

from __future__ import annotations

from typing import Any

from loguru import logger


# =============================================================================
# Concept definitions: (concept_id, name, category, difficulty, subject, description)
# =============================================================================
BIOLOGY_CONCEPTS: list[tuple[str, str, str, float, str, str]] = [
    ("bio_cells", "Cells", "prerequisite", 0.2, "biology", "Basic unit of life"),
    ("bio_organelles", "Organelles", "prerequisite", 0.25, "biology", "Cell components: mitochondria, nucleus, etc."),
    ("bio_cell_membrane", "Cell Membrane", "prerequisite", 0.3, "biology", "Selectively permeable boundary"),
    ("bio_diffusion", "Diffusion", "prerequisite", 0.3, "biology", "Movement from high to low concentration"),
    ("bio_osmosis", "Osmosis", "prerequisite", 0.35, "biology", "Water movement across membranes"),
    ("bio_enzymes", "Enzymes", "prerequisite", 0.4, "biology", "Biological catalysts"),
    ("bio_atp", "ATP", "prerequisite", 0.4, "biology", "Adenosine triphosphate — energy currency"),
    ("bio_chloroplast", "Chloroplast", "prerequisite", 0.35, "biology", "Organelle for photosynthesis"),
    ("bio_photosynthesis", "Photosynthesis", "core", 0.5, "biology", "Converting light to chemical energy"),
    ("bio_light_reactions", "Light Reactions", "core", 0.55, "biology", "Photosystem I and II"),
    ("bio_calvin_cycle", "Calvin Cycle", "core", 0.6, "biology", "Carbon fixation cycle"),
    ("bio_cellular_respiration", "Cellular Respiration", "core", 0.55, "biology", "Breaking glucose for ATP"),
    ("bio_glycolysis", "Glycolysis", "core", 0.5, "biology", "Glucose to pyruvate"),
    ("bio_krebs_cycle", "Krebs Cycle", "core", 0.6, "biology", "Citric acid cycle"),
    ("bio_electron_transport", "Electron Transport Chain", "core", 0.65, "biology", "Final stage of aerobic respiration"),
    ("bio_dna", "DNA Structure", "core", 0.45, "biology", "Double helix, nucleotides"),
    ("bio_rna", "RNA", "core", 0.45, "biology", "Ribonucleic acid types"),
    ("bio_transcription", "Transcription", "core", 0.55, "biology", "DNA to mRNA"),
    ("bio_translation", "Translation", "core", 0.6, "biology", "mRNA to protein"),
    ("bio_protein_synthesis", "Protein Synthesis", "extension", 0.65, "biology", "Complete gene expression"),
    ("bio_mitosis", "Mitosis", "core", 0.45, "biology", "Cell division for growth"),
    ("bio_meiosis", "Meiosis", "core", 0.55, "biology", "Cell division for gametes"),
    ("bio_genetics", "Genetics", "core", 0.5, "biology", "Heredity and variation"),
    ("bio_punnett_square", "Punnett Square", "application", 0.4, "biology", "Predicting offspring genotypes"),
    ("bio_evolution", "Evolution", "core", 0.5, "biology", "Change in allele frequencies"),
    ("bio_natural_selection", "Natural Selection", "core", 0.45, "biology", "Survival of the fittest"),
    ("bio_ecology", "Ecology", "core", 0.4, "biology", "Organisms and their environment"),
    ("bio_food_chains", "Food Chains", "prerequisite", 0.3, "biology", "Energy flow in ecosystems"),
    ("bio_ecosystems", "Ecosystems", "core", 0.45, "biology", "Biotic and abiotic interactions"),
    ("bio_carbon_cycle", "Carbon Cycle", "extension", 0.5, "biology", "Carbon movement through Earth systems"),
]

MATH_CONCEPTS: list[tuple[str, str, str, float, str, str]] = [
    ("math_arithmetic", "Arithmetic", "prerequisite", 0.1, "math", "Basic operations"),
    ("math_fractions", "Fractions", "prerequisite", 0.2, "math", "Parts of a whole"),
    ("math_decimals", "Decimals", "prerequisite", 0.2, "math", "Decimal notation"),
    ("math_percentages", "Percentages", "prerequisite", 0.25, "math", "Parts per hundred"),
    ("math_ratios", "Ratios", "prerequisite", 0.25, "math", "Comparing quantities"),
    ("math_exponents", "Exponents", "prerequisite", 0.3, "math", "Powers and roots"),
    ("math_order_ops", "Order of Operations", "prerequisite", 0.2, "math", "PEMDAS/BODMAS"),
    ("math_variables", "Variables", "prerequisite", 0.25, "math", "Unknowns in expressions"),
    ("math_linear_eq", "Linear Equations", "core", 0.35, "math", "ax + b = c"),
    ("math_inequalities", "Inequalities", "core", 0.4, "math", "Greater/less than"),
    ("math_quadratic_eq", "Quadratic Equations", "core", 0.5, "math", "ax² + bx + c = 0"),
    ("math_factoring", "Factoring", "core", 0.45, "math", "Breaking into factors"),
    ("math_functions", "Functions", "core", 0.45, "math", "Input-output relationships"),
    ("math_graphing", "Graphing", "core", 0.4, "math", "Plotting on coordinate plane"),
    ("math_slope", "Slope", "core", 0.4, "math", "Rate of change"),
    ("math_systems_eq", "Systems of Equations", "core", 0.55, "math", "Simultaneous equations"),
    ("math_polynomials", "Polynomials", "core", 0.5, "math", "Multi-term expressions"),
    ("math_trig_basics", "Trigonometry Basics", "core", 0.5, "math", "Sin, cos, tan"),
    ("math_trig_identities", "Trig Identities", "extension", 0.6, "math", "Pythagorean, sum/diff"),
    ("math_logarithms", "Logarithms", "core", 0.55, "math", "Inverse of exponents"),
    ("math_sequences", "Sequences", "core", 0.45, "math", "Arithmetic and geometric"),
    ("math_series", "Series", "core", 0.55, "math", "Sum of sequences"),
    ("math_limits", "Limits", "core", 0.6, "math", "Approaching a value"),
    ("math_derivatives", "Derivatives", "core", 0.65, "math", "Rate of change (calculus)"),
    ("math_integrals", "Integrals", "core", 0.7, "math", "Area under curve"),
    ("math_probability", "Probability", "core", 0.4, "math", "Chance of events"),
    ("math_statistics", "Statistics", "core", 0.45, "math", "Mean, median, mode, std dev"),
    ("math_combinations", "Combinations", "core", 0.5, "math", "nCr"),
    ("math_permutations", "Permutations", "core", 0.5, "math", "nPr"),
    ("math_matrices", "Matrices", "extension", 0.6, "math", "Arrays of numbers"),
]

PHYSICS_CONCEPTS: list[tuple[str, str, str, float, str, str]] = [
    ("phys_units", "Units & Measurement", "prerequisite", 0.15, "physics", "SI units, conversions"),
    ("phys_vectors", "Vectors", "prerequisite", 0.3, "physics", "Magnitude and direction"),
    ("phys_kinematics", "Kinematics", "core", 0.4, "physics", "Motion without forces"),
    ("phys_newtons_laws", "Newton's Laws", "core", 0.45, "physics", "Three laws of motion"),
    ("phys_friction", "Friction", "core", 0.4, "physics", "Resistance to motion"),
    ("phys_work_energy", "Work & Energy", "core", 0.5, "physics", "W = Fd, KE, PE"),
    ("phys_momentum", "Momentum", "core", 0.5, "physics", "p = mv, conservation"),
    ("phys_gravity", "Gravity", "core", 0.4, "physics", "F = Gm1m2/r²"),
    ("phys_projectile", "Projectile Motion", "application", 0.55, "physics", "2D kinematics"),
    ("phys_circular_motion", "Circular Motion", "core", 0.55, "physics", "Centripetal acceleration"),
    ("phys_waves", "Waves", "core", 0.45, "physics", "Transverse and longitudinal"),
    ("phys_sound", "Sound", "core", 0.4, "physics", "Compression waves"),
    ("phys_light", "Light", "core", 0.4, "physics", "Electromagnetic spectrum"),
    ("phys_reflection", "Reflection", "core", 0.35, "physics", "Law of reflection"),
    ("phys_refraction", "Refraction", "core", 0.4, "physics", "Snell's law"),
    ("phys_electricity", "Electricity", "core", 0.5, "physics", "Charge, current, voltage"),
    ("phys_circuits", "Circuits", "core", 0.55, "physics", "Series and parallel"),
    ("phys_magnetism", "Magnetism", "core", 0.5, "physics", "Magnetic fields and forces"),
    ("phys_em_induction", "EM Induction", "extension", 0.6, "physics", "Faraday's law"),
    ("phys_thermodynamics", "Thermodynamics", "core", 0.55, "physics", "Heat, entropy, laws"),
    ("phys_heat_transfer", "Heat Transfer", "core", 0.45, "physics", "Conduction, convection, radiation"),
    ("phys_pressure", "Pressure", "core", 0.4, "physics", "Force per area"),
    ("phys_fluids", "Fluid Mechanics", "extension", 0.55, "physics", "Buoyancy, Bernoulli"),
    ("phys_nuclear", "Nuclear Physics", "extension", 0.6, "physics", "Fission, fusion, decay"),
    ("phys_relativity", "Relativity", "extension", 0.7, "physics", "Special and general"),
]

CHEMISTRY_CONCEPTS: list[tuple[str, str, str, float, str, str]] = [
    ("chem_atoms", "Atoms", "prerequisite", 0.2, "chemistry", "Protons, neutrons, electrons"),
    ("chem_periodic_table", "Periodic Table", "prerequisite", 0.25, "chemistry", "Element organization"),
    ("chem_electron_config", "Electron Configuration", "prerequisite", 0.35, "chemistry", "Orbital filling"),
    ("chem_ionic_bonds", "Ionic Bonds", "core", 0.4, "chemistry", "Electron transfer"),
    ("chem_covalent_bonds", "Covalent Bonds", "core", 0.4, "chemistry", "Electron sharing"),
    ("chem_lewis_structures", "Lewis Structures", "core", 0.45, "chemistry", "Dot diagrams"),
    ("chem_molecular_geometry", "Molecular Geometry", "core", 0.5, "chemistry", "VSEPR theory"),
    ("chem_moles", "Moles", "core", 0.45, "chemistry", "Avogadro's number"),
    ("chem_stoichiometry", "Stoichiometry", "core", 0.55, "chemistry", "Balancing equations"),
    ("chem_gas_laws", "Gas Laws", "core", 0.5, "chemistry", "Boyle, Charles, Ideal"),
    ("chem_solutions", "Solutions", "core", 0.45, "chemistry", "Concentrations, molarity"),
    ("chem_acids_bases", "Acids & Bases", "core", 0.5, "chemistry", "pH, neutralization"),
    ("chem_redox", "Redox Reactions", "core", 0.55, "chemistry", "Oxidation-reduction"),
    ("chem_equilibrium", "Chemical Equilibrium", "core", 0.6, "chemistry", "Le Chatelier's principle"),
    ("chem_kinetics", "Reaction Kinetics", "core", 0.55, "chemistry", "Rate laws, activation energy"),
    ("chem_thermochem", "Thermochemistry", "core", 0.55, "chemistry", "Enthalpy, Hess's law"),
    ("chem_electrochemistry", "Electrochemistry", "extension", 0.6, "chemistry", "Galvanic and electrolytic cells"),
    ("chem_organic_basics", "Organic Chemistry Basics", "core", 0.5, "chemistry", "Hydrocarbons, functional groups"),
    ("chem_polymers", "Polymers", "extension", 0.55, "chemistry", "Addition and condensation"),
    ("chem_nuclear_chem", "Nuclear Chemistry", "extension", 0.6, "chemistry", "Radioactivity, half-life"),
]

CS_CONCEPTS: list[tuple[str, str, str, float, str, str]] = [
    ("cs_variables", "Variables & Data Types", "prerequisite", 0.15, "cs", "Storing data"),
    ("cs_conditionals", "Conditionals", "prerequisite", 0.2, "cs", "If/else branching"),
    ("cs_loops", "Loops", "prerequisite", 0.25, "cs", "For, while iteration"),
    ("cs_functions", "Functions", "core", 0.3, "cs", "Reusable code blocks"),
    ("cs_arrays", "Arrays & Lists", "core", 0.3, "cs", "Ordered collections"),
    ("cs_strings", "String Operations", "core", 0.3, "cs", "Text manipulation"),
    ("cs_recursion", "Recursion", "core", 0.5, "cs", "Self-referencing functions"),
    ("cs_oop_basics", "OOP Basics", "core", 0.4, "cs", "Classes, objects, methods"),
    ("cs_inheritance", "Inheritance", "core", 0.45, "cs", "Class hierarchies"),
    ("cs_polymorphism", "Polymorphism", "core", 0.5, "cs", "Method overriding"),
    ("cs_data_structures", "Data Structures", "core", 0.5, "cs", "Stacks, queues, trees"),
    ("cs_algorithms", "Algorithms", "core", 0.5, "cs", "Searching, sorting"),
    ("cs_big_o", "Big-O Notation", "core", 0.55, "cs", "Time/space complexity"),
    ("cs_sorting", "Sorting Algorithms", "core", 0.5, "cs", "Bubble, merge, quick sort"),
    ("cs_searching", "Searching Algorithms", "core", 0.45, "cs", "Linear, binary search"),
    ("cs_graphs", "Graph Algorithms", "extension", 0.6, "cs", "BFS, DFS, shortest path"),
    ("cs_dynamic_prog", "Dynamic Programming", "extension", 0.7, "cs", "Memoization, tabulation"),
    ("cs_databases", "Databases", "core", 0.45, "cs", "SQL, NoSQL basics"),
    ("cs_networking", "Networking", "core", 0.45, "cs", "TCP/IP, HTTP"),
    ("cs_os_basics", "Operating Systems", "core", 0.5, "cs", "Processes, memory, scheduling"),
]

ALL_CONCEPTS: list[tuple[str, str, str, float, str, str]] = (
    BIOLOGY_CONCEPTS + MATH_CONCEPTS + PHYSICS_CONCEPTS + CHEMISTRY_CONCEPTS + CS_CONCEPTS
)


def seed_concepts(graph_manager: Any) -> int:
    """
    Seed all base concepts into the knowledge graph.

    Returns the number of concepts seeded.
    """
    from neurosync.knowledge.repositories.concepts import ConceptRepository

    repo = ConceptRepository(graph_manager)
    count = 0

    for concept_id, name, category, difficulty, subject, description in ALL_CONCEPTS:
        success = repo.create_concept(
            concept_id=concept_id,
            name=name,
            category=category,
            difficulty=difficulty,
            description=description,
            subject=subject,
        )
        if success:
            count += 1

    logger.info("Seeded {} concepts into the knowledge graph", count)
    return count
