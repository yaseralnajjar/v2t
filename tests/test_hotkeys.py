"""Tests for hotkey backend abstraction."""

import os
from unittest.mock import ANY, MagicMock, patch


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


class TestNativeHotkeyBackends:
    def test_windows_native_backend_uses_right_ctrl_vk(self):
        from hotkeys import WindowsNativeHotkeyBackend

        backend = WindowsNativeHotkeyBackend(vk=0xA3, label="Right Ctrl", user32=MagicMock())

        assert backend.vk == 0xA3
        assert backend.label == "Right Ctrl"

    @patch("hotkeys.subprocess.Popen")
    def test_linux_x11_listener_starts_xinput_process(self, mock_popen):
        from hotkeys import LinuxX11NativeHotkeyBackend

        process = MagicMock()
        process.stdout = iter([])
        process.poll.return_value = 0
        mock_popen.return_value = process

        backend = LinuxX11NativeHotkeyBackend(keycode=105, label="Right Ctrl")
        listener = backend.create_listener(on_press=MagicMock(), on_release=MagicMock())
        listener.start()
        listener.stop()

        mock_popen.assert_called_once_with(
            ["xinput", "test-xi2", "--root"],
            stdout=ANY,
            stderr=ANY,
            text=True,
        )


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

    @patch.dict(os.environ, {"V2T_PLATFORM_BACKEND": "windows", "V2T_HOTKEY_BACKEND": "native"}, clear=True)
    @patch("hotkeys._load_user32", return_value=MagicMock())
    def test_windows_native_backend_can_be_selected(self, mock_load_user32):
        from hotkeys import WindowsNativeHotkeyBackend, create_hotkey_backend

        backend = create_hotkey_backend()

        assert isinstance(backend, WindowsNativeHotkeyBackend)

    @patch.dict(
        os.environ,
        {"V2T_PLATFORM_BACKEND": "linux", "V2T_LINUX_SESSION": "x11", "V2T_HOTKEY_BACKEND": "native"},
        clear=True,
    )
    @patch("hotkeys.has_xinput", return_value=True)
    def test_linux_native_backend_can_be_selected(self, mock_has_xinput):
        from hotkeys import LinuxX11NativeHotkeyBackend, create_hotkey_backend

        backend = create_hotkey_backend()

        assert isinstance(backend, LinuxX11NativeHotkeyBackend)
