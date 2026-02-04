"""Warm bloop tones with rich harmonics."""

import numpy as np
import sounddevice as sd

from .base import SAMPLE_RATE, apply_envelope, generate_harmonic_tone


def play_start():
    """Play a soft 'bloop' activation sound - low fundamental with rich harmonics."""
    duration_ms = 120

    harmonics = [
        (140, 1.0),    # Fundamental
        (240, 0.37),   # ~1.7x
        (350, 0.14),   # ~2.5x
        (450, 0.11),   # ~3.2x
        (613, 0.12),   # ~4.4x
        (767, 0.09),   # ~5.5x
    ]

    tone = generate_harmonic_tone(140, duration_ms, harmonics)
    tone = apply_envelope(tone, attack_ms=8, decay_ms=100)

    tone = tone / np.max(np.abs(tone))
    sound = (tone * 0.35).astype(np.float32)

    sd.play(sound, samplerate=SAMPLE_RATE)


def play_stop():
    """Play a soft confirmation 'bloop' - similar but simpler harmonics."""
    duration_ms = 120

    harmonics = [
        (140, 1.0),    # Fundamental
        (243, 0.16),   # ~1.7x
        (413, 0.12),   # ~3x
    ]

    tone = generate_harmonic_tone(140, duration_ms, harmonics)
    tone = apply_envelope(tone, attack_ms=8, decay_ms=90)

    tone = tone / np.max(np.abs(tone))
    sound = (tone * 0.30).astype(np.float32)

    sd.play(sound, samplerate=SAMPLE_RATE)
