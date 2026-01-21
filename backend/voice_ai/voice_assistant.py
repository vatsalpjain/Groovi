"""
Voice Assistant - Main orchestrator for voice-to-voice pipeline

State machine:
- WAKE_WORD: Waiting for "Hey Groovi"
- LISTENING: VAD active, buffering audio
- PROCESSING: Running STT + agent
- SPEAKING: TTS playing response
"""

from typing import Literal, AsyncGenerator
import asyncio
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
    
    # Filler prompt for music search latency
    FILLER_SYSTEM_PROMPT = """You are Groovi, about to search for music.
Keep the user engaged with a SHORT response while searching (2 sentences, max 24 words).
Acknowledge their music request naturally.

Examples:
- "Perfect! Searching for calm tracks now."
- "Great choice! Finding some upbeat music."
- "Love it! Looking for those vibes."
"""
    
    # Idle timeout: go back to WAKE_WORD after this many seconds of silence
    IDLE_TIMEOUT_SEC = 5.0
    
    # Cooldown after TTS to prevent false wake word triggers from echo/noise
    WAKE_WORD_COOLDOWN_SEC = 1.0
    
    def __init__(self):
        """Initialize state and models"""
        # State machine
        self.state: Literal["WAKE_WORD", "LISTENING", "PROCESSING", "SPEAKING"] = "WAKE_WORD"
        
        # Audio buffer for collecting chunks during LISTENING
        self.audio_buffer: list[bytes] = []
        
        # Track last activity for idle timeout
        self.last_activity_time: float = 0.0
        
        # Cooldown timestamp - ignore wake word until this time
        self.wake_word_cooldown_until: float = 0.0
        
        # TTS playback tracking - True while frontend is playing TTS audio
        self.tts_playing: bool = False
        
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
    
    def _enter_wake_word_with_cooldown(self):
        """
        Switch to WAKE_WORD state with proper cleanup and cooldown.
        
        Clears all audio buffers and resets wake word model to prevent
        false triggers from residual TTS audio or noise.
        """
        self.state = "WAKE_WORD"
        self.audio_buffer = []
        self.stt.clear_buffer()
        self.wake_word.reset()  # Clear internal wake word model state
        # Set cooldown - ignore wake word detections for a brief period
        self.wake_word_cooldown_until = time.time() + self.WAKE_WORD_COOLDOWN_SEC
        logger.info(f"🔇 Wake word cooldown active for {self.WAKE_WORD_COOLDOWN_SEC}s")
    
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
            # Check cooldown - ignore detections right after TTS to prevent echo triggers
            if time.time() < self.wake_word_cooldown_until:
                return  # Still in cooldown, ignore this chunk
            
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
            if self.stt.vad.speech_ended(chunk):
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
                    # 1. Send response text to frontend
                    response = "Stopping voice mode. Goodbye!"
                    yield {"event": "response", "text": response}
                    
                    # 2. Switch to SPEAKING and stream TTS audio
                    self.state = "SPEAKING"
                    async for audio_chunk in self.tts.stream(response):
                        yield {"event": "audio", "data": audio_chunk}
                    
                    # 3. After TTS finishes, switch to WAKE_WORD with cooldown
                    self._enter_wake_word_with_cooldown()
                    logger.info("⏸️ Pause command → WAKE_WORD (with cooldown)")
                    yield {"event": "voice_mode_stop", "message": "Switching to click mode"}
                    return
                
                # Check for "play" keyword → Music Agent
                if self._is_music_request(transcript):
                    # Add user message to conversation history
                    self.conversation_history.append({
                        "role": "user",
                        "content": transcript
                    })
                    
                    yield {"event": "agent_started"}
                    
                    # Build context from conversation history (before current message)
                    context = self._get_context_for_agent()
                    query = f"{context} | Current request: {transcript}" if context else transcript
                    
                    # Generate filler response using LLM (contextual, engaging)
                    filler_response = self._generate_filler_response(transcript)
                    logger.info(f"🔊 Filler: {filler_response}")
                    
                    # Add filler to history
                    self.conversation_history.append({
                        "role": "assistant",
                        "content": filler_response
                    })
                    
                    yield {"event": "response", "text": filler_response}
                    
                    # Run music agent and filler TTS concurrently
                    if self.music_agent:
                        try:
                            # Start both tasks concurrently
                            logger.info(f"🎵 Starting music agent: {query[:50]}...")
                            
                            # Create async tasks
                            agent_task = asyncio.create_task(self.music_agent.run(query))
                            
                            # Switch to SPEAKING state while filler plays
                            self.state = "SPEAKING"
                            
                            # Stream filler TTS
                            tts_generator = self.tts.stream(filler_response)
                            
                            # Stream TTS while agent runs
                            async for audio_chunk in tts_generator:
                                # Check if agent finished
                                if agent_task.done():
                                    # Agent finished! Stop TTS
                                    self.tts.stop()
                                    logger.info("🛑 Agent finished, stopping filler TTS")
                                    break
                                yield {"event": "audio", "data": audio_chunk}
                            
                            # Wait for agent result
                            result = await agent_task
                            logger.info(f"🎵 Agent result keys: {result.keys() if result else 'None'}")
                            
                            # Check for tracks
                            tracks = result.get("tracks", [])
                            summary = result.get("summary", "")
                            error = result.get("error")
                            
                            if tracks:
                                # Success! Add music result to history
                                song_names = [f"{t['name']} by {t['artist']}" for t in tracks[:3]]
                                history_entry = f"{summary} Tracks: {', '.join(song_names)}"
                                self.conversation_history.append({
                                    "role": "assistant",
                                    "content": history_entry
                                })
                                # Send songs to frontend (summary for display, not TTS)
                                yield {
                                    "event": "songs",
                                    "summary": summary,
                                    "songs": tracks
                                }
                                
                                # Switch to WAKE_WORD with cooldown (music playing, done!)
                                self._enter_wake_word_with_cooldown()
                                yield {"event": "music_playing"}
                                logger.info("🎵 Music playing → WAKE_WORD (with cooldown)")
                                return
                                
                            elif error:
                                # Agent failed, speak error and stay in LISTENING
                                logger.warning(f"Music agent error: {error}")
                                response = "I had trouble searching Spotify. Try clicking the button instead!"
                            else:
                                # No tracks found
                                response = "Sorry, I couldn't find songs for that. Try describing your mood differently."
                                
                        except Exception as e:
                            logger.error(f"Music agent exception: {e}")
                            response = "Something went wrong while searching. Try the click mode!"
                    else:
                        response = "Music search isn't available right now. Try the click mode instead!"
                    
                    # If we got here, music agent failed - do normal TTS flow
                    # (fall through to TTS code below)
                else:
                    # Conversational response via LLM
                    response = self._chat_with_llm(transcript)
                
                yield {"event": "response", "text": response}
                
                # Switch to speaking and stream TTS
                self.state = "SPEAKING"
                self.tts_playing = True  # Mark TTS as playing on frontend
                async for audio_chunk in self.tts.stream(response):
                    yield {"event": "audio", "data": audio_chunk}
                
                # Stay in SPEAKING state - wait for frontend tts_complete callback
                # The frontend will send {"event": "tts_complete"} when audio.onended fires
                # This prevents idle timeout from triggering while TTS is still playing
                logger.info("🔊 TTS sent - waiting for frontend playback to complete")
        
        # ========== SPEAKING STATE ==========
        elif self.state == "SPEAKING":
            # Use VAD to detect if user is trying to interrupt (barge-in)
            speech_prob = self.stt.vad.get_speech_probability(chunk)
            
            # If user is speaking with high confidence, interrupt TTS
            if speech_prob > 0.7:  # Higher threshold to avoid false interrupts
                self.tts.stop()
                self.tts_playing = False
                self.state = "LISTENING"
                self.stt.clear_buffer()
                self.last_activity_time = time.time()
                logger.info(f"🛑 User interrupted TTS (VAD: {speech_prob:.2f}) → LISTENING")
                yield {"event": "tts_interrupted"}
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
    
    def _generate_filler_response(self, user_message: str) -> str:
        """
        Generate engaging filler response while music agent searches.
        Uses Groq LLM with conversation history for contextual responses.
        Falls back to hardcoded response if LLM fails.
        
        Args:
            user_message: User's music request (e.g., "play something calm")
            
        Returns:
            Short filler response (~12 words max)
        """
        # Try Groq LLM if available
        if self.llm:
            try:
                # Build messages with filler system prompt + recent history
                messages = [
                    {"role": "system", "content": self.FILLER_SYSTEM_PROMPT},
                    *self.conversation_history[-4:],  # Last 2 turns for context
                    {"role": "user", "content": user_message}
                ]
                
                response = self.llm.chat.completions.create(
                    messages=messages,
                    model="llama-3.1-8b-instant",  # Fast model
                    max_tokens=30,  # Force very short response
                    temperature=0.7
                )
                
                filler = response.choices[0].message.content.strip()
                logger.info(f"💬 Filler generated: {filler}")
                return filler
                
            except Exception as e:
                logger.warning(f"Filler LLM failed: {e}, using fallback")
                # Fall through to hardcoded
        
        # Fallback: simple hardcoded response
        return "Perfect! Searching for music now."
    
    async def handle_message(self, message: dict) -> AsyncGenerator[dict, None]:
        """
        Handle JSON messages from frontend (e.g., tts_complete callback).
        
        Args:
            message: Parsed JSON message from frontend
            
        Yields:
            Events to send back to frontend
        """
        event_type = message.get("event")
        
        if event_type == "tts_complete":
            # Frontend finished playing TTS audio
            if self.state == "SPEAKING" and self.tts_playing:
                self.tts_playing = False
                self.state = "LISTENING"
                self.stt.clear_buffer()
                self.last_activity_time = time.time()  # Start idle timer NOW
                logger.info("🔊 Frontend TTS playback complete → LISTENING")
                yield {"event": "listening"}
            else:
                logger.warning(f"Received tts_complete in unexpected state: {self.state}")
        else:
            logger.warning(f"Unknown message event: {event_type}")
