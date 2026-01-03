"""Local audio processing service using Faster-Whisper (STT) and Piper (TTS)"""

from pathlib import Path
import tempfile
import logging
import wave
import os

from faster_whisper import WhisperModel
from piper import PiperVoice

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Piper voice model config
PIPER_VOICE_NAME = "en_US-lessac-medium"
PIPER_MODEL_DIR = Path.home() / ".local" / "share" / "piper-voices"


class LocalAudioService:
    """Handles local speech-to-text and text-to-speech processing"""
    
    def __init__(self):
        """Initialize Faster-Whisper (STT) and Piper (TTS) models"""
        self.whisper_model = None
        self.piper_voice = None
        
        # Initialize Whisper STT
        try:
            logger.info("🎤 Loading Faster-Whisper model (base)...")
            self.whisper_model = WhisperModel(
                "base",
                device="cpu",
                compute_type="int8"
            )
            logger.info("✅ Faster-Whisper model loaded successfully")
        except Exception as e:
            logger.error(f"❌ Failed to load Whisper model: {e}")
            raise RuntimeError(f"Whisper initialization failed: {e}")
        
        # Initialize Piper TTS
        self._init_piper()
    
    def _init_piper(self):
        """
        Initialize Piper TTS voice model
        Downloads model on first run if not present
        """
        try:
            logger.info(f"🔊 Loading Piper TTS voice ({PIPER_VOICE_NAME})...")
            
            # Create model directory if not exists
            PIPER_MODEL_DIR.mkdir(parents=True, exist_ok=True)
            
            # Model file paths
            model_path = PIPER_MODEL_DIR / f"{PIPER_VOICE_NAME}.onnx"
            config_path = PIPER_MODEL_DIR / f"{PIPER_VOICE_NAME}.onnx.json"
            
            # Check if model exists, if not download
            if not model_path.exists():
                logger.info("📥 Downloading Piper voice model (first time only)...")
                self._download_piper_model()
            
            # Load the voice
            self.piper_voice = PiperVoice.load(str(model_path), str(config_path))
            logger.info("✅ Piper TTS voice loaded successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to load Piper TTS: {e}")
            self.piper_voice = None  # TTS will be disabled but STT works
    
    def _download_piper_model(self):
        """Download Piper voice model from huggingface"""
        import urllib.request
        
        base_url = "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/"
        model_path = PIPER_MODEL_DIR / f"{PIPER_VOICE_NAME}.onnx"
        config_path = PIPER_MODEL_DIR / f"{PIPER_VOICE_NAME}.onnx.json"
        
        # Download model file (~50MB)
        logger.info("Downloading voice model (this may take a minute)...")
        urllib.request.urlretrieve(f"{base_url}en_US-lessac-medium.onnx", model_path)
        
        # Download config file
        urllib.request.urlretrieve(f"{base_url}en_US-lessac-medium.onnx.json", config_path)
        
        logger.info("✅ Voice model downloaded")
    
    def transcribe(self, audio_path: str) -> str:
        """
        Transcribe audio file to text using Faster-Whisper
        
        Args:
            audio_path: Path to audio file (mp3, wav, webm, etc.)
            
        Returns:
            Transcribed text string
        """
        if not self.whisper_model:
            raise RuntimeError("Whisper model not initialized")
        
        # Verify file exists
        if not Path(audio_path).exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        try:
            import time
            start_time = time.time()
            
            logger.info(f"🎤 Transcribing: {audio_path}")
            
            # Run Whisper transcription
            segments, info = self.whisper_model.transcribe(
                audio_path,
                beam_size=5,
                language="en"
            )
            
            # Combine all segments into text
            transcript = " ".join([segment.text.strip() for segment in segments])
            
            elapsed = time.time() - start_time
            logger.info(f"✅ Transcription complete ({elapsed:.2f}s): {transcript[:50]}...")
            
            return transcript.strip()
            
        except Exception as e:
            logger.error(f"❌ Transcription failed: {e}")
            raise RuntimeError(f"Transcription failed: {e}")
    
    def synthesize(self, text: str, output_path: str = None) -> str:
        """
        Convert text to speech using Piper TTS
        
        Args:
            text: Text to speak (max 500 characters)
            output_path: Optional output file path. If None, creates temp file.
            
        Returns:
            Path to generated WAV audio file
        """
        if not self.piper_voice:
            raise RuntimeError("Piper TTS not initialized")
        
        # Validate text length
        if len(text) > 500:
            text = text[:500]
            logger.warning("Text truncated to 500 characters")
        
        try:
            import time
            start_time = time.time()
            
            logger.info(f"🔊 Synthesizing speech: {text[:50]}...")
            
            # Create output path if not provided
            if output_path is None:
                temp_dir = tempfile.gettempdir()
                output_path = os.path.join(temp_dir, f"groovi_tts_{int(time.time())}.wav")
            
            # Use synthesize_wav which handles WAV format automatically
            # Use SynthesisConfig to control speech speed (length_scale > 1.0 = slower)
            from piper.voice import SynthesisConfig
            syn_config = SynthesisConfig(length_scale=1.4)
            
            with wave.open(output_path, "wb") as wav_file:
                self.piper_voice.synthesize_wav(text, wav_file, syn_config=syn_config)
            
            elapsed = time.time() - start_time
            file_size = os.path.getsize(output_path) / 1024  # KB
            logger.info(f"✅ TTS complete ({elapsed:.2f}s, {file_size:.1f}KB): {output_path}")
            
            return output_path
            
        except Exception as e:
            logger.error(f"❌ TTS failed: {e}")
            raise RuntimeError(f"Text-to-speech failed: {e}")


# Global instance - initialized once when module is imported
# Note: This will load models on import (~10 seconds first time)
local_audio_service = None

def get_local_audio_service():
    """Get or create the LocalAudioService singleton"""
    global local_audio_service
    if local_audio_service is None:
        local_audio_service = LocalAudioService()
    return local_audio_service
