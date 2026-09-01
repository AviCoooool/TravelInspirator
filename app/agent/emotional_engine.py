from app.models.schemas import TravelRequest

MOOD_DIMENSIONS = {
    "restless": {"energy": "high", "seeking": "movement", "avoid": "routine"},
    "peaceful": {"energy": "low", "seeking": "calm", "avoid": "crowds"},
    "adventurous": {"energy": "high", "seeking": "challenge", "avoid": "comfort zones"},
    "romantic": {"energy": "medium", "seeking": "connection", "avoid": "harsh environments"},
    "curious": {"energy": "medium", "seeking": "learning", "avoid": "superficial tourism"},
    "burnt-out": {"energy": "low", "seeking": "restoration", "avoid": "packed schedules"},
    "excited": {"energy": "high", "seeking": "novelty", "avoid": "repetition"},
    "nostalgic": {"energy": "medium", "seeking": "meaning", "avoid": "ultra-modern only"},
    "happy": {"energy": "high", "seeking": "celebration", "avoid": "heavy logistics"},
    "sad": {"energy": "low", "seeking": "healing", "avoid": "overstimulation"},
    "frustrated": {"energy": "medium", "seeking": "release", "avoid": "rigid schedules"},
    "anxious": {"energy": "medium", "seeking": "safety", "avoid": "uncertainty"},
}

# Approximate daily ranges by currency for each budget tier
BUDGET_BY_CURRENCY = {
    "USD": {
        "budget": "$30–$70",
        "moderate": "$80–$150",
        "luxury": "$200+",
        "flexible": "varies",
    },
    "EUR": {
        "budget": "€30–€65",
        "moderate": "€75–€140",
        "luxury": "€190+",
        "flexible": "varies",
    },
    "GBP": {
        "budget": "£25–£55",
        "moderate": "£65–£120",
        "luxury": "£170+",
        "flexible": "varies",
    },
    "INR": {
        "budget": "₹2,000–₹5,000",
        "moderate": "₹6,000–₹12,000",
        "luxury": "₹15,000+",
        "flexible": "varies",
    },
    "AED": {
        "budget": "AED 110–260",
        "moderate": "AED 300–550",
        "luxury": "AED 750+",
        "flexible": "varies",
    },
    "JPY": {
        "budget": "¥4,500–¥10,000",
        "moderate": "¥12,000–¥22,000",
        "luxury": "¥30,000+",
        "flexible": "varies",
    },
    "AUD": {
        "budget": "A$45–A$100",
        "moderate": "A$120–A$220",
        "luxury": "A$300+",
        "flexible": "varies",
    },
}

BUDGET_STYLES = {
    "budget": "hostels / guesthouses, street food, public transport",
    "moderate": "boutique stays, mix of dining, some tours",
    "luxury": "premium hotels, fine dining, private experiences",
    "flexible": "optimize for experience over fixed spend tier",
}


def _fmt_optional(label: str, value: str | None) -> str:
    return f"- {label}: {value}" if value else f"- {label}: not provided"


def build_emotional_context(request: TravelRequest) -> str:
    mood_key = request.mood.lower().strip()
    mood_data = MOOD_DIMENSIONS.get(
        mood_key, {"energy": "medium", "seeking": "balance", "avoid": "mismatch"}
    )
    currency = request.currency
    daily = BUDGET_BY_CURRENCY.get(currency, BUDGET_BY_CURRENCY["USD"]).get(
        request.budget, BUDGET_BY_CURRENCY["USD"]["moderate"]
    )
    style = BUDGET_STYLES.get(request.budget, BUDGET_STYLES["moderate"])

    profile = request.profile
    preferences = request.preferences
    policy = request.policy
    signals = request.emotion_signals

    three_ps = "\n".join(
        [
            "PROFILE (identity):",
            _fmt_optional("Home base", profile.home_base if profile else None),
            _fmt_optional("Traveler type", profile.traveler_type if profile else None),
            _fmt_optional("Languages", profile.languages if profile else None),
            _fmt_optional("Companions", profile.companions if profile else None),
            "PREFERENCES (soft likes):",
            _fmt_optional("Interests", preferences.interests if preferences else None),
            _fmt_optional("Pace", preferences.pace if preferences else None),
            _fmt_optional("Climate", preferences.climate if preferences else None),
            _fmt_optional(
                "Social context / friend-circle cues",
                preferences.social_context if preferences else None,
            ),
            "POLICY (hard constraints):",
            _fmt_optional("Visa constraints", policy.visa_constraints if policy else None),
            _fmt_optional("Corporate policy", policy.corporate_policy if policy else None),
            _fmt_optional("Accessibility", policy.accessibility if policy else None),
            _fmt_optional("Max flight hours", policy.max_flight_hours if policy else None),
        ]
    )

    emotion_block = "\n".join(
        [
            "MULTI-MODAL EMOTION SIGNALS:",
            f"- Capture source: {signals.source if signals else 'manual'}",
            _fmt_optional("Facial / selfie hint", signals.facial_hint if signals else None),
            _fmt_optional("Voice emotion hint", signals.voice_hint if signals else None),
            _fmt_optional("Text sentiment", signals.text_sentiment if signals else None),
            _fmt_optional(
                "Signal confidence",
                f"{signals.confidence:.0%}" if signals and signals.confidence is not None else None,
            ),
        ]
    )

    return f"""
EMOTIONAL PROFILE INPUT:
- Stated mood: {request.mood}
- Mood energy level: {mood_data['energy']}
- Core seeking: {mood_data['seeking']}
- Should avoid: {mood_data['avoid']}
- Travel intent: {request.intent}
- Travel style: {request.travel_style}
- Budget tier: {request.budget} ({daily}/day in {currency}, {style})
- Currency for all cost estimates: {currency}
- Additional context: {request.context or 'None provided'}

{three_ps}

{emotion_block}

EMOTIONAL RECOMMENDATION GUIDELINES:
1. Lead with how each destination will make the traveler FEEL, not just what to see.
2. Fuse mood + multi-modal emotion signals + Profile / Preferences / Policy (3 Ps) before recommending.
3. Match personality archetype (Explorer, Nurturer, Seeker, Connector, Adventurer, Restorer).
4. Prefer destinations that fit THIS traveler over purely popular alternatives.
5. Express ALL costs in {currency}. Be honest about cost and time trade-offs.
6. Provide 2-3 curated travel concepts with 1-3 destinations each.
7. Create an inspiration board with 2-3 thematic clusters.
8. Respect hard Policy constraints even if they conflict with mood-led ideas.
""".strip()
