from pynput import keyboard
import threading
import time
import sys
import signal
import os
from recorder import AudioRecorder
from transcriber import AudioTranscriber
from injector import TextInjector
from sounds import play_start_sound, play_stop_sound
from permissions import request_macos_permissions


class VoiceToTextApp:
    def __init__(self):
        self.recorder = AudioRecorder()
        self.transcriber = AudioTranscriber()
        self.injector = TextInjector()
        self.is_recording = False
        self.shutdown_event = threading.Event()

        # Recording mode: "toggle" or "push_to_talk"
        # Set via V2T_MODE environment variable (default: push_to_talk)
        self.mode = os.environ.get("V2T_MODE", "push_to_talk").lower()
        if self.mode not in ("toggle", "push_to_talk", "ptt"):
            print(f"Warning: Unknown V2T_MODE '{self.mode}', using 'push_to_talk'")
            self.mode = "push_to_talk"
        if self.mode == "ptt":
            self.mode = "push_to_talk"

        # Hotkey configuration: Right Command only.
        self.HOTKEY = {keyboard.Key.cmd_r}
        self.hotkey_down = set()

        # Keep transcriptions in order and avoid concurrent text injection races.
        self._transcribe_count_lock = threading.Lock()
        self._transcribe_worker_lock = threading.Lock()
        self._active_transcriptions = 0

        self.overlay = self._create_overlay()

    def _env_flag(self, key, default=True):
        value = os.environ.get(key)
        if value is None:
            return default
        return value.strip().lower() not in ("0", "false", "off", "no")

    def _create_overlay(self):
        if not self._env_flag("V2T_GUI", default=True):
            return None

        try:
            from gui_overlay import FloatingOverlay

            return FloatingOverlay(
                get_level=self.recorder.get_current_level,
                mode=self.mode,
                hotkey_label="Right Command",
            )
        except Exception as e:
            print(f"Warning: GUI overlay disabled ({e})", flush=True)
            return None

    def _set_overlay_state(self, state):
        if self.overlay:
            self.overlay.set_state_threadsafe(state)

    def _on_recording_start(self):
        self._set_overlay_state("recording")

    def _on_recording_stop(self):
        with self._transcribe_count_lock:
            has_pending = self._active_transcriptions > 0
        if not has_pending:
            self._set_overlay_state("idle")

    def _on_transcribe_start(self):
        self._set_overlay_state("transcribing")

    def _on_transcribe_end(self):
        with self._transcribe_count_lock:
            has_pending = self._active_transcriptions > 0
        if not self.is_recording and not has_pending:
            self._set_overlay_state("idle")

    def _begin_transcription(self):
        should_notify = False
        with self._transcribe_count_lock:
            self._active_transcriptions += 1
            if self._active_transcriptions == 1:
                should_notify = True
        if should_notify:
            self._on_transcribe_start()

    def _end_transcription(self):
        should_notify = False
        with self._transcribe_count_lock:
            if self._active_transcriptions > 0:
                self._active_transcriptions -= 1
            if self._active_transcriptions == 0:
                should_notify = True
        if should_notify:
            self._on_transcribe_end()

    def _is_hotkey(self, key):
        if key in self.HOTKEY:
            return True
        # Match Right Command by virtual key as an extra guard.
        value = getattr(key, "value", None)
        vk = getattr(value, "vk", None)
        return vk == 54

    def _key_id(self, key):
        value = getattr(key, "value", None)
        return getattr(value, "vk", key)

    def on_press(self, key):
        if not self._is_hotkey(key):
            return

        key_id = self._key_id(key)
        already_held = bool(self.hotkey_down)
        self.hotkey_down.add(key_id)

        # Ignore duplicate press callbacks while the hotkey is already held.
        if already_held:
            return

        if self.mode == "toggle":
            if self.is_recording:
                self.stop_recording_and_transcribe()
            else:
                self.start_recording()
        else:  # push_to_talk
            if not self.is_recording:
                self.start_recording()

    def on_release(self, key):
        if not self._is_hotkey(key):
            return

        key_id = self._key_id(key)
        self.hotkey_down.discard(key_id)

        # Only stop when all hotkey variants are released.
        if self.hotkey_down:
            return

        if self.mode == "push_to_talk" and self.is_recording:
            self.stop_recording_and_transcribe()

    def start_recording(self):
        print("Hotkey pressed! Starting recording...", flush=True)
        play_start_sound()
        self.is_recording = True
        self.recorder.start()
        self._on_recording_start()

    def stop_recording_and_transcribe(self):
        print("Hotkey released! Stopping recording...", flush=True)
        play_stop_sound()
        self.is_recording = False
        audio_data = self.recorder.stop()

        if len(audio_data) == 0:
            print("No audio recorded.", flush=True)
            self._on_recording_stop()
            return

        self._begin_transcription()
        self._on_recording_stop()

        print("Transcribing...", flush=True)
        try:
            threading.Thread(target=self._process_audio, args=(audio_data,), daemon=True).start()
        except Exception:
            self._end_transcription()
            raise

    def _process_audio(self, audio_data):
        try:
            with self._transcribe_worker_lock:
                text = self.transcriber.transcribe(audio_data)
                print(f"Transcribed: '{text}'", flush=True)
                if text:
                    self.injector.type_text(text)
        except Exception as e:
            print(f"Error during processing: {e}", flush=True)
        finally:
            self._end_transcription()

    def run(self):
        print("Voice-to-Text App Running...")
        print(f"Model: {self.transcriber.get_model_name()}")
        print(f"Audio input: {self.recorder.get_input_device_info()}")
        print(f"Mode: {self.mode}")
        print(f"GUI overlay: {'enabled' if self.overlay else 'disabled'}")
        if self.mode == "toggle":
            print("Press Right Command to toggle recording (Start/Stop).")
        else:
            print("Hold Right Command to record, release to transcribe.")
        print("Press Ctrl+C to exit.")

        listener = keyboard.Listener(on_press=self.on_press, on_release=self.on_release)
        listener.start()

        try:
            if self.overlay:
                self._set_overlay_state("idle")
                self.overlay.run(self.shutdown_event)
            else:
                while not self.shutdown_event.is_set():
                    time.sleep(0.1)
        finally:
            listener.stop()
            if self.is_recording:
                self.recorder.stop()
                self.is_recording = False
            if self.overlay:
                self.overlay.close()


if __name__ == "__main__":
    if not request_macos_permissions():
        sys.exit(1)
    app = VoiceToTextApp()

    def signal_handler(signum, frame):
        app.shutdown_event.set()

    signal.signal(signal.SIGINT, signal_handler)

    app.run()
    print("Exiting...")
