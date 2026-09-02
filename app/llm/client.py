import json
import logging
import re
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class LLMClient:
    """LLM client: Coforge Quasar (self-hosted), Gemini direct, or mock."""

    def __init__(self) -> None:
        self.provider = settings.provider.lower().replace("_", "-")
        if self.provider not in {"gemini", "self-hosted", "mock"}:
            self.provider = "self-hosted"
        self.timeout = settings.query_timeout
        self.last_provider_used: str = self.provider
        self.last_error: str | None = None

    async def chat(self, system_prompt: str, user_prompt: str) -> str:
        chain = self._provider_chain()
        last_error: Exception | None = None
        errors: list[str] = []

        for provider in chain:
            try:
                result = await self._call_provider(provider, system_prompt, user_prompt)
                self.last_provider_used = provider
                self.last_error = None if provider != "mock" else ("; ".join(errors) or None)
                if provider != chain[0]:
                    logger.warning("LLM fallback: %s failed, used %s instead", chain[0], provider)
                return result
            except Exception as exc:
                last_error = exc
                errors.append(f"{provider}: {exc}")
                self.last_error = "; ".join(errors)
                logger.warning("LLM provider %s failed: %s", provider, exc)
                if not settings.llm_fallback_enabled:
                    break

        raise last_error or RuntimeError("All LLM providers failed")

    def _provider_chain(self) -> list[str]:
        primary = self.provider
        if not settings.llm_fallback_enabled:
            return [primary]
        fallbacks: list[str] = []
        if primary != "self-hosted" and (settings.llm_api_key or "").strip():
            fallbacks.append("self-hosted")
        if primary != "gemini" and (settings.gemini_api_key or "").strip():
            fallbacks.append("gemini")
        if primary != "mock":
            fallbacks.append("mock")
        return [primary, *fallbacks]

    def _http_client(self) -> httpx.AsyncClient:
        # Ignore HTTP(S)_PROXY — Cursor proxies break Quasar HTTPS CONNECT.
        return httpx.AsyncClient(timeout=self.timeout, trust_env=False)

    async def _call_provider(self, provider: str, system_prompt: str, user_prompt: str) -> str:
        if provider == "mock":
            return self._mock_response()
        if provider == "self-hosted":
            return await self._call_self_hosted(system_prompt, user_prompt)
        if provider == "gemini":
            return await self._call_gemini(system_prompt, user_prompt)
        raise ValueError(f"Unsupported provider: {provider}")

    async def _call_self_hosted(self, system_prompt: str, user_prompt: str) -> str:
        key = (settings.llm_api_key or "").strip()
        url = (settings.llm_api_url or "").strip()
        if not key or not url:
            raise RuntimeError("self-hosted requires LLM_API_KEY and LLM_API_URL")

        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": settings.model,
            "max_tokens": settings.max_tokens,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }

        async with self._http_client() as client:
            response = await client.post(url, headers=headers, json=payload)
            if response.status_code >= 400:
                body = response.text[:240]
                logger.error("Quasar error %s: %s", response.status_code, body)
                raise RuntimeError(f"HTTP {response.status_code}: {body}")
            data = response.json()
            return self._extract_openai_content(data)

    @staticmethod
    def _extract_openai_content(data: dict[str, Any]) -> str:
        choices = data.get("choices") or []
        if choices:
            message = choices[0].get("message") or {}
            content = message.get("content")
            if isinstance(content, str) and content.strip():
                return content
            if isinstance(content, list):
                parts = []
                for part in content:
                    if isinstance(part, dict) and part.get("text"):
                        parts.append(str(part["text"]))
                    elif isinstance(part, str):
                        parts.append(part)
                if parts:
                    return "\n".join(parts)
        if isinstance(data.get("text"), str) and data["text"].strip():
            return data["text"]
        raise RuntimeError(f"Unexpected Quasar response shape: {str(data)[:300]}")

    async def _call_gemini(self, system_prompt: str, user_prompt: str) -> str:
        model = settings.gemini_model
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{model}:generateContent?key={settings.gemini_api_key}"
        )
        payload = {
            "systemInstruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
            "generationConfig": {"maxOutputTokens": settings.max_tokens},
        }

        async with self._http_client() as client:
            response = await client.post(url, json=payload)
            if response.status_code >= 400:
                raise RuntimeError(f"Gemini HTTP {response.status_code}: {response.text[:240]}")
            data = response.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]

    @staticmethod
    def parse_json_response(text: str) -> dict[str, Any]:
        cleaned = text.strip()
        fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned)
        if fence_match:
            cleaned = fence_match.group(1).strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            start = cleaned.find("{")
            end = cleaned.rfind("}")
            if start != -1 and end != -1:
                return json.loads(cleaned[start : end + 1])
            raise

    def _mock_response(self) -> str:
        return json.dumps(
            {
                "emotional_profile": {
                    "primary_emotion": "restless curiosity",
                    "travel_personality": "The Thoughtful Explorer",
                    "decision_style": "Seeks meaning over hype",
                    "priority_factors": ["emotional renewal", "cultural depth"],
                },
                "travel_concepts": [
                    {
                        "title": "Slow Horizons",
                        "tagline": "Sample",
                        "emotional_hook": "Fallback payload",
                        "destinations": [
                            {
                                "name": "Luang Prabang",
                                "country": "Laos",
                                "match_score": 90,
                                "why_it_fits": "Internal client mock",
                                "estimated_cost": "$1,200",
                                "suggested_duration": "8 days",
                                "best_time_to_visit": "Nov–Feb",
                            }
                        ],
                        "vibe_keywords": ["serene"],
                        "sample_itinerary": ["Day 1: Arrive"],
                        "budget_breakdown": "n/a",
                        "personality_fit": "n/a",
                    }
                ],
                "inspiration_board": {
                    "board_title": "Fallback",
                    "subtitle": "Internal",
                    "emotional_summary": "Client mock",
                    "clusters": [
                        {
                            "cluster_name": "Quiet",
                            "theme": "Calm",
                            "mood_alignment": "peaceful",
                            "destinations": ["Luang Prabang"],
                            "visual_mood": "soft",
                            "color_palette": ["#2D5A4A", "#E8D5B7", "#87A878", "#F4E4C1"],
                            "suggested_activities": ["Walk"],
                        }
                    ],
                    "quote": "…",
                },
                "agent_reasoning": "Internal LLM-client mock",
                "source": "mock",
            }
        )
