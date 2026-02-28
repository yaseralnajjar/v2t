import shutil
import subprocess
import time

from backends.base import NoOpPermissionManager, BaseTextInjector
from backends.detect import get_linux_session_type


def _create_keyboard_controller():
    from pynput.keyboard import Controller

    return Controller()


class LinuxTextInjector(BaseTextInjector):
    platform_name = "linux"

    def __init__(self, platform_name="linux"):
        self.platform_name = platform_name
        self.keyboard = _create_keyboard_controller()

    def type_text(self, text):
        if not text:
            return
        time.sleep(0.1)
        self.keyboard.type(text)
        self.keyboard.type(" ")


class LinuxX11TextInjector(BaseTextInjector):
    platform_name = "linux"

    def __init__(self, executable="xdotool"):
        self.executable = executable

    def type_text(self, text):
        if not text:
            return
        time.sleep(0.1)
        subprocess.run(
            [self.executable, "type", "--delay", "0", "--clearmodifiers", f"{text} "],
            check=True,
            capture_output=True,
            text=True,
        )


def has_xdotool():
    return shutil.which("xdotool") is not None


class LinuxPermissionManager(NoOpPermissionManager):
    platform_name = "linux"

    def preflight(self):
        session_type = get_linux_session_type()
        if session_type == "x11":
            print("Linux session detected: X11. Using pynput for hotkeys and text injection.", flush=True)
        elif session_type == "wayland":
            print(
                "Linux session detected: Wayland. Global hotkeys and text injection are disabled unless a custom backend is added.",
                flush=True,
            )
        else:
            print(
                "Linux session type is unknown. Running without global hotkeys or text injection unless the session is configured explicitly.",
                flush=True,
            )
        return True
