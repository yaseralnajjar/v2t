"""Unit tests for permission backend selection and macOS permissions."""

import os
import subprocess
from types import SimpleNamespace
from unittest.mock import MagicMock, patch


class TestPermissionFacade:
    """Tests for permissions.py facade behavior."""

    @patch("permissions.create_permission_manager")
    def test_request_runtime_permissions_uses_backend_factory(self, mock_create_permission_manager):
        from permissions import request_runtime_permissions

        manager = MagicMock()
        manager.preflight.return_value = True
        mock_create_permission_manager.return_value = manager

        assert request_runtime_permissions() is True
        manager.preflight.assert_called_once()

    @patch("permissions.create_permission_manager")
    def test_request_macos_permissions_aliases_runtime_permissions(self, mock_create_permission_manager):
        from permissions import request_macos_permissions

        manager = MagicMock()
        manager.preflight.return_value = False
        mock_create_permission_manager.return_value = manager

        assert request_macos_permissions() is False
        manager.preflight.assert_called_once()


class TestCheckOrRequestEventAccess:
    """Tests for macOS event permission helper."""

    def test_returns_true_when_already_granted(self):
        from backends.macos import _check_or_request_event_access

        cg = SimpleNamespace(
            CGPreflightListenEventAccess=MagicMock(return_value=True),
            CGRequestListenEventAccess=MagicMock(return_value=True),
        )

        result = _check_or_request_event_access(
            cg,
            "CGPreflightListenEventAccess",
            "CGRequestListenEventAccess",
            "Input Monitoring",
        )

        assert result is True
        cg.CGRequestListenEventAccess.assert_not_called()

    def test_requests_when_not_granted(self):
        from backends.macos import _check_or_request_event_access

        cg = SimpleNamespace(
            CGPreflightPostEventAccess=MagicMock(return_value=False),
            CGRequestPostEventAccess=MagicMock(return_value=True),
        )

        result = _check_or_request_event_access(
            cg,
            "CGPreflightPostEventAccess",
            "CGRequestPostEventAccess",
            "Accessibility",
        )

        assert result is True
        cg.CGRequestPostEventAccess.assert_called_once()


class TestRequestAutomationPermission:
    """Tests for macOS automation permission check."""

    @patch("backends.macos.subprocess.run")
    def test_returns_true_on_success(self, mock_run):
        from backends.macos import _request_automation_permission

        assert _request_automation_permission() is True
        mock_run.assert_called_once()

    @patch("backends.macos.subprocess.run")
    def test_returns_false_on_denial(self, mock_run):
        from backends.macos import _request_automation_permission

        mock_run.side_effect = subprocess.CalledProcessError(
            returncode=1,
            cmd=["osascript"],
            stderr="not authorized to send Apple events to System Events",
        )
        assert _request_automation_permission() is False


class TestRequestMacosPermissions:
    """Tests for MacOSPermissionManager orchestration."""

    @patch("backends.macos._request_automation_permission")
    @patch("backends.macos._load_core_graphics")
    def test_sets_env_to_disable_applescript_when_automation_missing(
        self, mock_load_core_graphics, mock_request_automation
    ):
        from backends.macos import MacOSPermissionManager

        mock_request_automation.return_value = False
        core_graphics = SimpleNamespace(
            CGPreflightListenEventAccess=MagicMock(return_value=True),
            CGRequestListenEventAccess=MagicMock(return_value=True),
            CGPreflightPostEventAccess=MagicMock(return_value=True),
            CGRequestPostEventAccess=MagicMock(return_value=True),
        )
        mock_load_core_graphics.return_value = core_graphics

        with patch.dict(os.environ, {}, clear=True):
            assert MacOSPermissionManager().preflight() is True
            assert os.environ.get("V2T_DISABLE_APPLESCRIPT") == "1"

    @patch("backends.macos._request_automation_permission", return_value=True)
    @patch("backends.macos._open_settings_for_missing_permissions")
    @patch("backends.macos._load_core_graphics")
    def test_returns_false_when_critical_permissions_missing(
        self, mock_load_core_graphics, mock_open_settings, mock_request_automation
    ):
        from backends.macos import MacOSPermissionManager

        core_graphics = SimpleNamespace(
            CGPreflightListenEventAccess=MagicMock(return_value=False),
            CGRequestListenEventAccess=MagicMock(return_value=False),
            CGPreflightPostEventAccess=MagicMock(return_value=False),
            CGRequestPostEventAccess=MagicMock(return_value=False),
        )
        mock_load_core_graphics.return_value = core_graphics

        assert MacOSPermissionManager().preflight() is False
        mock_open_settings.assert_called_once()
