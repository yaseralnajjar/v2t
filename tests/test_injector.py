"""Unit tests for injector.py - TextInjector class."""

import sys
import subprocess
import os
from unittest.mock import Mock, patch, MagicMock
import pytest


class TestTextInjectorInit:
    """Tests for TextInjector initialization."""

    @patch('injector.Controller')
    def test_init_creates_keyboard_controller(self, mock_controller):
        """Test that __init__ creates a keyboard Controller."""
        from injector import TextInjector

        injector = TextInjector()

        mock_controller.assert_called_once()

    @patch('injector.Controller')
    def test_init_detects_mac_platform(self, mock_controller):
        """Test that __init__ correctly detects macOS."""
        from injector import TextInjector

        with patch.object(sys, 'platform', 'darwin'):
            injector = TextInjector()
            assert injector.is_mac is True

    @patch('injector.Controller')
    def test_init_detects_non_mac_platform(self, mock_controller):
        """Test that __init__ correctly detects non-macOS."""
        from injector import TextInjector

        with patch.object(sys, 'platform', 'linux'):
            injector = TextInjector()
            assert injector.is_mac is False

    @patch.dict(os.environ, {"V2T_DISABLE_APPLESCRIPT": "1"})
    @patch('injector.Controller')
    def test_init_disables_applescript_when_env_set(self, mock_controller):
        """Test that AppleScript can be disabled by startup permission checks."""
        from injector import TextInjector

        with patch.object(sys, 'platform', 'darwin'):
            injector = TextInjector()
            assert injector._use_applescript is False


class TestTextInjectorTypeText:
    """Tests for TextInjector.type_text() method."""

    @patch('injector.Controller')
    def test_type_text_does_nothing_for_empty_text(self, mock_controller):
        """Test that type_text does nothing for empty string."""
        from injector import TextInjector

        with patch.object(sys, 'platform', 'linux'):
            injector = TextInjector()
            injector.type_text("")

        injector.keyboard.type.assert_not_called()

    @patch('injector.Controller')
    def test_type_text_does_nothing_for_none(self, mock_controller):
        """Test that type_text does nothing for None."""
        from injector import TextInjector

        with patch.object(sys, 'platform', 'linux'):
            injector = TextInjector()
            injector.type_text(None)

        injector.keyboard.type.assert_not_called()

    @patch('injector.subprocess')
    @patch('injector.Controller')
    def test_type_text_uses_applescript_on_mac(self, mock_controller, mock_subprocess):
        """Test that type_text uses AppleScript on macOS."""
        from injector import TextInjector

        with patch.object(sys, 'platform', 'darwin'):
            injector = TextInjector()
            injector.type_text("hello")

        assert mock_subprocess.run.called
        calls = mock_subprocess.run.call_args_list
        assert any('osascript' in str(call) for call in calls)

    @patch('injector.subprocess')
    @patch('injector.Controller')
    def test_type_text_escapes_quotes_for_applescript(self, mock_controller, mock_subprocess):
        """Test that type_text escapes double quotes for AppleScript."""
        from injector import TextInjector

        with patch.object(sys, 'platform', 'darwin'):
            injector = TextInjector()
            injector.type_text('say "hello"')

        call_args = mock_subprocess.run.call_args_list[0]
        script = call_args[0][0][2]
        assert '\\"' in script

    @patch('injector.subprocess')
    @patch('injector.Controller')
    def test_type_text_escapes_backslashes_for_applescript(self, mock_controller, mock_subprocess):
        """Test that type_text escapes backslashes for AppleScript."""
        from injector import TextInjector

        with patch.object(sys, 'platform', 'darwin'):
            injector = TextInjector()
            injector.type_text('path\\to\\file')

        call_args = mock_subprocess.run.call_args_list[0]
        script = call_args[0][0][2]
        assert '\\\\' in script

    @patch('injector.subprocess')
    @patch('injector.Controller')
    def test_type_text_adds_trailing_space_on_mac(self, mock_controller, mock_subprocess):
        """Test that type_text adds a trailing space on macOS."""
        from injector import TextInjector

        with patch.object(sys, 'platform', 'darwin'):
            injector = TextInjector()
            injector.type_text("hello")

        assert mock_subprocess.run.call_count == 2
        space_call = mock_subprocess.run.call_args_list[1]
        assert 'keystroke " "' in space_call[0][0][2]

    @patch('injector.Controller')
    def test_type_text_uses_pynput_on_non_mac(self, mock_controller):
        """Test that type_text uses pynput on non-macOS."""
        from injector import TextInjector

        mock_keyboard = MagicMock()
        mock_controller.return_value = mock_keyboard

        with patch.object(sys, 'platform', 'linux'):
            injector = TextInjector()
            injector.type_text("hello")

        mock_keyboard.type.assert_any_call("hello")

    @patch('injector.Controller')
    def test_type_text_adds_trailing_space_on_non_mac(self, mock_controller):
        """Test that type_text adds a trailing space on non-macOS."""
        from injector import TextInjector

        mock_keyboard = MagicMock()
        mock_controller.return_value = mock_keyboard

        with patch.object(sys, 'platform', 'linux'):
            injector = TextInjector()
            injector.type_text("hello")

        calls = mock_keyboard.type.call_args_list
        assert calls[0][0][0] == "hello"
        assert calls[1][0][0] == " "

    @patch('injector.subprocess')
    @patch('injector.Controller')
    def test_type_text_falls_back_to_pynput_on_applescript_failure(self, mock_controller, mock_subprocess):
        """Test that type_text falls back to pynput when AppleScript fails."""
        from injector import TextInjector

        mock_subprocess.run.side_effect = Exception("AppleScript error")
        mock_keyboard = MagicMock()
        mock_controller.return_value = mock_keyboard

        with patch.object(sys, 'platform', 'darwin'):
            injector = TextInjector()
            injector.type_text("hello")

        mock_keyboard.type.assert_any_call("hello")

    @patch('injector.subprocess')
    @patch('injector.Controller')
    def test_type_text_disables_applescript_after_permission_failure(self, mock_controller, mock_subprocess):
        """Test that permission failure disables AppleScript retries for this session."""
        from injector import TextInjector

        mock_subprocess.run.side_effect = Exception("not allowed to send keystrokes")
        mock_keyboard = MagicMock()
        mock_controller.return_value = mock_keyboard

        with patch.object(sys, 'platform', 'darwin'):
            injector = TextInjector()
            injector.type_text("first")
            injector.type_text("second")

        # First call attempts AppleScript and fails, then all typing happens via pynput.
        assert mock_subprocess.run.call_count == 1
        assert mock_keyboard.type.call_count == 4

    @patch('injector.subprocess')
    @patch('injector.Controller')
    def test_type_text_disables_applescript_from_called_process_stderr(self, mock_controller, mock_subprocess):
        """Test that CalledProcessError stderr permission text disables AppleScript retries."""
        from injector import TextInjector

        mock_subprocess.run.side_effect = subprocess.CalledProcessError(
            returncode=1,
            cmd=["osascript"],
            stderr="System Events got an error: osascript is not allowed to send keystrokes. (1002)"
        )
        mock_keyboard = MagicMock()
        mock_controller.return_value = mock_keyboard

        with patch.object(sys, 'platform', 'darwin'):
            injector = TextInjector()
            injector.type_text("first")
            injector.type_text("second")

        assert mock_subprocess.run.call_count == 1
        assert mock_keyboard.type.call_count == 4

    @patch('injector.time')
    @patch('injector.Controller')
    def test_type_text_adds_delay_before_typing(self, mock_controller, mock_time):
        """Test that type_text adds a small delay for focus."""
        from injector import TextInjector

        mock_keyboard = MagicMock()
        mock_controller.return_value = mock_keyboard

        with patch.object(sys, 'platform', 'linux'):
            injector = TextInjector()
            injector.type_text("hello")

        mock_time.sleep.assert_called_with(0.1)
