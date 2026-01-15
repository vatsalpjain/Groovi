"""
Spotify OAuth Service

Handles Spotify user authentication flow:
1. Generate OAuth authorization URL
2. Exchange authorization code for tokens
3. Save refresh token to MCP server's .env
4. Token refresh management
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional

import spotipy
from spotipy.oauth2 import SpotifyOAuth

from config.settings import settings

logger = logging.getLogger(__name__)

# OAuth scopes required for playback and playlist control
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

# Path to MCP server's .env file (where refresh token is stored)
MCP_ENV_PATH = Path(__file__).parent.parent.parent / "spotify_mcp" / ".env"


class SpotifyAuthService:
    """Manages Spotify OAuth authentication flow"""
    
    def __init__(self):
        """Initialize OAuth manager"""
        self._oauth: Optional[SpotifyOAuth] = None
        self._user_sp: Optional[spotipy.Spotify] = None
        self._refresh_token: Optional[str] = None
        self._init_oauth()
    
    def _init_oauth(self):
        """Initialize SpotifyOAuth manager"""
        try:
            self._oauth = SpotifyOAuth(
                client_id=settings.SPOTIPY_CLIENT_ID,
                client_secret=settings.SPOTIPY_CLIENT_SECRET,
                redirect_uri="http://127.0.0.1:5000/callback",  # Exact match with Spotify Dashboard
                scope=" ".join(OAUTH_SCOPES),
                open_browser=False  # We handle the redirect ourselves
            )
            logger.info("✅ Spotify OAuth initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Spotify OAuth: {e}")
            raise
    
    def get_auth_url(self) -> str:
        """
        Get Spotify OAuth authorization URL.
        
        Returns:
            URL to redirect user to for Spotify login
        """
        return self._oauth.get_authorize_url()
    
    def exchange_code(self, code: str) -> Dict[str, Any]:
        """
        Exchange authorization code for access and refresh tokens.
        
        Args:
            code: Authorization code from Spotify callback
            
        Returns:
            Dict with success status and expiry info
        """
        try:
            token_info = self._oauth.get_access_token(code, as_dict=True)
            
            # Store refresh token
            self._refresh_token = token_info['refresh_token']
            
            # Save to MCP server's .env for persistence
            self._save_refresh_token(token_info['refresh_token'])
            
            # Create authenticated user client
            self._user_sp = spotipy.Spotify(auth=token_info['access_token'])
            
            logger.info("✅ Spotify user authenticated successfully")
            return {
                "success": True,
                "expires_in": token_info.get('expires_in', 3600)
            }
        except Exception as e:
            logger.error(f"❌ OAuth token exchange failed: {e}")
            raise
    
    def _save_refresh_token(self, refresh_token: str):
        """
        Save refresh token to MCP server's .env file.
        
        This allows the MCP server to authenticate with Spotify
        even after the backend restarts.
        """
        try:
            # Read existing .env content
            env_content = ""
            if MCP_ENV_PATH.exists():
                env_content = MCP_ENV_PATH.read_text()
            
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
            MCP_ENV_PATH.write_text('\n'.join(lines) + '\n')
            logger.info(f"✅ Refresh token saved to {MCP_ENV_PATH}")
            
        except Exception as e:
            logger.error(f"❌ Failed to save refresh token: {e}")
            # Don't raise - token save failure shouldn't break auth flow
    
    def get_access_token(self) -> Optional[str]:
        """
        Get current access token (refreshes if needed).
        
        Used by Web Playback SDK on frontend.
        
        Returns:
            Access token string or None if not authenticated
        """
        if not self._refresh_token:
            # Try to load from MCP env file
            self._load_refresh_token()
        
        if not self._refresh_token:
            logger.warning("⚠️ No refresh token available")
            return None
        
        try:
            token_info = self._oauth.refresh_access_token(self._refresh_token)
            return token_info['access_token']
        except Exception as e:
            logger.error(f"❌ Failed to get access token: {e}")
            return None
    
    def _load_refresh_token(self):
        """Load refresh token from MCP server's .env file"""
        try:
            if MCP_ENV_PATH.exists():
                content = MCP_ENV_PATH.read_text()
                for line in content.split('\n'):
                    if line.startswith('SPOTIFY_REFRESH_TOKEN='):
                        self._refresh_token = line.split('=', 1)[1].strip()
                        logger.info("✅ Loaded refresh token from MCP .env")
                        return
        except Exception as e:
            logger.error(f"❌ Failed to load refresh token: {e}")
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated with Spotify"""
        if self._user_sp is not None:
            return True
        
        # Try to restore session
        if not self._refresh_token:
            self._load_refresh_token()
        
        if self._refresh_token:
            try:
                token_info = self._oauth.refresh_access_token(self._refresh_token)
                self._user_sp = spotipy.Spotify(auth=token_info['access_token'])
                return True
            except Exception:
                return False
        
        return False
    
    def get_user_info(self) -> Optional[Dict[str, Any]]:
        """Get current user's Spotify profile info"""
        if not self.is_authenticated():
            return None
        
        try:
            user = self._user_sp.current_user()
            return {
                "id": user['id'],
                "display_name": user.get('display_name', user['id']),
                "email": user.get('email'),
                "image": user['images'][0]['url'] if user.get('images') else None
            }
        except Exception as e:
            logger.error(f"❌ Failed to get user info: {e}")
            return None


# Singleton instance
spotify_auth = SpotifyAuthService()
