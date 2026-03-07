#!/usr/bin/env python3
"""
Create 5 source PDFs for NeuroSync sample content generation.

Uses reportlab to produce clean, multi-page educational PDFs
covering CBSE Grade 9-10 topics.

Usage:
    python scripts/create_source_pdfs.py
"""

from __future__ import annotations

from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "sample_content" / "source_pdfs"

# ── shared styles ─────────────────────────────────────────────────────

_base = getSampleStyleSheet()

TITLE_STYLE = ParagraphStyle(
    "PDFTitle",
    parent=_base["Title"],
    fontSize=22,
    spaceAfter=24,
)

HEADING_STYLE = ParagraphStyle(
    "PDFHeading",
    parent=_base["Heading1"],
    fontSize=16,
    spaceBefore=18,
    spaceAfter=10,
)

SUB_HEADING_STYLE = ParagraphStyle(
    "PDFSubHeading",
    parent=_base["Heading2"],
    fontSize=13,
    spaceBefore=12,
    spaceAfter=8,
)

BODY_STYLE = ParagraphStyle(
    "PDFBody",
    parent=_base["BodyText"],
    fontSize=11,
    leading=16,
    spaceAfter=8,
)


def _build(filename: str, story: list) -> Path:
    path = OUTPUT_DIR / filename
    doc = SimpleDocTemplate(
        str(path),
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )
    doc.build(story)
    print(f"  Created {path.name} ({path.stat().st_size / 1024:.0f} KB)")
    return path


def _p(text: str, style=BODY_STYLE) -> Paragraph:
    return Paragraph(text, style)


def _gap(h: float = 0.3) -> Spacer:
    return Spacer(1, h * cm)


# ── 1. Photosynthesis ─────────────────────────────────────────────────


def create_photosynthesis() -> Path:
    s: list = []

    s.append(_p("Photosynthesis: How Plants Make Food", TITLE_STYLE))
    s.append(_p("CBSE Grade 10 Biology", SUB_HEADING_STYLE))
    s.append(_gap())

    s.append(_p("Introduction", HEADING_STYLE))
    s.append(_p(
        "Photosynthesis is the process by which green plants, algae, and certain bacteria "
        "convert light energy into chemical energy stored in glucose. It is fundamental to "
        "life on Earth because it produces the oxygen we breathe and forms the base of "
        "almost every food chain."
    ))
    s.append(_p(
        "The overall equation for photosynthesis is: "
        "6CO2 + 6H2O + light energy -> C6H12O6 + 6O2. "
        "This means six molecules of carbon dioxide react with six molecules of water, "
        "using sunlight, to produce one molecule of glucose and six molecules of oxygen."
    ))
    s.append(_p(
        "Photosynthesis takes place primarily in the leaves of plants, within specialised "
        "organelles called chloroplasts. Chloroplasts contain a green pigment called "
        "chlorophyll, which absorbs light energy from the sun. The absorbed energy drives "
        "the chemical reactions that convert carbon dioxide and water into glucose."
    ))

    s.append(_p("Light-Dependent Reactions", HEADING_STYLE))
    s.append(_p(
        "The light-dependent reactions occur in the thylakoid membranes of the chloroplast. "
        "When chlorophyll absorbs photons of light, the energy is used to split water "
        "molecules (photolysis): 2H2O -> 4H+ + 4e- + O2. The oxygen is released as a "
        "by-product."
    ))
    s.append(_p(
        "The energised electrons pass along an electron transport chain embedded in the "
        "thylakoid membrane. As they move through the chain, their energy is used to pump "
        "hydrogen ions across the membrane, creating a concentration gradient. This gradient "
        "drives ATP synthase, which produces ATP from ADP and inorganic phosphate."
    ))
    s.append(_p(
        "At the end of the electron transport chain, the electrons are accepted by NADP+, "
        "which combines with hydrogen ions to form NADPH. Together, ATP and NADPH are the "
        "energy carriers that power the next stage of photosynthesis."
    ))

    s.append(_p("The Calvin Cycle (Light-Independent Reactions)", HEADING_STYLE))
    s.append(_p(
        "The Calvin cycle takes place in the stroma of the chloroplast. It uses the ATP and "
        "NADPH produced during the light-dependent reactions to fix carbon dioxide into "
        "organic molecules."
    ))
    s.append(_p(
        "The cycle begins when CO2 combines with a five-carbon sugar called ribulose "
        "bisphosphate (RuBP), catalysed by the enzyme RuBisCO. This produces two molecules "
        "of a three-carbon compound called glycerate 3-phosphate (G3P)."
    ))
    s.append(_p(
        "G3P is then reduced to glyceraldehyde 3-phosphate (GALP) using ATP and NADPH. "
        "Some GALP molecules are used to synthesise glucose and other organic molecules, "
        "while the rest are recycled to regenerate RuBP, allowing the cycle to continue."
    ))

    s.append(_p("Factors Affecting Photosynthesis", HEADING_STYLE))
    s.append(_p(
        "Light intensity: As light intensity increases, the rate of photosynthesis increases "
        "proportionally, up to a saturation point. Beyond this point, other factors become "
        "limiting. In very low light, the rate of respiration exceeds photosynthesis, so "
        "there is a net release of CO2."
    ))
    s.append(_p(
        "Carbon dioxide concentration: CO2 is a raw material for the Calvin cycle. "
        "Increasing CO2 concentration raises the rate of photosynthesis until other factors "
        "(such as RuBisCO saturation or light availability) become limiting."
    ))
    s.append(_p(
        "Temperature: Photosynthesis is enzyme-driven, so temperature has a significant "
        "effect. The rate typically doubles for every 10 degrees Celsius rise, up to an "
        "optimum (usually 25-35 degrees Celsius for most plants). Beyond the optimum, "
        "enzymes denature and the rate drops sharply."
    ))
    s.append(_p(
        "Water availability: Water is a reactant in the light-dependent reactions. "
        "Water stress causes stomata to close, reducing CO2 intake and thereby lowering "
        "the rate of photosynthesis."
    ))

    s.append(_p("Summary and Key Equations", HEADING_STYLE))
    s.append(_p(
        "Photosynthesis can be summarised as: 6CO2 + 6H2O + light -> C6H12O6 + 6O2. "
        "It occurs in two stages: the light-dependent reactions (thylakoid membranes) "
        "produce ATP and NADPH, and the Calvin cycle (stroma) uses them to fix CO2 into "
        "glucose. The process is affected by light intensity, CO2 concentration, "
        "temperature, and water availability."
    ))

    return _build("photosynthesis.pdf", s)


# ── 2. Newton's Laws ─────────────────────────────────────────────────


def create_newtons_laws() -> Path:
    s: list = []

    s.append(_p("Newton's Laws of Motion", TITLE_STYLE))
    s.append(_p("CBSE Grade 9 Physics", SUB_HEADING_STYLE))
    s.append(_gap())

    s.append(_p("Introduction to Motion", HEADING_STYLE))
    s.append(_p(
        "Motion is a change in the position of an object with respect to time and a "
        "reference point. Sir Isaac Newton (1642-1727) formulated three fundamental laws "
        "that describe the relationship between the motion of an object and the forces "
        "acting on it. These laws form the foundation of classical mechanics."
    ))
    s.append(_p(
        "Key concepts: Velocity is the rate of change of displacement (m/s). Acceleration "
        "is the rate of change of velocity (m/s squared). Force is a push or pull that "
        "can change the state of motion of an object, measured in Newtons (N)."
    ))

    s.append(_p("Newton's First Law: The Law of Inertia", HEADING_STYLE))
    s.append(_p(
        "Statement: An object at rest stays at rest, and an object in motion stays in motion "
        "with the same speed and direction, unless acted upon by an unbalanced external force."
    ))
    s.append(_p(
        "Inertia is the tendency of an object to resist changes in its state of motion. "
        "The mass of an object is a measure of its inertia; heavier objects have greater "
        "inertia. For example, it is harder to push a loaded truck than an empty one."
    ))
    s.append(_p(
        "Examples: A ball rolling on a frictionless surface would roll forever. Passengers "
        "in a bus lurch forward when the bus stops suddenly because their bodies tend to "
        "continue moving. A coin on a cardboard placed over a glass falls into the glass "
        "when the cardboard is flicked away."
    ))

    s.append(_p("Newton's Second Law: Force and Acceleration", HEADING_STYLE))
    s.append(_p(
        "Statement: The net force acting on an object equals the mass of the object "
        "multiplied by its acceleration. Mathematically: F = m x a, where F is force in "
        "Newtons, m is mass in kilograms, and a is acceleration in m/s squared."
    ))
    s.append(_p(
        "This law tells us two things: (1) The acceleration of an object is directly "
        "proportional to the net force acting on it. Double the force, double the "
        "acceleration. (2) The acceleration is inversely proportional to the mass. "
        "For the same force, a heavier object accelerates less."
    ))
    s.append(_p(
        "Example calculation: A force of 20 N acts on a 4 kg object. What is the "
        "acceleration? a = F / m = 20 / 4 = 5 m/s squared. If the same force acts on a "
        "10 kg object: a = 20 / 10 = 2 m/s squared."
    ))

    s.append(_p("Newton's Third Law: Action and Reaction", HEADING_STYLE))
    s.append(_p(
        "Statement: For every action, there is an equal and opposite reaction. When object "
        "A exerts a force on object B, object B simultaneously exerts a force equal in "
        "magnitude but opposite in direction on object A."
    ))
    s.append(_p(
        "Important: The action and reaction forces act on different objects. They do not "
        "cancel each other because they act on different bodies."
    ))
    s.append(_p(
        "Examples: When you walk, your foot pushes the ground backward (action) and the "
        "ground pushes your foot forward (reaction). A rocket expels gas downward (action) "
        "and the gas pushes the rocket upward (reaction). When you swim, you push water "
        "backward and the water pushes you forward."
    ))

    s.append(_p("Applications and Problem Solving", HEADING_STYLE))
    s.append(_p(
        "Free body diagrams: To solve problems using Newton's laws, draw all forces acting "
        "on the object. Common forces include: weight (mg, downward), normal force "
        "(perpendicular to surface), friction (opposing motion), tension (along a rope), "
        "and applied force."
    ))
    s.append(_p(
        "Practice problem: A 5 kg block is pushed across a floor with a force of 30 N. "
        "The friction force is 10 N. Find the acceleration. Net force = 30 - 10 = 20 N. "
        "a = F / m = 20 / 5 = 4 m/s squared."
    ))

    return _build("newtons_laws.pdf", s)


# ── 3. Cell Structure ────────────────────────────────────────────────


def create_cell_structure() -> Path:
    s: list = []

    s.append(_p("Cell Structure and Function", TITLE_STYLE))
    s.append(_p("CBSE Grade 9 Biology", SUB_HEADING_STYLE))
    s.append(_gap())

    s.append(_p("Introduction to Cells", HEADING_STYLE))
    s.append(_p(
        "The cell is the basic structural and functional unit of all living organisms. "
        "Cell theory states three fundamental principles: (1) All living things are made "
        "of cells. (2) The cell is the basic unit of life. (3) All cells arise from "
        "pre-existing cells."
    ))
    s.append(_p(
        "Cells are broadly classified into two types: prokaryotic cells (bacteria and "
        "archaea), which lack a membrane-bound nucleus, and eukaryotic cells (plants, "
        "animals, fungi, protists), which have a true nucleus enclosed by a nuclear "
        "membrane."
    ))

    s.append(_p("Cell Membrane and Cytoplasm", HEADING_STYLE))
    s.append(_p(
        "The cell membrane (plasma membrane) is a thin, flexible barrier that surrounds "
        "every cell. It is composed of a phospholipid bilayer with embedded proteins. "
        "The phospholipids have hydrophilic (water-loving) heads facing outward and "
        "hydrophobic (water-fearing) tails facing inward."
    ))
    s.append(_p(
        "The cell membrane is selectively permeable, meaning it allows certain molecules "
        "to pass through while blocking others. Small nonpolar molecules (like oxygen and "
        "carbon dioxide) pass freely, while large or charged molecules require transport "
        "proteins."
    ))
    s.append(_p(
        "The cytoplasm is the gel-like substance that fills the cell between the cell "
        "membrane and the nucleus. It contains water, salts, organic molecules, and the "
        "cytoskeleton (a network of protein filaments). Most cellular activities occur "
        "in the cytoplasm."
    ))

    s.append(_p("Key Organelles: Part 1", HEADING_STYLE))
    s.append(_p(
        "Nucleus: The nucleus is the control centre of the cell. It contains the cell's "
        "DNA (genetic material) organised into chromosomes. The nucleus is surrounded by "
        "a double membrane called the nuclear envelope, which has pores for transport. "
        "Inside, the nucleolus produces ribosomal RNA."
    ))
    s.append(_p(
        "Mitochondria: Often called the 'powerhouse of the cell,' mitochondria generate "
        "ATP through cellular respiration. They have a double membrane: the outer membrane "
        "is smooth, while the inner membrane is folded into cristae to increase surface "
        "area. Mitochondria have their own DNA."
    ))
    s.append(_p(
        "Endoplasmic Reticulum (ER): The ER is a network of membranes. Rough ER has "
        "ribosomes on its surface and is involved in protein synthesis and modification. "
        "Smooth ER lacks ribosomes and is involved in lipid synthesis and detoxification."
    ))
    s.append(_p(
        "Golgi Apparatus: The Golgi apparatus processes, packages, and ships proteins and "
        "lipids received from the ER. It consists of flattened membrane sacs called "
        "cisternae. It also produces lysosomes."
    ))

    s.append(_p("Key Organelles: Part 2", HEADING_STYLE))
    s.append(_p(
        "Ribosomes: Ribosomes are the sites of protein synthesis. They can be free in the "
        "cytoplasm or attached to the rough ER. Each ribosome consists of two subunits "
        "made of ribosomal RNA and proteins."
    ))
    s.append(_p(
        "Lysosomes: Lysosomes are membrane-bound vesicles containing digestive enzymes. "
        "They break down waste materials, cellular debris, and foreign invaders. They "
        "maintain an acidic internal pH for optimal enzyme activity."
    ))
    s.append(_p(
        "Chloroplasts (plant cells only): Chloroplasts are the site of photosynthesis. "
        "They contain the green pigment chlorophyll, which captures light energy. "
        "Chloroplasts have a double outer membrane and internal thylakoid membranes "
        "arranged in stacks called grana."
    ))
    s.append(_p(
        "Vacuoles: Plant cells have a large central vacuole that stores water, nutrients, "
        "and waste products. It maintains turgor pressure, which helps the plant stay "
        "rigid. Animal cells have smaller vacuoles."
    ))

    s.append(_p("Plant vs Animal Cells", HEADING_STYLE))
    s.append(_p(
        "Plant cells have several structures absent in animal cells: a rigid cell wall "
        "(made of cellulose) outside the cell membrane, chloroplasts for photosynthesis, "
        "and a large central vacuole. Animal cells have centrioles (used in cell division) "
        "that plant cells lack. Both have a nucleus, mitochondria, ER, Golgi apparatus, "
        "ribosomes, and a cell membrane."
    ))

    return _build("cell_structure.pdf", s)


# ── 4. Chemical Bonding ──────────────────────────────────────────────


def create_chemical_bonds() -> Path:
    s: list = []

    s.append(_p("Chemical Bonding", TITLE_STYLE))
    s.append(_p("CBSE Grade 10 Chemistry", SUB_HEADING_STYLE))
    s.append(_gap())

    s.append(_p("Introduction to Chemical Bonds", HEADING_STYLE))
    s.append(_p(
        "A chemical bond is a lasting attraction between atoms that enables the formation "
        "of molecules and compounds. Atoms bond to achieve a more stable electron "
        "configuration, typically by attaining a full outer shell of electrons (the octet "
        "rule: 8 electrons in the outermost shell, or 2 for hydrogen and helium)."
    ))
    s.append(_p(
        "There are three main types of chemical bonds: ionic bonds (transfer of electrons), "
        "covalent bonds (sharing of electrons), and metallic bonds (delocalised electron "
        "sea). The type of bond formed depends on the electronegativity difference between "
        "the atoms involved."
    ))

    s.append(_p("Ionic Bonding", HEADING_STYLE))
    s.append(_p(
        "Ionic bonds form when one atom transfers one or more electrons to another atom. "
        "This typically occurs between a metal (which loses electrons to form a positive "
        "cation) and a non-metal (which gains electrons to form a negative anion). The "
        "electrostatic attraction between the oppositely charged ions creates the bond."
    ))
    s.append(_p(
        "Example: Sodium chloride (NaCl). Sodium (Na) has 1 electron in its outer shell; "
        "it loses this electron to become Na+. Chlorine (Cl) has 7 electrons in its outer "
        "shell; it gains one electron to become Cl-. The Na+ and Cl- ions attract each "
        "other to form NaCl."
    ))
    s.append(_p(
        "Properties of ionic compounds: high melting and boiling points (strong "
        "electrostatic forces), soluble in water, conduct electricity when dissolved or "
        "molten (free ions carry charge), form crystalline lattice structures, and are "
        "brittle (displaced layers repel)."
    ))

    s.append(_p("Covalent Bonding", HEADING_STYLE))
    s.append(_p(
        "Covalent bonds form when two atoms share one or more pairs of electrons. This "
        "typically occurs between two non-metal atoms. Each shared pair of electrons "
        "constitutes one covalent bond. A single bond shares 1 pair, a double bond shares "
        "2 pairs, and a triple bond shares 3 pairs."
    ))
    s.append(_p(
        "Examples: Water (H2O) has two single covalent bonds between oxygen and hydrogen. "
        "Carbon dioxide (CO2) has two double bonds between carbon and oxygen. Nitrogen gas "
        "(N2) has a triple bond between the two nitrogen atoms."
    ))
    s.append(_p(
        "Properties of covalent compounds: generally lower melting and boiling points than "
        "ionic compounds (weaker intermolecular forces), many are gases or liquids at room "
        "temperature, usually insoluble in water but soluble in organic solvents, and do "
        "not conduct electricity (no free ions or electrons)."
    ))

    s.append(_p("Metallic Bonding", HEADING_STYLE))
    s.append(_p(
        "Metallic bonds occur in metals, where atoms release their outer electrons into a "
        "shared 'sea' of delocalised electrons. The positive metal ions are arranged in a "
        "regular lattice and are held together by the attraction to this electron sea."
    ))
    s.append(_p(
        "Properties of metals (explained by metallic bonding): good electrical and thermal "
        "conductivity (delocalised electrons carry charge and heat), malleability and "
        "ductility (layers of ions can slide over each other without breaking the bond), "
        "high melting points (strong metallic bonds), and lustrous appearance (electrons "
        "reflect light)."
    ))

    s.append(_p("Comparing Bond Types", HEADING_STYLE))
    s.append(_p(
        "Ionic bonds: formed between metals and non-metals by electron transfer. High "
        "melting point. Conduct electricity in solution. Example: NaCl, MgO, CaF2."
    ))
    s.append(_p(
        "Covalent bonds: formed between non-metals by electron sharing. Lower melting "
        "point. Do not conduct electricity. Example: H2O, CO2, CH4."
    ))
    s.append(_p(
        "Metallic bonds: formed between metal atoms via delocalised electrons. Variable "
        "melting points. Conduct electricity as solids. Example: Fe, Cu, Al."
    ))
    s.append(_p(
        "To predict bond type: check electronegativity difference. Large difference "
        "(greater than 1.7) favours ionic bonding. Small difference (less than 1.7 between "
        "non-metals) favours covalent bonding. Same element or metals favour metallic "
        "bonding."
    ))

    return _build("chemical_bonds.pdf", s)


# ── 5. The Mughal Empire ─────────────────────────────────────────────


def create_mughal_empire() -> Path:
    s: list = []

    s.append(_p("The Mughal Empire in India", TITLE_STYLE))
    s.append(_p("CBSE Grade 10 History", SUB_HEADING_STYLE))
    s.append(_gap())

    s.append(_p("Introduction and Timeline", HEADING_STYLE))
    s.append(_p(
        "The Mughal Empire was one of the largest and most powerful empires in Indian "
        "history, ruling much of the Indian subcontinent from 1526 to 1857. The word "
        "'Mughal' is derived from 'Mongol,' as the dynasty traced its origins to the "
        "Mongol-Turkic conqueror Timur (Tamerlane) and to Genghis Khan through the "
        "maternal line."
    ))
    s.append(_p(
        "Key timeline: Babur founds the empire (1526), Humayun loses and regains the "
        "throne (1530-1556), Akbar's golden age (1556-1605), Jahangir (1605-1627), "
        "Shah Jahan (1627-1658), Aurangzeb's expansion and decline (1658-1707), and "
        "gradual decline until the last Mughal emperor was deposed by the British (1857)."
    ))

    s.append(_p("Babur and the Founding of the Empire", HEADING_STYLE))
    s.append(_p(
        "Zahir-ud-din Muhammad Babur (1483-1530) was a Central Asian prince from Fergana "
        "(modern Uzbekistan). After losing his ancestral kingdom, he turned his ambitions "
        "toward India. In 1526, at the First Battle of Panipat, Babur defeated Ibrahim "
        "Lodi, the last sultan of the Delhi Sultanate, despite being vastly outnumbered."
    ))
    s.append(_p(
        "Babur's victory was due to superior military tactics. He used a combination of "
        "field fortifications (carts tied together), cavalry flanking manoeuvres, and "
        "gunpowder weapons (cannons and matchlocks), which were relatively new to India. "
        "This battle established Mughal rule in northern India."
    ))
    s.append(_p(
        "Babur's son Humayun (reigned 1530-1540, 1555-1556) faced rebellions and was "
        "driven out of India by Sher Shah Suri. After 15 years in exile in Persia, "
        "Humayun recaptured Delhi in 1555 but died in an accident in 1556."
    ))

    s.append(_p("Akbar the Great (1556-1605)", HEADING_STYLE))
    s.append(_p(
        "Akbar, arguably the greatest Mughal emperor, ascended the throne at age 13. "
        "His reign is considered the golden age of the Mughal Empire. He expanded the "
        "empire across northern and central India through military conquest and strategic "
        "alliances, particularly with Rajput kingdoms through marriage diplomacy."
    ))
    s.append(_p(
        "Administrative reforms: Akbar established the Mansabdari system, a hierarchical "
        "ranking system for officials. He reformed tax collection (the Zabt system, based "
        "on measured land productivity). He divided the empire into provinces (Subahs) "
        "governed by appointed officials."
    ))
    s.append(_p(
        "Religious tolerance: Akbar promoted Sulh-i-Kul (universal peace). He abolished "
        "the jizya (tax on non-Muslims), held interfaith dialogues at his court, and "
        "founded Din-i-Ilahi, a syncretic belief system drawing from Islam, Hinduism, "
        "Christianity, Zoroastrianism, and Jainism."
    ))
    s.append(_p(
        "Cultural achievements: Akbar patronised art, architecture, and literature. "
        "He built the city of Fatehpur Sikri, commissioned illustrated manuscripts, "
        "and supported the translation of Sanskrit texts into Persian."
    ))

    s.append(_p("Shah Jahan and Aurangzeb", HEADING_STYLE))
    s.append(_p(
        "Shah Jahan (reigned 1627-1658) is best known as the builder of the Taj Mahal "
        "(1632-1653), a white marble mausoleum in Agra built in memory of his wife "
        "Mumtaz Mahal. The Taj Mahal is considered one of the finest examples of Mughal "
        "architecture and is a UNESCO World Heritage Site."
    ))
    s.append(_p(
        "Shah Jahan also built the Red Fort and Jama Masjid in Delhi, and the Peacock "
        "Throne (Takht-e-Taus), encrusted with precious gems. However, his lavish "
        "building projects strained the imperial treasury."
    ))
    s.append(_p(
        "Aurangzeb (reigned 1658-1707) expanded the empire to its greatest territorial "
        "extent but also sowed the seeds of its decline. He reversed Akbar's policy of "
        "religious tolerance, reimposing the jizya and destroying several Hindu temples. "
        "His campaigns in the Deccan dragged on for decades, exhausting the treasury and "
        "the military."
    ))

    s.append(_p("Decline and Legacy", HEADING_STYLE))
    s.append(_p(
        "After Aurangzeb's death in 1707, the empire fragmented rapidly. Weak successors, "
        "provincial governors declaring independence, and invasions by Nadir Shah (1739) "
        "and Ahmad Shah Abdali weakened central authority. The Marathas, Sikhs, and "
        "regional powers filled the vacuum."
    ))
    s.append(_p(
        "By the early 19th century, the Mughal emperor was a figurehead under British "
        "protection. After the Indian Rebellion of 1857, the British formally ended the "
        "Mughal dynasty, exiling the last emperor Bahadur Shah Zafar to Burma."
    ))
    s.append(_p(
        "Legacy: The Mughals left a profound impact on Indian civilisation. Their "
        "contributions include monumental architecture (Taj Mahal, Red Fort, Fatehpur "
        "Sikri), the Urdu language (a fusion of Persian and Hindi), Mughal miniature "
        "painting, garden design (charbagh), cuisine (biryani, kebabs), and "
        "administrative systems that influenced later British colonial governance."
    ))

    return _build("mughal_empire.pdf", s)


# ── main ──────────────────────────────────────────────────────────────


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Creating 5 source PDFs in {OUTPUT_DIR}/\n")

    pdfs = [
        create_photosynthesis(),
        create_newtons_laws(),
        create_cell_structure(),
        create_chemical_bonds(),
        create_mughal_empire(),
    ]

    print(f"\nDone. {len(pdfs)} PDFs created.")


if __name__ == "__main__":
    main()
