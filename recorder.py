import sounddevice as sd
import numpy as np
import queue
import threading

class AudioRecorder:
    def __init__(self, samplerate=16000, channels=1):
        self.samplerate = samplerate
        self.channels = channels
        self.q = queue.Queue()
        self.recording = False
        self.stream = None

    def get_input_device_info(self):
        """Get information about the current default input device."""
        try:
            device_info = sd.query_devices(kind='input')
            return device_info['name']
        except Exception as e:
            return f"Unknown (error: {e})"

    def _callback(self, indata, frames, time, status):
        """This is called (from a separate thread) for each audio block."""
        if status:
            print(status, flush=True)
        if self.recording:
            self.q.put(indata.copy())

    def start(self):
        """Start recording audio."""
        if self.recording:
            return
        self.recording = True
        self.q.queue.clear()
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
            return np.array([])
        
        self.recording = False
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
