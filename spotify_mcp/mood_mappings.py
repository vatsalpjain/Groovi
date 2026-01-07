"""
Mood to Spotify Audio Features Mapping

Maps detected mood categories to Spotify's audio features for recommendations.
These values are passed to Spotify's /recommendations API.

Audio Features:
- valence: Musical positivity (0.0 = sad/angry, 1.0 = happy/cheerful)
- energy: Intensity and activity (0.0 = calm, 1.0 = energetic)
- danceability: How suitable for dancing (0.0 = least, 1.0 = most)
- seed_genres: Genre seeds to guide recommendations (must be from Spotify's valid list)

Valid genres can be fetched from: https://api.spotify.com/v1/recommendations/available-genre-seeds
"""

from typing import Dict, Any

# Mood category -> Spotify audio features mapping
# Using only valid Spotify genre seeds
MOOD_AUDIO_FEATURES: Dict[str, Dict[str, Any]] = {
    "happy": {
        "target_valence": 0.8,
        "target_energy": 0.7,
        "target_danceability": 0.7,
        "seed_genres": ["pop", "dance"]  # "happy" is not a valid genre
    },
    "energetic": {
        "target_valence": 0.7,
        "target_energy": 0.9,
        "target_danceability": 0.8,
        "seed_genres": ["electronic", "dance"]
    },
    "calm": {
        "target_valence": 0.5,
        "target_energy": 0.3,
        "target_danceability": 0.4,
        "seed_genres": ["chill", "acoustic"]
    },
    "sad": {
        "target_valence": 0.2,
        "target_energy": 0.3,
        "target_danceability": 0.3,
        "seed_genres": ["acoustic", "piano"]  # "sad" is not a valid genre
    },
    "angry": {
        "target_valence": 0.3,
        "target_energy": 0.9,
        "target_danceability": 0.5,
        "seed_genres": ["rock", "metal"]
    },
    "anxious": {
        "target_valence": 0.3,
        "target_energy": 0.6,
        "target_danceability": 0.4,
        "seed_genres": ["ambient", "chill"]
    },
    "romantic": {
        "target_valence": 0.7,
        "target_energy": 0.4,
        "target_danceability": 0.5,
        "seed_genres": ["r-n-b", "soul"]
    },
    "neutral": {
        "target_valence": 0.5,
        "target_energy": 0.5,
        "target_danceability": 0.5,
        "seed_genres": ["pop", "indie"]
    }
}


def get_audio_features_for_mood(mood: str) -> Dict[str, Any]:
    """
    Get Spotify audio features for a given mood category.
    
    Args:
        mood: Mood category (happy, sad, energetic, etc.)
    
    Returns:
        Dict with target_valence, target_energy, target_danceability, seed_genres
    """
    mood_lower = mood.lower()
    return MOOD_AUDIO_FEATURES.get(mood_lower, MOOD_AUDIO_FEATURES["neutral"])
