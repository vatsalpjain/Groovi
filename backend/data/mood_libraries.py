"""Curated song libraries by mood - fallback recommendations"""

MOOD_SONG_LIBRARIES = {
    "Very Positive": [
        {"name": "Happy", "artist": "Pharrell Williams", "search_terms": ["happy", "celebration"]},
        {"name": "Can't Stop the Feeling!", "artist": "Justin Timberlake", "search_terms": ["feel good", "dance"]},
        {"name": "Good as Hell", "artist": "Lizzo", "search_terms": ["confidence", "empowerment"]},
        {"name": "Uptown Funk", "artist": "Mark Ronson ft. Bruno Mars", "search_terms": ["funk", "party"]},
        {"name": "Walking on Sunshine", "artist": "Katrina and the Waves", "search_terms": ["sunshine", "energy"]},
        {"name": "I Gotta Feeling", "artist": "The Black Eyed Peas", "search_terms": ["party", "celebration"]},
        {"name": "Don't Worry Be Happy", "artist": "Bobby McFerrin", "search_terms": ["happy", "carefree"]},
        {"name": "Best Day of My Life", "artist": "American Authors", "search_terms": ["best day", "joy"]},
    ],
    
    "Positive": [
        {"name": "Good 4 U", "artist": "Olivia Rodrigo", "search_terms": ["pop", "upbeat"]},
        {"name": "Levitating", "artist": "Dua Lipa", "search_terms": ["dance", "feel good"]},
        {"name": "Sunflower", "artist": "Post Malone, Swae Lee", "search_terms": ["chill", "positive"]},
        {"name": "Blinding Lights", "artist": "The Weeknd", "search_terms": ["synthwave", "energy"]},
        {"name": "Don't Stop Me Now", "artist": "Queen", "search_terms": ["rock", "unstoppable"]},
        {"name": "Good Vibes", "artist": "Chris Brown", "search_terms": ["good vibes", "chill"]},
        {"name": "High Hopes", "artist": "Panic! At The Disco", "search_terms": ["optimistic", "hope"]},
        {"name": "Count on Me", "artist": "Bruno Mars", "search_terms": ["friendship", "positive"]},
    ],
    
    "Neutral": [
        {"name": "Weightless", "artist": "Marconi Union", "search_terms": ["ambient", "calm"]},
        {"name": "Holocene", "artist": "Bon Iver", "search_terms": ["indie", "introspective"]},
        {"name": "Clair de Lune", "artist": "Claude Debussy", "search_terms": ["classical", "peaceful"]},
        {"name": "Breathe Me", "artist": "Sia", "search_terms": ["emotional", "reflective"]},
        {"name": "The Night We Met", "artist": "Lord Huron", "search_terms": ["indie", "nostalgic"]},
        {"name": "Skinny Love", "artist": "Bon Iver", "search_terms": ["indie", "acoustic"]},
        {"name": "Mad About You", "artist": "Sting", "search_terms": ["mellow", "romantic"]},
        {"name": "Vienna", "artist": "Billy Joel", "search_terms": ["piano", "reflective"]},
    ],
    
    "Negative": [
        {"name": "Someone Like You", "artist": "Adele", "search_terms": ["heartbreak", "emotional"]},
        {"name": "Fix You", "artist": "Coldplay", "search_terms": ["healing", "support"]},
        {"name": "The Sound of Silence", "artist": "Disturbed", "search_terms": ["introspective", "powerful"]},
        {"name": "Everybody Hurts", "artist": "R.E.M.", "search_terms": ["support", "comfort"]},
        {"name": "Mad World", "artist": "Gary Jules", "search_terms": ["melancholy", "sad"]},
        {"name": "Tears Don't Fall", "artist": "Bullet for My Valentine", "search_terms": ["emotional", "rock"]},
        {"name": "In the End", "artist": "Linkin Park", "search_terms": ["struggle", "rock"]},
        {"name": "Heavy", "artist": "Linkin Park ft. Kiiara", "search_terms": ["burden", "support"]},
    ],
    
    "Very Negative": [
        {"name": "Hurt", "artist": "Johnny Cash", "search_terms": ["pain", "regret"]},
        {"name": "Black", "artist": "Pearl Jam", "search_terms": ["grunge", "loss"]},
        {"name": "Tears in Heaven", "artist": "Eric Clapton", "search_terms": ["loss", "grief"]},
        {"name": "Creep", "artist": "Radiohead", "search_terms": ["alienation", "emotional"]},
        {"name": "Snuff", "artist": "Slipknot", "search_terms": ["loss", "metal"]},
        {"name": "One More Day", "artist": "Diamond Rio", "search_terms": ["loss", "country"]},
        {"name": "Whiskey Lullaby", "artist": "Brad Paisley ft. Alison Krauss", "search_terms": ["tragedy", "loss"]},
        {"name": "Gone Away", "artist": "The Offspring", "search_terms": ["grief", "punk rock"]},
    ]
}

def get_songs_for_mood(mood_category: str) -> list:
    """Get curated songs for a mood category"""
    return MOOD_SONG_LIBRARIES.get(mood_category, MOOD_SONG_LIBRARIES["Neutral"])