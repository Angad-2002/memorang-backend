# Backend Deployment to Render

## Quick Start

1. **Push code to GitHub**

2. **Connect to Render**:
   - Go to https://dashboard.render.com
   - Click "New +" → "Blueprint"
   - Connect your GitHub repository
   - Render will auto-detect `render.yaml` in the `backend/` directory

3. **Set Environment Variables**:
   - `OPENAI_API_KEY`: Your OpenAI API key
   - `CORS_ORIGINS`: Your frontend URL (e.g., `https://your-app.vercel.app`)

4. **Deploy**: Render will automatically build and deploy

## Manual Setup

If not using `render.yaml`:

1. Create a new **Web Service** in Render
2. Connect your GitHub repository
3. Set **Root Directory** to `backend`
4. Configure:
   - **Build Command**: `uv sync`
   - **Start Command**: `uv run uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Environment**: Python 3
5. Add environment variables (see above)
6. Deploy

## Environment Variables

- `OPENAI_API_KEY` (required): Your OpenAI API key
- `CORS_ORIGINS` (required): Comma-separated origins or `*` for all
- `PYTHON_VERSION` (optional): Defaults to 3.11

## Health Check

After deployment, verify:
- `https://your-service.onrender.com/health` returns `{"status": "ok"}`

## Notes

- Render free tier services spin down after 15 minutes of inactivity
- First request after spin-down may be slow (~30 seconds)
- Consider upgrading for production use

