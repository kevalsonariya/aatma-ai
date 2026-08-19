# Agnikavach — Backend

FastAPI backend for the Agnikavach offline AI assistant.

## Requirements
- Python ≥ 3.11
- [Ollama](https://ollama.com/) running locally
- Qwen3 4B model: `ollama pull qwen3:4b`

## Setup

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
```

## Run

```bash
uvicorn app.main:app --reload --port 8000
```

- API docs: http://localhost:8000/docs
- Health:   http://localhost:8000/health

## Project Layout

```
backend/
├── app/
│   ├── main.py               # FastAPI app + middleware + health route
│   ├── core/
│   │   └── config.py         # Settings (pydantic-settings)
│   ├── api/
│   │   └── routes/           # Feature routes (not yet implemented)
│   └── services/
│       └── ollama_client.py  # Ollama HTTP client stub
├── requirements.txt
├── .env.example
└── README.md
```
