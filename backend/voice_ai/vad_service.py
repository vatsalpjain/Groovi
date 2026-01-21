"""
Voice Activity Detection (VAD) Service using Silero VAD

Provides speech detection capabilities:
- get_speech_probability: Instant speech probability for a chunk
- SpeechEndDetector: Stateful detector for end-of-speech events
"""

import logging
import numpy as np
import torch

logger = logging.getLogger(__name__)


class VADService:
    """
    Voice Activity Detection using Silero VAD model.
    
    Provides both instant probability and stateful speech-end detection.
    """
    
    def __init__(self):
        """Initialize Silero VAD model"""
        self.vad_model = None
        
        try:
            logger.info("🎤 Loading Silero VAD...")
            self.vad_model, _ = torch.hub.load(
                repo_or_dir='snakers4/silero-vad',
                model='silero_vad'
            )
            logger.info("✅ Silero VAD loaded")
        except Exception as e:
            logger.error(f"❌ VAD load failed: {e}")
            raise
        
        # State for speech-end detection
        self.is_speaking = False
        self.silence_frames = 0
        self.silence_threshold = 10  # ~1 second of silence at 100ms chunks
    
    def get_speech_probability(self, audio_chunk: bytes) -> float:
        """
        Get instant speech probability for an audio chunk.
        
        Args:
            audio_chunk: Raw PCM audio (16kHz, 16-bit mono)
            
        Returns:
            Speech probability (0.0 to 1.0)
        """
        if self.vad_model is None:
            return 0.0
            
        try:
            audio_array = np.frombuffer(audio_chunk, dtype=np.int16)
            audio_tensor = torch.from_numpy(audio_array).float() / 32768.0
            return self.vad_model(audio_tensor, 16000).item()
        except Exception as e:
            logger.error(f"VAD error: {e}")
            return 0.0
    
    def speech_ended(self, audio_chunk: bytes) -> bool:
        """
        Check if user stopped speaking (stateful).
        
        Tracks consecutive silence frames after speech.
        
        Args:
            audio_chunk: Raw PCM audio (16kHz, 16-bit mono)
            
        Returns:
            True if speech ended (silence detected after speech)
        """
        speech_prob = self.get_speech_probability(audio_chunk)
        
        if speech_prob > 0.5:
            # User is speaking
            self.is_speaking = True
            self.silence_frames = 0
            return False
        else:
            # Silence detected
            if self.is_speaking:
                self.silence_frames += 1
                # If enough silence after speech, user stopped
                if self.silence_frames >= self.silence_threshold:
                    self.is_speaking = False
                    self.silence_frames = 0
                    return True
            return False
    
    def reset(self):
        """Reset speech-end detection state"""
        self.is_speaking = False
        self.silence_frames = 0


# Singleton instance (lazy loaded)
_vad_service: VADService | None = None


def get_vad_service() -> VADService:
    """Get or create the singleton VAD service"""
    global _vad_service
    if _vad_service is None:
        _vad_service = VADService()
    return _vad_service
