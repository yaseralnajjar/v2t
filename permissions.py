from backends import create_permission_manager
from backends.macos import (
    _check_or_request_event_access,
    _load_core_graphics,
    _open_settings_for_missing_permissions,
    _request_automation_permission,
)


def request_runtime_permissions():
    return create_permission_manager().preflight()


def request_macos_permissions():
    return request_runtime_permissions()
