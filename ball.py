"""Moving collectible and hazard balls."""
import math
import random


class Ball:
    def __init__(self, canvas, x, y, radius, speed, color, kind):
        self.canvas = canvas
        self.x = x
        self.y = y
        self.radius = radius
        self.speed = speed
        self.kind = kind
        angle = random.uniform(0, math.tau)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.item = canvas.create_oval(0, 0, 0, 0, fill=color, outline="white")
        self._sync()

    def update(self, arena):
        """Move one step and reflect on the arena walls (left, top, right, bottom)."""
        left, top, right, bottom = arena
        self.x += self.vx
        self.y += self.vy
        if self.x - self.radius <= left:
            self.x = left + self.radius
            self.vx = abs(self.vx)
        elif self.x + self.radius >= right:
            self.x = right - self.radius
            self.vx = -abs(self.vx)
        if self.y - self.radius <= top:
            self.y = top + self.radius
            self.vy = abs(self.vy)
        elif self.y + self.radius >= bottom:
            self.y = bottom - self.radius
            self.vy = -abs(self.vy)
        self._sync()

    def rescale(self, ratio):
        """Window size changed: scale size and speed by `ratio`."""
        self.radius *= ratio
        self.vx *= ratio
        self.vy *= ratio
        self.speed *= ratio
        self._sync()

    def _sync(self):
        r = self.radius
        self.canvas.coords(self.item, self.x - r, self.y - r, self.x + r, self.y + r)
        self.canvas.itemconfigure(self.item, width=max(2, int(r / 4)))

    def remove(self):
        self.canvas.delete(self.item)
