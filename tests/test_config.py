"""Tests for configuration module."""

import os
import pytest


class TestSoundConfig:
    """Tests for sound configuration."""

    def test_default_sound_type(self, monkeypatch):
        """Default sound type should be 'bloop'."""
        monkeypatch.delenv("V2T_SOUND", raising=False)
        # Need to reimport to pick up the env change
        import importlib
        import config
        importlib.reload(config)
        assert config.SOUND_TYPE == "bloop"

    def test_sound_type_from_env(self, monkeypatch):
        """Sound type should be configurable via V2T_SOUND env var."""
        monkeypatch.setenv("V2T_SOUND", "click")
        import importlib
        import config
        importlib.reload(config)
        assert config.SOUND_TYPE == "click"

    def test_sound_type_custom_value(self, monkeypatch):
        """Custom sound type values should be accepted."""
        monkeypatch.setenv("V2T_SOUND", "custom")
        import importlib
        import config
        importlib.reload(config)
        assert config.SOUND_TYPE == "custom"


class TestModelConfig:
    """Tests for model configuration."""

    def test_default_model(self, monkeypatch):
        """Default model should be 'small.en'."""
        monkeypatch.delenv("V2T_MODEL", raising=False)
        import importlib
        import config
        importlib.reload(config)
        assert config.MODEL == "small.en"

    def test_model_from_env(self, monkeypatch):
        """Model should be configurable via V2T_MODEL env var."""
        monkeypatch.setenv("V2T_MODEL", "large-v3")
        import importlib
        import config
        importlib.reload(config)
        assert config.MODEL == "large-v3"
