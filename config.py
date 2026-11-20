"""Shared constants and the saved text-size setting.

ALL TEXT SIZES LIVE IN THE `FONT` TABLE BELOW. Change a number there and it
takes effect everywhere. Sizes are "design pixels" for a 1280x800 window: the
real size is scaled automatically to the actual window (see ui.py).
"""
import json
from pathlib import Path

# --- Colors ---
BACKGROUND = "#07111f"
HUD_BG = "#0c1c30"
HUD_LINE = "#2a4a70"
CYAN = "#35c9ff"
WHITE = "#ffffff"
TEXT = "#e6edf5"
MUTED = "#a9bbcf"
GOLD = "#ffd166"
RED = "#ff5555"
GREEN = "#5ee38b"

# --- Window ---
MIN_WIDTH, MIN_HEIGHT = 960, 640   # smallest allowed window
DESIGN_W, DESIGN_H = 1280, 800     # window size that FONT sizes are designed for

# --- Text ---
FONT_FAMILIES = ("DejaVu Sans", "Liberation Sans", "Arial", "Segoe UI", "Helvetica")
MIN_FONT_PX = 16                   # no text is ever drawn smaller than this

FONT = {
    # Start screen
    "title": 104,       # VECTOR RUSH / GAME OVER
    "subtitle": 44,     # COLLECT BLACK - AVOID RED
    "body": 40,         # instructions
    "prompt": 46,       # PRESS SPACE ...
    "best": 44,         # BEST SCORE
    "scores": 38,       # recent scores
    "hint": 28,         # text-size / fullscreen hint
    # Game over screen
    "final": 64,        # FINAL SCORE
    "record": 46,       # NEW RECORD!
    "heading": 32,      # RECENT SCORES heading
    # In-game bar
    "hud_main": 34,     # score, lives, level
    "hud_side": 30,     # black / red counters
}

# --- User text-size setting (keys + / - in the game) ---
TEXT_SCALE_MIN, TEXT_SCALE_MAX, TEXT_SCALE_STEP = 0.7, 2.0, 1.1
SETTINGS_FILE = Path(__file__).resolve().parent / "settings.json"


def clamp_text_scale(value):
    return max(TEXT_SCALE_MIN, min(TEXT_SCALE_MAX, value))


def load_text_scale():
    """Saved text-size multiplier, or 1.0 if missing or invalid."""
    try:
        data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        return clamp_text_scale(float(data["text_scale"]))
    except (OSError, ValueError, KeyError, TypeError):
        return 1.0


def save_text_scale(value):
    try:
        SETTINGS_FILE.write_text(json.dumps({"text_scale": round(value, 2)}),
                                 encoding="utf-8")
    except OSError:
        pass
