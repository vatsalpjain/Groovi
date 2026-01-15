"""
Spotify MCP Client - Full OAuth + Playback + Playlist Support

Two authentication modes:
1. Client Credentials (sp) - For public endpoints: search, recommendations, track info
2. User OAuth (user_sp) - For user-specific: playback control, playlist creation
"""

import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth

from config.settings import settings

logger = logging.getLogger(__name__)

# OAuth scopes required for full playback and playlist control
# Web Playback SDK requires: streaming, user-read-email, user-read-private
OAUTH_SCOPES = [
    "streaming",                    # Web Playback SDK - REQUIRED
    "user-read-email",              # Web Playback SDK - REQUIRED
    "user-read-private",            # Web Playback SDK - REQUIRED
    "user-modify-playback-state",   # Play, pause, skip, shuffle, repeat
    "user-read-playback-state",     # Get current playback
    "user-read-currently-playing",  # Current track info
    "playlist-modify-public",       # Create public playlists
    "playlist-modify-private",      # Create private playlists
    "user-library-read",            # Check if song is liked
    "user-library-modify",          # Like/unlike songs
]


class SpotifyAPI:
    """Spotify REST API wrapper using Spotipy"""
    def __init__(self):
        """Initialize both Spotify clients"""
        # Client Credentials - for public endpoints (always available)
        try:
            auth_manager = SpotifyClientCredentials(
                client_id=settings.spotipy_client_id,
                client_secret=settings.spotipy_client_secret
            )
            self.sp = spotipy.Spotify(auth_manager=auth_manager)
            logger.info("✅ Spotify Client Credentials initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Spotify: {e}")
            raise
        
        # User OAuth - for playback/playlists (optional, requires login)
        self.user_sp: Optional[spotipy.Spotify] = None
        self.oauth: Optional[SpotifyOAuth] = None
        self._init_oauth()
        self._try_restore_user_session()

    def _init_oauth(self):
        """Initialize OAuth manager"""
        self.oauth = SpotifyOAuth(
            client_id=settings.spotipy_client_id,
            client_secret=settings.spotipy_client_secret,
            redirect_uri=settings.spotipy_redirect_uri,
            scope=" ".join(OAUTH_SCOPES),
            open_browser=False  # We handle the redirect ourselves
        )

    def _try_restore_user_session(self):
        """Try to restore user session from saved refresh token"""
        if settings.spotify_refresh_token:
            try:
                self._refresh_token = settings.spotify_refresh_token  # Store in memory
                token_info = self.oauth.refresh_access_token(settings.spotify_refresh_token)
                self.user_sp = spotipy.Spotify(auth=token_info['access_token'])
                logger.info("✅ Restored Spotify user session from refresh token")
            except Exception as e:
                logger.warning(f"⚠️ Could not restore user session: {e}")
                self.user_sp = None
                self._refresh_token = None

    def get_access_token(self) -> Optional[str]:
        """Get current access token for Web Playback SDK"""
        # Use in-memory token first, fall back to settings
        refresh_token = getattr(self, '_refresh_token', None) or settings.spotify_refresh_token
        
        if not refresh_token:
            logger.warning("⚠️ No refresh token available")
            return None
        
        try:
            token_info = self.oauth.refresh_access_token(refresh_token)
            return token_info['access_token']
        except Exception as e:
            logger.error(f"❌ Failed to get access token: {e}")
            return None

    def is_user_authenticated(self) -> bool:
        """Check if user is authenticated"""
        return self.user_sp is not None

    # ==================== Search & Recommendations ====================
    
    def search_tracks(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for tracks on Spotify"""
        try:
            results = self.sp.search(q=query, type='track', limit=limit)
            return [self._format_track(item) for item in results['tracks']['items']]
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []

    def get_recommendations(
        self,
        seed_genres: Optional[List[str]] = None,
        seed_tracks: Optional[List[str]] = None,
        seed_artists: Optional[List[str]] = None,
        limit: int = 5,
        **audio_features
    ) -> List[Dict[str, Any]]:
        """Get song recommendations based on seeds and audio features"""
        try:
            params = {'limit': limit}
            
            if seed_genres:
                params['seed_genres'] = seed_genres[:5]
            if seed_tracks:
                params['seed_tracks'] = seed_tracks[:5]
            if seed_artists:
                params['seed_artists'] = seed_artists[:5]
            
            # Add audio features (target_valence, target_energy, etc.)
            params.update(audio_features)
            
            results = self.sp.recommendations(**params)
            return [self._format_track(item) for item in results['tracks']]
        except Exception as e:
            logger.error(f"Recommendations error: {e}")
            return []

    def get_track_audio_features(self, track_id: str) -> Optional[Dict[str, Any]]:
        """Get audio features for a track"""
        try:
            return self.sp.audio_features([track_id])[0]
        except Exception as e:
            logger.error(f"Audio features error: {e}")
            return None

    def get_available_genre_seeds(self) -> List[str]:
        """Get list of available genre seeds"""
        try:
            return self.sp.recommendation_genre_seeds()['genres']
        except Exception as e:
            logger.error(f"Genre seeds error: {e}")
            return []

    def get_track_by_id(self, track_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed track information"""
        try:
            track = self.sp.track(track_id)
            return self._format_track(track)
        except Exception as e:
            logger.error(f"Get track error: {e}")
            return None

    # ==================== Agent Tools ====================
    
    def search_artist(self, name: str) -> Optional[Dict[str, Any]]:
        """Find an artist by name"""
        try:
            results = self.sp.search(q=name, type='artist', limit=1)
            artists = results['artists']['items']
            if artists:
                artist = artists[0]
                return {
                    'id': artist['id'],
                    'name': artist['name'],
                    'genres': artist.get('genres', []),
                    'popularity': artist.get('popularity', 0),
                    'followers': artist['followers']['total'] if artist.get('followers') else 0,
                    'image': artist['images'][0]['url'] if artist.get('images') else None
                }
            return None
        except Exception as e:
            logger.error(f"Search artist error: {e}")
            return None

    def get_artist_top_tracks(self, artist_id: str, country: str = 'US') -> List[Dict[str, Any]]:
        """Get top tracks of an artist"""
        try:
            results = self.sp.artist_top_tracks(artist_id, country=country)
            return [self._format_track(track) for track in results['tracks']]
        except Exception as e:
            logger.error(f"Artist top tracks error: {e}")
            return []

    def get_related_artists(self, artist_id: str) -> List[Dict[str, Any]]:
        """Find artists similar to the given artist"""
        try:
            results = self.sp.artist_related_artists(artist_id)
            return [{
                'id': artist['id'],
                'name': artist['name'],
                'genres': artist.get('genres', []),
                'popularity': artist.get('popularity', 0)
            } for artist in results['artists'][:10]]  # Limit to top 10
        except Exception as e:
            logger.error(f"Related artists error: {e}")
            return []

    def search_playlists(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for playlists by query"""
        try:
            results = self.sp.search(q=query, type='playlist', limit=limit)
            return [{
                'id': playlist['id'],
                'name': playlist['name'],
                'description': playlist.get('description', ''),
                'owner': playlist['owner']['display_name'],
                'tracks_total': playlist['tracks']['total'],
                'image': playlist['images'][0]['url'] if playlist.get('images') else None
            } for playlist in results['playlists']['items'] if playlist]
        except Exception as e:
            logger.error(f"Search playlists error: {e}")
            return []

    def get_playlist_tracks(self, playlist_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get tracks from a playlist"""
        try:
            results = self.sp.playlist_tracks(playlist_id, limit=limit)
            tracks = []
            for item in results['items']:
                if item['track']:  # Some playlist items can be null
                    tracks.append(self._format_track(item['track']))
            return tracks
        except Exception as e:
            logger.error(f"Get playlist tracks error: {e}")
            return []

    def search_by_genre(self, genre: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search tracks by genre"""
        try:
            # Spotify search supports genre: filter
            results = self.sp.search(q=f'genre:"{genre}"', type='track', limit=limit)
            return [self._format_track(item) for item in results['tracks']['items']]
        except Exception as e:
            logger.error(f"Search by genre error: {e}")
            return []

    def get_new_releases(self, country: str = 'US', limit: int = 10) -> List[Dict[str, Any]]:
        """Get new album releases"""
        try:
            results = self.sp.new_releases(country=country, limit=limit)
            albums = []
            for album in results['albums']['items']:
                albums.append({
                    'id': album['id'],
                    'name': album['name'],
                    'artist': album['artists'][0]['name'] if album['artists'] else 'Unknown',
                    'release_date': album.get('release_date', ''),
                    'total_tracks': album.get('total_tracks', 0),
                    'image': album['images'][0]['url'] if album.get('images') else None
                })
            return albums
        except Exception as e:
            logger.error(f"Get new releases error: {e}")
            return []

    # ==================== Playback Control ====================
    
    def start_playback(
        self, 
        uris: Optional[List[str]] = None, 
        device_id: Optional[str] = None
    ) -> bool:
        """Start playback with optional track URIs"""
        if not self.user_sp:
            logger.error("❌ User not authenticated for playback")
            return False
        
        try:
            self.user_sp.start_playback(device_id=device_id, uris=uris)
            logger.info(f"▶️ Started playback with {len(uris) if uris else 0} tracks")
            return True
        except Exception as e:
            logger.error(f"Playback error: {e}")
            return False

    def pause_playback(self, device_id: Optional[str] = None) -> bool:
        """Pause playback"""
        if not self.user_sp:
            return False
        
        try:
            self.user_sp.pause_playback(device_id=device_id)
            logger.info("⏸️ Playback paused")
            return True
        except Exception as e:
            logger.error(f"Pause error: {e}")
            return False

    def next_track(self, device_id: Optional[str] = None) -> bool:
        """Skip to next track"""
        if not self.user_sp:
            return False
        
        try:
            self.user_sp.next_track(device_id=device_id)
            logger.info("⏭️ Skipped to next track")
            return True
        except Exception as e:
            logger.error(f"Next track error: {e}")
            return False

    def previous_track(self, device_id: Optional[str] = None) -> bool:
        """Go to previous track"""
        if not self.user_sp:
            return False
        
        try:
            self.user_sp.previous_track(device_id=device_id)
            logger.info("⏮️ Went to previous track")
            return True
        except Exception as e:
            logger.error(f"Previous track error: {e}")
            return False

    def seek_to_position(self, position_ms: int, device_id: Optional[str] = None) -> bool:
        """Seek to position in current track"""
        if not self.user_sp:
            return False
        
        try:
            self.user_sp.seek_track(position_ms, device_id=device_id)
            return True
        except Exception as e:
            logger.error(f"Seek error: {e}")
            return False

    def set_volume(self, volume_percent: int, device_id: Optional[str] = None) -> bool:
        """Set playback volume (0-100)"""
        if not self.user_sp:
            return False
        
        try:
            self.user_sp.volume(volume_percent, device_id=device_id)
            return True
        except Exception as e:
            logger.error(f"Volume error: {e}")
            return False

    def get_playback_state(self) -> Optional[Dict[str, Any]]:
        """Get current playback state"""
        if not self.user_sp:
            return None
        
        try:
            return self.user_sp.current_playback()
        except Exception as e:
            logger.error(f"Playback state error: {e}")
            return None

    def get_available_devices(self) -> List[Dict[str, Any]]:
        """Get list of available playback devices"""
        if not self.user_sp:
            return []
        
        try:
            return self.user_sp.devices()['devices']
        except Exception as e:
            logger.error(f"Devices error: {e}")
            return []

    # ==================== Playlist Management ====================
    
    def create_playlist(
        self, 
        name: str, 
        description: str = "", 
        public: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Create a new playlist in user's account"""
        if not self.user_sp:
            logger.error("❌ User not authenticated for playlist creation")
            return None
        
        try:
            user_id = self.user_sp.current_user()['id']
            playlist = self.user_sp.user_playlist_create(
                user_id, 
                name, 
                public=public, 
                description=description
            )
            logger.info(f"📋 Created playlist: {name}")
            return {
                'id': playlist['id'],
                'name': playlist['name'],
                'external_url': playlist['external_urls']['spotify'],
                'uri': playlist['uri']
            }
        except Exception as e:
            logger.error(f"Playlist creation error: {e}")
            return None

    def add_tracks_to_playlist(
        self, 
        playlist_id: str, 
        track_uris: List[str]
    ) -> bool:
        """Add tracks to a playlist"""
        if not self.user_sp:
            return False
        
        try:
            self.user_sp.playlist_add_items(playlist_id, track_uris)
            logger.info(f"➕ Added {len(track_uris)} tracks to playlist")
            return True
        except Exception as e:
            logger.error(f"Add tracks error: {e}")
            return False

    # ==================== Helper Methods ====================
    
    def _format_track(self, track: Dict[str, Any]) -> Dict[str, Any]:
        """Format track data for API response"""
        return {
            'id': track['id'],
            'name': track['name'],
            'artist': ', '.join([artist['name'] for artist in track['artists']]),
            'album': track['album']['name'],
            'uri': track['uri'],
            'external_url': track['external_urls']['spotify'],
            'album_art': track['album']['images'][0]['url'] if track['album']['images'] else None,
            'preview_url': track.get('preview_url'),
            'duration_ms': track.get('duration_ms'),
            'popularity': track.get('popularity')
        }


# Singleton instance
spotify_api = SpotifyAPI()