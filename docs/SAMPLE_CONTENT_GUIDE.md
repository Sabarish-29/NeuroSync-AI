# Sample Content Creation Guide

## Required PDFs

Create 5 PDFs (5-10 pages each) in `sample_content/source_pdfs/`:

### 1. photosynthesis.pdf (Biology, 10 pages)

**Content to include:**
```
Title: Photosynthesis - How Plants Make Food

Section 1: Introduction
- What is photosynthesis?
- Why is it important?
- Where does it occur?

Section 2: Light and Pigments
- Chlorophyll structure and function
- Light absorption spectrum
- Photosystems I and II

Section 3: Light-Dependent Reactions
- Thylakoid membrane
- Electron transport chain
- ATP and NADPH production
- Water splitting

Section 4: Calvin Cycle (Light-Independent)
- Carbon fixation
- RuBisCO enzyme
- G3P production
- Regeneration of RuBP

Section 5: Factors Affecting Photosynthesis
- Light intensity
- CO2 concentration
- Temperature
- Water availability

Section 6: Summary and Importance
- Oxygen production
- Food chain base
- Carbon cycle role
```

**How to create:**
1. Use Google Docs or Word
2. Add simple diagrams (hand-drawn or from Wikipedia)
3. Include 2-3 images per section
4. Keep language grade-appropriate
5. Export as PDF

### 2. newtons_laws.pdf (Physics, 8 pages)

**Content outline:**
```
- Introduction to motion and force
- Newton's First Law (Inertia)
  - Examples: car braking, space objects
- Newton's Second Law (F = ma)
  - Force calculations
  - Mass vs weight
- Newton's Third Law (Action-Reaction)
  - Examples: rocket propulsion, walking
- Real-world applications
- Problem-solving examples
```

### 3. cell_structure.pdf (Biology, 10 pages)

**Content outline:**
```
- Cell theory
- Prokaryotic vs Eukaryotic
- Plant cell organelles
- Animal cell organelles
- Organelle functions (nucleus, mitochondria, ER, Golgi, etc.)
- Cell membrane structure
- Comparison table
```

### 4. chemical_bonds.pdf (Chemistry, 9 pages)

**Content outline:**
```
- Introduction to bonding
- Ionic bonds (electron transfer)
- Covalent bonds (electron sharing)
- Metallic bonds
- Bond strength comparison
- Lewis structures
- Examples and applications
```

### 5. mughal_empire.pdf (History, 12 pages)

**Content outline:**
```
- Origin and founding (Babur)
- Major emperors (Akbar, Jahangir, Shah Jahan, Aurangzeb)
- Administrative system
- Architecture (Taj Mahal, Red Fort)
- Art and culture
- Economy and trade
- Decline and fall
- Legacy
```

## Quick Creation Methods

### Method 1: Use Existing Resources
1. Find Khan Academy articles
2. Open in browser
3. Print to PDF
4. Combine multiple pages if needed

### Method 2: Wikipedia
1. Find topic on Wikipedia
2. Click "Print/export" > "Download as PDF"
3. Edit to appropriate length (5-10 pages)

### Method 3: Create from Scratch
1. Use Google Docs with template:
   - Title page
   - Table of contents
   - 4-6 sections with headers
   - 2-3 images per section
   - Summary page
2. Export as PDF

## Quality Checklist

For each PDF:
- [ ] 5-10 pages in length
- [ ] Clear section headings
- [ ] Grade-appropriate language
- [ ] 2-3 images/diagrams included
- [ ] No copyright issues (use Creative Commons or create own)
- [ ] Text is selectable (not scanned image)
- [ ] File size < 5 MB

## Testing Your PDFs

```bash
# Test parsing
python -c "
from neurosync.content.parsers.pdf_parser import PDFParser
parser = PDFParser()
result = parser.parse('sample_content/source_pdfs/photosynthesis.pdf')
print(f'Pages: {result.total_pages}')
print(f'Words: {result.word_count}')
print(f'Sections: {len(result.sections)}')
"
```

Should output:
- Pages: 8-12
- Words: 2000-3000
- Sections: 5-8
