@echo off
REM Windows batch script to run the ChatKit backend server

echo Starting ChatKit Backend Server...

REM Check if we're in the backend directory
if not exist "pyproject.toml" (
    echo Error: pyproject.toml not found. Please run this script from the backend directory.
    exit /b 1
)

REM Check if uv is installed
where uv >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Error: 'uv' is not installed. Please install it from https://github.com/astral-sh/uv
    exit /b 1
)

REM Check if OPENAI_API_KEY is set
if "%OPENAI_API_KEY%"=="" (
    echo Warning: OPENAI_API_KEY environment variable is not set.
    echo Please set it before running the server:
    echo   set OPENAI_API_KEY=your-api-key-here
)

REM Install dependencies and run the server
echo Installing dependencies...
uv sync

echo Starting server on http://localhost:8000
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

