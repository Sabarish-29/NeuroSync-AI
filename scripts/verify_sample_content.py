"""
Verify all sample content was generated correctly.
Run after generate_sample_content.py completes.
"""

import json
import sys
from pathlib import Path
from loguru import logger

REQUIRED_COURSES = [
    "photosynthesis",
    "newtons_laws",
    "cell_structure",
    "chemical_bonds",
    "mughal_empire",
]


def verify_course(course_id: str) -> dict:
    """Verify one course has all required files."""

    course_dir = Path(f"sample_content/generated/{course_id}")

    if not course_dir.exists():
        return {
            "course_id": course_id,
            "valid": False,
            "error": "Course directory not found",
        }

    # Load metadata
    metadata_path = course_dir / "metadata.json"
    if not metadata_path.exists():
        return {
            "course_id": course_id,
            "valid": False,
            "error": "metadata.json not found",
        }

    with open(metadata_path) as f:
        metadata = json.load(f)

    # Check required files
    required_files = [
        metadata.get("video_path"),
        metadata.get("slides_path"),
        metadata.get("quiz_path"),
        metadata.get("notes_path"),
    ]

    missing_files = []
    for file_path in required_files:
        if not file_path or not Path(file_path).exists():
            missing_files.append(file_path or "unknown")

    if missing_files:
        return {
            "course_id": course_id,
            "valid": False,
            "error": f"Missing files: {missing_files}",
        }

    # Check video file size (should be > 1 MB)
    video_path = Path(metadata["video_path"])
    video_size_mb = video_path.stat().st_size / 1024 / 1024

    if video_size_mb < 1.0:
        return {
            "course_id": course_id,
            "valid": False,
            "error": f"Video too small ({video_size_mb:.1f} MB)",
        }

    # All checks passed
    return {
        "course_id": course_id,
        "valid": True,
        "video_size_mb": video_size_mb,
        "concepts_count": metadata.get("concepts_count", 0),
        "generation_time_min": metadata.get("generation_time_seconds", 0) / 60,
    }


def main():
    logger.info("VERIFYING SAMPLE CONTENT")
    logger.info("=" * 70)

    results = []

    for course_id in REQUIRED_COURSES:
        logger.info(f"\nChecking: {course_id}")
        result = verify_course(course_id)
        results.append(result)

        if result["valid"]:
            logger.info("  Valid")
            logger.info(f"     Video: {result['video_size_mb']:.1f} MB")
            logger.info(f"     Concepts: {result['concepts_count']}")
            logger.info(f"     Generation: {result['generation_time_min']:.1f} min")
        else:
            logger.error(f"  Invalid: {result['error']}")

    # Summary
    valid_count = len([r for r in results if r["valid"]])

    logger.info("\n" + "=" * 70)
    logger.info("VERIFICATION SUMMARY")
    logger.info("=" * 70)
    logger.info(f"Total courses: {len(REQUIRED_COURSES)}")
    logger.info(f"Valid: {valid_count}")
    logger.info(f"Invalid: {len(REQUIRED_COURSES) - valid_count}")

    if valid_count == len(REQUIRED_COURSES):
        logger.info("\nALL SAMPLE CONTENT READY FOR DEMO!")
    else:
        logger.error("\nSome content is missing or invalid")
        logger.error("   Run: python scripts/generate_sample_content.py")

    return valid_count == len(REQUIRED_COURSES)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
