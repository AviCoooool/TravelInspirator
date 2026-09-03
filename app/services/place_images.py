"""Generate realtime photos from Quasar/GPT image_prompts."""

from __future__ import annotations

import asyncio
import base64
import hashlib
import logging
import re
from urllib.parse import quote

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

UA = {"User-Agent": "TravelInspirator/1.0 (hackathon)"}
POLLINATIONS = "https://image.pollinations.ai/prompt/{prompt}"


def svg_placeholder(prompt: str, index: int, place: str = "") -> bytes:
    title = (place or "Travel scene").strip()[:48] or "Travel scene"
    detail = (prompt or f"Scene {index + 1}").strip()[:90]
    safe_title = _xml(title)
    safe_detail = _xml(detail)
    palettes = [
        ("#0f2a33", "#2d6a5a", "#d4a56a"),
        ("#1a1530", "#6a3d7a", "#e8a87c"),
        ("#102033", "#2e86ab", "#87a878"),
    ]
    c1, c2, c3 = palettes[index % 3]
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="800" height="600" viewBox="0 0 800 600">
  <defs>
    <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="{c1}"/>
      <stop offset="55%" stop-color="{c2}"/>
      <stop offset="100%" stop-color="{c3}"/>
    </linearGradient>
  </defs>
  <rect width="800" height="600" fill="url(#sky)"/>
  <circle cx="640" cy="110" r="56" fill="rgba(255,255,255,0.22)"/>
  <path d="M0 390 L140 270 L260 340 L400 210 L560 320 L720 250 L800 300 L800 600 L0 600 Z" fill="rgba(0,0,0,0.28)"/>
  <path d="M0 470 L180 360 L320 430 L480 340 L650 410 L800 370 L800 600 L0 600 Z" fill="rgba(0,0,0,0.22)"/>
  <rect x="28" y="420" width="744" height="140" rx="18" fill="rgba(0,0,0,0.45)"/>
  <text x="400" y="470" text-anchor="middle" font-family="Georgia, serif" font-size="32" fill="#f5f0e8">{safe_title}</text>
  <text x="400" y="508" text-anchor="middle" font-family="Arial, sans-serif" font-size="16" fill="#d4cfc4">GPT scene {index + 1} of 3</text>
  <text x="400" y="538" text-anchor="middle" font-family="Arial, sans-serif" font-size="13" fill="#b0aaa0">{safe_detail}</text>
</svg>"""
    return svg.encode("utf-8")


def _xml(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _clean(name: str) -> str:
    base = re.sub(r"\s*\([^)]*\)\s*", " ", name or "").strip()
    return re.sub(r"\s+", " ", base)


def _seed(prompt: str, index: int) -> int:
    digest = hashlib.sha256(f"{prompt}|{index}".encode()).hexdigest()
    return int(digest[:8], 16) % 1_000_000


def _to_data_uri(content: bytes, media_type: str) -> str:
    b64 = base64.b64encode(content).decode("ascii")
    return f"data:{media_type};base64,{b64}"


def _images_generations_url() -> str:
    override = (getattr(settings, "image_api_url", None) or "").strip()
    if override:
        return override
    chat = (settings.llm_api_url or "").strip()
    if not chat:
        return ""
    if "/chat/completions" in chat:
        return chat.replace("/chat/completions", "/images/generations")
    return chat.rstrip("/") + "/images/generations"


async def _fetch_quasar_image(prompt: str) -> tuple[bytes, str] | None:
    """Generate image via Quasar OpenAI-compatible /images/generations (same GPT key)."""
    key = (settings.llm_api_key or "").strip()
    url = _images_generations_url()
    if not key or not url:
        return None

    model = (getattr(settings, "image_model", None) or "").strip() or "dall-e-3"
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        **UA,
    }
    payload = {
        "model": model,
        "prompt": (prompt or "")[:1000],
        "n": 1,
        "size": "1024x1024",
        "response_format": "b64_json",
    }

    try:
        # trust_env=False — same as LLM client (corporate proxies break Quasar CONNECT)
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(45.0, connect=15.0),
            trust_env=False,
            follow_redirects=True,
            headers=UA,
        ) as client:
            res = await client.post(url, headers=headers, json=payload)
            if res.status_code >= 400:
                logger.warning("Quasar image HTTP %s: %s", res.status_code, res.text[:200])
                return None
            data = res.json()
            items = data.get("data") or []
            if not items:
                return None
            item = items[0]
            b64 = item.get("b64_json")
            if b64:
                raw = base64.b64decode(b64)
                return raw, "image/png"
            remote = item.get("url")
            if remote:
                img = await client.get(remote)
                if img.status_code == 200 and len(img.content) > 800:
                    ctype = (img.headers.get("content-type") or "image/png").split(";")[0]
                    return img.content, ctype
    except Exception as exc:
        logger.warning("Quasar image failed: %s", exc)
    return None


async def _fetch_pollinations(prompt: str, index: int) -> tuple[bytes, str] | None:
    """Fallback realtime renderer for GPT prompts when Quasar images is unavailable."""
    text = (prompt or "").strip()
    if not text:
        return None
    seed = _seed(text, index)
    url = POLLINATIONS.format(prompt=quote(text[:350]))
    params = {
        "width": 800,
        "height": 600,
        "nologo": "true",
        "enhance": "true",
        "seed": seed,
        "model": "flux",
    }
    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(90.0, connect=20.0),
            trust_env=False,
            follow_redirects=True,
            headers={**UA, "Accept": "image/*", "Referer": "https://pollinations.ai/"},
        ) as client:
            res = await client.get(url, params=params)
            if res.status_code != 200:
                logger.warning("Pollinations HTTP %s for idx=%s", res.status_code, index)
                return None
            ctype = (res.headers.get("content-type") or "image/jpeg").split(";")[0].strip()
            if not ctype.startswith("image/") or len(res.content) < 800:
                return None
            return res.content, ctype
    except Exception as exc:
        logger.warning("Pollinations failed idx=%s: %s", index, exc)
        return None


async def fetch_photo_bytes_from_prompt(
    prompt: str, index: int = 0, place: str = ""
) -> tuple[bytes, str]:
    """Realtime image from GPT prompt. Tries Quasar GPT image API, then Pollinations."""
    text = (prompt or "").strip() or f"travel destination scene {index + 1}"
    live = await _fetch_quasar_image(text)
    if live:
        return live
    live = await _fetch_pollinations(text, index)
    if live:
        return live
    return svg_placeholder(text, index, place=place), "image/svg+xml"


async def fetch_photo_as_data_uri(prompt: str, index: int = 0, place: str = "") -> str:
    content, media_type = await fetch_photo_bytes_from_prompt(prompt, index, place=place)
    return _to_data_uri(content, media_type)


async def fetch_photo_bytes(name: str, country: str | None, index: int) -> tuple[bytes, str]:
    place = f"{_clean(name)}, {country or ''}".strip().strip(",")
    prompt = (
        f"photorealistic travel photo of {place}, "
        f"distinct scenic view {index + 1}, natural light"
    )
    return await fetch_photo_bytes_from_prompt(prompt, index, place=place)


async def fetch_place_images(name: str, country: str | None = None, limit: int = 3) -> list[dict]:
    place = _clean(name)
    country = (country or "").strip()
    prompts = [
        f"photorealistic travel photo of {place}, {country}, iconic landmark wide shot, golden hour",
        f"photorealistic travel photo of {place}, {country}, local street or market atmosphere, natural light",
        f"photorealistic travel photo of {place}, {country}, nature or skyline viewpoint at blue hour, cinematic",
    ][:limit]
    uris = await asyncio.gather(
        *[fetch_photo_as_data_uri(p, i, place=place) for i, p in enumerate(prompts)]
    )
    return [
        {
            "url": uris[i],
            "thumb": uris[i],
            "title": f"{place} — GPT scene {i + 1}",
            "prompt": prompts[i],
        }
        for i in range(len(prompts))
    ]


async def attach_destination_images(response) -> None:
    """Block until every destination has 3 realtime images from its GPT prompts."""
    jobs: list[tuple[object, int, str, str]] = []
    for concept in response.travel_concepts:
        for dest in concept.destinations:
            prompts = list(dest.image_prompts or [])[:3]
            while len(prompts) < 3:
                prompts.append(
                    f"photorealistic travel photo of {dest.name}, {dest.country}, scenic view {len(prompts) + 1}"
                )
            dest.image_prompts = prompts
            place = f"{dest.name}, {dest.country}"
            for i, prompt in enumerate(prompts):
                jobs.append((dest, i, prompt, place))

    if not jobs:
        return

    sem = asyncio.Semaphore(4)

    async def _one(prompt: str, i: int, place: str) -> str:
        async with sem:
            return await fetch_photo_as_data_uri(prompt, i, place=place)

    results = await asyncio.gather(
        *[_one(prompt, i, place) for _, i, prompt, place in jobs],
        return_exceptions=True,
    )

    by_dest: dict[int, list[str | None]] = {}
    dest_objs: dict[int, object] = {}
    for (dest, i, prompt, place), result in zip(jobs, results):
        key = id(dest)
        dest_objs[key] = dest
        by_dest.setdefault(key, [None, None, None])
        if isinstance(result, Exception):
            logger.warning("Image attach failed: %s", result)
            svg = svg_placeholder(prompt, i, place=place)
            by_dest[key][i] = _to_data_uri(svg, "image/svg+xml")
        else:
            by_dest[key][i] = result

    for key, dest in dest_objs.items():
        uris = [u for u in by_dest[key] if u]
        dest.images = uris[:3]
