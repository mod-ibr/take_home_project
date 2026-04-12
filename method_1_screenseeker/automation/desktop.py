"""
automation/desktop.py
---------------------
Desktop control helpers — screenshot capture, mouse, keyboard.
Wraps pyautogui operations used throughout the automation workflow.
"""

import time
import pyautogui


def take_screenshot(path):
    """Capture full screen and save to the given path."""
    screenshot = pyautogui.screenshot()
    screenshot.save(path)


def double_click(x, y):
    """Double-click at the given screen coordinates."""
    pyautogui.doubleClick(x, y)


def type_text(text):
    """Type text character-by-character with a short interval."""
    pyautogui.write(text, interval=0.02)


def press_hotkey(*keys):
    """Press a keyboard shortcut (e.g. 'ctrl', 's')."""
    pyautogui.hotkey(*keys)


def press_key(key):
    """Press a single key (e.g. 'enter')."""
    pyautogui.press(key)


def wait(seconds):
    """Sleep for the given number of seconds."""
    time.sleep(seconds)
