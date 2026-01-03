"""Test Spotify API connection"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.spotify_client import spotify_client


def test_connection():
    """Test basic Spotify API connection"""
    print("🎵 Testing Spotify API...")
    
    try:
        results = spotify_client.search_track("Happy Pharrell Williams", limit=1)
        
        if results:
            track = spotify_client.format_track(results[0])
            print(f"✅ Connected! Test: {track['name']} by {track['artist']}")
            return True
        else:
            print("⚠️ Connected but no results")
            return False
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False


if __name__ == "__main__":
    test_connection()
