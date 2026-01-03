"""Spotify API client wrapper"""

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from config.settings import settings

class SpotifyClient:
    """Handles all Spotify API operations"""
    
    def __init__(self):
        self.client = spotipy.Spotify(
            client_credentials_manager=SpotifyClientCredentials(
                client_id=settings.SPOTIPY_CLIENT_ID,
                client_secret=settings.SPOTIPY_CLIENT_SECRET
            )
        )
        print("✅ Spotify client initialized")
    
    def search_track(self, query: str, limit: int = 1) -> list:
        """Search for tracks on Spotify"""
        try:
            results = self.client.search(q=query, type='track', limit=limit)
            return results['tracks']['items']
        except Exception as e:
            print(f"❌ Spotify search failed for '{query}': {e}")
            return []
    
    def format_track(self, track: dict) -> dict:
        """Format Spotify track data for API response"""
        return {
            'name': track['name'],
            'artist': track['artists'][0]['name'],
            'uri': track['uri'],
            'album_art': track['album']['images'][0]['url'] if track['album']['images'] else None,
            'external_url': track['external_urls']['spotify']
        }

spotify_client = SpotifyClient()