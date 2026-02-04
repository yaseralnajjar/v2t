"""Unit tests for sounds.py - audio feedback functions."""

from unittest.mock import Mock, patch
import numpy as np
import pytest


class TestGenerateTone:
    """Tests for _generate_tone() helper function."""

    @patch('sounds.sd')
    def test_generate_tone_returns_numpy_array(self, mock_sd):
        """Test that _generate_tone returns a numpy array."""
        from sounds import _generate_tone

        result = _generate_tone(440, 0.1)

        assert isinstance(result, np.ndarray)

    @patch('sounds.sd')
    def test_generate_tone_returns_float32(self, mock_sd):
        """Test that _generate_tone returns float32 dtype."""
        from sounds import _generate_tone

        result = _generate_tone(440, 0.1)

        assert result.dtype == np.float32

    @patch('sounds.sd')
    def test_generate_tone_correct_length(self, mock_sd):
        """Test that _generate_tone returns correct number of samples."""
        from sounds import _generate_tone

        duration = 0.1
        samplerate = 44100
        expected_samples = int(samplerate * duration)

        result = _generate_tone(440, duration, samplerate)

        assert len(result) == expected_samples

    @patch('sounds.sd')
    def test_generate_tone_amplitude_scaled(self, mock_sd):
        """Test that _generate_tone amplitude is scaled to 0.3."""
        from sounds import _generate_tone

        result = _generate_tone(440, 0.5)

        assert np.max(np.abs(result)) <= 0.31

    @patch('sounds.sd')
    def test_generate_tone_has_fade_in(self, mock_sd):
        """Test that _generate_tone has fade in (starts near zero)."""
        from sounds import _generate_tone

        result = _generate_tone(440, 0.5)

        assert abs(result[0]) < 0.01

    @patch('sounds.sd')
    def test_generate_tone_has_fade_out(self, mock_sd):
        """Test that _generate_tone has fade out (ends near zero)."""
        from sounds import _generate_tone

        result = _generate_tone(440, 0.5)

        assert abs(result[-1]) < 0.01

    @patch('sounds.sd')
    def test_generate_tone_different_frequencies(self, mock_sd):
        """Test that different frequencies produce different tones."""
        from sounds import _generate_tone

        tone_440 = _generate_tone(440, 0.1)
        tone_880 = _generate_tone(880, 0.1)

        assert not np.array_equal(tone_440, tone_880)


class TestPlayStartSound:
    """Tests for play_start_sound() function."""

    @patch('sounds.sd')
    def test_play_start_sound_calls_sd_play(self, mock_sd):
        """Test that play_start_sound calls sd.play."""
        from sounds import play_start_sound

        play_start_sound()

        mock_sd.play.assert_called_once()

    @patch('sounds.sd')
    def test_play_start_sound_uses_correct_samplerate(self, mock_sd):
        """Test that play_start_sound uses 44100 Hz samplerate."""
        from sounds import play_start_sound

        play_start_sound()

        call_kwargs = mock_sd.play.call_args
        assert call_kwargs.kwargs['samplerate'] == 44100

    @patch('sounds.sd')
    def test_play_start_sound_uses_880_hz(self, mock_sd):
        """Test that play_start_sound uses A5 (880 Hz) frequency."""
        from sounds import play_start_sound, _generate_tone

        expected_tone = _generate_tone(880, 0.1)
        play_start_sound()

        actual_tone = mock_sd.play.call_args[0][0]
        np.testing.assert_array_almost_equal(actual_tone, expected_tone)


class TestPlayStopSound:
    """Tests for play_stop_sound() function."""

    @patch('sounds.sd')
    def test_play_stop_sound_calls_sd_play(self, mock_sd):
        """Test that play_stop_sound calls sd.play."""
        from sounds import play_stop_sound

        play_stop_sound()

        mock_sd.play.assert_called_once()

    @patch('sounds.sd')
    def test_play_stop_sound_uses_correct_samplerate(self, mock_sd):
        """Test that play_stop_sound uses 44100 Hz samplerate."""
        from sounds import play_stop_sound

        play_stop_sound()

        call_kwargs = mock_sd.play.call_args
        assert call_kwargs.kwargs['samplerate'] == 44100

    @patch('sounds.sd')
    def test_play_stop_sound_uses_440_hz(self, mock_sd):
        """Test that play_stop_sound uses A4 (440 Hz) frequency."""
        from sounds import play_stop_sound, _generate_tone

        expected_tone = _generate_tone(440, 0.1)
        play_stop_sound()

        actual_tone = mock_sd.play.call_args[0][0]
        np.testing.assert_array_almost_equal(actual_tone, expected_tone)

    @patch('sounds.sd')
    def test_start_and_stop_sounds_are_different(self, mock_sd):
        """Test that start and stop sounds use different frequencies."""
        from sounds import play_start_sound, play_stop_sound

        play_start_sound()
        start_tone = mock_sd.play.call_args[0][0]

        mock_sd.reset_mock()

        play_stop_sound()
        stop_tone = mock_sd.play.call_args[0][0]

        assert not np.array_equal(start_tone, stop_tone)
