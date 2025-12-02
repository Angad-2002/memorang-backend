# PowerShell script to run the ChatKit backend server

Write-Host "Starting ChatKit Backend Server..." -ForegroundColor Green

# Check if we're in the backend directory
if (-not (Test-Path "pyproject.toml")) {
    Write-Host "Error: pyproject.toml not found. Please run this script from the backend directory." -ForegroundColor Red
    exit 1
}

# Check if uv is installed
$uvInstalled = Get-Command uv -ErrorAction SilentlyContinue
if (-not $uvInstalled) {
    Write-Host "Error: 'uv' is not installed. Please install it from https://github.com/astral-sh/uv" -ForegroundColor Red
    exit 1
}

# Check if OPENAI_API_KEY is set
if (-not $env:OPENAI_API_KEY) {
    Write-Host "Warning: OPENAI_API_KEY environment variable is not set." -ForegroundColor Yellow
    Write-Host "Please set it before running the server:" -ForegroundColor Yellow
    Write-Host '  $env:OPENAI_API_KEY = "your-api-key-here"' -ForegroundColor Yellow
}

# Install dependencies and run the server
Write-Host "Installing dependencies..." -ForegroundColor Cyan
uv sync

Write-Host "Starting server on http://localhost:8000" -ForegroundColor Green
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

