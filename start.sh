#!/bin/bash

# Voice-to-Text Launcher
# This script starts the Voice-to-Text app

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if another instance is running
if pgrep -f "python.*main.py" > /dev/null; then
    echo "⚠️  Voice-to-Text is already running!"
    echo "To stop it, run: pkill -f 'python.*main.py'"
    exit 1
fi

echo "🎙️  Starting Voice-to-Text..."
echo "Press Right Command to toggle recording (Start/Stop)"
echo "Press Ctrl+C to quit"
echo ""

uv run python main.py
