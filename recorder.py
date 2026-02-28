import numpy as np
import queue
import threading

try:
    import sounddevice as sd
except OSError:
    class _MissingSoundDevice:
        class InputStream:
            def __init__(self, *args, **kwargs):
                raise OSError("PortAudio library not found")

        def query_devices(self, *args, **kwargs):
            raise OSError("PortAudio library not found")

    sd = _MissingSoundDevice()

class AudioRecorder:
    def __init__(self, samplerate=16000, channels=1):
        self.samplerate = samplerate
        self.channels = channels
        self.q = queue.Queue()
        self.recording = False
        self.stream = None
        self._level_lock = threading.Lock()
        self._current_level = 0.0

    def get_input_device_info(self):
        """Get information about the current default input device."""
        try:
            device_info = sd.query_devices(kind='input')
            return device_info['name']
        except Exception as e:
            return f"Unknown (error: {e})"

    def get_current_level(self):
        """Return a normalized live input level in range [0.0, 1.0]."""
        with self._level_lock:
            return self._current_level

    def _callback(self, indata, frames, time, status):
        """This is called (from a separate thread) for each audio block."""
        if status:
            print(status, flush=True)

        if indata.size:
            rms = float(np.sqrt(np.mean(np.square(indata))))
            normalized = min(1.0, rms * 8.0)
        else:
            normalized = 0.0

        with self._level_lock:
            self._current_level = normalized if self.recording else 0.0

        if self.recording:
            self.q.put(indata.copy())

    def start(self):
        """Start recording audio."""
        if self.recording:
            return
        self.recording = True
        self.q.queue.clear()
        with self._level_lock:
            self._current_level = 0.0
        self.stream = sd.InputStream(
            samplerate=self.samplerate,
            channels=self.channels,
            callback=self._callback
        )
        self.stream.start()
        print("Recording started...", flush=True)

    def stop(self):
        """Stop recording and return the audio data."""
        if not self.recording:
            with self._level_lock:
                self._current_level = 0.0
            return np.array([])
        
        self.recording = False
        with self._level_lock:
            self._current_level = 0.0
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        
        print("Recording stopped.", flush=True)
        
        # Collect all data from the queue
        data = []
        while not self.q.empty():
            data.append(self.q.get())
        
        if not data:
            return np.array([])
            
        return np.concatenate(data, axis=0)

if __name__ == "__main__":
    # Test the recorder
    import time
    recorder = AudioRecorder()
    print("Press Ctrl+C to stop manually if needed, but this test runs for 3 seconds.")
    recorder.start()
    time.sleep(3)
    audio = recorder.stop()
    print(f"Recorded {len(audio)} samples.")
