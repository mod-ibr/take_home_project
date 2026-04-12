import os
import re
import json
import time
import pyautogui
import mss
from PIL import Image
from google import genai
from dotenv import load_dotenv

# ==========================================
# 1. Setup Gemini API
# ==========================================
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("Please set GEMINI_API_KEY in your .env file")

# استخدام المكتبة الجديدة
client = genai.Client(api_key=api_key)

# هنستخدم موديل 2.0 فلاش عشان سريع ودقيق جداً في الصور
# model_id = 'gemini-3.1-flash-image-preview'
# model_id = 'gemini-3-flash-preview'
model_id = "gemini-3.1-flash-lite-preview"

# ==========================================
# 2. Core Functions
# ==========================================


def take_screenshot():
    """Show the Desktop then Captures the full screen and returns a PIL Image."""
    pyautogui.hotkey("win", "d")
    time.sleep(1)  # استنى ثانية قبل التصوير
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        sct_img = sct.grab(monitor)
        img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
        return img


def find_icon_with_gemini(image, target_name):
    """Sends the image to Gemini and asks for bounding box coordinates."""

    print(f"Asking Gemini 2.0 to find '{target_name}'...")

    prompt = f"""
    Find the {target_name} desktop icon in this image.
    Return its bounding box. 
    Format the response strictly as a valid JSON list of 4 numbers: [ymin, xmin, ymax, xmax].
    These values must be normalized coordinates between 0 and 1000.
    Do not include any other text, markdown, or explanation, just the JSON list.
    """

    try:
        # الطريقة الجديدة للتعامل مع الـ API
        response = client.models.generate_content(
            model=model_id, contents=[image, prompt]
        )
        result_text = response.text.strip()

        # تنظيف الإجابة
        clean_json = re.sub(r"```[a-zA-Z]*", "", result_text).strip()
        clean_json = clean_json.strip("`")

        box = json.loads(clean_json)

        if len(box) == 4:
            print(f"Gemini found it! Normalized box: {box}")
            return box
        else:
            print("Invalid box format received.")
            return None

    except Exception as e:
        print(f"Error communicating with Gemini: {e}")
        return None


def click_normalized_box(box, screen_width=1920, screen_height=1080):
    """Converts 0-1000 coordinates to actual screen pixels and clicks."""
    ymin, xmin, ymax, xmax = box

    # تحويل الإحداثيات للمقاس الحقيقي للشاشة
    real_ymin = (ymin / 1000) * screen_height
    real_xmin = (xmin / 1000) * screen_width
    real_ymax = (ymax / 1000) * screen_height
    real_xmax = (xmax / 1000) * screen_width

    # حساب نقطة المنتصف
    center_x = (real_xmin + real_xmax) / 2
    center_y = (real_ymin + real_ymax) / 2

    print(f"Moving mouse to: X={center_x:.0f}, Y={center_y:.0f}")

    # تحريك الماوس وعمل دبل كليك
    pyautogui.moveTo(center_x, center_y, duration=0.5)
    pyautogui.doubleClick()


# ==========================================
# 3. Main Execution
# ==========================================
if __name__ == "__main__":
    target = "Notepad icon"
    print("Capturing desktop...")
    desktop_img = take_screenshot()

    box = find_icon_with_gemini(desktop_img, target)

    if box:
        click_normalized_box(box)
    else:
        print("Failed to find the icon.")
