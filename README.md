<p align="center">
  <h1 align="center">🖥️ Vision-Based Desktop Automation</h1>
  <p align="center">
    <strong>A Comparative Study of Three Icon Grounding Approaches for GUI Automation</strong>
  </p>
  <p align="center">
    <em>Take-Home Interview Project — Desktop Automation with Dynamic Visual Element Detection</em>
  </p>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Platform-Windows%2011-0078D6?logo=windows&logoColor=white" alt="Platform">
  <img src="https://img.shields.io/badge/Automation-PyAutoGUI-brightgreen" alt="PyAutoGUI">
  <img src="https://img.shields.io/badge/Vision-OpenCV%20%7C%20Gemini%20%7C%20Qwen-orange" alt="Vision">
</p>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Problem Statement](#-problem-statement)
- [Solution Architecture](#-solution-architecture)
- [Method 1 — ScreenSeeker (Qwen2.5-VL via HuggingFace)](#-method-1--screenseeker-qwen25-vl-via-huggingface)
- [Method 2 — Gemini (Google Gemini VLM)](#-method-2--gemini-google-gemini-vlm)
- [Method 3 — Template Matching (OpenCV)](#-method-3--template-matching-opencv)
- [Comparative Analysis](#-comparative-analysis)
- [Project Structure](#-project-structure)
- [Prerequisites](#-prerequisites)
- [Installation & Setup](#-installation--setup)
- [Usage](#-usage)
- [Output](#-output)
- [Troubleshooting](#-troubleshooting)
- [References](#-references)

---

## 🎯 Overview

This project implements a **fully automated desktop workflow** that programmatically:

1. **Fetches structured data** from a REST API ([JSONPlaceholder](https://jsonplaceholder.typicode.com/posts))
2. **Visually locates** the Notepad application icon on the Windows desktop using computer vision
3. **Launches Notepad** via simulated double-click
4. **Types post content** into the editor
5. **Saves each post** as an individual `.txt` file on the desktop
6. **Repeats** the cycle for 10 blog posts

Three distinct **icon grounding strategies** are implemented and compared, ranging from a lightweight classical approach (OpenCV template matching) to state-of-the-art Vision-Language Models (VLMs).
<img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/7ac0f099-f177-4dc9-8315-0e3d0743f209" />

---

## 📝 Problem Statement

> **Task**: Build an automated script that opens Notepad on Windows, types text content fetched from an API, and saves each entry as a separate file — using **visual desktop detection** to locate and interact with the Notepad icon rather than shell commands (e.g., `subprocess`, `os.startfile`).

### Key Constraints

| Constraint | Description |
|---|---|
| **Visual Grounding** | The Notepad icon must be located on the desktop dynamically via screenshot analysis — not hardcoded coordinates or OS commands |
| **Full Automation** | No manual intervention once the script starts |
| **API Integration** | Content must be fetched from `https://jsonplaceholder.typicode.com/posts` |
| **File Persistence** | Each of the first 10 posts should be saved as `post_{id}.txt` |
| **Platform** | Windows 11 with desktop Notepad shortcut visible |

---

## 🏗️ Solution Architecture

All three methods share a **common pipeline** with the only variation being the **icon detection strategy**:

```
┌──────────────────────────────────────────────────────────────────────┐
│                        AUTOMATION PIPELINE                          │
│                                                                     │
│  ┌─────────────┐   ┌───────────────────┐   ┌────────────────────┐  │
│  │ 1. FETCH    │──▶│ 2. SHOW DESKTOP   │──▶│ 3. CAPTURE         │  │
│  │    API Data │   │    (Win+D)        │   │    SCREENSHOT      │  │
│  └─────────────┘   └───────────────────┘   └────────┬───────────┘  │
│                                                      │              │
│                              ┌────────────────────────┘              │
│                              ▼                                       │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │              4. ICON DETECTION (varies by method)            │   │
│  │                                                              │   │
│  │   Method 1: Qwen2.5-VL two-stage ReGround (HuggingFace)    │   │
│  │   Method 2: Gemini VLM bounding-box detection (Google)      │   │
│  │   Method 3: OpenCV template matching (local, no API)        │   │
│  │                                                              │   │
│  │   Output: (x, y) pixel coordinates of Notepad icon center   │   │
│  └──────────────────────────────┬───────────────────────────────┘   │
│                                 │                                    │
│                                 ▼                                    │
│  ┌─────────────┐   ┌───────────────────┐   ┌────────────────────┐  │
│  │ 5. DOUBLE   │──▶│ 6. TYPE CONTENT   │──▶│ 7. SAVE & CLOSE   │  │
│  │    CLICK    │   │    into Notepad   │   │    (Ctrl+S, etc.) │  │
│  └─────────────┘   └───────────────────┘   └────────────────────┘  │
│                                                                     │
│                     ── Repeat for 10 posts ──                       │
└──────────────────────────────────────────────────────────────────────┘
```

### Common Modules (shared across all methods)

| Module | Responsibility |
|---|---|
| `automation/desktop.py` | PyAutoGUI wrappers — mouse clicks, keyboard input, hotkeys, screenshots |
| `utils/helpers.py` | API data fetching with fallback, debug screenshot annotation |
| `config.py` | Centralised paths, API keys, retry settings, screen dimensions |
| `main.py` | End-to-end orchestration: fetch → detect → launch → type → save → close |

---

## 🔬 Method 1 — ScreenSeeker (Qwen2.5-VL via HuggingFace)

### Concept

Inspired by the **ReGround** methodology from the [ScreenSpot-Pro paper](https://arxiv.org/abs/2504.07981), this approach uses a large Vision-Language Model (**Qwen2.5-VL-72B-Instruct**) hosted on HuggingFace's Inference API to ground UI elements from natural language descriptions.

### Detection Pipeline: Two-Stage ReGround

```
Screenshot (1920×1080)
        │
        ▼
┌─────────────────────────┐
│  STAGE 1 — COARSE       │  Full screenshot → VLM → POINT(nx, ny)
│  Send full screenshot   │  normalised coordinates [0.0 – 1.0]
│  to Qwen2.5-VL-72B     │  → pixel (cx, cy)
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  STAGE 2 — FINE         │  Crop 400×400 around (cx, cy)
│  Send cropped region    │  → VLM → POINT(nx, ny)
│  to Qwen2.5-VL-72B     │  → map back to full-screen space
│  for precise grounding  │  → final (fx, fy)
└─────────────────────────┘
```

**Why two stages?**  
The coarse pass identifies the approximate region; the fine pass removes noise from the rest of the screen, giving the VLM a focused crop for higher precision.

### Grounding Prompt

```text
You are a GUI grounding assistant. Given a screenshot and an instruction,
your ONLY job is to return the center pixel of the target UI element.

Rules:
1. Output EXACTLY one line:  POINT(x, y)
   where x and y are NORMALISED coordinates in [0.0, 1.0]
2. Do NOT output any explanation, markdown, or extra text.
3. If the element is not visible, output:  NOT_FOUND

Instruction: Notepad application shortcut icon on the Windows desktop.
```

### Key Technical Details

| Aspect | Detail |
|---|---|
| **Model** | `Qwen/Qwen2.5-VL-72B-Instruct` (72B parameter VLM) |
| **API Endpoint** | `https://router.huggingface.co/v1/chat/completions` (OpenAI-compatible) |
| **Auth** | HuggingFace API token (`HF_TOKEN`) |
| **Cost** | Free tier available (rate-limited) |
| **Crop Size** | 400×400 px (configurable via `REGROUND_SIZE`) |
| **Output Format** | Normalised `POINT(x, y)` ∈ [0, 1] |
| **Key Packages** | `huggingface_hub`, `requests`, `Pillow`, `mss`, `PyAutoGUI` |
| **Debug** | Annotated screenshots with crosshair saved to `debug/screenshots/` |

### Directory Structure

```
method_1_screenseeker/
├── .env                      # HF_TOKEN=hf_YOUR_TOKEN_HERE
├── config.py                 # Paths, tokens, retry settings
├── grounder.py               # Two-stage ReGround with Qwen2.5-VL
├── main.py                   # End-to-end workflow orchestrator
├── requirements.txt          # Python dependencies
├── automation/
│   ├── __init__.py
│   └── desktop.py            # PyAutoGUI wrappers (click, type, hotkey)
├── utils/
│   ├── __init__.py
│   ├── helpers.py            # API fetch + annotated screenshot saver
│   └── check_models.py       # Utility: list free HF vision models
└── debug/
    └── screenshots/          # Annotated detection debug images
```

---

## 🤖 Method 2 — Gemini (Google Gemini VLM)

### Concept

Uses **Google Gemini 3.1 Flash Lite** to perform **bounding-box detection** on the desktop screenshot. The model returns normalised `[ymin, xmin, ymax, xmax]` coordinates (0–1000 scale), which are converted to screen-space pixel coordinates.

### Detection Pipeline: Single-Stage Bounding Box

```
Screenshot (1920×1080)
        │
        ▼
┌─────────────────────────────┐
│  Gemini VLM                 │
│  Input:  screenshot + prompt│
│  Output: [ymin, xmin,       │
│           ymax, xmax]       │  normalised 0-1000
│  → center (x, y) pixels    │
└─────────────────────────────┘
```

### Grounding Prompt

```text
Find the Notepad icon desktop icon in this image.
Return its bounding box.
Format the response strictly as a valid JSON list of 4 numbers: [ymin, xmin, ymax, xmax].
These values must be normalized coordinates between 0 and 1000.
Do not include any other text, markdown, or explanation, just the JSON list.
```

### Key Technical Details

| Aspect | Detail |
|---|---|
| **Model** | `gemini-3.1-flash-lite-preview` (Google Gemini) |
| **API** | Google GenAI SDK (`google-genai` Python package) |
| **Auth** | Google API key (`GEMINI_API_KEY`) |
| **Cost** | Free tier available (generous quota) |
| **Coord System** | Bounding box `[ymin, xmin, ymax, xmax]` normalised to 0–1000 |
| **Center Calc** | `center_x = (xmin + xmax) / 2 / 1000 × screen_width` |
| **Key Packages** | `google-genai`, `Pillow`, `mss`, `PyAutoGUI`, `requests` |
| **Debug** | Annotated screenshots with crosshair saved to `debug/screenshots/` |

### Directory Structure

```
method_2_gemini/
├── .env                      # GEMINI_API_KEY=YOUR_KEY_HERE
├── config.py                 # Paths, model ID, screen dimensions
├── gemini_agent.py           # Standalone agent (original prototype)
├── main.py                   # End-to-end workflow orchestrator
├── requirements.txt          # Python dependencies
├── automation/
│   ├── __init__.py
│   └── desktop.py            # PyAutoGUI wrappers (click, type, hotkey)
├── utils/
│   ├── __init__.py
│   ├── helpers.py            # API fetch + annotated screenshot saver
│   └── check_models.py       # Utility: list available Gemini models
├── vision/
│   ├── __init__.py
│   └── gemini_grounder.py    # GeminiGrounder class — bbox detection
└── debug/
    └── screenshots/          # Annotated detection debug images
```

---

## 📐 Method 3 — Template Matching (OpenCV)

### Concept

A **classical computer vision** approach that uses **OpenCV's `matchTemplate`** function with **normalised cross-correlation** (`TM_CCOEFF_NORMED`). A pre-captured reference image of the Notepad icon is matched against the desktop screenshot to find the best location.

### Detection Pipeline: Pixel-Level Template Correlation

```
Screenshot (1920×1080)         Template (notepad_icon_small.png)
        │                              │
        ▼                              ▼
  ┌───────────┐                 ┌───────────┐
  │ Grayscale │                 │ Grayscale │
  └─────┬─────┘                 └─────┬─────┘
        │                              │
        └──────────┬───────────────────┘
                   ▼
        ┌─────────────────────┐
        │  cv2.matchTemplate  │
        │  TM_CCOEFF_NORMED   │
        └─────────┬───────────┘
                  │
                  ▼
        ┌─────────────────────┐
        │  max_val ≥ 0.8 ?    │──No──▶ return None
        │                     │
        │  Yes ▼              │
        │  center = max_loc   │
        │  + (w//2, h//2)     │──────▶ return (x, y)
        └─────────────────────┘
```

### Key Technical Details

| Aspect | Detail |
|---|---|
| **Algorithm** | `cv2.matchTemplate` with `TM_CCOEFF_NORMED` |
| **Template** | Pre-captured `notepad_icon_small.png` stored in `assets/` |
| **Threshold** | `0.8` (configurable) — minimum correlation for a valid match |
| **API Required** | ❌ None — fully offline |
| **Auth** | ❌ None |
| **Cost** | **Free** — no cloud API calls |
| **Speed** | **< 100ms** per detection (CPU only) |
| **Key Packages** | `opencv-python`, `numpy`, `PyAutoGUI`, `requests`, `Pillow` |

### Directory Structure

```
method_3_template_matching/
├── requirements.txt          # Python dependencies
├── assets/
│   └── notepad_icon_small.png  # Reference template image
├── screenshots/
│   └── screen.png            # Captured desktop screenshot
└── src/
    ├── config.py             # Paths, threshold, retry settings
    ├── main.py               # End-to-end workflow orchestrator
    ├── automation/
    │   └── desktop.py        # PyAutoGUI wrappers (click, type, hotkey)
    ├── utils/
    │   └── helpers.py        # (Placeholder for future utilities)
    └── vision/
        └── template_matcher.py  # OpenCV template matching logic
```

---

## ⚖️ Comparative Analysis

### Method Comparison Matrix

| Criterion | Method 1: ScreenSeeker | Method 2: Gemini | Method 3: Template Matching |
|---|:---:|:---:|:---:|
| **Vision Model** | Qwen2.5-VL-72B | Gemini 3.1 Flash Lite | OpenCV `matchTemplate` |
| **Model Type** | VLM (72B params) | VLM (proprietary) | Classical CV |
| **Detection Strategy** | Two-stage ReGround | Single-stage bbox | Pixel correlation |
| **API Required** | ✅ HuggingFace | ✅ Google GenAI | ❌ None |
| **Internet Required** | ✅ Yes | ✅ Yes | ❌ No |
| **Authentication** | HF Token | Google API Key | None |
| **Cost** | Free (rate-limited) | Free (generous quota) | Free |
| **Latency per Detection** | ~3–8 seconds | ~1–3 seconds | < 100 ms |
| **Grounding Input** | Natural language description | Natural language description | Reference image (template) |
| **Coordinate System** | Normalised POINT(x,y) ∈ [0,1] | Bbox [ymin,xmin,ymax,xmax] / 1000 | Pixel coordinates directly |
| **Handles Icon Changes** | ✅ Robust (semantic understanding) | ✅ Robust (semantic understanding) | ⚠️ Fragile (pixel-exact match) |
| **Resolution Independence** | ✅ Normalised coordinates → scales  | ⚠️ Requires known screen dimensions | ❌ Template must match scale |
| **DPI / Theme Changes** | ✅ Adapts (semantic) | ✅ Adapts (semantic) | ❌ Breaks (pixel mismatch) |
| **Setup Complexity** | Medium (HF token + deps) | Low (API key + pip install) | Very Low (pip install) |
| **Dependency Weight** | Moderate (~150MB) | Light (~80MB) | Light (~50MB) |
| **Key Dependencies** | `huggingface_hub`, `requests`, `Pillow` | `google-genai`, `Pillow` | `opencv-python`, `numpy` |

### Evaluation Summary

#### 🏅 Best for Production Reliability — **Method 2 (Gemini)**

Gemini offers the best balance of **accuracy, speed, and simplicity**. The Google GenAI SDK is lightweight, the free tier is generous, and the single-stage bounding box approach is fast (~1–3s). Semantic understanding means it handles theme changes, DPI scaling, and icon variations gracefully.

#### 🧪 Best for Research / Maximum Accuracy — **Method 1 (ScreenSeeker)**

The two-stage ReGround approach achieves the **highest grounding precision** by eliminating visual noise in the second pass. Ideal for complex GUIs with densely packed icons. However, the 72B model is slower and the dependency footprint is heavy.

#### ⚡ Best for Speed / Offline Use — **Method 3 (Template Matching)**

Sub-100ms detection with **zero API dependencies** makes this ideal for controlled environments where the desktop theme, DPI, and icon appearance are fixed. Fails in dynamic environments where the icon appearance may change.

### Trade-off Visualisation

```
Accuracy    ★★★★★  ScreenSeeker (two-stage VLM)
            ★★★★☆  Gemini (single-stage VLM)
            ★★★☆☆  Template Matching (rigid pixel match)

Speed       ★☆☆☆☆  ScreenSeeker (~3-8s)
            ★★★☆☆  Gemini (~1-3s)
            ★★★★★  Template Matching (<100ms)

Robustness  ★★★★★  ScreenSeeker (semantic, resolution-invariant)
            ★★★★☆  Gemini (semantic, requires screen dims)
            ★★☆☆☆  Template Matching (fragile to visual changes)

Simplicity  ★★☆☆☆  ScreenSeeker (heavy deps, HF token)
            ★★★★☆  Gemini (lightweight, simple API)
            ★★★★★  Template Matching (no API, no auth)

Offline     ❌      ScreenSeeker
            ❌      Gemini
            ✅      Template Matching

Cost        🆓      All methods: free tier / fully free
```

---

## 📁 Project Structure

```
take_home_project_new/
│
├── README.md                          # This file
├── .gitignore                         # Excludes venvs, __pycache__, .env
│
├── method_1_screenseeker/             # VLM: Qwen2.5-VL via HuggingFace
│   ├── .env                           # HF_TOKEN
│   ├── config.py                      # Centralised settings
│   ├── grounder.py                    # Two-stage ReGround logic
│   ├── main.py                        # Orchestrator
│   ├── requirements.txt
│   ├── automation/
│   │   ├── __init__.py
│   │   └── desktop.py                 # Mouse/keyboard wrappers
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── helpers.py                 # API fetch + annotations
│   │   └── check_models.py            # HF model discovery tool
│   └── debug/screenshots/             # Annotated detection images
│
├── method_2_gemini/                   # VLM: Google Gemini
│   ├── .env                           # GEMINI_API_KEY
│   ├── config.py                      # Centralised settings
│   ├── gemini_agent.py                # Original standalone prototype
│   ├── main.py                        # Orchestrator
│   ├── requirements.txt
│   ├── automation/
│   │   ├── __init__.py
│   │   └── desktop.py                 # Mouse/keyboard wrappers
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── helpers.py                 # API fetch + annotations
│   │   └── check_models.py            # Gemini model discovery tool
│   ├── vision/
│   │   ├── __init__.py
│   │   └── gemini_grounder.py         # GeminiGrounder class
│   └── debug/screenshots/             # Annotated detection images
│
└── method_3_template_matching/        # Classical CV: OpenCV
    ├── requirements.txt
    ├── assets/
    │   └── notepad_icon_small.png     # Reference template
    ├── screenshots/
    │   └── screen.png                 # Runtime desktop capture
    └── src/
        ├── config.py                  # Paths, threshold
        ├── main.py                    # Orchestrator
        ├── automation/
        │   └── desktop.py            # Mouse/keyboard wrappers
        ├── utils/
        │   └── helpers.py            # (Placeholder)
        └── vision/
            └── template_matcher.py   # cv2.matchTemplate logic
```

---

## ✅ Prerequisites

| Requirement | Version | Purpose |
|---|---|---|
| **Python** | ≥ 3.10 | Core runtime |
| **Windows** | 10/11 | Desktop automation target |
| **Notepad shortcut** | — | Must be visible on the desktop |
| **Screen Resolution** | 1920×1080 recommended | Methods 2 & 3 assume this resolution |
| **Internet** | Required for Methods 1 & 2 | API calls to HuggingFace / Google |

### API Keys (Methods 1 & 2 Only)

| Method | Service | Key Variable | How to Obtain |
|---|---|---|---|
| Method 1 | HuggingFace | `HF_TOKEN` | [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens) |
| Method 2 | Google Gemini | `GEMINI_API_KEY` | [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey) |
| Method 3 | — | — | No API key needed |

---

## 🚀 Installation & Setup

### Method 1 — ScreenSeeker

```powershell
cd method_1_screenseeker

# Create and activate virtual environment
python -m venv venv_screenseeker
.\venv_screenseeker\Scripts\Activate

# Install dependencies
pip install -r requirements.txt

# Configure API token
# Create a .env file with:
#   HF_TOKEN=hf_YOUR_TOKEN_HERE
```

### Method 2 — Gemini

```powershell
cd method_2_gemini

# Create and activate virtual environment
python -m venv venv_gemini
.\venv_gemini\Scripts\Activate

# Install dependencies
pip install -r requirements.txt

# Configure API key
# Create a .env file with:
#   GEMINI_API_KEY=YOUR_API_KEY_HERE
```

### Method 3 — Template Matching

```powershell
cd method_3_template_matching

# Create and activate virtual environment
python -m venv venv_template_matching
.\venv_template_matching\Scripts\Activate

# Install dependencies
pip install -r requirements.txt

# No API key required
```

---

## ▶️ Usage

> **⚠️ Important**: Before running any method, ensure:
> 1. The **Notepad shortcut** is visible on the Windows desktop
> 2. No other windows are covering the desktop icons
> 3. The virtual environment is activated
> 4. API keys are configured (Methods 1 & 2)

### Running Method 1

```powershell
cd method_1_screenseeker
.\venv_screenseeker\Scripts\Activate
python main.py
```

**Expected output:**
```
12:00:00 [INFO] ✓ HF_TOKEN loaded from .env
12:00:00 [INFO] Initialising grounder (Qwen2.5-VL-72B via HuggingFace Inference API) …
12:00:01 [INFO] Fetched 10 posts. Starting automation workflow …
12:00:01 [INFO] ═══ Processing post 1 ═══════════════════════════════
12:00:01 [INFO] Capturing desktop screenshot …
12:00:02 [INFO] Stage 1: coarse grounding on full screenshot …
12:00:06 [INFO] Stage 2: re-grounding crop …
12:00:08 [INFO] ✓ Notepad icon detected at (40, 136)
12:00:08 [INFO] Double-clicking on icon at (40, 136) …
```

### Running Method 2

```powershell
cd method_2_gemini
.\venv_gemini\Scripts\Activate
python main.py
```

**Expected output:**
```
12:00:00 [INFO] ✓ GEMINI_API_KEY loaded from .env
12:00:00 [INFO] Initialising Gemini grounder (model: gemini-3.1-flash-lite-preview) …
12:00:01 [INFO] Fetched 10 posts. Starting automation workflow …
12:00:01 [INFO] Asking Gemini to find 'Notepad icon' …
12:00:03 [INFO] Gemini found it! Normalized box: [110, 12, 165, 55]
12:00:03 [INFO] ✓ Notepad icon detected at (64, 148)
```

### Running Method 3

```powershell
cd method_3_template_matching\src
..\venv_template_matching\Scripts\Activate
python main.py
```

**Expected output:**
```
Processing post 1
[Attempt 1] Taking screenshot...
Icon found at: (40, 136)
Double clicking on icon...
Waiting for Notepad to open...
Continuing...
```

---

## 📂 Output

All methods save files to:

```
%USERPROFILE%\Desktop\tjm-project\
├── post_1.txt
├── post_2.txt
├── post_3.txt
├── ...
└── post_10.txt
```

Each file contains:

```
Title: sunt aut facere repellat provident occaecati excepturi optio reprehenderit

quia et suscipit
suscipit recusandae consequuntur expedita et cum
reprehenderit molestiae ut ut quas totam
nostrum rerum est autem sunt rem eveniet architecto
```

### Debug Output (Methods 1 & 2)

Annotated screenshots showing the detected icon location (red crosshair) are saved to:
```
method_{1,2}/debug/screenshots/detected_notepad_{timestamp}.png
```

---

## 🔧 Troubleshooting

| Issue | Cause | Solution |
|---|---|---|
| `ConnectionResetError` during API fetch | Network/firewall issue | Script falls back to dummy data automatically |
| `Icon not found` after all retries | Notepad shortcut not on desktop | Ensure shortcut is visible; minimize windows |
| `HF_TOKEN not found` | Missing `.env` file | Create `.env` with `HF_TOKEN=hf_...` |
| `GEMINI_API_KEY not found` | Missing `.env` file | Create `.env` with `GEMINI_API_KEY=...` |
| `HTTP 429` (rate limit) | Too many API requests | Wait and retry; the script handles this automatically |
| `HTTP 402` (payment required) | Model on paid tier | Use `check_models.py` to find free alternatives |
| Template matching fails | DPI/theme mismatch | Re-capture `notepad_icon_small.png` at current scale |
| Wrong save location | Address bar not focused | Ensure Notepad's Save dialog is standard (Win11) |

---

## 📚 References

1. **ScreenSpot-Pro** — Wu et al. (2025). *ScreenSpot-Pro: GUI Grounding for Web, Desktop, and Mobile*. [arXiv:2504.07981](https://arxiv.org/abs/2504.07981)
2. **Qwen2.5-VL** — Alibaba Qwen Team. *Qwen2.5-VL: Vision-Language Model*. [HuggingFace](https://huggingface.co/Qwen/Qwen2.5-VL-72B-Instruct)
3. **Google Gemini** — Google DeepMind. *Gemini API Documentation*. [ai.google.dev](https://ai.google.dev/docs)
4. **OpenCV Template Matching** — Bradski, G. (2000). *The OpenCV Library*. [docs.opencv.org](https://docs.opencv.org/4.x/d4/dc6/tutorial_py_template_matching.html)
5. **JSONPlaceholder** — Typicode. *Free fake API for testing*. [jsonplaceholder.typicode.com](https://jsonplaceholder.typicode.com)
6. **PyAutoGUI** — Sweigart, A. *PyAutoGUI: Cross-platform GUI automation*. [pyautogui.readthedocs.io](https://pyautogui.readthedocs.io)

---

<p align="center">
  <strong>Developed as a technical demonstration for a Desktop Automation Interview Task</strong><br>
  <em>Three approaches, one goal: robust, vision-driven GUI automation</em>
</p>
