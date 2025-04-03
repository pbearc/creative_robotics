import aubio
import numpy as np
import pyaudio

# Constants
BUFFER_SIZE = 1024  # Number of audio samples per frame
SAMPLE_RATE = 44100  # Sample rate in Hz

# Open the microphone stream
p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paFloat32, channels=1, rate=SAMPLE_RATE, input=True, frames_per_buffer=BUFFER_SIZE)

# Initialize pitch detection
pitch_detector = aubio.pitch("default", BUFFER_SIZE * 2, BUFFER_SIZE, SAMPLE_RATE)
pitch_detector.set_unit("Hz")
pitch_detector.set_silence(-40)

# Define note frequencies (A4 = 440 Hz tuning)
note_frequencies = {
    "C": 261.63, "D": 293.66, "E": 329.63, "F": 349.23,
    "G": 392.00, "A": 440.00, "B": 493.88
}

# Function to find the closest musical note
def find_closest_note(frequency):
    if frequency == 0:
        return None  # No sound detected
    return min(note_frequencies, key=lambda note: abs(note_frequencies[note] - frequency))

print("Listening for pitch... (Press Ctrl+C to stop)")

try:
    while True:
        audio_data = np.frombuffer(stream.read(BUFFER_SIZE), dtype=np.float32)
        pitch = pitch_detector(audio_data)[0]  # Get detected pitch in Hz

        if pitch > 50:  # Ignore low frequencies (background noise)
            note = find_closest_note(pitch)
            print(f"Detected Note: {note} ({pitch:.2f} Hz)")

except KeyboardInterrupt:
    print("\nStopping...")

finally:
    stream.stop_stream()
    stream.close()
    p.terminate()
