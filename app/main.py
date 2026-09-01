from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.agent.travel_agent import TravelAgent
from app.config import settings
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
    key = (settings.gemini_api_key or "").strip()
    configured = settings.provider.lower()
    # What inspire() will actually try first
    if configured == "mock" or not key:
        active = "mock"
        reason = "PROVIDER=mock" if configured == "mock" else "no GEMINI_API_KEY"
    else:
        active = "gemini"
        reason = "PROVIDER=gemini with API key set"
    return {
        "status": "ok",
        "configured_provider": configured,
        "active_engine": active,
        "gemini_key_present": bool(key),
        "gemini_model": settings.gemini_model,
        "reason": reason,
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
