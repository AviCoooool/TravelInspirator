from app.agent.destination_matcher import build_personality_context
from app.agent.emotional_engine import build_emotional_context
from app.agent.inspiration_cluster import build_clustering_context
from app.agent.mock_inspire import build_mock_response
from app.config import settings
from app.llm.client import LLMClient
from app.models.schemas import TravelRequest, TravelResponse

SYSTEM_PROMPT = """You are the AI Travel Inspirator — an emotion-first, context-aware travel discovery agent.

Your mission is to help people who don't know where to go find destinations that will genuinely make them happier — not just the most popular places.

You excel at:
1. Emotional recommendation — matching feelings (manual, selfie, voice, text sentiment) to places
2. Personality-driven destination matching — understanding travel style
3. Inspiration clustering — creating mood boards of travel possibilities
4. Context-aware suggestions — fusing Profile, Preferences, and Policy (the 3 Ps) with budget/currency

Always respond with valid JSON matching this exact schema:
{
  "emotional_profile": {
    "primary_emotion": "string",
    "travel_personality": "string (archetype name)",
    "decision_style": "string",
    "priority_factors": ["string", ...]
  },
  "travel_concepts": [
    {
      "title": "string",
      "tagline": "string",
      "emotional_hook": "string",
      "destinations": [
        {
          "name": "string",
          "country": "string",
          "match_score": 0-100,
          "why_it_fits": "string",
          "estimated_cost": "string",
          "suggested_duration": "string",
          "best_time_to_visit": "string"
        }
      ],
      "vibe_keywords": ["string", ...],
      "sample_itinerary": ["string", ...],
      "budget_breakdown": "string",
      "personality_fit": "string"
    }
  ],
  "inspiration_board": {
    "board_title": "string",
    "subtitle": "string",
    "emotional_summary": "string",
    "clusters": [
      {
        "cluster_name": "string",
        "theme": "string",
        "mood_alignment": "string",
        "destinations": ["string", ...],
        "visual_mood": "string",
        "color_palette": ["#hex", ...],
        "suggested_activities": ["string", ...]
      }
    ],
    "quote": "string"
  },
  "agent_reasoning": "string explaining your recommendation logic",
  "context_summary": "string summarizing how 3 Ps + emotion signals shaped recommendations"
}

Provide 2-3 travel concepts and 2-3 inspiration clusters. Be specific, warm, and honest about trade-offs.

IMPORTANT:
- Express ALL costs in the traveler's selected currency (USD / EUR / GBP / INR / AED / JPY / AUD).
- Respect home_base first: prefer domestic and nearby regional destinations when home base or currency (e.g. INR → India) implies local travel. Do NOT default to far-away Europe/US icons unless the traveler clearly wants international.
- Mix: include at least 1–2 destinations in/near the traveler's home country when known; international only when mood/budget/intent ask for it.
- Policy constraints are hard filters; Preferences and Profile are soft ranking signals.
- Multi-modal emotion signals (selfie / voice / text sentiment) should influence tone of recommendations.
"""


def _build_context_summary(request: TravelRequest) -> str:
    parts = [
        f"Mood={request.mood}",
        f"Currency={request.currency}",
        f"Budget={request.budget}",
        f"Style={request.travel_style}",
    ]
    if request.emotion_signals:
        parts.append(f"EmotionSource={request.emotion_signals.source}")
        if request.emotion_signals.facial_hint:
            parts.append(f"Facial={request.emotion_signals.facial_hint}")
        if request.emotion_signals.voice_hint:
            parts.append(f"Voice={request.emotion_signals.voice_hint}")
        if request.emotion_signals.text_sentiment:
            parts.append(f"Sentiment={request.emotion_signals.text_sentiment}")
    if request.profile and any(
        [request.profile.home_base, request.profile.traveler_type, request.profile.companions]
    ):
        parts.append("Profile=enriched")
    if request.preferences and any(
        [request.preferences.interests, request.preferences.pace, request.preferences.social_context]
    ):
        parts.append("Preferences=enriched")
    if request.policy and any(
        [
            request.policy.visa_constraints,
            request.policy.corporate_policy,
            request.policy.accessibility,
        ]
    ):
        parts.append("Policy=applied")
    return " · ".join(parts)


class TravelAgent:
    def __init__(self) -> None:
        self.llm = LLMClient()

    async def inspire(self, request: TravelRequest) -> TravelResponse:
        # Mood-aware mock when explicitly in mock mode (or no Gemini key)
        if settings.provider.lower() == "mock" or not (settings.gemini_api_key or "").strip():
            return build_mock_response(request)

        user_prompt = "\n\n".join(
            [
                build_emotional_context(request),
                build_personality_context(request),
                build_clustering_context(request),
                (
                    "Generate personalized travel inspiration for this traveler. "
                    "Prefer domestic/nearby destinations when home_base or currency implies local travel "
                    f"(e.g. INR or India home → India-first). Use currency {request.currency} for all costs. "
                    "Return JSON only."
                ),
            ]
        )

        try:
            raw = await self.llm.chat(SYSTEM_PROMPT, user_prompt)
            data = self.llm.parse_json_response(raw)
            data["context_summary"] = _build_context_summary(request)
            data["source"] = "gemini"
            response = TravelResponse.model_validate(data)
            if self.llm.last_provider_used == "mock":
                # LLM chain fell back to static mock — replace with mood-aware mock
                return build_mock_response(request)
            return response
        except Exception:
            return build_mock_response(request)
