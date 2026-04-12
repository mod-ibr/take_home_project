"""
config.py
---------
Centralised configuration for the method_1_screenseeker project.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# ── Load .env ────────────────────────────────────────────────────────────────
_env_path = Path(__file__).parent / ".env"
if _env_path.exists():
    load_dotenv(dotenv_path=_env_path, override=True)

# ── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
DEBUG_DIR = BASE_DIR / "debug"
SCREENSHOT_DIR = DEBUG_DIR / "screenshots"
OUTPUT_DIR = os.path.join(os.path.expanduser("~"), "Desktop", "tjm-project")

# ── API Token ────────────────────────────────────────────────────────────────
HF_TOKEN = os.environ.get("HF_TOKEN", "")

# ── Grounding Config ────────────────────────────────────────────────────────
RETRY_COUNT = 3
RETRY_DELAY = 1.0
REGROUND_SIZE = 400
MOUSE_DURATION = 0.5

# ── Instruction for VLM ─────────────────────────────────────────────────────
NOTEPAD_INSTRUCTION = (
    "Notepad application shortcut icon on the Windows desktop. "
    "It looks like a small notepad with lines on it."
)
