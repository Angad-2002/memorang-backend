# ChatKit Starter App - Python Backend

This is a Python backend implementation for the ChatKit Starter App that enables dynamic widget interactions. Unlike the frontend-only version that uses OpenAI-hosted workflows, this backend gives you full control over widget actions and state management.

## Features

- **Dynamic Widget Actions**: Handle `mcq.submit`, `mcq.clear`, `mcq.next`, and `mcq.finish` actions
- **Widget State Updates**: Update widget state in real-time based on user interactions
- **MCQ Question Management**: Built-in store for managing multiple choice questions
- **FastAPI Backend**: RESTful API with CORS support for frontend integration

## Prerequisites

- Python 3.11 or higher
- [uv](https://github.com/astral-sh/uv) package manager
- OpenAI API key

## Setup

1. **Install dependencies**:
   ```bash
   cd backend
   uv sync
   ```

2. **Set environment variables**:
   ```bash
   # Windows PowerShell
   $env:OPENAI_API_KEY = "your-api-key-here"
   
   # Linux/Mac
   export OPENAI_API_KEY="your-api-key-here"
   ```

## Running the Backend

### Option 1: Using the provided scripts

**Windows (PowerShell)**:
```powershell
cd backend
.\scripts\run-backend.ps1
```

**Windows (CMD)**:
```cmd
cd backend
scripts\run-backend.cmd
```

**Linux/Mac**:
```bash
cd backend
chmod +x scripts/run-backend.sh
./scripts/run-backend.sh
```

### Option 2: Manual run

```bash
cd backend
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The server will start on `http://localhost:8000`

## Frontend Configuration

To connect the frontend to this backend, set the following environment variable in your `.env.local` file:

```env
NEXT_PUBLIC_CHATKIT_API_URL=http://localhost:8000/chatkit
NEXT_PUBLIC_CHATKIT_API_DOMAIN_KEY=domain_pk_localhost_dev
```

**Note**: The domain key is a placeholder for local development. For production, register your domain at [OpenAI Domain Allowlist](https://platform.openai.com/settings/organization/security/domain-allowlist).

## API Endpoints

- `POST /chatkit` - Main ChatKit endpoint for handling conversations and widget actions
- `GET /health` - Health check endpoint

## Widget Actions

The backend handles the following widget actions:

- **mcq.submit**: Submit an answer to an MCQ question
- **mcq.clear**: Clear the selected answer
- **mcq.next**: Move to the next question
- **mcq.finish**: Finish the quiz

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI entrypoint
│   ├── server.py            # ChatKitServer implementation
│   ├── memory_store.py      # In-memory thread store
│   ├── request_context.py   # Request context
│   ├── thread_item_converter.py  # Thread item converter
│   ├── data/
│   │   ├── __init__.py
│   │   └── mcq_store.py     # MCQ question store
│   └── widgets/
│       ├── __init__.py
│       └── mcq_widget.py     # MCQ widget builder
├── scripts/
│   ├── run-backend.ps1      # PowerShell script
│   ├── run-backend.sh       # Bash script
│   └── run-backend.cmd      # CMD script
├── pyproject.toml           # Python dependencies
└── README.md
```

## Development

The backend uses:
- **FastAPI** for the web framework
- **openai-chatkit** for ChatKit server implementation
- **uvicorn** as the ASGI server
- **jinja2** for widget template rendering

## Differences from OpenAI-Hosted Workflow

When using this custom backend:
- Widgets are **dynamic** - state can be updated in real-time
- Full control over widget action handling
- Can implement custom business logic
- Requires running a separate backend server

When using OpenAI-hosted workflow (default):
- Widgets are **static** - defined by templates only
- Actions handled by OpenAI's workflow
- No backend server needed
- Less control over widget behavior

## Troubleshooting

1. **Port already in use**: Change the port in the run script or command
2. **CORS errors**: Make sure the frontend URL is in the CORS allowlist in `main.py`
3. **Widget not updating**: Check that widget actions are being sent correctly from the frontend
4. **Missing dependencies**: Run `uv sync` to install all dependencies

