"""Unit tests for recorder.py - AudioRecorder class."""

import threading
import queue
from unittest.mock import Mock, patch, MagicMock
import numpy as np
import pytest


class TestAudioRecorderInit:
    """Tests for AudioRecorder initialization."""

    @patch('recorder.sd')
    def test_init_sets_default_samplerate(self, mock_sd):
        """Test that __init__ sets default samplerate to 16000."""
        from recorder import AudioRecorder

        recorder = AudioRecorder()

        assert recorder.samplerate == 16000

    @patch('recorder.sd')
    def test_init_sets_default_channels(self, mock_sd):
        """Test that __init__ sets default channels to 1 (mono)."""
        from recorder import AudioRecorder

        recorder = AudioRecorder()

        assert recorder.channels == 1

    @patch('recorder.sd')
    def test_init_with_custom_samplerate(self, mock_sd):
        """Test that __init__ accepts custom samplerate."""
        from recorder import AudioRecorder

        recorder = AudioRecorder(samplerate=44100)

        assert recorder.samplerate == 44100

    @patch('recorder.sd')
    def test_init_with_custom_channels(self, mock_sd):
        """Test that __init__ accepts custom channels."""
        from recorder import AudioRecorder

        recorder = AudioRecorder(channels=2)

        assert recorder.channels == 2

    @patch('recorder.sd')
    def test_init_creates_queue(self, mock_sd):
        """Test that __init__ creates a queue for audio data."""
        from recorder import AudioRecorder

        recorder = AudioRecorder()

        assert isinstance(recorder.q, queue.Queue)

    @patch('recorder.sd')
    def test_init_sets_recording_false(self, mock_sd):
        """Test that __init__ sets recording to False."""
        from recorder import AudioRecorder

        recorder = AudioRecorder()

        assert recorder.recording is False


class TestAudioRecorderStart:
    """Tests for AudioRecorder.start() method."""

    @patch('recorder.sd')
    def test_start_sets_recording_true(self, mock_sd):
        """Test that start() sets recording flag to True."""
        from recorder import AudioRecorder

        recorder = AudioRecorder()
        recorder.start()

        assert recorder.recording is True

    @patch('recorder.sd')
    def test_start_clears_queue(self, mock_sd):
        """Test that start() clears any existing data in queue."""
        from recorder import AudioRecorder

        recorder = AudioRecorder()
        recorder.q.put(np.array([1, 2, 3]))

        recorder.start()

        assert recorder.q.empty()

    @patch('recorder.sd')
    def test_start_creates_input_stream(self, mock_sd):
        """Test that start() creates an InputStream with correct parameters."""
        from recorder import AudioRecorder

        recorder = AudioRecorder(samplerate=16000, channels=1)
        recorder.start()

        mock_sd.InputStream.assert_called_once()
        call_kwargs = mock_sd.InputStream.call_args.kwargs
        assert call_kwargs['samplerate'] == 16000
        assert call_kwargs['channels'] == 1

    @patch('recorder.sd')
    def test_start_starts_stream(self, mock_sd):
        """Test that start() starts the audio stream."""
        from recorder import AudioRecorder

        mock_stream = MagicMock()
        mock_sd.InputStream.return_value = mock_stream

        recorder = AudioRecorder()
        recorder.start()

        mock_stream.start.assert_called_once()

    @patch('recorder.sd')
    def test_start_does_nothing_if_already_recording(self, mock_sd):
        """Test that start() is idempotent when already recording."""
        from recorder import AudioRecorder

        recorder = AudioRecorder()
        recorder.start()
        mock_sd.InputStream.reset_mock()

        recorder.start()

        mock_sd.InputStream.assert_not_called()


class TestAudioRecorderStop:
    """Tests for AudioRecorder.stop() method."""

    @patch('recorder.sd')
    def test_stop_sets_recording_false(self, mock_sd):
        """Test that stop() sets recording flag to False."""
        from recorder import AudioRecorder

        mock_stream = MagicMock()
        mock_sd.InputStream.return_value = mock_stream

        recorder = AudioRecorder()
        recorder.start()
        recorder.stop()

        assert recorder.recording is False

    @patch('recorder.sd')
    def test_stop_stops_stream(self, mock_sd):
        """Test that stop() stops the audio stream."""
        from recorder import AudioRecorder

        mock_stream = MagicMock()
        mock_sd.InputStream.return_value = mock_stream

        recorder = AudioRecorder()
        recorder.start()
        recorder.stop()

        mock_stream.stop.assert_called_once()

    @patch('recorder.sd')
    def test_stop_closes_stream(self, mock_sd):
        """Test that stop() closes the audio stream."""
        from recorder import AudioRecorder

        mock_stream = MagicMock()
        mock_sd.InputStream.return_value = mock_stream

        recorder = AudioRecorder()
        recorder.start()
        recorder.stop()

        mock_stream.close.assert_called_once()

    @patch('recorder.sd')
    def test_stop_returns_empty_array_when_not_recording(self, mock_sd):
        """Test that stop() returns empty array if not recording."""
        from recorder import AudioRecorder

        recorder = AudioRecorder()
        result = recorder.stop()

        assert isinstance(result, np.ndarray)
        assert len(result) == 0

    @patch('recorder.sd')
    def test_stop_returns_concatenated_audio_data(self, mock_sd):
        """Test that stop() returns concatenated audio from queue."""
        from recorder import AudioRecorder

        mock_stream = MagicMock()
        mock_sd.InputStream.return_value = mock_stream

        recorder = AudioRecorder()
        recorder.start()

        recorder.q.put(np.array([[0.1], [0.2]]))
        recorder.q.put(np.array([[0.3], [0.4]]))

        result = recorder.stop()

        expected = np.array([[0.1], [0.2], [0.3], [0.4]])
        np.testing.assert_array_equal(result, expected)

    @patch('recorder.sd')
    def test_stop_returns_empty_array_when_queue_empty(self, mock_sd):
        """Test that stop() returns empty array when no audio recorded."""
        from recorder import AudioRecorder

        mock_stream = MagicMock()
        mock_sd.InputStream.return_value = mock_stream

        recorder = AudioRecorder()
        recorder.start()
        result = recorder.stop()

        assert isinstance(result, np.ndarray)
        assert len(result) == 0

    @patch('recorder.sd')
    def test_stop_sets_stream_to_none(self, mock_sd):
        """Test that stop() sets stream to None."""
        from recorder import AudioRecorder

        mock_stream = MagicMock()
        mock_sd.InputStream.return_value = mock_stream

        recorder = AudioRecorder()
        recorder.start()
        assert recorder.stream is not None

        recorder.stop()

        assert recorder.stream is None


class TestAudioRecorderCallback:
    """Tests for AudioRecorder._callback() method."""

    @patch('recorder.sd')
    def test_callback_puts_data_in_queue_when_recording(self, mock_sd):
        """Test that callback puts audio data in queue when recording."""
        from recorder import AudioRecorder

        recorder = AudioRecorder()
        recorder.recording = True

        indata = np.array([[0.1], [0.2], [0.3]])
        recorder._callback(indata, 3, None, None)

        assert not recorder.q.empty()
        queued_data = recorder.q.get()
        np.testing.assert_array_equal(queued_data, indata)

    @patch('recorder.sd')
    def test_callback_does_not_queue_when_not_recording(self, mock_sd):
        """Test that callback ignores data when not recording."""
        from recorder import AudioRecorder

        recorder = AudioRecorder()
        recorder.recording = False

        indata = np.array([[0.1], [0.2], [0.3]])
        recorder._callback(indata, 3, None, None)

        assert recorder.q.empty()

    @patch('recorder.sd')
    def test_callback_copies_data(self, mock_sd):
        """Test that callback stores a copy of the data."""
        from recorder import AudioRecorder

        recorder = AudioRecorder()
        recorder.recording = True

        indata = np.array([[0.1], [0.2], [0.3]])
        recorder._callback(indata, 3, None, None)

        queued_data = recorder.q.get()

        indata[0, 0] = 999
        assert queued_data[0, 0] != 999


class TestAudioRecorderGetInputDeviceInfo:
    """Tests for AudioRecorder.get_input_device_info() method."""

    @patch('recorder.sd')
    def test_get_input_device_info_returns_device_name(self, mock_sd):
        """Test that get_input_device_info returns the device name."""
        from recorder import AudioRecorder

        mock_sd.query_devices.return_value = {'name': 'MacBook Pro Microphone'}

        recorder = AudioRecorder()
        result = recorder.get_input_device_info()

        assert result == 'MacBook Pro Microphone'
        mock_sd.query_devices.assert_called_once_with(kind='input')

    @patch('recorder.sd')
    def test_get_input_device_info_handles_exception(self, mock_sd):
        """Test that get_input_device_info handles errors gracefully."""
        from recorder import AudioRecorder

        mock_sd.query_devices.side_effect = Exception("No device")

        recorder = AudioRecorder()
        result = recorder.get_input_device_info()

        assert "Unknown" in result
        assert "No device" in result
