"""Tests for sounds.base module."""

import numpy as np
import pytest

from sounds.base import SAMPLE_RATE, apply_envelope, generate_harmonic_tone


class TestSampleRate:
    def test_sample_rate_is_standard(self):
        """Sample rate should be CD quality (44100 Hz)."""
        assert SAMPLE_RATE == 44100


class TestApplyEnvelope:
    def test_returns_same_length(self):
        """Envelope should not change signal length."""
        signal = np.ones(1000)
        result = apply_envelope(signal)
        assert len(result) == len(signal)

    def test_attack_starts_at_zero(self):
        """Signal should start at zero with attack envelope."""
        signal = np.ones(1000)
        result = apply_envelope(signal, attack_ms=10)
        assert result[0] == pytest.approx(0, abs=0.01)

    def test_decay_ends_at_zero(self):
        """Signal should end at zero after decay."""
        signal = np.ones(1000)
        result = apply_envelope(signal, attack_ms=5, decay_ms=20)
        assert result[-1] == pytest.approx(0, abs=0.01)

    def test_envelope_modifies_signal(self):
        """Envelope should modify the original signal."""
        signal = np.ones(1000)
        result = apply_envelope(signal, attack_ms=5, decay_ms=50)
        assert not np.array_equal(result, signal)

    def test_zero_attack_no_fade_in(self):
        """Zero attack should not add fade in."""
        signal = np.ones(1000)
        result = apply_envelope(signal, attack_ms=0, decay_ms=0)
        # With no attack and no decay, signal should be unchanged
        assert result[0] == pytest.approx(1.0, abs=0.01)

    def test_short_signal_handled(self):
        """Very short signals should not cause errors."""
        signal = np.ones(10)
        result = apply_envelope(signal, attack_ms=100, decay_ms=100)
        assert len(result) == 10


class TestGenerateHarmonicTone:
    def test_returns_correct_length(self):
        """Generated tone should have correct number of samples."""
        duration_ms = 100
        expected_samples = int(SAMPLE_RATE * duration_ms / 1000)
        harmonics = [(440, 1.0)]
        result = generate_harmonic_tone(440, duration_ms, harmonics)
        assert len(result) == expected_samples

    def test_single_harmonic_generates_sine(self):
        """Single harmonic should generate a sine wave."""
        harmonics = [(440, 1.0)]
        result = generate_harmonic_tone(440, 100, harmonics)
        # Check that it oscillates (has positive and negative values)
        assert np.any(result > 0)
        assert np.any(result < 0)

    def test_multiple_harmonics_combined(self):
        """Multiple harmonics should be combined."""
        single = generate_harmonic_tone(440, 100, [(440, 1.0)])
        double = generate_harmonic_tone(440, 100, [(440, 1.0), (880, 0.5)])
        # Combined signal should be different
        assert not np.array_equal(single, double)

    def test_amplitude_scaling(self):
        """Amplitude parameter should scale the harmonic."""
        quiet = generate_harmonic_tone(440, 100, [(440, 0.1)])
        loud = generate_harmonic_tone(440, 100, [(440, 1.0)])
        assert np.max(np.abs(loud)) > np.max(np.abs(quiet))

    def test_empty_harmonics_returns_zeros(self):
        """Empty harmonics list should return zeros."""
        result = generate_harmonic_tone(440, 100, [])
        assert np.all(result == 0)

    def test_zero_duration_returns_empty(self):
        """Zero duration should return empty array."""
        result = generate_harmonic_tone(440, 0, [(440, 1.0)])
        assert len(result) == 0
