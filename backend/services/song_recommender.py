"""Song recommendation using multiple strategies"""

import random
from services.spotify_client import spotify_client
from data.mood_libraries import MOOD_SONG_LIBRARIES

class SongRecommender:
    """Recommends songs based on mood using Spotify + curated libraries"""
    
    def get_from_groq_suggestions(self, groq_recs: list) -> list:
        """
        Strategy 1: Use Groq's AI song suggestions
        Search each suggestion on Spotify
        """
        if not groq_recs:
            return []
        
        tracks = []
        for song_info in groq_recs:
            query = f"{song_info.get('name', '')} {song_info.get('artist', '')}"
            results = spotify_client.search_track(query, limit=1)
            
            if results:
                tracks.append(spotify_client.format_track(results[0]))
            
            if len(tracks) >= 5:
                break
        
        print(f"✅ Got {len(tracks)} songs from Groq suggestions")
        return tracks
    
    def get_from_mood_library(self, mood_category: str) -> list:
        """
        Strategy 2: Use curated mood library
        Search library songs on Spotify, fill with mood-based search
        """
        mood_songs = MOOD_SONG_LIBRARIES.get(mood_category, [])
        selected_songs = random.sample(mood_songs, min(3, len(mood_songs)))
        
        tracks = []
        
        # Search for each selected song
        for song_info in selected_songs:
            query = f"{song_info['name']} {song_info['artist']}"
            results = spotify_client.search_track(query, limit=1)
            
            if results:
                tracks.append(spotify_client.format_track(results[0]))
        
        # Fill remaining slots with mood-based search
        if len(tracks) < 5 and selected_songs:
            search_terms = random.choice(selected_songs)['search_terms']
            search_term = random.choice(search_terms)
            results = spotify_client.search_track(search_term, limit=10)
            
            for track in results:
                if len(tracks) >= 5:
                    break
                formatted = spotify_client.format_track(track)
                # Avoid duplicates
                if not any(t['uri'] == formatted['uri'] for t in tracks):
                    tracks.append(formatted)
        
        print(f"✅ Got {len(tracks)} songs from mood library")
        return tracks[:5]
    
    def get_fallback_songs(self, mood_category: str) -> list:
        """
        Strategy 3: Use curated fallback (when Spotify fails)
        Returns curated songs without Spotify links
        """
        mood_songs = MOOD_SONG_LIBRARIES.get(mood_category, [])
        selected = random.sample(mood_songs, min(5, len(mood_songs)))
        
        print(f"✅ Using {len(selected)} curated fallback songs")
        return [{
            'name': song['name'],
            'artist': song['artist'],
            'uri': f'spotify:track:fallback_{mood_category}_{i}',
            'album_art': 'https://i.scdn.co/image/ab67616d0000b273c8b444df094279e70d0ed856',
            'external_url': f'https://open.spotify.com/search/{song["name"]} {song["artist"]}'
        } for i, song in enumerate(selected)]
    
    def recommend(self, mood_analysis: dict, groq_recs: list = None) -> list:
        """
        MAIN FUNCTION - Get 5 songs using multiple strategies
        
        Flow:
        1. Try Groq song recommendations → Spotify
        2. Try mood library → Spotify  
        3. Use curated fallback songs
        
        Always returns exactly 5 songs
        """
        # Strategy 1: Groq recommendations
        if groq_recs:
            print("🎵 Strategy 1: Trying Groq recommendations")
            tracks = self.get_from_groq_suggestions(groq_recs)
            if len(tracks) >= 3:
                return tracks[:5]
        
        # Strategy 2: Mood library with Spotify
        print("🎵 Strategy 2: Trying mood library + Spotify")
        tracks = self.get_from_mood_library(mood_analysis['mood_category'])
        if len(tracks) >= 3:
            return tracks[:5]
        
        # Strategy 3: Curated fallback
        print("🎵 Strategy 3: Using curated fallback")
        return self.get_fallback_songs(mood_analysis['mood_category'])

song_recommender = SongRecommender()