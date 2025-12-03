# Voice-to-Text macOS App

A macOS application that captures microphone input, transcribes speech using a local Whisper model (`whisper.cpp`), and automatically types the transcribed text into the currently focused text input field.

## Features

- **Hotkey Control**: Press **Right Command** to toggle recording (Start/Stop)
- **Local Transcription**: Uses `pywhispercpp` with the `small.en` model for high-accuracy offline speech-to-text.
- **Automatic Text Injection**: Types transcribed text directly into any focused text field using AppleScript (macOS native).
- **Privacy-First**: All processing happens locally on your Mac.

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
   
   # OR directly with uv
   uv run python main.py
   ```

## Permissions

The app requires the following macOS permissions:

1. **Microphone Access**: Allow when prompted.
2. **Accessibility Access**: Required for input monitoring (hotkeys) and text injection.
   - Go to **System Settings** > **Privacy & Security** > **Accessibility**
   - Add/Enable your Terminal app (e.g., iTerm, Terminal, VS Code)

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