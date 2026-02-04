"""Tests for sounds package registry and configuration."""

import pytest
from importlib import import_module

from sounds import SOUND_PROVIDERS


class TestSoundProviders:
    """Tests for the sound provider registry."""

    def test_all_providers_registered(self):
        """All expected providers should be in the registry."""
        expected = {"bloop", "warm", "simple", "click"}
        assert set(SOUND_PROVIDERS.keys()) == expected

    def test_default_provider_exists(self):
        """Default provider (bloop) should exist."""
        assert "bloop" in SOUND_PROVIDERS

    @pytest.mark.parametrize("name", ["bloop", "warm", "simple", "click"])
    def test_provider_module_exists(self, name):
        """Each registered provider module should be importable."""
        module = import_module(f"sounds.{SOUND_PROVIDERS[name]}")
        assert module is not None

    @pytest.mark.parametrize("name", ["bloop", "warm", "simple", "click"])
    def test_provider_has_required_functions(self, name):
        """Each provider module should have play_start and play_stop."""
        module = import_module(f"sounds.{SOUND_PROVIDERS[name]}")
        assert hasattr(module, "play_start")
        assert hasattr(module, "play_stop")
        assert callable(module.play_start)
        assert callable(module.play_stop)


class TestSoundsPackageExports:
    """Tests for the sounds package public interface."""

    def test_exports_play_start_sound(self):
        """Package should export play_start_sound function."""
        from sounds import play_start_sound
        assert callable(play_start_sound)

    def test_exports_play_stop_sound(self):
        """Package should export play_stop_sound function."""
        from sounds import play_stop_sound
        assert callable(play_stop_sound)

    def test_exports_sound_providers(self):
        """Package should export SOUND_PROVIDERS dict."""
        from sounds import SOUND_PROVIDERS
        assert isinstance(SOUND_PROVIDERS, dict)
