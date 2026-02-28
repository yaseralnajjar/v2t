import os

# Model configuration
# Set V2T_MODEL environment variable to change the model
# Examples: "tiny.en", "base.en", "small.en", "medium.en", "large"
# Or provide a full path to a GGML model file
MODEL = os.environ.get("V2T_MODEL", "small.en")

# Sound configuration
# Set V2T_SOUND to choose sound type:
#   "bloop" (default) - bloop sound effects from wav files
#   "warm" - warm bloop tones with rich harmonics
#   "simple" - simple sine wave tones (880Hz/440Hz)
#   "click" - short click sounds
SOUND_TYPE = os.environ.get("V2T_SOUND", "bloop")

# Platform configuration
# "auto" uses the current OS. Explicit values are useful for testing backend selection.
PLATFORM_BACKEND = os.environ.get("V2T_PLATFORM_BACKEND", "auto")
INJECT_MODE = os.environ.get("V2T_INJECT_MODE", "auto")
HOTKEY_BACKEND = os.environ.get("V2T_HOTKEY_BACKEND", "auto")
LINUX_SESSION = os.environ.get("V2T_LINUX_SESSION", "")
ALLOW_DEGRADED_MODE = os.environ.get("V2T_ALLOW_DEGRADED_MODE", "0")
