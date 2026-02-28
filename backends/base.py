from dataclasses import dataclass


@dataclass(frozen=True)
class PlatformCapabilities:
    global_hotkeys: bool
    text_injection: bool
    overlay_supported: bool
    permission_prompt_supported: bool
    reason: str | None = None


class BaseTextInjector:
    platform_name = "unknown"

    def type_text(self, text):
        raise NotImplementedError


class NoOpTextInjector(BaseTextInjector):
    platform_name = "disabled"

    def type_text(self, text):
        if text:
            print("Text injection is disabled for this session.", flush=True)


class BasePermissionManager:
    platform_name = "unknown"

    def preflight(self):
        raise NotImplementedError


class NoOpPermissionManager(BasePermissionManager):
    def preflight(self):
        return True
