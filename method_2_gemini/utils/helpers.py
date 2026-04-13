"""
utils/helpers.py
----------------
Utility functions: API data fetching and debug screenshot annotation.
"""

import logging
from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageFont

log = logging.getLogger("helpers")


def fetch_posts():
    """
    Fetch the first 10 blog posts from JSONPlaceholder API.
    Falls back to dummy data if the API is unavailable.
    """
    try:
        session = requests.Session()
        session.headers.update({"User-Agent": "Mozilla/5.0"})

        response = session.get(
            "https://jsonplaceholder.typicode.com/posts", timeout=10, verify=True
        )
        response.raise_for_status()
        return response.json()[:10]

    except Exception as e:
        log.warning("API fetch failed: %s — using fallback data.", e)
        return [
            {"id": i, "title": f"Test Title {i}", "body": f"Test Body {i}"}
            for i in range(1, 11)
        ]


def save_annotated(
    screenshot: Image.Image,
    x: int,
    y: int,
    label: str,
    filename: str,
    output_dir: Path,
) -> Path:
    """
    Draw a red crosshair + label on screenshot and save to the output dir.
    Returns the path of the saved annotated image.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

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

    out_path = output_dir / filename
    annotated.save(out_path)
    log.info("Annotated screenshot saved → %s", out_path)
    return out_path
