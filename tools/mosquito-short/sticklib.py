"""
sticklib — Style 4 ("Cozy Storytelling") drawing library for the 9:16 short
"Mosquito: An Overreaction" (1080x1920, 25s, 30fps).

Design contract honoured here (skills/directing-stickman-videos/references/cozy-storytelling.md):

  One minimalist 2D cartoon protagonist with a white filled circular head, two
  small dark oval eyes, simple eyebrow strokes and a short curved mouth. The
  torso is a slim closed tapered shape with solid white fill inside its dark
  outline. Both arms and both legs are dark single-line strokes with constant
  medium weight; hands are small dark rounded shapes and feet are short dark
  rounded strokes.

Exactly two arms and two legs exist; a moving limb replaces its previous pose.
Expressions only change the simple facial marks.
"""

from __future__ import annotations

import math

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

# ---------------------------------------------------------------- canvas ----
W, H = 1080, 1920          # output resolution (9:16)
FPS = 30
DUR = 25.0
SS = 2                     # supersample factor for line art

# palette (ordinary descriptive names in the prompts; raw tuples live in code)
INK = (38, 32, 48)         # warm near-black outline / limbs
PAPER = (255, 253, 249)    # character white fill
VIVID_RED = (232, 48, 52)  # accent 1 — rage, danger, fire
WARM_GOLD = (255, 186, 74)  # accent 2 — warmth, lamp light, orbital beam
ELECTRIC_BLUE = (86, 168, 255)  # accent 3 — night, moonlight


def col(c, a=255):
    return (int(c[0]), int(c[1]), int(c[2]), int(a))


# ------------------------------------------------------------ utilities -----
def lerp(a, b, t):
    return a + (b - a) * t


def clamp(v, lo=0.0, hi=1.0):
    return lo if v < lo else hi if v > hi else v


def seg(t, a, b):
    """normalised progress of t inside [a, b]"""
    if b <= a:
        return 1.0
    return clamp((t - a) / (b - a))


def ease(t):
    t = clamp(t)
    return t * t * (3 - 2 * t)


def ease_in(t):
    t = clamp(t)
    return t * t * t


def ease_out(t):
    t = clamp(t)
    return 1 - (1 - t) ** 3


def ease_out_quint(t):
    t = clamp(t)
    return 1 - (1 - t) ** 5


def ease_out_back(t, s=1.9):
    t = clamp(t)
    return 1 + (s + 1) * (t - 1) ** 3 + s * (t - 1) ** 2


def ease_elastic(t, amp=1.0, per=0.32):
    t = clamp(t)
    if t in (0.0, 1.0):
        return t
    return 1 - amp * math.cos(t * math.pi * 4 / per) * (1 - t) ** 2


def pulse(t, a, b):
    """0 → 1 → 0 over [a, b]"""
    if t <= a or t >= b:
        return 0.0
    u = (t - a) / (b - a)
    return math.sin(u * math.pi)


def rot_pt(p, o, deg):
    if deg == 0:
        return p
    a = math.radians(deg)
    ca, sa = math.cos(a), math.sin(a)
    x, y = p[0] - o[0], p[1] - o[1]
    return (o[0] + x * ca - y * sa, o[1] + x * sa + y * ca)


def mix(c1, c2, t):
    t = clamp(t)
    return tuple(int(round(lerp(c1[i], c2[i], t))) for i in range(3))


def shake(t, amp, freq=38.0, seed=0.0):
    if amp <= 0:
        return (0.0, 0.0)
    return (amp * math.sin(t * freq + seed), amp * math.sin(t * freq * 0.87 + seed * 1.7 + 1.1))


# --------------------------------------------------------------- camera -----
class Cam:
    """world -> screen mapping. World is authored at the 1080x1920 frame scale."""

    __slots__ = ("s", "cx", "cy", "ss")

    def __init__(self, s=1.0, cx=W / 2, cy=H / 2, ss=SS):
        self.s = s
        self.cx = cx
        self.cy = cy
        self.ss = ss

    def at(self, ss):
        c = Cam(self.s, self.cx, self.cy, ss)
        return c

    def pt(self, x, y):
        k = self.s * self.ss
        return ((x - self.cx) * k + W * self.ss / 2, (y - self.cy) * k + H * self.ss / 2)

    def sc(self, v):
        return v * self.s * self.ss

    def inv(self, sx, sy):
        """screen pixel -> world point (used to author effects in frame space)"""
        return (self.cx + (sx - W / 2) / self.s, self.cy + (sy - H / 2) / self.s)


# ------------------------------------------------------------------ pen -----
class Pen:
    """vector drawing through the camera transform."""

    def __init__(self, dr, cam, img=None):
        self.dr = dr
        self.cam = cam
        self.img = img

    def _w(self, w):
        return max(1, int(round(self.cam.sc(w))))

    def line(self, pts, color, width=10, joint="curve", alpha=None):
        p = [self.cam.pt(*q) for q in pts]
        f = color if alpha is None else col(color, alpha)
        if len(p) == 2:
            self.dr.line(p, fill=f, width=self._w(width))
        else:
            self.dr.line(p, fill=f, width=self._w(width), joint=joint)

    def circle(self, c, r, fill=None, outline=None, width=8):
        x, y = self.cam.pt(*c)
        rr = self.cam.sc(r)
        self.dr.ellipse([x - rr, y - rr, x + rr, y + rr], fill=fill, outline=outline,
                        width=self._w(width) if outline else 0)

    def ellipse(self, c, rx, ry, fill=None, outline=None, width=8, angle=0.0):
        x, y = self.cam.pt(*c)
        rxx, ryy = self.cam.sc(rx), self.cam.sc(ry)
        box = [x - rxx, y - ryy, x + rxx, y + ryy]
        if angle:
            tmp = Image.new("RGBA", (int(rxx * 2) + 4, int(ryy * 2) + 4), (0, 0, 0, 0))
            d = ImageDraw.Draw(tmp)
            d.ellipse([2, 2, int(rxx * 2) + 1, int(ryy * 2) + 1], fill=fill, outline=outline,
                      width=self._w(width) if outline else 0)
            tmp = tmp.rotate(math.degrees(angle), resample=Image.BILINEAR, expand=True)
            self.img.paste(tmp, (int(x - tmp.width / 2), int(y - tmp.height / 2)), tmp)
        else:
            self.dr.ellipse(box, fill=fill, outline=outline, width=self._w(width) if outline else 0)

    def poly(self, pts, fill=None, outline=None, width=8, round_join=False, alpha=None):
        p = [self.cam.pt(*q) for q in pts]
        f = fill if alpha is None else (col(fill, alpha) if fill else None)
        self.dr.polygon(p, fill=f)
        if outline:
            self.line(pts + ([pts[0]] if round_join else []), outline, width)

    def rrect(self, box, radius, fill=None, outline=None, width=8, alpha=None):
        x0, y0 = self.cam.pt(box[0], box[1])
        x1, y1 = self.cam.pt(box[2], box[3])
        f = fill if alpha is None else (col(fill, alpha) if fill else None)
        o = outline if alpha is None else (col(outline, alpha) if outline else None)
        self.dr.rounded_rectangle([x0, y0, x1, y1], radius=self.cam.sc(radius), fill=f,
                                  outline=o, width=self._w(width) if outline else 0)

    def rrect_rot(self, c, w, h, r, angle_deg, fill=None, outline=None, width=8):
        """rounded rectangle rotated about its own centre"""
        pad = 6
        tmp = Image.new("RGBA", (int(self.cam.sc(w)) + pad * 2, int(self.cam.sc(h)) + pad * 2), (0, 0, 0, 0))
        d = ImageDraw.Draw(tmp)
        d.rounded_rectangle([pad, pad, int(self.cam.sc(w)) + pad, int(self.cam.sc(h)) + pad],
                            radius=max(1, int(self.cam.sc(r))), fill=fill,
                            outline=outline, width=self._w(width) if outline else 0)
        tmp = tmp.rotate(angle_deg, resample=Image.BILINEAR, expand=True)
        x, y = self.cam.pt(*c)
        self.img.paste(tmp, (int(x - tmp.width / 2), int(y - tmp.height / 2)), tmp)

    def arc(self, c, rx, ry, a0, a1, color, width=8):
        rx, ry = max(abs(rx), 1.0), max(abs(ry), 1.0)
        x, y = self.cam.pt(*c)
        self.dr.arc([x - self.cam.sc(rx), y - self.cam.sc(ry), x + self.cam.sc(rx), y + self.cam.sc(ry)],
                    a0, a1, fill=color, width=self._w(width))

    def star(self, c, r, color, n=5, rot=0.0):
        pts = []
        for i in range(n * 2):
            a = rot + i * math.pi / n
            rr = r if i % 2 == 0 else r * 0.42
            pts.append((c[0] + math.cos(a) * rr, c[1] + math.sin(a) * rr))
        self.poly(pts, fill=color)


# --------------------------------------------------------------- frame ------
class Frame:
    """one composited frame: crisp vector art (supersampled) + soft layer + glow."""

    def __init__(self, cam: Cam, bg: Image.Image | None = None, bg_off=(0.0, 0.0)):
        self.cam = cam
        self.base = Image.new("RGB", (W * SS, H * SS), (0, 0, 0))
        if bg is not None:
            img = bg.resize((W * SS, H * SS), Image.BILINEAR) if bg.size != (W * SS, H * SS) else bg
            self.base.paste(img, (int(bg_off[0]), int(bg_off[1])))
        self.dr = ImageDraw.Draw(self.base)
        self.pen = Pen(self.dr, cam, self.base)
        self.soft = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        self.sdr = ImageDraw.Draw(self.soft)
        self.spen = Pen(self.sdr, cam.at(1), self.soft)
        self.glow = Image.new("RGB", (W, H), (0, 0, 0))
        self.gdr = ImageDraw.Draw(self.glow)
        self.gpen = Pen(self.gdr, cam.at(1), self.glow)

    # -- compositing ---------------------------------------------------------
    def finish(self, glow_radius=26.0, flash=None, flash_a=0.0, tint=None, tint_a=0.0,
               vignette=0.30, fade=0.0, grain=0.0):
        img = self.base.resize((W, H), Image.LANCZOS)
        if self.soft.getbbox() is not None:
            img = Image.alpha_composite(img.convert("RGBA"), self.soft).convert("RGB")
        out = np.asarray(img, dtype=np.float32)

        if glow_radius > 0.5:
            g = self.glow.filter(ImageFilter.GaussianBlur(glow_radius))
            ga = np.asarray(g, dtype=np.float32)
            if ga.max() > 1.0:
                out = 255.0 - (255.0 - out) * (255.0 - ga) / 255.0  # screen

        if tint is not None and tint_a > 0:
            t = np.array(tint, dtype=np.float32)
            out = out * (1 - tint_a) + t * tint_a
        if flash is not None and flash_a > 0:
            f = np.array(flash, dtype=np.float32)
            out = out * (1 - flash_a) + f * flash_a
        if vignette > 0:
            out *= VIGNETTE
        if grain > 0:
            out += GRAIN * grain
        if fade > 0:
            out *= (1.0 - fade)

        return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))


# precomputed vignette + grain
_yy, _xx = np.mgrid[0:H, 0:W]
_r = np.sqrt((( _xx - W / 2) / (W / 2)) ** 2 + ((_yy - H / 2) / (H / 2)) ** 2)
VIGNETTE = (1.0 - 0.42 * np.clip((_r - 0.55) / 0.75, 0, 1) ** 1.6)[:, :, None]
_rng = np.random.default_rng(7)
GRAIN = _rng.normal(0, 7.0, (H, W, 1)).astype(np.float32)


def vgrad(w, h, top, bot, mid=None, mid_at=0.5):
    ys = np.linspace(0, 1, h, dtype=np.float32)[:, None]
    t = np.array(top, dtype=np.float32)[None, :]
    b = np.array(bot, dtype=np.float32)[None, :]
    if mid is None:
        arr = t + (b - t) * ys
    else:
        m = np.array(mid, dtype=np.float32)[None, :]
        k = (ys / mid_at).clip(0, 1)
        arr2 = m + (b - m) * ((ys - mid_at) / (1 - mid_at)).clip(0, 1)
        arr = t + (m - t) * k
        arr = np.where(ys <= mid_at, arr, arr2)
    arr = np.repeat(arr[:, None, :], w, axis=1)
    return Image.fromarray(arr.astype(np.uint8), "RGB")


def vgrad_wide(w, h, stops):
    """stops: [(pos, (r,g,b)), ...]"""
    ys = np.linspace(0, 1, h, dtype=np.float32)
    arr = np.zeros((h, 3), dtype=np.float32)
    stops = sorted(stops)
    for i in range(len(stops) - 1):
        p0, c0 = stops[i]
        p1, c1 = stops[i + 1]
        m = (ys >= p0) & (ys <= p1)
        u = np.clip((ys[m] - p0) / max(1e-6, p1 - p0), 0, 1)[:, None]
        arr[m] = np.array(c0, dtype=np.float32)[None, :] * (1 - u) + np.array(c1, dtype=np.float32)[None, :] * u
    arr[ys <= stops[0][0]] = np.array(stops[0][1], dtype=np.float32)
    arr[ys >= stops[-1][0]] = np.array(stops[-1][1], dtype=np.float32)
    return Image.fromarray(np.repeat(arr[:, None, :], w, axis=1).astype(np.uint8), "RGB")


# ---------------------------------------------------------------- anim ------
class Anim:
    """keyframed pose track. Keys are flat dicts of floats + a few strings.
    '_ease' on a key names the easing used to arrive at it (default smoothstep)."""

    EASES = {
        "ease": ease, "in": ease_in, "out": ease_out, "out5": ease_out_quint,
        "back": ease_out_back, "elastic": ease_elastic, "linear": lambda t: clamp(t),
        "hold": lambda t: 0.0,
    }

    def __init__(self, base, keys):
        self.base = dict(base)
        self.keys = sorted(keys, key=lambda k: k[0])

    def keys_at(self, t):
        return [k for k in self.keys if k[0] <= t + 1e-9]

    def sample(self, t):
        if not self.keys or t <= self.keys[0][0]:
            out = dict(self.base)
            if self.keys:
                out.update(self.keys[0][1])
            return out
        if t >= self.keys[-1][0]:
            out = dict(self.base)
            for _, p in self.keys:
                out.update(p)
            return out
        for i in range(len(self.keys) - 1):
            t0, p0 = self.keys[i]
            t1, p1 = self.keys[i + 1]
            if t0 <= t <= t1:
                e = self.EASES.get(p1.get("_ease", "ease"), ease)
                u = e((t - t0) / max(1e-9, t1 - t0))
                out = dict(self.base)
                for _, pk in self.keys[:i + 1]:
                    out.update(pk)
                for k, v1 in p1.items():
                    if k.startswith("_"):
                        continue
                    v0 = out.get(k, self.base.get(k, v1))
                    if isinstance(v0, (int, float)) and isinstance(v1, (int, float)):
                        out[k] = lerp(v0, v1, u)
                    else:
                        out[k] = v0 if u < 1.0 else v1
                return out
        return dict(self.base)


# ----------------------------------------------------------------- rig ------
class Rig:
    """Style 4 protagonist. Sizes are in world units; 1.0 ≈ 720 units tall."""

    def __init__(self, scale=1.0):
        k = scale
        self.k = k
        self.head_r = 76 * k
        self.torso = 200 * k
        self.shoulder_w = 86 * k
        self.waist_w = 48 * k
        self.arm1, self.arm2 = 112 * k, 108 * k
        self.leg1, self.leg2 = 134 * k, 130 * k
        self.limb_w = 11 * k
        self.outline_w = 9 * k
        self.hand_r = 13 * k
        self.foot_l = 36 * k

    @property
    def height(self):
        return self.head_r * 2 + self.torso + self.leg1 + self.leg2 + 20

    # two-bone IK: returns (joint, end_effector)
    def ik(self, root, target, l1, l2, bend=1.0):
        dx, dy = target[0] - root[0], target[1] - root[1]
        d = math.hypot(dx, dy)
        d = clamp(d, abs(l1 - l2) + 0.5, l1 + l2 - 0.5, )
        a = math.atan2(dy, dx)
        cosb = (l1 * l1 + d * d - l2 * l2) / (2 * l1 * d)
        b = math.acos(clamp(cosb, -1.0, 1.0))
        ang = a + bend * b
        joint = (root[0] + math.cos(ang) * l1, root[1] + math.sin(ang) * l1)
        end = (root[0] + math.cos(a) * d, root[1] + math.sin(a) * d)
        return joint, end

    # ---- skeleton anchors (shared by the drawing code and prop attachment) ----
    def face_rot(self, pose):
        return math.degrees(pose.get("head", 0.0)) * 0.8 + pose.get("frot", 0.0)

    def anchors(self, pose):
        hip = (pose["x"], pose["y"])
        lr = math.radians(pose.get("lean", 0.0))
        rot = pose.get("rot", 0.0)
        n = lambda p: rot_pt(p, hip, rot) if rot else p
        neck = n((hip[0] + math.sin(lr) * self.torso, hip[1] - math.cos(lr) * self.torso))
        sh = n((neck[0] + math.sin(lr) * 18 * self.k, neck[1] - math.cos(lr) * 18 * self.k))
        ha = lr + math.radians(pose.get("head", 0.0))
        head = n((neck[0] + math.sin(ha) * (self.head_r + 6 * self.k),
                  neck[1] - math.cos(ha) * (self.head_r + 6 * self.k)))
        return hip, neck, sh, head, n

    def hand_pos(self, pose, side):
        hip, neck, sh, head, n = self.anchors(pose)
        dx = -1 if side == "L" else 1
        lr = math.radians(pose.get("lean", 0.0))
        tx = pose.get("h%sx" % side, hip[0] + dx * 46 * self.k + math.sin(lr) * 26 * self.k)
        ty = pose.get("h%sy" % side, hip[1] + 118 * self.k)
        bend = pose.get("h%sb" % side, -1.0 if side == "L" else 1.0)
        _, e = self.ik(sh, (tx, ty), self.arm1, self.arm2, bend)
        return n(e)

    def nose(self, pose, k=0.95):
        _, _, _, head, _ = self.anchors(pose)
        r = self.head_r * pose.get("hs", 1.0)
        return rot_pt((head[0], head[1] - k * r), head, self.face_rot(pose))

    def face_pt(self, pose, local=(0.0, 0.0)):
        _, _, _, head, _ = self.anchors(pose)
        r = self.head_r * pose.get("hs", 1.0)
        return rot_pt((head[0] + local[0] * r, head[1] + local[1] * r), head, self.face_rot(pose))

    def draw(self, pen: Pen, pose: dict, glow_pen: Pen | None = None):
        k = self.k
        hip = (pose["x"], pose["y"])
        lean = pose.get("lean", 0.0)
        rot = pose.get("rot", 0.0)
        lr = math.radians(lean)
        n = lambda p: rot_pt(p, hip, rot) if rot else p

        neck = n((hip[0] + math.sin(lr) * self.torso, hip[1] - math.cos(lr) * self.torso))
        sh = n((neck[0] + math.sin(lr) * 18 * k, neck[1] - math.cos(lr) * 18 * k))
        head_tilt = pose.get("head", 0.0)
        ha = lr + math.radians(head_tilt)
        head = n((neck[0] + math.sin(ha) * (self.head_r + 6 * k),
                  neck[1] - math.cos(ha) * (self.head_r + 6 * k)))

        # --- limb targets (defaults: relaxed standing) -----------------------
        def hand(side):
            dx = -1 if side == "L" else 1
            return (pose.get("h%sx" % side, hip[0] + dx * 46 * k + math.sin(lr) * 26 * k),
                    pose.get("h%sy" % side, hip[1] + 118 * k),
                    pose.get("h%sb" % side, -1.0 if side == "L" else 1.0))

        def foot(side):
            dx = -1 if side == "L" else 1
            return (pose.get("f%sx" % side, hip[0] + dx * 40 * k),
                    pose.get("f%sy" % side, hip[1] + (self.leg1 + self.leg2) * 0.94),
                    pose.get("f%sb" % side, -1.0 if side == "L" else 1.0))

        limbs = {}
        for side in ("L", "R"):
            tx, ty, tb = hand(side)
            j, e = self.ik(sh, (tx, ty), self.arm1, self.arm2, tb)
            limbs["h" + side] = (n(sh), n(j), n(e))
        for side in ("L", "R"):
            tx, ty, tb = foot(side)
            j, e = self.ik(hip, (tx, ty), self.leg1, self.leg2, tb)
            limbs["f" + side] = (n(hip), n(j), n(e))

        ink = pose.get("ink", INK)
        fill = pose.get("fill", PAPER)
        lw = self.limb_w * pose.get("lw", 1.0)

        # --- far limbs -------------------------------------------------------
        for key in ("fL", "hL", "fR", "hR"):
            a, b, c = limbs[key]
            is_arm = key.startswith("h")
            pen.line([a, b, c], ink, lw)
            if is_arm:
                pen.circle(c, self.hand_r * pose.get("lw", 1.0), fill=ink)
            else:
                bx, by = c[0] - b[0], c[1] - b[1]
                ang = math.atan2(by, bx) + math.radians(-70 if key == "fR" else 70)
                pen.line([c, (c[0] + math.cos(ang) * self.foot_l,
                              c[1] + math.sin(ang) * self.foot_l)], ink, lw * 1.2)

        # --- torso ------------------------------------------------------------
        nx, ny = neck
        sw, ww = self.shoulder_w / 2, self.waist_w / 2
        ux, uy = math.sin(lr), -math.cos(lr)          # up along torso
        px, py = math.cos(lr), math.sin(lr)           # perpendicular
        s_l = (nx - px * sw, ny - py * sw)
        s_r = (nx + px * sw, ny + py * sw)
        h_l = (hip[0] - px * ww, hip[1] - py * ww)
        h_r = (hip[0] + px * ww, hip[1] + py * ww)
        torso_pts = [n(p) for p in (h_l, s_l, s_r, h_r)]
        pen.poly(torso_pts, fill=fill, outline=ink, width=self.outline_w, round_join=True)

        # --- head -------------------------------------------------------------
        hr = self.head_r * pose.get("hs", 1.0)
        pen.circle(head, hr, fill=fill, outline=ink, width=self.outline_w)
        self._face(pen, head, hr, pose, glow_pen, ha)

    # ---- face marks --------------------------------------------------------
    def _face(self, pen, head, hr, pose, glow_pen, ha):
        expr = pose.get("expr", "open")
        ink = pose.get("ink", INK)
        ex = hr * 0.36
        ey = -hr * 0.12
        er = hr * 0.11
        t = pose.get("_t", 0.0)

        def rot(p):
            return rot_pt((head[0] + p[0], head[1] + p[1]), head, self.face_rot(pose))

        if expr in ("closed", "sleep"):
            for s in (-1, 1):
                a = rot((s * ex - er, ey + er * 0.4))
                b = rot((s * ex + er, ey + er * 0.4))
                pen.line([a, b], ink, hr * 0.10)
        elif expr == "x":
            for s in (-1, 1):
                c = (s * ex, ey)
                d = er * 1.1
                pen.line([rot((c[0] - d, c[1] - d)), rot((c[0] + d, c[1] + d))], ink, hr * 0.10)
                pen.line([rot((c[0] - d, c[1] + d)), rot((c[0] + d, c[1] - d))], ink, hr * 0.10)
        elif expr == "rage":
            rr = er * 1.5
            if glow_pen is not None:
                for s in (-1, 1):
                    glow_pen.circle(rot((s * ex, ey)), rr * 2.0, fill=(120, 0, 0))
                    glow_pen.circle(rot((s * ex, ey)), rr * 1.05, fill=(255, 40, 40))
            for s in (-1, 1):
                pen.circle(rot((s * ex, ey)), rr, fill=VIVID_RED, outline=ink, width=hr * 0.055)
                pen.circle(rot((s * ex - s * rr * 0.25, ey + rr * 0.15)), rr * 0.28, fill=(255, 240, 235))
        elif expr == "wide":
            for s in (-1, 1):
                pen.circle(rot((s * ex, ey)), er * 1.45, fill=(255, 255, 255), outline=ink, width=hr * 0.07)
                pen.circle(rot((s * ex + s * er * 0.2, ey)), er * 0.55, fill=ink)
        elif expr == "spiral":
            for s in (-1, 1):
                pen.circle(rot((s * ex, ey)), er * 1.3, fill=(255, 255, 255), outline=ink, width=hr * 0.07)
                pen.arc(rot((s * ex, ey)), er * 0.95, er * 0.95, 0, 300, ink, hr * 0.07)
                pen.arc(rot((s * ex, ey)), er * 0.45, er * 0.45, 90, 400, ink, hr * 0.06)
        else:  # open / proud / determined
            big = 1.25 if expr == "proud" else 1.0
            for s in (-1, 1):
                pen.ellipse(rot((s * ex, ey)), er * 0.95 * big, er * 1.15 * big, fill=ink)

        # brows
        brow = pose.get("brow", 0.0)
        if brow != 0.0:
            for s in (-1, 1):
                a = rot((s * ex - er * 1.2, ey - er * 2.5 + s * brow * er * 1.1))
                b = rot((s * ex + er * 1.2, ey - er * 2.5 - s * brow * er * 1.1))
                pen.line([a, b], ink, hr * 0.095)

        # mouth
        m = pose.get("mouth", "flat")
        mw = hr * 0.30 * pose.get("mws", 1.0)
        my = ey + hr * 0.46
        if m == "o":
            pen.ellipse(rot((0, my)), mw * 0.34, mw * 0.44, fill=ink)
        elif m == "open":
            pen.ellipse(rot((0, my + hr * 0.04)), mw * 0.62, mw * 0.86, fill=(96, 40, 46), outline=ink,
                        width=hr * 0.06)
        elif m == "smile":
            pen.arc(rot((0, my - mw * 0.5)), mw * 1.15, mw * 1.15, 20, 160, ink, hr * 0.10)
        elif m == "grin":
            pen.arc(rot((0, my - mw * 0.7)), mw * 1.5, mw * 1.5, 15, 165, ink, hr * 0.12)
        elif m == "frown":
            pen.arc(rot((0, my + mw * 1.1)), mw * 1.15, mw * 1.15, 200, 340, ink, hr * 0.10)
        elif m == "wiggle":
            pts = []
            for i in range(7):
                u = i / 6
                pts.append(rot((-mw + 2 * mw * u, my + math.sin(u * 6.0 + t * 9) * hr * 0.09)))
            pen.line(pts, ink, hr * 0.085)
        elif m == "flat":
            pen.line([rot((-mw * 0.7, my)), rot((mw * 0.7, my))], ink, hr * 0.09)


# ---------------------------------------------------- soft / glow helpers ---
def puff(spen: Pen, c, r, color, alpha):
    spen.circle(c, r, fill=col(color, alpha))


def glow_circle(gpen: Pen, c, r, color, layers=3):
    for i in range(layers, 0, -1):
        f = i / layers
        gpen.circle(c, r * (0.45 + f * 0.85), fill=tuple(int(v * (0.35 + 0.65 * (1 - f))) for v in color))


def glow_line(gpen: Pen, pts, color, width, layers=3, scale=1.0):
    for i in range(layers, 0, -1):
        f = i / layers
        gpen.line(pts, tuple(int(v * (0.3 + 0.7 * (1 - f))) for v in color), width * scale * (0.5 + f))


def star_flash(pen: Pen, c, r, color, n=6, rot=0.0):
    for i in range(n):
        a = rot + i * math.pi / n
        a2 = rot + (i + 0.5) * math.pi / n
        pen.poly([c,
                  (c[0] + math.cos(a) * r, c[1] + math.sin(a) * r),
                  (c[0] + math.cos(a2) * r * 0.16, c[1] + math.sin(a2) * r * 0.16)],
                 fill=color)
