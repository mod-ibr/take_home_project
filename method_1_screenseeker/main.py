"""
main.py
-------
Step 1 of the vlm-desktop-grounding project:
  1. Show desktop (Win+D) and capture a screenshot
  2. Use two-stage ReGround (Qwen2.5-VL-72B via HuggingFace) to locate the icon
  3. Move the mouse precisely to the detected coordinates

Run:
    python main.py

Requires a .env file in the same directory:
    HF_TOKEN=hf_YOUR_TOKEN_HERE

Annotated debug screenshots are saved to ./debug/
"""

import os
import sys
import time
import logging
from pathlib import Path

import pyautogui
from PIL import Image, ImageDraw, ImageFont
from dotenv import load_dotenv

from grounder import Grounder, capture_desktop_screenshot

# ── Load .env ─────────────────────────────────────────────────────────────────
_env_path = Path(__file__).parent / ".env"
if _env_path.exists():
    load_dotenv(dotenv_path=_env_path, override=True)

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("main")

# ── Config ────────────────────────────────────────────────────────────────────
DEBUG_DIR = Path("debug")
SCREENSHOT_DIR =  Path("debug") / "screenshots"
MAX_RETRIES = 3
RETRY_DELAY = 1.0
MOUSE_DURATION = 0.5

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.1


# ── Helpers ───────────────────────────────────────────────────────────────────


def save_annotated(
    screenshot: Image.Image,
    x: int,
    y: int,
    label: str,
    filename: str,
) -> Path:
    """Draw a red crosshair + label on screenshot and save to debug dir."""
    DEBUG_DIR.mkdir(exist_ok=True)
    annotated = screenshot.copy()
    draw = ImageDraw.Draw(annotated)

    r = 20
    draw.ellipse([x - r, y - r, x + r, y + r], outline="red", width=3)
    draw.line([x - r * 2, y, x + r * 2, y], fill="red", width=2)
    draw.line([x, y - r * 2, x, y + r * 2], fill="red", width=2)

    try:
        font = ImageFont.truetype("arial.ttf", 20)
    except Exception:
        font = ImageFont.load_default()

    text = f"{label}  ({x}, {y})"
    bbox = draw.textbbox((x + r + 4, y - 12), text, font=font)
    draw.rectangle(bbox, fill="black")
    draw.text((x + r + 4, y - 12), text, fill="lime", font=font)

    out_path = DEBUG_DIR / "screenshots" / filename
    annotated.save(out_path)
    log.info("Annotated screenshot saved → %s", out_path)
    return out_path


# ── Core flow ─────────────────────────────────────────────────────────────────


def find_and_move_to_notepad(grounder: Grounder) -> bool:
    """
    Capture desktop screenshot → reground Notepad icon → move mouse.
    Retries up to MAX_RETRIES times. Returns True on success.
    """
    instruction = (
        "Notepad application shortcut icon on the Windows desktop. "
        "It looks like a small notepad with lines on it."
    )

    for attempt in range(1, MAX_RETRIES + 1):
        log.info(
            "─── Attempt %d / %d ───────────────────────────────", attempt, MAX_RETRIES
        )

        # capture_desktop_screenshot is called inside grounder.reground(),
        # but we also keep a reference here for the annotated debug image.
        log.info("Capturing desktop screenshot …")
        screenshot = capture_desktop_screenshot()

        log.info("Regrounding instruction: %r", instruction)
        result = grounder.reground(instruction=instruction, screenshot=screenshot)

        if result is None:
            log.warning("Icon not found on attempt %d.", attempt)
            if attempt < MAX_RETRIES:
                log.info("Retrying in %.1fs …", RETRY_DELAY)
                time.sleep(RETRY_DELAY)
            continue

        x, y = result

        # Validate coords are within screen bounds
        screen_w, screen_h = pyautogui.size()
        if not (0 <= x <= screen_w and 0 <= y <= screen_h):
            log.warning(
                "Coords (%d, %d) outside screen (%dx%d) — retrying.",
                x,
                y,
                screen_w,
                screen_h,
            )
            time.sleep(RETRY_DELAY)
            continue

        log.info("✓ Notepad icon detected at (%d, %d)", x, y)

        # Save annotated debug screenshot
        save_annotated(
            screenshot,
            x,
            y,
            label="Notepad",
            filename=f"detected_notepad_{int(time.time())}.png",
        )

        # Move mouse smoothly to the icon
        log.info("Moving mouse to (%d, %d) …", x, y)
        pyautogui.moveTo(x, y, duration=MOUSE_DURATION)
        log.info("✓ Mouse moved to Notepad icon successfully.")
        return True

    log.error("✗ Could not locate Notepad icon after %d attempts.", MAX_RETRIES)
    return False


# ── Entry point ───────────────────────────────────────────────────────────────


def main():
    token = os.environ.get("HF_TOKEN", "")
    if not token:
        log.error(
            "HF_TOKEN not found.\n"
            "  Create a .env file in this directory:\n"
            "      HF_TOKEN=hf_YOUR_TOKEN_HERE"
        )
        sys.exit(1)

    log.info("✓ HF_TOKEN loaded from .env")
    log.info("Initialising grounder (Qwen2.5-VL-72B via HuggingFace Inference API) …")

    grounder = Grounder(
        hf_token=token,
        max_retries=MAX_RETRIES,
        retry_delay=RETRY_DELAY,
        reground_size=400,
        screenshot_dir=str(DEBUG_DIR / "screenshots"),
    )

    success = find_and_move_to_notepad(grounder)

    if success:
        log.info("Done. Annotated screenshots saved in ./%s/", DEBUG_DIR)
        sys.exit(0)
    else:
        log.error("Detection failed. Check ./%s/ for debug screenshots.", DEBUG_DIR)
        sys.exit(1)


if __name__ == "__main__":
    main()
