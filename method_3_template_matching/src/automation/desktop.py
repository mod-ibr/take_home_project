import pyautogui
import time

def take_screenshot(path):
    screenshot = pyautogui.screenshot()
    screenshot.save(path)

def double_click(x, y):
    pyautogui.doubleClick(x, y)

def type_text(text):
    pyautogui.write(text, interval=0.02)

def press_hotkey(*keys):
    pyautogui.hotkey(*keys)

def press_key(key):
    pyautogui.press(key)

def wait(seconds):
    time.sleep(seconds)