"""
vision/gemini_grounder.py
-------------------------
Visual grounding module using Google Gemini API.
Sends a screenshot to Gemini and returns the center (x, y) coordinates
of the target icon/element on screen.

Extracted from the original gemini_agent.py — detection logic preserved exactly.
"""

import re
import json
import logging
from typing import Optional, Tuple

from PIL import Image
from google import genai

log = logging.getLogger("gemini_grounder")


class GeminiGrounder:
    """
    Visual grounder using Gemini VLM.

    Parameters
    ----------
    api_key : str
        Google Gemini API key.
    model_id : str
        Gemini model identifier.
    screen_width : int
        Screen width in pixels (default 1920).
    screen_height : int
        Screen height in pixels (default 1080).
    """

    def __init__(
        self,
        api_key: str,
        model_id: str = "gemini-3.1-flash-lite-preview",
        screen_width: int = 1920,
        screen_height: int = 1080,
    ):
        if not api_key:
            raise ValueError("Please set GEMINI_API_KEY in your .env file")

        self.client = genai.Client(api_key=api_key)
        self.model_id = model_id
        self.screen_width = screen_width
        self.screen_height = screen_height

    def find_icon(
        self,
        image: Image.Image,
        target_name: str,
    ) -> Optional[Tuple[int, int]]:
        """
        Ask Gemini to find the target icon in the screenshot.

        Parameters
        ----------
        image : PIL.Image
            Screenshot of the desktop.
        target_name : str
            Name/description of the icon to find (e.g. "Notepad icon").

        Returns
        -------
        (x, y) center coordinates in screen pixels, or None if not found.
        """
        log.info("Asking Gemini to find '%s' …", target_name)

        prompt = f"""
    Find the {target_name} desktop icon in this image.
    Return its bounding box. 
    Format the response strictly as a valid JSON list of 4 numbers: [ymin, xmin, ymax, xmax].
    These values must be normalized coordinates between 0 and 1000.
    Do not include any other text, markdown, or explanation, just the JSON list.
    """

        try:
            response = self.client.models.generate_content(
                model=self.model_id, contents=[image, prompt]
            )
            result_text = response.text.strip()

            # Clean the response (remove markdown code fences if present)
            clean_json = re.sub(r"```[a-zA-Z]*", "", result_text).strip()
            clean_json = clean_json.strip("`")

            box = json.loads(clean_json)

            if len(box) == 4:
                log.info("Gemini found it! Normalized box: %s", box)
                return self._box_to_center(box)
            else:
                log.warning("Invalid box format received: %s", box)
                return None

        except Exception as e:
            log.error("Error communicating with Gemini: %s", e)
            return None

    def _box_to_center(self, box) -> Tuple[int, int]:
        """
        Convert 0-1000 normalised bounding box to screen center pixel coordinates.
        """
        ymin, xmin, ymax, xmax = box

        real_ymin = (ymin / 1000) * self.screen_height
        real_xmin = (xmin / 1000) * self.screen_width
        real_ymax = (ymax / 1000) * self.screen_height
        real_xmax = (xmax / 1000) * self.screen_width

        center_x = int((real_xmin + real_xmax) / 2)
        center_y = int((real_ymin + real_ymax) / 2)

        log.info("Center coordinates: X=%d, Y=%d", center_x, center_y)
        return center_x, center_y
