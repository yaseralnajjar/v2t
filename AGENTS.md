# Repository Guidelines

## Project Structure & Module Organization
This repository is a small Python 3.12 macOS app with a flat module layout at the repo root. Core runtime files include `main.py` (app orchestration), `recorder.py` (audio capture), `transcriber.py` (Whisper integration), `injector.py` (text injection), `gui_overlay.py` (floating UI), and `permissions.py` (macOS access checks). Sound providers live in `sounds/`. Static assets live in `assets/icons/` and `assets/sounds/`. Tests are in `tests/` and mirror the runtime modules, for example `tests/test_main.py` and `tests/test_transcriber.py`.

## Build, Test, and Development Commands
Install dependencies with `uv sync`. Run the app with `./start.sh` for the standard launcher or `uv run python main.py` for direct execution. Run the full test suite with `uv run pytest`. Target a single file with `uv run pytest tests/test_main.py`. Package tooling is listed in `pyproject.toml`; `pyinstaller` is available in the dev group when packaging work is needed.

## Coding Style & Naming Conventions
Follow existing Python style: 4-space indentation, `snake_case` for functions and variables, `CapWords` for classes, and short module names such as `config.py` or `recorder.py`. Keep files focused on one responsibility. Prefer explicit, readable control flow over compact abstractions. Match the current import style and docstring usage in touched files. No formatter or linter is configured here, so keep changes consistent with surrounding code and run tests before submitting.

## Testing Guidelines
Use `pytest`; test discovery is configured through `pyproject.toml` with `tests/` as the test root. Add or update tests whenever behavior changes, especially around hotkey handling, permissions, configuration env vars, and transcription flow. Name test files `test_<module>.py` and test functions `test_<behavior>`. There is no documented coverage gate, but avoid shipping untested logic changes.

## Commit & Pull Request Guidelines
Recent commits use short, imperative summaries such as `Add app icon`, `Improve placement`, and `Fix jumping behavior`. Keep commit messages concise, present tense, and scoped to one change. Pull requests should explain user-visible behavior, list test coverage, and note any macOS-specific setup or permission impacts. Include screenshots or short recordings for overlay or asset changes.

## Security & Configuration Tips
Do not commit local models, secrets, or machine-specific paths. Prefer environment variables such as `V2T_MODEL`, `V2T_MODE`, `V2T_GUI`, and `V2T_SOUND` for local configuration. When documenting reproduction steps, note that microphone, accessibility, input monitoring, and automation permissions are required on macOS.
