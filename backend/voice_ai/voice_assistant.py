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

from groq import AsyncGroq
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
        
        # Post-TTS state: tells tts_complete handler what state to transition to
        # None = default (LISTENING), "WAKE_WORD" = enter wake word mode after TTS
        self._post_tts_state: str | None = None
        
        # Conversation history for LLM context
        self.conversation_history: list[dict] = []
        
        # Initialize all services
        logger.info("🚀 Initializing VoiceAssistant...")
        
        # LLM for conversational responses
        self.llm = None
        self.music_agent = None
        if settings.GROQ_API_KEY:
            try:
                self.llm = AsyncGroq(api_key=settings.GROQ_API_KEY)
                
                # We defer creating the agent until queues are set up below
                # or we can pass a lambda that calls output_queue.put
                self.music_agent = None  
                logger.info("✅ Groq LLM initialized")
            except Exception as e:
                logger.warning(f"⚠️ Groq init failed: {e} - using canned responses")
        
        self.wake_word = WakeWordService()
        self.stt = StreamingSTT()
        self.tts = StreamingTTS()
        
        self.output_queue: asyncio.Queue = asyncio.Queue()
        self.tts_queue: asyncio.Queue = asyncio.Queue()
        
        # Now that output_queue is created, initialize the Music Agent
        if self.llm:
            self.music_agent = MusicRecommendationAgent(
                self.llm, 
                on_iteration=self.output_queue.put
            )
            logger.info("✅ Music Agent initialized with iteration callback")
            
        # Background tasks
        self.tts_task: asyncio.Task | None = None
        
        
        # Flag to track if music agent is currently fetching (prevents accidental wake word during delay)
        self.is_fetching_music: bool = False
        
        logger.info("✅ VoiceAssistant initialized in WAKE_WORD mode")

    async def start(self):
        """Start background workers"""
        if not self.tts_task:
            self.tts_task = asyncio.create_task(self._tts_worker())
            logger.info("▶️ VoiceAssistant workers started")

    async def _tts_worker(self):
        """Background worker to consume text and stream TTS audio"""
        while True:
            try:
                # Get text to speak
                text = await self.tts_queue.get()
                
                if not text:
                    continue
                    
                # Signal speaking start
                self._switch_to_speaking()
                
                # Notify the pipeline UI that TTS is starting.
                await self.output_queue.put({"event": "tts_start"})
                
                # Stream audio chunks as binary
                async for chunk in self.tts.stream(text):
                    await self.output_queue.put({"event": "audio", "data": chunk})
                
                # Signal local completion (frontend will send tts_complete)
                self.tts_queue.task_done()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"TTS worker error: {e}")
    
    def _enter_wake_word_with_cooldown(self):
        """
        Switch to WAKE_WORD state with proper cleanup and cooldown.
        
        Clears all audio buffers and resets wake word model to prevent
        false triggers from residual TTS audio or noise.
        """
        self.state = "WAKE_WORD"
        self.tts_playing = False  # Reset TTS flag to prevent false barge-in triggers
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
    
    async def speak(self, text: str):
        """Enqueue text for TTS"""
        await self.tts_queue.put(text)

    async def stop_speaking(self):
        """Stop current TTS and clear pending speech"""
        if self.tts_playing:
            self.tts.stop()
            self.tts_playing = False
            
            # Clear queues
            while not self.tts_queue.empty():
                try:
                    self.tts_queue.get_nowait()
                    self.tts_queue.task_done()
                except asyncio.QueueEmpty:
                    break
            
            # Notify frontend of interruption
            await self.output_queue.put({"event": "tts_interrupted"})
            await self.output_queue.put({"event": "listening"})
            logger.info("🛑 Stopped speaking (queues cleared)")

    async def handle_audio_chunk(self, chunk: bytes):
        """
        Process incoming audio chunk (Full Duplex).
        Non-blocking: Buffers audio and spawns background tasks for processing.
        """
        # Global barge-in check
        if (self.state == "SPEAKING" or self.tts_playing) and not self.is_fetching_music:
            if self.stt.vad.is_user_speaking(chunk, threshold=0.7):
                await self.stop_speaking()
                self._switch_to_listening()
                return

        # ========== WAKE_WORD STATE ==========
        if self.state == "WAKE_WORD":
            if self.is_fetching_music:
                return

            if time.time() < self.wake_word_cooldown_until:
                return

            if self.wake_word.detect(chunk):
                logger.info("🎤 Wake word detected")
                await self.output_queue.put({"event": "wake_word_detected"})
                await self.speak(self.WAKE_WORD_RESPONSE)
        
        # ========== LISTENING STATE ==========
        elif self.state == "LISTENING":
            # Idle timeout
            if time.time() - self.last_activity_time > self.IDLE_TIMEOUT_SEC:
                self._enter_wake_word_with_cooldown()
                await self.output_queue.put({"event": "idle_timeout"})
                return

            self.stt.add_chunk(chunk)
            
            if self.stt.vad.speech_ended(chunk):
                self.state = "PROCESSING"
                self.last_activity_time = time.time()
                
                # Transcribe
                transcript = self.stt.transcribe()
                self.stt.clear_buffer()
                
                if transcript:
                    await self.output_queue.put({"event": "transcript", "text": transcript})
                    # Spawn background task for processing
                    asyncio.create_task(self._process_transcript(transcript))
                else:
                    self._enter_wake_word_with_cooldown()
                    await self.output_queue.put({"event": "error", "message": "No speech detected"})
                    
            elif self.stt.vad.is_speaking:
                self.last_activity_time = time.time()

    async def _process_transcript(self, transcript: str):
        """Process transcribed text (LLM/Agent) in background"""
        try:
            # Check for pause command
            if self._is_pause_command(transcript):
                response = "Pausing. Say 'Hey Groovi' when you're ready to continue."
                # Send AI text to frontend for chat bubble display
                await self.output_queue.put({"event": "response_text", "text": response})
                # Tell tts_complete handler to enter WAKE_WORD after TTS finishes
                self._post_tts_state = "WAKE_WORD"
                await self.speak(response)
                return

            # Chat with LLM — time the call so we can report latency
            llm_start = time.time()
            response = await self._chat_with_llm(transcript)
            llm_elapsed_ms = int((time.time() - llm_start) * 1000)
            
            # Check for music intent
            if response.startswith("[MUSIC]"):
                filler_response = response.replace("[MUSIC]", "").strip()
                
                # Add to history
                self.conversation_history.append({"role": "user", "content": transcript})
                self.conversation_history.append({"role": "assistant", "content": filler_response})
                
                await self.output_queue.put({"event": "processing"})
                
                # Send filler text to frontend for chat bubble display
                await self.output_queue.put({"event": "response_text", "text": filler_response})
                
                # Set flag so we don't switch to LISTENING when filler TTS ends
                self.is_fetching_music = True
                await self.speak(filler_response)
                
                # Run Music Agent
                if self.music_agent:
                    context = self._get_context_for_agent()
                    query = f"{context} | Current request: {transcript}" if context else transcript
                    
                    try:
                        logger.info(f"🎵 Starting music agent: {query[:50]}...")
                        result = await self.music_agent.run(query)
                        
                        if result and result.get("tracks"):
                            # Success
                            tracks = result["tracks"]
                            summary = result.get("summary", "")
                            
                            song_names = [f"{t['name']} by {t['artist']}" for t in tracks[:3]]
                            history_entry = f"{summary} Tracks: {', '.join(song_names)}"
                            self.conversation_history.append({"role": "assistant", "content": history_entry})
                            
                            # Send results
                            await self.output_queue.put({
                                "event": "songs",
                                "mood_analysis": result.get("mood_analysis"),
                                "songs": tracks
                            })
                            
                            self._enter_wake_word_with_cooldown()
                            await self.output_queue.put({"event": "music_playing"})
                            # Reset flag (music playing handled by wake word cooldown)
                            self.is_fetching_music = False
                            return
                            
                        elif result and result.get("error"):
                             logger.warning(f"Music agent error: {result['error']}")
                             response = "I had trouble searching Spotify. Try clicking the button instead!"
                        else:
                             response = "Sorry, I couldn't find songs for that."
                             
                    except Exception as e:
                        logger.error(f"Music agent exception: {e}")
                        response = "Something went wrong while searching."
                    
                    # Reset flag (failed or completed without tracks)
                    self.is_fetching_music = False
                else:
                     self.music_agent = None  
                     self.is_fetching_music = False
                     response = "Music search isn't available right now."
                
                # Send AI text to frontend for chat bubble display
                await self.output_queue.put({"event": "response_text", "text": response})
                # Tell tts_complete handler to enter WAKE_WORD after TTS finishes
                self._post_tts_state = "WAKE_WORD"
                # Speak fallback/result response if we didn't return early
                await self.speak(response)
                
            else:
                # Normal (non-music) chat — emit LLM latency so the pipeline UI shows it
                await self.output_queue.put({
                    "event": "agent_complete",
                    "totalMs": llm_elapsed_ms,
                })
                
                # Send AI text to frontend for chat bubble display
                await self.output_queue.put({"event": "response_text", "text": response})
                # Normal chat response
                await self.speak(response)
                
                # Emit response_complete so the frontend can calculate TTS + Total latency
                await self.output_queue.put({"event": "response_complete"})
                
        except Exception as e:
            logger.error(f"Error processing transcript: {e}")
            await self.speak("Sorry, something went wrong.")

    def cleanup(self):
        """Clean up all models and free memory"""
        logger.info("🧹 Cleaning up VoiceAssistant...")
        
        # Cancel background tasks
        if self.tts_task:
            self.tts_task.cancel()
            self.tts_task = None
        
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

    async def _chat_with_llm(self, user_message: str) -> str:
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
                
                response = await self.llm.chat.completions.create(
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
    
    async def _generate_filler_response(self, user_message: str) -> str:
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
                
                response = await self.llm.chat.completions.create(
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
    
    async def handle_message(self, message: dict):
        """
        Handle JSON messages from frontend (e.g., tts_complete callback).
        Args:
            message: Parsed JSON message from frontend
        """
        event_type = message.get("event")
        
        if event_type == "tts_complete":
            # Frontend finished playing TTS audio
            
            # If fetching music, go to WAKE_WORD (safe state) instead of LISTENING
            if self.is_fetching_music:
                logger.info("🎵 Music fetch in progress - tts_complete received, switching to WAKE_WORD")
                self.tts_playing = False
                self._enter_wake_word_with_cooldown()
                return

            if self.state == "SPEAKING" and self.tts_playing:
                self.tts_playing = False
                
                if self._post_tts_state == "WAKE_WORD":
                    self._post_tts_state = None
                    self._enter_wake_word_with_cooldown()
                    logger.info("🔊 Frontend TTS playback complete → WAKE_WORD")
                    await self.output_queue.put({"event": "idle_timeout"})
                else:
                    self._switch_to_listening()
                    logger.info("🔊 Frontend TTS playback complete → LISTENING")
                    await self.output_queue.put({"event": "listening"})
            else:
                logger.warning(f"Received tts_complete in unexpected state: {self.state}")
        else:
            logger.warning(f"Unknown message event: {event_type}")
