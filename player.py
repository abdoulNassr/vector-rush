"""Player ship: continuous vector movement and reflected wall collisions."""
import math


class Player:
    def __init__(self, canvas, arena, scale=1.0):
        self.canvas = canvas
        self.scale = scale
        self.radius = 17 * self.scale
        self.reset(arena)

    def reset(self, arena):
        left, top, right, bottom = arena
        self.x = (left + right) / 2
        self.y = (top + bottom) / 2
        self.angle = -math.pi / 2
        self.speed = 3.0 * self.scale
        self.min_speed = 1.2 * self.scale
        self.max_speed = 7.0 * self.scale
        self.turn_rate = 0.075
        self.invulnerable_until = 0.0
        self.flash_visible = True
        self.item = self.canvas.create_polygon(0, 0, 0, 0, 0, 0,
                                               fill="#35c9ff", outline="white",
                                               width=2)

    def update(self, keys, now, arena):
        """Steer/accelerate, move, then reflect on the arena walls."""
        left, top, right, bottom = arena
        # Rotation and acceleration are applied before movement. A wall collision
        # later in this update overrides the resulting direction.
        if "Left" in keys or "a" in keys:
            self.angle -= self.turn_rate
        if "Right" in keys or "d" in keys:
            self.angle += self.turn_rate
        if "Up" in keys or "w" in keys:
            self.speed = min(self.max_speed, self.speed + 0.12 * self.scale)
        if "Down" in keys or "s" in keys:
            self.speed = max(self.min_speed, self.speed - 0.12 * self.scale)

        vx = math.cos(self.angle) * self.speed
        vy = math.sin(self.angle) * self.speed
        self.x += vx
        self.y += vy

        bounced = False
        if self.x < left + self.radius:
            self.x = left + self.radius
            vx = abs(vx)
            bounced = True
        elif self.x > right - self.radius:
            self.x = right - self.radius
            vx = -abs(vx)
            bounced = True
        if self.y < top + self.radius:
            self.y = top + self.radius
            vy = abs(vy)
            bounced = True
        elif self.y > bottom - self.radius:
            self.y = bottom - self.radius
            vy = -abs(vy)
            bounced = True

        if bounced:
            # Reflection is authoritative for this frame; keyboard rotation
            # cannot override the reflected velocity.
            self.angle = math.atan2(vy, vx)

        self._draw(now)

    def rescale(self, ratio):
        """Window size changed: scale size and speeds by `ratio`."""
        self.scale *= ratio
        self.radius *= ratio
        self.speed *= ratio
        self.min_speed *= ratio
        self.max_speed *= ratio

    def _draw(self, now):
        if now < self.invulnerable_until:
            self.flash_visible = int(now * 12) % 2 == 0
        else:
            self.flash_visible = True
        if not self.flash_visible:
            self.canvas.itemconfigure(self.item, state="hidden")
            return
        self.canvas.itemconfigure(self.item, state="normal")
        points = []
        for distance, offset in ((22 * self.scale, 0), (-15 * self.scale, 2.45), (-15 * self.scale, -2.45)):
            a = self.angle + offset
            points.extend((self.x + math.cos(a) * distance,
                           self.y + math.sin(a) * distance))
        self.canvas.coords(self.item, *points)

    def hit(self, now, duration=2.0):
        if now < self.invulnerable_until:
            return False
        self.invulnerable_until = now + duration
        return True
