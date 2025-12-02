"""Agent implementation for the starter app with MCQ widget tools."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Annotated, Any

from agents import Agent, RunContextWrapper, function_tool
from chatkit.agents import AgentContext
from chatkit.types import (
    AssistantMessageContent,
    AssistantMessageItem,
    ThreadItemDoneEvent,
    WidgetItem,
)
from pydantic import BaseModel, ConfigDict, Field

from ..data.mcq_store import MCQQuestion, MCQStore
from ..memory_store import MemoryStore
from ..request_context import RequestContext
from ..widgets.mcq_widget import build_mcq_widget

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)  # Ensure this logger shows INFO messages

INSTRUCTIONS = """
You are a helpful assistant that can answer questions and help with MCQ quizzes.

When users ask for a quiz or to generate questions:
1. Use the `create_questions` tool to store the questions you generate
2. Then use the `show_mcq_widget` tool to display the first question interactively
3. If you need existing questions, use the `get_questions` tool to fetch from the store

IMPORTANT RULES:
- When you generate questions, use `create_questions` to store them, then use `show_mcq_widget` to display them
- DO NOT repeat the questions in your text response - the widget displays them interactively
- Only provide a brief, friendly introduction message when showing the widget (e.g., "Let's test your knowledge about [topic]! Here's your first question:")
- The widget will only show questions that have been stored via `create_questions` or `get_questions`
- After showing the widget, do not list the questions again in text

Be friendly and encouraging, but keep your responses concise since the widget handles the question display.
"""

MODEL = "gpt-4o-mini"


class StarterAgentContext(AgentContext):
    """Agent context for the starter app."""
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    store: Annotated[MemoryStore, Field(exclude=True)]
    mcq_store: Annotated[MCQStore, Field(exclude=True)]
    request_context: Annotated[RequestContext, Field(exclude=True)]
    current_quiz: list[MCQQuestion] | None = None
    current_index: int = 0
    
    def generate_id(self, item_type: str) -> str:
        """Generate an item ID using the store."""
        return self.store.generate_item_id(item_type, self.thread, self.request_context)


# -- Structured results for tool calls --------------------------------------


class QuestionOption(BaseModel):
    """A single MCQ option."""
    label: str
    value: str
    disabled: bool | None = None


class QuestionInput(BaseModel):
    """Input for creating a question."""
    id: str
    prompt: str
    options: list[QuestionOption]
    correct_answer: str
    hint: str | None = None
    explanation: str | None = None


class QuestionsResult(BaseModel):
    """Result from creating questions."""
    questions: list[MCQQuestion]
    total: int


# -- Tool definitions -------------------------------------------------------


@function_tool(
    description_override=(
        "Get MCQ questions from the store.\n"
        "- `limit`: Maximum number of questions to get (default: 5)"
    )
)
async def get_questions(
    ctx: RunContextWrapper[StarterAgentContext],
    limit: int = 5,
) -> dict[str, Any]:
    """Get questions from the MCQ store."""
    print(f"[TOOL CALL] get_questions limit={limit}")
    logger.info(f"[TOOL CALL] get_questions limit={limit}")
    questions = ctx.context.mcq_store.get_questions(limit=limit)
    print(f"[TOOL CALL] get_questions returned {len(questions)} questions")
    logger.info(f"[TOOL CALL] get_questions returned {len(questions)} questions")
    for i, q in enumerate(questions):
        print(f"[TOOL CALL] Question {i}: id={q.get('id')}, prompt={q.get('prompt', '')[:50]}...")
        logger.info(f"[TOOL CALL] Question {i}: id={q.get('id')}, prompt={q.get('prompt', '')[:50]}...")
    ctx.context.current_quiz = questions
    ctx.context.current_index = 0
    return {
        "questions": questions,
        "total": len(questions),
    }


@function_tool(
    description_override=(
        "Create and set MCQ questions dynamically. Use this when you generate questions in your response.\n"
        "- `questions`: List of question objects, each with 'id', 'prompt', 'options' (list of {label, value}), 'correct_answer', 'hint' (optional), 'explanation' (optional)"
    )
)
async def create_questions(
    ctx: RunContextWrapper[StarterAgentContext],
    questions: list[QuestionInput],
) -> QuestionsResult:
    """Create questions dynamically and set them as the current quiz."""
    print(f"[TOOL CALL] create_questions with {len(questions)} questions")
    logger.info(f"[TOOL CALL] create_questions with {len(questions)} questions")
    
    # Validate and format questions
    formatted_questions = []
    for i, q in enumerate(questions):
        # Convert Pydantic options to dict format
        options_dict = [
            {
                "label": opt.label,
                "value": opt.value,
                "disabled": opt.disabled,
            }
            for opt in q.options
        ]
        formatted_q: MCQQuestion = {
            "id": q.id,
            "prompt": q.prompt,
            "options": options_dict,
            "correct_answer": q.correct_answer,
            "hint": q.hint,
            "explanation": q.explanation,
        }
        formatted_questions.append(formatted_q)
        print(f"[TOOL CALL] Created question {i}: id={q.id}, prompt={q.prompt[:50]}...")
        logger.info(f"[TOOL CALL] Created question {i}: id={q.id}, prompt={q.prompt[:50]}...")
    
    # Set as current quiz
    ctx.context.current_quiz = formatted_questions
    ctx.context.current_index = 0
    
    # Store quiz in thread metadata so action handlers can access it
    if not ctx.context.thread.metadata:
        ctx.context.thread.metadata = {}
    ctx.context.thread.metadata["current_quiz"] = formatted_questions
    ctx.context.thread.metadata["current_index"] = 0
    # Save the updated thread
    await ctx.context.store.save_thread(ctx.context.thread, ctx.context.request_context)
    
    return QuestionsResult(
        questions=formatted_questions,
        total=len(formatted_questions),
    )


@function_tool(
    description_override=(
        "Display an MCQ question widget for the user to answer.\n"
        "- `question_index`: Which question to show (0-based, default: 0)\n"
        "- `message`: Optional introductory message"
    )
)
async def show_mcq_widget(
    ctx: RunContextWrapper[StarterAgentContext],
    question_index: int = 0,
    message: str | None = None,
) -> str:
    """Display an MCQ widget with a question."""
    print(f"[TOOL CALL] show_mcq_widget question_index={question_index}")
    logger.info(f"[TOOL CALL] show_mcq_widget question_index={question_index}")
    print(f"[TOOL CALL] current_quiz is None: {ctx.context.current_quiz is None}")
    logger.info(f"[TOOL CALL] current_quiz is None: {ctx.context.current_quiz is None}")
    
    if not ctx.context.current_quiz:
        # If no quiz is active, get some questions
        logger.info("[TOOL CALL] No current quiz, fetching questions from store")
        questions = ctx.context.mcq_store.get_questions(limit=5)
        logger.info(f"[TOOL CALL] Fetched {len(questions)} questions from store")
        ctx.context.current_quiz = questions
        ctx.context.current_index = 0
    
    if question_index < 0 or question_index >= len(ctx.context.current_quiz):
        return f"Question index {question_index} is out of range. Available: 0-{len(ctx.context.current_quiz) - 1}"
    
    ctx.context.current_index = question_index
    question = ctx.context.current_quiz[question_index]
    
    print(f"[TOOL CALL] Building widget for question:")
    print(f"  - question_id: {question.get('id')}")
    print(f"  - index: {question_index + 1}")
    print(f"  - total: {len(ctx.context.current_quiz)}")
    print(f"  - prompt: {question.get('prompt', '')[:100]}...")
    print(f"  - options count: {len(question.get('options', []))}")
    logger.info(f"[TOOL CALL] Building widget for question:")
    logger.info(f"  - question_id: {question.get('id')}")
    logger.info(f"  - index: {question_index + 1}")
    logger.info(f"  - total: {len(ctx.context.current_quiz)}")
    logger.info(f"  - prompt: {question.get('prompt', '')[:100]}...")
    logger.info(f"  - options count: {len(question.get('options', []))}")
    for i, opt in enumerate(question.get('options', [])):
        print(f"    Option {i}: {opt.get('label', '')[:50]}... (value: {opt.get('value')})")
        logger.info(f"    Option {i}: {opt.get('label', '')[:50]}... (value: {opt.get('value')})")
    
    # Build the widget
    widget = build_mcq_widget(
        question_id=question["id"],
        index=question_index + 1,
        total=len(ctx.context.current_quiz),
        prompt=question["prompt"],
        options=question["options"],
        selected="",
        status="idle",
        feedback={},
    )
    
    logger.info(f"[TOOL CALL] Widget built, type: {type(widget)}")
    if isinstance(widget, dict):
        logger.info(f"[TOOL CALL] Widget keys: {list(widget.keys())}")
        if "type" in widget:
            logger.info(f"[TOOL CALL] Widget type field: {widget.get('type')}")
        # Check if it has children and log the first child's title
        if "children" in widget:
            children = widget.get("children", [])
            logger.info(f"[TOOL CALL] Widget has {len(children)} children")
            for i, child in enumerate(children[:3]):  # Log first 3 children
                if isinstance(child, dict):
                    logger.info(f"[TOOL CALL] Child {i}: type={child.get('type')}, value={str(child.get('value', ''))[:50]}")
    
    # Stream an introductory message if provided (keep it brief)
    if message:
        await ctx.context.stream(
            ThreadItemDoneEvent(
                item=AssistantMessageItem(
                    thread_id=ctx.context.thread.id,
                    id=ctx.context.generate_id("message"),
                    created_at=datetime.now(),
                    content=[AssistantMessageContent(text=message)],
                ),
            )
        )
    
    # Stream the widget (don't include the question prompt in copy_text to avoid duplication)
    logger.info(f"[TOOL CALL] Streaming widget to client")
    await ctx.context.stream_widget(widget, copy_text="")  # Empty copy_text to avoid showing question below widget
    logger.info(f"[TOOL CALL] Widget streamed successfully")
    
    return f"Question {question_index + 1} of {len(ctx.context.current_quiz)} displayed successfully."


# -- Agent definition -------------------------------------------------------

starter_agent = Agent(
    name="Starter Assistant",
    instructions=INSTRUCTIONS,
    model=MODEL,
    tools=[
        get_questions,
        create_questions,
        show_mcq_widget,
    ],
)

