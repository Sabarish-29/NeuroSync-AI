"""
NeuroSync AI — Quiz Generator.

Uses GPT-4 to generate interactive quiz questions from extracted concepts.
Supports multiple question types: MCQ, true/false, short answer, fill-blank.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Literal

from loguru import logger


QuestionType = Literal["mcq", "true_false", "short_answer", "fill_blank"]
DifficultyLevel = Literal["easy", "medium", "hard"]


@dataclass
class QuizQuestion:
    """A single quiz question."""
    question_id: str
    concept_name: str
    question_text: str
    question_type: QuestionType = "mcq"
    difficulty: DifficultyLevel = "medium"
    options: list[str] = field(default_factory=list)       # for MCQ
    correct_answer: str = ""
    explanation: str = ""
    points: int = 1

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict for JSON export."""
        return {
            "question_id": self.question_id,
            "concept": self.concept_name,
            "question": self.question_text,
            "type": self.question_type,
            "difficulty": self.difficulty,
            "options": self.options,
            "correct_answer": self.correct_answer,
            "explanation": self.explanation,
            "points": self.points,
        }


@dataclass
class QuizBank:
    """Collection of quiz questions."""
    title: str
    questions: list[QuizQuestion] = field(default_factory=list)
    total_points: int = 0
    concept_coverage: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.total_points = sum(q.points for q in self.questions)
        self.concept_coverage = list({q.concept_name for q in self.questions})

    def to_dict(self) -> dict[str, Any]:
        """Serialize entire quiz bank for JSON export."""
        return {
            "title": self.title,
            "total_questions": len(self.questions),
            "total_points": self.total_points,
            "concept_coverage": self.concept_coverage,
            "questions": [q.to_dict() for q in self.questions],
        }

    def filter_by_difficulty(self, difficulty: DifficultyLevel) -> list[QuizQuestion]:
        """Return questions of a specific difficulty."""
        return [q for q in self.questions if q.difficulty == difficulty]

    def filter_by_concept(self, concept: str) -> list[QuizQuestion]:
        """Return questions for a specific concept."""
        return [q for q in self.questions if q.concept_name == concept]


class QuizGenerator:
    """Generate quiz questions using GPT-4."""

    SYSTEM_PROMPT = (
        "You are an expert quiz creator. Generate educational quiz questions "
        "for the given concept. Create a mix of question types.\n"
        "Return valid JSON:\n"
        '{"questions": [{"question_id": "q1", "question_text": "...", '
        '"question_type": "mcq|true_false|short_answer|fill_blank", '
        '"difficulty": "easy|medium|hard", '
        '"options": ["A", "B", "C", "D"], '
        '"correct_answer": "A", '
        '"explanation": "...", "points": 1}]}'
    )

    def __init__(self, client: Any = None, model: str = "gpt-4-turbo-preview",
                 max_tokens: int = 2000, temperature: float = 0.5,
                 questions_per_concept: int = 3) -> None:
        self.client = client
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.questions_per_concept = questions_per_concept

    async def generate_quiz(self, concepts: list[Any],
                             title: str = "") -> QuizBank:
        """
        Generate a quiz bank from extracted concepts.

        Args:
            concepts: List of ExtractedConcept objects.
            title: Quiz title.

        Returns:
            QuizBank with generated questions.
        """
        if not concepts:
            return QuizBank(title=title or "Empty Quiz")

        all_questions: list[QuizQuestion] = []
        q_counter = 0

        for concept in concepts:
            try:
                questions = await self._generate_for_concept(concept, q_counter)
                all_questions.extend(questions)
                q_counter += len(questions)
            except Exception as e:
                logger.warning("Quiz generation failed for {}: {}", concept.name, e)
                # Fallback question
                q_counter += 1
                all_questions.append(QuizQuestion(
                    question_id=f"q{q_counter}",
                    concept_name=concept.name,
                    question_text=f"Explain the concept of {concept.name} in your own words.",
                    question_type="short_answer",
                    difficulty="medium",
                    correct_answer=concept.description or f"A clear explanation of {concept.name}",
                    explanation=f"This tests understanding of {concept.name}.",
                ))

        bank = QuizBank(
            title=title or "Course Quiz",
            questions=all_questions,
        )

        logger.info(
            "Generated {} questions for {} concepts ({} total points)",
            len(all_questions), len(concepts), bank.total_points,
        )
        return bank

    async def _generate_for_concept(self, concept: Any,
                                     start_index: int) -> list[QuizQuestion]:
        """Generate quiz questions for a single concept."""
        if self.client is None:
            raise RuntimeError("OpenAI client not configured")

        user_msg = (
            f"Concept: {concept.name}\n"
            f"Description: {concept.description}\n"
            f"Difficulty: {concept.difficulty}\n"
            f"Keywords: {', '.join(concept.keywords) if concept.keywords else 'none'}\n"
            f"Generate {self.questions_per_concept} questions."
        )

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
            ],
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content or '{"questions": []}'
        data = json.loads(content)

        questions: list[QuizQuestion] = []
        for i, q_data in enumerate(data.get("questions", [])):
            q_type = q_data.get("question_type", "mcq")
            if q_type not in ("mcq", "true_false", "short_answer", "fill_blank"):
                q_type = "mcq"

            difficulty = q_data.get("difficulty", "medium")
            if difficulty not in ("easy", "medium", "hard"):
                difficulty = "medium"

            questions.append(QuizQuestion(
                question_id=q_data.get("question_id", f"q{start_index + i + 1}"),
                concept_name=concept.name,
                question_text=q_data.get("question_text", ""),
                question_type=q_type,
                difficulty=difficulty,
                options=q_data.get("options", []),
                correct_answer=q_data.get("correct_answer", ""),
                explanation=q_data.get("explanation", ""),
                points=q_data.get("points", 1),
            ))

        return questions
