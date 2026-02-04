"""
Audio feedback sounds for voice-to-text.

To add a new sound type:
1. Create a new file in this directory (e.g., mysound.py)
2. Implement play_start() and play_stop() functions
3. Add it to SOUND_PROVIDERS below

Select sound type via V2T_SOUND environment variable.
"""

from importlib import import_module

from config import SOUND_TYPE

# Registry of available sound providers
# Maps V2T_SOUND value -> module name
SOUND_PROVIDERS = {
    "bloop": "bloop",
    "warm": "warm",
    "simple": "simple",
    "click": "click",
}


def _get_provider():
    """Load the sound provider module based on config."""
    module_name = SOUND_PROVIDERS.get(SOUND_TYPE, "bloop")
    return import_module(f".{module_name}", package=__name__)


_provider = _get_provider()


def play_start_sound():
    """Play the start/activation sound."""
    _provider.play_start()


def play_stop_sound():
    """Play the stop/confirmation sound."""
    _provider.play_stop()
