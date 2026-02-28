"""Tests for backend platform detection and capabilities."""

import os
from unittest.mock import patch


class TestPlatformDetection:
    @patch.dict(os.environ, {}, clear=True)
    @patch("backends.detect.sys.platform", "darwin")
    def test_get_platform_name_uses_current_platform_by_default(self):
        from backends.detect import get_platform_name

        assert get_platform_name() == "darwin"

    @patch.dict(os.environ, {"V2T_PLATFORM_BACKEND": "windows"})
    def test_get_platform_name_honors_override(self):
        from backends.detect import get_platform_name

        assert get_platform_name() == "win32"

    @patch.dict(os.environ, {"XDG_SESSION_TYPE": "wayland"}, clear=True)
    def test_get_linux_session_type_reads_environment(self):
        from backends.detect import get_linux_session_type

        assert get_linux_session_type() == "wayland"

    @patch.dict(os.environ, {"V2T_LINUX_SESSION": "x11"}, clear=True)
    def test_get_linux_session_type_honors_override(self):
        from backends.detect import get_linux_session_type

        assert get_linux_session_type() == "x11"


class TestPlatformCapabilities:
    @patch.dict(os.environ, {}, clear=True)
    @patch("backends.detect.sys.platform", "darwin")
    def test_macos_capabilities_enable_full_support(self):
        from backends.detect import get_platform_capabilities

        capabilities = get_platform_capabilities()

        assert capabilities.global_hotkeys is True
        assert capabilities.text_injection is True
        assert capabilities.permission_prompt_supported is True

    @patch.dict(os.environ, {"XDG_SESSION_TYPE": "wayland"}, clear=True)
    @patch("backends.detect.sys.platform", "linux")
    def test_wayland_capabilities_disable_hotkeys_and_injection(self):
        from backends.detect import get_platform_capabilities

        capabilities = get_platform_capabilities()

        assert capabilities.global_hotkeys is False
        assert capabilities.text_injection is False
        assert "Wayland" in capabilities.reason

    @patch.dict(os.environ, {}, clear=True)
    @patch("backends.detect.sys.platform", "linux")
    def test_unknown_linux_session_disables_hotkeys_and_injection(self):
        from backends.detect import get_platform_capabilities

        capabilities = get_platform_capabilities()

        assert capabilities.global_hotkeys is False
        assert capabilities.text_injection is False
        assert "Linux desktop session" in capabilities.reason
