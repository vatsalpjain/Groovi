"""
Simple test script for wake word model loading
Run with: uv run python tests/test_wakeword.py
"""

from pathlib import Path

print("=" * 50)
print("Testing Wake Word Model Loading")
print("=" * 50)

# Paths
MODEL_DIR = Path(__file__).parent.parent / "models"
ONNX_MODEL = MODEL_DIR / "Hey_Groovy.onnx"
TFLITE_MODEL = MODEL_DIR / "Hey_Groovi.tflite"

print(f"\nLooking for models in: {MODEL_DIR}")
print(f"   ONNX exists: {ONNX_MODEL.exists()}")
print(f"   TFLite exists: {TFLITE_MODEL.exists()}")

# Test 1: Import openWakeWord
print("\nTest 1: Importing openWakeWord...")
try:
    from openwakeword.model import Model
    print("   Import successful")
except ImportError as e:
    print(f"   Import failed: {e}")
    exit(1)

# Test 2: Load model with no arguments (default models)
print("\nTest 2: Loading default models...")
try:
    model = Model()
    print(f"   Default models loaded")
    print(f"   Available models: {list(model.models.keys())}")
except Exception as e:
    print(f"   Failed: {e}")

# Test 3: Load ONNX model
if ONNX_MODEL.exists():
    print(f"\nTest 3: Loading ONNX model ({ONNX_MODEL.name})...")
    try:
        model = Model(wakeword_model_paths=[str(ONNX_MODEL)])
        print(f"   ONNX model loaded")
        print(f"   Models: {list(model.models.keys())}")
    except Exception as e:
        print(f"   Failed: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

# Test 4: Load TFLite model
if TFLITE_MODEL.exists():
    print(f"\nTest 4: Loading TFLite model ({TFLITE_MODEL.name})...")
    try:
        model = Model(wakeword_model_paths=[str(TFLITE_MODEL)])
        print(f"   TFLite model loaded")
        print(f"   Models: {list(model.models.keys())}")
    except Exception as e:
        print(f"   Failed: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "=" * 50)
print("Test Complete")
print("=" * 50)
