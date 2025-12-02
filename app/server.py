"""ChatKitServer implementation for the starter app."""

from __future__ import annotations

import base64
from datetime import datetime
from typing import Any, AsyncIterator

from agents import Runner
from chatkit.agents import stream_agent_response
from chatkit.server import ChatKitServer, stream_widget
from chatkit.types import (
    Action,
    AssistantMessageContent,
    AssistantMessageItem,
    Attachment,
    HiddenContextItem,
    ImageAttachment,
    ThreadItemDoneEvent,
    ThreadItemUpdated,
    ThreadMetadata,
    ThreadStreamEvent,
    UserMessageItem,
    WidgetItem,
    WidgetRootUpdated,
)
from openai.types.responses import (
    ResponseInputContentParam,
    ResponseInputFileParam,
    ResponseInputImageParam,
)

from .agents.starter_agent import StarterAgentContext, starter_agent
from .data.mcq_store import MCQStore
from .memory_store import MemoryStore
from .request_context import RequestContext
from .thread_item_converter import StarterAppThreadItemConverter
from .widgets.mcq_widget import build_mcq_widget


class StarterAppServer(ChatKitServer[RequestContext]):
    """ChatKit server for the starter app."""

    def __init__(self) -> None:
        self.store: MemoryStore = MemoryStore()
        super().__init__(self.store)

        self.mcq_store = MCQStore()
        self.thread_item_converter = StarterAppThreadItemConverter(store=self.store)

    async def respond(
        self,
        thread: ThreadMetadata,
        item: UserMessageItem | None,
        context: RequestContext,
    ) -> AsyncIterator[ThreadStreamEvent]:
        """
        Handle user messages and generate responses using the agent.
        
        This method:
        1. Loads recent thread items for context
        2. Converts them to agent input format
        3. Runs the agent with the input
        4. Streams the agent's response back to the client
        """
        # Load recent thread items so the agent has conversation context
        items_page = await self.store.load_thread_items(
            thread.id,
            after=None,
            limit=20,
            order="desc",
            context=context,
        )
        # Reverse so most recent message is last (as expected by Runner)
        items = list(reversed(items_page.data))
        
        # Convert ChatKit thread items to agent input format
        input_items = await self.thread_item_converter.to_agent_input(items)

        # Create agent context with access to stores and thread
        agent_context = StarterAgentContext(
            thread=thread,
            store=self.store,
            mcq_store=self.mcq_store,
            request_context=context,
        )

        # Run the agent with the input items and stream the response
        result = Runner.run_streamed(
            starter_agent,
            input_items,
            context=agent_context,
        )

        # Stream agent response events back to the client
        async for event in stream_agent_response(agent_context, result):
            yield event
        return

    async def action(
        self,
        thread: ThreadMetadata,
        action: Action[str, Any],
        sender: WidgetItem | None,
        context: RequestContext,
    ) -> AsyncIterator[ThreadStreamEvent]:
        """
        Handle widget actions.
        
        Actions are handled on the server by default (when handler is not "client" in the widget definition).
        The sender argument is the widget item that triggered the action (if available).
        
        Action payloads should be treated as untrusted input from the client.
        
        To record user actions for the model to see on the next turn, use HiddenContextItem.
        To update widgets, use ThreadItemUpdated with WidgetRootUpdated.
        To create new widgets, use stream_widget.
        """
        if action.type == "mcq.submit":
            async for event in self._handle_submit_action(thread, action, sender, context):
                yield event
            return
        if action.type == "mcq.clear":
            async for event in self._handle_clear_action(action, sender, thread, context):
                yield event
            return
        if action.type == "mcq.next":
            async for event in self._handle_next_action(thread, action, sender, context):
                yield event
            return
        if action.type == "mcq.finish":
            async for event in self._handle_finish_action(thread, action, sender, context):
                yield event
            return

        return

    async def to_message_content(self, _input: Attachment) -> ResponseInputContentParam:
        """Convert an attachment to message content that can be sent to the model."""
        # Load attachment bytes from store
        attachment_bytes = None
        if hasattr(self.store, "load_attachment_bytes"):
            attachment_bytes = self.store.load_attachment_bytes(_input.id)
        
        # If we have bytes, process based on MIME type
        if attachment_bytes:
            mime_type = _input.mime_type or "application/octet-stream"
            
            # Handle images
            if isinstance(_input, ImageAttachment) or mime_type.startswith("image/"):
                data_url = f"data:{mime_type};base64,{base64.b64encode(attachment_bytes).decode('utf-8')}"
                return ResponseInputImageParam(
                    type="input_image",
                    detail="auto",
                    image_url=data_url,
                )
            
            # Handle PDFs
            if mime_type == "application/pdf":
                data_url = f"data:{mime_type};base64,{base64.b64encode(attachment_bytes).decode('utf-8')}"
                return ResponseInputFileParam(
                    type="input_file",
                    file_data=data_url,
                    filename=_input.name or "unknown",
                )
            
            # Handle text files
            if mime_type.startswith("text/"):
                try:
                    text_content = attachment_bytes.decode("utf-8")
                    return {
                        "type": "input_text",
                        "text": text_content,
                    }
                except UnicodeDecodeError:
                    pass
        
        # Fallback: return text description
        filename = _input.name or "unnamed file"
        content_type = _input.mime_type or "unknown type"
        return {
            "type": "input_text",
            "text": f"[File attachment: {filename} ({content_type})]",
        }

    # -- Helpers ----------------------------------------------------

    async def _handle_submit_action(
        self,
        thread: ThreadMetadata,
        action: Action[str, Any],
        sender: WidgetItem | None,
        context: RequestContext,
    ) -> AsyncIterator[ThreadStreamEvent]:
        """Handle answer submission."""
        # Treat action payloads as untrusted input from the client
        question_id = action.payload.get("questionId") if action.payload else None
        # Form submissions include form field values in the payload
        answer = action.payload.get("answer") if action.payload else None

        if not question_id or not sender or not sender.widget:
            print(f"[ACTION] submit: missing question_id or sender")
            return

        # Try to get question from thread metadata first (for dynamically created questions)
        # Then fall back to MCQStore
        question = None
        total = 0
        
        # Check thread metadata for current quiz
        if thread.metadata and "current_quiz" in thread.metadata:
            quiz = thread.metadata.get("current_quiz", [])
            total = len(quiz)
            for q in quiz:
                if q.get("id") == question_id:
                    question = q
                    break
        
        # Fall back to MCQStore if not found in metadata
        if not question:
            question = self.mcq_store.get_question(question_id)
            total = len(self.mcq_store.questions)
        
        if not question:
            print(f"[ACTION] submit: question {question_id} not found")
            return

        # Check answer
        correct_answer = question.get("correct_answer", "")
        is_correct = correct_answer == answer
        status = "correct" if is_correct else "incorrect"
        
        result = {
            "correct": is_correct,
            "hint": question.get("hint") if not is_correct else None,
            "explanation": question.get("explanation") if is_correct else None,
        }

        print(f"[ACTION] submit: question_id={question_id}, answer={answer}, correct={is_correct}")

        # Record the user action so the model can see it on the next turn
        hidden = HiddenContextItem(
            id=self.store.generate_item_id("message", thread, context),
            thread_id=thread.id,
            created_at=datetime.now(),
            content=f"User submitted answer '{answer}' for question {question_id}. Result: {'correct' if is_correct else 'incorrect'}.",
        )
        # HiddenContextItems need to be manually saved because ChatKitServer
        # only auto-saves streamed items, and HiddenContextItem should never be streamed to the client.
        await self.store.add_thread_item(thread.id, hidden, context)

        # Get current widget state from payload - IMPORTANT: keep the same index
        current_index = action.payload.get("index", 1) if action.payload else 1
        print(f"[ACTION] submit: keeping index={current_index} (from payload)")
        
        # Build updated widget with the SAME index (don't reset it)
        updated_widget = build_mcq_widget(
            question_id=question_id,
            index=current_index,  # Keep the current index, don't reset to 1
            total=total,
            prompt=question["prompt"],
            options=question["options"],
            selected=answer or "",
            status=status,
            feedback={
                "hint": result.get("hint"),
                "explanation": result.get("explanation"),
            },
        )

        # Update the existing widget using ThreadItemUpdated
        yield ThreadItemUpdated(
            item_id=sender.id,
            update=WidgetRootUpdated(widget=updated_widget),
        )

    async def _handle_clear_action(
        self,
        action: Action[str, Any],
        sender: WidgetItem | None,
        thread: ThreadMetadata,
        context: RequestContext,
    ) -> AsyncIterator[ThreadStreamEvent]:
        """Handle clearing the selected answer."""
        if not sender or not sender.widget:
            return

        question_id = action.payload.get("questionId") if action.payload else None
        if not question_id:
            return

        # Try to get question from thread metadata first, then MCQStore
        question = None
        total = 0
        
        if thread.metadata and "current_quiz" in thread.metadata:
            quiz = thread.metadata.get("current_quiz", [])
            total = len(quiz)
            for q in quiz:
                if q.get("id") == question_id:
                    question = q
                    break
        
        if not question:
            question = self.mcq_store.get_question(question_id)
            total = len(self.mcq_store.questions)
        
        if not question:
            return

        # Extract current index from payload or default to 1
        current_index = action.payload.get("index", 1) if action.payload else 1

        updated_widget = build_mcq_widget(
            question_id=question_id,
            index=current_index,
            total=total,
            prompt=question["prompt"],
            options=question["options"],
            selected="",
            status="idle",
            feedback={},
        )

        # Update the existing widget using ThreadItemUpdated
        yield ThreadItemUpdated(
            item_id=sender.id,
            update=WidgetRootUpdated(widget=updated_widget),
        )

    async def _handle_next_action(
        self,
        thread: ThreadMetadata,
        action: Action[str, Any],
        sender: WidgetItem | None,
        context: RequestContext,
    ) -> AsyncIterator[ThreadStreamEvent]:
        """Handle moving to the next question."""
        print(f"[ACTION] next: payload={action.payload if action.payload else None}")
        if not sender or not sender.widget:
            print(f"[ACTION] next: missing sender or widget")
            return

        question_id = action.payload.get("questionId") if action.payload else None
        if not question_id:
            print(f"[ACTION] next: missing question_id")
            return

        # Extract current index from payload or default to 1
        current_index = action.payload.get("index", 1) if action.payload else 1
        print(f"[ACTION] next: current_index={current_index}, question_id={question_id}")
        
        # Get questions from thread metadata or MCQStore
        questions = []
        if thread.metadata and "current_quiz" in thread.metadata:
            questions = thread.metadata.get("current_quiz", [])
            print(f"[ACTION] next: got {len(questions)} questions from thread metadata")
        else:
            questions = self.mcq_store.get_questions()
            print(f"[ACTION] next: got {len(questions)} questions from MCQStore")
        
        total = len(questions)
        next_index = current_index + 1
        print(f"[ACTION] next: total={total}, next_index={next_index}")

        if next_index > total:
            # Already at the end, handle finish
            print(f"[ACTION] next: reached end, calling finish")
            async for event in self._handle_finish_action(thread, action, sender, context):
                yield event
            return

        # Get the next question (next_index is 1-based, array is 0-based)
        if next_index <= len(questions):
            next_question = questions[next_index - 1]
            print(f"[ACTION] next: moving to question {next_index}: id={next_question.get('id')}, prompt={next_question.get('prompt', '')[:50]}...")
            updated_widget = build_mcq_widget(
                question_id=next_question["id"],
                index=next_index,
                total=total,
                prompt=next_question["prompt"],
                options=next_question["options"],
                selected="",
                status="idle",
                feedback={},
            )

            # Update the existing widget using ThreadItemUpdated
            yield ThreadItemUpdated(
                item_id=sender.id,
                update=WidgetRootUpdated(widget=updated_widget),
            )
        else:
            print(f"[ACTION] next: next_index {next_index} out of range for {len(questions)} questions")

    async def _handle_finish_action(
        self,
        thread: ThreadMetadata,
        action: Action[str, Any],
        sender: WidgetItem | None,
        context: RequestContext,
    ) -> AsyncIterator[ThreadStreamEvent]:
        """Handle finishing the quiz."""
        message_item = AssistantMessageItem(
            thread_id=thread.id,
            id=self.store.generate_item_id("message", thread, context),
            created_at=datetime.now(),
            content=[
                AssistantMessageContent(
                    text="Great job completing the quiz! Would you like to try another one?"
                )
            ],
        )
        yield ThreadItemDoneEvent(item=message_item)


def create_chatkit_server() -> StarterAppServer | None:
    """Return a configured ChatKit server instance if dependencies are available."""
    return StarterAppServer()

