"""
Generate 5 sample courses for hackathon demo.
Runs after Groq migration completes.

Courses:
1. Photosynthesis (Biology, Grade 10)
2. Newton's Laws (Physics, Grade 9)
3. Cell Structure (Biology, Grade 9)
4. Chemical Bonds (Chemistry, Grade 10)
5. Mughal Empire (History, Grade 10)

Each course includes:
- Narrated video (MP4)
- Slide deck (PPTX)
- Quiz bank (JSON)
- Story format (Markdown)
- Concept metadata (JSON)
"""

import asyncio
import sys
import json
import time
from pathlib import Path
from loguru import logger

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from neurosync.content.pipeline import ContentPipeline, PipelineConfig

# Course definitions
SAMPLE_COURSES = [
    {
        "id": "photosynthesis",
        "name": "Photosynthesis: How Plants Make Food",
        "subject": "biology",
        "grade_level": 10,
        "pdf_path": "sample_content/source_pdfs/photosynthesis.pdf",
        "description": "Learn how plants convert sunlight into energy through photosynthesis",
        "duration_minutes": 15,
        "concepts_expected": 10,
    },
    {
        "id": "newtons_laws",
        "name": "Newton's Three Laws of Motion",
        "subject": "physics",
        "grade_level": 9,
        "pdf_path": "sample_content/source_pdfs/newtons_laws.pdf",
        "description": "Understand the fundamental laws that govern motion and force",
        "duration_minutes": 12,
        "concepts_expected": 8,
    },
    {
        "id": "cell_structure",
        "name": "Cell Structure and Function",
        "subject": "biology",
        "grade_level": 9,
        "pdf_path": "sample_content/source_pdfs/cell_structure.pdf",
        "description": "Explore the organelles and functions of plant and animal cells",
        "duration_minutes": 14,
        "concepts_expected": 12,
    },
    {
        "id": "chemical_bonds",
        "name": "Chemical Bonding",
        "subject": "chemistry",
        "grade_level": 10,
        "pdf_path": "sample_content/source_pdfs/chemical_bonds.pdf",
        "description": "Learn about ionic, covalent, and metallic bonds",
        "duration_minutes": 13,
        "concepts_expected": 9,
    },
    {
        "id": "mughal_empire",
        "name": "The Mughal Empire in India",
        "subject": "history",
        "grade_level": 10,
        "pdf_path": "sample_content/source_pdfs/mughal_empire.pdf",
        "description": "Discover the history, culture, and legacy of the Mughal Empire",
        "duration_minutes": 16,
        "concepts_expected": 11,
    },
]


class ContentGenerator:
    """Manages sample content generation."""

    def __init__(self):
        self.output_dir = Path("sample_content/generated")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.pipeline = ContentPipeline()
        self.results = []

    async def generate_course(self, course_info: dict) -> dict:
        """
        Generate one complete course.

        Returns:
            dict with success status and file paths
        """
        course_id = course_info["id"]
        pdf_path = course_info["pdf_path"]

        logger.info("=" * 70)
        logger.info(f"GENERATING COURSE: {course_info['name']}")
        logger.info("=" * 70)
        logger.info(f"PDF: {pdf_path}")
        logger.info(f"Subject: {course_info['subject']}")
        logger.info(f"Grade: {course_info['grade_level']}")
        logger.info(f"Expected duration: ~{course_info['duration_minutes']} minutes")
        logger.info("")

        # Check PDF exists
        if not Path(pdf_path).exists():
            logger.error(f"PDF not found: {pdf_path}")
            logger.error("Please create this PDF first!")
            return {
                "course_id": course_id,
                "success": False,
                "error": "PDF not found",
            }

        # Configure pipeline
        config = PipelineConfig(
            generate_video=True,
            generate_slides=True,
            generate_notes=True,
            generate_story=True,
            generate_quiz=True,
        )

        # Generate content
        start_time = time.time()

        try:
            logger.info("Starting content generation...")
            logger.info("This will take 8-12 minutes...")
            logger.info("")

            result = await self.pipeline.process(
                pdf_path=pdf_path,
                config=config,
            )

            elapsed = time.time() - start_time

            if result.success:
                logger.info("")
                logger.info("GENERATION COMPLETE!")
                logger.info(f"Time: {elapsed / 60:.1f} minutes")
                logger.info("")
                logger.info("Generated files:")
                logger.info(f"   Video:  {result.video_path}")
                logger.info(f"   Slides: {result.slides_path}")
                logger.info(f"   Notes:  {result.markdown_path}")
                logger.info(f"   Story:  {result.story_path}")
                logger.info(f"   Quiz:   {result.quiz_path}")
                logger.info("")
                logger.info(f"Concepts extracted: {len(result.concepts)}")

                # Create course metadata
                course_output_dir = self.output_dir / course_id
                course_output_dir.mkdir(exist_ok=True)

                metadata = {
                    "course_id": course_id,
                    "name": course_info["name"],
                    "subject": course_info["subject"],
                    "grade_level": course_info["grade_level"],
                    "description": course_info["description"],
                    "generated_at": time.time(),
                    "generation_time_seconds": elapsed,
                    "concepts_count": len(result.concepts),
                    "video_path": result.video_path,
                    "slides_path": result.slides_path,
                    "quiz_path": result.quiz_path,
                    "notes_path": result.markdown_path,
                    "story_path": result.story_path,
                }

                # Save metadata
                metadata_path = course_output_dir / "metadata.json"
                with open(metadata_path, "w") as f:
                    json.dump(metadata, f, indent=2)

                logger.info(f"Metadata saved: {metadata_path}")

                return {
                    "course_id": course_id,
                    "success": True,
                    "metadata": metadata,
                }

            else:
                logger.error("")
                logger.error("GENERATION FAILED")
                logger.error(f"Error: {result.error}")
                logger.error("")

                return {
                    "course_id": course_id,
                    "success": False,
                    "error": result.error,
                }

        except Exception as e:
            logger.exception("Exception during generation:")

            return {
                "course_id": course_id,
                "success": False,
                "error": str(e),
            }

    async def generate_all(self):
        """Generate all sample courses."""
        logger.info("NEUROSYNC SAMPLE CONTENT GENERATION")
        logger.info("=" * 70)
        logger.info(f"Courses to generate: {len(SAMPLE_COURSES)}")
        logger.info(f"Estimated total time: {len(SAMPLE_COURSES) * 10} minutes")
        logger.info("=" * 70)
        logger.info("")

        # Check all PDFs exist first
        missing_pdfs = []
        for course in SAMPLE_COURSES:
            if not Path(course["pdf_path"]).exists():
                missing_pdfs.append(course["pdf_path"])

        if missing_pdfs:
            logger.error("MISSING PDFS:")
            for pdf in missing_pdfs:
                logger.error(f"   {pdf}")
            logger.error("")
            logger.error("Please create these PDFs first.")
            logger.error("See: docs/SAMPLE_CONTENT_GUIDE.md")
            return

        # Generate each course
        for i, course in enumerate(SAMPLE_COURSES, 1):
            logger.info(f"\n{'=' * 70}")
            logger.info(f"COURSE {i}/{len(SAMPLE_COURSES)}")
            logger.info(f"{'=' * 70}\n")

            result = await self.generate_course(course)
            self.results.append(result)

            if result["success"]:
                logger.info(f"Course {i} complete")
            else:
                logger.error(f"Course {i} failed")

            logger.info("")

        # Summary
        successful = len([r for r in self.results if r["success"]])
        failed = len([r for r in self.results if not r["success"]])

        logger.info("\n" + "=" * 70)
        logger.info("GENERATION SUMMARY")
        logger.info("=" * 70)
        logger.info(f"Total courses: {len(SAMPLE_COURSES)}")
        logger.info(f"Successful: {successful}")
        logger.info(f"Failed: {failed}")
        logger.info("")

        if successful > 0:
            logger.info("Generated courses:")
            for result in self.results:
                if result["success"]:
                    logger.info(f"   - {result['course_id']}")

        if failed > 0:
            logger.error("\nFailed courses:")
            for result in self.results:
                if not result["success"]:
                    logger.error(f"   - {result['course_id']}: {result['error']}")

        logger.info("\n" + "=" * 70)
        logger.info("SAMPLE CONTENT GENERATION COMPLETE!")
        logger.info("=" * 70)

        # Save summary
        summary_path = self.output_dir / "generation_summary.json"
        with open(summary_path, "w") as f:
            json.dump(
                {
                    "total": len(SAMPLE_COURSES),
                    "successful": successful,
                    "failed": failed,
                    "results": self.results,
                    "generated_at": time.time(),
                },
                f,
                indent=2,
            )

        logger.info(f"\nSummary saved: {summary_path}")


async def main():
    generator = ContentGenerator()
    await generator.generate_all()


if __name__ == "__main__":
    asyncio.run(main())
