from typing import Literal

from pydantic import BaseModel, Field

CurrencyCode = Literal["USD", "EUR", "GBP", "INR", "AED", "JPY", "AUD"]
BudgetTier = Literal["budget", "moderate", "luxury", "flexible"]
EmotionSource = Literal["manual", "selfie", "voice", "text_sentiment"]


class TravelProfile(BaseModel):
    """Traveler identity context (the first P)."""

    home_base: str | None = Field(None, description="City/country of residence")
    traveler_type: str | None = Field(None, description="e.g. leisure, bleisure, corporate, student")
    languages: str | None = Field(None, description="Preferred languages")
    companions: str | None = Field(None, description="Who they travel with")


class TravelPreferences(BaseModel):
    """Soft preferences that enrich recommendations (the second P)."""

    interests: str | None = Field(None, description="Culture, food, nature, nightlife, wellness...")
    pace: str | None = Field(None, description="slow / balanced / packed")
    climate: str | None = Field(None, description="Preferred climate")
    social_context: str | None = Field(
        None, description="Friend circle / social inspiration cues (future: Instagram/TikTok graph)"
    )


class TravelPolicy(BaseModel):
    """Hard constraints and policies (the third P)."""

    visa_constraints: str | None = Field(None, description="Visa / passport constraints")
    corporate_policy: str | None = Field(None, description="Company travel policy rules")
    accessibility: str | None = Field(None, description="Accessibility needs")
    max_flight_hours: str | None = Field(None, description="Max acceptable flight duration")


class EmotionSignals(BaseModel):
    """Multi-modal emotion capture signals for the agent."""

    source: EmotionSource = "manual"
    facial_hint: str | None = Field(None, description="Selfie-derived expression hint, e.g. happy, sad, frustrated")
    voice_hint: str | None = Field(None, description="Voice-tone / spoken emotion hint")
    text_sentiment: str | None = Field(None, description="Sentiment inferred from intent text")
    confidence: float | None = Field(None, ge=0, le=1, description="Optional confidence score")


class TravelRequest(BaseModel):
    mood: str = Field(..., description="Current emotional state")
    intent: str = Field(..., description="What the traveler hopes to gain from the trip")
    budget: BudgetTier = Field("moderate", description="Daily budget tier")
    currency: CurrencyCode = Field("INR", description="Preferred currency for cost estimates")
    travel_style: str = Field(..., description="Preferred travel style")
    context: str | None = Field(None, description="Season, duration, departure city, constraints")
    profile: TravelProfile | None = None
    preferences: TravelPreferences | None = None
    policy: TravelPolicy | None = None
    emotion_signals: EmotionSignals | None = None


class DestinationMatch(BaseModel):
    name: str
    country: str
    match_score: int = Field(..., ge=0, le=100)
    why_it_fits: str
    estimated_cost: str
    suggested_duration: str
    best_time_to_visit: str


class TravelConcept(BaseModel):
    title: str
    tagline: str
    emotional_hook: str
    destinations: list[DestinationMatch]
    vibe_keywords: list[str]
    sample_itinerary: list[str]
    budget_breakdown: str
    personality_fit: str


class InspirationCluster(BaseModel):
    cluster_name: str
    theme: str
    mood_alignment: str
    destinations: list[str]
    visual_mood: str
    color_palette: list[str]
    suggested_activities: list[str]


class InspirationBoard(BaseModel):
    board_title: str
    subtitle: str
    emotional_summary: str
    clusters: list[InspirationCluster]
    quote: str


class EmotionalProfile(BaseModel):
    primary_emotion: str
    travel_personality: str
    decision_style: str
    priority_factors: list[str]


class TravelResponse(BaseModel):
    emotional_profile: EmotionalProfile
    travel_concepts: list[TravelConcept]
    inspiration_board: InspirationBoard
    agent_reasoning: str
    context_summary: str | None = Field(
        None, description="How Profile, Preferences, Policy, and emotion signals shaped the result"
    )
    source: Literal["gemini", "mock", "self-hosted"] = Field(
        "mock",
        description="Which engine produced this response: Quasar self-hosted, Gemini, or local mock",
    )
