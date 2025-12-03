"""User model for authentication."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from beanie import Document
from pydantic import EmailStr, Field


class User(Document):
    """User document model for MongoDB."""

    email: EmailStr = Field(..., unique=True, index=True)
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "users"
        indexes = [
            "email",  # Ensure email is indexed for fast lookups
        ]

    async def update_timestamp(self) -> None:
        """Update the updated_at timestamp."""
        self.updated_at = datetime.utcnow()
        await self.save()

