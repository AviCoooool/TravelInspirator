import json
import logging
import re
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class LLMClient:
    """LLM client supporting Gemini and mock providers."""

    def __init__(self) -> None:
        self.provider = settings.provider.lower()
        if self.provider not in {"gemini", "mock"}:
            self.provider = "gemini"
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
        if primary != "gemini" and settings.gemini_api_key:
            fallbacks.append("gemini")
        if primary != "mock":
            fallbacks.append("mock")
        return [primary, *fallbacks]

    async def _call_provider(self, provider: str, system_prompt: str, user_prompt: str) -> str:
        if provider == "mock":
            return self._mock_response()
        if provider == "gemini":
            return await self._call_gemini(system_prompt, user_prompt)
        raise ValueError(f"Unsupported provider: {provider}")

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
                            },
                            {
                                "name": "Azores",
                                "country": "Portugal",
                                "match_score": 89,
                                "why_it_fits": "Dramatic nature without crowds; ideal for reflective solo travel.",
                                "estimated_cost": "$1,500–$2,200 for 7 days (moderate)",
                                "suggested_duration": "5–8 days",
                                "best_time_to_visit": "May to October",
                            },
                        ],
                        "vibe_keywords": ["serene", "authentic", "unhurried", "green"],
                        "sample_itinerary": [
                            "Day 1–2: Settle in, morning walks, local café rituals",
                            "Day 3–4: Nature day trips without rigid schedules",
                            "Day 5–7: Cultural immersion — markets, cooking, conversations",
                        ],
                        "budget_breakdown": "40% accommodation, 25% food, 20% transport, 15% experiences",
                        "personality_fit": "Perfect for travelers who recharge through quiet beauty rather than nightlife.",
                    },
                    {
                        "title": "Hidden Mediterranean",
                        "tagline": "Sun-soaked secrets the crowds haven't found",
                        "emotional_hook": "You want warmth and wonder without the Instagram circus.",
                        "destinations": [
                            {
                                "name": "Puglia",
                                "country": "Italy",
                                "match_score": 91,
                                "why_it_fits": "Trulli towns and Adriatic coast deliver Italy's soul at half the price of Rome.",
                                "estimated_cost": "$1,800–$2,500 for 10 days (moderate)",
                                "suggested_duration": "7–10 days",
                                "best_time_to_visit": "April to June",
                            }
                        ],
                        "vibe_keywords": ["sun-drenched", "local", "coastal", "foodie"],
                        "sample_itinerary": [
                            "Day 1–3: Base in Ostuni, explore white hill towns",
                            "Day 4–5: Adriatic beach days and seafood dinners",
                            "Day 6–8: Lecce baroque architecture and wine country",
                        ],
                        "budget_breakdown": "35% accommodation, 30% food, 20% transport, 15% experiences",
                        "personality_fit": "Ideal for food-loving explorers who prefer charm over celebrity destinations.",
                    },
                ],
                "inspiration_board": {
                    "board_title": "Your Soul Map",
                    "subtitle": "Curated for a restless heart seeking gentle adventure",
                    "emotional_summary": "You're not looking for the most popular place — you're looking for the place that will change how you feel.",
                    "clusters": [
                        {
                            "cluster_name": "Quiet Wonder",
                            "theme": "Places that whisper instead of shout",
                            "mood_alignment": "Peaceful introspection with subtle awe",
                            "destinations": ["Luang Prabang", "Azores", "Slovenian Alps"],
                            "visual_mood": "Mist over mountains, golden hour light, empty paths",
                            "color_palette": ["#2D5A4A", "#E8D5B7", "#87A878", "#F4E4C1"],
                            "suggested_activities": [
                                "Sunrise meditation at a temple",
                                "Coastal hiking with picnic lunch",
                                "Local cooking class with a family",
                            ],
                        },
                        {
                            "cluster_name": "Warm Discovery",
                            "theme": "Sun, culture, and flavors that feel like home",
                            "mood_alignment": "Curious contentment and sensory joy",
                            "destinations": ["Puglia", "Croatian islands", "Moroccan coast"],
                            "visual_mood": "Terracotta rooftops, turquoise water, market colors",
                            "color_palette": ["#C4704A", "#2E86AB", "#F5E6D3", "#D4A574"],
                            "suggested_activities": [
                                "Wandering through old town markets",
                                "Sunset aperitivo by the sea",
                                "Day trip to a lesser-known village",
                            ],
                        },
                    ],
                    "quote": "Travel isn't about finding yourself — it's about finding the place that lets you breathe.",
                },
                "agent_reasoning": "Based on a restless yet reflective mood with moderate budget, I prioritized destinations offering emotional renewal over tourist density. The recommendations balance cost efficiency with transformative experiences.",
                "context_summary": "Mood=restless · Currency=USD · Budget=moderate · Style=solo · EmotionSource=manual · Demo mock data",
            }
        )
