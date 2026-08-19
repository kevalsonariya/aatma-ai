# Agnikavach

> An offline-first AI assistant powered by Ollama + Qwen3 4B — no internet required.

## Project Structure

```
agnikavach/
├── frontend/   # React + Vite (TypeScript)
└── backend/    # Python FastAPI
```

## Quick Start

### 1. Prerequisites
- [Node.js](https://nodejs.org/) ≥ 18
- [Python](https://python.org/) ≥ 3.11
- [Ollama](https://ollama.com/) installed and running locally
- Qwen3 4B model pulled: `ollama pull qwen3:4b`

### 2. Backend

```bash
cd backend
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Backend will be available at: `http://localhost:8000`
Health check: `GET http://localhost:8000/health`

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend will be available at: `http://localhost:5173`

## Tech Stack

| Layer       | Technology           |
|-------------|----------------------|
| Frontend    | React + Vite + TypeScript |
| Backend     | Python FastAPI       |
| LLM Runtime | Ollama (local)       |
| Model       | Qwen3 4B             |

## Notes
- All inference runs **100% offline** — no data leaves your machine.
- No database, authentication, or cloud dependencies.
