"""
automation/desktop.py
---------------------
Desktop control helpers — screenshot capture, mouse, keyboard.
Wraps pyautogui operations used throughout the automation workflow.
"""

import time
import pyautogui
import mss
from PIL import Image


def take_screenshot():
    """
    Show the Desktop then capture the full primary monitor.
    Returns a PIL Image.
    """
    pyautogui.hotkey("win", "d")
    time.sleep(1)
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        sct_img = sct.grab(monitor)
        img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
        return img


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
