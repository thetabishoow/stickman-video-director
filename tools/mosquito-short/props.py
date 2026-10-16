"""props — the Style 4 bedroom, its progressive destruction, and the weapons."""
from __future__ import annotations

import math
import random

from sticklib import mix

from sticklib import (INK, PAPER, VIVID_RED, WARM_GOLD, ELECTRIC_BLUE, col, clamp, ease,
                      ease_out, lerp, pulse, rot_pt)

WOOD = (150, 101, 66)
WOOD_D = (112, 74, 48)
CREAM = (250, 245, 236)
NIGHT = (28, 38, 74)
MOON = (232, 236, 210)
METAL = (86, 92, 104)
METAL_D = (60, 64, 74)
OLIVE = (92, 104, 74)
RUG = (186, 158, 150)
WALL = (76, 84, 116)
WALL_D = (52, 58, 86)
FLOOR = (132, 100, 76)
FLOOR_D = (104, 76, 58)
SKY_HI = (30, 36, 66)
SKY_LO = (96, 74, 76)
ASHY = (116, 100, 92)

# room anchors (world space, 1080x1920) — side view of the bedroom
FLOOR_Y = 1520
BED = dict(x0=118, x1=800, mat_y0=1200, mat_y1=1330, base_y=1330, base_b=1462)
HEAD_X, HEAD_Y = 238, 1225          # sleeping head centre on the pillow
STAND = (470, 1256)                 # standing hip position on the floor


# ---------------------------------------------------------------- room ------
def window(pen, spen, gpen, t, lit=0.0, shake=0.0):
    x0, y0, x1, y1 = 660, 240, 1000, 640
    pen.rrect((x0 - 16, y0 - 16, x1 + 16, y1 + 16), 26, fill=(120, 104, 96), outline=INK, width=9)
    pen.rrect((x0, y0, x1, y1), 12, fill=NIGHT)
    # moon + stars
    gpen.circle((x0 + 92, y0 + 108), 74, fill=(70, 78, 120))
    pen.circle((x0 + 92, y0 + 96), 44, fill=MOON)
    pen.circle((x0 + 112, y0 + 84), 38, fill=NIGHT)
    rng = random.Random(5)
    for i in range(14):
        sx = rng.uniform(x0 + 24, x1 - 24)
        sy = rng.uniform(y0 + 20, y1 - 30)
        r = rng.uniform(2.0, 4.0)
        spen.circle((sx, sy), r * 2.4, fill=col((220, 228, 255), 90))
        pen.circle((sx, sy), r, fill=(236, 242, 255))
    # frame mullions
    pen.line([((x0 + x1) / 2, y0), ((x0 + x1) / 2, y1)], (120, 104, 96), 14)
    pen.line([(x0, (y0 + y1) / 2), (x1, (y0 + y1) / 2)], (120, 104, 96), 14)
    if lit > 0:      # outside firelight / explosion glow
        spen.rrect((x0 - 16, y0 - 16, x1 + 16, y1 + 16), 26, fill=col((255, 150, 60), int(120 * lit)))


def wall_lamp(pen, spen, gpen, state=0.0):
    """Bedside table lamp standing on the dresser."""
    x, y = 940, 1196
    if state < 0.6:
        # warm glow pool on wall behind
        for i in range(5, 0, -1):
            gpen.circle((x, y - 40), 120 * i / 5 + 60, fill=(46, 30, 10))
        gpen.circle((x, y - 60), 150, fill=(120, 78, 26))
    tx = x - state * 268
    ty = y + state * 252
    pen.line([(tx, ty), (tx, ty - 52)], INK, 9)
    pen.ellipse((tx, ty - 8), 46, 14, fill=WOOD, outline=INK, width=8)
    if state < 0.6:
        pen.poly([(tx - 54, ty - 60), (tx + 54, ty - 60), (tx + 38, ty - 132), (tx - 38, ty - 132)],
                 fill=(255, 224, 168), outline=INK, width=8)
        spen.circle((tx, ty - 90), 62, fill=col((255, 214, 140), 120))
    else:
        pen.poly([(tx - 58, ty - 58), (tx + 40, ty - 66), (tx + 30, ty - 128), (tx - 44, ty - 124)],
                 fill=(224, 206, 176), outline=INK, width=8)
        pen.line([(tx - 20, ty - 120), (tx - 30, ty - 70)], INK, 6)


def dresser(pen, spen, gpen, d=0.0, state=0.0):
    x0, x1, ty, by = 850, 1040, 1210, 1450
    if state < 0.5:
        pen.rrect((x0, ty, x1, by), 14, fill=WOOD, outline=INK, width=10)
        for i, dy in enumerate((ty + 18, ty + 92)):
            out = d * 46
            pen.rrect((x0 + 10, dy, x1 - 10, dy + 60 + out * 0.2), 8, fill=(238, 226, 208), outline=INK,
                      width=8)
            pen.circle((x0 + 46 + out, dy + 30), 7, fill=INK)
            pen.circle((x1 - 40 + out, dy + 30), 7, fill=INK)
        pen.rrect((x0 - 8, ty - 14, x1 + 8, ty + 8), 8, fill=WOOD_D, outline=INK, width=8)
        if d > 0.15:
            pen.line([(x0 + 30, ty + 20), (x1 - 40, by - 90)], INK, 7)
            pen.line([(x1 - 30, ty + 40), (x0 + 40, by - 60)], INK, 7)
    else:
        pen.rrect((x0 - 10, by - 74, x1 + 200, by - 20), 12, fill=WOOD, outline=INK, width=10)
        pen.rrect((x0 + 60, by - 26, x0 + 250, by + 8), 8, fill=(238, 226, 208), outline=INK, width=8)
        pen.line([(x0 + 10, by - 20), (x0 + 140, by + 30)], INK, 7)


def mirror(pen, spen, gpen, d=0.0, state=0.0):
    x, y = 520, 700
    if state < 0.5:
        pen.rrect((x - 108, y - 190, x + 108, y + 190), 96, fill=(206, 196, 186), outline=INK, width=10)
        pen.rrect((x - 84, y - 166, x + 84, y + 166), 74, fill=(196, 214, 226), outline=(150, 166, 180),
                  width=6)
        pen.poly([(x - 70, y + 150), (x + 10, y - 150), (x + 44, y - 150), (x - 36, y + 150)],
                 fill=col((255, 255, 255), 120))
        if d > 0.0:
            for i in range(7):
                a = i * math.tau / 7 + 0.3
                pen.line([(x, y), (x + math.cos(a) * 150 * d, y + math.sin(a) * 180 * d)], INK, 6)
    else:
        pen.line([(x - 90, y - 170), (x - 60, y + 30)], INK, 9)
        pen.poly([(x - 80, y + 40), (x + 70, y - 30), (x + 30, y + 70)], fill=(150, 170, 186),
                 outline=INK, width=7)
        pen.poly([(x - 30, y - 60), (x + 60, y - 120), (x + 60, y - 10)], fill=(170, 190, 204),
                 outline=INK, width=7)


def picture(pen, d=0.0, state=0.0):
    x, y = 270, 850
    a = d * 14
    p = [rot_pt((x + dx, y + dy), (x, y - 150), a) for dx, dy in
         ((-96, -128), (96, -128), (96, 128), (-96, 128))]
    pen.poly(p, fill=(226, 208, 178), outline=INK, width=10)
    if state < 0.5:
        pen.poly([rot_pt((x - 70, y + 90), (x, y - 150), a), rot_pt((x + 70, y + 90), (x, y - 150), a),
                  rot_pt((x + 20, y - 40), (x, y - 150), a), rot_pt((x - 50, y - 40), (x, y - 150), a)],
                 fill=(160, 190, 150))
        pen.circle(rot_pt((x + 44, y - 66), (x, y - 150), a), 20, fill=WARM_GOLD)
        if d > 0.3:
            pen.line([rot_pt((x - 40, y - 100), (x, y - 150), a),
                      rot_pt((x + 40, y + 80), (x, y - 150), a)], INK, 6)


def chair(pen, d=0.0, state=0.0):
    x, y = 250, 1620
    if state < 0.5:
        pen.line([(x - 46, y - 10), (x, y - 96), (x + 46, y - 10)], INK, 11)
        pen.line([(x, y - 96), (x, y - 6)], INK, 11)
        pen.line([(x - 60, y + 6), (x + 60, y + 6)], INK, 11)
        if d < 0.6:
            pen.rrect((x - 62, y - 96, x + 62, y - 34), 12, fill=WOOD, outline=INK, width=9)
            for sx in (-1, 1):
                pen.line([(x + sx * 52, y - 34), (x + sx * 58, y + 78)], INK, 11)
            pen.line([(x - 56, y + 40), (x + 56, y + 40)], WOOD_D, 9)
        else:
            pen.poly([(x - 70, y - 26), (x + 40, y + 18), (x + 20, y + 60), (x - 96, y + 20)],
                     fill=WOOD, outline=INK, width=9)
            pen.line([(x + 40, y + 60), (x + 96, y + 116)], INK, 11)
            pen.line([(x - 80, y + 60), (x - 110, y + 118)], INK, 11)


def plant(pen, spen, d=0.0, state=0.0):
    x, y = 940, 1500
    a = d * 78
    tx, ty = x + d * 30, y + d * 12
    pen.poly([rot_pt((tx - 52, ty - 60), (tx, ty + 40), a), rot_pt((tx + 52, ty - 60), (tx, ty + 40), a),
              rot_pt((tx + 38, ty + 40), (tx, ty + 40), a), rot_pt((tx - 38, ty + 40), (tx, ty + 40), a)],
             fill=(186, 120, 92), outline=INK, width=9)
    if state < 0.5:
        for i, (dx, dy, s) in enumerate(((-30, -110, 1.0), (0, -140, 1.15), (32, -104, 0.95))):
            ang = a + (i - 1) * 18
            pen.line([rot_pt((tx + dx, ty - 54), (tx, ty + 40), a),
                      rot_pt((tx + dx * 1.6, ty - 54 + dy * 0.6), (tx, ty + 40), a)], (74, 128, 76), 9)
            for k in range(3):
                t2 = 0.45 + k * 0.25
                px = lerp(tx + dx, tx + dx * 1.6, t2)
                py = lerp(ty - 54, ty - 54 + dy * 0.6, t2)
                pp = rot_pt((px, py), (tx, ty + 40), a)
                pen.ellipse(pp, 30 * s, 15 * s, fill=(96, 156, 92), outline=INK, width=6, angle=ang)
        if d > 0.4:
            for i in range(9):
                spen.circle((tx + (i % 3) * 34 - 30, ty + 46 + (i // 3) * 12), 16, fill=col((92, 68, 50), 150))
    else:
        pen.line([(tx - 90, ty + 30), (tx - 40, ty - 30)], INK, 9)


def bed_back(pen, spen, gpen, d=0.0):
    """frame, headboard, mattress and pillow — everything the sleeper rests on."""
    x0, x1 = BED["x0"], BED["x1"]
    by, bb = BED["base_y"], BED["base_b"]
    # base frame
    pen.rrect((x0, by, x1, bb), 20, fill=WOOD, outline=INK, width=10)
    pen.line([(x0 + 24, by + 44), (x1 - 24, by + 44)], WOOD_D, 8)
    for lx in (x0 + 30, x1 - 46):
        pen.line([(lx, bb - 6), (lx, bb + 40)], INK, 12)
    # headboard
    hx0, hx1, hy0, hy1 = x0 - 2, x0 + 92, 1030, by + 40
    pen.rrect((hx0, hy0, hx1, hy1), 24, fill=WOOD, outline=INK, width=11)
    pen.line([(hx0 + 20, hy0 + 40), (hx0 + 20, hy1 - 30)], WOOD_D, 8)
    # mattress
    mx0, mx1 = x0 + 34, x1 - 24
    pen.rrect((mx0, BED["mat_y0"], mx1, BED["mat_y1"]), 34, fill=CREAM, outline=INK, width=10)
    pen.line([(mx0 + 30, BED["mat_y1"] - 22), (mx1 - 30, BED["mat_y1"] - 22)], (226, 216, 202), 8)
    # pillow under the head
    pen.rrect((146, 1152, 428, 1292), 52, fill=(248, 246, 240), outline=INK, width=9)
    pen.line([(180, 1276), (400, 1276)], (222, 216, 206), 7)


def bed_front(pen, spen, gpen, d=0.0, t=0.0):
    """duvet over the legs + front lip of the pillow (drawn over the sleeper)."""
    if d < 0.5:
        pts = [(498, 1204), (600, 1196), (700, 1202), (782, 1214), (790, 1330), (700, 1342),
               (560, 1336), (500, 1318)]
        pen.poly(pts, fill=(198, 214, 232), outline=INK, width=10)
        for i in range(3):
            yy = 1240 + i * 30
            pen.line([(530, yy), (770, yy - 6)], (166, 186, 208), 7)
        pen.rrect((150, 1240, 432, 1300), 40, fill=(248, 246, 240), outline=INK, width=8)
    else:
        pen.poly([(470, 1300), (700, 1290), (800, 1370), (700, 1440), (520, 1430), (460, 1370)],
                 fill=(198, 214, 232), outline=INK, width=10)
        pen.poly([(150, 1268), (300, 1250), (430, 1300), (300, 1360)], fill=(248, 246, 240),
                 outline=INK, width=8)


def bed_rubble(pen, spen, gpen, t=0.0, seed=4):
    """collapsed bed state after the swatter smash"""
    pen.poly([(120, 1340), (420, 1318), (700, 1360), (800, 1440), (640, 1490), (240, 1478), (110, 1430)],
             fill=WOOD, outline=INK, width=10)
    pen.poly([(232, 1310), (476, 1296), (556, 1360), (404, 1402), (250, 1374)], fill=(226, 222, 214),
             outline=INK, width=9)
    pen.line([(300, 1300), (420, 1400)], INK, 7)
    pen.line([(430, 1300), (330, 1396)], INK, 7)
    pen.poly([(640, 1306), (768, 1316), (796, 1372), (664, 1382)], fill=(186, 204, 224),
             outline=INK, width=9)
    pen.line([(660, 1320), (786, 1364)], (160, 180, 202), 6)
    pen.line([(300, 1348), (520, 1332)], INK, 8)
    pen.poly([(140, 1352), (300, 1326), (430, 1378), (250, 1416)], fill=WOOD, outline=INK, width=9)
    pen.poly([(96, 1040), (200, 1064), (300, 1180), (168, 1204), (72, 1120)], fill=WOOD, outline=INK,
             width=9)
    pen.poly([(140, 1170), (330, 1240), (250, 1300), (120, 1230)], fill=(248, 246, 240), outline=INK, width=8)


def rug(pen):
    pen.ellipse((520, 1680), 470, 78, fill=RUG, outline=(168, 142, 140), width=8)


def wall_and_floor(pen, spen, gpen, burnt=0.0, moon=1.0, lamp=0.0, fire=0.0,
                   t=0.0, seed=6):
    """the bedroom shell: warm wall with a cool moon window pool and a wooden floor."""
    wc = mix(WALL, (44, 38, 40), burnt)
    pen.poly([(-460, -1000), (1540, -1000), (1540, FLOOR_Y + 30), (-460, FLOOR_Y + 30)], fill=wc)
    pen.poly([(0, FLOOR_Y - 190), (1080, FLOOR_Y - 190), (1080, FLOOR_Y + 30), (0, FLOOR_Y + 30)],
             fill=mix(wc, (22, 20, 28), 0.22))
    # faint wallpaper sheen near the lamp side
    spen.poly([(120, -200), (700, -200), (620, FLOOR_Y), (60, FLOOR_Y)],
              fill=col((255, 214, 150), int(26 * (1 - burnt)) + int(30 * fire)))
    if moon > 0.02:
        gpen.circle((836, 420), 400, fill=(18, 24, 52))
        for k, a in ((1.0, 10), (0.72, 9), (0.46, 8)):
            w0, w1 = (690, 1002) if k == 1.0 else ((760, 932) if k == 0.72 else (824, 868))
            spen.poly([(w0, 612), (w1, 612), (lerp(w0, w1, 1.35), FLOOR_Y + 26),
                       (lerp(w0, w1, -0.35), FLOOR_Y + 26)], fill=col(ELECTRIC_BLUE, int(a * moon)))
    # baseboard
    pen.poly([(-80, FLOOR_Y - 16), (1160, FLOOR_Y - 16), (1160, FLOOR_Y + 34), (-80, FLOOR_Y + 34)],
             fill=mix((66, 54, 50), (30, 26, 28), burnt))
    # floor
    fc = mix(FLOOR, (58, 48, 46), burnt)
    pen.poly([(-460, FLOOR_Y + 30), (1540, FLOOR_Y + 30), (1540, 2900), (-460, 2900)], fill=fc)
    fd = mix(FLOOR_D, (46, 38, 38), burnt)
    for i in range(8):
        yy = FLOOR_Y + 74 + i * 76
        pen.line([(-80, yy), (1160, yy)], col(fd, 150), 5)
    for i in range(-2, 9):
        xx = i * 172
        pen.line([(xx, FLOOR_Y + 42), (xx * 1.9 - 420, 2080)], col(fd, 110), 4)
    if fire > 0.02:
        for i in range(7):
            rng = random.Random(seed + i)
            spen.circle((rng.uniform(60, 1020), FLOOR_Y + rng.uniform(30, 300)), rng.uniform(80, 190),
                        fill=col((255, 150, 70), int(34 * fire)))


def room_back(pen, spen, gpen, t, dmg, state=0.0, fire=0.0):
    """wall + floor + everything behind the character."""
    wall_and_floor(pen, spen, gpen, burnt=state, moon=1.0 - state, fire=fire, t=t)
    rug(pen)
    if dmg.get("bed", 0.0) < 0.5:
        bed_back(pen, spen, gpen, dmg.get("bed", 0.0))
    else:
        bed_rubble(pen, spen, gpen, t)
    window(pen, spen, gpen, t, lit=fire)
    picture(pen, dmg["picture"], state)
    mirror(pen, spen, gpen, dmg["mirror"], state)
    chair(pen, dmg["chair"], state)
    dresser(pen, spen, gpen, dmg["dresser"], state)
    wall_lamp(pen, spen, gpen, dmg["lamp"])
    plant(pen, spen, dmg["plant"], state)


def debris(pen, spen, gpen, seed=9, n=42, t=0.0, spread=(40, 1040), life=None):
    rng = random.Random(seed)
    for i in range(n):
        x = rng.uniform(*spread)
        y = FLOOR_Y + rng.uniform(-20, 190)
        w = rng.uniform(14, 66)
        h = rng.uniform(8, 26)
        a = rng.uniform(-40, 40)
        kind = rng.random()
        if kind < 0.5:
            pen.poly([rot_pt((x + dx, y + dy), (x, y), a) for dx, dy in
                      ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2 * 0.7, h / 2), (-w / 2 * 0.8, h / 2))],
                     fill=WOOD if rng.random() < 0.6 else WOOD_D, outline=INK, width=6)
        elif kind < 0.78:
            pen.line([(x, y), (x + rng.uniform(-60, 60), y - rng.uniform(10, 40))], INK, 9)
        else:
            pen.ellipse((x, y), w * 0.36, h * 0.5, fill=(176, 196, 214), outline=INK, width=5, angle=a)


# ------------------------------------------------------------- weapons ------
def flyswatter(pen, spen, hand, ang, scale=1.0, holes=True, smear=0.0):
    """Giant red flyswatter: wooden handle, perforated red paddle, motion ghosts.
    hand = grip point, ang = direction the paddle points (degrees)."""
    sw = max(0.4, min(1.6, scale))

    def draw_at(deg, alpha=255, holes_alpha=255):
        a = math.radians(deg)
        ca, sa = math.cos(a), math.sin(a)

        def P(d, off=0.0):
            return (hand[0] + ca * d * scale - sa * off * scale, hand[1] + sa * d * scale + ca * off * scale)

        pen.line([P(-18), P(196)], col((104, 70, 46), alpha), 22 * sw)
        pen.line([P(-18), P(196)], col((78, 50, 32), alpha), 7 * sw)
        pen.rrect_rot(P(214), 52 * sw, 46 * sw, 13 * sw, deg + 90, fill=col((74, 64, 60), alpha),
                      outline=col(INK, alpha), width=8 * sw)
        pen.rrect_rot(P(288), 216 * scale, 240 * scale, 36 * scale, deg + 90,
                      fill=col(VIVID_RED, alpha), outline=col(INK, alpha), width=10 * sw)
        if holes:
            for r in range(4):
                for c in range(4):
                    d = 234 + c * 40
                    off = -84 + r * 56 + (c % 2) * 10
                    pen.circle(P(d, off), 14 * scale, fill=col((158, 24, 32), holes_alpha))
        pen.rrect_rot(P(214), 30 * scale, 214 * scale, 14 * scale, deg + 90, fill=col((196, 40, 44), alpha))
        pen.circle(P(14, 0), 12 * sw, fill=col((60, 54, 52), alpha))

    if smear > 0.02:
        for k in (2, 1):
            draw_at(ang - k * 15 * min(1.4, smear), alpha=int(70 * smear * (0.5 if k == 2 else 0.9)),
                    holes_alpha=int(40 * smear))
    draw_at(ang)


def bazooka(pen, spen, gpen, hand, ang, scale=1.0, fire=0.0):
    a = math.radians(ang)
    ca, sa = math.cos(a), math.sin(a)
    hx, hy = hand

    def P(d, off=0.0):
        return (hx + ca * d * scale - sa * off * scale, hy + sa * d * scale + ca * off * scale)

    def quad(d0, d1, o0, o1, fill, outline=None, w=9):
        pen.poly([P(d0, o0), P(d1, o0), P(d1, o1), P(d0, o1)], fill=fill, outline=outline, width=w * scale)

    quad(-30, 292, -34, 34, OLIVE, INK, 9)                      # main tube
    quad(292, 332, -52, 52, METAL_D, INK, 8)                    # muzzle flare
    quad(-64, -30, -24, 24, METAL, INK, 7)                      # back vent
    quad(56, 132, -16, 16, (196, 104, 60), INK, 7)              # handguard
    pen.line([P(46, 36), P(18, 104)], INK, 14 * scale)          # pistol grip
    pen.circle(P(96), 13 * scale, fill=(226, 220, 208), outline=INK, width=6 * scale)
    if fire > 0:
        tip = P(340)
        gpen.circle(tip, 120 * fire, fill=(190, 70, 20))
        spen.circle(tip, 90 * fire, fill=col((255, 178, 80), 150))
        pen.poly([P(330, -34 * fire - 4), P(430 * fire + 330, 0), P(330, 34 * fire + 4)], fill=(255, 236, 180))
        tail = P(-70)
        spen.circle(tail, 74 * fire, fill=col((220, 210, 200), 130))


def flamethrower(pen, spen, gpen, hand, ang, scale=1.0, fire=0.0, t=0.0):
    a = math.radians(ang)
    ca, sa = math.cos(a), math.sin(a)
    hx, hy = hand

    def P(d, off=0.0):
        return (hx + ca * d * scale - sa * off * scale, hy + sa * d * scale + ca * off * scale)

    # backpack tank
    pen.rrect((hx - 96 * scale, hy - 60 * scale, hx - 20 * scale, hy + 110 * scale), 26 * scale,
              fill=(178, 66, 58), outline=INK, width=9 * scale)
    pen.rrect((hx - 90 * scale, hy + 34 * scale, hx - 26 * scale, hy + 78 * scale), 8 * scale,
              fill=METAL, outline=INK, width=7 * scale)
    # nozzle pipe + grip
    pen.line([P(-40), P(150)], METAL, 20 * scale)
    pen.line([P(-40), P(150)], INK, 6 * scale)
    pen.line([P(10), P(10, 74)], INK, 16 * scale)
    pen.poly([P(150, -26), P(196, -18), P(196, 18), P(150, 26)], fill=METAL_D, outline=INK, width=8 * scale)
    pen.circle(P(36), 15 * scale, fill=VIVID_RED)
    if fire > 0:
        tip = P(198)
        gpen.circle(tip, 96 * scale, fill=(200, 80, 24))
        for i in range(9):
            d = 200 + i * 46
            w = 46 + i * 16
            pen.poly([P(d, -w), P(d + 62, 0), P(d, w)], fill=(255, 152, 44) if i % 2 else VIVID_RED)
            spen.circle(P(d + 20), w * 0.9, fill=col((255, 150, 60), 60))


def button_panel(pen, spen, gpen, c, scale=1.0, cover=0.0, press=0.0, charge=0.0, t=0.0):
    """emergency console: one big red dome button under a hinged safety cover. Icon only."""
    x, y = c
    pen.rrect((x - 210 * scale, y - 150 * scale, x + 210 * scale, y + 150 * scale), 26 * scale,
              fill=(226, 220, 208), outline=INK, width=11 * scale)
    pen.rrect((x - 186 * scale, y - 126 * scale, x + 186 * scale, y + 60 * scale), 14 * scale,
              fill=(196, 190, 180), outline=INK, width=7 * scale)
    # hazard stripes along the bottom rail (icon-only, no letters)
    for i in range(9):
        bx = x - 180 * scale + i * 42 * scale
        pen.poly([(bx, y + 96 * scale), (bx + 20 * scale, y + 96 * scale),
                  (bx + 34 * scale, y + 126 * scale), (bx + 14 * scale, y + 126 * scale)],
                 fill=(120, 112, 104) if i % 2 else WARM_GOLD)
    # dome
    dome_y = y - 34 * scale + press * 22 * scale
    if charge > 0:
        for i in range(5, 0, -1):
            gpen.circle((x, dome_y), (120 + i * 26) * scale * (0.4 + charge * 0.8), fill=(180, 40, 30))
    pen.circle((x, dome_y), 66 * scale, fill=(150, 40, 40) if press > 0 else VIVID_RED, outline=INK,
               width=10 * scale)
    pen.circle((x - 20 * scale, dome_y - 22 * scale), 20 * scale, fill=col((255, 226, 220), 190))
    # hinged safety cover
    if cover < 1.0:
        ang = -100 * cover
        cw, ch = 118 * scale, 96 * scale
        cx, cy = x, y - 118 * scale
        pts = [rot_pt((cx + dx, cy + dy), (x, y - 118 * scale), ang) for dx, dy in
               ((-cw, -ch * 0.2), (cw, -ch * 0.2), (cw, ch), (-cw, ch))]
        pen.poly(pts, fill=col((120, 132, 150), 210), outline=INK, width=9 * scale)
        pen.line([rot_pt((x - cw, y - 118 * scale), (x, y - 118 * scale), ang),
                  rot_pt((x + cw, y - 118 * scale), (x, y - 118 * scale), ang)], INK, 7 * scale)
    pen.circle((x, y - 118 * scale), 12 * scale, fill=METAL, outline=INK, width=6 * scale)
    if charge > 0.05:
        pen.arc((x, y - 118 * scale), 40 * scale, 40 * scale, -90, -90 + 340 * charge, VIVID_RED, 10 * scale)


def crate(pen, c, scale=1.0, open_=0.0):
    """weapons crate: wooden box with a stencilled rocket icon (no text)."""
    x, y = c
    w, h = 210 * scale, 150 * scale
    pen.rrect((x - w, y - h, x + w, y + h), 14 * scale, fill=WOOD, outline=INK, width=11 * scale)
    pen.line([(x - w, y - h + 40 * scale), (x + w, y - h + 40 * scale)], WOOD_D, 9 * scale)
    pen.rrect((x - w, y - h, x + w, y + h), 14 * scale, fill=None, outline=INK, width=11 * scale)
    pen.line([(x - w + 18 * scale, y - h + 52 * scale), (x + w - 18 * scale, y + h - 18 * scale)],
             WOOD_D, 12 * scale)
    pen.line([(x + w - 18 * scale, y - h + 52 * scale), (x - w + 18 * scale, y + h - 18 * scale)],
             WOOD_D, 12 * scale)
    for sx in (-1, 1):
        pen.line([(x + sx * (w - 10 * scale), y - h + 10 * scale),
                  (x + sx * (w - 10 * scale), y + h - 10 * scale)], INK, 9 * scale)
    lid = open_ * 46
    pen.poly([(x - w, y - h), (x + w, y - h), (x + w - lid * 0.4, y - h - lid), (x - w - lid * 0.4, y - h - lid)],
             fill=WOOD_D, outline=INK, width=10 * scale)


# --------------------------------------------------------------- crater -----
GROUND_Y = 1520


def crater_environment(pen, spen, gpen, t, seed=21, ash=1.0, glow=1.0):
    """everything is gone: night sky, smoke haze, scorched earth, smoking crater."""
    rng = random.Random(seed)
    # --- sky + haze band (the top of the 9:16 frame) ---
    gpen.poly([(-200, -900), (1280, -900), (1280, 1560), (-200, 1560)], fill=(26, 20, 30))
    gpen.circle((520, 1180), 620, fill=(120, 58, 24))
    gpen.circle((520, 1240), 380, fill=(150, 74, 26))
    spen.poly([(-200, 260), (1280, 260), (1280, 1520), (-200, 1520)], fill=col((74, 66, 74), 130))
    for i in range(9):
        u = (i / 9 + 0.07 * math.sin(t * 0.5 + i))
        spen.circle((140 + i * 132 + math.sin(t * 0.4 + i) * 30, 420 + math.sin(i * 2.1) * 90),
                    170 + 30 * math.sin(i), fill=col((96, 88, 96), int(70 * ash)))
    for i in range(22):                       # stars
        rr = random.Random(i * 13)
        if rr.random() < 0.5:
            continue
        spen.circle((rr.uniform(0, 1080), rr.uniform(40, 520)), 3.4,
                    fill=col((228, 226, 240), int(150 * ash)))
    # --- ground ---
    pen.poly([(-620, 1444), (1700, 1444), (1700, 2900), (-620, 2900)], fill=(112, 92, 84))
    pen.poly([(-200, 1444), (1280, 1444), (1280, 1560), (-200, 1560)], fill=(126, 104, 94))
    for i in range(26):                       # baked earth ridges
        rr = random.Random(i * 7)
        y = 1460 + rr.uniform(0, 60)
        pen.line([(rr.uniform(-100, 300), y), (rr.uniform(600, 1200), y + rr.uniform(-10, 10))],
                 col((92, 74, 68), 150), rr.uniform(4, 9))
    # crater
    pen.ellipse((520, 1706), 556, 250, fill=(150, 122, 106), outline=(94, 74, 66), width=12)
    pen.ellipse((520, 1716), 470, 206, fill=(92, 70, 62))
    pen.ellipse((520, 1730), 396, 168, fill=(62, 46, 44))
    pen.ellipse((520, 1746), 300, 122, fill=(44, 32, 32))
    if glow > 0:
        for i in range(26):                   # molten cracks
            a = i * 0.7
            pen.line([(520 + math.cos(a) * 300, 1740 + math.sin(a) * 122),
                      (520 + math.cos(a) * 470, 1730 + math.sin(a) * 200)], col((255, 120, 50), 130), 6)
    # rubble ring: chunky slabs, snapped beams, glass
    for i in range(30):
        rr = random.Random(i * 23)
        side = -1 if i % 2 else 1
        x = 520 + side * rr.uniform(430, 900)
        y = 1560 + rr.uniform(-40, 240)
        sc = rr.uniform(0.5, 1.5)
        kind = rr.random()
        fillc = rr.choice([(88, 74, 70), (70, 60, 58), (104, 84, 72)])
        if kind < 0.55:
            a = rr.uniform(-30, 30)
            pen.poly([rot_pt((x + dx * sc, y + dy * sc), (x, y), a) for dx, dy in
                      ((-70, -22), (46, -34), (74, 20), (-40, 30))], fill=fillc,
                     outline=(48, 40, 38), width=7)
        elif kind < 0.8:
            pen.line([(x, y), (x + rr.uniform(-120, 120), y - rr.uniform(40, 120))], (56, 46, 44), 13)
            pen.line([(x - 20, y + 10), (x + rr.uniform(60, 160), y - rr.uniform(10, 60))],
                     (66, 54, 50), 10)
        else:
            pen.ellipse((x, y), 34 * sc, 12 * sc, fill=(150, 168, 182), outline=(96, 108, 118),
                        width=5, angle=rr.uniform(-40, 40))
    # smoke columns from the ground
    if ash > 0:
        for i in range(5):
            fx_ = 180 + i * 190
            for j in range(9):
                rr = random.Random(i * 31 + j)
                u = (j / 9 + (t * 0.06 + rr.random()) % 1.0) % 1.0
                spen.circle((fx_ + math.sin(t * 0.5 + j) * 40, 1560 - u * 700),
                            60 + u * 130, fill=col((128, 118, 116), int(58 * (1 - u * 0.8) * ash)))
