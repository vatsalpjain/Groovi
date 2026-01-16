"""
Voice Assistant - Main orchestrator for voice-to-voice pipeline

State machine:
- WAKE_WORD: Waiting for "Hey Groovi"
- LISTENING: VAD active, buffering audio
- PROCESSING: Running STT + agent
- SPEAKING: TTS playing response
"""

from typing import Literal, AsyncGenerator
import logging
import time

from groq import Groq
from config.settings import settings
from services.music_agent import MusicRecommendationAgent

from voice_ai.wake_word_service import WakeWordService
from voice_ai.streaming_STT import StreamingSTT
from voice_ai.streaming_TTS import StreamingTTS

logger = logging.getLogger(__name__)


class VoiceAssistant:
    """Orchestrates wake word → STT → Agent → TTS pipeline"""
    
    # System prompt defining Groovi's personality (short responses for voice)
    SYSTEM_PROMPT = """You are Groovi, a friendly AI music assistant. You help users find music based on their mood.

Guidelines:
- Be warm, casual, and music-savvy
- Keep responses SHORT (1-2 sentences max) - you're speaking, not writing
- If user wants music, ask about their mood, then tell them to say "play" + mood
- You can discuss music genres, artists, and moods briefly

Example responses:
- "Hey! What kind of vibe are you feeling today?"
- "That sounds chill! Say 'play something calm' and I'll find you some tracks."
- "Nice choice! I love that genre too."
"""
    
    # Idle timeout: go back to WAKE_WORD after this many seconds of silence
    IDLE_TIMEOUT_SEC = 5.0
    
    def __init__(self):
        """Initialize state and models"""
        # State machine
        self.state: Literal["WAKE_WORD", "LISTENING", "PROCESSING", "SPEAKING"] = "WAKE_WORD"
        
        # Audio buffer for collecting chunks during LISTENING
        self.audio_buffer: list[bytes] = []
        
        # Track last activity for idle timeout
        self.last_activity_time: float = 0.0
        
        # Conversation history for LLM context
        self.conversation_history: list[dict] = []
        
        # Initialize all services
        logger.info("🚀 Initializing VoiceAssistant...")
        
        # LLM for conversational responses
        self.llm = None
        self.music_agent = None
        if settings.GROQ_API_KEY:
            try:
                self.llm = Groq(api_key=settings.GROQ_API_KEY)
                self.music_agent = MusicRecommendationAgent(self.llm)
                logger.info("✅ Groq LLM + Music Agent initialized")
            except Exception as e:
                logger.warning(f"⚠️ Groq init failed: {e} - using canned responses")
        
        self.wake_word = WakeWordService()
        self.stt = StreamingSTT()
        self.tts = StreamingTTS()
        
        logger.info("✅ VoiceAssistant initialized in WAKE_WORD mode")
    
    def cleanup(self):
        """Clean up all models and free memory"""
        logger.info("🧹 Cleaning up VoiceAssistant...")
        
        # Stop TTS if speaking
        if hasattr(self, 'tts') and self.tts:
            self.tts.stop()
            del self.tts
        
        # Clear STT buffers
        if hasattr(self, 'stt') and self.stt:
            self.stt.clear_buffer()
            del self.stt
        
        # Reset wake word
        if hasattr(self, 'wake_word') and self.wake_word:
            self.wake_word.reset()
            del self.wake_word
        
        # Clear audio buffer
        self.audio_buffer = []
        
        logger.info("✅ VoiceAssistant cleaned up - RAM freed")
    
    async def process_audio(self, chunk: bytes) -> AsyncGenerator[dict, None]:
        """
        Process incoming audio chunk based on current state.
        
        Yields events:
        - {"event": "wake_word_detected"}
        - {"event": "listening"}
        - {"event": "transcript", "text": "..."}
        - {"event": "response", "text": "..."}
        - {"event": "audio", "data": bytes}
        """
        
        # ========== WAKE_WORD STATE ==========
        if self.state == "WAKE_WORD":
            if self.wake_word.detect(chunk):
                self.state = "LISTENING"
                self.audio_buffer = []
                self.stt.clear_buffer()
                self.last_activity_time = time.time()  # Start timer
                logger.info("🎤 Wake word detected → LISTENING")
                yield {"event": "wake_word_detected"}
                yield {"event": "listening"}
        
        # ========== LISTENING STATE ==========
        elif self.state == "LISTENING":
            # Check for idle timeout
            if time.time() - self.last_activity_time > self.IDLE_TIMEOUT_SEC:
                self.state = "WAKE_WORD"
                self.stt.clear_buffer()
                self.audio_buffer = []
                logger.info("⏰ Idle timeout → WAKE_WORD")
                yield {"event": "idle_timeout"}
                return
            
            # Buffer audio
            self.audio_buffer.append(chunk)
            self.stt.add_chunk(chunk)
            
            # Check if user stopped speaking
            if self.stt.speech_ended(chunk):
                self.state = "PROCESSING"
                self.last_activity_time = time.time()  # Reset timer
                logger.info("🎤 Speech ended → PROCESSING")
                
                # Transcribe buffered audio
                transcript = self.stt.transcribe()
                self.stt.clear_buffer()
                self.audio_buffer = []
                
                if not transcript:
                    # No speech detected, go back to wake word
                    self.state = "WAKE_WORD"
                    yield {"event": "error", "message": "No speech detected"}
                    return
                
                yield {"event": "transcript", "text": transcript}
                
                # Check for pause/stop command → Switch to click mode
                if self._is_pause_command(transcript):
                    self.state = "WAKE_WORD"
                    logger.info("⏸️ Pause command → returning to WAKE_WORD")
                    yield {"event": "voice_mode_stop", "message": "Switching to click mode"}
                    return
                
                # Check for "play" keyword → Music Agent
                if self._is_music_request(transcript):
                    yield {"event": "agent_started"}
                    
                    # Build context from conversation history
                    context = self._get_context_for_agent()
                    query = f"{context} | Current request: {transcript}" if context else transcript
                    
                    # Run music agent
                    if self.music_agent:
                        try:
                            logger.info(f"🎵 Running music agent: {query[:50]}...")
                            result = await self.music_agent.run(query)
                            logger.info(f"🎵 Agent result keys: {result.keys() if result else 'None'}")
                            
                            # Check for tracks (even if there's also an error)
                            tracks = result.get("tracks", [])
                            error = result.get("error")
                            
                            if tracks:
                                # Send songs to frontend
                                yield {"event": "songs", "songs": tracks}
                                
                                # Build TTS response with first 3 song names
                                song_names = [f"{t['name']} by {t['artist']}" for t in tracks[:3]]
                                response = f"Here are some songs for you: {', '.join(song_names)}."
                            elif error:
                                logger.warning(f"Music agent error: {error}")
                                response = "I had trouble searching Spotify. Try clicking the button instead!"
                            else:
                                response = "Sorry, I couldn't find songs for that. Try describing your mood differently."
                        except Exception as e:
                            logger.error(f"Music agent exception: {e}")
                            response = "Something went wrong while searching. Try the click mode!"
                    else:
                        response = "Music search isn't available right now. Try the click mode instead!"
                else:
                    # Conversational response via LLM
                    response = self._chat_with_llm(transcript)
                
                yield {"event": "response", "text": response}
                
                # Switch to speaking and stream TTS
                self.state = "SPEAKING"
                async for audio_chunk in self.tts.stream(response):
                    yield {"event": "audio", "data": audio_chunk}
                
                # After speaking, wait briefly then go back to LISTENING
                # (5 second conversational buffer)
                self.state = "LISTENING"
                self.stt.clear_buffer()
                yield {"event": "listening"}
        
        # ========== SPEAKING STATE ==========
        elif self.state == "SPEAKING":
            # Check for interrupt (user started speaking)
            if self.wake_word.detect(chunk):
                self.tts.stop()
                self.state = "LISTENING"
                self.stt.clear_buffer()
                logger.info("🛑 User interrupted → LISTENING")
                yield {"event": "interrupted"}
                yield {"event": "listening"}
    
    def _chat_with_llm(self, user_message: str) -> str:
        """
        Get response from Groq LLM with conversation context.
        Falls back to canned response if LLM unavailable.
        """
        # Add user message to history
        self.conversation_history.append({
            "role": "user", 
            "content": user_message
        })
        
        # Trim history to last 10 messages (5 turns)
        if len(self.conversation_history) > 10:
            self.conversation_history = self.conversation_history[-10:]
        
        # Try LLM if available
        if self.llm:
            try:
                # Build messages with system prompt
                messages = [
                    {"role": "system", "content": self.SYSTEM_PROMPT}
                ] + self.conversation_history
                
                response = self.llm.chat.completions.create(
                    messages=messages,
                    model="llama-3.1-8b-instant",  # Fast model for voice
                    max_tokens=100,  # Keep responses short
                    temperature=0.7
                )
                
                assistant_message = response.choices[0].message.content.strip()
                
                # Add to history
                self.conversation_history.append({
                    "role": "assistant",
                    "content": assistant_message
                })
                
                logger.info(f"💬 LLM response: {assistant_message[:50]}...")
                return assistant_message
                
            except Exception as e:
                logger.error(f"LLM error: {e}")
                # Fall through to canned response
        
        # Fallback: canned responses
        return self._get_canned_response(user_message)
    
    def _get_canned_response(self, transcript: str) -> str:
        """Fallback responses when LLM is unavailable"""
        text_lower = transcript.lower()
        
        if any(word in text_lower for word in ["hello", "hi", "hey"]):
            return "Hey! What kind of music are you in the mood for?"
        elif any(word in text_lower for word in ["thanks", "thank you"]):
            return "You're welcome! Let me know if you want more songs."
        elif any(word in text_lower for word in ["stop", "pause", "quiet"]):
            return "Okay, stopping."
        else:
            return "I'm Groovi! Say play followed by your mood for song recommendations."
    
    def _is_music_request(self, text: str) -> bool:
        """Check if user wants to play/find music"""
        keywords = ["play", "recommend", "suggest", "find me", "i want to hear", "put on", "music for"]
        text_lower = text.lower()
        return any(kw in text_lower for kw in keywords)
    
    def _get_context_for_agent(self) -> str:
        """Extract mood/context from conversation history for music agent"""
        if not self.conversation_history:
            return ""
        
        # Get user messages from last 3 turns
        user_messages = [
            msg["content"] 
            for msg in self.conversation_history[-6:] 
            if msg["role"] == "user"
        ]
        
        if not user_messages:
            return ""
        
        return " | ".join(user_messages[:-1]) if len(user_messages) > 1 else ""
    
    def _is_pause_command(self, text: str) -> bool:
        """Check if user wants to stop voice mode"""
        phrases = [
            "stop", "pause", "quit", "exit", 
            "stop voice", "switch to click", "click mode", "cancel"
        ]
        text_lower = text.lower()
        return any(phrase in text_lower for phrase in phrases)
