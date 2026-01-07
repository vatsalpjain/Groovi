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


class SpotifyMCPClient:
    """
    Spotify client with dual authentication:
    - Client Credentials for public API (search, recommendations)
    - User OAuth for playback and playlist management
    """
    
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

    # ==================== OAuth Methods ====================
    
    def get_auth_url(self) -> str:
        """Get Spotify OAuth authorization URL for user login"""
        return self.oauth.get_authorize_url()

    def exchange_code(self, code: str) -> Dict[str, Any]:
        """
        Exchange authorization code for access tokens.
        Saves refresh token to .env for persistence.
        """
        try:
            token_info = self.oauth.get_access_token(code, as_dict=True)
            
            # Store refresh token in memory AND save to .env
            self._refresh_token = token_info['refresh_token']
            self._save_refresh_token(token_info['refresh_token'])
            
            # Create authenticated user client
            self.user_sp = spotipy.Spotify(auth=token_info['access_token'])
            
            logger.info("✅ Spotify user authenticated successfully")
            return {
                "success": True,
                "expires_in": token_info.get('expires_in', 3600)
            }
        except Exception as e:
            logger.error(f"❌ OAuth token exchange failed: {e}")
            raise

    def _save_refresh_token(self, refresh_token: str):
        """Save refresh token to .env file for persistence"""
        # Save to spotify_mcp/.env (parent of this file's directory)
        env_path = Path(__file__).parent / ".env"
        
        # Read existing .env content
        env_content = ""
        if env_path.exists():
            env_content = env_path.read_text()
        
        # Update or add SPOTIFY_REFRESH_TOKEN
        lines = env_content.strip().split('\n') if env_content.strip() else []
        updated = False
        
        for i, line in enumerate(lines):
            if line.startswith('SPOTIFY_REFRESH_TOKEN='):
                lines[i] = f'SPOTIFY_REFRESH_TOKEN={refresh_token}'
                updated = True
                break
        
        if not updated:
            lines.append(f'SPOTIFY_REFRESH_TOKEN={refresh_token}')
        
        # Write back
        env_path.write_text('\n'.join(lines) + '\n')
        logger.info("✅ Refresh token saved to .env")

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
spotify_client = SpotifyMCPClient()