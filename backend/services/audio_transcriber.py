"""Audio transcription service using local Faster-Whisper"""

import tempfile
import os
from services.local_audio_service import get_local_audio_service


class AudioTranscriber:
    """Transcribes audio to text using local Faster-Whisper model"""
    
    def __init__(self):
        """Initialize local Whisper transcription service"""
        self.local_service = get_local_audio_service()
        print("✅ Local Whisper transcriber initialized")
    
    def transcribe_audio(self, audio_data: bytes) -> str:
        """
        Transcribe audio bytes to text using Faster-Whisper
        
        Args:
            audio_data: Raw audio file bytes (mp3, wav, webm, etc.)
            
        Returns:
            Transcribed text string
        """
        temp_path = None
        
        try:
            # Save bytes to temp file (Whisper needs file path)
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                f.write(audio_data)
                temp_path = f.name
            
            # Transcribe using local Whisper
            transcript = self.local_service.transcribe(temp_path)
            
            if not transcript or transcript.strip() == "":
                raise ValueError("No speech detected in audio")
            
            return transcript
            
        except Exception as e:
            print(f"❌ Transcription error: {e}")
            raise Exception(f"Failed to transcribe audio: {str(e)}")
            
        finally:
            # Cleanup temp file
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)


# Create global instance
audio_transcriber = AudioTranscriber()