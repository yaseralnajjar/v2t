from backends import create_text_injector


class TextInjector:
    def __init__(self):
        self.backend = create_text_injector()
        self.keyboard = getattr(self.backend, "keyboard", None)
        self.is_mac = getattr(self.backend, "platform_name", "") == "darwin"
        self._use_applescript = getattr(self.backend, "_use_applescript", False)

    def type_text(self, text):
        self.backend.type_text(text)
        self._use_applescript = getattr(self.backend, "_use_applescript", False)

if __name__ == "__main__":
    print("Testing injector in 3 seconds... Focus a text field!")
    injector = TextInjector()
    import time

    time.sleep(3)
    injector.type_text("Hello from Python!")
