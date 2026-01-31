from pywhispercpp.model import Model
import numpy as np
import os
import config

class AudioTranscriber:
    def __init__(self):
        self.model_name = config.MODEL
        project_root = os.path.dirname(os.path.abspath(__file__))

        # Check if MODEL is a full path to a file
        if os.path.isfile(self.model_name):
            model_path = self.model_name
        else:
            # Look for local model in models/whisper-cpp/
            model_path = os.path.join(project_root, "models", "whisper-cpp", "ggml-model.bin")

        if os.path.exists(model_path):
            print(f"Loading Whisper model from '{model_path}'...", flush=True)
            self.model = Model(model_path, print_realtime=False, print_progress=False, redirect_whispercpp_logs_to=None)
        else:
            print(f"Downloading Whisper model '{self.model_name}'...", flush=True)
            self.model = Model(self.model_name, print_realtime=False, print_progress=False, redirect_whispercpp_logs_to=None)

        print("Model loaded.", flush=True)

    def get_model_name(self):
        """Return the configured model name."""
        return self.model_name

    def transcribe(self, audio_data):
        """
        Transcribe audio data (numpy array).
        Returns the transcribed text string.
        """
        if len(audio_data) == 0:
            return ""

        # Flatten to 1D if needed (sounddevice returns (n, channels))
        if audio_data.ndim > 1:
            audio_data = audio_data.flatten()

        # pywhispercpp expects float32 audio
        if audio_data.dtype != np.float32:
            audio_data = audio_data.astype(np.float32)

        # Normalize audio if it's too quiet
        max_val = np.max(np.abs(audio_data))
        if max_val > 0:
            # Normalize to 0.5 peak (conservative) to avoid clipping if it was just quiet
            # Or just scale it up if it's very low.
            # Let's try simple peak normalization if max < 0.5
            if max_val < 0.5:
                audio_data = audio_data / max_val * 0.5

        # pywhispercpp transcribe returns a list of segments
        try:
            segments = self.model.transcribe(audio_data)
            text = []
            for segment in segments:
                text.append(segment.text)
            return "".join(text).strip()
        except Exception as e:
            print(f"Transcription error: {e}", flush=True)
            return ""

if __name__ == "__main__":
    # Test the transcriber (needs a dummy audio or real one)
    # We can generate a silent buffer to test model loading and interface
    print("Testing transcriber with silence...")
    transcriber = AudioTranscriber()
    # 1 second of silence at 16kHz
    silence = np.zeros(16000, dtype=np.float32)
    result = transcriber.transcribe(silence)
    print(f"Transcription result: '{result}'")
