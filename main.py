"""Entry point for Vector Rush."""
import sys
import tkinter as tk

import config as cfg
from game import VectorRushGame


def enable_sharp_text():
    """Windows: use real screen pixels so text is crisp, not blurry-stretched."""
    if sys.platform != "win32":
        return
    try:
        import ctypes
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass  # already set (e.g. when started from an IDE): nothing to do


def main():
    enable_sharp_text()
    root = tk.Tk()
    root.title("Vector Rush")

    # Default size = a share of the actual screen, centered. Resizable down to a minimum.
    screen_w, screen_h = root.winfo_screenwidth(), root.winfo_screenheight()
    min_w = min(cfg.MIN_WIDTH, screen_w - 40)
    min_h = min(cfg.MIN_HEIGHT, screen_h - 80)
    height = max(min_h, int(screen_h * 0.88))
    width = max(min_w, min(int(screen_w * 0.92), int(height * 1.7)))
    x = max(0, (screen_w - width) // 2)
    y = max(0, (screen_h - height) // 2 - 20)
    root.geometry(f"{width}x{height}+{x}+{y}")
    root.minsize(min_w, min_h)
    root.resizable(True, True)

    VectorRushGame(root)
    root.mainloop()


if __name__ == "__main__":
    main()
