import ctypes
import os
import shutil
import subprocess
import threading
import time
from types import SimpleNamespace

from backends.detect import get_platform_capabilities, get_platform_name


def _get_keyboard_module():
    from pynput import keyboard

    return keyboard


def _load_user32():
    loader = getattr(ctypes, "WinDLL", None)
    if loader is None:
        raise OSError("WinDLL is unavailable on this host")
    return loader("user32", use_last_error=True)


def _make_vk_event(vk):
    return SimpleNamespace(value=SimpleNamespace(vk=vk))


class NoOpListener:
    def start(self):
        return None

    def stop(self):
        return None


class PollingListener:
    def __init__(self, vk, on_press, on_release, get_pressed, poll_interval=0.01):
        self.vk = vk
        self.on_press = on_press
        self.on_release = on_release
        self.get_pressed = get_pressed
        self.poll_interval = poll_interval
        self._thread = None
        self._stop_event = threading.Event()

    def _run(self):
        was_pressed = False
        event = _make_vk_event(self.vk)
        while not self._stop_event.is_set():
            is_pressed = bool(self.get_pressed())
            if is_pressed and not was_pressed:
                self.on_press(event)
            elif was_pressed and not is_pressed:
                self.on_release(event)
            was_pressed = is_pressed
            time.sleep(self.poll_interval)

    def start(self):
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=0.5)


class XInputListener:
    def __init__(self, keycode, on_press, on_release, executable="xinput"):
        self.keycode = str(keycode)
        self.on_press = on_press
        self.on_release = on_release
        self.executable = executable
        self._thread = None
        self._process = None
        self._stop_event = threading.Event()

    def _handle_line(self, line, event_type):
        if f"detail: {self.keycode}" not in line:
            return event_type
        event = _make_vk_event(int(self.keycode))
        if event_type == "press":
            self.on_press(event)
        elif event_type == "release":
            self.on_release(event)
        return None

    def _run(self):
        self._process = subprocess.Popen(
            [self.executable, "test-xi2", "--root"],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        )
        event_type = None
        try:
            for line in self._process.stdout:
                if self._stop_event.is_set():
                    break
                if "RawKeyPress" in line:
                    event_type = "press"
                    continue
                if "RawKeyRelease" in line:
                    event_type = "release"
                    continue
                if event_type and "detail:" in line:
                    event_type = self._handle_line(line.strip(), event_type)
        finally:
            if self._process and self._process.poll() is None:
                self._process.terminate()

    def start(self):
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        if self._process and self._process.poll() is None:
            self._process.terminate()
        if self._thread:
            self._thread.join(timeout=0.5)


class DisabledHotkeyBackend:
    supported = False

    def __init__(self, reason=None, label="Unavailable"):
        self.reason = reason
        self.label = label

    def create_listener(self, on_press, on_release):
        return NoOpListener()

    def is_hotkey(self, key):
        return False

    def key_id(self, key):
        return key


class PynputHotkeyBackend:
    supported = True

    def __init__(self, key_name, vk, label):
        self.key_name = key_name
        self.vk = vk
        self.label = label

    def create_listener(self, on_press, on_release):
        keyboard = _get_keyboard_module()
        return keyboard.Listener(on_press=on_press, on_release=on_release)

    def is_hotkey(self, key):
        keyboard = _get_keyboard_module()
        expected = getattr(keyboard.Key, self.key_name, None)
        if expected is not None and key == expected:
            return True
        value = getattr(key, "value", None)
        return getattr(value, "vk", None) == self.vk

    def key_id(self, key):
        value = getattr(key, "value", None)
        return getattr(value, "vk", key)


class WindowsNativeHotkeyBackend:
    supported = True

    def __init__(self, vk, label, user32=None):
        self.vk = vk
        self.label = label
        self.user32 = user32 or _load_user32()

    def create_listener(self, on_press, on_release):
        return PollingListener(
            vk=self.vk,
            on_press=on_press,
            on_release=on_release,
            get_pressed=lambda: self.user32.GetAsyncKeyState(self.vk) & 0x8000,
        )

    def is_hotkey(self, key):
        value = getattr(key, "value", None)
        return getattr(value, "vk", None) == self.vk

    def key_id(self, key):
        value = getattr(key, "value", None)
        return getattr(value, "vk", key)


class LinuxX11NativeHotkeyBackend:
    supported = True

    def __init__(self, keycode, label, executable="xinput"):
        self.keycode = keycode
        self.label = label
        self.executable = executable

    def create_listener(self, on_press, on_release):
        return XInputListener(
            keycode=self.keycode,
            on_press=on_press,
            on_release=on_release,
            executable=self.executable,
        )

    def is_hotkey(self, key):
        value = getattr(key, "value", None)
        return getattr(value, "vk", None) == self.keycode

    def key_id(self, key):
        value = getattr(key, "value", None)
        return getattr(value, "vk", key)


def has_xinput():
    return shutil.which("xinput") is not None


def create_hotkey_backend():
    backend_name = os.environ.get("V2T_HOTKEY_BACKEND", "auto").strip().lower()
    capabilities = get_platform_capabilities()
    if backend_name == "disabled":
        return DisabledHotkeyBackend(reason="Disabled by V2T_HOTKEY_BACKEND=disabled")

    if not capabilities.global_hotkeys:
        return DisabledHotkeyBackend(reason=capabilities.reason)

    platform_name = get_platform_name()
    if backend_name not in {"auto", "pynput", "native"}:
        return DisabledHotkeyBackend(reason=f"Unsupported hotkey backend: {backend_name}")

    if platform_name == "darwin":
        if backend_name == "native":
            return DisabledHotkeyBackend(reason="No native macOS hotkey backend is implemented yet.")
        return PynputHotkeyBackend(key_name="cmd_r", vk=54, label="Right Command")

    if platform_name == "win32" and backend_name == "native":
        return WindowsNativeHotkeyBackend(vk=0xA3, label="Right Ctrl")

    if platform_name.startswith("linux") and backend_name == "native":
        if has_xinput():
            return LinuxX11NativeHotkeyBackend(keycode=105, label="Right Ctrl")
        return DisabledHotkeyBackend(reason="xinput is required for the native Linux X11 hotkey backend.")

    return PynputHotkeyBackend(key_name="ctrl_r", vk=105, label="Right Ctrl")
