"""Test local audio services (Faster-Whisper STT + Piper TTS)"""

import sys
import time
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.local_audio_service import get_local_audio_service


def test_tts():
    """Test Piper TTS - text to speech"""
    print("\n🔊 Testing Piper TTS...")
    
    try:
        service = get_local_audio_service()
        
        test_text = "Hello! Welcome to Groovi, your mood-based music recommender."
        
        start_time = time.time()
        audio_path = service.synthesize(test_text)
        elapsed = time.time() - start_time
        
        # Check file exists and has content
        audio_file = Path(audio_path)
        if audio_file.exists() and audio_file.stat().st_size > 0:
            size_kb = audio_file.stat().st_size / 1024
            print(f"✅ TTS Success! ({elapsed:.2f}s, {size_kb:.1f}KB)")
            print(f"   Audio saved to: {audio_path}")
            return audio_path
        else:
            print("❌ TTS failed - no audio file created")
            return None
            
    except Exception as e:
        print(f"❌ TTS Error: {e}")
        return None


def test_stt(audio_path: str = None):
    """Test Faster-Whisper STT - speech to text"""
    print("\n🎤 Testing Faster-Whisper STT...")
    
    if not audio_path:
        print("⚠️ No audio file provided, generating test audio first...")
        audio_path = test_tts()
        if not audio_path:
            print("❌ Cannot test STT without audio file")
            return False
    
    try:
        service = get_local_audio_service()
        
        start_time = time.time()
        transcript = service.transcribe(audio_path)
        elapsed = time.time() - start_time
        
        if transcript and transcript.strip():
            print(f"✅ STT Success! ({elapsed:.2f}s)")
            print(f"   Transcript: {transcript}")
            return True
        else:
            print("❌ STT failed - empty transcript")
            return False
            
    except Exception as e:
        print(f"❌ STT Error: {e}")
        return False


def test_round_trip():
    """Test full round trip: Text → Audio → Text"""
    print("\n🔄 Testing Round Trip (TTS → STT)...")
    
    original_text = "Groovi helps you find music that matches your mood."
    
    try:
        service = get_local_audio_service()
        
        # TTS: Text to Audio
        print(f"   Original: {original_text}")
        audio_path = service.synthesize(original_text)
        
        # STT: Audio to Text
        transcript = service.transcribe(audio_path)
        print(f"   Result:   {transcript}")
        
        # Compare (basic similarity check)
        original_words = set(original_text.lower().split())
        result_words = set(transcript.lower().split())
        common = original_words.intersection(result_words)
        similarity = len(common) / len(original_words) * 100
        
        print(f"   Similarity: {similarity:.0f}%")
        
        if similarity >= 50:
            print("✅ Round trip test PASSED")
            return True
        else:
            print("⚠️ Round trip test - low similarity")
            return False
            
    except Exception as e:
        print(f"❌ Round trip Error: {e}")
        return False


def run_all_tests():
    """Run all local audio tests"""
    print("=" * 50)
    print("🧪 Local Audio Service Tests")
    print("=" * 50)
    
    # Initialize service (loads models)
    print("\n📦 Loading models (this may take a moment)...")
    start_time = time.time()
    service = get_local_audio_service()
    load_time = time.time() - start_time
    print(f"✅ Models loaded in {load_time:.1f}s")
    
    # Run tests
    results = {
        "TTS": test_tts() is not None,
        "STT": test_stt(),
        "Round Trip": test_round_trip()
    }
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary")
    print("=" * 50)
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {test_name}: {status}")
    
    all_passed = all(results.values())
    print("\n" + ("🎉 All tests passed!" if all_passed else "⚠️ Some tests failed"))
    return all_passed


if __name__ == "__main__":
    run_all_tests()
