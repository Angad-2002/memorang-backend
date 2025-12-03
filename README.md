# ChatKit Starter App - Python Backend

This is a Python backend implementation for the ChatKit Starter App that enables dynamic widget interactions. Unlike the frontend-only version that uses OpenAI-hosted workflows, this backend gives you full control over widget actions and state management.

## Features

- **User Authentication**: Sign up and sign in with email and password
- **Session Management**: Sessions are tied to authenticated users
- **MongoDB Integration**: User data stored in MongoDB
- **JWT Authentication**: Secure token-based authentication
- **Dynamic Widget Actions**: Handle `mcq.submit`, `mcq.clear`, `mcq.next`, and `mcq.finish` actions
- **Widget State Updates**: Update widget state in real-time based on user interactions
- **MCQ Question Management**: Built-in store for managing multiple choice questions
- **FastAPI Backend**: RESTful API with CORS support for frontend integration

## Prerequisites

- Python 3.11 or higher
- [uv](https://github.com/astral-sh/uv) package manager
- OpenAI API key
- MongoDB (local or cloud instance like MongoDB Atlas)

## Setup

1. **Install dependencies**:
   ```bash
   cd backend
   uv sync
   ```

2. **Set up MongoDB**:
   - For local development: Install MongoDB locally or use Docker
   - For production: Use MongoDB Atlas (free tier available)
   - Get your MongoDB connection string

3. **Set environment variables**:
   
   Create a `.env` file in the `backend` directory:
   ```env
   OPENAI_API_KEY=your-api-key-here
   MONGODB_URL=mongodb://localhost:27017
   DATABASE_NAME=chatkit_app
   JWT_SECRET_KEY=your-secret-key-change-in-production
   CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
   ```
   
   Or set them in your shell:
   ```bash
   # Windows PowerShell
   $env:OPENAI_API_KEY = "your-api-key-here"
   $env:MONGODB_URL = "mongodb://localhost:27017"
   $env:DATABASE_NAME = "chatkit_app"
   $env:JWT_SECRET_KEY = "your-secret-key-change-in-production"
   
   # Linux/Mac
   export OPENAI_API_KEY="your-api-key-here"
   export MONGODB_URL="mongodb://localhost:27017"
   export DATABASE_NAME="chatkit_app"
   export JWT_SECRET_KEY="your-secret-key-change-in-production"
   ```
   
   **Note**: For MongoDB Atlas, use a connection string like:
   ```
   mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority
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

### ChatKit Endpoints
- `POST /chatkit` - Main ChatKit endpoint for handling conversations and widget actions
- `POST /files` - File upload endpoint for ChatKit attachments
- `GET /health` - Health check endpoint

### Authentication Endpoints
- `POST /auth/signup` - Sign up a new user
  ```json
  {
    "email": "user@example.com",
    "password": "password123"
  }
  ```
- `POST /auth/signin` - Sign in an existing user
  ```json
  {
    "email": "user@example.com",
    "password": "password123"
  }
  ```
- `GET /auth/me` - Get current user information (requires authentication)
  - Headers: `Authorization: Bearer <token>`

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
│   ├── request_context.py   # Request context with auth
│   ├── thread_item_converter.py  # Thread item converter
│   ├── database.py          # MongoDB connection
│   ├── auth.py              # Authentication utilities
│   ├── models/
│   │   ├── __init__.py
│   │   └── user.py          # User model
│   ├── routers/
│   │   ├── __init__.py
│   │   └── auth.py          # Authentication routes
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
- **MongoDB** (via Motor/Beanie) for user data storage
- **JWT** (python-jose) for authentication tokens
- **bcrypt** (passlib) for password hashing

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

## Authentication Flow

1. User signs up or signs in via `/auth/signup` or `/auth/signin`
2. Backend returns a JWT token
3. Frontend stores the token in localStorage
4. Frontend includes the token in the `Authorization: Bearer <token>` header for all API requests
5. Backend extracts user ID from the token and uses it for session management

## Troubleshooting

1. **Port already in use**: Change the port in the run script or command
2. **CORS errors**: Make sure the frontend URL is in the CORS allowlist in `main.py`
3. **Widget not updating**: Check that widget actions are being sent correctly from the frontend
4. **Missing dependencies**: Run `uv sync` to install all dependencies
5. **MongoDB connection errors**: 
   - Verify MongoDB is running (local) or connection string is correct (Atlas)
   - Check that `MONGODB_URL` environment variable is set correctly
6. **Authentication errors**: 
   - Verify `JWT_SECRET_KEY` is set
   - Check that the token is being sent in the Authorization header
   - Ensure MongoDB is accessible and user collection can be created

