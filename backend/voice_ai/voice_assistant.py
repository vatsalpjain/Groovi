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
    
    # System prompt with strict music intent detection via [MUSIC] prefix
    SYSTEM_PROMPT = """You are Groovi, a friendly AI music assistant.

Guidelines:
- Be warm, casual, and music-savvy
- Keep responses SHORT (1-2 sentences max) - you're speaking, not writing

CRITICAL - [MUSIC] Prefix Rules:
ONLY use "[MUSIC]" prefix when the user gives a DIRECT COMMAND to play/find music.

USE [MUSIC] for these EXACT patterns:
- "play [something]" → "[MUSIC] ..."
- "put on [something]" → "[MUSIC] ..."
- "find me [songs/music]" → "[MUSIC] ..."
- "I want to listen to [something]" → "[MUSIC] ..."

DO NOT use [MUSIC] for:
- Questions: "what can you play?", "do you know X artist?"
- Discussions: "I like jazz", "tell me about rock music"
- Mood sharing: "I'm feeling happy", "I'm tired"
- Anything that's NOT a direct command to search/play

When in doubt, DO NOT use [MUSIC]. Just chat normally and ask what they want to hear.
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
    
    # Response to acknowledge wake word detection
    WAKE_WORD_RESPONSE = "I'm listening."
    
    def __init__(self):
        """Initialize state and models"""
        # State machine
        self.state: Literal["WAKE_WORD", "LISTENING", "PROCESSING", "SPEAKING"] = "WAKE_WORD"
        
        # Track last activity for idle timeout
        self.last_activity_time: float = 0.0
        
        # Cooldown timestamp - ignore wake word until this time
        self.wake_word_cooldown_until: float = 0.0
        
        # TTS playback tracking - True while frontend is playing TTS audio
        self.tts_playing: bool = False
        
        # Speech detection tracking - True when VAD detects active speech
        self.speech_detected: bool = False
        
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
        self.stt.clear_buffer()
        self.wake_word.reset()  # Clear internal wake word model state
        # Set cooldown - ignore wake word detections for a brief period
        self.wake_word_cooldown_until = time.time() + self.WAKE_WORD_COOLDOWN_SEC
        logger.info(f"🔇 Wake word cooldown active for {self.WAKE_WORD_COOLDOWN_SEC}s")
    
    def _switch_to_listening(self):
        """
        Switch to LISTENING state with proper cleanup.
        
        Clears audio buffer, resets speech detection, and starts idle timeout timer.
        """
        self.state = "LISTENING"
        self.stt.clear_buffer()
        self.speech_detected = False
        self.last_activity_time = time.time()
    
    def _switch_to_speaking(self):
        """
        Switch to SPEAKING state.
        
        Marks TTS as playing for frontend tracking.
        """
        self.state = "SPEAKING"
        self.tts_playing = True
    
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
                logger.info("🎤 Wake word detected → Acknowledging")
                yield {"event": "wake_word_detected"}
                
                # Acknowledge with voice
                yield {"event": "response", "text": self.WAKE_WORD_RESPONSE}
                
                # Switch to speaking and stream TTS
                self._switch_to_speaking()
                async for audio_chunk in self.tts.stream(self.WAKE_WORD_RESPONSE):
                    yield {"event": "audio", "data": audio_chunk}
                
                # After TTS finishes, frontend will send tts_complete -> triggers LISTENING transition
                # in self.handle_message()
        
        # ========== LISTENING STATE ==========
        elif self.state == "LISTENING":
            # Check for idle timeout
            if time.time() - self.last_activity_time > self.IDLE_TIMEOUT_SEC:
                self._enter_wake_word_with_cooldown()
                logger.info("⏰ Idle timeout → WAKE_WORD")
                yield {"event": "idle_timeout"}
                return
            
            # Buffer audio in STT
            self.stt.add_chunk(chunk)
            
            # Check if user stopped speaking (also updates is_speaking flag internally)
            if self.stt.vad.speech_ended(chunk):
                self.state = "PROCESSING"
                self.last_activity_time = time.time()  # Reset timer
                logger.info("🎤 Speech ended → PROCESSING")
            elif self.stt.vad.is_speaking:
                # User is actively speaking - refresh timeout to prevent idle timeout
                self.last_activity_time = time.time()
                return
            else:
                # No speech yet or silence - just return
                return
            
            # Only reach here if speech ended - proceed with transcription
            # Transcribe buffered audio
            transcript = self.stt.transcribe()
            self.stt.clear_buffer()
            self.speech_detected = False
            
            if not transcript:
                # No speech detected, go back to wake word
                self._enter_wake_word_with_cooldown()
                yield {"event": "error", "message": "No speech detected"}
                return
            
            yield {"event": "transcript", "text": transcript}
                
                # Check for pause/stop command → Go back to wake word
            if self._is_pause_command(transcript):
                response = "Pausing. Say 'Hey Groovi' when you're ready to continue."
                yield {"event": "response", "text": response}
                
                # Stream TTS audio
                self._switch_to_speaking()
                async for audio_chunk in self.tts.stream(response):
                    yield {"event": "audio", "data": audio_chunk}
                
                # Go back to WAKE_WORD after TTS finishes
                self._enter_wake_word_with_cooldown()
                logger.info("⏸️ Pause command → WAKE_WORD (say 'Hey Groovi' to continue)")
                return
            
            # Get LLM response - it will prefix with [MUSIC] if user wants music
            response = self._chat_with_llm(transcript)
            
            # Check if LLM detected a music request via [MUSIC] prefix
            if response.startswith("[MUSIC]"):
                # Strip the prefix and use as filler response
                filler_response = response.replace("[MUSIC]", "").strip()
                
                # Add user message to conversation history
                self.conversation_history.append({
                    "role": "user",
                    "content": transcript
                })
                
                yield {"event": "agent_started"}
                
                # Build context from conversation history
                context = self._get_context_for_agent()
                query = f"{context} | Current request: {transcript}" if context else transcript
                
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
                        logger.info(f"🎵 Starting music agent: {query[:50]}...")
                        
                        # Create async task for music agent
                        agent_task = asyncio.create_task(self.music_agent.run(query))
                        
                        # Switch to SPEAKING state while filler plays
                        self._switch_to_speaking()
                        
                        # Stream filler TTS
                        tts_generator = self.tts.stream(filler_response)
                        
                        # Stream TTS while agent runs
                        async for audio_chunk in tts_generator:
                            if agent_task.done():
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
                            # Send songs to frontend
                            yield {
                                "event": "songs",
                                "summary": summary,
                                "songs": tracks
                            }
                            
                            # Switch to WAKE_WORD (music playing)
                            self._enter_wake_word_with_cooldown()
                            yield {"event": "music_playing"}
                            logger.info("🎵 Music playing → WAKE_WORD (with cooldown)")
                            return
                            
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
                
                # If we got here, music agent failed - do normal TTS flow
            # else: response is already set from _chat_with_llm (no [MUSIC] prefix)
            
            yield {"event": "response", "text": response}
            
            # Switch to speaking and stream TTS
            self._switch_to_speaking()
            async for audio_chunk in self.tts.stream(response):
                yield {"event": "audio", "data": audio_chunk}
            
            # Stay in SPEAKING state - wait for frontend tts_complete callback
            # The frontend will send {"event": "tts_complete"} when audio.onended fires
            # This prevents idle timeout from triggering while TTS is still playing
            logger.info("🔊 TTS sent - waiting for frontend playback to complete")
        
        # ========== SPEAKING STATE ==========
        elif self.state == "SPEAKING":
            # Use VAD to detect if user is trying to interrupt (barge-in)
            # Higher threshold (0.7) to avoid false interrupts from noise/echo
            if self.stt.vad.is_user_speaking(chunk, threshold=0.7):
                self.tts.stop()
                self.tts_playing = False
                self._switch_to_listening()
                logger.info("🛑 User interrupted TTS (barge-in detected) → LISTENING")
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
        """Check if user wants to stop voice mode using word boundaries to avoid false positives"""
        import re
        # Word boundaries prevent 'quite' from matching 'quit'
        patterns = [r"\bstop\b", r"\bpause\b", r"\bexit\b"]
        text_lower = text.lower()
        return any(re.search(p, text_lower) for p in patterns)
    
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
                self._switch_to_listening()
                logger.info("🔊 Frontend TTS playback complete → LISTENING")
                yield {"event": "listening"}
            else:
                logger.warning(f"Received tts_complete in unexpected state: {self.state}")
        else:
            logger.warning(f"Unknown message event: {event_type}")
