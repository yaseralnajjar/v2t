import os

from backends.base import NoOpTextInjector
from backends.detect import get_platform_capabilities, get_platform_name


def create_text_injector():
    inject_mode = os.environ.get("V2T_INJECT_MODE", "auto").strip().lower()
    capabilities = get_platform_capabilities()

    if inject_mode == "disabled":
        return NoOpTextInjector()

    platform_name = get_platform_name()
    if platform_name == "darwin":
        if inject_mode == "pynput":
            from backends.linux import LinuxTextInjector

            return LinuxTextInjector(platform_name="darwin")
        from backends.macos import MacOSTextInjector

        return MacOSTextInjector()
    if platform_name == "win32":
        if inject_mode == "native":
            from backends.windows import WindowsNativeTextInjector

            return WindowsNativeTextInjector()
        from backends.windows import WindowsTextInjector

        return WindowsTextInjector()
    if not capabilities.text_injection:
        return NoOpTextInjector()
    from backends.detect import get_linux_session_type
    from backends.linux import LinuxTextInjector, LinuxX11TextInjector, has_xdotool

    if inject_mode == "native" and get_linux_session_type() == "x11" and has_xdotool():
        return LinuxX11TextInjector()

    return LinuxTextInjector()


def create_permission_manager():
    platform_name = get_platform_name()
    if platform_name == "darwin":
        from backends.macos import MacOSPermissionManager

        return MacOSPermissionManager()
    if platform_name == "win32":
        from backends.windows import WindowsPermissionManager

        return WindowsPermissionManager()
    from backends.linux import LinuxPermissionManager

    return LinuxPermissionManager()


__all__ = [
    "create_permission_manager",
    "create_text_injector",
    "get_platform_capabilities",
    "get_platform_name",
]
