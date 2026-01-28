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
        self.silence_threshold = 20  # ~2 seconds of silence (was 10)
    
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
    
    def speech_ended(self, audio_chunk: bytes, threshold: int = None, speech_prob_threshold: float = 0.5) -> bool:
        """
        Check if user stopped speaking (stateful).
        
        Tracks consecutive silence frames after speech.
        
        Args:
            audio_chunk: Raw PCM audio (16kHz, 16-bit mono)
            threshold: Custom silence threshold (frames). If None, uses self.silence_threshold
            speech_prob_threshold: VAD probability threshold (0.0-1.0). Speech detected when prob > this value. Default 0.5
            
        Returns:
            True if speech ended (silence detected after speech)
        """
        speech_prob = self.get_speech_probability(audio_chunk)
        
        # Use custom threshold or default
        silence_threshold = threshold if threshold is not None else self.silence_threshold
        
        if speech_prob > speech_prob_threshold:
            # User is speaking
            self.is_speaking = True
            self.silence_frames = 0
            return False
        else:
            # Silence detected
            if self.is_speaking:
                self.silence_frames += 0.7
                # If enough silence after speech, user stopped
                if self.silence_frames >= silence_threshold:
                    self.is_speaking = False
                    self.silence_frames = 0
                    return True
            return False
    
    def is_user_speaking(self, audio_chunk: bytes, threshold: float = 0.7) -> bool:
        """
        Check if user is currently speaking (instant detection, no state).
        
        Useful for barge-in detection during TTS playback.
        Higher threshold recommended to avoid false positives from noise/echo.
        
        Args:
            audio_chunk: Raw PCM audio (512 bytes = 16ms @ 16kHz)
            threshold: Minimum speech probability to consider as active speech (0.0-1.0, default: 0.7)
        
        Returns:
            True if speech probability exceeds threshold, False otherwise
        """
        prob = self.get_speech_probability(audio_chunk)
        return prob > threshold
    
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
