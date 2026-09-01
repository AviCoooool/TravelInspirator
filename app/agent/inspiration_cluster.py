from app.models.schemas import TravelRequest


def build_clustering_context(request: TravelRequest) -> str:
    return f"""
INSPIRATION CLUSTERING GUIDELINES:
- Group destinations into 2-3 thematic clusters for a visual inspiration board.
- Each cluster needs: name, theme, mood alignment, destinations, visual mood description, color palette (4 hex colors), activities.
- The board should feel like a Pinterest/mood board — evocative and personal.
- Board title and subtitle should reflect the traveler's emotional journey.
- Include an inspiring quote tailored to their mood and intent.
- Reference their mood ({request.mood}) and intent ({request.intent}) throughout.
- Costs and practical cues should remain consistent with currency {request.currency}.
""".strip()
