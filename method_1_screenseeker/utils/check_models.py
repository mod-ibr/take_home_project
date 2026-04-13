"""
check_models.py
---------------
Lists all vision-capable models available on your HuggingFace account
and tests each one with a tiny request to determine if it's free or paid.

Run:
    python check_models.py

Requires .env file with:
    HF_TOKEN=hf_YOUR_TOKEN_HERE
"""

import time
import requests
import sys
from pathlib import Path

# Add the parent folder (method_1_screenseeker) to Python's search path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import HF_TOKEN

if not HF_TOKEN:
    print("ERROR: HF_TOKEN not found in .env")
    exit(1)

HF_ROUTER = "https://router.huggingface.co/v1"
HEADERS = {"Authorization": f"Bearer {HF_TOKEN}", "Content-Type": "application/json"}

# Keywords to identify vision/multimodal models
VISION_KEYWORDS = ["VL", "vision", "Vision", "visual", "Visual", "vl-", "image"]

# ── Fetch model list ──────────────────────────────────────────────────────────
print("\n📋 Fetching model list from HuggingFace router …\n")
resp = requests.get(f"{HF_ROUTER}/models", headers=HEADERS, timeout=30)
if resp.status_code != 200:
    print(f"ERROR fetching models: {resp.status_code} {resp.text}")
    exit(1)

all_models = resp.json().get("data", [])
vision_models = [m for m in all_models if any(kw in m["id"] for kw in VISION_KEYWORDS)]

print(f"Found {len(all_models)} total models, {len(vision_models)} vision models.\n")
print("=" * 70)

# ── Test each vision model ────────────────────────────────────────────────────
results = []

for m in vision_models:
    model_id = m["id"]
    owner = m.get("owned_by", "unknown")

    # Send the smallest possible request — just text, no image
    # If it's paywalled we get 402 before it even processes anything
    payload = {
        "model": model_id,
        "messages": [{"role": "user", "content": "hi"}],
        "max_tokens": 1,
    }

    try:
        r = requests.post(
            f"{HF_ROUTER}/chat/completions",
            headers=HEADERS,
            json=payload,
            timeout=20,
        )
        status = r.status_code

        if status == 200:
            tier = "✅ FREE"
        elif status == 402:
            tier = "💳 PAID"
        elif status == 429:
            tier = "⏳ RATE LIMITED (likely free, just busy)"
        elif status == 422:
            # Unprocessable — model exists but our tiny payload was invalid
            # That still means we can reach it (not paywalled)
            tier = "✅ FREE (needs image input)"
        else:
            tier = f"❓ STATUS {status}"

    except requests.exceptions.Timeout:
        tier = "⏱️  TIMEOUT"
    except Exception as e:
        tier = f"⚠️  ERROR: {e}"

    results.append((tier, model_id, owner))
    print(f"{tier:<40} {model_id}  (by {owner})")
    time.sleep(0.3)  # be polite to the API

# ── Summary ───────────────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("\n🆓 FREE models you can use right now:\n")
free = [r for r in results if r[0].startswith("✅")]
if free:
    for tier, model_id, owner in free:
        print(f"   {model_id}")
else:
    print("   None found — all vision models require a paid plan.")
    print("\n💡 Tip: Consider switching to Google Gemini Flash API")
    print("   → https://aistudio.google.com/app/apikey  (free tier, vision support)")

print()
