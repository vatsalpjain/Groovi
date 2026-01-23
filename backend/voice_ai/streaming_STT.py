"""
Streaming Speech-to-Text Service using Faster-Whisper

Buffers audio chunks and transcribes when user stops speaking.
Uses VADService for speech boundary detection.
"""

import logging
import numpy as np

from voice_ai.vad_service import get_vad_service

logger = logging.getLogger(__name__)


class StreamingSTT:
    """
    Speech-to-text with audio buffering and VAD.
    
    Collects audio chunks, detects when speech ends via VAD,
    then transcribes the complete utterance.
    """
    
    def __init__(self):
        """Initialize Faster-Whisper model and VAD service"""
        self.whisper_model = None
        self.audio_buffer: list[bytes] = []
        
        # Get shared VAD service
        self.vad = get_vad_service()
        
        # Initialize Whisper
        try:
            from faster_whisper import WhisperModel
            
            logger.info("🎤 Loading Faster-Whisper (base)...")
            self.whisper_model = WhisperModel(
                "base",
                device="cpu",
                compute_type="int8"
            )
            logger.info("✅ Whisper model loaded")
            
        except ImportError:
            logger.error("❌ faster-whisper not installed")
            raise
    
    def add_chunk(self, audio_chunk: bytes):
        """Add audio chunk to buffer"""
        self.audio_buffer.append(audio_chunk)

    
    def transcribe(self, audio_chunks: list[bytes] = None) -> str:
        """
        Transcribe buffered or provided audio chunks.
        
        Args:
            audio_chunks: Optional list of audio chunks (uses buffer if None)
            
        Returns:
            Transcribed text
        """
        chunks = audio_chunks or self.audio_buffer
        
        if not chunks:
            return ""
        
        try:
            # Combine all chunks
            audio_data = b''.join(chunks)
            
            # Check minimum duration (prevent transcribing noise bursts)
            duration_sec = len(audio_data) / (16000 * 2)  # 16kHz, 16-bit (2 bytes/sample)
            if duration_sec < 0.5:
                logger.info(f"⏭️ Ignoring {duration_sec:.2f}s audio (too short, likely noise)")
                return ""
            
            # Convert bytes to numpy array (no temp file needed!)
            audio_array = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
            
            # Transcribe directly from numpy array
            segments, _ = self.whisper_model.transcribe(
                audio_array,
                beam_size=1, 
                language="en"
            )
            
            transcript = " ".join([seg.text.strip() for seg in segments])
            
            logger.info(f"📝 Transcribed ({duration_sec:.1f}s): {transcript[:50]}...")
            return transcript.strip()
            
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return ""
    
    def clear_buffer(self):
        """Clear audio buffer and reset VAD state"""
        self.audio_buffer = []
        self.vad.reset()
