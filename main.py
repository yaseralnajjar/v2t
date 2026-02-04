from pynput import keyboard
import numpy as np
import threading
import time
import sys
import signal
from recorder import AudioRecorder
from transcriber import AudioTranscriber
from injector import TextInjector
from sounds import play_start_sound, play_stop_sound

class VoiceToTextApp:
    def __init__(self):
        self.recorder = AudioRecorder()
        self.transcriber = AudioTranscriber()
        self.injector = TextInjector()
        self.is_recording = False
        self.shutdown_event = threading.Event()

        # Hotkey configuration: Right Command
        self.HOTKEY = {keyboard.Key.cmd_r}
        self.current_keys = set()

    def on_press(self, key):
        if key in self.HOTKEY:
            # Toggle logic
            if self.is_recording:
                self.stop_recording_and_transcribe()
            else:
                self.start_recording()

    def on_release(self, key):
        # No action on release for toggle mode
        
        if key == keyboard.Key.esc:
            # Optional: Exit app on ESC? Or maybe just keep running.
            # Let's keep running, but maybe print a message.
            pass

    def start_recording(self):
        print("Hotkey pressed! Starting recording...", flush=True)
        play_start_sound()
        self.is_recording = True
        self.recorder.start()

    def stop_recording_and_transcribe(self):
        print("Hotkey released! Stopping recording...", flush=True)
        play_stop_sound()
        self.is_recording = False
        audio_data = self.recorder.stop()
        
        if len(audio_data) == 0:
            print("No audio recorded.", flush=True)
            return

        print("Transcribing...", flush=True)
        # Run transcription in a separate thread to not block the listener?
        # Actually, we want to block or at least process it. 
        # Since we are in the listener callback, we should be careful not to block it for too long if we want to detect other keys.
        # But for this simple app, blocking the listener might be okay, or we can offload to a thread.
        # Let's offload to a thread to keep the UI/Hotkey responsive.
        threading.Thread(target=self._process_audio, args=(audio_data,), daemon=True).start()

    def _process_audio(self, audio_data):
        try:
            text = self.transcriber.transcribe(audio_data)
            print(f"Transcribed: '{text}'", flush=True)
            if text:
                self.injector.type_text(text)
        except Exception as e:
            print(f"Error during processing: {e}", flush=True)

    def run(self):
        print("Voice-to-Text App Running...")
        print(f"Model: {self.transcriber.get_model_name()}")
        print(f"Audio input: {self.recorder.get_input_device_info()}")
        print("Press Right Command to toggle recording (Start/Stop).")
        print("Press Ctrl+C to exit.")

        listener = keyboard.Listener(on_press=self.on_press, on_release=self.on_release)
        listener.start()

        try:
            while not self.shutdown_event.is_set():
                time.sleep(0.1)
        finally:
            listener.stop()
            if self.is_recording:
                self.recorder.stop()

if __name__ == "__main__":
    app = VoiceToTextApp()

    def signal_handler(signum, frame):
        app.shutdown_event.set()

    signal.signal(signal.SIGINT, signal_handler)

    app.run()
    print("Exiting...")
