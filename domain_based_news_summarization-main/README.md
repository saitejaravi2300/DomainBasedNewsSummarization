# Domain-Based News Summarization

A full-stack prototype for domain-aware news trend discovery, summarization, and digest generation.

The project includes:
- **Backend:** FastAPI service for news ingestion, NLP-based clustering, summarization, saved trends, and authentication.
- **Frontend:** Next.js dashboard with domain selection, saved trends, custom domain workflows, and content browsing.
- **ML foundation:** A separate `ml-lab/` workspace for model-assisted ranking, deduplication, and baseline pipeline experiments.

## Key Features

- Domain-specific news digests for verticals like AI, finance, healthcare, climate, crypto, legal, policy, and cybersecurity
- AI-assisted summarization and trend extraction
- Saved trends persistence and custom domain management
- User authentication and backend data APIs
- Local full-stack development support via PowerShell scripts

## Technology Stack

- Backend: `FastAPI`, `pydantic`, `httpx`, `google-generativeai`, `pymongo`, `python-jose`, `nltk`, `scikit-learn`, `torch`, `transformers`
- Frontend: `Next.js`, `React`, `Tailwind CSS`, `Radix UI`, `Recharts`, `React Hook Form`
- Data and storage: MongoDB Atlas (configured via backend `.env`)

## Repository Structure

- `backend/` - FastAPI application and server-side logic
- `frontend/` - Next.js UI and client application
- `ml-lab/` - experimental ML pipeline and baseline model utilities
- `start-dev.ps1` / `stop-dev.ps1` - local development helpers
- `PROGRESS_README.md` - project status, roadmap, and feature summary

## Prerequisites

- Python 3.11+
- Node.js and package manager compatible with `pnpm`
- `pnpm` installed globally for frontend dependency management
- MongoDB Atlas or another MongoDB connection configured for the backend
- PowerShell available for local start/stop scripts

## Setup

### 1. Backend

1. Open a terminal in `backend/`
2. Install dependencies:
   ```powershell
   python -m pip install -U pip
   python -m pip install -e .
   ```
3. Create a `.env` file inside `backend/` with your environment variables.

Suggested backend variables:
```text
GEMINI_API_KEY=
GEMINI_MODEL=
GEMINI_ENABLED=true
GROQ_API_KEY=
GROQ_MODEL=llama-3.1-8b-instant
GROQ_ENABLED=true
HF_TOKEN=
GEMMA_PRIMARY_ENABLED=true
GEMMA_BASE_MODEL_ID=google/gemma-2-2b
GEMMA_ADAPTER_DIR=
GEMMA_MAX_NEW_TOKENS=160
GEMMA_TIMEOUT_SECONDS=90
NEWS_API_KEY=
GNEWS_API_KEY=
ALLOW_MOCK_FALLBACK=false
DB_FIRST_ONLY_MODE=true
DB_MIN_ARTICLES_THRESHOLD=15
JWT_SECRET_KEY=your-super-secret-key-change-this-in-production-min-32-chars-12345
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
MONGODB_URI=
```

> Note: The backend loads the `.env` file from `backend/.env`.

### 2. Frontend

1. Open a terminal in `frontend/`
2. Install dependencies:
   ```powershell
   pnpm install
   ```

## Running Locally

### Option 1: Use PowerShell scripts

From the project root, run:
```powershell
./start-dev.ps1
```

To stop local servers:
```powershell
./stop-dev.ps1
```

### Option 2: Start manually

Backend:
```powershell
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Frontend:
```powershell
cd frontend
pnpm run dev
```

## Notes

- The UI expects the backend API to be available on `http://localhost:8000` and the frontend to run on `http://localhost:3000`.
- `PROGRESS_README.md` contains a detailed project roadmap, completion status, and current prototype capabilities.
- The backend includes support for news APIs, Gemini, Groq, and Gemma configurations, with fallback and mock behavior toggles.

## Troubleshooting

- If the backend fails to start, verify `backend/.env` and MongoDB connectivity.
- If the frontend fails to build, ensure `pnpm` is installed and the `frontend/package.json` dependencies are installed.
- Use `test_api.py` and the scripts under `backend/` for basic endpoint checks.

## License

This repository does not include a license file. Add one if you intend to open source or share the code publicly.
