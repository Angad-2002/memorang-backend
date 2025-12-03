"""Request context for ChatKit handlers."""

from __future__ import annotations

from typing import Annotated

from fastapi import Request
from pydantic import BaseModel, ConfigDict, Field

from .auth import decode_access_token


class RequestContext(BaseModel):
    """Typed request context shared across ChatKit handlers."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    request: Annotated[Request | None, Field(default=None, exclude=True)]
    user_id: str | None = None

    @classmethod
    def from_request(cls, request: Request) -> RequestContext:
        """Create RequestContext from FastAPI Request, extracting user from JWT if present."""
        user_id = None
        
        # Try to extract JWT token from Authorization header
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            token_data = decode_access_token(token)
            if token_data and token_data.user_id:
                user_id = token_data.user_id
        
        return cls(request=request, user_id=user_id)

