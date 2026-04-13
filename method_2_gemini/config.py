"""
config.py
---------
Centralised configuration for the method_2_gemini project.
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

# ── API Key ──────────────────────────────────────────────────────────────────
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# ── Gemini Model ─────────────────────────────────────────────────────────────
GEMINI_MODEL_ID = "gemini-3.1-flash-lite-preview"

# ── Grounding Config ────────────────────────────────────────────────────────
RETRY_COUNT = 3
RETRY_DELAY = 1.0
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
MOUSE_DURATION = 0.5
