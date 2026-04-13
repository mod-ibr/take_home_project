"""
main.py
-------
Vision-Based Desktop Automation with Dynamic Icon Grounding
Method 1: ScreenSeeker — Two-stage ReGround (Qwen2.5-VL-72B via HuggingFace)

Full workflow:
  1. Show desktop and capture screenshot
  2. Use VLM-based grounding to locate the Notepad icon
  3. Double-click to launch Notepad
  4. Fetch blog posts from JSONPlaceholder API
  5. For each of 10 posts: type content → save as post_{id}.txt → close
  6. Repeat with fresh screenshot + grounding for each iteration

Run:
    python main.py

Requires .env in this directory:
    HF_TOKEN=hf_YOUR_TOKEN_HERE
"""

import os
import sys
import time
import logging

import pyautogui

from config import (
    HF_TOKEN,
    OUTPUT_DIR,
    RETRY_COUNT,
    RETRY_DELAY,
    REGROUND_SIZE,
    MOUSE_DURATION,
    SCREENSHOT_DIR,
    NOTEPAD_INSTRUCTION,
)

from automation.desktop import (
    double_click,
    type_text,
    press_hotkey,
    press_key,
    wait,
    navigate_to_center,
)

from utils.helpers import fetch_posts, save_annotated
from grounder import Grounder, capture_desktop_screenshot

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("main")

# ── PyAutoGUI safety ─────────────────────────────────────────────────────────
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.1


# ── Core Functions ───────────────────────────────────────────────────────────


def ensure_output_dir():
    """Create the output directory if it doesn't exist."""
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        log.info("Created output directory: %s", OUTPUT_DIR)


def launch_notepad(grounder: Grounder) -> bool:
    """
    Capture desktop screenshot → reground Notepad icon → double-click to launch.
    Retries up to RETRY_COUNT times. Returns True on success.
    """
    for attempt in range(1, RETRY_COUNT + 1):
        log.info(
            "─── Attempt %d / %d ───────────────────────────────", attempt, RETRY_COUNT
        )

        # Show desktop and capture screenshot
        log.info("Capturing desktop screenshot …")
        screenshot = capture_desktop_screenshot()

        # Use VLM-based grounding to find the Notepad icon
        log.info("Regrounding instruction: %r", NOTEPAD_INSTRUCTION)
        result = grounder.reground(
            instruction=NOTEPAD_INSTRUCTION, screenshot=screenshot
        )

        if result is None:
            log.warning("Icon not found on attempt %d.", attempt)
            if attempt < RETRY_COUNT:
                log.info("Retrying in %.1fs …", RETRY_DELAY)
                wait(RETRY_DELAY)
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
            wait(RETRY_DELAY)
            continue

        log.info("✓ Notepad icon detected at (%d, %d)", x, y)

        # Save annotated debug screenshot
        save_annotated(
            screenshot,
            x,
            y,
            label="Notepad",
            filename=f"detected_notepad_{int(time.time())}.png",
            output_dir=SCREENSHOT_DIR,
        )

        # Double-click the icon to launch Notepad
        log.info("Double-clicking on icon at (%d, %d) …", x, y)
        pyautogui.moveTo(x, y, duration=MOUSE_DURATION)
        double_click(x, y)
        log.info("Waiting for Notepad to open …")
        wait(2)
        return True

    log.error("✗ Could not locate Notepad icon after %d attempts.", RETRY_COUNT)
    return False


def save_file(filename):
    """
    Save the current Notepad file:
    Ctrl+S → type filename → navigate to output dir → save.
    """
    press_hotkey("ctrl", "s")
    wait(2)

    # Write the file name
    type_text(filename)
    wait(2)

    # Focus address bar
    press_hotkey("alt", "d")
    wait(1)

    # Write the output directory path
    type_text(OUTPUT_DIR)
    press_key("enter")  # to unfocus address bar
    wait(1)

    # By trial and error: in Win11 this is the only way to unfocus the address bar
    # and save the file just only for the first time, after that it works without this step.
    # Sol: Focus address bar again and press enter to unfocus then
    press_hotkey("alt", "d")
    wait(1)
    press_key("enter")
    wait(1)

    # Press Enter again to save the file in the output directory with the given filename
    press_key("enter")
    wait(1)


def close_notepad():
    """Close the current Notepad window."""
    press_hotkey("ctrl", "w")
    wait(2)


# ── Entry Point ──────────────────────────────────────────────────────────────


def main():
    # Validate HF token
    if not HF_TOKEN:
        log.error(
            "HF_TOKEN not found.\n"
            "  Create a .env file in this directory:\n"
            "      HF_TOKEN=hf_YOUR_TOKEN_HERE"
        )
        sys.exit(1)

    log.info("✓ HF_TOKEN loaded from .env")

    # Create output directory
    ensure_output_dir()

    # Initialise the VLM grounder
    log.info("Initialising grounder (Qwen2.5-VL-72B via HuggingFace Inference API) …")
    grounder = Grounder(
        hf_token=HF_TOKEN,
        max_retries=RETRY_COUNT,
        retry_delay=RETRY_DELAY,
        reground_size=REGROUND_SIZE,
        screenshot_dir=str(SCREENSHOT_DIR),
    )

    # Fetch blog posts from JSONPlaceholder API
    posts = fetch_posts()
    if not posts:
        log.error("No posts fetched. Exiting.")
        return

    log.info("Fetched %d posts. Starting automation workflow …", len(posts))

    # Process each post
    for post in posts:
        log.info("\n═══ Processing post %d ═══════════════════════════════", post["id"])

        # Launch Notepad via VLM grounding
        if not launch_notepad(grounder):
            log.warning("Failed to launch Notepad. Skipping post %d …", post["id"])
            continue

        # Type the post content
        content = f"Title: {post['title']}\n\n{post['body']}"
        type_text(content)
        wait(1)

        # Save the file
        filename = f"post_{post['id']}.txt"
        save_file(filename)
        log.info("Saved %s", filename)

        # Close Notepad
        close_notepad()

        # Navigate the Mose to the center of the screen
        navigate_to_center()

        log.info("Notepad closed. Moving to next post …")

    log.info("\n✓ All posts processed. Files saved to: %s", OUTPUT_DIR)
    log.info("Debug screenshots saved in: %s", SCREENSHOT_DIR)


if __name__ == "__main__":
    main()
