# AI Travel Inspirator

An emotion-first, **global** travel discovery agent that helps you find destinations based on **how you feel** — enriched with Profile, Preferences, and Policy (3 Ps).

## Features

- **Mood-based recommendations** — Manual mood chips + optional selfie / voice / text sentiment signals
- **Global multi-currency** — USD · EUR · GBP · INR · AED · JPY · AUD
- **3 Ps context** — Profile · Preferences · Policy enrich the agent beyond a single prompt
- **Personality-driven destinations** — Solo, couple, family, backpacker, and more
- **Inspiration boards** — Curated concepts with match scores and thematic clusters

## Quick Start (Docker — recommended)

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (or Docker Engine + Compose v2)

### 1. Configure environment

```bash
cd ~/Projects/ai-travel-inspirator
cp .env.example .env
```

Edit `.env`:

```env
# Live AI
PROVIDER=gemini
GEMINI_API_KEY=your-google-ai-studio-key
GEMINI_MODEL=gemini-2.5-flash

# Or offline demo (no key needed)
# PROVIDER=mock

APP_PORT=8000
```

### 2. Build and run

```bash
docker compose up --build -d
```

Open **http://localhost:8000**

### Useful commands

```bash
# Logs
docker compose logs -f travel-inspirator

# Health
curl http://localhost:8000/health

# Stop
docker compose down

# Rebuild after code changes
docker compose up --build -d
```

### Demo without Gemini

```bash
PROVIDER=mock docker compose up --build -d
```

## Quick Start (local Python)

```bash
cd ~/Projects/ai-travel-inspirator
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # set GEMINI_API_KEY or PROVIDER=mock
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

| Provider | `PROVIDER` | Notes |
|----------|------------|-------|
| Gemini | `gemini` | Requires `GEMINI_API_KEY` |
| Offline demo | `mock` | Sample data, no API calls |

## API

### `POST /api/inspire`

```json
{
  "mood": "peaceful",
  "intent": "Reset my mind and find quiet beauty",
  "budget": "moderate",
  "currency": "USD",
  "travel_style": "solo",
  "context": "10 days in spring",
  "profile": { "home_base": "London, UK" },
  "preferences": { "interests": "museums, food", "pace": "slow" },
  "policy": { "visa_constraints": "EU passport" },
  "emotion_signals": {
    "source": "text_sentiment",
    "text_sentiment": "seeking relief / restoration"
  }
}
```

### `GET /health`

Returns `{ "status": "ok", "provider": "..." }`.

### `POST /api/diagnose`

Requires `Authorization: Bearer <DEV_BEARER_TOKEN>`.

## Project Structure

```
ai-travel-inspirator/
├── app/                 # FastAPI + agent
├── static/              # Web UI
├── docs/                # PPT + architecture Mermaid
├── Dockerfile
├── docker-compose.yml
├── .env.example
└── requirements.txt
```

## License

MIT
