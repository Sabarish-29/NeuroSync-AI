#!/usr/bin/env python
"""
NeuroSync AI — Sample Content Verification Script.

Checks that all 5 source PDFs exist and are parseable,
and optionally validates generated course outputs.

Usage:
    python scripts/verify_sample_content.py          # verify source PDFs only
    python scripts/verify_sample_content.py --full    # also verify generated courses
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Ensure project root is importable
sys.path.insert(0, str(Path(__file__).parent.parent))

SOURCE_DIR = Path("sample_content/source_pdfs")
GENERATED_DIR = Path("sample_content/generated")

EXPECTED_PDFS = [
    "photosynthesis.pdf",
    "newtons_laws.pdf",
    "cell_structure.pdf",
    "chemical_bonds.pdf",
    "mughal_empire.pdf",
]

MIN_PDF_SIZE_BYTES = 1_000          # 1 KB minimum
MIN_WORD_COUNT = 200                # minimum extractable words


def _print(msg: str, ok: bool | None = None) -> None:
    if ok is True:
        prefix = "  [PASS]"
    elif ok is False:
        prefix = "  [FAIL]"
    else:
        prefix = "  [INFO]"
    print(f"{prefix} {msg}")


def verify_source_pdfs() -> tuple[int, int]:
    """Check that each source PDF exists and is non-trivial."""
    print("\n--- Source PDFs ---")
    passed = 0
    failed = 0

    for name in EXPECTED_PDFS:
        pdf_path = SOURCE_DIR / name
        if not pdf_path.exists():
            _print(f"{name}: NOT FOUND", ok=False)
            failed += 1
            continue

        size = pdf_path.stat().st_size
        if size < MIN_PDF_SIZE_BYTES:
            _print(f"{name}: too small ({size} bytes)", ok=False)
            failed += 1
            continue

        _print(f"{name}: {size / 1024:.1f} KB", ok=True)
        passed += 1

    # Try to import the PDF parser and do a deeper check
    try:
        from neurosync.content.parsers.pdf_parser import PDFParser

        parser = PDFParser()
        print("\n--- PDF Parse Check ---")
        for name in EXPECTED_PDFS:
            pdf_path = SOURCE_DIR / name
            if not pdf_path.exists():
                continue
            try:
                result = parser.parse(str(pdf_path))
                words = getattr(result, "total_word_count", 0) or getattr(result, "word_count", 0)
                pages = getattr(result, "total_pages", 0)
                sections = len(getattr(result, "sections", getattr(result, "pages", [])))
                if words < MIN_WORD_COUNT:
                    _print(
                        f"{name}: only {words} extractable words (need {MIN_WORD_COUNT}+)",
                        ok=False,
                    )
                else:
                    _print(
                        f"{name}: {pages} pages, {words} words, {sections} sections",
                        ok=True,
                    )
            except Exception as exc:
                _print(f"{name}: parse error — {exc}", ok=False)
    except ImportError:
        _print("PDFParser not found — skipping deep parse check", ok=None)

    return passed, failed


def verify_generated_courses() -> tuple[int, int]:
    """Check that generated course directories contain expected artifacts."""
    print("\n--- Generated Courses ---")
    passed = 0
    failed = 0

    if not GENERATED_DIR.exists():
        _print("generated/ directory does not exist — run generate_sample_content.py first", ok=False)
        return 0, 1

    course_dirs = sorted(
        [d for d in GENERATED_DIR.iterdir() if d.is_dir()],
    )

    if not course_dirs:
        _print("No course directories found in generated/", ok=False)
        return 0, 1

    for course_dir in course_dirs:
        course_id = course_dir.name
        meta_path = course_dir / "metadata.json"

        if not meta_path.exists():
            _print(f"{course_id}: missing metadata.json", ok=False)
            failed += 1
            continue

        with open(meta_path) as f:
            meta = json.load(f)

        # Check key fields
        missing = [k for k in ("name", "subject", "concepts_count") if k not in meta]
        if missing:
            _print(f"{course_id}: metadata missing keys {missing}", ok=False)
            failed += 1
        else:
            _print(
                f"{course_id}: {meta.get('name', '?')} "
                f"({meta.get('concepts_count', '?')} concepts)",
                ok=True,
            )
            passed += 1

    return passed, failed


def main() -> None:
    full_check = "--full" in sys.argv

    print("=" * 60)
    print("  NeuroSync AI — Sample Content Verification")
    print("=" * 60)

    pdf_pass, pdf_fail = verify_source_pdfs()

    gen_pass, gen_fail = 0, 0
    if full_check:
        gen_pass, gen_fail = verify_generated_courses()

    total_pass = pdf_pass + gen_pass
    total_fail = pdf_fail + gen_fail

    print("\n" + "=" * 60)
    print(f"  RESULTS: {total_pass} passed, {total_fail} failed")
    if total_fail == 0:
        print("  STATUS: ALL CHECKS PASSED")
    else:
        print("  STATUS: SOME CHECKS FAILED")
    print("=" * 60 + "\n")

    sys.exit(0 if total_fail == 0 else 1)


if __name__ == "__main__":
    main()
