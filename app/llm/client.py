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

    async def chat(self, system_prompt: str, user_prompt: str) -> str:
        chain = self._provider_chain()
        last_error: Exception | None = None

        for provider in chain:
            try:
                result = await self._call_provider(provider, system_prompt, user_prompt)
                self.last_provider_used = provider
                if provider != chain[0]:
                    logger.warning("LLM fallback: %s failed, used %s instead", chain[0], provider)
                return result
            except Exception as exc:
                last_error = exc
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

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, headers=headers, json=payload)
            if response.status_code >= 400:
                logger.error(
                    "Quasar error %s: %s",
                    response.status_code,
                    response.text[:500],
                )
            response.raise_for_status()
            data = response.json()
            return self._extract_openai_content(data)

    @staticmethod
    def _extract_openai_content(data: dict[str, Any]) -> str:
        # OpenAI-compatible: choices[0].message.content
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
        # Some routers return top-level text
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

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
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
                    "decision_style": "Seeks meaning over hype, values authentic experiences",
                    "priority_factors": ["emotional renewal", "cultural depth", "manageable cost"],
                },
                "travel_concepts": [
                    {
                        "title": "Slow Horizons",
                        "tagline": "Where time stretches and the soul exhales",
                        "emotional_hook": "You crave space to think without the pressure of ticking boxes.",
                        "destinations": [
                            {
                                "name": "Luang Prabang",
                                "country": "Laos",
                                "match_score": 94,
                                "why_it_fits": "Gentle pace, temple mornings, and river sunsets match a peaceful reset.",
                                "estimated_cost": "$1,200–$1,800 for 10 days (moderate)",
                                "suggested_duration": "8–12 days",
                                "best_time_to_visit": "November to February",
                            }
                        ],
                        "vibe_keywords": ["serene", "authentic", "unhurried"],
                        "sample_itinerary": [
                            "Day 1–2: Settle in, morning walks",
                            "Day 3–4: Nature day trips",
                            "Day 5–7: Cultural immersion",
                        ],
                        "budget_breakdown": "40% stay · 25% food · 20% transport · 15% experiences",
                        "personality_fit": "Quiet beauty over nightlife.",
                    }
                ],
                "inspiration_board": {
                    "board_title": "Your Soul Map",
                    "subtitle": "Sample board",
                    "emotional_summary": "Demo fallback when live LLM is unavailable.",
                    "clusters": [
                        {
                            "cluster_name": "Quiet Wonder",
                            "theme": "Places that whisper",
                            "mood_alignment": "Peaceful",
                            "destinations": ["Luang Prabang"],
                            "visual_mood": "Mist and golden hour",
                            "color_palette": ["#2D5A4A", "#E8D5B7", "#87A878", "#F4E4C1"],
                            "suggested_activities": ["Sunrise walk", "Local meal"],
                        }
                    ],
                    "quote": "Different feelings deserve different maps.",
                },
                "agent_reasoning": "Static LLM-client mock payload (prefer app mock_inspire).",
                "context_summary": "Internal fallback",
                "source": "mock",
            }
        )
