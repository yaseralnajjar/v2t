#!/bin/bash

# Voice-to-Text Launcher
# This script starts the Voice-to-Text app

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Default to push-to-talk mode unless explicitly overridden.
export V2T_MODE="${V2T_MODE:-push_to_talk}"

# Check if another instance is running
if pgrep -f "python.*main.py" > /dev/null; then
    echo "⚠️  Voice-to-Text is already running!"
    echo "To stop it, run: pkill -f 'python.*main.py'"
    exit 1
fi

echo "🎙️  Starting Voice-to-Text..."
echo "Mode: $V2T_MODE"
if [ "$V2T_MODE" = "toggle" ]; then
    echo "Press Right Command to toggle recording (Start/Stop)"
else
    echo "Hold Right Command to record, release to transcribe"
fi
echo "Press Ctrl+C to quit"
echo ""

uv run python main.py
