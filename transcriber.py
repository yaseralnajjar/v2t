from pywhispercpp.model import Model
import numpy as np
import os

class AudioTranscriber:
    def __init__(self, model_size="base.en", device="cpu"):
        # device param is kept for compatibility but pywhispercpp handles backend selection automatically (e.g. Metal on Mac)
        # We construct the local model path assuming it's relative to the project root or in a known location
        # Adjust the path as per your project structure. Here assuming 'models/whisper-cpp/ggml-model.bin'
        # exists for the 'base.en' model. If model_size changes, this path logic needs to be dynamic or configured.
        
        # For this specific setup, we are using the converted 'base.en' model located at:
        project_root = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(project_root, "models", "whisper-cpp", "ggml-model.bin")
        
        if not os.path.exists(model_path):
             print(f"Warning: Local model not found at {model_path}. pywhispercpp might try to download or fail.", flush=True)
             # Fallback logic or just pass model_size to let pywhispercpp handle it (it downloads to its own cache)
             # But since we want to use our manually converted/downloaded model:
             self.model = Model(model_size, print_realtime=False, print_progress=False)
        else:
             print(f"Loading Whisper model from '{model_path}'...", flush=True)
             self.model = Model(model_path, print_realtime=False, print_progress=False)
             
        print("Model loaded.", flush=True)

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
