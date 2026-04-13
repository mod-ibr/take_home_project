import os
import requests

from config import (
    ICON_PATH_small,
    SCREENSHOT_PATH,
    OUTPUT_DIR,
    THRESHOLD,
    RETRY_COUNT,
    RETRY_DELAY,
)

from automation.desktop import (
    take_screenshot,
    double_click,
    type_text,
    press_hotkey,
    press_key,
    wait,
)

from vision.template_matcher import find_icon


def fetch_posts():
    try:
        # Test 1: Try with a session
        session = requests.Session()
        session.headers.update({"User-Agent": "Mozilla/5.0"})

        response = session.get(
            "https://jsonplaceholder.typicode.com/posts", timeout=10, verify=True
        )
        response.raise_for_status()
        return response.json()[:10]

    # except requests.exceptions.SSLError as e:
    #     print("SSL Error - try verify=False:", e)
    # except requests.exceptions.ConnectionError as e:
    #     print("Connection blocked or no internet access:", e)
    except Exception as e:
        print("Other error:", e)
        # return []
        # Fallback to dummy data
        return [
            {"id": i, "title": f"Test Title {i}", "body": f"Test Body {i}"}
            for i in range(1, 11)
        ]


def ensure_output_dir():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)


def launch_notepad():
    for attempt in range(RETRY_COUNT):
        print(f"[Attempt {attempt+1}] Taking screenshot...")
        press_hotkey("win", "d")  # Show desktop
        wait(1)
        take_screenshot(SCREENSHOT_PATH)
        wait(1)
        coords = find_icon(SCREENSHOT_PATH, ICON_PATH_small, THRESHOLD)

        if coords:
            print("Icon found at:", coords)
            print("Double clicking on icon...")
            double_click(*coords)
            print("Waiting for Notepad to open...")
            wait(2)
            print("Continuing...")
            return True

        print("Icon not found, retrying...")
        wait(RETRY_DELAY)

    return False


def save_file(filename):
    # full_path = os.path.join(OUTPUT_DIR, filename)

    press_hotkey("ctrl", "s")
    wait(2)
    # Write the file name
    type_text(filename)
    wait(2)

    # focus address bar
    press_hotkey("alt", "d")
    wait(1)

    # Write the output directory path
    type_text(OUTPUT_DIR)
    press_key("enter")  # to unfocus address bar
    wait(1)
    # By trial and error I found that in Win11 this is the Only way to unfocus the address bar
    #  and save the file just only for the first time, after that it works without this step,
    # Sol: Focus address bar again and press enter to unfocus then
    press_hotkey("alt", "d")
    wait(1)
    press_key("enter")
    wait(1)
    # press Enter again save the file in the output directory with the given filename
    press_key("enter")
    wait(1)


def close_notepad():
    press_hotkey("ctrl", "w")
    wait(2)
    # press_hotkey("alt", "f4")
    # wait(2)


def main():
    ensure_output_dir()

    posts = fetch_posts()

    if not posts:
        print("No posts fetched. Exiting.")
        return

    for post in posts:
        print(f"\nProcessing post {post['id']}")

        if not launch_notepad():
            print("Failed to launch Notepad. Skipping...")
            continue

        content = f"Title: {post['title']}\n\n{post['body']}"
        type_text(content)
        wait(1)

        filename = f"post_{post['id']}.txt"
        save_file(filename)

        close_notepad()


if __name__ == "__main__":
    main()
