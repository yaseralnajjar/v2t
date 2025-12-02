from pynput.keyboard import Controller
import time
import sys
import subprocess

class TextInjector:
    def __init__(self):
        self.keyboard = Controller()
        self.is_mac = sys.platform == 'darwin'

    def type_text(self, text):
        """
        Type the given text into the currently focused window.
        """
        if not text:
            return
            
        # Add a small delay to ensure focus is correct
        time.sleep(0.1)
        
        if self.is_mac:
            try:
                # AppleScript is often more reliable on macOS
                # We need to escape backslashes and double quotes for the AppleScript string
                safe_text = text.replace('\\', '\\\\').replace('"', '\\"')
                
                # Construct the AppleScript command
                # We use specific keystroke commands to better handle potential permission issues
                script = f'tell application "System Events" to keystroke "{safe_text}"'
                
                subprocess.run(['osascript', '-e', script], check=True)
                
                # Type a space
                subprocess.run(['osascript', '-e', 'tell application "System Events" to keystroke " "'], check=True)
                return
            except Exception as e:
                print(f"AppleScript injection failed: {e}. Falling back to pynput.", flush=True)

        # Fallback or non-macOS
        self.keyboard.type(text)
        self.keyboard.type(' ')

if __name__ == "__main__":
    print("Testing injector in 3 seconds... Focus a text field!")
    injector = TextInjector()
    time.sleep(3)
    injector.type_text("Hello from Python!")
