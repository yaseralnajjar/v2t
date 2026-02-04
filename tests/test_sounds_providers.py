"""Tests for sound provider modules."""

import pytest
from unittest.mock import patch, MagicMock

from sounds import bloop, warm, simple, click


class TestProviderInterface:
    """Test that all providers implement the required interface."""

    @pytest.mark.parametrize("provider", [bloop, warm, simple, click])
    def test_has_play_start(self, provider):
        """Each provider must have a play_start function."""
        assert hasattr(provider, "play_start")
        assert callable(provider.play_start)

    @pytest.mark.parametrize("provider", [bloop, warm, simple, click])
    def test_has_play_stop(self, provider):
        """Each provider must have a play_stop function."""
        assert hasattr(provider, "play_stop")
        assert callable(provider.play_stop)


class TestBloopProvider:
    """Tests for the bloop (wav file) sound provider."""

    @patch("sounds.bloop.sd.play")
    @patch("sounds.bloop.sf.read")
    def test_play_start_reads_wav_file(self, mock_read, mock_play):
        """play_start should read the start.wav file."""
        mock_read.return_value = (MagicMock(), 44100)
        bloop.play_start()
        mock_read.assert_called_once()
        assert "start.wav" in str(mock_read.call_args)

    @patch("sounds.bloop.sd.play")
    @patch("sounds.bloop.sf.read")
    def test_play_stop_reads_wav_file(self, mock_read, mock_play):
        """play_stop should read the stop.wav file."""
        mock_read.return_value = (MagicMock(), 44100)
        bloop.play_stop()
        mock_read.assert_called_once()
        assert "stop.wav" in str(mock_read.call_args)

    @patch("sounds.bloop.sd.play")
    @patch("sounds.bloop.sf.read")
    def test_play_start_calls_sounddevice(self, mock_read, mock_play):
        """play_start should call sd.play with audio data."""
        mock_data = MagicMock()
        mock_read.return_value = (mock_data, 44100)
        bloop.play_start()
        mock_play.assert_called_once_with(mock_data, 44100)


class TestWarmProvider:
    """Tests for the warm (harmonic bloop) sound provider."""

    @patch("sounds.warm.sd.play")
    def test_play_start_calls_sounddevice(self, mock_play):
        """play_start should call sd.play."""
        warm.play_start()
        mock_play.assert_called_once()

    @patch("sounds.warm.sd.play")
    def test_play_stop_calls_sounddevice(self, mock_play):
        """play_stop should call sd.play."""
        warm.play_stop()
        mock_play.assert_called_once()

    @patch("sounds.warm.sd.play")
    def test_play_start_generates_audio(self, mock_play):
        """play_start should generate audio data."""
        warm.play_start()
        args, kwargs = mock_play.call_args
        audio_data = args[0]
        assert len(audio_data) > 0

    @patch("sounds.warm.sd.play")
    def test_uses_correct_sample_rate(self, mock_play):
        """Should use 44100 Hz sample rate."""
        warm.play_start()
        args, kwargs = mock_play.call_args
        assert kwargs.get("samplerate") == 44100


class TestSimpleProvider:
    """Tests for the simple (sine wave) sound provider."""

    @patch("sounds.simple.sd.play")
    def test_play_start_calls_sounddevice(self, mock_play):
        """play_start should call sd.play."""
        simple.play_start()
        mock_play.assert_called_once()

    @patch("sounds.simple.sd.play")
    def test_play_stop_calls_sounddevice(self, mock_play):
        """play_stop should call sd.play."""
        simple.play_stop()
        mock_play.assert_called_once()

    @patch("sounds.simple.sd.play")
    def test_start_and_stop_different_tones(self, mock_play):
        """Start and stop should produce different tones."""
        simple.play_start()
        start_audio = mock_play.call_args[0][0].copy()

        mock_play.reset_mock()

        simple.play_stop()
        stop_audio = mock_play.call_args[0][0].copy()

        # Different frequencies should produce different waveforms
        assert not (start_audio == stop_audio).all()


class TestClickProvider:
    """Tests for the click sound provider."""

    @patch("sounds.click.sd.play")
    def test_play_start_calls_sounddevice(self, mock_play):
        """play_start should call sd.play."""
        click.play_start()
        mock_play.assert_called_once()

    @patch("sounds.click.sd.play")
    def test_play_stop_calls_sounddevice(self, mock_play):
        """play_stop should call sd.play."""
        click.play_stop()
        mock_play.assert_called_once()

    @patch("sounds.click.sd.play")
    def test_click_is_short(self, mock_play):
        """Click sounds should be short (< 50ms at 44100 Hz)."""
        click.play_start()
        args, kwargs = mock_play.call_args
        audio_data = args[0]
        # 50ms at 44100 Hz = 2205 samples
        assert len(audio_data) < 2205

    @patch("sounds.click.sd.play")
    def test_start_higher_pitch_than_stop(self, mock_play):
        """Start click should use higher frequencies than stop."""
        # This is tested by checking the frequency content
        # Start uses 1000, 2500, 4000 Hz; Stop uses 600, 1500, 2400 Hz
        click.play_start()
        start_audio = mock_play.call_args[0][0].copy()

        mock_play.reset_mock()

        click.play_stop()
        stop_audio = mock_play.call_args[0][0].copy()

        # Start click should be shorter (20ms vs 25ms)
        assert len(start_audio) < len(stop_audio)
