/**
 * AudioWorklet Processor for Raw PCM Capture
 * 
 * Runs in a separate audio thread.
 * Captures raw audio samples and sends them to the main thread.
 * 
 * Input: Float32 samples at native sample rate (usually 48kHz)
 * Output: Int16 PCM samples (16-bit) via postMessage
 */

class AudioCaptureProcessor extends AudioWorkletProcessor {
  constructor() {
    super()
    this.bufferSize = 4096  // Accumulate samples before sending
    this.buffer = new Float32Array(this.bufferSize)
    this.bufferIndex = 0
  }

  process(inputs, outputs, parameters) {
    const input = inputs[0]
    
    // Check if we have audio input
    if (!input || !input[0] || input[0].length === 0) {
      return true
    }

    const samples = input[0]  // Mono channel

    // Accumulate samples into buffer
    for (let i = 0; i < samples.length; i++) {
      this.buffer[this.bufferIndex++] = samples[i]

      // When buffer is full, send it
      if (this.bufferIndex >= this.bufferSize) {
        // Convert Float32 (-1 to 1) to Int16 (-32768 to 32767)
        const int16Buffer = new Int16Array(this.bufferSize)
        for (let j = 0; j < this.bufferSize; j++) {
          // Clamp and convert
          const sample = Math.max(-1, Math.min(1, this.buffer[j]))
          int16Buffer[j] = sample < 0 
            ? sample * 0x8000 
            : sample * 0x7FFF
        }

        // Send to main thread
        this.port.postMessage({
          type: 'audio',
          buffer: int16Buffer.buffer,
          sampleRate: sampleRate  // Built-in AudioWorklet variable
        }, [int16Buffer.buffer])

        // Reset buffer
        this.buffer = new Float32Array(this.bufferSize)
        this.bufferIndex = 0
      }
    }

    return true  // Keep processor alive
  }
}

registerProcessor('audio-capture-processor', AudioCaptureProcessor)
