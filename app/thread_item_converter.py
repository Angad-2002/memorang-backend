"""Helpers that convert ChatKit thread items into model-friendly inputs."""

from __future__ import annotations

import base64

from chatkit.agents import ThreadItemConverter
from chatkit.types import Attachment, HiddenContextItem, ImageAttachment
from openai.types.responses import (
    ResponseInputFileParam,
    ResponseInputImageParam,
    ResponseInputTextParam,
)
from openai.types.responses.response_input_item_param import Message


class StarterAppThreadItemConverter(ThreadItemConverter):
    """Converts thread items for ChatKit Starter App."""

    def __init__(self, store=None):
        """Initialize converter with optional store for loading attachment bytes."""
        self.store = store

    async def hidden_context_to_input(self, item: HiddenContextItem):
        return Message(
            type="message",
            content=[
                ResponseInputTextParam(
                    type="input_text",
                    text=item.content,
                )
            ],
            role="user",
        )

    async def attachment_to_message_content(self, attachment: Attachment):
        """Convert an attachment to message content."""
        # Load attachment bytes if store is available
        attachment_bytes = None
        if self.store and hasattr(self.store, "load_attachment_bytes"):
            attachment_bytes = self.store.load_attachment_bytes(attachment.id)
        
        mime_type = attachment.mime_type or "application/octet-stream"
        
        # Handle images
        if isinstance(attachment, ImageAttachment) or mime_type.startswith("image/"):
            if attachment_bytes:
                data_url = f"data:{mime_type};base64,{base64.b64encode(attachment_bytes).decode('utf-8')}"
                return ResponseInputImageParam(
                    type="input_image",
                    detail="auto",
                    image_url=data_url,
                )
        
        # Handle PDFs
        if mime_type == "application/pdf":
            if attachment_bytes:
                data_url = f"data:{mime_type};base64,{base64.b64encode(attachment_bytes).decode('utf-8')}"
                return ResponseInputFileParam(
                    type="input_file",
                    file_data=data_url,
                    filename=attachment.name or "unknown",
                )
        
        # Handle text files
        if mime_type.startswith("text/") and attachment_bytes:
            try:
                text_content = attachment_bytes.decode("utf-8")
                return ResponseInputTextParam(
                    type="input_text",
                    text=text_content,
                )
            except UnicodeDecodeError:
                pass
        
        # Fallback: return text description
        filename = attachment.name or "unnamed file"
        return ResponseInputTextParam(
            type="input_text",
            text=f"[File attachment: {filename} ({mime_type})]",
        )

