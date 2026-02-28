import os

from backends.detect import get_platform_capabilities, get_platform_name


def _get_keyboard_module():
    from pynput import keyboard

    return keyboard


class NoOpListener:
    def start(self):
        return None

    def stop(self):
        return None


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


def create_hotkey_backend():
    backend_name = os.environ.get("V2T_HOTKEY_BACKEND", "auto").strip().lower()
    capabilities = get_platform_capabilities()
    if backend_name == "disabled":
        return DisabledHotkeyBackend(reason="Disabled by V2T_HOTKEY_BACKEND=disabled")

    if not capabilities.global_hotkeys:
        return DisabledHotkeyBackend(reason=capabilities.reason)

    platform_name = get_platform_name()
    if backend_name not in {"auto", "pynput"}:
        return DisabledHotkeyBackend(reason=f"Unsupported hotkey backend: {backend_name}")

    if platform_name == "darwin":
        return PynputHotkeyBackend(key_name="cmd_r", vk=54, label="Right Command")

    return PynputHotkeyBackend(key_name="ctrl_r", vk=105, label="Right Ctrl")
