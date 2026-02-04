"""Sound provider using wav files from assets/sounds/."""

import os
import sounddevice as sd
import soundfile as sf

ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "sounds")


def play_start():
    """Play the start sound from wav file."""
    data, samplerate = sf.read(os.path.join(ASSETS_DIR, "start.wav"))
    sd.play(data, samplerate)


def play_stop():
    """Play the stop sound from wav file."""
    data, samplerate = sf.read(os.path.join(ASSETS_DIR, "stop.wav"))
    sd.play(data, samplerate)
