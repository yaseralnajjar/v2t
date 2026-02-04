"""Simple sine wave tones."""

import numpy as np
import sounddevice as sd

from .base import SAMPLE_RATE


def _generate_tone(frequency, duration):
    """Generate a simple sine wave tone."""
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), False)
    tone = np.sin(2 * np.pi * frequency * t)
    # Apply fade in/out to avoid clicks
    fade_samples = int(SAMPLE_RATE * 0.01)
    tone[:fade_samples] *= np.linspace(0, 1, fade_samples)
    tone[-fade_samples:] *= np.linspace(1, 0, fade_samples)
    return (tone * 0.3).astype(np.float32)


def play_start():
    """Play a short high tone to indicate recording started."""
    tone = _generate_tone(880, 0.1)  # A5 note, 100ms
    sd.play(tone, samplerate=SAMPLE_RATE)


def play_stop():
    """Play a short low tone to indicate recording stopped."""
    tone = _generate_tone(440, 0.1)  # A4 note, 100ms
    sd.play(tone, samplerate=SAMPLE_RATE)
