from app.models.schemas import TravelRequest

PERSONALITY_ARCHETYPES = {
    "solo": "Independent Seeker — values freedom, self-discovery, flexible pacing",
    "couple": "Intimate Explorer — values shared moments, romance, privacy",
    "family": "Memory Builder — values safety, variety, kid-friendly wonder",
    "backpacker": "Budget Adventurer — values authenticity, social connections, flexibility",
    "luxury": "Curated Connoisseur — values comfort, exclusivity, seamless experiences",
    "digital nomad": "Rootless Creator — values connectivity, coworking, cultural immersion",
    "group": "Social Connector — values shared experiences, group activities, nightlife",
}


def build_personality_context(request: TravelRequest) -> str:
    style_key = request.travel_style.lower().strip()
    archetype = next(
        (desc for key, desc in PERSONALITY_ARCHETYPES.items() if key in style_key),
        "Flexible Traveler — open to diverse experiences",
    )
    currency = request.currency

    return f"""
DESTINATION MATCHING CRITERIA:
- Travel style archetype: {archetype}
- Budget constraint: {request.budget} (all amounts in {currency})
- Intent alignment: {request.intent}
- Global market: recommend worldwide destinations unless Policy restricts region/visa

MATCHING RULES:
1. Score each destination 0-100 based on mood + personality + budget + 3 Ps fit.
2. Prefer destinations that outperform popular alternatives for THIS specific traveler.
3. Include estimated cost range in {currency} and suggested trip duration.
4. Mention best time to visit considering weather and crowds.
5. Explain WHY each destination fits emotionally, not just logically.
6. Apply Profile / Preferences / Policy as weighted context — Policy is hard filter.
""".strip()
