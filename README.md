# Voice-to-Text Desktop App

A desktop application that captures microphone input, transcribes speech using a local Whisper model (`whisper.cpp`), and types the transcribed text into the currently focused text input field.

## Features

- **Push-to-Talk by Default**: Hold **Right Command** to record, release to transcribe
- **Floating GUI Overlay**: Minimal always-on-top pill with hover hint and live wave animation
- **Audio Feedback**: Distinct tones when recording starts/stops
- **Local Transcription**: Uses `pywhispercpp` with configurable Whisper models for offline speech-to-text
- **Automatic Text Injection**: Uses platform backends for focused-field typing
- **Privacy-First**: All processing happens locally on your machine
- **Startup Info**: Shows selected audio input device and model on launch

## Platform Status

- **macOS**: Full path. Global hotkeys, overlay, permission preflight, and AppleScript typing are supported.
- **Windows**: Experimental. `pynput` hotkeys are available; typing supports `pynput` and a native `SendInput` backend.
- **Linux X11**: Experimental. `pynput` hotkeys and typing are supported.
- **Linux Wayland**: Degraded mode only by default. Global hotkeys and text injection are intentionally disabled.

## Installation

### Prerequisites
- Python 3.12+
- `uv` package manager (recommended)
- Desktop session with microphone access

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

Linux and Windows do not currently perform OS-native permission prompting. On Linux Wayland, global hotkeys and synthetic typing are disabled unless you add a custom backend.

## Native Backend Requirements

The `native` backend modes are platform-specific and depend on external OS APIs or tools:

- **Windows native text injection**: `V2T_INJECT_MODE=native` uses Win32 `SendInput` and does not require extra tools.
- **Windows native hotkeys**: `V2T_HOTKEY_BACKEND=native` uses `GetAsyncKeyState` polling for **Right Ctrl**.
- **Linux X11 native text injection**: `V2T_INJECT_MODE=native` requires `xdotool` to be installed and available on `PATH`.
- **Linux X11 native hotkeys**: `V2T_HOTKEY_BACKEND=native` requires `xinput` to be installed and available on `PATH`.
- **Linux Wayland**: native hotkey and injection backends are not implemented. Use degraded mode with `V2T_ALLOW_DEGRADED_MODE=1`.

Example Linux packages:

```bash
# Debian/Ubuntu
sudo apt-get install xdotool xinput
```

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

### Recording Mode

You can configure recording behavior with `V2T_MODE`:

```bash
# Default: push-to-talk mode (hold to record, release to transcribe)
./start.sh

# Push-to-talk mode (hold to record, release to transcribe)
V2T_MODE=push_to_talk ./start.sh
# Alias:
V2T_MODE=ptt ./start.sh

# Explicit toggle mode (press once to start, press again to stop)
V2T_MODE=toggle ./start.sh
```

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

### GUI Overlay

You can enable/disable the floating overlay with `V2T_GUI`:

```bash
# Default: enabled
./start.sh

# Disable overlay and run in terminal-only mode
V2T_GUI=0 ./start.sh
```

### Platform Backends

You can force backend selection during testing or troubleshooting:

```bash
# Override platform detection
V2T_PLATFORM_BACKEND=windows uv run python main.py
V2T_PLATFORM_BACKEND=linux uv run python main.py

# Force Linux session detection
V2T_LINUX_SESSION=x11 uv run python main.py
V2T_LINUX_SESSION=wayland uv run python main.py

# Choose text injection backend
V2T_INJECT_MODE=auto ./start.sh
V2T_INJECT_MODE=pynput ./start.sh
V2T_INJECT_MODE=native ./start.sh
V2T_INJECT_MODE=disabled ./start.sh

# Choose hotkey backend
V2T_HOTKEY_BACKEND=auto ./start.sh
V2T_HOTKEY_BACKEND=pynput ./start.sh
V2T_HOTKEY_BACKEND=native ./start.sh
V2T_HOTKEY_BACKEND=disabled ./start.sh

# Allow startup without global hotkeys
V2T_ALLOW_DEGRADED_MODE=1 ./start.sh
```

Notes:
- macOS defaults to the AppleScript injector unless `V2T_INJECT_MODE=pynput` is set.
- Windows defaults to `pynput`; `V2T_INJECT_MODE=native` enables the `SendInput` path.
- Windows `V2T_HOTKEY_BACKEND=native` uses a polling-based `GetAsyncKeyState` backend for **Right Ctrl**.
- Linux X11 defaults to `pynput`; `V2T_INJECT_MODE=native` requires `xdotool`, and `V2T_HOTKEY_BACKEND=native` requires `xinput`.
- Linux Wayland and unknown Linux sessions require `V2T_ALLOW_DEGRADED_MODE=1` to continue without hotkeys.

## Usage

1. Launch the app.
2. Hold the configured hotkey to start recording.
3. Speak your text.
4. Release the hotkey to stop and transcribe.
5. Wait a moment for transcription; the text will appear in your active window.

## Technical Details

- **Language**: Python 3.12
- **GUI**: PySide6 (Qt for Python)
- **Transcription**: pywhispercpp (Bindings for whisper.cpp)
- **Model**: small.en (GGML format)
- **Audio**: sounddevice + numpy
- **Input/Output**: pynput, AppleScript, Win32 `SendInput`

## License

[Add License Here]
