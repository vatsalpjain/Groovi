"""VADER-based mood analysis with fallback song recommendations - Complete standalone file"""

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import random


# ==================== FALLBACK SONG LIBRARY ====================

FALLBACK_SONGS = {
    "happy": [
        {"name": "Happy", "artist": "Pharrell Williams", "search_terms": ["happy", "celebration"]},
        {"name": "Can't Stop the Feeling!", "artist": "Justin Timberlake", "search_terms": ["feel good", "dance"]},
        {"name": "Good as Hell", "artist": "Lizzo", "search_terms": ["confidence", "empowerment"]},
        {"name": "Uptown Funk", "artist": "Mark Ronson ft. Bruno Mars", "search_terms": ["funk", "party"]},
        {"name": "Walking on Sunshine", "artist": "Katrina and the Waves", "search_terms": ["sunshine", "energy"]},
        {"name": "I Gotta Feeling", "artist": "The Black Eyed Peas", "search_terms": ["party", "celebration"]},
        {"name": "Don't Worry Be Happy", "artist": "Bobby McFerrin", "search_terms": ["happy", "carefree"]},
        {"name": "Best Day of My Life", "artist": "American Authors", "search_terms": ["best day", "joy"]},
        {"name": "Good Vibrations", "artist": "The Beach Boys", "search_terms": ["classic", "positive"]},
        {"name": "Dancing Queen", "artist": "ABBA", "search_terms": ["disco", "joy"]},
    ],
    
    "energetic": [
        {"name": "Good 4 U", "artist": "Olivia Rodrigo", "search_terms": ["pop", "upbeat"]},
        {"name": "Levitating", "artist": "Dua Lipa", "search_terms": ["dance", "feel good"]},
        {"name": "Blinding Lights", "artist": "The Weeknd", "search_terms": ["synthwave", "energy"]},
        {"name": "Don't Stop Me Now", "artist": "Queen", "search_terms": ["rock", "unstoppable"]},
        {"name": "High Hopes", "artist": "Panic! At The Disco", "search_terms": ["optimistic", "hope"]},
        {"name": "Thunderstruck", "artist": "AC/DC", "search_terms": ["rock", "electric", "power"]},
        {"name": "Eye of the Tiger", "artist": "Survivor", "search_terms": ["motivation", "workout"]},
        {"name": "Pump It", "artist": "The Black Eyed Peas", "search_terms": ["energetic", "pump up"]},
        {"name": "Can't Hold Us", "artist": "Macklemore & Ryan Lewis", "search_terms": ["hip hop", "energy"]},
        {"name": "Stronger", "artist": "Kanye West", "search_terms": ["hip hop", "power"]},
    ],
    
    "calm": [
        {"name": "Weightless", "artist": "Marconi Union", "search_terms": ["ambient", "calm"]},
        {"name": "Holocene", "artist": "Bon Iver", "search_terms": ["indie", "introspective"]},
        {"name": "Clair de Lune", "artist": "Claude Debussy", "search_terms": ["classical", "peaceful"]},
        {"name": "Breathe Me", "artist": "Sia", "search_terms": ["emotional", "reflective"]},
        {"name": "Skinny Love", "artist": "Bon Iver", "search_terms": ["indie", "acoustic"]},
        {"name": "Vienna", "artist": "Billy Joel", "search_terms": ["piano", "reflective"]},
        {"name": "Sunset Lover", "artist": "Petit Biscuit", "search_terms": ["chill", "electronic"]},
        {"name": "River Flows in You", "artist": "Yiruma", "search_terms": ["piano", "peaceful"]},
        {"name": "Strawberry Swing", "artist": "Coldplay", "search_terms": ["calm", "indie"]},
        {"name": "To Build a Home", "artist": "The Cinematic Orchestra", "search_terms": ["emotional", "peaceful"]},
    ],
    
    "neutral": [
        {"name": "Sunflower", "artist": "Post Malone, Swae Lee", "search_terms": ["chill", "positive"]},
        {"name": "The Night We Met", "artist": "Lord Huron", "search_terms": ["indie", "nostalgic"]},
        {"name": "Good Vibes", "artist": "Chris Brown", "search_terms": ["good vibes", "chill"]},
        {"name": "Count on Me", "artist": "Bruno Mars", "search_terms": ["friendship", "positive"]},
        {"name": "Budapest", "artist": "George Ezra", "search_terms": ["indie", "folk"]},
        {"name": "Riptide", "artist": "Vance Joy", "search_terms": ["indie", "acoustic"]},
        {"name": "Home", "artist": "Phillip Phillips", "search_terms": ["folk", "uplifting"]},
        {"name": "Better Together", "artist": "Jack Johnson", "search_terms": ["acoustic", "chill"]},
        {"name": "Ho Hey", "artist": "The Lumineers", "search_terms": ["folk", "indie"]},
        {"name": "Little Talks", "artist": "Of Monsters and Men", "search_terms": ["indie", "folk"]},
    ],
    
    "sad": [
        {"name": "Someone Like You", "artist": "Adele", "search_terms": ["heartbreak", "emotional"]},
        {"name": "Fix You", "artist": "Coldplay", "search_terms": ["healing", "support"]},
        {"name": "The Sound of Silence", "artist": "Disturbed", "search_terms": ["introspective", "powerful"]},
        {"name": "Everybody Hurts", "artist": "R.E.M.", "search_terms": ["support", "comfort"]},
        {"name": "Mad World", "artist": "Gary Jules", "search_terms": ["melancholy", "sad"]},
        {"name": "Tears Don't Fall", "artist": "Bullet for My Valentine", "search_terms": ["emotional", "rock"]},
        {"name": "In the End", "artist": "Linkin Park", "search_terms": ["struggle", "rock"]},
        {"name": "Heavy", "artist": "Linkin Park ft. Kiiara", "search_terms": ["burden", "support"]},
        {"name": "Skinny Love", "artist": "Birdy", "search_terms": ["sad", "cover"]},
        {"name": "When I Was Your Man", "artist": "Bruno Mars", "search_terms": ["regret", "ballad"]},
    ],
    
    "anxious": [
        {"name": "Breathe", "artist": "Telepopmusik", "search_terms": ["calm", "soothing"]},
        {"name": "Weightless", "artist": "Marconi Union", "search_terms": ["anxiety relief", "calm"]},
        {"name": "Let It Be", "artist": "The Beatles", "search_terms": ["comfort", "peace"]},
        {"name": "Three Little Birds", "artist": "Bob Marley", "search_terms": ["reassurance", "calm"]},
        {"name": "Unwritten", "artist": "Natasha Bedingfield", "search_terms": ["hope", "empowerment"]},
        {"name": "Float On", "artist": "Modest Mouse", "search_terms": ["optimistic", "indie"]},
        {"name": "Here Comes the Sun", "artist": "The Beatles", "search_terms": ["hopeful", "uplifting"]},
        {"name": "Don't Panic", "artist": "Coldplay", "search_terms": ["calm", "reassurance"]},
        {"name": "Better Days", "artist": "OneRepublic", "search_terms": ["hope", "uplifting"]},
        {"name": "I'll Be OK", "artist": "Nothing But Thieves", "search_terms": ["reassurance", "rock"]},
    ],
    
    "angry": [
        {"name": "Break Stuff", "artist": "Limp Bizkit", "search_terms": ["anger", "nu metal"]},
        {"name": "Killing in the Name", "artist": "Rage Against the Machine", "search_terms": ["rage", "rock"]},
        {"name": "Numb", "artist": "Linkin Park", "search_terms": ["frustration", "rock"]},
        {"name": "Last Resort", "artist": "Papa Roach", "search_terms": ["anger", "rock"]},
        {"name": "Bodies", "artist": "Drowning Pool", "search_terms": ["aggressive", "metal"]},
        {"name": "Chop Suey!", "artist": "System of a Down", "search_terms": ["intense", "metal"]},
        {"name": "Down with the Sickness", "artist": "Disturbed", "search_terms": ["anger", "metal"]},
        {"name": "Given Up", "artist": "Linkin Park", "search_terms": ["frustration", "intense"]},
        {"name": "Freak on a Leash", "artist": "Korn", "search_terms": ["nu metal", "anger"]},
        {"name": "Wait and Bleed", "artist": "Slipknot", "search_terms": ["metal", "intense"]},
    ],
    
    "romantic": [
        {"name": "Perfect", "artist": "Ed Sheeran", "search_terms": ["love", "romantic"]},
        {"name": "Thinking Out Loud", "artist": "Ed Sheeran", "search_terms": ["romantic", "ballad"]},
        {"name": "All of Me", "artist": "John Legend", "search_terms": ["love", "piano"]},
        {"name": "Make You Feel My Love", "artist": "Adele", "search_terms": ["romantic", "love"]},
        {"name": "A Thousand Years", "artist": "Christina Perri", "search_terms": ["romantic", "love"]},
        {"name": "Can't Help Falling in Love", "artist": "Elvis Presley", "search_terms": ["classic", "love"]},
        {"name": "At Last", "artist": "Etta James", "search_terms": ["romantic", "soul"]},
        {"name": "Wonderful Tonight", "artist": "Eric Clapton", "search_terms": ["romantic", "classic"]},
        {"name": "Unchained Melody", "artist": "The Righteous Brothers", "search_terms": ["classic", "romantic"]},
        {"name": "Your Song", "artist": "Elton John", "search_terms": ["classic", "love"]},
    ]
}


# ==================== VADER ANALYZER ====================

class VaderFallback:
    """Simple VADER mood analysis returning 10 curated songs"""
    
    def __init__(self):
        self.vader = SentimentIntensityAnalyzer()
    
    def _score_to_category(self, score: float) -> str:
        """Map VADER compound score to mood category"""
        if score >= 0.5:
            return "happy"
        elif score >= 0.3:
            return "energetic"
        elif score >= 0.1:
            return "calm"
        elif score >= -0.1:
            return "neutral"
        elif score >= -0.3:
            return "anxious"
        elif score >= -0.5:
            return "sad"
        else:
            return "angry"
    
    def get_songs(self, text: str) -> list:
        """
        Analyze text mood and return 10 fallback songs.
        
        Args:
            text: User's mood text
            
        Returns:
            List of 10 song dictionaries with name, artist, search_terms
        """
        # Analyze sentiment with VADER
        sentiment = self.vader.polarity_scores(text)
        score = sentiment['compound']
        
        # Get mood category
        category = self._score_to_category(score)
        
        # Get songs for this category
        songs = FALLBACK_SONGS.get(category, FALLBACK_SONGS["neutral"])
        
        # Return 10 songs (each category now has exactly 10)
        return songs


# ==================== PUBLIC API ====================

# Singleton instance
vader_fallback = VaderFallback()


def get_fallback_songs(text: str) -> list:
    """
    Simple function: text in, 10 songs out.
    
    Args:
        text: User's mood text
        
    Returns:
        List of 10 song dictionaries
    """
    return vader_fallback.get_songs(text)
