# Voice-to-Text macOS App

A macOS application that captures microphone input, transcribes speech using a local Whisper model (`whisper.cpp`), and automatically types the transcribed text into the currently focused text input field.

## Features

- **Hotkey Control**: Press **Right Command** to toggle recording (Start/Stop)
- **Audio Feedback**: Distinct tones when recording starts/stops
- **Local Transcription**: Uses `pywhispercpp` with configurable Whisper models for offline speech-to-text
- **Automatic Text Injection**: Types transcribed text directly into any focused text field using AppleScript (macOS native)
- **Privacy-First**: All processing happens locally on your Mac
- **Startup Info**: Shows selected audio input device and model on launch

## Installation

### Prerequisites
- Python 3.12+
- `uv` package manager (recommended)
- macOS (for text injection and optimizations)

### Setup

1. **Clone the repository**
   ```bash
   git clone <repo-url>
   cd v2t
   ```

2. **Install dependencies**
   ```bash
   uv sync
   ```

3. **Model Setup (Important)**
   Due to network restrictions in some environments, the model might not download automatically. You need a GGML-converted Whisper model.
   
   - **Option A (Automatic):** The app attempts to download the model on first run.
   - **Option B (Manual):** If automatic download fails:
     1. Download or convert a Whisper model to GGML format (e.g., `ggml-small.en.bin`).
     2. Place it at: `models/whisper-cpp/ggml-model.bin`

4. **Run the App**
   ```bash
   # Using the launcher
   ./start.sh

   # OR directly with uv (from the project directory)
   uv run python ./main.py
   ```

## Permissions

The app requires the following macOS permissions:

1. **Microphone Access**: Allow when prompted.
2. **Accessibility Access**: Required for input monitoring (hotkeys) and text injection.
   - Go to **System Settings** > **Privacy & Security** > **Accessibility**
   - Add/Enable your Terminal app (e.g., iTerm, Terminal, VS Code)
3. **Input Monitoring**: Required for global hotkey listening.
4. **Automation (System Events)**: Required for AppleScript text injection.

On startup, the app now performs a best-effort permission preflight and requests missing access where macOS allows prompting.  
If permission was previously denied, macOS may not show the prompt again; grant it manually in **System Settings**.

## Configuration

You can configure the Whisper model using the `V2T_MODEL` environment variable:

```bash
# Use a different model size
V2T_MODEL=tiny.en ./start.sh
V2T_MODEL=medium.en ./start.sh
V2T_MODEL=large-v3-turbo ./start.sh

# Or use a custom model path
V2T_MODEL=/path/to/your/model.bin ./start.sh

# With uv run directly
V2T_MODEL=large-v3 uv run python ./main.py

# Export for the session
export V2T_MODEL=medium.en
./start.sh
```

Available models:

| Model | Size | Speed | Best for |
|-------|------|-------|----------|
| `tiny.en` | 39M | Fastest | Quick drafts, low latency |
| `base.en` | 74M | Fast | Good balance for English |
| `small.en` | 244M | Moderate | **Default** - accurate English |
| `medium.en` | 769M | Slow | High accuracy English |
| `large-v3` | 1.5G | Slowest | Multilingual, accents |
| `large-v3-turbo` | 1.5G | Slow | Faster large model |

The `.en` models are English-only but faster and more accurate for English speech.

### Sound Type

You can configure the audio feedback sounds using the `V2T_SOUND` environment variable:

```bash
# Use bloop sound effects (default)
./start.sh

# Use warm bloop tones with rich harmonics
V2T_SOUND=warm ./start.sh

# Use simple sine wave tones (880Hz/440Hz)
V2T_SOUND=simple ./start.sh

# Use short click sounds
V2T_SOUND=click ./start.sh
```

| Value | Description |
|-------|-------------|
| `bloop` | Bloop sound effects from wav files (default) |
| `warm` | Warm bloop tones with rich harmonics |
| `simple` | Simple sine wave tones |
| `click` | Short click sounds |

## Usage

1. Launch the app.
2. Press **Right Command** once to start recording.
3. Speak your text.
4. Press **Right Command** again to stop.
5. Wait a moment for transcription; the text will appear in your active window.

## Technical Details

- **Language**: Python 3.12
- **Transcription**: pywhispercpp (Bindings for whisper.cpp)
- **Model**: small.en (GGML format)
- **Audio**: sounddevice + numpy
- **Input/Output**: pynput (monitoring), AppleScript (injection)

## License

[Add License Here]
