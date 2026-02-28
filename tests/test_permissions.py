"""Unit tests for permissions.py."""

import os
import subprocess
from types import SimpleNamespace
from unittest.mock import MagicMock, patch


class TestCheckOrRequestEventAccess:
    """Tests for _check_or_request_event_access helper."""

    def test_returns_true_when_already_granted(self):
        from permissions import _check_or_request_event_access

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
        from permissions import _check_or_request_event_access

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
    """Tests for automation permission check."""

    @patch("permissions.subprocess.run")
    def test_returns_true_on_success(self, mock_run):
        from permissions import _request_automation_permission

        assert _request_automation_permission() is True
        mock_run.assert_called_once()

    @patch("permissions.subprocess.run")
    def test_returns_false_on_denial(self, mock_run):
        from permissions import _request_automation_permission

        mock_run.side_effect = subprocess.CalledProcessError(
            returncode=1,
            cmd=["osascript"],
            stderr="not authorized to send Apple events to System Events",
        )
        assert _request_automation_permission() is False


class TestRequestMacosPermissions:
    """Tests for request_macos_permissions orchestration."""

    @patch("permissions._request_automation_permission")
    @patch("permissions._load_core_graphics")
    @patch("permissions.sys.platform", "linux")
    def test_skips_on_non_macos(self, mock_load_core_graphics, mock_request_automation):
        from permissions import request_macos_permissions

        assert request_macos_permissions() is True

        mock_load_core_graphics.assert_not_called()
        mock_request_automation.assert_not_called()

    @patch("permissions._request_automation_permission", return_value=False)
    @patch("permissions._open_settings_for_missing_permissions")
    @patch("permissions._load_core_graphics")
    @patch("permissions.sys.platform", "darwin")
    def test_sets_env_to_disable_applescript_when_automation_missing(
        self, mock_load_core_graphics, mock_open_settings, mock_request_automation
    ):
        from permissions import request_macos_permissions

        core_graphics = SimpleNamespace(
            CGPreflightListenEventAccess=MagicMock(return_value=True),
            CGRequestListenEventAccess=MagicMock(return_value=True),
            CGPreflightPostEventAccess=MagicMock(return_value=True),
            CGRequestPostEventAccess=MagicMock(return_value=True),
        )
        mock_load_core_graphics.return_value = core_graphics

        with patch.dict(os.environ, {}, clear=True):
            assert request_macos_permissions() is True
            assert os.environ.get("V2T_DISABLE_APPLESCRIPT") == "1"
        mock_open_settings.assert_called_once()

    @patch("permissions._request_automation_permission", return_value=True)
    @patch("permissions._open_settings_for_missing_permissions")
    @patch("permissions._load_core_graphics")
    @patch("permissions.sys.platform", "darwin")
    def test_returns_false_when_critical_permissions_missing(
        self, mock_load_core_graphics, mock_open_settings, mock_request_automation
    ):
        from permissions import request_macos_permissions

        core_graphics = SimpleNamespace(
            CGPreflightListenEventAccess=MagicMock(return_value=False),
            CGRequestListenEventAccess=MagicMock(return_value=False),
            CGPreflightPostEventAccess=MagicMock(return_value=False),
            CGRequestPostEventAccess=MagicMock(return_value=False),
        )
        mock_load_core_graphics.return_value = core_graphics

        assert request_macos_permissions() is False
        mock_open_settings.assert_called_once()
