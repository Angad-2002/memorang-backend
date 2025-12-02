#!/bin/bash
# Shell script to run the ChatKit backend server

echo "Starting ChatKit Backend Server..."

# Check if we're in the backend directory
if [ ! -f "pyproject.toml" ]; then
    echo "Error: pyproject.toml not found. Please run this script from the backend directory."
    exit 1
fi

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "Error: 'uv' is not installed. Please install it from https://github.com/astral-sh/uv"
    exit 1
fi

# Check if OPENAI_API_KEY is set
if [ -z "$OPENAI_API_KEY" ]; then
    echo "Warning: OPENAI_API_KEY environment variable is not set."
    echo "Please set it before running the server:"
    echo '  export OPENAI_API_KEY="your-api-key-here"'
fi

# Install dependencies and run the server
echo "Installing dependencies..."
uv sync

echo "Starting server on http://localhost:8000"
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

