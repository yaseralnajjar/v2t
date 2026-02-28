import os
import sys

from backends.base import PlatformCapabilities


def get_platform_name():
    override = os.environ.get("V2T_PLATFORM_BACKEND", "auto").strip().lower()
    if override in {"macos", "darwin"}:
        return "darwin"
    if override in {"windows", "win32"}:
        return "win32"
    if override == "linux":
        return "linux"
    return sys.platform


def get_linux_session_type():
    override = os.environ.get("V2T_LINUX_SESSION", "").strip().lower()
    if override:
        return override
    session_type = os.environ.get("XDG_SESSION_TYPE", "").strip().lower()
    if session_type:
        return session_type
    if os.environ.get("WAYLAND_DISPLAY"):
        return "wayland"
    if os.environ.get("DISPLAY"):
        return "x11"
    return "unknown"


def get_platform_capabilities():
    platform_name = get_platform_name()

    if platform_name == "darwin":
        return PlatformCapabilities(
            global_hotkeys=True,
            text_injection=True,
            overlay_supported=True,
            permission_prompt_supported=True,
        )

    if platform_name == "win32":
        return PlatformCapabilities(
            global_hotkeys=True,
            text_injection=True,
            overlay_supported=True,
            permission_prompt_supported=False,
        )

    if platform_name.startswith("linux"):
        session_type = get_linux_session_type()
        if session_type == "x11":
            return PlatformCapabilities(
                global_hotkeys=True,
                text_injection=True,
                overlay_supported=True,
                permission_prompt_supported=False,
            )
        if session_type == "wayland":
            return PlatformCapabilities(
                global_hotkeys=False,
                text_injection=False,
                overlay_supported=True,
                permission_prompt_supported=False,
                reason="Wayland sessions usually block global key capture and synthetic typing.",
            )
        return PlatformCapabilities(
            global_hotkeys=False,
            text_injection=False,
            overlay_supported=True,
            permission_prompt_supported=False,
            reason="Linux desktop session could not be confirmed; hotkeys and text injection are disabled.",
        )

    return PlatformCapabilities(
        global_hotkeys=False,
        text_injection=False,
        overlay_supported=False,
        permission_prompt_supported=False,
        reason=f"Unsupported platform: {platform_name}",
    )
