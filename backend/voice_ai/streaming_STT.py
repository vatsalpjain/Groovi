"""
Streaming Speech-to-Text Service using Faster-Whisper

Buffers audio chunks and transcribes when user stops speaking.
Uses VADService for speech boundary detection.
"""

import logging
import tempfile
import os

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
            
            # Write to temp file (Whisper needs file path)
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                # Write WAV header + data
                self._write_wav(f, audio_data)
                temp_path = f.name
            
            # Transcribe
            segments, _ = self.whisper_model.transcribe(
                temp_path,
                beam_size=5,
                language="en"
            )
            
            transcript = " ".join([seg.text.strip() for seg in segments])
            
            # Cleanup
            os.unlink(temp_path)
            
            logger.info(f"📝 Transcribed: {transcript[:50]}...")
            return transcript.strip()
            
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return ""
    
    def clear_buffer(self):
        """Clear audio buffer and reset VAD state"""
        self.audio_buffer = []
        self.vad.reset()
    
    def _write_wav(self, f, audio_data: bytes):
        """Write raw PCM data as WAV file"""
        import struct
        
        sample_rate = 16000
        channels = 1
        bits_per_sample = 16
        
        data_size = len(audio_data)
        file_size = 36 + data_size
        
        # WAV header
        f.write(b'RIFF')
        f.write(struct.pack('<I', file_size))
        f.write(b'WAVE')
        f.write(b'fmt ')
        f.write(struct.pack('<I', 16))  # Subchunk1Size
        f.write(struct.pack('<H', 1))   # AudioFormat (PCM)
        f.write(struct.pack('<H', channels))
        f.write(struct.pack('<I', sample_rate))
        f.write(struct.pack('<I', sample_rate * channels * bits_per_sample // 8))
        f.write(struct.pack('<H', channels * bits_per_sample // 8))
        f.write(struct.pack('<H', bits_per_sample))
        f.write(b'data')
        f.write(struct.pack('<I', data_size))
        f.write(audio_data)
