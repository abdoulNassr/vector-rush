"""Start screen, game-over screen and HUD, drawn on the canvas.

How text stays readable (the rules this file enforces):
  1. Every size is defined once in config.FONT, for a 1280x800 window.
  2. The real size is computed from the CURRENT window size and the user's
     text-size setting (keys + / -), so text follows the window.
  3. Screens are laid out from MEASURED text heights and widths. If the text
     does not fit, everything is shrunk together, so nothing overlaps or
     leaves the window.
"""
from collections import namedtuple
import tkinter.font as tkfont

import config as cfg

SAFE = 0.94  # fraction of the window that a screen's text may use

# One line of text: size is a key of config.FONT; gap = space below (design px).
Line = namedtuple("Line", "text size bold color gap")


class GameUI:
    def __init__(self, canvas, text_scale=1.0):
        self.canvas = canvas
        self.text_scale = text_scale
        self.width = 1
        self.height = 1
        self.hud = None
        self._fonts = {}
        names = set(tkfont.families(canvas))
        self.family = next((n for n in cfg.FONT_FAMILIES if n in names), "TkDefaultFont")

    # ---------- Sizing ----------
    def resize(self, width, height):
        self.width, self.height = width, height

    @property
    def unit(self):
        """Global text multiplier: follows the window size and the user setting."""
        return min(self.width / cfg.DESIGN_W, self.height / cfg.DESIGN_H) * self.text_scale

    def font(self, key, bold, unit):
        """Cached pixel-sized font for a config.FONT key."""
        px = max(cfg.MIN_FONT_PX, round(cfg.FONT[key] * unit))
        if (px, bold) not in self._fonts:
            self._fonts[(px, bold)] = tkfont.Font(
                root=self.canvas, family=self.family, size=-px,
                weight="bold" if bold else "normal")
        return self._fonts[(px, bold)]

    def _measure(self, lines, unit):
        """Return (total height, widest line) of a block of lines."""
        height = widest = 0
        for i, ln in enumerate(lines):
            f = self.font(ln.size, ln.bold, unit)
            height += f.metrics("linespace")
            if i < len(lines) - 1:
                height += ln.gap * unit
            widest = max(widest, f.measure(ln.text))
        return height, widest

    def _draw_lines(self, lines):
        """Clear the canvas and draw a vertically centered block of lines."""
        c = self.canvas
        c.delete("all")
        self.hud = None
        unit = self.unit
        for _ in range(40):  # shrink until the block fits in the window
            height, widest = self._measure(lines, unit)
            if height <= self.height * SAFE and widest <= self.width * SAFE:
                break
            unit *= 0.95
        height, _ = self._measure(lines, unit)
        y = (self.height - height) / 2
        for ln in lines:
            f = self.font(ln.size, ln.bold, unit)
            c.create_text(self.width / 2, y, text=ln.text, anchor="n",
                          fill=ln.color, font=f)
            y += f.metrics("linespace") + ln.gap * unit

    # ---------- Screens ----------
    def _screen_text(self, x, y, text, size, color, anchor="nw", bold=True):
        unit = min(self.width / 1426, self.height / 842)
        px = max(15, round(size * unit * self.text_scale))
        font = tkfont.Font(root=self.canvas, family=self.family, size=-px,
                           weight="bold" if bold else "normal")
        return self.canvas.create_text(x, y, text=text, anchor=anchor,
                                       fill=color, font=font)

    def _panel(self, x1, y1, x2, y2):
        self.canvas.create_rectangle(x1, y1, x2, y2, fill=cfg.HUD_BG,
                                     outline=cfg.HUD_LINE, width=1)

    def _draw_menu_frame(self, over=False, score=0, board=None, new_record=False):
        c = self.canvas
        c.delete("all")
        self.hud = None
        unit = min(self.width / 1426, self.height / 842)
        # Leave a little breathing room at the smallest supported window size.
        unit = max(0.66, unit)
        cx = self.width / 2
        title = "GAME OVER" if over else "VECTOR RUSH"
        subtitle = "YOUR RUN IS COMPLETE" if over else "COLLECT BLACK — AVOID RED"
        self._screen_text(cx, 12 * unit, title, 108 if not over else 96,
                          cfg.CYAN if not over else cfg.RED, "n", True)
        self._screen_text(cx, 135 * unit, subtitle, 46, cfg.GOLD, "n", True)

        # Action buttons are visual prompts; keyboard behavior remains unchanged.
        button_y = 221 * unit
        button_h = 74 * unit
        start_x = cx - 300 * unit
        self._panel(start_x, button_y, start_x + 388 * unit, button_y + button_h)
        c.create_rectangle(start_x, button_y, start_x + 388 * unit,
                           button_y + button_h, fill=cfg.CYAN, outline="")
        self._screen_text(start_x + 194 * unit, button_y + 8 * unit,
                          "PLAY AGAIN" if over else "START GAME", 48,
                          cfg.BACKGROUND, "n", True)
        exit_x = start_x + 405 * unit
        c.create_rectangle(exit_x, button_y, exit_x + 160 * unit,
                           button_y + button_h, fill="#203957", outline="")
        self._screen_text(exit_x + 80 * unit, button_y + 8 * unit,
                          "EXIT", 48, cfg.WHITE, "n", True)

        left = 65 * unit
        top = 306 * unit
        panel_w = 615 * unit
        panel_h = 452 * unit
        right = 697 * unit
        right_w = 628 * unit
        self._panel(left, top, left + panel_w, top + panel_h)
        self._panel(right, top, right + right_w, top + panel_h)

        if not over:
            self._screen_text(left + 20 * unit, top + 15 * unit,
                              "CONTROLS", 54, cfg.CYAN)
            rows = [
                ("UP", "Accelerate"),
                ("DOWN", "Decelerate"),
                ("LEFT", "Rotate left"),
                ("RIGHT", "Rotate right"),
            ]
            y = top + 90 * unit
            for key, action in rows:
                self._screen_text(left + 20 * unit, y, key, 44, cfg.CYAN)
                self._screen_text(left + 190 * unit, y, action, 43, cfg.WHITE, bold=False)
                y += 60 * unit
            # Colored collectible / hazard legend.
            c.create_oval(left + 21 * unit, y + 8 * unit,
                          left + 40 * unit, y + 27 * unit,
                          fill="#000000", outline=cfg.WHITE, width=1)
            self._screen_text(left + 190 * unit, y - 2 * unit,
                              "Collect: +5 points", 42, cfg.WHITE)
            y += 60 * unit
            c.create_oval(left + 21 * unit, y + 8 * unit,
                          left + 40 * unit, y + 27 * unit,
                          fill=cfg.RED, outline=cfg.WHITE, width=1)
            self._screen_text(left + 190 * unit, y - 2 * unit,
                              "Avoid: lose a life", 42, cfg.RED)
        else:
            self._screen_text(left + 20 * unit, top + 15 * unit,
                              "RUN SUMMARY", 54, cfg.CYAN)
            self._screen_text(left + 20 * unit, top + 105 * unit,
                              "YOUR SCORE", 38, cfg.MUTED)
            self._screen_text(left + 20 * unit, top + 150 * unit,
                              str(score), 82, cfg.GOLD)
            self._screen_text(left + 20 * unit, top + 265 * unit,
                              "BEST SCORE", 38, cfg.MUTED)
            self._screen_text(left + 20 * unit, top + 310 * unit,
                              str(board["best"]), 62, cfg.GOLD)
            if new_record:
                self._screen_text(left + 320 * unit, top + 320 * unit,
                                  "NEW RECORD!", 28, cfg.GREEN)

        self._screen_text(right + 20 * unit, top + 15 * unit,
                          f"BEST SCORE: {board['best']}", 54, cfg.GOLD)
        self._screen_text(right + 20 * unit, top + 92 * unit,
                          "RECENT SCORES", 48, cfg.CYAN)
        recent = list(reversed(board.get("recent", [])))[:8]
        if recent:
            for i, value in enumerate(recent):
                self._screen_text(right + 22 * unit, top + 163 * unit + i * 39 * unit,
                                  f"{i + 1}.   {value}", 34, cfg.WHITE, bold=False)
        else:
            self._screen_text(right + 22 * unit, top + 166 * unit,
                              "No scores yet", 32, cfg.MUTED, bold=False)

        footer = ("Press SPACE to restart     •     ENTER to quit" if over
                  else "Press SPACE or ENTER to start")
        self._screen_text(cx, self.height - 70 * unit, footer, 40,
                          cfg.MUTED, "n", False)

    def draw_start(self, board):
        self._draw_menu_frame(over=False, board=board)

    def draw_game_over(self, score, board, new_record):
        self._draw_menu_frame(over=True, score=score, board=board,
                              new_record=new_record)

    # ---------- HUD (top bar during the game) ----------
    def build_hud(self, score, lives, level, black, red):
        """Create the HUD items once, then place them. Returns the bar height."""
        c = self.canvas
        self.hud = {
            "bar": c.create_rectangle(0, 0, 0, 0, fill=cfg.HUD_BG, outline=""),
            "line": c.create_line(0, 0, 0, 0, fill=cfg.HUD_LINE, width=2),
            "left": c.create_text(0, 0, anchor="w", fill=cfg.WHITE),
            "mid": c.create_text(0, 0, anchor="center", fill=cfg.WHITE),
            "right": c.create_text(0, 0, anchor="e", fill=cfg.TEXT),
            "last": None,
        }
        height = self.place_hud()
        self.update_hud(score, lives, level, black, red)
        return height

    def place_hud(self):
        """(Re)size and position the HUD for the current window. Returns its height."""
        c, h = self.canvas, self.hud
        worst = ("SCORE  9999", "LIVES  3     LEVEL  99", "BLACK 24   RED 24")
        unit = self.unit
        for _ in range(40):  # shrink until the three texts fit side by side
            fonts = (self.font("hud_main", True, unit), self.font("hud_main", True, unit),
                     self.font("hud_side", False, unit))
            if sum(f.measure(t) for f, t in zip(fonts, worst)) <= self.width - 4 * 24 * unit:
                break
            unit *= 0.94
        margin = 24 * unit
        height = round(fonts[0].metrics("linespace") + 24 * unit)
        y = height / 2
        c.coords(h["bar"], 0, 0, self.width, height)
        c.coords(h["line"], 0, height, self.width, height)
        c.coords(h["left"], margin, y)
        c.coords(h["mid"], self.width / 2, y)
        c.coords(h["right"], self.width - margin, y)
        for key, font in zip(("left", "mid", "right"), fonts):
            c.itemconfigure(h[key], font=font)
        return height

    def update_hud(self, score, lives, level, black, red):
        """Change only the text, and only when a value changed."""
        values = (f"SCORE  {score}", f"LIVES  {lives}     LEVEL  {level}",
                  f"BLACK {black}   RED {red}")
        if self.hud is None or self.hud["last"] == values:
            return
        for key, text in zip(("left", "mid", "right"), values):
            self.canvas.itemconfigure(self.hud[key], text=text)
        self.hud["last"] = values
