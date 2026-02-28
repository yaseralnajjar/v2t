"""Tests for hotkey backend abstraction."""

import os
from unittest.mock import MagicMock, patch


class TestPynputHotkeyBackend:
    @patch("hotkeys._get_keyboard_module")
    def test_create_listener_uses_pynput_listener(self, mock_get_keyboard_module):
        from hotkeys import PynputHotkeyBackend

        mock_keyboard_module = type("KeyboardModule", (), {})()
        mock_keyboard_module.Listener = MagicMock()
        mock_get_keyboard_module.return_value = mock_keyboard_module

        backend = PynputHotkeyBackend(key_name="cmd_r", vk=54, label="Right Command")
        backend.create_listener(on_press="press", on_release="release")

        mock_keyboard_module.Listener.assert_called_once_with(on_press="press", on_release="release")


class TestCreateHotkeyBackend:
    @patch.dict(os.environ, {"V2T_HOTKEY_BACKEND": "disabled"}, clear=True)
    def test_disabled_backend_is_returned_when_requested(self):
        from hotkeys import DisabledHotkeyBackend, create_hotkey_backend

        backend = create_hotkey_backend()

        assert isinstance(backend, DisabledHotkeyBackend)

    @patch.dict(os.environ, {"XDG_SESSION_TYPE": "wayland"}, clear=True)
    @patch("hotkeys.get_platform_name", return_value="linux")
    def test_wayland_returns_disabled_backend(self, mock_platform_name):
        from hotkeys import DisabledHotkeyBackend, create_hotkey_backend

        backend = create_hotkey_backend()

        assert isinstance(backend, DisabledHotkeyBackend)

    @patch.dict(os.environ, {"V2T_PLATFORM_BACKEND": "windows"}, clear=True)
    def test_windows_default_uses_right_ctrl(self):
        from hotkeys import PynputHotkeyBackend, create_hotkey_backend

        backend = create_hotkey_backend()

        assert isinstance(backend, PynputHotkeyBackend)
        assert backend.label == "Right Ctrl"
