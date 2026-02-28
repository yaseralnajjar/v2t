"""Unit tests for injector.py and platform injector backends."""

import os
import subprocess
from unittest.mock import MagicMock, patch


class TestTextInjectorFacade:
    """Tests for injector.TextInjector facade behavior."""

    @patch("injector.create_text_injector")
    def test_init_uses_backend_factory(self, mock_create_text_injector):
        from injector import TextInjector

        backend = MagicMock()
        backend.platform_name = "linux"
        mock_create_text_injector.return_value = backend

        injector = TextInjector()

        assert injector.backend is backend
        mock_create_text_injector.assert_called_once()

    @patch("injector.create_text_injector")
    def test_type_text_delegates_to_backend(self, mock_create_text_injector):
        from injector import TextInjector

        backend = MagicMock()
        backend.platform_name = "win32"
        mock_create_text_injector.return_value = backend

        injector = TextInjector()
        injector.type_text("hello")

        backend.type_text.assert_called_once_with("hello")

    @patch.dict(os.environ, {"V2T_DISABLE_APPLESCRIPT": "1"})
    @patch("injector.create_text_injector")
    def test_init_preserves_backend_applescript_state(self, mock_create_text_injector):
        from injector import TextInjector

        backend = MagicMock()
        backend.platform_name = "darwin"
        backend._use_applescript = False
        mock_create_text_injector.return_value = backend

        injector = TextInjector()

        assert injector.is_mac is True
        assert injector._use_applescript is False


class TestInjectorFactory:
    @patch.dict(os.environ, {"V2T_PLATFORM_BACKEND": "windows", "V2T_INJECT_MODE": "native"}, clear=True)
    def test_factory_selects_native_windows_injector(self):
        from backends import create_text_injector
        import backends.windows
        from backends.windows import WindowsNativeTextInjector

        with patch.object(backends.windows, "_load_user32") as mock_load_user32:
            injector = create_text_injector()

        assert isinstance(injector, WindowsNativeTextInjector)

    @patch.dict(os.environ, {"V2T_PLATFORM_BACKEND": "linux", "V2T_LINUX_SESSION": "wayland"}, clear=True)
    def test_factory_disables_linux_injection_on_wayland(self):
        from backends import create_text_injector
        from backends.base import NoOpTextInjector

        injector = create_text_injector()

        assert isinstance(injector, NoOpTextInjector)

    @patch.dict(
        os.environ,
        {"V2T_PLATFORM_BACKEND": "linux", "V2T_LINUX_SESSION": "x11", "V2T_INJECT_MODE": "native"},
        clear=True,
    )
    def test_factory_selects_native_linux_x11_injector(self):
        from backends import create_text_injector
        import backends.linux
        from backends.linux import LinuxX11TextInjector

        with patch.object(backends.linux, "has_xdotool", return_value=True):
            injector = create_text_injector()

        assert isinstance(injector, LinuxX11TextInjector)


class TestMacOSTextInjector:
    """Tests for the macOS-specific injector backend."""

    @patch("backends.macos._create_keyboard_controller")
    def test_type_text_does_nothing_for_empty_text(self, mock_create_keyboard_controller):
        from backends.macos import MacOSTextInjector

        mock_keyboard = MagicMock()
        mock_create_keyboard_controller.return_value = mock_keyboard
        injector = MacOSTextInjector()
        injector.type_text("")

        injector.keyboard.type.assert_not_called()

    @patch("backends.macos.subprocess")
    @patch("backends.macos._create_keyboard_controller")
    def test_type_text_uses_applescript_on_mac(self, mock_create_keyboard_controller, mock_subprocess):
        from backends.macos import MacOSTextInjector

        injector = MacOSTextInjector()
        injector.type_text("hello")

        assert mock_subprocess.run.called
        calls = mock_subprocess.run.call_args_list
        assert any("osascript" in str(call) for call in calls)

    @patch("backends.macos.subprocess")
    @patch("backends.macos._create_keyboard_controller")
    def test_type_text_escapes_quotes_for_applescript(self, mock_create_keyboard_controller, mock_subprocess):
        from backends.macos import MacOSTextInjector

        injector = MacOSTextInjector()
        injector.type_text('say "hello"')

        call_args = mock_subprocess.run.call_args_list[0]
        script = call_args[0][0][2]
        assert '\\"' in script

    @patch("backends.macos.subprocess")
    @patch("backends.macos._create_keyboard_controller")
    def test_type_text_escapes_backslashes_for_applescript(self, mock_create_keyboard_controller, mock_subprocess):
        from backends.macos import MacOSTextInjector

        injector = MacOSTextInjector()
        injector.type_text("path\\to\\file")

        call_args = mock_subprocess.run.call_args_list[0]
        script = call_args[0][0][2]
        assert "\\\\" in script

    @patch("backends.macos.subprocess")
    @patch("backends.macos._create_keyboard_controller")
    def test_type_text_adds_trailing_space_on_mac(self, mock_create_keyboard_controller, mock_subprocess):
        from backends.macos import MacOSTextInjector

        injector = MacOSTextInjector()
        injector.type_text("hello")

        assert mock_subprocess.run.call_count == 2
        space_call = mock_subprocess.run.call_args_list[1]
        assert 'keystroke " "' in space_call[0][0][2]

    @patch("backends.macos.subprocess")
    @patch("backends.macos._create_keyboard_controller")
    def test_type_text_falls_back_to_pynput_on_applescript_failure(self, mock_create_keyboard_controller, mock_subprocess):
        from backends.macos import MacOSTextInjector

        mock_subprocess.run.side_effect = Exception("AppleScript error")
        mock_keyboard = MagicMock()
        mock_create_keyboard_controller.return_value = mock_keyboard

        injector = MacOSTextInjector()
        injector.type_text("hello")

        mock_keyboard.type.assert_any_call("hello")

    @patch("backends.macos.subprocess")
    @patch("backends.macos._create_keyboard_controller")
    def test_type_text_disables_applescript_after_permission_failure(self, mock_create_keyboard_controller, mock_subprocess):
        from backends.macos import MacOSTextInjector

        mock_subprocess.run.side_effect = Exception("not allowed to send keystrokes")
        mock_keyboard = MagicMock()
        mock_create_keyboard_controller.return_value = mock_keyboard

        injector = MacOSTextInjector()
        injector.type_text("first")
        injector.type_text("second")

        assert mock_subprocess.run.call_count == 1
        assert mock_keyboard.type.call_count == 4

    @patch("backends.macos.subprocess")
    @patch("backends.macos._create_keyboard_controller")
    def test_type_text_disables_applescript_from_called_process_stderr(self, mock_create_keyboard_controller, mock_subprocess):
        from backends.macos import MacOSTextInjector

        mock_subprocess.run.side_effect = subprocess.CalledProcessError(
            returncode=1,
            cmd=["osascript"],
            stderr="System Events got an error: osascript is not allowed to send keystrokes. (1002)",
        )
        mock_keyboard = MagicMock()
        mock_create_keyboard_controller.return_value = mock_keyboard

        injector = MacOSTextInjector()
        injector.type_text("first")
        injector.type_text("second")

        assert mock_subprocess.run.call_count == 1
        assert mock_keyboard.type.call_count == 4

    @patch("backends.macos.time")
    @patch("backends.macos._create_keyboard_controller")
    def test_type_text_adds_delay_before_typing(self, mock_create_keyboard_controller, mock_time):
        from backends.macos import MacOSTextInjector

        mock_keyboard = MagicMock()
        mock_create_keyboard_controller.return_value = mock_keyboard

        injector = MacOSTextInjector()
        injector.type_text("hello")

        mock_time.sleep.assert_called_with(0.1)


class TestCrossPlatformInjectors:
    """Tests for Linux and Windows fallback injectors."""

    @patch("backends.linux.time")
    @patch("backends.linux._create_keyboard_controller")
    def test_linux_injector_uses_keyboard_controller(self, mock_create_keyboard_controller, mock_time):
        from backends.linux import LinuxTextInjector

        keyboard = MagicMock()
        mock_create_keyboard_controller.return_value = keyboard

        injector = LinuxTextInjector()
        injector.type_text("hello")

        keyboard.type.assert_any_call("hello")
        keyboard.type.assert_any_call(" ")
        mock_time.sleep.assert_called_with(0.1)

    @patch("backends.linux.time")
    @patch("backends.linux.subprocess.run")
    def test_linux_x11_injector_uses_xdotool(self, mock_run, mock_time):
        from backends.linux import LinuxX11TextInjector

        injector = LinuxX11TextInjector()
        injector.type_text("hello")

        mock_run.assert_called_once_with(
            ["xdotool", "type", "--delay", "0", "--clearmodifiers", "hello "],
            check=True,
            capture_output=True,
            text=True,
        )
        mock_time.sleep.assert_called_with(0.1)

    @patch("backends.windows.time")
    @patch("backends.windows._create_keyboard_controller")
    def test_windows_injector_uses_keyboard_controller(self, mock_create_keyboard_controller, mock_time):
        from backends.windows import WindowsTextInjector

        keyboard = MagicMock()
        mock_create_keyboard_controller.return_value = keyboard

        injector = WindowsTextInjector()
        injector.type_text("hello")

        keyboard.type.assert_any_call("hello")
        keyboard.type.assert_any_call(" ")
        mock_time.sleep.assert_called_with(0.1)

    @patch("backends.windows.time")
    def test_windows_native_injector_sends_utf16_units(self, mock_time):
        from backends.windows import WindowsNativeTextInjector

        user32 = MagicMock()
        user32.SendInput.return_value = 1

        injector = WindowsNativeTextInjector(user32=user32)
        injector.type_text("A")

        assert user32.SendInput.call_count == 4
        mock_time.sleep.assert_called_with(0.1)

    def test_windows_native_injector_supports_non_bmp_text(self):
        from backends.windows import WindowsNativeTextInjector

        injector = WindowsNativeTextInjector(user32=MagicMock())
        units = list(injector._utf16_units("🙂"))

        assert len(units) == 2
