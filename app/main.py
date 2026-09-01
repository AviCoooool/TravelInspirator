from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.agent.travel_agent import TravelAgent
from app.config import settings
from app.llm.client import LLMClient
from app.models.schemas import TravelRequest, TravelResponse

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(
    title="AI Travel Inspirator",
    description="Emotion-first travel discovery powered by AI",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

agent = TravelAgent()


def verify_bearer(request: Request) -> None:
    auth = request.headers.get("Authorization", "")
    if auth != f"Bearer {settings.dev_bearer_token}":
        raise HTTPException(status_code=401, detail="Invalid bearer token")


@app.get("/", response_class=HTMLResponse)
async def home() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
async def health() -> dict:
    provider = settings.provider.lower().replace("_", "-")
    has_quasar = bool((settings.llm_api_key or "").strip() and (settings.llm_api_url or "").strip())
    has_gemini = bool((settings.gemini_api_key or "").strip())

    if provider == "mock":
        active, reason = "mock", "PROVIDER=mock"
    elif provider == "self-hosted":
        if has_quasar:
            active, reason = "self-hosted", f"Quasar model={settings.model}"
        else:
            active, reason = "mock", "self-hosted selected but LLM_API_KEY/URL missing"
    elif provider == "gemini":
        if has_gemini:
            active, reason = "gemini", f"Gemini model={settings.gemini_model}"
        else:
            active, reason = "mock", "gemini selected but GEMINI_API_KEY missing"
    else:
        active, reason = "mock", f"unknown PROVIDER={provider}"

    return {
        "status": "ok",
        "configured_provider": provider,
        "active_engine": active,
        "model": settings.model if active == "self-hosted" else settings.gemini_model,
        "llm_api_url": settings.llm_api_url if has_quasar else None,
        "quasar_key_present": has_quasar,
        "gemini_key_present": has_gemini,
        "reason": reason,
    }


@app.get("/api/llm-ping")
async def llm_ping() -> dict:
    """Probe the configured live LLM (Quasar / Gemini). Does not fall back to mock."""
    provider = settings.provider.lower().replace("_", "-")
    client = LLMClient()
    try:
        if provider == "mock":
            return {"ok": False, "provider": provider, "error": "PROVIDER=mock — nothing to ping"}
        text = await client.chat(
            "Reply with the single word PONG.",
            "Ping test. Reply PONG only.",
        )
        return {
            "ok": client.last_provider_used != "mock",
            "provider_used": client.last_provider_used,
            "model": settings.model if client.last_provider_used == "self-hosted" else settings.gemini_model,
            "preview": (text or "")[:200],
            "error": client.last_error,
        }
    except Exception as exc:
        return {
            "ok": False,
            "provider": provider,
            "error": client.last_error or f"{type(exc).__name__}: {exc}",
        }


@app.post("/api/inspire", response_model=TravelResponse)
async def inspire(request: TravelRequest) -> TravelResponse:
    try:
        return await agent.inspire(request)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Inspiration failed: {exc}") from exc


@app.post("/api/diagnose", response_model=TravelResponse, dependencies=[Depends(verify_bearer)])
async def diagnose(request: TravelRequest) -> TravelResponse:
    """Orchestrator-compatible endpoint for agent worker integration."""
    return await inspire(request)
