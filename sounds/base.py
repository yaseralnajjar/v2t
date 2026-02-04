"""Base utilities for sound generation."""

import numpy as np

SAMPLE_RATE = 44100


def apply_envelope(signal, attack_ms=5, decay_ms=50):
    """Apply attack and exponential decay envelope."""
    samples = len(signal)
    attack_samples = int(SAMPLE_RATE * attack_ms / 1000)
    decay_samples = int(SAMPLE_RATE * decay_ms / 1000)

    envelope = np.ones(samples)

    # Quick attack
    if attack_samples > 0 and attack_samples < samples:
        envelope[:attack_samples] = np.linspace(0, 1, attack_samples)

    # Exponential decay starting after attack
    if decay_samples > 0:
        decay_start = attack_samples
        decay_end = min(samples, decay_start + decay_samples)
        actual_decay = decay_end - decay_start
        if actual_decay > 0:
            envelope[decay_start:decay_end] = np.exp(-np.linspace(0, 6, actual_decay))
            envelope[decay_end:] = 0

    return signal * envelope


def generate_harmonic_tone(base_freq, duration_ms, harmonics):
    """Generate a tone with specific harmonic frequencies and amplitudes."""
    samples = int(SAMPLE_RATE * duration_ms / 1000)
    t = np.linspace(0, duration_ms / 1000, samples, False)

    tone = np.zeros(samples)
    for freq, amplitude in harmonics:
        tone += amplitude * np.sin(2 * np.pi * freq * t)

    return tone
