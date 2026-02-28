"""Shared pytest fixtures and configuration."""

import os
import sys
from pathlib import Path
import pytest

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture(autouse=True)
def disable_gui_overlay():
    """Keep tests headless and deterministic."""
    original = os.environ.get("V2T_GUI")
    os.environ["V2T_GUI"] = "0"
    try:
        yield
    finally:
        if original is None:
            os.environ.pop("V2T_GUI", None)
        else:
            os.environ["V2T_GUI"] = original
