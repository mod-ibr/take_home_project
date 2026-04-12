"""
utils/helpers.py
----------------
Utility functions: API data fetching.
"""

import logging
import requests

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
