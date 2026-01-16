"""
Streaming Text-to-Speech Service using Piper TTS

Generates audio in chunks for real-time streaming.
Uses synthesize_stream_raw for low-latency output.
"""

import logging
from pathlib import Path
from typing import AsyncGenerator

logger = logging.getLogger(__name__)

# Piper model paths
MODEL_DIR = Path(__file__).parent.parent / "models" / "piper"
PIPER_MODEL = MODEL_DIR / "en_US-lessac-medium.onnx"
PIPER_CONFIG = MODEL_DIR / "en_US-lessac-medium.onnx.json"


class StreamingTTS:
    """
    Text-to-speech with streaming audio output.
    
    Uses Piper TTS to generate audio chunks that can be
    sent immediately via WebSocket.
    """
    
    def __init__(self):
        """Initialize Piper TTS model"""
        self.voice = None
        self.sample_rate = 22050  # Piper default
        self._is_speaking = False
        
        try:
            from piper import PiperVoice
            
            logger.info("🔊 Loading Piper TTS...")
            
            if PIPER_MODEL.exists() and PIPER_CONFIG.exists():
                self.voice = PiperVoice.load(
                    str(PIPER_MODEL),
                    str(PIPER_CONFIG)
                )
                logger.info(f"✅ Piper loaded: {PIPER_MODEL.name}")
            else:
                logger.warning(f"⚠️ Piper model not found at {PIPER_MODEL}")
                logger.warning("⚠️ TTS will be disabled")
                self.voice = None
                
        except ImportError:
            logger.error("❌ piper-tts not installed")
            self.voice = None
        except Exception as e:
            logger.error(f"❌ Piper init failed: {e}")
            logger.warning("⚠️ TTS will be disabled")
            self.voice = None
    
    async def stream(self, text: str) -> AsyncGenerator[bytes, None]:
        """
        Stream audio chunks for given text.
        
        Args:
            text: Text to synthesize
            
        Yields:
            bytes: Raw PCM audio chunks (22050Hz, 16-bit mono)
        """
        if not self.voice or not text.strip():
            return
        
        self._is_speaking = True
        
        try:
            logger.info(f"🔊 Synthesizing: {text[:50]}...")
            
            # Accumulate all audio chunks for single WAV output
            audio_chunks = []
            
            # Use new piper1-gpl API: voice.synthesize() returns chunks
            for audio_chunk in self.voice.synthesize(text):
                if not self._is_speaking:
                    # Interrupted
                    logger.info("🔊 TTS interrupted")
                    break
                # audio_chunk has: sample_rate, sample_width, sample_channels, audio_int16_bytes
                audio_chunks.append(audio_chunk.audio_int16_bytes)
            
            # Combine all chunks and wrap in WAV header for browser playback
            if audio_chunks:
                full_audio = b''.join(audio_chunks)
                wav_audio = self._pcm_to_wav(full_audio, sample_rate=22050)
                yield wav_audio
                
            logger.info("🔊 TTS complete")
            
        except Exception as e:
            logger.error(f"TTS error: {e}")
        finally:
            self._is_speaking = False
    
    def _pcm_to_wav(self, pcm_data: bytes, sample_rate: int = 22050, channels: int = 1, sample_width: int = 2) -> bytes:
        """Wrap raw PCM data in WAV header for browser playback"""
        import struct
        
        data_size = len(pcm_data)
        file_size = data_size + 36  # WAV header is 44 bytes, minus 8 for RIFF chunk
        
        # WAV header
        header = struct.pack(
            '<4sI4s4sIHHIIHH4sI',
            b'RIFF',           # ChunkID
            file_size,         # ChunkSize
            b'WAVE',           # Format
            b'fmt ',           # Subchunk1ID
            16,                # Subchunk1Size (16 for PCM)
            1,                 # AudioFormat (1 = PCM)
            channels,          # NumChannels
            sample_rate,       # SampleRate
            sample_rate * channels * sample_width,  # ByteRate
            channels * sample_width,                # BlockAlign
            sample_width * 8,  # BitsPerSample
            b'data',           # Subchunk2ID
            data_size          # Subchunk2Size
        )
        
        return header + pcm_data
    
    def stop(self):
        """Stop current synthesis (for interrupts)"""
        self._is_speaking = False
    
    @property
    def is_speaking(self) -> bool:
        """Check if TTS is currently generating audio"""
        return self._is_speaking
