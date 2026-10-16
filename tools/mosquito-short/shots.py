"""shots — the 25-second timeline of "Mosquito: An Overreaction" (9:16, 1080x1920, 30fps).

Cut list (absolute seconds):
  00.0-03.2  THE HOOK        sleeping stickman, buzzing dot lands on his nose, rage eyes snap open
  03.2-10.7  THE ESCALATION  self-slap that misses, giant flyswatter, furniture wiped out
  10.7-19.6  THE CLIMAX      bazooka, flamethrower, red button, orbital laser, house erased
  19.6-25.0  THE PUNCHLINE   crater, proud breathing, mosquito on the lens, faint
"""
from __future__ import annotations

import math
import random

from PIL import Image

from sticklib import (Anim, Cam, Frame, H, INK, PAPER, Rig, SS, VIVID_RED, W, WARM_GOLD,
                      ELECTRIC_BLUE, clamp, col, ease, ease_elastic, ease_in, ease_out,
                      ease_out_back, ease_out_quint, lerp, pulse, rot_pt, seg, shake, star_flash)
import fx
import props

RIG = Rig(1.0)
DUST = fx.Dust(3)

# ------------------------------------------------------------------ tracks --
def cam_at(t, keys, ex=(0.0, 0.0)):
    if t <= keys[0][0]:
        k = keys[0]
        return Cam(k[1], k[2] + ex[0], k[3] + ex[1])
    if t >= keys[-1][0]:
        k = keys[-1]
        return Cam(k[1], k[2] + ex[0], k[3] + ex[1])
    for i in range(len(keys) - 1):
        t0, s0, x0, y0 = keys[i]
        t1, s1, x1, y1 = keys[i + 1]
        if t0 <= t <= t1:
            u = ease((t - t0) / max(1e-9, t1 - t0))
            return Cam(lerp(s0, s1, u), lerp(x0, x1, u) + ex[0], lerp(y0, y1, u) + ex[1])
    k = keys[-1]
    return Cam(k[1], k[2] + ex[0], k[3] + ex[1])


def impacts(t, evs, freq=26.0):
    """decaying camera shake from a list of (time, amplitude, tau)."""
    dx = dy = 0.0
    for (t0, amp, tau) in evs:
        if t >= t0:
            d = t - t0
            if d < tau * 4:
                k = amp * math.exp(-d / tau)
                dx += k * math.sin(d * freq)
                dy += k * math.sin(d * freq * 0.83 + 1.0)
    return (dx, dy)


def track(t, keys, e=ease):
    """generic scalar track: keys = [(t, v), ...]"""
    if t <= keys[0][0]:
        return keys[0][1]
    if t >= keys[-1][0]:
        return keys[-1][1]
    for i in range(len(keys) - 1):
        t0, v0 = keys[i]
        t1, v1 = keys[i + 1]
        if t0 <= t <= t1:
            return lerp(v0, v1, e((t - t0) / max(1e-9, t1 - t0)))
    return keys[-1][1]


def path(t, keys, e=ease):
    """2-D track: keys = [(t, x, y), ...]"""
    if t <= keys[0][0]:
        return keys[0][1:]
    if t >= keys[-1][0]:
        return keys[-1][1:]
    for i in range(len(keys) - 1):
        t0, x0, y0 = keys[i]
        t1, x1, y1 = keys[i + 1]
        if t0 <= t <= t1:
            u = e((t - t0) / max(1e-9, t1 - t0))
            return (lerp(x0, x1, u), lerp(y0, y1, u))
    return keys[-1][1:]


# ------------------------------------------------------- character poses ----
LYING = dict(x=520, y=props.HEAD_Y, lean=-90, frot=44, expr="closed", mouth="flat", brow=0.0,
             hs=1.0, lw=1.0, rot=0.0,
             hLx=452, hLy=1176, hLb=-1.0, hRx=470, hRy=1300, hRb=1.0,
             fLx=772, fLy=1258, fLb=-1.0, fRx=752, fRy=1222, fRb=1.0)

STAND = dict(x=470, y=1256, lean=0.0, frot=0.0, expr="open", mouth="flat", brow=0.0,
             hs=1.0, lw=1.0, rot=0.0,
             hLx=418, hLy=1372, hLb=-1.0, hRx=524, hRy=1372, hRb=1.0,
             fLx=428, fLy=1506, fLb=-1.0, fRx=514, fRy=1506, fRb=1.0)


def base(kind="stand"):
    p = dict(STAND if kind == "stand" else LYING)
    return p


ROOM_OK = dict(bed=0.0, dresser=0.0, lamp=0.0, mirror=0.0, chair=0.0, plant=0.0, picture=0.0)


# ============================================================== SHOT 1 ======
class Shot1:
    t0, t1 = 0.0, 3.10
    ease_out_to = 0.0

    def __init__(self):
        self.pose = Anim(LYING, [
            (0.00, dict(expr="closed", mouth="flat", brow=0.0)),
            (1.90, dict(brow=0.10, mouth="flat", hRy=1294)),
            (2.16, dict(brow=0.40, mouth="frown", frot=42)),
            (2.42, dict(brow=0.80, mouth="frown", hLx=470, hLy=1188, frot=41)),
            (2.55, dict(expr="rage", brow=1.0, mouth="open", y=1216, x=526, frot=40, _ease="hold")),
            (2.72, dict(expr="rage", brow=1.0, mouth="open", x=528, y=1212, hs=1.03)),
            (3.20, dict(expr="rage", brow=1.0, mouth="open", x=530, y=1210, hs=1.02)),
        ])
        # mosquito track in screen space, ending on the nose
        self.buzz = [(0.62, 120, 1146), (0.95, 268, 1082), (1.30, 246, 972), (1.62, 330, 902),
                     (1.90, 426, 902)]

    def render(self, t):
        red = ease(seg(t, 2.42, 2.85))
        sh = impacts(t, [(2.55, 17, 0.11)])
        cam = cam_at(t, [(0.00, 1.44, 384, 1330), (0.90, 1.56, 366, 1322), (1.80, 1.64, 358, 1318),
                         (2.38, 1.56, 366, 1320), (2.52, 1.96, 340, 1300), (3.20, 2.06, 336, 1294)], sh)
        f = Frame(cam)
        pen, spen, gpen = f.pen, f.spen, f.gpen
        dmg = ROOM_OK
        props.room_back(pen, spen, gpen, t, dmg, 0.0, fire=0.0)
        # wall glow from the bedside lamp
        t_room = t

        pose = self.pose.sample(t)
        pose["_t"] = t
        pose["y"] += math.sin(t * 2.05) * 2.6          # slow breathing
        pose["hRy"] += math.sin(t * 2.05) * 2.0
        RIG.draw(pen, pose, glow_pen=gpen)
        props.bed_front(pen, spen, gpen, 0.0, t)

        # zzz + snore puffs while asleep
        if t < 2.35:
            a = 1.0 - seg(t, 2.05, 2.35)
            fx.zzz(pen, (150, 1104), t, color=(150, 160, 190), seed=0.0)
            if int(t * 1.5) % 3 == 0:
                spen.circle((150, 1180 - (t % 0.7) * 40), 26 + (t % 0.7) * 30, fill=col((235, 232, 226), 46 * a))

        # mosquito
        if t > 0.60:
            nose_w = RIG.nose(pose, 0.98)
            target_w = cam.inv(426, 902)
            blend = ease(seg(t, 1.80, 1.98))
            sx, sy = path(t, self.buzz)
            world = cam.inv(sx, sy)
            px = lerp(world[0], nose_w[0] - 22, blend)
            py = lerp(world[1], nose_w[1] - 16, blend)
            if t < 0.75:
                px, py = cam.inv(lerp(120, sx, ease(seg(t, 0.62, 0.75))), sy)
            if t > 2.55:
                lift = ease_out_quint(seg(t, 2.72, 3.20)) * 46
                px += lift * 0.7
                py -= lift
            size = 1.05 if t < 1.6 else lerp(1.05, 1.4, ease(seg(t, 1.6, 1.95)))
            fx.mosquito(pen, spen, gpen, (px, py), size=size, wing=t * 46, tilt=math.sin(t * 6) * 14)
            if t > 2.55:
                for i in range(3):
                    fx.swing_arc(pen, (px + 40, py + 26), 26 + i * 12, 120, 250, (200, 200, 210), 5)

        # rage marks + eye glow bloom
        if t > 2.50:
            u = seg(t, 2.50, 2.95)
            a = int(150 * math.sin(u * math.pi) + 90 * (1 - u) * 0)
            fx.anger_mark(pen, RIG.face_pt(pose, (1.72, -1.16)), 0.85 + 0.35 * pulse(t, 2.5, 3.2))
            fx.anger_mark(spen, RIG.face_pt(pose, (-1.85, -1.22)), 0.6)
            for s_ in (-1, 1):
                ep = RIG.face_pt(pose, (s_ * 0.36, -0.12))
                fx.puff(spen, ep, 42 * (0.6 + u * 0.8), (255, 40, 30), 120 * u)

        return f.finish(glow_radius=24 + 26 * red, tint=(120, 10, 16), tint_a=0.16 * red,
                        vignette=0.30 + 0.18 * red)


# ============================================================ SHOT 2 =======
class Shot2:
    t0, t1 = 2.98, 10.67

    def __init__(self):
        self.pose = Anim(LYING, [
            (0.30, dict(LYING)),
            (0.52, dict(x=500, y=1226, lean=-52, frot=26, expr="rage", brow=1.0, mouth="open",
                        hLx=430, hLy=1250, hRx=470, hRy=1330, fLx=640, fLy=1400, fRx=560, fRy=1440,
                        _ease="back")),
            (0.72, dict(x=470, y=1256, lean=-4, frot=0, expr="rage", brow=1.0, mouth="open",
                        hLx=418, hLy=1300, hRx=520, hRy=1330, fLx=428, fLy=1506, fRx=514, fRy=1506,
                        _ease="out")),
            (0.88, dict(x=470, y=1250, lean=8, brow=1.0, mouth="open", hRx=498, hRy=1160, hRb=-1.6,
                        hLx=408, hLy=1240, _ease="out")),
            (1.00, dict(x=474, y=1244, lean=6, head=-9, mouth="open", hs=1.05, frown=0.0,
                        hRx=386, hRy=1160, hRb=-1.9, hLx=396, hLy=1236, fLx=420, fLy=1504, fRx=520,
                        fRy=1512, _ease="out")),
            (1.22, dict(x=470, y=1258, lean=-3, head=4, mouth="grin", hs=1.0, hRx=470, hRy=1300,
                        hRb=-1.0, _ease="out")),
            (1.55, dict(expr="rage", brow=1.0, mouth="frown", hRx=600, hRy=1440, hRb=1.4,
                        x=452, y=1274, lean=-8, _ease="in")),
            (1.78, dict(hRx=616, hRy=1452, x=444, y=1282, lean=-10)),
            (2.10, dict(x=470, y=1256, lean=0, head=0, mouth="open", expr="rage", hRx=560, hRy=1180,
                        hRb=-1.2, hLx=500, hLy=1230, hLb=-1.0, _ease="out")),
            (2.45, dict(hRx=520, hRy=1130, hLx=470, hLy=1180, lean=-8, head=-6)),
            (2.95, dict(hRx=690, hRy=1420, hLx=620, hLy=1390, lean=14, head=9, expr="rage",
                        mouth="open", fLx=418, fLy=1502, fRx=520, fRy=1510, _ease="in")),
            (3.12, dict(hRx=600, hRy=1250, lean=-4, head=2)),
            (3.60, dict(hRx=250, hRy=1180, hLx=330, hLy=1210, lean=-14, head=-8, fLx=440, fLy=1500,
                        fRx=520, fRy=1508, _ease="in")),
            (4.00, dict(hRx=140, hRy=1010, lean=-18, head=-10, _ease="out")),
            (4.50, dict(hRx=560, hRy=1470, lean=20, head=12, mouth="open",
                        fLx=400, fLy=1500, fRx=540, fRy=1512, _ease="in")),
            (4.72, dict(hRx=520, hRy=1290, lean=2, head=0, _ease="out")),
            (5.05, dict(x=440, y=1272, lean=-6, head=3, mouth="open", hRx=470, hRy=1300,
                        hLx=400, hLy=1320, _ease="out")),
            (5.35, dict(x=452, y=1266, lean=-2, head=0, hRx=520, hRy=1150, hLx=480, hLy=1200)),
            (6.30, dict(x=456, y=1262, lean=-2, hRx=540, hRy=1130, hLx=495, hLy=1185)),
            (6.75, dict(hRx=560, hRy=1090, lean=-6, head=-4)),
            (6.98, dict(hRx=640, hRy=1420, lean=16, head=10, mouth="open", _ease="in")),
            (7.35, dict(x=470, y=1452, lean=-10, rot=6, hRx=600, hRy=1500, hLx=380, hLy=1490,
                        fLx=610, fLy=1524, fRx=560, fRy=1560, expr="spiral", mouth="open",
                        _ease="in")),
            (7.80, dict(x=468, y=1462, lean=-14, rot=4, hRx=590, hRy=1512, hLx=370, hLy=1500,
                        expr="spiral", mouth="open", brow=0.3)),
        ])
        self.dmg = {
            "dresser": [(2.93, 0.0, 1.0)], "lamp": [(2.93, 0.0, 1.0)],
            "picture": [(3.60, 0.0, 1.0)], "mirror": [(3.60, 0.0, 1.0)], "chair": [(3.62, 0.0, 1.0)],
            "bed": [(4.50, 0.0, 1.0)], "plant": [(3.62, 0.0, 0.7)],
        }
        self.swat = [(1.30, 268.0), (1.75, 196.0), (2.05, 150.0), (2.45, -128.0), (2.95, 44.0),
                     (3.12, -104.0), (3.60, 6.0), (4.00, -96.0), (4.50, 78.0), (4.80, 70.0),
                     (5.30, 26.0), (6.30, 18.0), (6.75, -46.0), (6.98, 74.0), (7.80, 128.0)]
        self.swat_s = [(1.30, 0.42), (1.80, 0.95), (2.05, 2.15), (2.25, 2.30), (2.55, 2.42), (7.0, 2.42)]
        self.buzz = [(0.90, 426, 900), (1.00, 620, 760), (1.15, 742, 596), (1.55, 806, 470),
                     (2.30, 700, 560), (2.93, 330, 470), (3.10, 250, 610), (3.55, 250, 700),
                     (3.62, 848, 640), (4.05, 880, 540), (4.50, 520, 430), (4.75, 430, 400),
                     (5.40, 470, 430), (6.20, 480, 436), (6.60, 470, 424), (7.02, 150, 320),
                     (7.80, 60, 210)]
        self.dust = []

    def dmg_at(self, t, k, default=0.0):
        for (t0, a, b) in self.dmg.get(k, []):
            if t >= t0:
                return lerp(a, b, ease(seg(t, t0, t0 + 0.26)))
        return default

    def render(self, t):
        ev = [(2.98, 22, 0.09), (3.62, 20, 0.09), (4.50, 26, 0.11), (7.05, 12, 0.07)]
        cam = cam_at(t, [(0.00, 1.42, 368, 1300), (0.40, 1.06, 440, 1330), (0.85, 0.98, 462, 1340),
                         (1.30, 0.92, 505, 1364), (2.00, 0.88, 525, 1376), (2.60, 0.86, 545, 1390),
                         (4.80, 0.90, 525, 1372), (5.40, 0.98, 485, 1356), (6.30, 1.08, 475, 1342),
                         (6.90, 1.20, 475, 1330), (7.30, 0.96, 525, 1382), (7.80, 0.90, 600, 1410)],
                        impacts(t, ev))
        f = Frame(cam)
        pen, spen, gpen = f.pen, f.spen, f.gpen

        dmg = {k: self.dmg_at(t, k) for k in ("bed", "dresser", "lamp", "mirror", "chair", "plant",
                                              "picture")}
        fire = clamp(ease(seg(t, 5.6, 7.8)) * 0.5)
        props.room_back(pen, spen, gpen, t, dmg, 0.0, fire=fire)
        if dmg["chair"] > 0.45 or dmg["dresser"] > 0.5:
            pass
        props.debris(pen, spen, gpen, seed=9, n=int(18 * self.dmg_at(t, "mirror") +
                                                     14 * self.dmg_at(t, "dresser") +
                                                     20 * self.dmg_at(t, "bed")), t=t,
                     spread=(60, 1040))

        pose = self.pose.sample(t)
        pose["_t"] = t
        # panting after the rampage
        pant = ease(seg(t, 4.9, 5.4)) * (1 - ease(seg(t, 6.5, 7.0)))
        pose["y"] += math.sin(t * 11.0) * 3.4 * pant
        pose["lean"] += math.sin(t * 11.0 + 1.0) * 1.6 * pant
        RIG.draw(pen, pose, glow_pen=gpen)
        props.bed_front(pen, spen, gpen, self.dmg_at(t, "bed"), t)

        # --- the self-slap cheek mark ----------------------------------------
        slap = 1 - ease(seg(t, 1.05, 2.30))
        if slap > 0.02:
            cp = RIG.face_pt(pose, (0.58, 0.30))
            pen.circle(cp, 21, fill=col(VIVID_RED, int(105 * slap)))
            for i in range(3):
                a = math.radians(-70 + i * 45)
                pen.line([(cp[0] + math.cos(a) * 16, cp[1] + math.sin(a) * 16),
                          (cp[0] + math.cos(a) * 30, cp[1] + math.sin(a) * 30)],
                         col(VIVID_RED, int(140 * slap)), 4)
        if 0.98 < t < 1.25:
            u = seg(t, 0.98, 1.25)
            star_flash(pen, RIG.face_pt(pose, (0.55, 0.5)), 60 * (0.6 + u), (255, 226, 120), 7, u * 1.5)
            for i in range(5):
                a = -0.4 + i * 0.5
                pen.line([(RIG.face_pt(pose, (0.6, 0.4))[0], RIG.face_pt(pose, (0.6, 0.4))[1]),
                          (RIG.face_pt(pose, (0.6, 0.4))[0] + math.cos(a) * 130 * (1 + u),
                           RIG.face_pt(pose, (0.6, 0.4))[1] + math.sin(a) * 130 * (1 + u))],
                         (255, 240, 190), 6, alpha=int(200 * (1 - u)))
            spen.circle(RIG.face_pt(pose, (0.5, 0.5)), 90 * (0.5 + u), fill=col((255, 170, 90), 90))

        # dizzy stars while reeling
        if 1.0 < t < 1.35:
            hp = RIG.face_pt(pose, (0.0, -1.3))
            for i in range(3):
                a = t * 9 + i * 2.1
                pen.star((hp[0] + math.cos(a) * 66, hp[1] + math.sin(a) * 24), 13, (255, 214, 110))

        # --- giant flyswatter --------------------------------------------------
        scale = track(t, self.swat_s, ease_elastic)
        ang = track(t, self.swat, ease)
        hx, hy = RIG.hand_pos(pose, "R")
        if 0.6 < t < 1.85:            # the hand yanks it out from under the bed
            spen.circle((hx, hy), 40, fill=col((255, 255, 255), 80))
        if t > 1.25:
            # swing smear strength: peaks on every impact swing
            swatt = 0.0
            for (t0, amp, tau) in [(2.95, 1.0, 0.11), (3.60, 1.0, 0.11), (4.50, 1.0, 0.11),
                                   (6.98, 0.8, 0.11)]:
                if t >= t0:
                    swatt = max(swatt, amp * math.exp(-(t - t0) / tau))
            swatt += 0.55 * max(0.0, math.cos(math.radians(ang))) ** 3
            props.flyswatter(pen, spen, (hx, hy), ang, max(0.3, scale), smear=min(1.0, swatt))
            blade = (hx + math.cos(math.radians(ang)) * 288 * scale,
                     hy + math.sin(math.radians(ang)) * 288 * scale)

        # --- mosquito ---------------------------------------------------------
        nose_w = RIG.nose(pose, 0.98)
        if t < 0.9:
            mw = nose_w
        else:
            bx, by = path(t, self.buzz)
            bworld = cam.inv(bx, by)
            mw = bworld
            if 4.6 < t < 6.4:      # rests on the swatter blade
                bl = (hx + math.cos(math.radians(ang)) * 288 * scale,
                      hy + math.sin(math.radians(ang)) * 288 * scale)
                u = ease(seg(t, 4.6, 5.0))
                mw = (lerp(bworld[0], bl[0] - 30 * scale, u), lerp(bworld[1], bl[1] - 40 * scale, u))
        size = 1.18
        wing = t * 52
        if t > 0.9 and t < 6.9:
            # kung-fu flourish: extra spin while dodging
            for (t0, dur) in ((2.93, 0.35), (3.62, 0.35), (4.50, 0.35)):
                if t0 < t < t0 + dur:
                    u = seg(t, t0, t0 + dur)
                    mw = (mw[0] + math.cos(u * math.tau) * 26, mw[1] - math.sin(u * math.pi) * 40)
        tilt = math.sin(t * 5.2) * 16
        fx.mosquito(pen, spen, gpen, mw, size=size, wing=wing, tilt=tilt)
        if t > 5.5 and t < 6.6:
            pass

        # --- impact bursts -----------------------------------------------------
        for (t0, origin, n, spd, sz, cl) in [
            (2.95, (905, 1210), 26, 300, (10, 30), (150, 130, 110)),
            (3.60, (520, 700), 22, 260, (8, 22), (170, 190, 205)),
            (4.50, (520, 1270), 34, 320, (12, 32), (238, 232, 222)),
        ]:
            if t0 <= t < t0 + 0.9:
                u = seg(t, t0, t0 + 0.9)
                rng = random.Random(int(t0 * 100))
                if t - t0 < 1 / 30:
                    self.dust += DUST.burst(n, origin, 40, spd, 0.85, tilt=190, gravity=420,
                                            size=sz, color=cl)
                if 5.6 <= t <= 6.5:
                    pass
        self.dust = DUST.step(self.dust, 1 / 30)
        DUST.draw_soft(spen, self.dust)
        DUST.draw_hard(pen, self.dust)

        # floating feathers after the bed explodes
        if t > 4.5:
            for i in range(14):
                rng = random.Random(i * 31)
                u = (t - 4.5) * 0.22 + rng.random()
                x = 200 + rng.random() * 620 + math.sin(u * 3 + i) * 40
                y = 1180 - (u % 1.0) * 240
                pen.ellipse((x, y), 16, 7, fill=(250, 248, 244), angle=u * 40)

        if t > 5.6:
            fx.smoke_column(spen, 905, 1210, t, height=520, width=140, density=18, seed=3,
                            color=(196, 188, 180), alpha=90)
        if t > 6.6:
            fx.sweat(pen, RIG.face_pt(pose, (-0.9, -1.1)), 0.7, (150, 200, 255))

        return f.finish(glow_radius=20 + 26 * ease(seg(t, 5.6, 7.8)), vignette=0.30)


# ============================================================ SHOT 3 =======
class Shot3:
    t0, t1 = 10.55, 19.48

    def __init__(self):
        self.pose = Anim(STAND, [
            (0.00, dict(x=468, y=1462, lean=-14, rot=4, expr="spiral", mouth="open", brow=0.3,
                        hRx=590, hRy=1512, hLx=370, hLy=1500, fLx=610, fLy=1524, fRx=560,
                        fRy=1560)),
            (0.55, dict(x=470, y=1400, lean=-8, rot=0, expr="rage", mouth="frown", brow=1.0,
                        hRx=520, hRy=1420, hLx=420, hLy=1440, fLx=430, fLy=1506, fRx=516,
                        fRy=1506, _ease="out")),
            (0.95, dict(x=470, y=1256, lean=0, head=0, expr="rage", brow=1.0, mouth="frown",
                        hRx=560, hRy=1330, hLx=420, hLy=1350, _ease="out")),
            (1.30, dict(hRx=430, hRy=1560, hLx=400, hLy=1290, lean=-24, head=14, expr="open",
                        mouth="o", _ease="in")),
            (1.75, dict(x=470, y=1256, lean=-6, head=-4, expr="rage", brow=1.0, mouth="frown",
                        hRx=520, hRy=1240, hLx=430, hLy=1260, _ease="out")),
            (2.05, dict(hRx=520, hRy=1190, hLx=470, hLy=1220, lean=-12, head=-8, x=450, y=1258)),
            (2.18, dict(hRx=560, hRy=1150, lean=-22, head=-12, x=420, y=1266, fLx=470, fLy=1506,
                        fRx=420, fRy=1512, mouth="open", _ease="in")),
            (2.55, dict(x=452, y=1262, lean=6, head=6, hRx=500, hRy=1200, hLx=430, hLy=1240,
                        _ease="out")),
            (3.30, dict(x=430, y=1268, lean=-16, head=-8, expr="rage", brow=1.0, mouth="grin",
                        hRx=470, hRy=1560, hLx=408, hLy=1300, _ease="in")),
            (3.75, dict(x=440, y=1260, lean=-4, head=0, hRx=500, hRy=1350, hLx=430, hLy=1360)),
            (4.30, dict(x=430, y=1258, lean=-10, head=-4, hRx=560, hRy=1300, hLx=470, hLy=1320,
                        _ease="out")),
            (4.90, dict(x=430, y=1240, lean=-16, head=-10, mouth="open", hRx=590, hRy=1270,
                        hLx=500, hLy=1290)),
            (5.60, dict(x=430, y=1256, lean=0, head=0, expr="rage", brow=1.0, mouth="o",
                        hRx=520, hRy=1340, hLx=430, hLy=1350, _ease="out")),
            (6.15, dict(x=436, y=1246, lean=-6, head=-4, mouth="open", hRx=560, hRy=1290,
                        hLx=470, hLy=1320)),
            (6.45, dict(x=440, y=1262, lean=4, head=-2, hRx=520, hRy=1330, hLx=440, hLy=1350,
                        mouth="open", _ease="out")),
            (7.10, dict(x=470, y=1300, lean=10, head=8, expr="wide", mouth="open",
                        hRx=470, hRy=1460, hLx=380, hLy=1460, fLx=430, fLy=1520, fRx=530,
                        fRy=1520, _ease="out")),
            (7.55, dict(x=520, y=1330, lean=22, head=14, expr="wide", mouth="open", hRx=560,
                        hRy=1500, hLx=420, hLy=1500, fLx=430, fLy=1540, fRx=560, fRy=1560,
                        _ease="in")),
            (7.95, dict(x=520, y=1370, lean=34, head=20, rot=24, expr="x", mouth="open", hRx=610,
                        hRy=1520, hLx=420, hLy=1530, fLx=450, fLy=1560, fRx=600, fRy=1600,
                        _ease="in")),
            (8.60, dict(x=520, y=1382, lean=36, head=22, rot=26, expr="x", mouth="open", hRx=620,
                        hRy=1530, hLx=430, hLy=1540, fLx=460, fLy=1570, fRx=610, fRy=1610)),
            (9.20, dict(x=520, y=1380, lean=34, head=20, rot=24, expr="x", mouth="open", hRx=620,
                        hRy=1530, hLx=430, hLy=1540, fLx=460, fLy=1570, fRx=610, fRy=1610)),
        ])
        self.buzz = [(0.80, 700, 620), (1.20, 760, 500), (1.70, 640, 380), (2.05, 420, 330),
                     (2.25, 300, 420), (2.60, 820, 420), (3.30, 300, 640), (3.80, 760, 700),
                     (4.40, 700, 300), (5.40, 300, 280), (6.30, 620, 300), (7.20, 700, 360)]
        self.dust = []

    def dmg_at(self, t, k):
        return 1.0 if t > 0.4 else 0.6

    def render(self, t):
        ev = [(2.18, 30, 0.13), (3.40, 12, 0.10), (7.85, 26, 0.20), (8.05, 34, 0.30)]
        cam = cam_at(t, [(0.00, 0.94, 520, 1370), (0.60, 1.02, 470, 1330), (1.40, 1.00, 470, 1320),
                         (2.20, 0.92, 470, 1320), (3.00, 0.98, 500, 1320), (4.00, 1.06, 520, 1310),
                         (5.00, 1.00, 480, 1300), (6.00, 1.16, 470, 1260), (6.60, 1.30, 500, 1210),
                         (7.20, 1.05, 520, 1120), (7.90, 0.78, 520, 1000), (8.60, 0.72, 520, 900),
                         (9.20, 0.70, 520, 880)], impacts(t, ev))
        f = Frame(cam)
        pen, spen, gpen = f.pen, f.spen, f.gpen

        burning = ease(seg(t, 3.4, 5.2))
        destroyed = ease(seg(t, 7.9, 8.7))
        dmg = {k: 1.0 for k in ("bed", "dresser", "lamp", "mirror", "chair", "plant", "picture")}
        if destroyed < 0.98:
            props.room_back(pen, spen, gpen, t, dmg, destroyed, fire=burning * 0.7)
            props.debris(pen, spen, gpen, seed=12, n=40, t=t, spread=(40, 1040))
        if burning > 0.05:
            for i, (fx_, fy_) in enumerate([(300, 1300), (700, 1330), (520, 1360), (900, 1300)]):
                n = int(9 * burning)
                for j in range(n):
                    rng = random.Random(i * 7 + j)
                    a = rng.uniform(0, math.tau)
                    r = rng.uniform(20, 120)
                    col_ = (255, 150 + rng.randint(0, 60), 60) if rng.random() < 0.5 else VIVID_RED
                    pen.circle((fx_ + math.cos(a) * r * 1.6, fy_ + math.sin(a) * r * 0.5),
                               rng.uniform(8, 26), fill=col_)

        pose = self.pose.sample(t)
        pose["_t"] = t
        RIG.draw(pen, pose, glow_pen=gpen)

        # --- crate + held weapons ---------------------------------------------
        hxr, hyr = RIG.hand_pos(pose, "R")
        hxl, hyl = RIG.hand_pos(pose, "L")
        # crate in the foreground, lid flips open
        props.crate(pen, (250, 1700), 0.9, open_=ease_out_quint(seg(t, 0.9, 1.5)))
        if 1.35 < t < 2.55:      # bazooka
            u = ease_out(seg(t, 1.35, 1.75))
            prop_u = u
            pen.poly([(250, 1700 - 60 * (1 - prop_u)), (330, 1700), (250, 1760), (170, 1700)],
                     fill=(40, 36, 34), alpha=None)
            bx = lerp(250, (hxr + hxl) / 2, prop_u)
            by = lerp(1660, (hyr + hyl) / 2 + 10, prop_u)
            ang = lerp(-90, -22 + math.sin(t * 2) * 3, prop_u)
            fire = 1.0 if 2.14 <= t < 2.34 else 0.0
            props.bazooka(pen, spen, gpen, (bx, by), ang, 1.0, fire)
            if 2.14 <= t < 2.22:
                u2 = seg(t, 2.14, 2.22)
                pen.circle((bx + math.cos(math.radians(ang)) * 380, by + math.sin(math.radians(ang)) * 380),
                           40 * (1 - u2), fill=(255, 240, 180))
        if 2.30 < t < 3.35:      # the bazooka is flung away
            u = seg(t, 2.30, 3.35)
            bx = lerp(430, -160, ease_in(u))
            by = lerp(1230, 900, ease_out(u)) + math.sin(u * 9) * 30
            props.bazooka(pen, spen, gpen, (bx, by), -30 + u * 720, 1.0, 0.0)
        if 3.35 < t < 5.05:      # flamethrower
            u = ease_out(seg(t, 3.35, 3.7))
            bx = lerp(250, (hxr + hxl) / 2 + 40, u)
            by = lerp(1650, (hyr + hyl) / 2, u)
            ang = lerp(-80, -14, u) + math.sin(t * 3.1) * 8
            firing = 1.0 if 3.72 <= t < 4.85 else 0.0
            props.flamethrower(pen, spen, gpen, (bx, by), ang, 1.0, firing, t)
            if firing:
                nz = (bx + math.cos(math.radians(ang)) * 200, by + math.sin(math.radians(ang)) * 200)
                fx.fire_cone(pen, spen, gpen, nz, ang, 900, 120, seed=5, t=t)
                spen.circle(nz, 200, fill=col((255, 140, 50), 60))
        if 4.90 < t < 7.9:       # the emergency console rises out of the crate
            u = ease_out(seg(t, 4.90, 5.35))
            px = lerp(300, 725, u)
            py = lerp(1800, 1330, u) - math.sin(min(1.0, u) * math.pi) * 70
            cover = ease_in(seg(t, 5.55, 5.95))
            press = ease_out(seg(t, 6.30, 6.42))
            charge = ease(seg(t, 6.00, 6.32))
            props.button_panel(pen, spen, gpen, (px, py), 0.56, cover, press, charge, t)
            if t > 6.30:
                spen.circle((px, py - 18), 110 * ease(seg(t, 6.30, 6.7)), fill=col((255, 80, 60), 120))
        if t > 6.55:            # the button-press hand reaches the console
            pass

        # --- mosquito ----------------------------------------------------------
        bworld = cam.inv(*path(t, self.buzz)) if t < 7.4 else cam.inv(700, 400)
        size = 1.12
        fx.mosquito(pen, spen, gpen, bworld, size=size, wing=t * 60,
                    tilt=math.sin(t * 6) * 20)

        # --- orbital laser ------------------------------------------------------
        lock = ease(seg(t, 6.55, 7.05))
        beam = ease(seg(t, 7.05, 7.35))
        if lock > 0.02 and beam < 0.02:
            top = cam.inv(520, -40)
            ground = cam.inv(520 + math.sin(t * 30) * 6, 1400)
            pen.line([top, ground], col(WARM_GOLD, int(200 * lock)), 4)
            pen.circle(ground, 26 * lock, fill=col((255, 230, 160), int(220 * lock)))
            for i in range(3):
                pen.circle(ground, (30 + i * 22) * lock, outline=col(WARM_GOLD, int(180 * lock * (1 - i / 3))),
                           width=5)
            spen.circle((520, 1500), 200 * lock, fill=col((255, 200, 120), int(70 * lock)))
        if beam > 0.02:
            top_w = cam.inv(520, -120)
            hit_w = cam.inv(520, 1420)
            fx.laser_beam(pen, spen, gpen, 520, top_w[1], hit_w[1], 120 * beam, t)
            for i in range(4):
                rr = 120 + i * 90
                pen.ellipse((520, 1420 + i * 30), rr * 1.6 * beam, rr * 0.34 * beam,
                            outline=col((255, 210, 150), int(150 * beam)), width=8)
            if t > 7.30:
                u = seg(t, 7.30, 7.95)
                for i in range(3):
                    a = i * 2.1
                    spen.circle((520 + math.cos(a) * 200 * u, 1300 + math.sin(a) * 60 * u),
                                220 * u, fill=col((255, 200, 140), int(50 * (1 - u))))

        # --- explosion ----------------------------------------------------------
        flash = 0.0
        if t > 7.90:
            u = seg(t, 7.90, 8.35)
            fx.blast(pen, spen, gpen, cam.inv(520, 1320), 1500, u, color=(255, 176, 70))
            flash = 1 - ease(seg(t, 7.90, 8.28))
        if t > 7.85:
            rng = random.Random(int(t * 30))
            u = seg(t, 7.85, 9.2)
            for i in range(30):
                rr = random.Random(i * 11)
                ang = rr.uniform(-2.6, -0.5)
                dist = (200 + rr.random() * 900) * ease_out(u)
                x = 520 + math.cos(ang) * dist
                y = 1320 + math.sin(ang) * dist * 0.7
                s = rr.uniform(16, 70) * (1 - u * 0.3)
                a = rr.uniform(0, 6.28)
                pen.poly([rot_pt((x + dx * s, y + dy * s), (x, y), a * 40) for dx, dy in
                          ((-1, -0.3), (1, -0.4), (0.9, 0.5), (-0.8, 0.4))], fill=(58, 46, 44))
            fx.smoke_column(spen, 520, 1500, t, height=1500, width=300, density=30, seed=8,
                            color=(168, 158, 152), drift=0.1, spread=1.6, alpha=140)
            for i in range(16):
                rr = random.Random(i * 5)
                spen.circle((520 + rr.uniform(-420, 420), 1520 - rr.uniform(0, 340)), rr.uniform(60, 150),
                            fill=col((120, 110, 106), 90))

        # screen shake belongs to the explosion frames
        return f.finish(glow_radius=26, flash=(255, 250, 240) if flash > 0.02 else None,
                        flash_a=flash, vignette=0.32 + 0.2 * (1 - flash))


# ============================================================ SHOT 4 =======
class Shot4:
    t0, t1 = 19.36, 25.00

    def __init__(self):
        self.pose = Anim(STAND, [
            (0.00, dict(x=520, y=1440, lean=2, head=0, expr="closed", mouth="frown", brow=0.2,
                        hRx=470, hRy=1560, hLx=570, hLy=1560, fLx=470, fLy=1700, fRx=570,
                        fRy=1700, lw=0.9)),
            (0.45, dict(x=520, y=1436, lean=-4, expr="open", mouth="flat", hRx=470, hRy=1560,
                        hLx=570, hLy=1560, hs=1.0)),
            (0.75, dict(y=1450, lean=-10, expr="open", mouth="frown", head=-4, hRx=452, hRy=1530,
                        hLx=590, hLy=1530, _ease="out")),
            (1.10, dict(x=522, y=1424, lean=-6, head=-6, expr="determined", mouth="flat",
                        hRx=460, hRy=1540, hLx=580, hLy=1540, _ease="out")),
            (1.60, dict(x=520, y=1430, lean=-9, head=-3, expr="proud", mouth="smile", brow=0.3,
                        hRx=440, hRy=1520, hLx=600, hLy=1520, fLx=468, fLy=1700, fRx=574,
                        fRy=1700)),
            (2.60, dict(x=520, y=1428, lean=-9, head=-3, expr="proud", mouth="smile", hRx=436,
                        hRy=1516, hLx=604, hLy=1516)),
            (3.30, dict(x=520, y=1426, lean=-10, head=-2, expr="proud", mouth="smile", hs=1.02)),
            (3.62, dict(expr="open", mouth="o", brow=0.2, hs=1.0, _ease="hold")),
            (4.45, dict(expr="wide", mouth="open", brow=0.5, hRx=420, hRy=1490, hLx=620, hLy=1490)),
            (4.85, dict(expr="x", mouth="open", brow=0.9, lean=-16, head=-8, x=506, y=1436)),
            (5.25, dict(x=430, y=1508, lean=0, rot=-84, head=0, expr="x", mouth="open",
                        hRx=380, hRy=1450, hLx=300, hLy=1520, fLx=560, fLy=1700, fRx=660,
                        fRy=1690, _ease="in")),
            (5.35, dict(x=430, y=1520, lean=0, rot=-86, expr="x", mouth="open", hs=1.03)),
            (5.70, dict(x=430, y=1516, rot=-86, expr="x", mouth="open", hs=1.0)),
        ])
        self.dust = []

    def render(self, t):
        ev = [(0.00, 10, 0.35), (5.22, 20, 0.16)]
        cam = cam_at(t, [(0.00, 0.80, 520, 1500), (0.70, 0.92, 520, 1470), (1.60, 1.05, 520, 1440),
                         (2.60, 1.16, 520, 1420), (3.30, 1.34, 512, 1400), (3.90, 1.70, 505, 1380),
                         (4.40, 2.05, 505, 1370), (4.90, 1.60, 500, 1420), (5.30, 1.05, 520, 1480),
                         (5.70, 0.98, 520, 1500)], impacts(t, ev))
        f = Frame(cam)
        pen, spen, gpen = f.pen, f.spen, f.gpen

        props.crater_environment(pen, spen, gpen, t, ash=1.0)
        props.debris(pen, spen, gpen, seed=31, n=34, t=t, spread=(0, 1080))
        for i in range(4):
            fx.smoke_column(spen, 180 + i * 240, 1640, t + i, height=760, width=180, density=12,
                            seed=20 + i, color=(150, 142, 138), drift=0.06 * (1 if i % 2 else -1),
                            alpha=80)
        # molten embers on the crater rim
        for i in range(30):
            rng = random.Random(i * 17)
            x = 90 + rng.random() * 900
            y = 1580 + rng.random() * 200
            u = 0.5 + 0.5 * math.sin(t * (1.4 + rng.random()) + i)
            pen.circle((x, y), 3 + u * 4, fill=(255, int(120 + 90 * u), 60))

        pose = self.pose.sample(t)
        pose["_t"] = t
        breath = ease(seg(t, 0.4, 1.4)) * (1 - ease(seg(t, 4.6, 5.0)))
        pose["y"] += math.sin(t * 9.4) * 4.6 * breath
        pose["hs"] *= 1 + 0.012 * math.sin(t * 9.4) * breath
        RIG.draw(pen, pose, glow_pen=gpen)

        # --- the mosquito returns to the lens ---------------------------------
        if t < 3.30:
            mw = cam.inv(760, 520)
            fx.mosquito(pen, spen, gpen, mw, size=1.12, wing=t * 55, tilt=math.sin(t * 4) * 14)
        else:
            u = ease_out_quint(seg(t, 3.30, 4.15))
            mw = cam.inv(lerp(760, 384, u), lerp(520, 596, u) - math.sin(u * math.pi) * 70)
            size = lerp(1.12, 5.3, ease(seg(t, 3.3, 4.2)))
            hero = t > 3.9
            fx.mosquito(pen, spen, gpen, mw, size=size, wing=t * 90, tilt=math.sin(t * 7) * 22,
                        hero=hero, aura=ease(seg(t, 3.7, 4.3)))
            if t > 3.75:
                spen.circle((384, 606), 210 * ease(seg(t, 3.75, 4.3)), fill=col((255, 250, 235), 40))

        # reaction shots
        if 3.55 < t < 4.5:
            hp = RIG.face_pt(pose, (0.0, -1.35))
            for i in range(3):
                a = -1.0 + i * 0.35
                L = 70 * ease(seg(t, 3.55 + i * 0.06, 3.75 + i * 0.06))
                pen.line([(hp[0] + math.cos(a) * 60, hp[1] + math.sin(a) * 60),
                          (hp[0] + math.cos(a) * (60 + L), hp[1] + math.sin(a) * (60 + L))],
                         (255, 255, 255), 8)
        if t > 5.18 and t < 5.45 and len(self.dust) < 40:
            self.dust += DUST.burst(24, (470, 1640), 60, 260, 0.8, tilt=200, gravity=380,
                                    size=(10, 30), color=(150, 138, 130))
        self.dust = DUST.step(self.dust, 1 / 30)
        DUST.draw_soft(spen, self.dust)
        DUST.draw_hard(pen, self.dust)

        fade = ease(seg(t, 5.35, 5.70))
        return f.finish(glow_radius=24, flash=(255, 250, 235) if t > 4.0 else None,
                        flash_a=0.10 * ease(seg(t, 4.0, 4.4)) * (1 - ease(seg(t, 4.6, 5.0))),
                        tint=(120, 100, 96), tint_a=0.10, vignette=0.34, fade=fade)


SHOTS = [Shot1(), Shot2(), Shot3(), Shot4()]


X_OVER = 0.12


def render(t):
    """composite the timeline at absolute time t (short dissolves = fast cuts)."""
    import numpy as np
    acc = None
    wsum = 0.0
    for i, sh in enumerate(SHOTS):
        if t < sh.t0 - 1e-6 or t > sh.t1 + 1e-6:
            continue
        a = 1.0
        if i > 0 and t < sh.t0 + X_OVER:
            a = ease((t - sh.t0) / X_OVER)
        if t > sh.t1 - X_OVER:
            a = min(a, 1.0 - ease((t - (sh.t1 - X_OVER)) / X_OVER))
        if a <= 0.01:
            continue
        arr = np.asarray(sh.render(t - sh.t0), dtype=np.float32)
        acc = arr * a if acc is None else acc + arr * a
        wsum += a
    if acc is None:
        return Image.new("RGB", (W, H), (0, 0, 0))
    return Image.fromarray(np.clip(acc / wsum, 0, 255).astype(np.uint8))


SYNOPSIS = """
 00.00-03.10  THE HOOK        bedroom, night. A stickman sleeps; a tiny black dot buzzes in,
                              lands on his nose, and his eyes snap open glowing red.
 03.10-10.67  THE ESCALATION  he slaps himself, misses, and comes back with a giant red
                              flyswatter. Every swing levels furniture; the mosquito dodges
                              like a kung-fu master and even perches on the paddle.
 10.67-19.48  THE CLIMAX      bazooka, then flamethrower, then the emergency red button
                              brings a giant orbital laser down the frame. The house is gone.
 19.48-25.00  THE PUNCHLINE   smoking crater, proud breathing… and the mosquito flies straight
                              back onto the camera lens. He faints.
"""


def keyframes(times=(0.4, 2.6, 4.5, 7.5, 11.0, 14.6, 17.8, 20.6, 22.6, 24.2), size=(300, 533)):
    from PIL import Image as _I
    return [(t, render(t).resize(size, _I.LANCZOS)) for t in times]
