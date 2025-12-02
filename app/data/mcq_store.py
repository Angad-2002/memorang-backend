"""MCQ data store for managing questions and quizzes."""

from __future__ import annotations

from typing import Any, TypedDict


class MCQOption(TypedDict):
    label: str
    value: str
    disabled: bool | None


class MCQQuestion(TypedDict):
    id: str
    prompt: str
    options: list[MCQOption]
    correct_answer: str
    hint: str | None
    explanation: str | None


class MCQStore:
    """Store for managing MCQ questions."""

    def __init__(self):
        self.questions: list[MCQQuestion] = []
        self._load_default_questions()

    def _load_default_questions(self) -> None:
        """Load default sample questions."""
        self.questions = [
            {
                "id": "q1",
                "prompt": "What problem is identified in the brief?",
                "options": [
                    {"label": "AI tools lack a structured, persistent learning flow.", "value": "a", "disabled": None},
                    {"label": "AI models cannot read PDFs.", "value": "b", "disabled": None},
                    {"label": "Online courses are too long.", "value": "c", "disabled": None},
                    {"label": "PDF uploads are insecure.", "value": "d", "disabled": None},
                ],
                "correct_answer": "a",
                "hint": "Focus on the need for structure over raw capabilities.",
                "explanation": "The brief cites a missing structured, persistent pedagogy as the core issue.",
            },
            {
                "id": "q2",
                "prompt": "What is the capital of France?",
                "options": [
                    {"label": "London", "value": "a", "disabled": None},
                    {"label": "Paris", "value": "b", "disabled": None},
                    {"label": "Berlin", "value": "c", "disabled": None},
                    {"label": "Madrid", "value": "d", "disabled": None},
                ],
                "correct_answer": "b",
                "hint": "It's known as the City of Light",
                "explanation": "Paris is the capital and largest city of France.",
            },
        ]

    def get_question(self, question_id: str) -> MCQQuestion | None:
        """Get a specific question by ID."""
        for question in self.questions:
            if question["id"] == question_id:
                return question
        return None

    def get_questions(self, limit: int | None = None) -> list[MCQQuestion]:
        """Get all questions, optionally limited."""
        questions = self.questions
        if limit:
            questions = questions[:limit]
        return questions

    def add_question(self, question: MCQQuestion) -> None:
        """Add a new question to the store."""
        self.questions.append(question)

    def check_answer(self, question_id: str, answer: str) -> dict[str, Any]:
        """Check if an answer is correct."""
        question = self.get_question(question_id)
        if not question:
            return {"error": "Question not found"}

        is_correct = question["correct_answer"] == answer
        return {
            "correct": is_correct,
            "hint": question.get("hint") if not is_correct else None,
            "explanation": question.get("explanation") if is_correct else None,
        }

