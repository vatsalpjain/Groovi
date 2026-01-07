from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """MCP Server Settings"""
    
    # Spotify API - Client Credentials
    spotipy_client_id: str
    spotipy_client_secret: str
    spotipy_redirect_uri: str = "http://127.0.0.1:5000/callback"
    
    # Spotify OAuth - User Authentication (for playback/playlists)
    spotify_refresh_token: Optional[str] = None  # Stored after first OAuth login
    
    # Server settings
    server_name: str = "groovi-spotify-mcp"
    server_version: str = "1.0.0"
    http_port: int = 5000  # HTTP server port (must match Spotify redirect URI)
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()