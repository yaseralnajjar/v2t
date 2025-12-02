import whisper
import numpy as np
import os

class AudioTranscriber:
    def __init__(self, model_size="base.en", device="cpu"):
        print(f"Loading Whisper model '{model_size}' on {device}...", flush=True)
        self.model = whisper.load_model(model_size, device=device)
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

        # openai-whisper expects float32 audio
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

        # openai-whisper transcribe
        # fp16=False for CPU to avoid warnings/errors if not supported
        result = self.model.transcribe(audio_data, fp16=False)
        
        return result["text"].strip()

if __name__ == "__main__":
    # Test the transcriber (needs a dummy audio or real one)
    # We can generate a silent buffer to test model loading and interface
    print("Testing transcriber with silence...")
    transcriber = AudioTranscriber()
    # 1 second of silence at 16kHz
    silence = np.zeros(16000, dtype=np.float32)
    result = transcriber.transcribe(silence)
    print(f"Transcription result: '{result}'")
