"""Unit tests for main.py - VoiceToTextApp class."""

import threading
import signal
import time
from unittest.mock import Mock, patch, MagicMock
import numpy as np
import pytest


class TestVoiceToTextAppInit:
    """Tests for VoiceToTextApp initialization."""

    @patch('main.AudioRecorder')
    @patch('main.AudioTranscriber')
    @patch('main.TextInjector')
    def test_init_creates_components(self, mock_injector, mock_transcriber, mock_recorder):
        """Test that __init__ creates recorder, transcriber, and injector."""
        from main import VoiceToTextApp

        app = VoiceToTextApp()

        mock_recorder.assert_called_once()
        mock_transcriber.assert_called_once()
        mock_injector.assert_called_once()

    @patch('main.AudioRecorder')
    @patch('main.AudioTranscriber')
    @patch('main.TextInjector')
    def test_init_sets_default_state(self, mock_injector, mock_transcriber, mock_recorder):
        """Test that __init__ sets correct default state."""
        from main import VoiceToTextApp

        app = VoiceToTextApp()

        assert app.is_recording is False
        assert isinstance(app.shutdown_event, threading.Event)
        assert not app.shutdown_event.is_set()

    @patch('main.AudioRecorder')
    @patch('main.AudioTranscriber')
    @patch('main.TextInjector')
    def test_init_configures_hotkey(self, mock_injector, mock_transcriber, mock_recorder):
        """Test that __init__ configures the right command key as hotkey."""
        from main import VoiceToTextApp
        from pynput import keyboard

        app = VoiceToTextApp()

        assert keyboard.Key.cmd_r in app.HOTKEY


class TestVoiceToTextAppShutdown:
    """Tests for the shutdown mechanism (main feature of this branch)."""

    @patch('main.AudioRecorder')
    @patch('main.AudioTranscriber')
    @patch('main.TextInjector')
    def test_shutdown_event_stops_run_loop(self, mock_injector, mock_transcriber, mock_recorder):
        """Test that setting shutdown_event causes run() to exit."""
        from main import VoiceToTextApp

        app = VoiceToTextApp()
        app.recorder.get_input_device_info.return_value = "Test Device"
        app.transcriber.get_model_name.return_value = "test.en"

        def set_shutdown():
            time.sleep(0.2)
            app.shutdown_event.set()

        shutdown_thread = threading.Thread(target=set_shutdown)
        shutdown_thread.start()

        with patch('main.keyboard.Listener') as mock_listener:
            mock_listener_instance = MagicMock()
            mock_listener.return_value = mock_listener_instance

            app.run()

        shutdown_thread.join()
        mock_listener_instance.stop.assert_called_once()

    @patch('main.AudioRecorder')
    @patch('main.AudioTranscriber')
    @patch('main.TextInjector')
    def test_shutdown_stops_recording_if_active(self, mock_injector, mock_transcriber, mock_recorder):
        """Test that shutdown stops recording if recording is in progress."""
        from main import VoiceToTextApp

        app = VoiceToTextApp()
        app.recorder.get_input_device_info.return_value = "Test Device"
        app.transcriber.get_model_name.return_value = "test.en"

        def set_recording_and_shutdown():
            time.sleep(0.1)
            app.is_recording = True
            time.sleep(0.1)
            app.shutdown_event.set()

        thread = threading.Thread(target=set_recording_and_shutdown)
        thread.start()

        with patch('main.keyboard.Listener') as mock_listener:
            mock_listener_instance = MagicMock()
            mock_listener.return_value = mock_listener_instance

            app.run()

        thread.join()
        app.recorder.stop.assert_called()

    @patch('main.AudioRecorder')
    @patch('main.AudioTranscriber')
    @patch('main.TextInjector')
    def test_shutdown_event_is_thread_safe(self, mock_injector, mock_transcriber, mock_recorder):
        """Test that shutdown_event can be safely set from another thread."""
        from main import VoiceToTextApp

        app = VoiceToTextApp()

        results = []

        def check_and_set():
            time.sleep(0.05)
            results.append(app.shutdown_event.is_set())
            app.shutdown_event.set()
            results.append(app.shutdown_event.is_set())

        thread = threading.Thread(target=check_and_set)
        thread.start()
        thread.join()

        assert results == [False, True]


class TestVoiceToTextAppRecording:
    """Tests for recording start/stop functionality."""

    @patch('main.AudioRecorder')
    @patch('main.AudioTranscriber')
    @patch('main.TextInjector')
    @patch('main.play_start_sound')
    def test_start_recording_plays_sound(self, mock_play_start, mock_injector, mock_transcriber, mock_recorder):
        """Test that start_recording plays the start sound."""
        from main import VoiceToTextApp

        app = VoiceToTextApp()
        app.start_recording()

        mock_play_start.assert_called_once()

    @patch('main.AudioRecorder')
    @patch('main.AudioTranscriber')
    @patch('main.TextInjector')
    @patch('main.play_start_sound')
    def test_start_recording_sets_flag(self, mock_play_start, mock_injector, mock_transcriber, mock_recorder):
        """Test that start_recording sets is_recording to True."""
        from main import VoiceToTextApp

        app = VoiceToTextApp()
        assert app.is_recording is False

        app.start_recording()

        assert app.is_recording is True

    @patch('main.AudioRecorder')
    @patch('main.AudioTranscriber')
    @patch('main.TextInjector')
    @patch('main.play_start_sound')
    def test_start_recording_starts_recorder(self, mock_play_start, mock_injector, mock_transcriber, mock_recorder):
        """Test that start_recording calls recorder.start()."""
        from main import VoiceToTextApp

        app = VoiceToTextApp()
        app.start_recording()

        app.recorder.start.assert_called_once()

    @patch('main.AudioRecorder')
    @patch('main.AudioTranscriber')
    @patch('main.TextInjector')
    @patch('main.play_stop_sound')
    def test_stop_recording_plays_sound(self, mock_play_stop, mock_injector, mock_transcriber, mock_recorder):
        """Test that stop_recording_and_transcribe plays the stop sound."""
        from main import VoiceToTextApp

        app = VoiceToTextApp()
        app.is_recording = True
        app.recorder.stop.return_value = np.array([])

        app.stop_recording_and_transcribe()

        mock_play_stop.assert_called_once()

    @patch('main.AudioRecorder')
    @patch('main.AudioTranscriber')
    @patch('main.TextInjector')
    @patch('main.play_stop_sound')
    def test_stop_recording_clears_flag(self, mock_play_stop, mock_injector, mock_transcriber, mock_recorder):
        """Test that stop_recording_and_transcribe sets is_recording to False."""
        from main import VoiceToTextApp

        app = VoiceToTextApp()
        app.is_recording = True
        app.recorder.stop.return_value = np.array([])

        app.stop_recording_and_transcribe()

        assert app.is_recording is False

    @patch('main.AudioRecorder')
    @patch('main.AudioTranscriber')
    @patch('main.TextInjector')
    @patch('main.play_stop_sound')
    def test_stop_recording_handles_empty_audio(self, mock_play_stop, mock_injector, mock_transcriber, mock_recorder):
        """Test that stop_recording_and_transcribe handles empty audio gracefully."""
        from main import VoiceToTextApp

        app = VoiceToTextApp()
        app.is_recording = True
        app.recorder.stop.return_value = np.array([])

        app.stop_recording_and_transcribe()

        app.transcriber.transcribe.assert_not_called()


class TestVoiceToTextAppHotkeyHandling:
    """Tests for hotkey press/release handling."""

    @patch('main.AudioRecorder')
    @patch('main.AudioTranscriber')
    @patch('main.TextInjector')
    @patch('main.play_start_sound')
    def test_on_press_hotkey_starts_recording_when_not_recording(
        self, mock_play_start, mock_injector, mock_transcriber, mock_recorder
    ):
        """Test that pressing hotkey when not recording starts recording."""
        from main import VoiceToTextApp
        from pynput import keyboard

        app = VoiceToTextApp()
        assert app.is_recording is False

        app.on_press(keyboard.Key.cmd_r)

        assert app.is_recording is True

    @patch('main.AudioRecorder')
    @patch('main.AudioTranscriber')
    @patch('main.TextInjector')
    @patch('main.play_start_sound')
    @patch('main.play_stop_sound')
    def test_on_press_hotkey_stops_recording_when_recording(
        self, mock_play_stop, mock_play_start, mock_injector, mock_transcriber, mock_recorder
    ):
        """Test that pressing hotkey when recording stops recording."""
        from main import VoiceToTextApp
        from pynput import keyboard

        app = VoiceToTextApp()
        app.recorder.stop.return_value = np.array([])

        app.on_press(keyboard.Key.cmd_r)
        assert app.is_recording is True

        app.on_press(keyboard.Key.cmd_r)
        assert app.is_recording is False

    @patch('main.AudioRecorder')
    @patch('main.AudioTranscriber')
    @patch('main.TextInjector')
    def test_on_press_non_hotkey_does_nothing(self, mock_injector, mock_transcriber, mock_recorder):
        """Test that pressing non-hotkey key does nothing."""
        from main import VoiceToTextApp
        from pynput import keyboard

        app = VoiceToTextApp()

        app.on_press(keyboard.Key.space)

        assert app.is_recording is False
        app.recorder.start.assert_not_called()


class TestProcessAudio:
    """Tests for audio processing thread."""

    @patch('main.AudioRecorder')
    @patch('main.AudioTranscriber')
    @patch('main.TextInjector')
    def test_process_audio_transcribes_and_injects(self, mock_injector, mock_transcriber, mock_recorder):
        """Test that _process_audio transcribes audio and injects text."""
        from main import VoiceToTextApp

        app = VoiceToTextApp()
        app.transcriber.transcribe.return_value = "hello world"

        audio_data = np.array([0.1, 0.2, 0.3])
        app._process_audio(audio_data)

        app.transcriber.transcribe.assert_called_once_with(audio_data)
        app.injector.type_text.assert_called_once_with("hello world")

    @patch('main.AudioRecorder')
    @patch('main.AudioTranscriber')
    @patch('main.TextInjector')
    def test_process_audio_skips_empty_transcription(self, mock_injector, mock_transcriber, mock_recorder):
        """Test that _process_audio doesn't inject empty text."""
        from main import VoiceToTextApp

        app = VoiceToTextApp()
        app.transcriber.transcribe.return_value = ""

        audio_data = np.array([0.1, 0.2, 0.3])
        app._process_audio(audio_data)

        app.injector.type_text.assert_not_called()

    @patch('main.AudioRecorder')
    @patch('main.AudioTranscriber')
    @patch('main.TextInjector')
    def test_process_audio_handles_exception(self, mock_injector, mock_transcriber, mock_recorder):
        """Test that _process_audio handles exceptions gracefully."""
        from main import VoiceToTextApp

        app = VoiceToTextApp()
        app.transcriber.transcribe.side_effect = Exception("Test error")

        audio_data = np.array([0.1, 0.2, 0.3])
        app._process_audio(audio_data)

        app.injector.type_text.assert_not_called()

    @patch('main.AudioRecorder')
    @patch('main.AudioTranscriber')
    @patch('main.TextInjector')
    @patch('main.play_stop_sound')
    def test_audio_processing_runs_in_daemon_thread(self, mock_play_stop, mock_injector, mock_transcriber, mock_recorder):
        """Test that audio processing thread is a daemon thread."""
        from main import VoiceToTextApp

        app = VoiceToTextApp()
        app.is_recording = True
        app.recorder.stop.return_value = np.array([0.1, 0.2, 0.3])

        threads_before = threading.enumerate()

        with patch('main.threading.Thread') as mock_thread:
            mock_thread_instance = MagicMock()
            mock_thread.return_value = mock_thread_instance

            app.stop_recording_and_transcribe()

            mock_thread.assert_called_once()
            call_kwargs = mock_thread.call_args
            assert call_kwargs.kwargs.get('daemon') is True


class TestSignalHandler:
    """Tests for signal handling (SIGINT/Ctrl+C)."""

    @patch('main.AudioRecorder')
    @patch('main.AudioTranscriber')
    @patch('main.TextInjector')
    def test_signal_handler_sets_shutdown_event(self, mock_injector, mock_transcriber, mock_recorder):
        """Test that the signal handler sets the shutdown event."""
        from main import VoiceToTextApp

        app = VoiceToTextApp()

        def signal_handler(signum, frame):
            app.shutdown_event.set()

        assert not app.shutdown_event.is_set()
        signal_handler(signal.SIGINT, None)
        assert app.shutdown_event.is_set()

    @patch('main.AudioRecorder')
    @patch('main.AudioTranscriber')
    @patch('main.TextInjector')
    def test_sigint_exits_run_loop(self, mock_injector, mock_transcriber, mock_recorder):
        """Test that SIGINT (Ctrl+C) causes the app to exit gracefully.

        This is the key test for the fix/ctrl-c-hang branch - it verifies that
        sending SIGINT to the process actually causes run() to exit.
        """
        import os
        from main import VoiceToTextApp

        app = VoiceToTextApp()
        app.recorder.get_input_device_info.return_value = "Test Device"
        app.transcriber.get_model_name.return_value = "test.en"

        # Register signal handler the same way __main__ does
        def signal_handler(signum, frame):
            app.shutdown_event.set()

        original_handler = signal.signal(signal.SIGINT, signal_handler)

        def send_sigint():
            time.sleep(0.2)
            os.kill(os.getpid(), signal.SIGINT)

        sigint_thread = threading.Thread(target=send_sigint)
        sigint_thread.start()

        try:
            with patch('main.keyboard.Listener') as mock_listener:
                mock_listener_instance = MagicMock()
                mock_listener.return_value = mock_listener_instance

                # This should exit when SIGINT is received
                app.run()

            # If we get here, the signal handler worked
            assert app.shutdown_event.is_set()
            mock_listener_instance.stop.assert_called_once()
        finally:
            signal.signal(signal.SIGINT, original_handler)
            sigint_thread.join()
