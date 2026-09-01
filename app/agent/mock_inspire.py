"""Request-aware mock inspiration — varies by mood, currency, style (demo without LLM)."""

from __future__ import annotations

from app.models.schemas import TravelRequest, TravelResponse

# Mood → curated concepts (name, country, why, season, duration days)
MOOD_DESTINATIONS: dict[str, list[dict]] = {
    "peaceful": [
        {
            "title": "Still Waters",
            "tagline": "Quiet places that lower the volume of life",
            "hook": "You need calm that isn't empty — beauty without noise.",
            "destinations": [
                ("Kyoto", "Japan", "Temple gardens and slow mornings reset a restless mind.", "March–May or Oct–Nov", 8),
                ("Queenstown lakeside", "New Zealand", "Alpine water and open sky without megacity pace.", "Dec–Mar", 7),
            ],
            "vibes": ["calm", "green", "ritual", "silence"],
            "cluster": ("Soft Stillness", "Places that whisper", "#2D5A4A", "#E8D5B7"),
        },
        {
            "title": "Coastal Exhale",
            "tagline": "Sea air and soft schedules",
            "hook": "Water and wind do the healing when itineraries won't.",
            "destinations": [
                ("Algarve (west coast)", "Portugal", "Cliffs and quiet beaches without Albufeira crowds.", "May–Jun or Sep", 7),
                ("Tulum (away from strip)", "Mexico", "Cenotes and jungle calm if you stay inland.", "Nov–Apr", 6),
            ],
            "vibes": ["ocean", "breeze", "unhurried", "sun"],
            "cluster": ("Salt & Sky", "Coastal restoration", "#2E86AB", "#F5E6D3"),
        },
    ],
    "adventurous": [
        {
            "title": "Edge of the Map",
            "tagline": "Movement, altitude, and earned views",
            "hook": "You want challenge that wakes you up — not a checklist of tourist traps.",
            "destinations": [
                ("Patagonia", "Chile / Argentina", "Trekking and vast landscapes match high energy.", "Nov–Mar", 12),
                ("Nepal (Annapurna region)", "Nepal", "Trail days and teahouse rhythm for true adventure.", "Mar–May or Oct–Nov", 10),
            ],
            "vibes": ["rugged", "altitude", "wild", "trail"],
            "cluster": ("Wild Heights", "Earn the view", "#C4704A", "#3D5A5B"),
        },
        {
            "title": "Active Horizons",
            "tagline": "Surf, climb, cycle — stay in motion",
            "hook": "Adventure that still leaves room for local food and people.",
            "destinations": [
                ("Bali (Uluwatu / Amed)", "Indonesia", "Surf + cliffs + quieter east-coast diving.", "Apr–Oct", 10),
                ("Interlaken region", "Switzerland", "Paragliding, trails, lakes — high-adrenaline hub.", "Jun–Sep", 7),
            ],
            "vibes": ["sport", "adrenaline", "scenic", "active"],
            "cluster": ("Motion First", "Body in motion, mind clear", "#E07A5F", "#81B29A"),
        },
    ],
    "romantic": [
        {
            "title": "Soft Light Escapes",
            "tagline": "Places built for two",
            "hook": "Connection thrives where evenings linger and crowds thin out.",
            "destinations": [
                ("Amalfi (Positano off-peak)", "Italy", "Vertical beauty and shared meals by the sea.", "Apr–May or Sep–Oct", 7),
                ("Santorini (Oia quieter hours)", "Greece", "Sunset drama — visit shoulder season for intimacy.", "Apr–Jun or Sep", 5),
            ],
            "vibes": ["intimate", "sunset", "wine", "together"],
            "cluster": ("Golden Hour", "Evenings meant for two", "#C4704A", "#F4E4C1"),
        },
        {
            "title": "Hidden Romance",
            "tagline": "Charm without the circus",
            "hook": "You want romance that feels discovered, not staged.",
            "destinations": [
                ("Ljubljana + Lake Bled", "Slovenia", "Fairytale scale without Italian summer crush.", "May–Sep", 6),
                ("Colmar / Alsace", "France", "Canal towns and wine villages for quiet walks.", "May–Jun or Sep", 5),
            ],
            "vibes": ["storybook", "local", "walkable", "wine"],
            "cluster": ("Quiet Spark", "Romance off the main stage", "#B8A9C9", "#E8D5B7"),
        },
    ],
    "curious": [
        {
            "title": "Culture Deep Dive",
            "tagline": "Learn with your feet",
            "hook": "Curiosity wants layers — markets, museums, conversations.",
            "destinations": [
                ("Istanbul", "Turkey", "Two continents, endless texture, food as storytelling.", "Apr–May or Sep–Oct", 8),
                ("Mexico City", "Mexico", "Museums, murals, markets — dense cultural payoff.", "Nov–Apr", 7),
            ],
            "vibes": ["culture", "food", "history", "urban"],
            "cluster": ("Layered Cities", "Curiosity rewarded", "#2E86AB", "#D4A574"),
        },
        {
            "title": "Living Museums",
            "tagline": "Places that teach without lectures",
            "hook": "You learn best when the city is the classroom.",
            "destinations": [
                ("Fez medina", "Morocco", "Artisan alleys and sensory immersion.", "Mar–May or Sep–Nov", 6),
                ("Hanoi + Ninh Binh", "Vietnam", "Street culture plus nature day trips.", "Oct–Apr", 8),
            ],
            "vibes": ["artisan", "street", "authentic", "sensory"],
            "cluster": ("Texture Trail", "Learn through the senses", "#E8A87C", "#87A878"),
        },
    ],
    "excited": [
        {
            "title": "High Spark Cities",
            "tagline": "Energy that matches yours",
            "hook": "Excitement wants nightlife, novelty, and big moments.",
            "destinations": [
                ("Tokyo", "Japan", "Neon, food alleys, endless neighborhoods to explore.", "Mar–May or Oct–Nov", 8),
                ("Barcelona", "Spain", "Beach + architecture + night energy.", "May–Jun or Sep", 6),
            ],
            "vibes": ["vibrant", "nightlife", "iconic", "buzz"],
            "cluster": ("Bright Pulse", "Cities that keep up", "#E07A5F", "#F2CC8F"),
        },
        {
            "title": "Festival & Flow",
            "tagline": "Moments you won't forget",
            "hook": "You want stories — not just sights.",
            "destinations": [
                ("Rio de Janeiro", "Brazil", "Music, movement, and dramatic coastline.", "Sep–Mar (avoid peak Carnival prices if needed)", 7),
                ("Berlin", "Germany", "Creative scenes, day trips, nocturnal culture.", "May–Sep", 6),
            ],
            "vibes": ["music", "creative", "bold", "social"],
            "cluster": ("Story Fuel", "Memories over monuments", "#81B29A", "#E07A5F"),
        },
    ],
    "burnt-out": [
        {
            "title": "Reset Mode",
            "tagline": "Low stimulation, high restoration",
            "hook": "You don't need more input — you need permission to stop.",
            "destinations": [
                ("Ubud (outskirts)", "Indonesia", "Rice terraces and slow mornings away from party zones.", "Apr–Oct", 8),
                ("Finnish Lapland (summer)", "Finland", "Nature silence and soft light — true mental quiet.", "Jun–Aug", 7),
            ],
            "vibes": ["restorative", "slow", "nature", "gentle"],
            "cluster": ("Nervous System Reset", "Heal before you hustle", "#2D5A4A", "#F4E4C1"),
        },
        {
            "title": "Spa of Place",
            "tagline": "The destination is the treatment",
            "hook": "Choose places designed for recovery, not FOMO.",
            "destinations": [
                ("Banff / Lake Louise (off-peak)", "Canada", "Mountain air and short walks beat packed itineraries.", "May–Jun or Sep", 6),
                ("Chiang Mai", "Thailand", "Cafés, temples, massage culture — soft landing.", "Nov–Feb", 7),
            ],
            "vibes": ["wellness", "soft", "retreat", "air"],
            "cluster": ("Gentle Days", "Do less, feel more", "#87A878", "#E8D5B7"),
        },
    ],
    "nostalgic": [
        {
            "title": "Memory Landscapes",
            "tagline": "Places that feel like stories you already know",
            "hook": "Nostalgia wants texture — old towns, trains, handwritten pace.",
            "destinations": [
                ("Prague", "Czechia", "Cobblestones and café culture with fairy-tale gravity.", "Apr–Jun or Sep", 5),
                ("Kyoto (Gion evenings)", "Japan", "Timeless rituals and lantern streets.", "Mar–May or Nov", 7),
            ],
            "vibes": ["timeless", "story", "heritage", "soft"],
            "cluster": ("Yesterday's Light", "Memory-forward travel", "#B8A9C9", "#E8D5B7"),
        },
        {
            "title": "Heritage Trails",
            "tagline": "The past, walking-distance",
            "hook": "You want meaning layered into streets and meals.",
            "destinations": [
                ("Lisbon + Sintra", "Portugal", "Trams, azulejos, and day-trip palaces.", "Apr–Jun or Sep–Oct", 6),
                ("Hoi An", "Vietnam", "Lantern town charm and riverside evenings.", "Feb–Apr", 5),
            ],
            "vibes": ["heritage", "lanterns", "coastal", "photo"],
            "cluster": ("Keepsake Towns", "Bring home a feeling", "#C4704A", "#F5E6D3"),
        },
    ],
    "restless": [
        {
            "title": "Motion Therapy",
            "tagline": "New ground under your feet",
            "hook": "Restlessness wants change of scenery — not more scrolling.",
            "destinations": [
                ("Georgia (Tbilisi + Kazbegi)", "Georgia", "City energy plus mountain day trips.", "May–Oct", 8),
                ("Cape Town + surrounds", "South Africa", "City, coast, and wine country in one trip.", "Oct–Apr", 9),
            ],
            "vibes": ["change", "contrast", "drive", "discover"],
            "cluster": ("New Ground", "Shake the snowglobe", "#E8A87C", "#2E86AB"),
        },
        {
            "title": "Open Road Energy",
            "tagline": "Itineraries with breathing room",
            "hook": "You need options, not a rigid tour bus.",
            "destinations": [
                ("Iceland (Ring Road highlights)", "Iceland", "Waterfalls and wild weather — motion as medicine.", "Jun–Aug", 8),
                ("Scotland Highlands", "United Kingdom", "Road-trip solitude and dramatic landscapes.", "May–Sep", 7),
            ],
            "vibes": ["road", "wild", "weather", "space"],
            "cluster": ("Wide Open", "Distance clears the head", "#3D5A5B", "#E8D5B7"),
        },
    ],
    "happy": [
        {
            "title": "Celebrate Out Loud",
            "tagline": "Joy deserves a stage",
            "hook": "Happiness wants color, music, and shared tables.",
            "destinations": [
                ("Lisbon", "Portugal", "Sun, miradouros, and late dinners with friends.", "May–Jun or Sep", 6),
                ("Seville", "Spain", "Tapas, plazas, and festive street life.", "Mar–May or Sep–Oct", 5),
            ],
            "vibes": ["festive", "sunny", "social", "music"],
            "cluster": ("Bright Tables", "Joy in public", "#E07A5F", "#F2CC8F"),
        },
        {
            "title": "Playful Escapes",
            "tagline": "Light itineraries, big smiles",
            "hook": "Keep it playful — not precious.",
            "destinations": [
                ("Copenhagen", "Denmark", "Design, bikes, and hygge-level good vibes.", "May–Aug", 5),
                ("Melbourne", "Australia", "Coffee culture, laneways, nearby coast.", "Sep–Nov or Mar–May", 6),
            ],
            "vibes": ["playful", "design", "café", "easy"],
            "cluster": ("Easy Joy", "Happy without trying", "#81B29A", "#E8C99A"),
        },
    ],
    "sad": [
        {
            "title": "Gentle Holding Places",
            "tagline": "Soft landscapes for heavy days",
            "hook": "When you're low, choose places that hold you — not hype you.",
            "destinations": [
                ("Irish countryside (Galway + Connemara)", "Ireland", "Green space and kind hospitality.", "May–Sep", 7),
                ("Lake District", "United Kingdom", "Walks, water, and quiet inns.", "May–Sep", 5),
            ],
            "vibes": ["gentle", "green", "healing", "rain"],
            "cluster": ("Soft Ground", "Healing at walking pace", "#2D5A4A", "#B8A9C9"),
        },
        {
            "title": "Warmth & Kindness",
            "tagline": "Sun and soft company",
            "hook": "Warmth outside can help warmth return inside.",
            "destinations": [
                ("Crete (west coast villages)", "Greece", "Village hospitality and sea without Athens rush.", "May–Jun or Sep", 7),
                ("Sri Lanka (south coast quieter towns)", "Sri Lanka", "Ocean, tea country day trips, gentle rhythm.", "Dec–Mar", 8),
            ],
            "vibes": ["warm", "kind", "sea", "slow"],
            "cluster": ("Held by Place", "Let the land care for you", "#E8A87C", "#87A878"),
        },
    ],
    "frustrated": [
        {
            "title": "Release Valves",
            "tagline": "Burn energy, not bridges",
            "hook": "Frustration needs movement and distance from triggers.",
            "destinations": [
                ("Dolomites", "Italy", "Day hikes that empty the mind.", "Jun–Sep", 6),
                ("Costa Rica (Arenal / Monteverde)", "Costa Rica", "Nature intensity without urban friction.", "Dec–Apr", 8),
            ],
            "vibes": ["release", "physical", "nature", "clear"],
            "cluster": ("Burn It Off", "Move until it softens", "#E07A5F", "#3D5A5B"),
        },
        {
            "title": "Clean Slate Cities",
            "tagline": "New systems, new habits",
            "hook": "A different city rhythm can interrupt a stuck loop.",
            "destinations": [
                ("Singapore", "Singapore", "Order, greenery, food — frictionless days.", "Year-round (avoid peak humidity if possible)", 5),
                ("Seoul", "South Korea", "Efficient transit + vibrant food scenes.", "Apr–Jun or Sep–Oct", 6),
            ],
            "vibes": ["efficient", "fresh", "urban", "reset"],
            "cluster": ("System Reset", "Friction out, flow in", "#2E86AB", "#E8D5B7"),
        },
    ],
    "anxious": [
        {
            "title": "Safe Soft Landings",
            "tagline": "Predictable, welcoming, low chaos",
            "hook": "Anxiety eases when logistics are simple and people are kind.",
            "destinations": [
                ("Amsterdam", "Netherlands", "Walkable, English-friendly, clear transit.", "Apr–Jun or Sep", 5),
                ("Vancouver", "Canada", "Nature + city safety net for nervous systems.", "May–Sep", 6),
            ],
            "vibes": ["safe", "walkable", "clear", "kind"],
            "cluster": ("Steady Ground", "Low-anxiety logistics", "#81B29A", "#E8C99A"),
        },
        {
            "title": "Nature Buffer",
            "tagline": "Fewer crowds, more oxygen",
            "hook": "Open space reduces noise — literally and mentally.",
            "destinations": [
                ("Norwegian fjords (Bergen base)", "Norway", "Scenic day trips with calm evenings.", "Jun–Aug", 7),
                ("Tasmania", "Australia", "Quiet nature and small-town pace.", "Dec–Mar", 8),
            ],
            "vibes": ["space", "air", "quiet", "grounded"],
            "cluster": ("Wide Calm", "Anxiety loses volume outdoors", "#2D5A4A", "#F4E4C1"),
        },
    ],
}

DEFAULT_MOOD = "curious"

# India-first packs — used when home base / currency implies India (demo without LLM)
INDIA_MOOD_DESTINATIONS: dict[str, list[dict]] = {
    "peaceful": [
        {
            "title": "Quiet India",
            "tagline": "Stillness without a passport queue",
            "hook": "You need calm close to home — beauty without long-haul fatigue.",
            "destinations": [
                ("Alleppey backwaters", "India", "Houseboat pace and coconut silence reset a noisy mind.", "Sep–Mar", 5),
                ("Spiti Valley (shoulder)", "India", "High desert quiet and monastery mornings.", "Jun–Sep", 8),
            ],
            "vibes": ["calm", "water", "mountains", "slow"],
            "cluster": ("Near Calm", "Peace within reach", "#2D5A4A", "#E8D5B7"),
        },
        {
            "title": "Soft Hills",
            "tagline": "Cool air, short flights",
            "hook": "A weekend of green can do more than a far-away checklist.",
            "destinations": [
                ("Coorg", "India", "Coffee estates and misty walks — unhurried South.", "Oct–Mar", 4),
                ("Munnar", "India", "Tea gardens and soft weather for mental quiet.", "Sep–Mar", 4),
            ],
            "vibes": ["green", "tea", "estate", "breeze"],
            "cluster": ("Hill Exhale", "Domestic restoration", "#87A878", "#F5E6D3"),
        },
    ],
    "adventurous": [
        {
            "title": "India on Edge",
            "tagline": "Altitude, trails, and earned views at home",
            "hook": "Adventure doesn't require Europe — it requires intent.",
            "destinations": [
                ("Ladakh (Leh + Nubra)", "India", "High passes and vast sky for true trail energy.", "Jun–Sep", 9),
                ("Meghalaya (living root bridges)", "India", "Caves, rain forests, and trek days with local guides.", "Oct–Apr", 7),
            ],
            "vibes": ["altitude", "trek", "wild", "local"],
            "cluster": ("Desi Wild", "Challenge close to home", "#C4704A", "#3D5A5B"),
        },
        {
            "title": "Near Abroad Thrill",
            "tagline": "Short hop, big landscape",
            "hook": "If you want a stamp, keep it regional and intense.",
            "destinations": [
                ("Nepal (Annapurna / Pokhara)", "Nepal", "Trail days without a 20-hour flight.", "Mar–May or Oct–Nov", 8),
                ("Bhutan (Paro + Thimphu)", "Bhutan", "Himalayan calm with measured adventure.", "Mar–May or Sep–Nov", 6),
            ],
            "vibes": ["himalaya", "regional", "trail", "visa-light"],
            "cluster": ("Neighbour Peaks", "Adventure next door", "#E07A5F", "#81B29A"),
        },
    ],
    "romantic": [
        {
            "title": "Together in India",
            "tagline": "Shared evenings, short travel",
            "hook": "Romance thrives on time together — not jet lag.",
            "destinations": [
                ("Udaipur", "India", "Lake views and palace evenings without peak chaos if timed right.", "Oct–Mar", 4),
                ("Pondicherry + Auroville", "India", "Promenade walks, cafés, and soft coastal light.", "Nov–Feb", 4),
            ],
            "vibes": ["intimate", "lake", "coast", "together"],
            "cluster": ("Near Spark", "Date-night destinations", "#C4704A", "#F4E4C1"),
        },
        {
            "title": "Quiet Couple Escapes",
            "tagline": "Charm without the circus",
            "hook": "Choose places that feel discovered, not staged for crowds.",
            "destinations": [
                ("Andaman (Havelock quieter stays)", "India", "Clear water and shared slow mornings.", "Nov–Apr", 6),
                ("Gokarna", "India", "Beach stillness without Goa’s party volume.", "Nov–Feb", 4),
            ],
            "vibes": ["beach", "quiet", "sand", "sunset"],
            "cluster": ("Soft Shore", "Romance at walking pace", "#2E86AB", "#E8D5B7"),
        },
    ],
    "curious": [
        {
            "title": "Culture at Home",
            "tagline": "Depth without departure boards",
            "hook": "Curiosity wants layers — India has more than a lifetime.",
            "destinations": [
                ("Jaipur + nearby craft towns", "India", "Markets, forts, and artisan workshops.", "Oct–Mar", 5),
                ("Varanasi (gentle pacing)", "India", "Living heritage — approach with respect and soft mornings.", "Oct–Mar", 4),
            ],
            "vibes": ["heritage", "food", "craft", "ritual"],
            "cluster": ("Living India", "Learn with your feet", "#2E86AB", "#D4A574"),
        },
        {
            "title": "Food & Form",
            "tagline": "Cities that teach through taste",
            "hook": "You learn best when the street is the classroom.",
            "destinations": [
                ("Hyderabad", "India", "Biryani trails, Charminar lanes, layered history.", "Oct–Feb", 4),
                ("Kolkata", "India", "Adda culture, literature, and neighbourhood walks.", "Oct–Mar", 4),
            ],
            "vibes": ["food", "urban", "story", "local"],
            "cluster": ("City Layers", "Curiosity rewarded", "#E8A87C", "#87A878"),
        },
    ],
    "excited": [
        {
            "title": "India High Energy",
            "tagline": "Festivals, nights, and big moments",
            "hook": "Excitement wants buzz — you don’t need Tokyo for that.",
            "destinations": [
                ("Goa (North evenings / South days)", "India", "Music, beach, and food with flexible nights.", "Nov–Feb", 5),
                ("Mumbai", "India", "City pulse, street food, and neighbourhood hops.", "Nov–Feb", 4),
            ],
            "vibes": ["nightlife", "buzz", "food", "coast"],
            "cluster": ("Bright Pulse IN", "Cities that keep up", "#E07A5F", "#F2CC8F"),
        },
        {
            "title": "Festive & Flow",
            "tagline": "Moments you’ll actually remember",
            "hook": "Pick seasons for colour and celebration.",
            "destinations": [
                ("Rajasthan desert circuit", "India", "Camps, stars, and dramatic evenings.", "Oct–Feb", 6),
                ("Kochi + Fort area", "India", "Harbour energy, art, and spice history.", "Oct–Mar", 4),
            ],
            "vibes": ["festive", "colour", "music", "story"],
            "cluster": ("Story Fuel IN", "Memories over monuments", "#81B29A", "#E07A5F"),
        },
    ],
    "burnt-out": [
        {
            "title": "India Reset",
            "tagline": "Low stimulation, short travel",
            "hook": "You need rest, not a 14-hour flight.",
            "destinations": [
                ("Rishikesh (quieter banks)", "India", "River sound and soft yoga mornings — skip party hostels.", "Sep–Mar", 5),
                ("Waynad", "India", "Forest stays and zero FOMO itineraries.", "Oct–Mar", 4),
            ],
            "vibes": ["restorative", "forest", "river", "gentle"],
            "cluster": ("Nervous System Home", "Heal before you hustle", "#2D5A4A", "#F4E4C1"),
        },
        {
            "title": "Wellness Near",
            "tagline": "The destination is the treatment",
            "hook": "Choose recovery over sightseeing.",
            "destinations": [
                ("Kerala Ayurveda stays", "India", "Structured rest with local wellness tradition.", "Sep–Mar", 7),
                ("Bir Billing (gentle)", "India", "Mountain air and café pace — keep days light.", "Mar–Jun or Sep–Nov", 5),
            ],
            "vibes": ["wellness", "soft", "retreat", "air"],
            "cluster": ("Gentle Days IN", "Do less, feel more", "#87A878", "#E8D5B7"),
        },
    ],
    "nostalgic": [
        {
            "title": "Memory Landscapes IN",
            "tagline": "Places that feel like old stories",
            "hook": "Nostalgia wants texture — trains, old towns, handwritten pace.",
            "destinations": [
                ("Shimla + Kalka toy train", "India", "Colonial lanes and slow rail nostalgia.", "Mar–Jun or Sep–Nov", 5),
                ("Mysore", "India", "Palace evenings and soft South Indian rhythm.", "Oct–Feb", 4),
            ],
            "vibes": ["heritage", "train", "palace", "soft"],
            "cluster": ("Yesterday’s Light IN", "Memory-forward travel", "#B8A9C9", "#E8D5B7"),
        },
        {
            "title": "Heritage Trails IN",
            "tagline": "The past, walking-distance",
            "hook": "Meaning layered into streets and meals.",
            "destinations": [
                ("Hampi", "India", "Ruins at golden hour — cinematic without a flight abroad.", "Oct–Feb", 4),
                ("Madurai + temple towns", "India", "Living devotion and dense cultural texture.", "Oct–Mar", 4),
            ],
            "vibes": ["ruins", "temple", "history", "photo"],
            "cluster": ("Keepsake India", "Bring home a feeling", "#C4704A", "#F5E6D3"),
        },
    ],
    "restless": [
        {
            "title": "Motion Therapy IN",
            "tagline": "New ground without jet lag",
            "hook": "Restlessness wants change of scenery — India is large enough.",
            "destinations": [
                ("Manali to Spiti road (seasonal)", "India", "Road days that empty the mind.", "Jun–Sep", 8),
                ("Andaman island hopping", "India", "Boats, beaches, and fresh rhythm.", "Nov–Apr", 7),
            ],
            "vibes": ["road", "island", "change", "drive"],
            "cluster": ("New Ground IN", "Shake the snowglobe", "#E8A87C", "#2E86AB"),
        },
        {
            "title": "Open Road Energy IN",
            "tagline": "Itineraries with breathing room",
            "hook": "You need options, not a rigid tour bus.",
            "destinations": [
                ("Leh day trips circuit", "India", "Passes and viewpoints on your own clock.", "Jun–Sep", 7),
                ("Konkan coast road", "India", "Beaches and food stops between quiet towns.", "Nov–Feb", 6),
            ],
            "vibes": ["road", "coast", "space", "flexible"],
            "cluster": ("Wide Open IN", "Distance clears the head", "#3D5A5B", "#E8D5B7"),
        },
    ],
    "happy": [
        {
            "title": "Celebrate Out Loud IN",
            "tagline": "Joy deserves colour nearby",
            "hook": "Happiness wants music, food, and shared tables.",
            "destinations": [
                ("Jaipur festive season", "India", "Colour, crafts, and lively evenings.", "Oct–Feb", 4),
                ("Goa South beaches", "India", "Sun, shared meals, easy laughs.", "Nov–Feb", 5),
            ],
            "vibes": ["festive", "sunny", "social", "food"],
            "cluster": ("Bright Tables IN", "Joy in public", "#E07A5F", "#F2CC8F"),
        },
        {
            "title": "Playful Escapes IN",
            "tagline": "Light itineraries, big smiles",
            "hook": "Keep it playful — not precious.",
            "destinations": [
                ("Lonavala / Khandala (long weekend)", "India", "Quick getaway energy from western metros.", "Jul–Sep or Nov–Feb", 3),
                ("McLeod Ganj", "India", "Cafés, views, and easy social vibe.", "Mar–Jun or Sep–Nov", 4),
            ],
            "vibes": ["playful", "weekend", "café", "easy"],
            "cluster": ("Easy Joy IN", "Happy without trying", "#81B29A", "#E8C99A"),
        },
    ],
    "sad": [
        {
            "title": "Gentle Holding Places IN",
            "tagline": "Soft landscapes for heavy days",
            "hook": "When you’re low, choose places that hold you — not hype you.",
            "destinations": [
                ("Darjeeling (quieter stays)", "India", "Mist, tea, and kind hospitality.", "Mar–May or Sep–Nov", 5),
                ("Alleppey / Kumarakom", "India", "Water and slow boats without pressure.", "Sep–Mar", 5),
            ],
            "vibes": ["gentle", "mist", "water", "healing"],
            "cluster": ("Soft Ground IN", "Healing at walking pace", "#2D5A4A", "#B8A9C9"),
        },
        {
            "title": "Warmth & Kindness IN",
            "tagline": "Sun and soft company",
            "hook": "Warmth outside can help warmth return inside.",
            "destinations": [
                ("Gokarna quieter beaches", "India", "Sea without megacity noise.", "Nov–Feb", 5),
                ("Ooty", "India", "Cool air and garden-town gentleness.", "Sep–May", 4),
            ],
            "vibes": ["warm", "kind", "sea", "slow"],
            "cluster": ("Held by Place IN", "Let the land care for you", "#E8A87C", "#87A878"),
        },
    ],
    "frustrated": [
        {
            "title": "Release Valves IN",
            "tagline": "Burn energy, not bridges",
            "hook": "Frustration needs movement and distance from triggers.",
            "destinations": [
                ("Triund trek (Dharamshala)", "India", "Day hike that empties the mind.", "Mar–Jun or Sep–Nov", 3),
                ("Ziro Valley", "India", "Open space and soft village pace.", "Mar–May or Sep–Oct", 5),
            ],
            "vibes": ["release", "trek", "nature", "clear"],
            "cluster": ("Burn It Off IN", "Move until it softens", "#E07A5F", "#3D5A5B"),
        },
        {
            "title": "Clean Slate Cities IN",
            "tagline": "New rhythm, short hop",
            "hook": "A different city can interrupt a stuck loop.",
            "destinations": [
                ("Ahmedabad heritage walk + Sabarmati", "India", "Orderly days and strong food culture.", "Oct–Feb", 3),
                ("Chandigarh + Sukhna", "India", "Planned city calm and lake evenings.", "Oct–Mar", 3),
            ],
            "vibes": ["fresh", "urban", "walkable", "reset"],
            "cluster": ("System Reset IN", "Friction out, flow in", "#2E86AB", "#E8D5B7"),
        },
    ],
    "anxious": [
        {
            "title": "Safe Soft Landings IN",
            "tagline": "Familiar language, simpler logistics",
            "hook": "Anxiety eases when travel feels known and kind.",
            "destinations": [
                ("Bengaluru weekend nature (Nandi / nearby)", "India", "Short escape with familiar systems.", "Year-round (pick dry weeks)", 2),
                ("Jaipur with a trusted stay", "India", "Guided days and clear hotel anchors.", "Oct–Mar", 4),
            ],
            "vibes": ["safe", "familiar", "clear", "kind"],
            "cluster": ("Steady Ground IN", "Low-anxiety logistics", "#81B29A", "#E8C99A"),
        },
        {
            "title": "Nature Buffer IN",
            "tagline": "Fewer crowds, more oxygen",
            "hook": "Open space reduces noise — literally and mentally.",
            "destinations": [
                ("Jim Corbett (gentle zone)", "India", "Forest buffer and structured safaris.", "Nov–Jun", 4),
                ("Coorg estate stays", "India", "Private green and soft schedules.", "Oct–Mar", 4),
            ],
            "vibes": ["space", "forest", "quiet", "grounded"],
            "cluster": ("Wide Calm IN", "Anxiety loses volume outdoors", "#2D5A4A", "#F4E4C1"),
        },
    ],
}

INDIA_HINTS = (
    "india",
    "bharat",
    "delhi",
    "new delhi",
    "mumbai",
    "bengaluru",
    "bangalore",
    "hyderabad",
    "chennai",
    "kolkata",
    "pune",
    "ahmedabad",
    "jaipur",
    "kochi",
    "gurgaon",
    "gurugram",
    "noida",
    "inr",
)


def _prefer_india(request: TravelRequest) -> bool:
    """Domestic-first when currency or home base points to India."""
    if (request.currency or "").upper() == "INR":
        return True
    home = (request.profile.home_base if request.profile else None) or ""
    interests = (request.preferences.interests if request.preferences else None) or ""
    visa = (request.policy.visa_constraints if request.policy else None) or ""
    traveler = (request.profile.traveler_type if request.profile else None) or ""
    blob = " ".join([home, traveler, interests, visa, request.intent or ""]).lower()
    return any(h in blob for h in INDIA_HINTS)


COST_BANDS = {
    "budget": {"USD": (800, 1400), "EUR": (750, 1300), "GBP": (650, 1100), "INR": (65000, 120000), "AED": (3000, 5200), "JPY": (120000, 210000), "AUD": (1200, 2100)},
    "moderate": {"USD": (1500, 2500), "EUR": (1400, 2300), "GBP": (1200, 2000), "INR": (120000, 210000), "AED": (5500, 9200), "JPY": (220000, 380000), "AUD": (2200, 3800)},
    "luxury": {"USD": (3500, 6000), "EUR": (3200, 5500), "GBP": (2800, 4800), "INR": (280000, 500000), "AED": (13000, 22000), "JPY": (520000, 900000), "AUD": (5200, 9000)},
    "flexible": {"USD": (1200, 3200), "EUR": (1100, 3000), "GBP": (950, 2600), "INR": (100000, 280000), "AED": (4500, 12000), "JPY": (180000, 480000), "AUD": (1800, 4800)},
}

CURRENCY_SYMBOL = {
    "USD": "$",
    "EUR": "€",
    "GBP": "£",
    "INR": "₹",
    "AED": "AED ",
    "JPY": "¥",
    "AUD": "A$",
}

PERSONALITIES = {
    "peaceful": ("The Restorer", "Chooses calm over spectacle"),
    "adventurous": ("The Trailblazer", "Grows through challenge"),
    "romantic": ("The Connector", "Travel is shared meaning"),
    "curious": ("The Seeker", "Learns through places"),
    "excited": ("The Spark", "Chases energy and novelty"),
    "burnt-out": ("The Recoverer", "Protects energy first"),
    "nostalgic": ("The Storykeeper", "Looks for timeless texture"),
    "restless": ("The Mover", "Needs new ground"),
    "happy": ("The Celebrant", "Amplifies joy"),
    "sad": ("The Gentle Wanderer", "Needs soft landscapes"),
    "frustrated": ("The Releaser", "Moves to clear the mind"),
    "anxious": ("The Steady Planner", "Needs predictable comfort"),
}


def _fmt_cost(currency: str, budget: str, days: int, scale: float = 1.0) -> str:
    bands = COST_BANDS.get(budget, COST_BANDS["moderate"])
    lo, hi = bands.get(currency, bands["USD"])
    # Scale roughly by days vs 7-day baseline; optional domestic discount
    day_scale = max(days, 4) / 7
    lo_i, hi_i = int(lo * day_scale * scale), int(hi * day_scale * scale)
    sym = CURRENCY_SYMBOL.get(currency, f"{currency} ")
    if currency in {"INR", "JPY"}:
        return f"{sym}{lo_i:,}–{sym}{hi_i:,} for {days} days ({budget})"
    return f"{sym}{lo_i:,}–{sym}{hi_i:,} for {days} days ({budget})"


def build_mock_response(request: TravelRequest) -> TravelResponse:
    mood = (request.mood or DEFAULT_MOOD).lower().strip()
    india_first = _prefer_india(request)
    source = INDIA_MOOD_DESTINATIONS if india_first else MOOD_DESTINATIONS
    catalog = source.get(mood) or MOOD_DESTINATIONS.get(mood, MOOD_DESTINATIONS[DEFAULT_MOOD])
    # Domestic packs use ~55% of international cost bands (shorter hops, local pricing)
    cost_scale = 0.55 if india_first else 1.0
    currency = request.currency
    budget = request.budget
    style = request.travel_style
    personality, decision = PERSONALITIES.get(mood, PERSONALITIES[DEFAULT_MOOD])
    home = (request.profile.home_base if request.profile else None) or ("India" if india_first else "global")

    concepts = []
    all_dest_names: list[str] = []
    clusters = []

    for block in catalog:
        dests = []
        for i, (name, country, why, season, days) in enumerate(block["destinations"]):
            score = 96 - i * 5
            dests.append(
                {
                    "name": name,
                    "country": country,
                    "match_score": score,
                    "why_it_fits": why,
                    "estimated_cost": _fmt_cost(currency, budget, days, scale=cost_scale),
                    "suggested_duration": f"{max(days - 1, 2)}–{days + 2} days",
                    "best_time_to_visit": season,
                }
            )
            all_dest_names.append(name)

        concepts.append(
            {
                "title": block["title"],
                "tagline": block["tagline"],
                "emotional_hook": f"{block['hook']} (style: {style})",
                "destinations": dests,
                "vibe_keywords": block["vibes"],
                "sample_itinerary": [
                    f"Day 1–2: Arrive, settle, local walk — match your {mood} energy",
                    "Day 3–4: Signature nature or culture day without rushing",
                    "Day 5+: Deeper immersion — food, people, unplanned time",
                ],
                "budget_breakdown": "40% stay · 25% food · 20% transport · 15% experiences",
                "personality_fit": f"Tuned for {style} travelers in a {mood} emotional state.",
            }
        )

        cname, theme, c1, c2 = block["cluster"]
        clusters.append(
            {
                "cluster_name": cname,
                "theme": theme,
                "mood_alignment": f"Aligned to {mood}",
                "destinations": [d[0] for d in block["destinations"]],
                "visual_mood": theme,
                "color_palette": [c1, c2, "#F5E6D3", "#1A1F2E"],
                "suggested_activities": [
                    f"Morning ritual that supports feeling {mood}",
                    "Local meal with no agenda",
                    "Golden-hour walk or viewpoint",
                ],
            }
        )

    intent_bit = (request.intent or "this trip")[:80]
    scope = "India domestic / nearby" if india_first else "global"
    data = {
        "emotional_profile": {
            "primary_emotion": mood,
            "travel_personality": personality,
            "decision_style": decision,
            "priority_factors": [
                f"mood:{mood}",
                f"currency:{currency}",
                f"budget:{budget}",
                f"style:{style}",
                f"scope:{scope}",
                f"home:{home}",
            ],
        },
        "travel_concepts": concepts,
        "inspiration_board": {
            "board_title": f"Your {mood.title()} Map",
            "subtitle": f"Curated for: {intent_bit}",
            "emotional_summary": (
                f"Because you're feeling {mood}, we prioritized {scope} destinations that match that need "
                f"in {currency} — anchored to home base ({home})."
            ),
            "clusters": clusters,
            "quote": "Different feelings deserve different maps — often closer than you think.",
        },
        "agent_reasoning": (
            f"Demo engine used the '{mood}' pack with scope={scope} "
            f"(INR or India home base → domestic-first; otherwise global). "
            f"Costs in {currency} for budget '{budget}'. "
            "Set PROVIDER=gemini + GEMINI_API_KEY for live LLM variety."
        ),
        "context_summary": (
            f"Mood={mood} · Scope={scope} · Home={home} · Currency={currency} · "
            f"Budget={budget} · Style={style} · Demo=mood-aware mock"
        ),
    }
    return TravelResponse.model_validate(data)
