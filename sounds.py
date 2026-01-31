import numpy as np
import sounddevice as sd


def _generate_tone(frequency, duration, samplerate=44100):
    """Generate a simple sine wave tone."""
    t = np.linspace(0, duration, int(samplerate * duration), False)
    tone = np.sin(2 * np.pi * frequency * t)
    # Apply fade in/out to avoid clicks
    fade_samples = int(samplerate * 0.01)
    tone[:fade_samples] *= np.linspace(0, 1, fade_samples)
    tone[-fade_samples:] *= np.linspace(1, 0, fade_samples)
    return (tone * 0.3).astype(np.float32)


def play_start_sound():
    """Play a short ascending tone to indicate recording started."""
    tone = _generate_tone(880, 0.1)  # A5 note, 100ms
    sd.play(tone, samplerate=44100)


def play_stop_sound():
    """Play a short descending tone to indicate recording stopped."""
    tone = _generate_tone(440, 0.1)  # A4 note, 100ms
    sd.play(tone, samplerate=44100)
