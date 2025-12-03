"""MongoDB database connection and configuration."""

from __future__ import annotations

import os
from pathlib import Path

from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

from .models.user import User

# Load environment variables
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

# MongoDB connection string from environment variable
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "chatkit_app")

# Global client instance
_client: AsyncIOMotorClient | None = None


async def init_database() -> None:
    """Initialize MongoDB connection and Beanie ODM."""
    global _client
    
    _client = AsyncIOMotorClient(MONGODB_URL)
    
    # Initialize Beanie with the database and document models
    await init_beanie(
        database=_client[DATABASE_NAME],
        document_models=[User],
    )


async def close_database() -> None:
    """Close MongoDB connection."""
    global _client
    if _client:
        _client.close()
        _client = None

