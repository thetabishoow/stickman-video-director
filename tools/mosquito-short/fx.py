"""fx — mosquito, particles, smoke, fire, laser and impact effects."""
from __future__ import annotations

import math
import random

from sticklib import (INK, VIVID_RED, WARM_GOLD, ELECTRIC_BLUE, col, clamp, ease, lerp,
                      pulse, puff, VIGNETTE)

# ------------------------------------------------------------- mosquito -----
def mosquito(pen, spen, gpen, pos, size=1.0, wing=0.0, tilt=0.0, hero=False, aura=0.0):
    """Tiny black mosquito: dark abdomen, splayed kung-fu legs, blurring wings, needle nose."""
    x, y = pos
    s = size
    a = math.radians(tilt)
    ca, sa = math.cos(a), math.sin(a)

    def P(dx, dy):
        return (x + (dx * ca - dy * sa) * s, y + (dx * sa + dy * ca) * s)

    BODY = (26, 22, 30)
    RIM = (226, 232, 244)

    # --- wings: fast vibrating smear (behind the body) ---
    fl = 0.5 + 0.5 * math.sin(wing)
    for j in range(4):
        k = 1 - j * 0.2
        wob = (j - 1.5) * 5.0
        spen.ellipse(P(-4 + wob, -13 - j * 1.6), (20 + j * 3) * k, (7.2 + j * 1.1) * k,
                     fill=col((236, 242, 255), 62))
    pen.ellipse(P(-5, -12 - fl * 3), 21 * s, 7.0 * s, fill=col((246, 249, 255), 205),
                outline=(196, 204, 224), width=2.2 * s, angle=-a - 0.5 - fl * 0.22)
    pen.ellipse(P(-6, -14 + fl * 3), 17 * s, 5.6 * s, fill=col((250, 252, 255), 170),
                outline=(206, 214, 230), width=2.0 * s, angle=-a - 1.0 + fl * 0.22)
    pen.line([P(-5, -12), P(-22, -20)], col((214, 220, 238)), 2.4 * s)

    # --- legs (three splayed pairs, kung-fu stance) ---
    legs = [(5, -5, 27, -22, -1), (6, 0, 33, -3, 0), (5, 6, 26, 21, 1)]
    for dx, dy, ex, ey, bend in legs:
        pen.line([P(dx, dy), P(ex, ey), P(ex + 11, ey + (10 if ey > 0 else -10))], BODY, 3.2 * s)
        pen.circle(P(ex, ey), 2.4 * s, fill=BODY)

    # --- body ---
    if hero:
        for i in range(5, 0, -1):        # dark halo so the silhouette reads on the lens
            f = i / 5
            gpen.circle((x, y + 2 * s), (58 + f * 70) * s, fill=(14, 10, 12))
    pen.ellipse(P(-11, 3), 15 * s, 9.0 * s, fill=BODY, angle=-a + 0.5)
    pen.ellipse(P(-11, 1), 11 * s, 5.4 * s, fill=(48, 42, 52), angle=-a + 0.5)
    pen.ellipse(P(3, -1), 9.5 * s, 8.0 * s, fill=BODY, angle=-a)
    pen.ellipse(P(5, -4), 5.6 * s, 4.2 * s, fill=(54, 48, 58), angle=-a)
    pen.circle(P(11, -4), 7.2 * s, fill=BODY)                     # head
    if hero or size > 0.7:
        pen.circle(P(13, -6), 3.0 * s, fill=(255, 76, 62))        # eye catches the light
        pen.circle(P(13.6, -6.6), 1.1 * s, fill=(255, 236, 226))
    if hero:                                                      # rim light
        for j in range(3):
            pen.arc(P(3, -1), (11 + j) * s, (9 + j) * s, 200, 350, col(RIM, 150 - j * 40), 2.4 * s)
    # proboscis
    pen.line([P(17, -3), P(34, 2)], (18, 14, 20), 2.8 * s)
    pen.line([P(17, -3), P(34, 2)], (70, 60, 72), 1.2 * s)
    # antennae
    pen.line([P(12, -9), P(25, -19)], BODY, 2.0 * s)
    pen.line([P(13, -7), P(28, -14)], BODY, 2.0 * s)
    if aura > 0:
        for i in range(4, 0, -1):
            f = i / 4
            spen.circle((x, y), (58 + f * 60) * s, fill=col((255, 238, 200), int(30 * aura * (1 - f))))


# ------------------------------------------------------------- particles ----
class Dust:
    """fast particle bank: dust, sparks, debris, ash, vapour."""

    def __init__(self, seed=3):
        self.rng = random.Random(seed)

    def burst(self, n, origin, spread, speed, life, tilt=0.0, gravity=0.0,
              size=(6, 22), color=(120, 110, 100), jitter=1.0):
        out = []
        for i in range(n):
            a = self.rng.uniform(0, math.tau)
            sp = speed * self.rng.uniform(0.35, 1.25)
            out.append({
                "x": origin[0] + self.rng.uniform(-8, 8) * jitter,
                "y": origin[1] + self.rng.uniform(-8, 8) * jitter,
                "vx": math.cos(a) * sp * self.rng.uniform(0.5, 1.0) + math.cos(math.radians(tilt)) * spread,
                "vy": math.sin(a) * sp * self.rng.uniform(0.5, 1.0) + math.sin(math.radians(tilt)) * spread,
                "r": self.rng.uniform(*size),
                "life": life * self.rng.uniform(0.55, 1.3),
                "age": 0.0,
                "g": gravity,
                "c": color,
                "spin": self.rng.uniform(-8, 8),
                "rot": self.rng.uniform(0, 6.28),
                "dr": self.rng.uniform(-0.4, 0.6),
            })
        return out

    def step(self, ps, dt):
        alive = []
        for p in ps:
            p["age"] += dt
            if p["age"] >= p["life"]:
                continue
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            p["vy"] += p["g"] * dt
            p["vx"] *= (1 - 1.6 * dt)
            p["vy"] *= (1 - 1.1 * dt)
            p["rot"] += p["spin"] * dt
            p["r"] = max(0.6, p["r"] * (1 + p["dr"] * dt * 0.6))
            alive.append(p)
        return alive

    def draw_soft(self, spen, ps):
        for p in ps:
            u = p["age"] / p["life"]
            a = int(150 * (1 - u) ** 1.5)
            if a <= 3:
                continue
            spen.circle((p["x"], p["y"]), p["r"] * (1 + u * 1.5), fill=col(p["c"], a))

    def draw_hard(self, pen, ps):
        for p in ps:
            u = p["age"] / p["life"]
            if u > 0.85:
                continue
            pen.ellipse((p["x"], p["y"]), p["r"] * 0.7, p["r"] * 0.45, fill=p["c"], angle=p["rot"])


def smoke_column(spen, x, y, t, height=520, width=140, density=26, color=(212, 205, 198), drift=0.0,
                 seed=11, spread=1.0, alpha=120):
    rng = random.Random(seed)
    for i in range(density):
        u = (i / density + (t * 0.12) % 1.0) % 1.0
        r = 30 + u * 90 * spread
        wob = math.sin(t * 0.7 + i * 1.7) * (18 + 46 * u)
        spen.circle((x + wob + drift * u * 340, y - u * height), r,
                    fill=col(color, int(alpha * (1 - u * 0.72))))


def fire_cone(pen, spen, gpen, origin, angle, length, width, seed=5, t=0.0):
    rng = random.Random(seed)
    a = math.radians(angle)
    ca, sa = math.cos(a), math.sin(a)

    def P(d, off):
        return (origin[0] + ca * d - sa * off, origin[1] + sa * d + ca * off)

    # outer flame body
    for i in range(16):
        d = length * (i / 16 + 0.06)
        w = width * (0.32 + 1.1 * (d / length)) * (1 + 0.16 * math.sin(t * 22 + i))
        spen.poly([P(d - length * 0.11, -w * 0.75), P(d + length * 0.10, 0), P(d - length * 0.11, w * 0.75)],
                  fill=col((255, 176, 62), 58), alpha=None)
    for i in range(14):
        d = length * (i / 14 + 0.05)
        w = width * (0.22 + 0.9 * (d / length)) * (1 + 0.2 * math.sin(t * 26 + i * 0.7))
        pen.poly([P(d - length * 0.13, -w * 0.6), P(d + length * 0.09, 0), P(d - length * 0.13, w * 0.6)],
                 fill=(255, 152, 44))
        if i < 9:
            ww = w * 0.5
            pen.poly([P(d - length * 0.15, -ww * 0.5), P(d + length * 0.04, 0), P(d - length * 0.15, ww * 0.5)],
                     fill=(255, 236, 168) if i % 2 else VIVID_RED)
    gpen.circle(origin, width * 1.15, fill=(220, 70, 20))
    gpen.circle(P(length * 0.5, 0), width * 0.95, fill=(180, 60, 12))


def laser_beam(pen, spen, gpen, x, top_y, hit_y, width, t, flicker=1.0):
    w = width * (0.92 + 0.12 * math.sin(t * 44)) * flicker
    gpen.poly([(x - w * 1.9, top_y), (x + w * 1.9, top_y), (x + w * 2.3, hit_y), (x - w * 2.3, hit_y)],
              fill=(150, 40, 30))
    spen.poly([(x - w * 1.25, top_y), (x + w * 1.25, top_y), (x + w * 1.45, hit_y), (x - w * 1.45, hit_y)],
              fill=col((255, 120, 60), 120))
    pen.poly([(x - w * 0.55, top_y), (x + w * 0.55, top_y), (x + w * 0.66, hit_y), (x - w * 0.66, hit_y)],
             fill=VIVID_RED, alpha=None)
    pen.poly([(x - w * 0.24, top_y), (x + w * 0.24, top_y), (x + w * 0.3, hit_y), (x - w * 0.3, hit_y)],
             fill=(255, 250, 214))


def blast(pen, spen, gpen, c, r, t01, color=(255, 170, 60)):
    """expanding shockwave ring + core"""
    u = ease(t01)
    rad = r * u
    spen.circle(c, rad * 0.9, fill=col(color, int(120 * (1 - u))))
    gpen.circle(c, rad * 0.62, fill=tuple(int(v * 0.7) for v in color))
    pen.circle(c, rad * 0.42, fill=(255, 244, 210))
    pen.line([(c[0] - rad * 1.25, c[1]), (c[0] + rad * 1.25, c[1])], (255, 240, 200), rad * 0.05)
    pen.line([(c[0], c[1] - rad * 1.1), (c[0], c[1] + rad * 1.1)], (255, 240, 200), rad * 0.05)


def speed_lines(pen, origin, direction, n=7, length=180, spread=0.9, color=(255, 255, 255), alpha=None):
    a = math.radians(direction)
    for i in range(n):
        u = (i / (n - 1) - 0.5) * 2 if n > 1 else 0
        off = u * spread * length * 0.5
        d0 = length * (0.35 + 0.3 * abs(u))
        x0 = origin[0] + math.cos(a) * d0 - math.sin(a) * off
        y0 = origin[1] + math.sin(a) * d0 + math.cos(a) * off
        x1 = x0 + math.cos(a) * length * 0.55
        y1 = y0 + math.sin(a) * length * 0.55
        pen.line([(x0, y0), (x1, y1)], color, 5, alpha=alpha)


def swing_arc(pen, c, r, a0, a1, color=(255, 255, 255), width=16, alpha=None):
    n = 10
    for i in range(n):
        rr = max(4.0, r - i * max(1.0, r * 0.06))
        pen.arc(c, rr, rr, a0, a1, color, max(2.0, width * (1 - i / n * 0.7)))


def anger_mark(pen, c, s=1.0, color=(232, 48, 52)):
    """manga-style detached anger cross, floats by the head."""
    x, y = c
    for sgn in (-1, 1):
        pen.line([(x - 20 * s, y - 20 * s), (x + 20 * s, y + 20 * s)], color, 8 * s)
    for sgn in (-1, 1):
        pen.line([(x - 20 * s, y + 20 * s), (x + 20 * s, y - 20 * s)], color, 8 * s)


def sweat(pen, c, s=1.0, color=(120, 190, 255)):
    x, y = c
    pen.poly([(x, y - 16 * s), (x + 11 * s, y + 8 * s), (x - 11 * s, y + 8 * s)], fill=color)
    pen.circle((x, y + 6 * s), 11 * s, fill=color)


def zzz(pen, c, t, color=(186, 196, 224), seed=0.0):
    """drifting sleep puffs — dots instead of letters, so nothing on screen is text"""
    for i in range(4):
        u = (t * 0.5 + i / 4.0 + seed) % 1.0
        r = 5 + u * 15
        x = c[0] + 34 * i + u * 54 + math.sin(u * 6 + i) * 8
        y = c[1] - u * 150 - i * 24
        a = int(200 * min(1.0, (1 - u) * 2.2))
        pen.circle((x, y), r, fill=col(color, a))
        if i == 3:
            pen.circle((x + r * 0.9, y - r * 0.5), r * 0.62, fill=col(color, int(a * 0.8)))
