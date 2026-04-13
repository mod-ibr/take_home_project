import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

ICON_PATH_small = os.path.join(BASE_DIR, "assets", "notepad_icon_small.png")
SCREENSHOT_PATH = os.path.join(BASE_DIR, "screenshots", "screen.png")
OUTPUT_DIR = os.path.join(os.path.expanduser("~"), "Desktop", "tjm-project")

THRESHOLD = 0.8
RETRY_COUNT = 3
RETRY_DELAY = 1
