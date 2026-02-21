"""
NeuroSync AI — Content Generation Pipeline.

Orchestrates the complete content generation workflow:
  PDF → Parse → Clean → Analyze → Extract Concepts →
  Generate (Slides + Scripts + Audio + Video + Story + Quiz) →
  Export all 5 formats.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional

from loguru import logger

from neurosync.content.analyzers.complexity_assessor import ComplexityAssessor, ComplexityReport
from neurosync.content.analyzers.concept_extractor import ConceptExtractor, ConceptMap
from neurosync.content.analyzers.structure_analyzer import DocumentStructure, StructureAnalyzer
from neurosync.content.formats.markdown import MarkdownGenerator, MarkdownOutput
from neurosync.content.formats.quiz import QuizExporter, QuizOutput
from neurosync.content.formats.story import StoryExporter, StoryOutput
from neurosync.content.generators.quiz_generator import QuizBank, QuizGenerator
from neurosync.content.generators.script_generator import FullScript, ScriptGenerator
from neurosync.content.generators.slide_generator import SlideDeck, SlideGenerator
from neurosync.content.generators.story_generator import FullStory, StoryGenerator
from neurosync.content.generators.video_assembler import VideoAssembler
from neurosync.content.parsers.pdf_parser import PDFDocument, PDFParser
from neurosync.content.parsers.text_cleaner import CleanedText, TextCleaner
from neurosync.content.progress_tracker import PipelineStage, ProgressTracker
from neurosync.content.tts.openai_tts import OpenAITTS


@dataclass
class PipelineConfig:
    """Configuration for the content generation pipeline."""
    # PDF Parsing
    max_pages: int = 200
    chunk_size: int = 4000
    chunk_overlap: int = 200

    # Concept Extraction
    extraction_model: str = "gpt-4-turbo-preview"
    extraction_max_tokens: int = 2000
    extraction_temperature: float = 0.3

    # Slide Generation
    max_slides_per_concept: int = 3

    # Script / Narration
    script_model: str = "gpt-4-turbo-preview"
    tts_model: str = "tts-1"
    tts_voice: str = "alloy"

    # Story
    story_model: str = "gpt-4-turbo-preview"
    story_temperature: float = 0.8

    # Quiz
    quiz_model: str = "gpt-4-turbo-preview"
    quiz_questions_per_concept: int = 3

    # Video
    video_fps: int = 24
    video_resolution: tuple[int, int] = (1920, 1080)
    slide_duration_seconds: float = 8.0

    # Output
    output_dir: str = "output"

    # Feature flags (which formats to generate)
    generate_video: bool = True
    generate_slides: bool = True
    generate_notes: bool = True
    generate_story: bool = True
    generate_quiz: bool = True
    generate_audio: bool = True


@dataclass
class PipelineResult:
    """Complete result from the content generation pipeline."""
    title: str
    concept_map: Optional[ConceptMap] = None
    complexity: Optional[ComplexityReport] = None
    structure: Optional[DocumentStructure] = None
    slide_deck: Optional[SlideDeck] = None
    scripts: Optional[FullScript] = None
    story: Optional[FullStory] = None
    quiz_bank: Optional[QuizBank] = None
    outputs: dict[str, str] = field(default_factory=dict)     # format → file path
    errors: list[str] = field(default_factory=list)
    elapsed_seconds: float = 0.0
    concept_count: int = 0
    formats_generated: list[str] = field(default_factory=list)

    def summary(self) -> dict[str, Any]:
        """Return a summary of what was generated."""
        return {
            "title": self.title,
            "concept_count": self.concept_count,
            "formats_generated": self.formats_generated,
            "outputs": self.outputs,
            "errors": self.errors,
            "elapsed_seconds": round(self.elapsed_seconds, 1),
        }


class ContentPipeline:
    """
    Main content generation pipeline orchestrator.

    Takes a PDF and produces up to 5 output formats:
    video, slides, notes, story, quiz.
    """

    def __init__(self, openai_client: Any = None,
                 config: Optional[PipelineConfig] = None,
                 progress_callback: Optional[Callable] = None) -> None:
        self.config = config or PipelineConfig()
        self.client = openai_client or self._create_client()
        self.tracker = ProgressTracker(callback=progress_callback)

        # Initialize sub-components
        self.pdf_parser = PDFParser(max_pages=self.config.max_pages)
        self.text_cleaner = TextCleaner()
        self.structure_analyzer = StructureAnalyzer()
        self.complexity_assessor = ComplexityAssessor()
        self.concept_extractor = ConceptExtractor(
            client=self.client,
            model=self.config.extraction_model,
            max_tokens=self.config.extraction_max_tokens,
            temperature=self.config.extraction_temperature,
        )
        self.slide_generator = SlideGenerator(
            max_slides_per_concept=self.config.max_slides_per_concept,
        )
        self.script_generator = ScriptGenerator(
            client=self.client,
            model=self.config.script_model,
        )
        self.tts = OpenAITTS(
            client=self.client,
            model=self.config.tts_model,
            voice=self.config.tts_voice,
        )
        self.video_assembler = VideoAssembler(
            fps=self.config.video_fps,
            resolution=self.config.video_resolution,
            default_slide_duration=self.config.slide_duration_seconds,
        )
        self.story_generator = StoryGenerator(
            client=self.client,
            model=self.config.story_model,
            temperature=self.config.story_temperature,
        )
        self.quiz_generator = QuizGenerator(
            client=self.client,
            model=self.config.quiz_model,
            questions_per_concept=self.config.quiz_questions_per_concept,
        )
        self.markdown_generator = MarkdownGenerator()
        self.story_exporter = StoryExporter()
        self.quiz_exporter = QuizExporter()

    @staticmethod
    def _create_client() -> Any:
        """Create an LLM client based on environment configuration.

        Tries Groq (FREE) first, falls back to OpenAI.
        Returns None if no provider is configured.
        """
        import os

        provider = os.getenv("LLM_PROVIDER", "openai")
        groq_key = os.getenv("GROQ_API_KEY", "")
        openai_key = os.getenv("OPENAI_API_KEY", "")

        if provider == "groq" and groq_key:
            try:
                from openai import AsyncOpenAI

                # Groq is OpenAI-compatible; use the OpenAI SDK pointed at Groq
                client = AsyncOpenAI(
                    api_key=groq_key,
                    base_url="https://api.groq.com/openai/v1",
                )
                logger.info("ContentPipeline using Groq client (FREE)")
                return client
            except Exception as e:
                logger.warning("Groq client creation failed: {}", e)

        if openai_key:
            try:
                from openai import AsyncOpenAI

                client = AsyncOpenAI(api_key=openai_key)
                logger.info("ContentPipeline using OpenAI client")
                return client
            except Exception as e:
                logger.warning("OpenAI client creation failed: {}", e)

        return None

    async def process_pdf(self, pdf_path: str | Path) -> PipelineResult:
        """
        Process a PDF through the complete pipeline.

        Args:
            pdf_path: Path to the PDF file.

        Returns:
            PipelineResult with all generated content.
        """
        start_time = time.time()
        result = PipelineResult(title="")
        self.tracker.start_pipeline()

        try:
            # === Stage 1: Parse PDF ===
            self.tracker.start_stage(PipelineStage.PARSING, "Reading PDF...")
            doc = self.pdf_parser.parse(pdf_path)
            self.tracker.complete_stage(PipelineStage.PARSING, f"Parsed {doc.total_pages} pages")

            # === Stage 2: Clean text ===
            self.tracker.start_stage(PipelineStage.CLEANING, "Cleaning text...")
            cleaned = self.text_cleaner.clean(doc.full_text())
            title = self.text_cleaner.extract_title(cleaned.text)
            result.title = title
            self.tracker.complete_stage(PipelineStage.CLEANING, f"Cleaned {cleaned.cleaned_length} chars")

            # === Stage 3: Analyze structure & complexity ===
            self.tracker.start_stage(PipelineStage.ANALYZING, "Analyzing content...")
            result.structure = self.structure_analyzer.analyze(cleaned.text, title)
            result.complexity = self.complexity_assessor.assess(cleaned.text)
            self.tracker.complete_stage(
                PipelineStage.ANALYZING,
                f"Difficulty: {result.complexity.difficulty_label}",
            )

            # === Stage 4: Extract concepts ===
            self.tracker.start_stage(PipelineStage.EXTRACTING_CONCEPTS, "Extracting concepts...")
            chunks = doc.text_chunks(
                chunk_size=self.config.chunk_size,
                overlap=self.config.chunk_overlap,
            )
            result.concept_map = await self.concept_extractor.extract_from_chunks(chunks, title)
            result.concept_count = len(result.concept_map.concepts)
            self.tracker.complete_stage(
                PipelineStage.EXTRACTING_CONCEPTS,
                f"Found {result.concept_count} concepts",
            )

            # Prepare output directory
            output_dir = Path(self.config.output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)

            concepts = result.concept_map.concepts
            objectives = result.concept_map.learning_objectives
            summary = result.concept_map.summary

            # === Stage 5: Generate slides ===
            if self.config.generate_slides:
                self.tracker.start_stage(PipelineStage.GENERATING_SLIDES, "Creating slides...")
                try:
                    result.slide_deck = self.slide_generator.generate(
                        concepts, title, summary, objectives,
                    )
                    slides_path = output_dir / "slides" / f"{_safe_name(title)}.pptx"
                    self.slide_generator.export_pptx(result.slide_deck, slides_path)
                    result.outputs["slides"] = str(slides_path)
                    result.formats_generated.append("slides")
                    self.tracker.complete_stage(
                        PipelineStage.GENERATING_SLIDES,
                        f"{result.slide_deck.slide_count} slides",
                    )
                except Exception as e:
                    result.errors.append(f"Slides: {e}")
                    self.tracker.fail_stage(PipelineStage.GENERATING_SLIDES, str(e))

            # === Stage 6: Generate scripts ===
            if self.config.generate_audio or self.config.generate_video:
                self.tracker.start_stage(PipelineStage.GENERATING_SCRIPTS, "Writing scripts...")
                try:
                    result.scripts = await self.script_generator.generate_scripts(concepts, title)
                    self.tracker.complete_stage(
                        PipelineStage.GENERATING_SCRIPTS,
                        f"{len(result.scripts.scripts)} scripts",
                    )
                except Exception as e:
                    result.errors.append(f"Scripts: {e}")
                    self.tracker.fail_stage(PipelineStage.GENERATING_SCRIPTS, str(e))

            # === Stage 7: Generate audio ===
            audio_segments = []
            if self.config.generate_audio and result.scripts:
                self.tracker.start_stage(PipelineStage.GENERATING_AUDIO, "Recording narration...")
                try:
                    audio_dir = output_dir / "audio"
                    audio_segments = await self.tts.generate_for_scripts(
                        result.scripts.scripts, audio_dir,
                    )
                    self.tracker.complete_stage(
                        PipelineStage.GENERATING_AUDIO,
                        f"{len(audio_segments)} audio segments",
                    )
                except Exception as e:
                    result.errors.append(f"Audio: {e}")
                    self.tracker.fail_stage(PipelineStage.GENERATING_AUDIO, str(e))

            # === Stage 8: Generate video ===
            if self.config.generate_video and result.slide_deck:
                self.tracker.start_stage(PipelineStage.GENERATING_VIDEO, "Assembling video...")
                try:
                    slide_titles = [s.title for s in result.slide_deck.slides]
                    audio_paths = [s.audio_path for s in audio_segments] if audio_segments else None
                    durations = [s.duration_seconds for s in audio_segments] if audio_segments else None

                    segments = self.video_assembler.create_segments(
                        slide_titles, audio_paths, durations,
                    )
                    video_path = output_dir / "videos" / f"{_safe_name(title)}.mp4"
                    video_result = self.video_assembler.assemble(segments, video_path)
                    result.outputs["video"] = video_result.output_path
                    result.formats_generated.append("video")
                    self.tracker.complete_stage(
                        PipelineStage.GENERATING_VIDEO,
                        f"{video_result.total_duration_seconds:.0f}s video",
                    )
                except Exception as e:
                    result.errors.append(f"Video: {e}")
                    self.tracker.fail_stage(PipelineStage.GENERATING_VIDEO, str(e))

            # === Stage 9: Generate story ===
            if self.config.generate_story:
                self.tracker.start_stage(PipelineStage.GENERATING_STORY, "Writing story...")
                try:
                    result.story = await self.story_generator.generate_story(concepts, title)
                    story_path = output_dir / "stories" / f"{_safe_name(title)}_story.md"
                    self.story_exporter.export(result.story, story_path)
                    result.outputs["story"] = str(story_path)
                    result.formats_generated.append("story")
                    self.tracker.complete_stage(
                        PipelineStage.GENERATING_STORY,
                        f"{result.story.total_word_count} words",
                    )
                except Exception as e:
                    result.errors.append(f"Story: {e}")
                    self.tracker.fail_stage(PipelineStage.GENERATING_STORY, str(e))

            # === Stage 10: Generate quiz ===
            if self.config.generate_quiz:
                self.tracker.start_stage(PipelineStage.GENERATING_QUIZ, "Creating quiz...")
                try:
                    result.quiz_bank = await self.quiz_generator.generate_quiz(concepts, title)
                    quiz_path = output_dir / "quizzes" / f"{_safe_name(title)}_quiz.json"
                    self.quiz_exporter.export(result.quiz_bank, quiz_path)
                    result.outputs["quiz"] = str(quiz_path)
                    result.formats_generated.append("quiz")
                    self.tracker.complete_stage(
                        PipelineStage.GENERATING_QUIZ,
                        f"{len(result.quiz_bank.questions)} questions",
                    )
                except Exception as e:
                    result.errors.append(f"Quiz: {e}")
                    self.tracker.fail_stage(PipelineStage.GENERATING_QUIZ, str(e))

            # === Stage 11: Export notes (Markdown) ===
            if self.config.generate_notes:
                self.tracker.start_stage(PipelineStage.EXPORTING, "Exporting notes...")
                try:
                    md_content = self.markdown_generator.generate(
                        concepts, title, summary, objectives,
                    )
                    notes_path = output_dir / "notes" / f"{_safe_name(title)}_notes.md"
                    self.markdown_generator.export(md_content, notes_path)
                    result.outputs["notes"] = str(notes_path)
                    result.formats_generated.append("notes")
                    self.tracker.complete_stage(PipelineStage.EXPORTING, "Notes exported")
                except Exception as e:
                    result.errors.append(f"Notes: {e}")
                    self.tracker.fail_stage(PipelineStage.EXPORTING, str(e))

            # Done!
            result.elapsed_seconds = time.time() - start_time
            self.tracker.complete_pipeline()

            logger.info(
                "Pipeline complete: {} formats in {:.1f}s ({} concepts, {} errors)",
                len(result.formats_generated), result.elapsed_seconds,
                result.concept_count, len(result.errors),
            )

        except Exception as e:
            result.errors.append(f"Pipeline: {e}")
            result.elapsed_seconds = time.time() - start_time
            self.tracker.fail_pipeline(str(e))
            logger.error("Pipeline failed: {}", e)

        return result


def _safe_name(title: str) -> str:
    """Convert title to a safe filename."""
    import re
    safe = re.sub(r"[^\w\s-]", "", title.lower())
    safe = re.sub(r"[\s]+", "_", safe.strip())
    return safe[:80] or "content"
