"""Tests for sounds package top-level delegation and simple provider tone generation."""

from unittest.mock import patch

import numpy as np


class TestSoundsDelegation:
    @patch("sounds._provider")
    def test_play_start_sound_delegates_to_provider(self, mock_provider):
        from sounds import play_start_sound

        play_start_sound()

        mock_provider.play_start.assert_called_once()

    @patch("sounds._provider")
    def test_play_stop_sound_delegates_to_provider(self, mock_provider):
        from sounds import play_stop_sound

        play_stop_sound()

        mock_provider.play_stop.assert_called_once()


class TestSimpleToneGeneration:
    def test_generate_tone_returns_numpy_array(self):
        from sounds.simple import _generate_tone

        result = _generate_tone(440, 0.1)

        assert isinstance(result, np.ndarray)

    def test_generate_tone_returns_float32(self):
        from sounds.simple import _generate_tone

        result = _generate_tone(440, 0.1)

        assert result.dtype == np.float32

    def test_generate_tone_correct_length(self):
        from sounds.base import SAMPLE_RATE
        from sounds.simple import _generate_tone

        duration = 0.1
        expected_samples = int(SAMPLE_RATE * duration)

        result = _generate_tone(440, duration)

        assert len(result) == expected_samples

    def test_generate_tone_amplitude_scaled(self):
        from sounds.simple import _generate_tone

        result = _generate_tone(440, 0.5)

        assert np.max(np.abs(result)) <= 0.31

    def test_generate_tone_has_fade_in_and_out(self):
        from sounds.simple import _generate_tone

        result = _generate_tone(440, 0.5)

        assert abs(result[0]) < 0.01
        assert abs(result[-1]) < 0.01

    def test_generate_tone_different_frequencies(self):
        from sounds.simple import _generate_tone

        tone_440 = _generate_tone(440, 0.1)
        tone_880 = _generate_tone(880, 0.1)

        assert not np.array_equal(tone_440, tone_880)


class TestSimpleProviderPlayback:
    @patch("sounds.simple.sd.play")
    def test_play_start_sound_uses_correct_samplerate_and_tone(self, mock_play):
        from sounds.base import SAMPLE_RATE
        from sounds.simple import _generate_tone, play_start

        play_start()

        actual_tone = mock_play.call_args[0][0]
        expected_tone = _generate_tone(880, 0.1)
        np.testing.assert_array_almost_equal(actual_tone, expected_tone)
        assert mock_play.call_args.kwargs["samplerate"] == SAMPLE_RATE

    @patch("sounds.simple.sd.play")
    def test_play_stop_sound_uses_correct_samplerate_and_tone(self, mock_play):
        from sounds.base import SAMPLE_RATE
        from sounds.simple import _generate_tone, play_stop

        play_stop()

        actual_tone = mock_play.call_args[0][0]
        expected_tone = _generate_tone(440, 0.1)
        np.testing.assert_array_almost_equal(actual_tone, expected_tone)
        assert mock_play.call_args.kwargs["samplerate"] == SAMPLE_RATE
