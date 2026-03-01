#!/bin/bash

# Voice-to-Text Launcher
# This script starts the Voice-to-Text app

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Default to push-to-talk mode unless explicitly overridden.
export V2T_MODE="${V2T_MODE:-push_to_talk}"

# Default to the GUI overlay on platforms where it is known to be stable.
if [ -z "${V2T_GUI+x}" ]; then
    PLATFORM_OVERRIDE="$(printf '%s' "${V2T_PLATFORM_BACKEND:-auto}" | tr '[:upper:]' '[:lower:]')"
    if [ "$PLATFORM_OVERRIDE" = "linux" ]; then
        export V2T_GUI=0
    elif [ "$PLATFORM_OVERRIDE" = "auto" ] && [ "$(uname -s)" = "Linux" ]; then
        export V2T_GUI=0
    else
        export V2T_GUI=1
    fi
fi

# Check if another instance is running
if pgrep -f "python.*main.py" > /dev/null; then
    echo "⚠️  Voice-to-Text is already running!"
    echo "To stop it, run: pkill -f 'python.*main.py'"
    exit 1
fi

echo "🎙️  Starting Voice-to-Text..."
echo "Mode: $V2T_MODE"
echo "GUI overlay: $V2T_GUI"
if [ "$V2T_GUI" = "0" ] && [ "$(uname -s)" = "Linux" ]; then
    echo "Set V2T_GUI=1 to force the overlay after installing the required Qt X11 runtime packages."
fi
if [ "$V2T_MODE" = "toggle" ]; then
    echo "Press Right Command to toggle recording (Start/Stop)"
else
    echo "Hold Right Command to record, release to transcribe"
fi
echo "Press Ctrl+C to quit"
echo ""

uv run python main.py
