import os

# Model configuration
# Set V2T_MODEL environment variable to change the model
# Examples: "tiny.en", "base.en", "small.en", "medium.en", "large"
# Or provide a full path to a GGML model file
MODEL = os.environ.get("V2T_MODEL", "small.en")
