"""
grounder.py
-----------
Visual grounding module inspired by the ReGround method in the
ScreenSpot-Pro paper (arxiv 2504.07981).

Given a screenshot and a natural language instruction, returns (x, y)
pixel coordinates of the target UI element using Qwen2.5-VL-72B via
the HuggingFace Inference API — no local GPU required.

Two-stage approach (ReGround):
  Stage 1 — Coarse : full screenshot → rough (x, y)
  Stage 2 — Fine   : 400×400 crop around coarse point → precise (x, y)

Usage:
    from grounder import Grounder
    g = Grounder()                  # reads HF_TOKEN from .env
    x, y = g.reground("Notepad application icon on the Windows desktop")
"""

import os
import re
import time
import base64
import logging
from io import BytesIO
from pathlib import Path
from typing import Optional, Tuple

import mss
import pyautogui
import numpy as np
from PIL import Image
import requests

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("grounder")

# ── Constants ─────────────────────────────────────────────────────────────────
# HuggingFace Inference Providers — OpenAI-compatible router endpoint
HF_API_URL = "https://router.huggingface.co/v1/chat/completions"

# Best available vision model on HF free tier (confirmed working April 2026)
HF_MODEL = "Qwen/Qwen2.5-VL-72B-Instruct"

# Grounding prompt — instructs model to return normalised POINT(x, y)
GROUNDING_PROMPT = """\
You are a GUI grounding assistant. Given a screenshot and an instruction,
your ONLY job is to return the center pixel of the target UI element.

Rules:
1. Output EXACTLY one line in this format:  POINT(x, y)
   where x and y are NORMALISED coordinates in [0.0, 1.0]
   (0,0 = top-left corner, 1,1 = bottom-right corner).
2. Do NOT output any explanation, markdown, or extra text.
3. If the element is not visible, output:  NOT_FOUND

Instruction: {instruction}
"""

# ── Helpers ───────────────────────────────────────────────────────────────────

def capture_desktop_screenshot(save_path: Optional[str] = None) -> Image.Image:
    """
    Show the desktop (Win+D), wait for animation, then capture the
    primary monitor and return a PIL Image.
    """
    pyautogui.hotkey("win", "d")   # minimise all windows → show desktop
    time.sleep(1.0)                # wait for animation to finish
    with mss.mss() as sct:
        monitor = sct.monitors[1]  # monitors[0] is the virtual combined display
        raw = sct.grab(monitor)
        img = Image.frombytes("RGB", raw.size, raw.bgra, "raw", "BGRX")
    if save_path:
        img.save(save_path)
        log.info("Screenshot saved → %s", save_path)
    log.info("Screenshot captured: %dx%d", img.width, img.height)
    return img


def pil_to_base64_resized(img: Image.Image, max_side: int = 1920) -> Tuple[str, int, int]:
    """
    Resize image (keeping aspect ratio) so the longer side ≤ max_side,
    encode as base64 JPEG, and return (b64_string, width, height).
    At 1920×1080 with max_side=1920 no resizing occurs — full resolution
    is sent for maximum grounding precision.
    """
    w, h = img.size
    scale = min(max_side / max(w, h), 1.0)
    if scale < 1.0:
        img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
        log.info("Resized to %dx%d for API", img.width, img.height)
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return base64.b64encode(buf.getvalue()).decode("utf-8"), img.width, img.height


def parse_point(text: str, img_w: int, img_h: int) -> Optional[Tuple[int, int]]:
    """
    Parse normalised POINT(x, y) from model output and convert to pixels.
    Falls back to any (float, float) pattern if POINT(...) is not found.
    """
    text = text.strip()
    if "NOT_FOUND" in text.upper():
        return None

    m = re.search(r"POINT\s*\(\s*([\d.]+)\s*,\s*([\d.]+)\s*\)", text, re.IGNORECASE)
    if not m:
        m = re.search(r"\(\s*([\d.]+)\s*,\s*([\d.]+)\s*\)", text)
    if not m:
        log.warning("Could not parse model output: %r", text)
        return None

    nx = max(0.0, min(1.0, float(m.group(1))))
    ny = max(0.0, min(1.0, float(m.group(2))))
    px, py = int(nx * img_w), int(ny * img_h)
    log.info("Parsed (%.4f, %.4f) → pixel (%d, %d)", nx, ny, px, py)
    return px, py


# ── Grounder class ────────────────────────────────────────────────────────────

class Grounder:
    """
    Two-stage visual grounder using Qwen2.5-VL-72B via HuggingFace Inference.

    Parameters
    ----------
    hf_token : str | None
        HuggingFace API token. If None, reads from HF_TOKEN env var (set via .env).
    max_retries : int
        Number of API retry attempts per stage.
    retry_delay : float
        Seconds between retries.
    reground_size : int
        Side length (px) of the Stage 2 crop window. Default 400px.
    screenshot_dir : str | None
        If set, raw screenshots are saved here for debugging.
    """

    def __init__(
        self,
        hf_token: Optional[str] = None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        reground_size: int = 400,
        screenshot_dir: Optional[str] = None,
    ):
        self.token = hf_token or os.environ.get("HF_TOKEN", "")
        if not self.token:
            raise ValueError(
                "HuggingFace token required. Set HF_TOKEN in your .env file."
            )
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.reground_size = reground_size
        self.screenshot_dir = Path(screenshot_dir) if screenshot_dir else None
        if self.screenshot_dir:
            self.screenshot_dir.mkdir(parents=True, exist_ok=True)

    # ── Public API ────────────────────────────────────────────────────────────

    def reground(
        self,
        instruction: str,
        screenshot: Optional[Image.Image] = None,
    ) -> Optional[Tuple[int, int]]:
        """
        Two-stage ReGround: coarse full-screen pass → fine cropped pass.

        Parameters
        ----------
        instruction : str
            Natural language target description.
            E.g. "Notepad application shortcut icon on the Windows desktop"
        screenshot : PIL.Image | None
            Pre-captured screenshot. If None, captures desktop automatically.

        Returns
        -------
        (x, y) pixel coordinates of the target center, or None if not found.
        """
        # Capture desktop screenshot if not provided
        if screenshot is None:
            save_path = None
            if self.screenshot_dir:
                save_path = str(self.screenshot_dir / f"screenshot_{int(time.time())}.png")
            screenshot = capture_desktop_screenshot(save_path=save_path)

        orig_w, orig_h = screenshot.size
        prompt = GROUNDING_PROMPT.format(instruction=instruction)

        # ── Stage 1: Coarse — full screenshot at 1920px ───────────────────────
        log.info("Stage 1: coarse grounding on full screenshot …")
        b64, sent_w, sent_h = pil_to_base64_resized(screenshot, max_side=1920)
        raw = self._call_api(b64, prompt)
        if raw is None:
            log.error("Stage 1 API call failed.")
            return None
        log.info("Stage 1 model output: %r", raw)

        coarse = parse_point(raw, sent_w, sent_h)
        if coarse is None:
            log.warning("Stage 1 could not parse coordinates.")
            return None

        # Scale coarse coords to original resolution (no-op if no resize happened)
        cx = int(coarse[0] * orig_w / sent_w)
        cy = int(coarse[1] * orig_h / sent_h)
        log.info("Stage 1 coarse coords: (%d, %d)", cx, cy)

        # ── Stage 2: Fine — crop 400×400 around coarse point ─────────────────
        rg = self.reground_size // 2
        x1 = max(0, cx - rg)
        y1 = max(0, cy - rg)
        x2 = min(orig_w, cx + rg)
        y2 = min(orig_h, cy + rg)

        crop = screenshot.crop((x1, y1, x2, y2))
        crop_w, crop_h = crop.size
        log.info("Stage 2: re-grounding crop (%d,%d)→(%d,%d) [%dx%d] …",
                 x1, y1, x2, y2, crop_w, crop_h)

        b64_crop, _, _ = pil_to_base64_resized(crop, max_side=max(crop_w, crop_h))
        raw2 = self._call_api(b64_crop, prompt)
        if raw2 is None:
            log.warning("Stage 2 failed — using coarse coords.")
            return cx, cy
        log.info("Stage 2 model output: %r", raw2)

        fine = parse_point(raw2, crop_w, crop_h)
        if fine is None:
            log.warning("Stage 2 parse failed — using coarse coords.")
            return cx, cy

        # Map fine crop-relative coords back to full-screen space
        fx = x1 + fine[0]
        fy = y1 + fine[1]
        log.info("Stage 2 fine coords (final): (%d, %d)", fx, fy)
        return fx, fy

    # ── Internal ──────────────────────────────────────────────────────────────

    def _call_api(self, b64_image: str, prompt: str) -> Optional[str]:
        """POST to HuggingFace Inference API and return the model text response."""
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": HF_MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{b64_image}"},
                        },
                        {
                            "type": "text",
                            "text": prompt,
                        },
                    ],
                }
            ],
            "max_tokens": 64,
            "temperature": 0.0,
        }

        for attempt in range(1, self.max_retries + 1):
            try:
                log.info("API call attempt %d/%d …", attempt, self.max_retries)
                resp = requests.post(HF_API_URL, headers=headers, json=payload, timeout=60)
                resp.raise_for_status()
                return resp.json()["choices"][0]["message"]["content"]

            except requests.exceptions.HTTPError as e:
                status = e.response.status_code if e.response else "?"
                log.warning("HTTP %s on attempt %d: %s", status, attempt, e)
                if status == 429:
                    wait = self.retry_delay * 3
                    log.info("Rate limited — waiting %.1fs …", wait)
                    time.sleep(wait)
                elif status in (401, 403):
                    log.error("Authentication error — check your HF token.")
                    return None
                else:
                    time.sleep(self.retry_delay)

            except requests.exceptions.Timeout:
                log.warning("Request timed out on attempt %d.", attempt)
                time.sleep(self.retry_delay)

            except Exception as e:
                log.warning("Unexpected error on attempt %d: %s", attempt, e)
                time.sleep(self.retry_delay)

        return None
