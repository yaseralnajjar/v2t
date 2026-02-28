from pynput.keyboard import Controller
import time
import sys
import subprocess
import os

class TextInjector:
    def __init__(self):
        self.keyboard = Controller()
        self.is_mac = sys.platform == 'darwin'
        self._use_applescript = self.is_mac and os.environ.get("V2T_DISABLE_APPLESCRIPT") != "1"

    def type_text(self, text):
        """
        Type the given text into the currently focused window.
        """
        if not text:
            return
            
        # Add a small delay to ensure focus is correct
        time.sleep(0.1)
        
        if self._use_applescript:
            try:
                # AppleScript is often more reliable on macOS
                # We need to escape backslashes and double quotes for the AppleScript string
                safe_text = text.replace('\\', '\\\\').replace('"', '\\"')
                
                # Construct the AppleScript command
                # We use specific keystroke commands to better handle potential permission issues
                script = f'tell application "System Events" to keystroke "{safe_text}"'
                
                subprocess.run(
                    ['osascript', '-e', script],
                    check=True,
                    capture_output=True,
                    text=True
                )
                
                # Type a space
                subprocess.run(
                    ['osascript', '-e', 'tell application "System Events" to keystroke " "'],
                    check=True,
                    capture_output=True,
                    text=True
                )
                return
            except Exception as e:
                error_details = str(e)
                stderr = getattr(e, "stderr", None)
                if stderr:
                    error_details = f"{error_details} {stderr}"

                # If AppleScript is blocked by permissions, stop retrying it every time.
                if "not allowed to send keystrokes" in error_details:
                    self._use_applescript = False
                    print(
                        "AppleScript text injection is not permitted for this process. "
                        "Falling back to pynput for this session.",
                        flush=True
                    )
                    print(
                        "To fix this: System Settings > Privacy & Security > Accessibility "
                        "and enable your terminal app (Terminal/iTerm/VS Code).",
                        flush=True
                    )
                    print(
                        "Also check: System Settings > Privacy & Security > Automation "
                        "and allow control of System Events.",
                        flush=True
                    )
                else:
                    print(
                        f"AppleScript injection failed: {error_details}. Falling back to pynput.",
                        flush=True
                    )

        # Fallback or non-macOS
        self.keyboard.type(text)
        self.keyboard.type(' ')

if __name__ == "__main__":
    print("Testing injector in 3 seconds... Focus a text field!")
    injector = TextInjector()
    time.sleep(3)
    injector.type_text("Hello from Python!")
