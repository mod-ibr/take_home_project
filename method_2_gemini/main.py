"""
main.py
-------
Vision-Based Desktop Automation with Dynamic Icon Grounding
Method 2: Gemini — Google Gemini VLM bounding box detection

Full workflow:
  1. Show desktop and capture screenshot
  2. Use Gemini VLM to locate the Notepad icon (bounding box → center coords)
  3. Double-click to launch Notepad
  4. Fetch blog posts from JSONPlaceholder API
  5. For each of 10 posts: type content → save as post_{id}.txt → close
  6. Repeat with fresh screenshot + grounding for each iteration

Run:
    python main.py

Requires .env in this directory:
    GEMINI_API_KEY=YOUR_API_KEY_HERE
"""

import os
import sys
import logging

import pyautogui

from config import (
    GEMINI_API_KEY,
    GEMINI_MODEL_ID,
    OUTPUT_DIR,
    RETRY_COUNT,
    RETRY_DELAY,
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
)

from automation.desktop import (
    take_screenshot,
    double_click,
    type_text,
    press_hotkey,
    press_key,
    wait,
)

from vision.gemini_grounder import GeminiGrounder
from utils.helpers import fetch_posts

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


def launch_notepad(grounder: GeminiGrounder) -> bool:
    """
    Capture desktop screenshot → ask Gemini to find Notepad icon → double-click.
    Retries up to RETRY_COUNT times. Returns True on success.
    """
    target = "Notepad icon"

    for attempt in range(1, RETRY_COUNT + 1):
        log.info(
            "─── Attempt %d / %d ───────────────────────────────", attempt, RETRY_COUNT
        )

        # Show desktop and capture screenshot
        log.info("Capturing desktop screenshot …")
        desktop_img = take_screenshot()

        # Use Gemini VLM to find the Notepad icon
        coords = grounder.find_icon(desktop_img, target)

        if coords:
            x, y = coords
            log.info("✓ Notepad icon detected at (%d, %d)", x, y)

            # Move mouse and double-click to launch
            log.info("Double-clicking on icon at (%d, %d) …", x, y)
            pyautogui.moveTo(x, y, duration=0.5)
            double_click(x, y)
            log.info("Waiting for Notepad to open …")
            wait(2)
            return True

        log.warning("Icon not found on attempt %d.", attempt)
        if attempt < RETRY_COUNT:
            log.info("Retrying in %.1fs …", RETRY_DELAY)
            wait(RETRY_DELAY)

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
    # Validate Gemini API key
    if not GEMINI_API_KEY:
        log.error(
            "GEMINI_API_KEY not found.\n"
            "  Create a .env file in this directory:\n"
            "      GEMINI_API_KEY=YOUR_API_KEY_HERE"
        )
        sys.exit(1)

    log.info("✓ GEMINI_API_KEY loaded from .env")

    # Create output directory
    ensure_output_dir()

    # Initialise the Gemini grounder
    log.info("Initialising Gemini grounder (model: %s) …", GEMINI_MODEL_ID)
    grounder = GeminiGrounder(
        api_key=GEMINI_API_KEY,
        model_id=GEMINI_MODEL_ID,
        screen_width=SCREEN_WIDTH,
        screen_height=SCREEN_HEIGHT,
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

        # Launch Notepad via Gemini grounding
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
        log.info("Notepad closed. Moving to next post …")

    log.info("\n✓ All posts processed. Files saved to: %s", OUTPUT_DIR)


if __name__ == "__main__":
    main()
