"""Main Vector Rush game controller."""
import math
import random
import time
import tkinter as tk

import config as cfg
from player import Player
from ball import Ball
from ui import GameUI
from scores import load_scores, save_score
from audio import AudioManager

TICK_MS = 16
MAX_PER_TYPE = 24  # Doubling forever (2**level) would freeze the game.


class VectorRushGame:
    def __init__(self, root):
        self.root = root
        self.root.configure(bg=cfg.BACKGROUND)
        self.canvas = tk.Canvas(root, bg=cfg.BACKGROUND, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.ui = GameUI(self.canvas, cfg.load_text_scale())
        self.audio = AudioManager()
        self.board = load_scores()
        self.keys = set()
        self.state = "start"
        self.width = self.height = 0
        self.arena = (0, 0, 1, 1)  # (left, top, right, bottom) of the play area
        self.scale = 1.0
        self.balls = []
        self.black_balls = []
        self.red_balls = []
        self.score = 0
        self.lives = 3
        self.level = 0
        self.new_record = False
        self.player = None
        self._release_jobs = {}
        self._loop_job = None
        self._resize_job = None
        self.root.bind("<KeyPress>", self.key_down)
        self.root.bind("<KeyRelease>", self.key_up)
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        # The first <Configure> (window shown) and every resize redraw the screen.
        self.canvas.bind("<Configure>", self._on_configure)

    # ---------- Layout / resizing ----------
    def _on_configure(self, _event):
        if self._resize_job is not None:
            self.root.after_cancel(self._resize_job)
        self._resize_job = self.root.after(30, self._apply_layout)

    def _apply_layout(self):
        """Redraw for the current window size (start, game over or live game)."""
        self._resize_job = None
        w, h = self.canvas.winfo_width(), self.canvas.winfo_height()
        if w < 200 or h < 200:
            return
        self.width, self.height = w, h
        self.ui.resize(w, h)
        if self.state == "start":
            self.ui.draw_start(self.board)
        elif self.state == "over":
            self.ui.draw_game_over(self.score, self.board, self.new_record)
        elif self.state == "playing":
            self._relayout_world()

    @staticmethod
    def _compute_scale(arena):
        """Size/speed factor of the game objects for a given play area."""
        left, top, right, bottom = arena
        scale = min((right - left) / 900, (bottom - top) / 620) * 1.2
        return max(0.7, min(2.6, scale))

    def _relayout_world(self):
        """Window or text size changed mid-game: map everything to the new arena."""
        hud_h = self.ui.place_hud()
        new_arena = (0, hud_h, self.width, self.height)
        new_scale = self._compute_scale(new_arena)
        ol, ot, orr, ob = self.arena
        nl, nt, nr, nb = new_arena
        old_w, old_h = max(1, orr - ol), max(1, ob - ot)
        ratio = new_scale / self.scale
        for obj in [self.player] + self.balls:
            obj.x = nl + (obj.x - ol) / old_w * (nr - nl)
            obj.y = nt + (obj.y - ot) / old_h * (nb - nt)
            obj.rescale(ratio)
        self.arena, self.scale = new_arena, new_scale

    def change_text_scale(self, direction):
        """+ / - keys: make all text bigger or smaller and remember the choice."""
        factor = cfg.TEXT_SCALE_STEP if direction > 0 else 1 / cfg.TEXT_SCALE_STEP
        self.ui.text_scale = round(cfg.clamp_text_scale(self.ui.text_scale * factor), 2)
        cfg.save_text_scale(self.ui.text_scale)
        self._apply_layout()

    def toggle_fullscreen(self, force=None):
        try:
            current = bool(self.root.attributes("-fullscreen"))
            self.root.attributes("-fullscreen", (not current) if force is None else force)
        except tk.TclError:
            pass

    # ---------- Keyboard ----------
    def key_down(self, event):
        key = event.keysym
        # Cancel a pending release: X11 sends fake release/press pairs
        # while a key is held (auto-repeat).
        job = self._release_jobs.pop(key, None)
        if job is not None:
            self.root.after_cancel(job)
        if key in ("plus", "equal", "KP_Add"):
            self.change_text_scale(+1)
            return
        if key in ("minus", "underscore", "KP_Subtract"):
            self.change_text_scale(-1)
            return
        if key == "F11":
            self.toggle_fullscreen()
            return
        if key == "Escape":
            self.toggle_fullscreen(force=False)
            return
        if self.state == "start":
            if key == "space":
                self.start_game()
            elif key in ("Return", "KP_Enter"):
                self.close()
            return
        if self.state == "over":
            if key == "space":
                self.start_game()
            elif key in ("Return", "KP_Enter"):
                self.close()
            return
        if self.state == "playing":
            self.keys.add(key)

    def key_up(self, event):
        key = event.keysym
        job = self._release_jobs.pop(key, None)
        if job is not None:
            self.root.after_cancel(job)
        self._release_jobs[key] = self.root.after(30, self._release, key)

    def _release(self, key):
        self._release_jobs.pop(key, None)
        self.keys.discard(key)

    # ---------- Game flow ----------
    def start_game(self):
        self._cancel_loop()
        self.canvas.delete("all")
        self.keys.clear()
        self.balls = []
        self.black_balls = []
        self.red_balls = []
        self.score = 0
        self.lives = 3
        self.level = 0
        self.new_record = False
        hud_h = self.ui.build_hud(self.score, self.lives, 1, 0, 0)
        self.arena = (0, hud_h, self.width, self.height)
        self.scale = self._compute_scale(self.arena)
        self.player = Player(self.canvas, self.arena, self.scale)
        self._sync_ball_counts(initial=True)
        self.ui.update_hud(self.score, self.lives, self.level + 1,
                           len(self.black_balls), len(self.red_balls))
        self.state = "playing"
        self._loop()

    def _cancel_loop(self):
        if self._loop_job is not None:
            self.root.after_cancel(self._loop_job)
            self._loop_job = None

    def _safe_position(self, radius):
        left, top, right, bottom = self.arena
        for _ in range(300):
            x = random.uniform(left + radius + 8, right - radius - 8)
            y = random.uniform(top + radius + 8, bottom - radius - 8)
            if math.hypot(x - self.player.x, y - self.player.y) < 100 * self.scale:
                continue
            if any(math.hypot(x - b.x, y - b.y) < radius + b.radius + 12 for b in self.balls):
                continue
            return x, y
        return random.uniform(left + radius, right - radius), random.uniform(top + radius, bottom - radius)

    def _ball_speed(self, kind):
        base = (1.65 + self.level * 0.30) if kind == "black" else (1.40 + self.level * 0.26)
        return base * self.scale

    def _new_ball(self, kind):
        if kind == "black":
            radius, color = 8 * self.scale, "#000000"
        else:
            radius, color = 10 * self.scale, "#ff4d5a"
        x, y = self._safe_position(radius)
        ball = Ball(self.canvas, x, y, radius, self._ball_speed(kind), color, kind)
        self.balls.append(ball)
        if kind == "black":
            self.black_balls.append(ball)
        else:
            self.red_balls.append(ball)

    def _sync_ball_counts(self, initial=False):
        # At level 0: 1 black, 0 red. At each 15-point milestone,
        # both existing populations double (the first red population is 1).
        target_black = min(MAX_PER_TYPE, 2 ** self.level)
        target_red = 0 if self.level == 0 else min(MAX_PER_TYPE, 2 ** (self.level - 1))
        if initial:
            self.black_balls, self.red_balls = [], []
        while len(self.black_balls) < target_black:
            self._new_ball("black")
        while len(self.red_balls) < target_red:
            self._new_ball("red")

        # A level-up increases the speed of every ball already on screen,
        # not just balls spawned after the level-up.
        for ball in self.balls:
            new_speed = self._ball_speed(ball.kind)
            current_speed = math.hypot(ball.vx, ball.vy)
            if current_speed:
                factor = new_speed / current_speed
                ball.vx *= factor
                ball.vy *= factor
            ball.speed = new_speed

    def _loop(self):
        self._loop_job = None
        if self.state != "playing":
            return
        now = time.monotonic()
        self.player.update(self.keys, now, self.arena)
        for ball in list(self.balls):
            ball.update(self.arena)
        self._check_collisions(now)
        if self.state != "playing":
            return
        self.ui.update_hud(self.score, self.lives, self.level + 1,
                           len(self.black_balls), len(self.red_balls))
        self._loop_job = self.root.after(TICK_MS, self._loop)

    def _check_collisions(self, now):
        for ball in list(self.balls):
            distance = math.hypot(self.player.x - ball.x, self.player.y - ball.y)
            if distance > self.player.radius + ball.radius:
                continue
            if ball.kind == "black":
                self.score += 5
                self._remove_ball(ball)
                self._new_ball("black")
                self.audio.play("collect")
                new_level = self.score // 15
                if new_level > self.level:
                    self.level = new_level
                    self._sync_ball_counts()
                    self.audio.play("level_up")
            else:
                if self.player.hit(now):
                    self.lives -= 1
                    self._remove_ball(ball)
                    self._new_ball("red")
                    if self.lives <= 0:
                        self.end_game()
                        return

    def _remove_ball(self, ball):
        if ball in self.balls:
            self.balls.remove(ball)
        target = self.black_balls if ball.kind == "black" else self.red_balls
        if ball in target:
            target.remove(ball)
        ball.remove()

    def end_game(self):
        self._cancel_loop()
        self.state = "over"
        self.keys.clear()
        self.audio.play("game_over")
        self.new_record = self.score > self.board["best"]
        self.board = save_score(self.score)
        self.ui.draw_game_over(self.score, self.board, self.new_record)

    def close(self):
        self.state = "closed"
        self._cancel_loop()
        if self._resize_job is not None:
            self.root.after_cancel(self._resize_job)
        for job in self._release_jobs.values():
            self.root.after_cancel(job)
        self.audio.close()
        self.root.destroy()
