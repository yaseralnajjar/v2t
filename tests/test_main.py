"""Unit tests for main.py - VoiceToTextApp class."""

import threading
import signal
import time
import os
from unittest.mock import Mock, patch, MagicMock
import numpy as np
import pytest
from backends.base import PlatformCapabilities


def _set_command_hotkey_backend(app):
    from pynput import keyboard

    backend = MagicMock()
    backend.supported = True
    backend.label = "Right Command"
    backend.key_name = "cmd_r"
    backend.is_hotkey.side_effect = lambda key: key == keyboard.Key.cmd_r or getattr(getattr(key, "value", None), "vk", None) == 54
    backend.key_id.side_effect = lambda key: getattr(getattr(key, "value", None), "vk", key)
    app.hotkeys = backend
    app.hotkey_label = backend.label


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
    def test_init_configures_hotkey_backend(self, mock_injector, mock_transcriber, mock_recorder):
        """Test that __init__ configures a hotkey backend."""
        from main import VoiceToTextApp

        app = VoiceToTextApp()

        assert hasattr(app.hotkeys, "is_hotkey")
        assert app.hotkey_label

    @patch('main.AudioRecorder')
    @patch('main.AudioTranscriber')
    @patch('main.TextInjector')
    def test_init_default_mode_is_push_to_talk(self, mock_injector, mock_transcriber, mock_recorder):
        """Test that default mode is push_to_talk."""
        from main import VoiceToTextApp

        app = VoiceToTextApp()

        assert app.mode == "push_to_talk"

    @patch.dict(os.environ, {"V2T_MODE": "push_to_talk"})
    @patch('main.AudioRecorder')
    @patch('main.AudioTranscriber')
    @patch('main.TextInjector')
    def test_init_push_to_talk_mode(self, mock_injector, mock_transcriber, mock_recorder):
        """Test that V2T_MODE=push_to_talk sets push_to_talk mode."""
        from main import VoiceToTextApp

        app = VoiceToTextApp()

        assert app.mode == "push_to_talk"

    @patch.dict(os.environ, {"V2T_MODE": "ptt"})
    @patch('main.AudioRecorder')
    @patch('main.AudioTranscriber')
    @patch('main.TextInjector')
    def test_init_ptt_alias(self, mock_injector, mock_transcriber, mock_recorder):
        """Test that V2T_MODE=ptt is alias for push_to_talk."""
        from main import VoiceToTextApp

        app = VoiceToTextApp()

        assert app.mode == "push_to_talk"

    @patch.dict(os.environ, {"V2T_MODE": "invalid"})
    @patch('main.AudioRecorder')
    @patch('main.AudioTranscriber')
    @patch('main.TextInjector')
    def test_init_invalid_mode_falls_back_to_push_to_talk(self, mock_injector, mock_transcriber, mock_recorder):
        """Test that invalid V2T_MODE falls back to push_to_talk."""
        from main import VoiceToTextApp

        app = VoiceToTextApp()

        assert app.mode == "push_to_talk"


class TestVoiceToTextAppShutdown:
    """Tests for the shutdown mechanism."""

    @patch('main.AudioRecorder')
    @patch('main.AudioTranscriber')
    @patch('main.TextInjector')
    def test_shutdown_event_stops_run_loop(self, mock_injector, mock_transcriber, mock_recorder):
        """Test that setting shutdown_event causes run() to exit."""
        from main import VoiceToTextApp

        app = VoiceToTextApp()
        app.recorder.get_input_device_info.return_value = "Test Device"
        app.transcriber.get_model_name.return_value = "test.en"
        app.capabilities = PlatformCapabilities(True, True, True, True)

        def set_shutdown():
            time.sleep(0.2)
            app.shutdown_event.set()

        shutdown_thread = threading.Thread(target=set_shutdown)
        shutdown_thread.start()

        mock_listener_instance = MagicMock()
        app.hotkeys = MagicMock()
        app.hotkeys.create_listener.return_value = mock_listener_instance
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
        app.capabilities = PlatformCapabilities(True, True, True, True)

        def set_recording_and_shutdown():
            time.sleep(0.1)
            app.is_recording = True
            time.sleep(0.1)
            app.shutdown_event.set()

        thread = threading.Thread(target=set_recording_and_shutdown)
        thread.start()

        mock_listener_instance = MagicMock()
        app.hotkeys = MagicMock()
        app.hotkeys.create_listener.return_value = mock_listener_instance
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


@patch.dict(os.environ, {"V2T_MODE": "toggle"})
class TestToggleModeHotkeyHandling:
    """Tests for hotkey handling in toggle mode (default)."""

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
        assert app.mode == "toggle"
        assert app.is_recording is False
        _set_command_hotkey_backend(app)

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
        """Test that pressing hotkey when recording stops recording (toggle mode)."""
        from main import VoiceToTextApp
        from pynput import keyboard

        app = VoiceToTextApp()
        _set_command_hotkey_backend(app)
        app.recorder.stop.return_value = np.array([])

        app.on_press(keyboard.Key.cmd_r)
        assert app.is_recording is True

        app.on_release(keyboard.Key.cmd_r)
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
        _set_command_hotkey_backend(app)

        app.on_press(keyboard.Key.space)

        assert app.is_recording is False
        app.recorder.start.assert_not_called()

    @patch('main.AudioRecorder')
    @patch('main.AudioTranscriber')
    @patch('main.TextInjector')
    @patch('main.play_start_sound')
    def test_on_release_does_nothing_in_toggle_mode(
        self, mock_play_start, mock_injector, mock_transcriber, mock_recorder
    ):
        """Test that releasing hotkey does nothing in toggle mode."""
        from main import VoiceToTextApp
        from pynput import keyboard

        app = VoiceToTextApp()
        _set_command_hotkey_backend(app)
        app.on_press(keyboard.Key.cmd_r)
        assert app.is_recording is True

        app.on_release(keyboard.Key.cmd_r)

        # Still recording - release doesn't stop in toggle mode
        assert app.is_recording is True

    @patch('main.AudioRecorder')
    @patch('main.AudioTranscriber')
    @patch('main.TextInjector')
    @patch('main.play_start_sound')
    def test_on_press_ignores_duplicate_hotkey_callbacks(
        self, mock_play_start, mock_injector, mock_transcriber, mock_recorder
    ):
        """Repeated right-command press callbacks should trigger once per hold."""
        from main import VoiceToTextApp
        from pynput import keyboard

        app = VoiceToTextApp()
        _set_command_hotkey_backend(app)

        app.on_press(keyboard.Key.cmd_r)
        app.on_press(keyboard.Key.cmd_r)

        assert app.is_recording is True
        app.recorder.start.assert_called_once()

    @patch('main.AudioRecorder')
    @patch('main.AudioTranscriber')
    @patch('main.TextInjector')
    @patch('main.play_start_sound')
    def test_on_press_generic_cmd_does_nothing(
        self, mock_play_start, mock_injector, mock_transcriber, mock_recorder
    ):
        """Generic/left command should not trigger hotkey behavior."""
        from main import VoiceToTextApp
        from pynput import keyboard

        app = VoiceToTextApp()
        _set_command_hotkey_backend(app)

        app.on_press(keyboard.Key.cmd)

        assert app.is_recording is False
        app.recorder.start.assert_not_called()


class TestPushToTalkModeHotkeyHandling:
    """Tests for hotkey handling in push-to-talk mode."""

    @patch.dict(os.environ, {"V2T_MODE": "push_to_talk"})
    @patch('main.AudioRecorder')
    @patch('main.AudioTranscriber')
    @patch('main.TextInjector')
    @patch('main.play_start_sound')
    def test_on_press_starts_recording(self, mock_play_start, mock_injector, mock_transcriber, mock_recorder):
        """Test that pressing hotkey starts recording in push-to-talk mode."""
        from main import VoiceToTextApp
        from pynput import keyboard

        app = VoiceToTextApp()
        assert app.mode == "push_to_talk"
        assert app.is_recording is False
        _set_command_hotkey_backend(app)

        app.on_press(keyboard.Key.cmd_r)

        assert app.is_recording is True
        app.recorder.start.assert_called_once()

    @patch.dict(os.environ, {"V2T_MODE": "push_to_talk"})
    @patch('main.AudioRecorder')
    @patch('main.AudioTranscriber')
    @patch('main.TextInjector')
    @patch('main.play_start_sound')
    def test_on_press_does_not_restart_if_already_recording(
        self, mock_play_start, mock_injector, mock_transcriber, mock_recorder
    ):
        """Test that pressing hotkey doesn't restart recording if already recording."""
        from main import VoiceToTextApp
        from pynput import keyboard

        app = VoiceToTextApp()
        _set_command_hotkey_backend(app)
        app.is_recording = True
        app.recorder.start.reset_mock()

        app.on_press(keyboard.Key.cmd_r)

        assert app.is_recording is True
        app.recorder.start.assert_not_called()

    @patch.dict(os.environ, {"V2T_MODE": "push_to_talk"})
    @patch('main.AudioRecorder')
    @patch('main.AudioTranscriber')
    @patch('main.TextInjector')
    @patch('main.play_start_sound')
    @patch('main.play_stop_sound')
    def test_on_release_stops_recording(
        self, mock_play_stop, mock_play_start, mock_injector, mock_transcriber, mock_recorder
    ):
        """Test that releasing hotkey stops recording in push-to-talk mode."""
        from main import VoiceToTextApp
        from pynput import keyboard

        app = VoiceToTextApp()
        _set_command_hotkey_backend(app)
        app.recorder.stop.return_value = np.array([0.1, 0.2])

        app.on_press(keyboard.Key.cmd_r)
        assert app.is_recording is True

        with patch('main.threading.Thread'):
            app.on_release(keyboard.Key.cmd_r)

        assert app.is_recording is False
        app.recorder.stop.assert_called_once()

    @patch.dict(os.environ, {"V2T_MODE": "push_to_talk"})
    @patch('main.AudioRecorder')
    @patch('main.AudioTranscriber')
    @patch('main.TextInjector')
    def test_on_release_does_nothing_when_not_recording(self, mock_injector, mock_transcriber, mock_recorder):
        """Test that releasing hotkey does nothing if not recording."""
        from main import VoiceToTextApp
        from pynput import keyboard

        app = VoiceToTextApp()
        _set_command_hotkey_backend(app)
        assert app.is_recording is False

        app.on_release(keyboard.Key.cmd_r)

        assert app.is_recording is False
        app.recorder.stop.assert_not_called()

    @patch.dict(os.environ, {"V2T_MODE": "push_to_talk"})
    @patch('main.AudioRecorder')
    @patch('main.AudioTranscriber')
    @patch('main.TextInjector')
    @patch('main.play_start_sound')
    def test_on_release_ignores_other_keys(self, mock_play_start, mock_injector, mock_transcriber, mock_recorder):
        """Test that releasing non-hotkey keys doesn't stop recording."""
        from main import VoiceToTextApp
        from pynput import keyboard

        app = VoiceToTextApp()
        _set_command_hotkey_backend(app)
        app.on_press(keyboard.Key.cmd_r)
        assert app.is_recording is True

        app.on_release(keyboard.Key.alt_l)
        app.on_release(keyboard.Key.space)

        assert app.is_recording is True
        app.recorder.stop.assert_not_called()

    @patch.dict(os.environ, {"V2T_MODE": "push_to_talk"})
    @patch('main.AudioRecorder')
    @patch('main.AudioTranscriber')
    @patch('main.TextInjector')
    @patch('main.play_start_sound')
    @patch('main.play_stop_sound')
    def test_on_release_generic_cmd_does_not_stop_recording(
        self, mock_play_stop, mock_play_start, mock_injector, mock_transcriber, mock_recorder
    ):
        """Releasing generic/left command should not stop right-command recording."""
        from main import VoiceToTextApp
        from pynput import keyboard

        app = VoiceToTextApp()
        _set_command_hotkey_backend(app)
        app.recorder.stop.return_value = np.array([0.1, 0.2])

        app.on_press(keyboard.Key.cmd_r)
        assert app.is_recording is True

        # Releasing generic cmd should not stop.
        app.on_release(keyboard.Key.cmd)
        assert app.is_recording is True
        app.recorder.stop.assert_not_called()

    @patch.dict(os.environ, {"V2T_MODE": "push_to_talk"})
    @patch('main.AudioRecorder')
    @patch('main.AudioTranscriber')
    @patch('main.TextInjector')
    @patch('main.play_start_sound')
    @patch('main.play_stop_sound')
    def test_full_push_to_talk_cycle(
        self, mock_play_stop, mock_play_start, mock_injector, mock_transcriber, mock_recorder
    ):
        """Test complete push-to-talk cycle: press -> release."""
        from main import VoiceToTextApp
        from pynput import keyboard

        app = VoiceToTextApp()
        _set_command_hotkey_backend(app)
        app.recorder.stop.return_value = np.array([0.1, 0.2])

        # Press hotkey - should start recording
        app.on_press(keyboard.Key.cmd_r)
        assert app.is_recording is True
        app.recorder.start.assert_called_once()

        # Release hotkey - should stop and transcribe
        with patch('main.threading.Thread'):
            app.on_release(keyboard.Key.cmd_r)

        assert app.is_recording is False
        app.recorder.stop.assert_called_once()


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
        """Test that SIGINT (Ctrl+C) causes the app to exit gracefully."""
        import os
        from main import VoiceToTextApp

        app = VoiceToTextApp()
        app.recorder.get_input_device_info.return_value = "Test Device"
        app.transcriber.get_model_name.return_value = "test.en"
        app.capabilities = PlatformCapabilities(True, True, True, True)

        def signal_handler(signum, frame):
            app.shutdown_event.set()

        original_handler = signal.signal(signal.SIGINT, signal_handler)

        def send_sigint():
            time.sleep(0.2)
            if os.name == "nt":
                signal.raise_signal(signal.SIGINT)
            else:
                os.kill(os.getpid(), signal.SIGINT)

        sigint_thread = threading.Thread(target=send_sigint)
        sigint_thread.start()

        try:
            mock_listener_instance = MagicMock()
            app.hotkeys = MagicMock()
            app.hotkeys.create_listener.return_value = mock_listener_instance
            app.hotkeys.supported = True
            app.hotkey_label = "Right Command"
            app.capabilities = PlatformCapabilities(True, True, True, True)
            app.run()

            assert app.shutdown_event.is_set()
            mock_listener_instance.stop.assert_called_once()
        finally:
            signal.signal(signal.SIGINT, original_handler)
            sigint_thread.join()


class TestDegradedMode:
    @patch.dict(os.environ, {"V2T_ALLOW_DEGRADED_MODE": "0"})
    @patch("main.AudioRecorder")
    @patch("main.AudioTranscriber")
    @patch("main.TextInjector")
    def test_run_returns_early_when_hotkeys_unavailable_and_not_allowed(
        self, mock_injector, mock_transcriber, mock_recorder
    ):
        from main import VoiceToTextApp

        app = VoiceToTextApp()
        app.recorder.get_input_device_info.return_value = "Test Device"
        app.transcriber.get_model_name.return_value = "test.en"
        app.hotkeys = MagicMock()
        app.hotkeys.supported = False
        app.hotkeys.create_listener.return_value = MagicMock()
        app.capabilities = PlatformCapabilities(False, False, True, False, "Wayland sessions usually block global key capture and synthetic typing.")

        app.run()

        app.hotkeys.create_listener.assert_not_called()

    @patch.dict(os.environ, {"V2T_ALLOW_DEGRADED_MODE": "1"})
    @patch("main.AudioRecorder")
    @patch("main.AudioTranscriber")
    @patch("main.TextInjector")
    def test_run_starts_noop_listener_in_degraded_mode(
        self, mock_injector, mock_transcriber, mock_recorder
    ):
        from main import VoiceToTextApp

        app = VoiceToTextApp()
        app.recorder.get_input_device_info.return_value = "Test Device"
        app.transcriber.get_model_name.return_value = "test.en"
        app.hotkeys = MagicMock()
        app.hotkeys.supported = False
        listener = MagicMock()
        app.hotkeys.create_listener.return_value = listener
        app.capabilities = PlatformCapabilities(False, False, True, False, "Wayland sessions usually block global key capture and synthetic typing.")

        def set_shutdown():
            time.sleep(0.1)
            app.shutdown_event.set()

        thread = threading.Thread(target=set_shutdown)
        thread.start()
        app.run()
        thread.join()

        app.hotkeys.create_listener.assert_called_once()
        listener.start.assert_called_once()
