"""FastAPI entrypoint wiring the ChatKit server and REST endpoints."""

from __future__ import annotations

import logging
from typing import Any

import base64
import uuid
from datetime import datetime
from pathlib import Path

from chatkit.server import StreamingResult
from chatkit.types import FileAttachment
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import Response, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

# Configure logging to show INFO level and above
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    force=True  # Force reconfiguration even if logging was already configured
)

# Set specific loggers to INFO level
logging.getLogger("app.agents.starter_agent").setLevel(logging.INFO)
logging.getLogger("app.widgets.mcq_widget").setLevel(logging.INFO)
logging.getLogger("app.server").setLevel(logging.INFO)

from .request_context import RequestContext
from .server import StarterAppServer, create_chatkit_server

app = FastAPI(title="ChatKit Starter App API")

_chatkit_server: StarterAppServer | None = create_chatkit_server()

# Add CORS middleware to allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_chatkit_server() -> StarterAppServer:
    if _chatkit_server is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "ChatKit dependencies are missing. Install the ChatKit Python "
                "package to enable the conversational endpoint."
            ),
        )
    return _chatkit_server


@app.post("/chatkit")
async def chatkit_endpoint(
    request: Request, server: StarterAppServer = Depends(get_chatkit_server)
) -> Response:
    payload = await request.body()
    context = RequestContext(request=request)
    result = await server.process(payload, context)
    if isinstance(result, StreamingResult):
        return StreamingResponse(result, media_type="text/event-stream")
    if hasattr(result, "json"):
        return Response(content=result.json, media_type="application/json")
    return JSONResponse(result)


@app.post("/files")
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    server: StarterAppServer = Depends(get_chatkit_server),
) -> Response:
    """Handle direct file uploads for ChatKit attachments."""
    try:
        content = await file.read()
        content_type = file.content_type or "application/octet-stream"
        
        # Generate attachment ID
        attachment_id = f"att_{uuid.uuid4().hex}"
        
        # Create attachment metadata using FileAttachment (not Attachment which is a Union type)
        attachment = FileAttachment(
            id=attachment_id,
            mime_type=content_type,
            name=file.filename or "unnamed",
            size=len(content),
            created_at=datetime.now(),
            preview_url=None,
        )
        
        # Save attachment bytes to store (using internal method)
        if hasattr(server.store, "save_attachment_bytes"):
            server.store.save_attachment_bytes(attachment_id, content)
        
        # Save attachment metadata via Store interface
        context = RequestContext(request=request)
        await server.store.save_attachment(attachment, context)
        
        # Return attachment JSON as required by direct upload strategy
        return JSONResponse(attachment.model_dump())
    except Exception as e:
        import traceback
        error_detail = f"Upload failed: {str(e)}\n{traceback.format_exc()}"
        print(f"Upload error: {error_detail}")  # Log for debugging
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}

