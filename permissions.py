import ctypes
import ctypes.util
import os
import subprocess
import sys


def _load_core_graphics():
    """Load CoreGraphics dynamic library for event permission checks."""
    library_path = ctypes.util.find_library("CoreGraphics")
    if not library_path:
        library_path = "/System/Library/Frameworks/CoreGraphics.framework/CoreGraphics"
    try:
        return ctypes.CDLL(library_path)
    except OSError:
        return None


def _check_or_request_event_access(core_graphics, preflight_name, request_name, label):
    """Check an event permission and request it if missing."""
    preflight = getattr(core_graphics, preflight_name, None)
    request = getattr(core_graphics, request_name, None)
    if preflight is None or request is None:
        print(f"Could not verify macOS {label} permission on this system.", flush=True)
        return False

    preflight.restype = ctypes.c_bool
    request.restype = ctypes.c_bool

    if preflight():
        return True

    print(f"Requesting macOS {label} permission...", flush=True)
    return bool(request())


def _request_automation_permission():
    """
    Trigger Automation permission prompt for controlling System Events.
    Returns True when command succeeds; False if permission is missing/denied.
    """
    script = 'tell application "System Events" to get name of first process'
    try:
        subprocess.run(
            ["osascript", "-e", script],
            check=True,
            capture_output=True,
            text=True,
        )
        return True
    except Exception as exc:
        details = str(exc)
        stderr = getattr(exc, "stderr", None)
        if stderr:
            details = f"{details} {stderr}"

        # Common macOS automation denial text from Apple Events sandboxing.
        if (
            "not authorized to send Apple events to System Events" in details
            or "not permitted to send keystrokes" in details
            or "not allowed to send keystrokes" in details
        ):
            print("Automation permission for System Events is missing.", flush=True)
        else:
            print(f"Automation permission check failed: {details}", flush=True)
        return False


def _print_manual_permission_steps(missing):
    """Print explicit manual navigation steps for missing permissions."""
    print("", flush=True)
    print("Manual permission setup:", flush=True)
    print("1) Open System Settings", flush=True)
    print("2) Go to Privacy & Security", flush=True)

    if "Accessibility" in missing:
        print("3) Open Accessibility", flush=True)
        print(
            "   Path: System Settings > Privacy & Security > Accessibility",
            flush=True,
        )
        print(
            "   Enable the app running ./start.sh (Terminal, iTerm, or VS Code).",
            flush=True,
        )

    if "Input Monitoring" in missing:
        print("4) Open Input Monitoring", flush=True)
        print(
            "   Path: System Settings > Privacy & Security > Input Monitoring",
            flush=True,
        )
        print(
            "   Enable the app running ./start.sh (Terminal, iTerm, or VS Code).",
            flush=True,
        )

    if "Automation (System Events)" in missing:
        print("5) Open Automation", flush=True)
        print(
            "   Path: System Settings > Privacy & Security > Automation",
            flush=True,
        )
        print("   Allow your app to control System Events.", flush=True)

    print("6) Quit and reopen that app, then run ./start.sh again.", flush=True)


def _open_settings_for_missing_permissions(missing):
    """Open System Settings pages for missing permissions."""
    urls = []
    if "Accessibility" in missing:
        urls.append("x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility")
    if "Input Monitoring" in missing:
        urls.append("x-apple.systempreferences:com.apple.preference.security?Privacy_ListenEvent")
    if "Automation (System Events)" in missing:
        urls.append("x-apple.systempreferences:com.apple.preference.security?Privacy_Automation")

    for url in urls:
        try:
            subprocess.run(["open", url], check=False)
        except Exception:
            pass


def request_macos_permissions():
    """
    Best-effort startup permission request flow for macOS.
    - Input Monitoring: needed for global key listening.
    - Accessibility (event posting): needed for keyboard injection.
    - Automation: needed for AppleScript -> System Events.
    """
    if sys.platform != "darwin":
        return True

    print("Checking macOS permissions...", flush=True)

    missing = []
    critical_missing = []
    core_graphics = _load_core_graphics()

    if core_graphics is None:
        print("Could not load CoreGraphics; skipping permission preflight checks.", flush=True)
    else:
        listen_ok = _check_or_request_event_access(
            core_graphics,
            "CGPreflightListenEventAccess",
            "CGRequestListenEventAccess",
            "Input Monitoring",
        )
        if not listen_ok:
            missing.append("Input Monitoring")
            critical_missing.append("Input Monitoring")

        post_ok = _check_or_request_event_access(
            core_graphics,
            "CGPreflightPostEventAccess",
            "CGRequestPostEventAccess",
            "Accessibility",
        )
        if not post_ok:
            missing.append("Accessibility")
            critical_missing.append("Accessibility")

    automation_ok = _request_automation_permission()
    if not automation_ok:
        missing.append("Automation (System Events)")
        # Avoid repeated AppleScript failures; injector will use pynput directly.
        os.environ["V2T_DISABLE_APPLESCRIPT"] = "1"

    if missing:
        joined = ", ".join(missing)
        print(f"Missing macOS permissions: {joined}", flush=True)
        _print_manual_permission_steps(missing)
        _open_settings_for_missing_permissions(missing)

    if critical_missing:
        print(
            "Critical permissions are missing. Grant access, then restart ./start.sh.",
            flush=True,
        )
        return False

    return True
