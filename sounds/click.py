"""Short click sounds for minimal audio feedback."""

import numpy as np

try:
    import sounddevice as sd
except OSError:
    class _MissingSoundDevice:
        def play(self, *args, **kwargs):
            raise OSError("PortAudio library not found")

    sd = _MissingSoundDevice()

from .base import SAMPLE_RATE


def play_start():
    """Play a short click sound to indicate recording started."""
    duration_ms = 20
    samples = int(SAMPLE_RATE * duration_ms / 1000)
    t = np.linspace(0, duration_ms / 1000, samples, False)

    # Click: short burst with multiple high frequencies
    click = (
        np.sin(2 * np.pi * 1000 * t) * 0.5 +
        np.sin(2 * np.pi * 2500 * t) * 0.3 +
        np.sin(2 * np.pi * 4000 * t) * 0.2
    )

    # Sharp exponential decay
    decay = np.exp(-t * 300)
    click = click * decay

    click = click / np.max(np.abs(click))
    sound = (click * 0.4).astype(np.float32)

    sd.play(sound, samplerate=SAMPLE_RATE)


def play_stop():
    """Play a short click sound to indicate recording stopped."""
    duration_ms = 25
    samples = int(SAMPLE_RATE * duration_ms / 1000)
    t = np.linspace(0, duration_ms / 1000, samples, False)

    # Lower-pitched click for "done" feel
    click = (
        np.sin(2 * np.pi * 600 * t) * 0.5 +
        np.sin(2 * np.pi * 1500 * t) * 0.3 +
        np.sin(2 * np.pi * 2400 * t) * 0.2
    )

    # Slightly softer decay than start
    decay = np.exp(-t * 250)
    click = click * decay

    click = click / np.max(np.abs(click))
    sound = (click * 0.35).astype(np.float32)

    sd.play(sound, samplerate=SAMPLE_RATE)
