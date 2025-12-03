"""Title generation agent for chat threads."""

from __future__ import annotations

from agents import Agent
from chatkit.agents import AgentContext

title_agent = Agent[AgentContext](
    model="gpt-4o-mini",
    name="Title generator",
    instructions="""
    Generate a short conversation title for an educational assistant
    that helps users with questions, explanations, and multiple-choice quizzes.
    The first user message in the thread is included below to provide context.
    Use your own words, respond with 2-5 words, and avoid punctuation.
    """,
)

