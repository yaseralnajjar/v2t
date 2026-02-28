import ctypes
import time
from ctypes import wintypes

from backends.base import NoOpPermissionManager, BaseTextInjector

INPUT_KEYBOARD = 1
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004
ULONG_PTR = getattr(wintypes, "ULONG_PTR", ctypes.c_size_t)


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


class _INPUTUNION(ctypes.Union):
    _fields_ = [("ki", KEYBDINPUT)]


class INPUT(ctypes.Structure):
    _anonymous_ = ("u",)
    _fields_ = [("type", wintypes.DWORD), ("u", _INPUTUNION)]


def _create_keyboard_controller():
    from pynput.keyboard import Controller

    return Controller()


def _load_user32():
    loader = getattr(ctypes, "WinDLL", None)
    if loader is None:
        raise OSError("WinDLL is unavailable on this host")
    return loader("user32", use_last_error=True)


class WindowsTextInjector(BaseTextInjector):
    platform_name = "win32"

    def __init__(self):
        self.keyboard = _create_keyboard_controller()

    def type_text(self, text):
        if not text:
            return
        time.sleep(0.1)
        self.keyboard.type(text)
        self.keyboard.type(" ")


class WindowsNativeTextInjector(BaseTextInjector):
    platform_name = "win32"

    def __init__(self, user32=None):
        self.user32 = user32 or _load_user32()

    def _utf16_units(self, text):
        data = text.encode("utf-16-le")
        for index in range(0, len(data), 2):
            yield int.from_bytes(data[index:index + 2], "little")

    def _send_unit(self, unit, keyup=False):
        flags = KEYEVENTF_UNICODE | (KEYEVENTF_KEYUP if keyup else 0)
        event = INPUT(
            type=INPUT_KEYBOARD,
            ki=KEYBDINPUT(
                wVk=0,
                wScan=unit,
                dwFlags=flags,
                time=0,
                dwExtraInfo=0,
            ),
        )
        sent = self.user32.SendInput(1, ctypes.byref(event), ctypes.sizeof(INPUT))
        if sent != 1:
            raise OSError(ctypes.get_last_error() or "SendInput failed")

    def type_text(self, text):
        if not text:
            return
        time.sleep(0.1)
        for unit in self._utf16_units(f"{text} "):
            self._send_unit(unit, keyup=False)
            self._send_unit(unit, keyup=True)


class WindowsPermissionManager(NoOpPermissionManager):
    platform_name = "win32"
