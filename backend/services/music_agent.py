"""
Music Recommendation AI Agent

Uses Groq LLM with function calling to explore Spotify's catalog
and curate personalized song recommendations.

The agent can:
1. Search for artists, playlists, and tracks
2. Explore related artists and top tracks
3. Browse by genre and new releases
4. Iterate to refine results
5. Curate final playlist with reasoning
"""

import json
import logging
from typing import Dict, Any
import httpx

logger = logging.getLogger(__name__)

# MCP Server URL for Spotify tools
MCP_URL = "http://localhost:5000"

# Maximum iterations for agent loop
MAX_ITERATIONS = 5

# Tool definitions for Groq function calling
AGENT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_artist",
            "description": "Find an artist by name. Use this when user mentions a specific artist.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Artist name to search for"}
                },
                "required": ["name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_artist_top_tracks",
            "description": "Get the top/popular tracks of an artist. Use after finding an artist.",
            "parameters": {
                "type": "object",
                "properties": {
                    "artist_id": {"type": "string", "description": "Spotify artist ID"}
                },
                "required": ["artist_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_related_artists",
            "description": "Find artists similar to a given artist. Great for discovery.",
            "parameters": {
                "type": "object",
                "properties": {
                    "artist_id": {"type": "string", "description": "Spotify artist ID"}
                },
                "required": ["artist_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_tracks",
            "description": "Search for tracks by keywords. Use for mood/activity-based queries.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query (mood, activity, genre, etc.)"},
                    "limit": {"type": "integer", "description": "Number of results (default 10)", "default": 10}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_playlists",
            "description": "Search for curated playlists by theme/mood/activity.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Playlist search query"},
                    "limit": {"type": "integer", "description": "Number of results (default 5)", "default": 5}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_playlist_tracks",
            "description": "Get tracks from a specific playlist.",
            "parameters": {
                "type": "object",
                "properties": {
                    "playlist_id": {"type": "string", "description": "Spotify playlist ID"},
                    "limit": {"type": "integer", "description": "Number of tracks (default 20)", "default": 20}
                },
                "required": ["playlist_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_by_genre",
            "description": "Search tracks by genre. Use when user asks for a specific genre.",
            "parameters": {
                "type": "object",
                "properties": {
                    "genre": {"type": "string", "description": "Genre name (e.g., rock, jazz, hip-hop)"},
                    "limit": {"type": "integer", "description": "Number of results (default 10)", "default": 10}
                },
                "required": ["genre"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_genres",
            "description": "Get list of all available Spotify genres. Use to discover valid genre names.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_new_releases",
            "description": "Get recently released albums. Use when user wants fresh/new music.",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "Number of albums (default 10)", "default": 10}
                }
            }
        }
    }
]

# System prompt for the agent
SYSTEM_PROMPT = """You are a music recommendation AI with access to Spotify's catalog.

Your job is to find the PERFECT songs based on what the user describes.

## AVAILABLE TOOLS:
- search_artist: Find an artist by name
- get_artist_top_tracks: Get top tracks of an artist  
- get_related_artists: Find similar artists
- search_tracks: Search tracks by keywords
- search_playlists: Find themed playlists
- get_playlist_tracks: Get tracks from a playlist
- search_by_genre: Search by genre
- get_genres: List all available genres
- get_new_releases: Get new album releases

## STRATEGY:
1. If user mentions an ARTIST → search_artist → get their top tracks
2. If user mentions a MOOD/ACTIVITY → search_playlists + search_tracks with relevant keywords
3. If user mentions a GENRE → search_by_genre or search_tracks with genre keywords
4. If user wants NEW music → get_new_releases
5. **If user mentions a DECADE/ERA (80s, 90s, 2000s, etc.):**
   - Search for iconic artists FROM THAT ERA (e.g., "90s hip hop" → search for Tupac, Notorious B.I.G., Dr. Dre)
   - Include the decade in playlist search (e.g., "90s hip hop classics")
   - Verify tracks are actually from that era!

## EXAMPLES:
- "Hindi Love Songs" -> search_artist("Arijit Singh"), search_artist("Shreya Ghoshal"), search_playlists("Hindi love songs")
- "80s rock" → search_artist("Guns N Roses"), search_artist("Bon Jovi"), search_playlists("80s rock hits")
- "2000s pop" → search_artist("Britney Spears"), search_artist("NSYNC"), search_playlists("2000s pop hits")

## RULES:
- Make 2-4 tool calls to gather enough options
- Pick the 5 BEST tracks that ACTUALLY match the user's request
- For decade requests, ensure songs are from that decade!
- Each track must have a reason for why it fits
- Return ONLY valid Spotify track URIs

## FINAL RESPONSE FORMAT (JSON):
When you have enough tracks, respond with this JSON:
{
    "tracks": [
        {"name": "...", "artist": "...", "uri": "spotify:track:...", "reason": "Why this fits"},
        ... (exactly 5 tracks)
    ],
    "mood": "detected mood/vibe",
    "summary": "Brief explanation of your curation"
}

Think step by step. Explain your reasoning before each tool call."""


class MusicRecommendationAgent:
    """AI Agent that uses Groq + MCP tools to recommend music"""
    
    def __init__(self, groq_client):
        """
        Initialize the agent with a Groq client.
        
        Args:
            groq_client: Initialized Groq client with API key
        """
        self.groq = groq_client
        self.http_client = httpx.AsyncClient(timeout=30.0)
        
    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool by calling the MCP server.
        
        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments
            
        Returns:
            Tool result from MCP server
        """
        # Map tool names to endpoints
        endpoint_map = {
            "search_artist": "/tools/search_artist",
            "get_artist_top_tracks": "/tools/artist_top_tracks",
            "get_related_artists": "/tools/related_artists",
            "search_tracks": "/tools/search_tracks",
            "search_playlists": "/tools/search_playlists",
            "get_playlist_tracks": "/tools/playlist_tracks",
            "search_by_genre": "/tools/search_by_genre",
            "get_genres": "/tools/genres",
            "get_new_releases": "/tools/new_releases"
        }
        
        endpoint = endpoint_map.get(tool_name)
        if not endpoint:
            return {"error": f"Unknown tool: {tool_name}"}
        
        try:
            url = f"{MCP_URL}{endpoint}"
            response = await self.http_client.get(url, params=arguments)
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"API error: {response.status_code}", "detail": response.text}
                
        except Exception as e:
            logger.error(f"Tool execution error: {e}")
            return {"error": str(e)}
    
    async def run(self, user_query: str) -> Dict[str, Any]:
        """
        Run the agent loop to get music recommendations.
        
        Args:
            user_query: User's music request (e.g., "something like Arctic Monkeys")
            
        Returns:
            Dict with tracks, mood, summary, and thought_process
        """
        # Track agent's thought process for UI display
        thought_process = []
        
        # Collect all tracks found during search
        all_tracks = []
        
        # Initialize messages with system prompt and user query
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_query}
        ]
        
        logger.info(f"🎵 Agent starting for query: {user_query}")
        
        for iteration in range(MAX_ITERATIONS):
            logger.info(f"🔄 Agent iteration {iteration + 1}/{MAX_ITERATIONS}")
            
            # On last iteration, force final answer by not passing tools
            is_last_iteration = iteration >= MAX_ITERATIONS - 1
            
            try:
                # Call Groq with tools (or without on last iteration)
                if is_last_iteration and all_tracks:
                    # Force final answer by asking to pick from gathered tracks
                    messages.append({
                        "role": "user",
                        "content": f"""You MUST now provide your final recommendation. 
                        
Pick the 5 BEST tracks from what you've found and return ONLY this JSON:
{{
    "tracks": [
        {{"name": "...", "artist": "...", "uri": "spotify:track:...", "reason": "Why this fits"}},
        ... (exactly 5 tracks)
    ],
    "mood": "detected mood/vibe",
    "summary": "Brief explanation of your curation"
}}

Here are some tracks you found: {json.dumps(all_tracks[:20])}"""
                    })
                    
                    response = self.groq.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=messages,
                        temperature=0.7,
                        max_tokens=2000
                    )
                else:
                    response = self.groq.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=messages,
                        tools=AGENT_TOOLS,
                        tool_choice="auto",
                        temperature=0.7,
                        max_tokens=2000
                    )
                
                message = response.choices[0].message
                
                # Check if agent wants to call tools
                if message.tool_calls and not is_last_iteration:
                    # Record the assistant message with tool calls
                    messages.append({
                        "role": "assistant",
                        "content": message.content or "",
                        "tool_calls": [
                            {
                                "id": tc.id,
                                "type": "function",
                                "function": {
                                    "name": tc.function.name,
                                    "arguments": tc.function.arguments
                                }
                            }
                            for tc in message.tool_calls
                        ]
                    })
                    
                    # Execute each tool call
                    for tool_call in message.tool_calls:
                        tool_name = tool_call.function.name
                        try:
                            arguments = json.loads(tool_call.function.arguments)
                        except json.JSONDecodeError:
                            arguments = {}
                        
                        logger.info(f"🔧 Tool: {tool_name}({arguments})")
                        
                        # Record thought for UI
                        thought_process.append({
                            "iteration": iteration + 1,
                            "thought": message.content or f"Calling {tool_name}",
                            "tool": tool_name,
                            "arguments": arguments
                        })
                        
                        # Execute the tool
                        result = await self.execute_tool(tool_name, arguments)
                        
                        # Collect tracks from results
                        if "tracks" in result:
                            all_tracks.extend(result["tracks"])
                        
                        # Add tool result to messages
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": json.dumps(result)
                        })
                        
                        logger.info(f"📦 Tool result: {len(str(result))} chars")
                
                else:
                    # Agent returned final response (no more tool calls)
                    final_content = message.content or ""
                    
                    logger.info("✅ Agent finished, parsing final response")
                    
                    # Try to parse JSON from response
                    try:
                        # Find JSON in the response
                        json_start = final_content.find('{')
                        json_end = final_content.rfind('}') + 1
                        
                        if json_start >= 0 and json_end > json_start:
                            json_str = final_content[json_start:json_end]
                            result = json.loads(json_str)
                            
                            # Enrich tracks with album_art from collected data
                            if "tracks" in result and all_tracks:
                                result["tracks"] = self._enrich_tracks_with_metadata(
                                    result["tracks"], all_tracks
                                )
                            
                            # Add thought process to result
                            result["thought_process"] = thought_process
                            result["iterations"] = iteration + 1
                            
                            return result
                        else:
                            # No JSON found, build response from gathered tracks
                            if all_tracks:
                                return self._build_fallback_response(all_tracks, thought_process, iteration + 1)
                            
                            return {
                                "error": "Could not parse agent response",
                                "raw_response": final_content,
                                "thought_process": thought_process
                            }
                            
                    except json.JSONDecodeError as e:
                        logger.error(f"JSON parse error: {e}")
                        # Try to build response from gathered tracks
                        if all_tracks:
                            return self._build_fallback_response(all_tracks, thought_process, iteration + 1)
                        
                        return {
                            "error": "Invalid JSON in agent response",
                            "raw_response": final_content,
                            "thought_process": thought_process
                        }
                        
            except Exception as e:
                logger.error(f"Agent iteration error: {e}")
                thought_process.append({
                    "iteration": iteration + 1,
                    "error": str(e)
                })
        
        # Max iterations reached - build response from gathered tracks
        if all_tracks:
            return self._build_fallback_response(all_tracks, thought_process, MAX_ITERATIONS)
        
        return {
            "error": "Agent reached maximum iterations without completing",
            "thought_process": thought_process
        }
    
    def _build_fallback_response(self, tracks: list, thought_process: list, iterations: int) -> Dict[str, Any]:
        """Build a response from gathered tracks when agent fails to return JSON"""
        # Deduplicate by URI
        seen_uris = set()
        unique_tracks = []
        for track in tracks:
            uri = track.get("uri", "")
            if uri and uri not in seen_uris:
                seen_uris.add(uri)
                unique_tracks.append({
                    "name": track.get("name", "Unknown"),
                    "artist": track.get("artist", "Unknown"),
                    "uri": uri,
                    "album_art": track.get("album_art", ""),
                    "reason": "Found by AI agent exploration"
                })
        
        return {
            "tracks": unique_tracks[:5],
            "mood": "curated",
            "summary": "Curated from AI agent exploration",
            "thought_process": thought_process,
            "iterations": iterations
        }
    
    def _enrich_tracks_with_metadata(self, agent_tracks: list, collected_tracks: list) -> list:
        """
        Enrich tracks returned by LLM with metadata from collected raw data.
        LLM only returns name/artist/uri/reason - we need album_art from the raw API data.
        """
        # Build lookup dict by URI for fast matching
        track_lookup = {}
        for track in collected_tracks:
            uri = track.get("uri", "")
            if uri:
                track_lookup[uri] = track
        
        enriched = []
        for agent_track in agent_tracks:
            uri = agent_track.get("uri", "")
            
            # Try to find matching track in collected data
            raw_track = track_lookup.get(uri, {})
            
            enriched.append({
                "name": agent_track.get("name", raw_track.get("name", "Unknown")),
                "artist": agent_track.get("artist", raw_track.get("artist", "Unknown")),
                "uri": uri,
                "album_art": raw_track.get("album_art", ""),  # Get from raw data
                "external_url": raw_track.get("external_url", ""),  # Get from raw data
                "reason": agent_track.get("reason", "")
            })
        
        return enriched
    
    async def close(self):
        """Close HTTP client"""
        await self.http_client.aclose()

