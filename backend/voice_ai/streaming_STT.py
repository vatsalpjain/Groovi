"""
Streaming Speech-to-Text Service using Faster-Whisper with Silero VAD

Buffers audio chunks and transcribes when user stops speaking.
Uses VAD to detect speech boundaries.
"""

import logging
import tempfile
import os
from pathlib import Path

logger = logging.getLogger(__name__)


class StreamingSTT:
    """
    Speech-to-text with audio buffering and VAD.
    
    Collects audio chunks, detects when speech ends via VAD,
    then transcribes the complete utterance.
    """
    
    def __init__(self):
        """Initialize Faster-Whisper model and Silero VAD"""
        self.whisper_model = None
        self.vad_model = None
        self.audio_buffer: list[bytes] = []
        self.is_speaking = False
        self.silence_frames = 0
        self.silence_threshold = 10  # ~1 second of silence at 100ms chunks
        
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
        
        # Initialize Silero VAD
        try:
            import torch
            
            logger.info("🎤 Loading Silero VAD...")
            self.vad_model, utils = torch.hub.load(
                repo_or_dir='snakers4/silero-vad',
                model='silero_vad'
            )
            self.get_speech_timestamps = utils[0]
            logger.info("✅ Silero VAD loaded")
            
        except Exception as e:
            logger.error(f"❌ VAD load failed: {e}")
            raise
    
    def add_chunk(self, audio_chunk: bytes):
        """Add audio chunk to buffer"""
        self.audio_buffer.append(audio_chunk)
    
    def speech_ended(self, audio_chunk: bytes) -> bool:
        """
        Check if user stopped speaking using VAD.
        
        Args:
            audio_chunk: Raw PCM audio (16kHz, 16-bit mono)
            
        Returns:
            True if speech ended (silence detected after speech)
        """
        try:
            import torch
            import numpy as np
            
            # Convert bytes to tensor
            audio_array = np.frombuffer(audio_chunk, dtype=np.int16)
            audio_tensor = torch.from_numpy(audio_array).float() / 32768.0
            
            # Get speech probability
            speech_prob = self.vad_model(audio_tensor, 16000).item()
            
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
                
        except Exception as e:
            logger.error(f"VAD error: {e}")
            return False
    
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
        """Clear audio buffer"""
        self.audio_buffer = []
        self.is_speaking = False
        self.silence_frames = 0
    
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
