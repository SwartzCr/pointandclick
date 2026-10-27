"""The Nave, painted in the manner of Sam & Max Hit the Road / Day of the
Tentacle backgrounds: no outlines, lamplight, contact shadows, mottled
paint, crooked perspective, reduced to 256 colours."""
import math
import numpy as np
import paint
from paint import Painting

W, H, VH = 1280, 800, 576
VP = (640, 110)          # vanishing point for the furniture tops


def warp(x, y):
    """A gentle fisheye: the floor bows down at the sides, the ceiling bows
    up, and verticals fan out towards the bottom."""
    nx = (x - 640) / 640
    ny = (y - 300) / 300
    return 640 + (x - 640) * (1 + 0.07 * ny), y + 22 * nx * nx * ny


# ------------------------------------------------------------------ helpers
def toward(p, f, vp=VP):
    return (p[0] + (vp[0] - p[0]) * f, p[1] + (vp[1] - p[1]) * f)


def box(pt, x0, y0, x1, y1, f, base, top=1.15, front=0.82, side=0.55, contact=True, top_col=None,
        mottle=0.05, grain=None, lip=True):
    """A box standing in the room: front face (x0..x1, y0..y1), top and the
    side facing the middle, receding towards the vanishing point by f."""
    tl, tr, br, bl = (x0, y0), (x1, y0), (x1, y1), (x0, y1)
    btl, btr = toward(tl, f), toward(tr, f)
    bbr, bbl = toward(br, f), toward(bl, f)
    if contact:
        foot = pt.mask('poly', [bl, br, bbr, bbl])
        pt.contact(foot, radius=10, amount=0.55)
    mtop = pt.mask('poly', [tl, tr, btr, btl])
    pt.fill(mtop, top_col or base, facing=top, mottle=mottle)
    cx = (x0 + x1) / 2
    if cx < VP[0]:
        mside = pt.mask('poly', [tr, btr, bbr, br])
    else:
        mside = pt.mask('poly', [tl, btl, bbl, bl])
    pt.fill(mside, base, facing=side, mottle=mottle, grad=((0, 1), 0.25))
    mfront = pt.mask('poly', [tl, tr, br, bl])
    pt.fill(mfront, base, facing=front, mottle=mottle, grad=((0, 1), 0.3))
    if grain:
        for m in (mtop, mfront, mside):
            pt.strokes(m, int(abs(x1 - x0) * abs(y1 - y0) / 140) + 4, 22, grain, alpha=0.3, angle=0.0, jitter=0.08)
    if lip:
        pt.crease([tl, tr], width=1.5, amount=0.25)
    return mtop, mfront, mside


def cylinder(pt, m, base, facing=1.0, axis='v', hi=True):
    """Light a cylindrical shape: dark on the side away from the lamps, a
    bright streak on the near side."""
    pt.fill(m, base, facing=facing, mottle=0.03)
    ys, xs = np.nonzero(m > 0.5)
    if not len(xs):
        return
    if axis == 'v':
        x0, x1 = xs.min(), xs.max()
        t = (pt.xx * paint.S - x0) / max(1, x1 - x0)
    else:
        y0, y1 = ys.min(), ys.max()
        t = (pt.yy * paint.S - y0) / max(1, y1 - y0)
    pt.shade(m * np.clip((t - 0.55) * 2.2, 0, 1), 0.55)
    if hi:
        streak = m * np.clip(1 - np.abs(t - 0.25) * 9, 0, 1)
        pt.glow(streak, 0.55)


def sphere(pt, x, y, r, base, hi=True):
    m = pt.mask('ellipse', [x - r, y - r, x + r, y + r])
    pt.fill(m, base, mottle=0.04)
    d = pt.mask('ellipse', [x - r * 0.75, y - r * 0.85, x + r * 0.95, y + r * 0.75])
    pt.shade(m * (1 - d), 0.55, blur=1.0)
    if hi:
        pt.glow(pt.mask('ellipse', [x - r * 0.55, y - r * 0.6, x - r * 0.1, y - r * 0.2]), 0.7, blur=0.8)
    return m


def noodles(pt, strands, base=(250, 218, 130), width=3):
    for pts in strands:
        pt.crease([(x + 1.2, y + 1.6) for x, y in pts], width=width, amount=0.45)
        m = pt.mask('line', pts, width=width)
        pt.fill(m, base, mottle=0.02)
        pt.glow(pt.mask('line', [(x - 0.6, y - 0.8) for x, y in pts], width=max(1, width * 0.35)), 0.35)


# ------------------------------------------------------------------ the room
def nave(seed=913):
    paint.set_warp(warp)
    pt = Painting(W, VH, seed)
    pt.ambient = np.array([0.36, 0.33, 0.44], np.float32)
    pt.light(420, 150, 760, 0.95, (1.0, 0.84, 0.58))       # left lamp
    pt.light(880, 150, 700, 0.85, (1.0, 0.82, 0.56))       # right lamp
    pt.light(608, 230, 330, 0.35, (0.55, 0.65, 1.0))       # through the stained glass
    rng = pt.rng

    BL, BR, BT, BB = 230, 1050, 78, 330
    # ceiling, with beams receding to the back wall
    ceil = pt.mask('poly', [(-60, -40), (1340, -40), (BR, BT), (BL, BT)])
    pt.fill(ceil, (110, 86, 76), facing=0.5, mottle=0.08, mscale=10)
    for k in range(-3, 4):
        x0 = 640 + k * 230
        xb = 640 + k * 118
        beam = pt.mask('poly', [(x0 - 24, -40), (x0 + 24, -40), (xb + 12, BT), (xb - 12, BT)])
        pt.fill(beam, (92, 64, 50), facing=0.45, mottle=0.06)
        pt.crease([(x0 + 24, -40), (xb + 12, BT)], width=3, amount=0.5)
    pt.crease([(200, 30), (330, 46), (360, 38), (470, 52)], width=1.5, amount=0.45)      # a crack
    # walls
    back = pt.mask('poly', [(BL, BT), (BR, BT), (BR, BB), (BL, BB)])
    pt.fill(back, (236, 214, 168), facing=1.0, mottle=0.035, mscale=14)
    left = pt.mask('poly', [(-60, -40), (BL, BT), (BL, BB), (-80, 600)])
    pt.fill(left, (232, 196, 140), facing=0.9, mottle=0.035, mscale=14, grad=((-1, 0), 0.35))
    right = pt.mask('poly', [(1340, -40), (BR, BT), (BR, BB), (1360, 600)])
    pt.fill(right, (232, 196, 140), facing=0.8, mottle=0.035, mscale=14, grad=((1, 0), 0.35))
    # wallpaper stripes with tiny forks
    for i, x in enumerate(range(BL, BR, 40)):
        if i % 2:
            stripe = pt.mask('rect', [x, BT + 22, x + 20, BB - 34])
            pt.shade(stripe, 0.12, colour=(170, 120, 80))
        for y in range(BT + 44 + (i % 2) * 24, BB - 50, 48):
            fx = x + 10
            pt.crease([(fx, y), (fx, y + 14)], width=1.4, amount=0.22)
            pt.crease([(fx - 4, y - 5), (fx - 4, y), (fx + 4, y), (fx + 4, y - 5)], width=1.2, amount=0.2)
    # wainscot and crown
    box(pt, BL, BB - 30, BR, BB, 0.0, (150, 92, 54), contact=False, grain=(110, 64, 36))
    pt.crease([(BL, BB - 30), (BR, BB - 30)], width=2, amount=0.4)
    for x in range(BL + 24, BR - 30, 82):
        pt.crease([(x, BB - 24), (x + 62, BB - 24), (x + 62, BB - 6)], width=1.2, amount=0.35)
        pt.glow(pt.mask('line', [(x, BB - 6), (x, BB - 24)], width=1.2), 0.25)
    pt.fill(pt.mask('rect', [BL, BT, BR, BT + 16]), (150, 96, 60), facing=0.7, mottle=0.04)
    pt.crease([(BL, BT + 16), (BR, BT + 16)], width=3, amount=0.45)
    # floor
    floor = pt.mask('poly', [(BL, BB), (BR, BB), (1360, 600), (-80, 600)])
    pt.fill(floor, (178, 104, 56), facing=1.0, mottle=0.07, mscale=5)
    for i in range(-16, 17):                    # boards converging on the back wall
        xb = 640 + i * 44
        xf = 640 + i * 44 * 2.6
        pt.crease([(xb, BB), (xf, 600)], width=1.6, amount=0.38)
    pt.strokes(floor, 900, 14, (120, 64, 34), alpha=0.22, angle=1.45, jitter=0.12)
    pt.strokes(floor, 300, 10, (220, 150, 90), alpha=0.18, angle=1.5, jitter=0.12)
    for y in (BB, BB + 1):
        pt.crease([(BL, y), (BR, y)], width=3, amount=0.55)
    pt.crease([(BL, BB), (-80, 600)], width=3, amount=0.5)
    pt.crease([(BR, BB), (1360, 600)], width=3, amount=0.5)
    pt.crease([(BL, BT), (BL, BB)], width=2, amount=0.35)
    pt.crease([(BR, BT), (BR, BB)], width=2, amount=0.35)

    # ---------------------------------------------------------- Weird Sauce (back wall, left)
    box(pt, 254, 108, 410, 296, 0.03, (132, 78, 44), contact=False, grain=(96, 54, 30))
    pt.contact(pt.mask('rect', [254, 108, 410, 296]), radius=8, amount=0.35)
    pt.fill(pt.mask('rect', [266, 118, 398, 144]), (70, 40, 26), facing=0.8)
    pt.text((332, 131), 'WEIRD SAUCE', 17, (255, 214, 96))
    for bx, col in ((280, (214, 36, 30)), (322, (88, 172, 52)), (364, (250, 180, 40))):
        cylinder(pt, pt.mask('rect', [bx, 160, bx + 28, 214]), col)
        cylinder(pt, pt.mask('rect', [bx + 8, 146, bx + 20, 162]), (210, 214, 226))
        cylinder(pt, pt.mask('rect', [bx + 11, 214, bx + 17, 234]), (196, 128, 80))
    cylinder(pt, pt.mask('rect', [292, 230, 376, 238]), (196, 128, 80), axis='h')
    sphere(pt, 334, 248, 15, (196, 202, 214))
    cylinder(pt, pt.mask('poly', [(328, 262), (340, 262), (342, 282), (326, 282)]), (196, 202, 214))
    sphere(pt, 388, 262, 13, (70, 44, 30), hi=False)
    pt.fill(pt.mask('ellipse', [380, 254, 396, 270]), (238, 220, 170), facing=1.0)
    pt.crease([(388, 262), (393, 256)], width=1.5, amount=0.9)
    pt.fill(pt.mask('rect', [308, 284, 360, 292]), (236, 236, 244), facing=1.0)
    pt.fill(pt.mask('ellipse', [326, 283, 340, 290]), (200, 40, 30), facing=1.0)

    # ---------------------------------------------------------- Glutenous Truth + crochet
    def frame(x0, y0, x1, y1, inner):
        box(pt, x0, y0, x1, y1, 0.02, (226, 178, 70), contact=False)
        pt.glow(pt.mask('line', [(x0 + 2, y1 - 2), (x0 + 2, y0 + 2), (x1 - 2, y0 + 2)], width=2), 0.5)
        m = pt.mask('rect', [x0 + 9, y0 + 9, x1 - 9, y1 - 9])
        pt.fill(m, inner, facing=0.9)
        pt.contact(pt.mask('rect', [x0, y0, x1, y1]), radius=6, amount=0.3)
        return m
    frame(428, 106, 514, 214, (50, 34, 76))
    sphere(pt, 471, 160, 24, (250, 204, 120))
    for a in range(0, 360, 30):
        r = math.radians(a)
        m = pt.mask('line', [(471 + 30 * math.cos(r), 160 + 30 * math.sin(r)), (471 + 38 * math.cos(r), 160 + 38 * math.sin(r))], width=2)
        pt.fill(m, (255, 236, 160), emissive=True)
    box(pt, 424, 246, 520, 254, 0.04, (130, 82, 50), contact=False)
    for i, c in enumerate([(250, 220, 140), (240, 196, 110), (232, 120, 64), (130, 180, 84), (250, 220, 140)]):
        sphere(pt, 436 + i * 18, 238, 8, c, hi=False)

    # ---------------------------------------------------------- stained-glass flat (centre)
    sx0, sx1, sy0, sy1 = 536, 680, 92, 326
    arch = [(sx0, sy1)] + [(608 + 72 * math.cos(math.radians(a)), sy0 + 72 - 72 * math.sin(math.radians(a)))
                           for a in range(180, -1, -10)] + [(sx1, sy1)]
    outer = [(sx0 - 9, sy1)] + [(608 + 81 * math.cos(math.radians(a)), sy0 + 72 - 81 * math.sin(math.radians(a)))
                                for a in range(180, -1, -10)] + [(sx1 + 9, sy1)]
    pt.contact(pt.mask('poly', outer), radius=10, amount=0.45)
    pt.fill(pt.mask('poly', outer), (86, 60, 48), facing=0.8)
    glass = pt.mask('poly', arch)
    panes = [(70, 104, 210), (214, 64, 70), (248, 200, 74), (74, 164, 100), (152, 84, 192), (238, 130, 52)]
    for row, y in enumerate(range(sy0 - 10, sy1, 26)):
        for col, x in enumerate(range(sx0, sx1, 26)):
            c = panes[(row * 2 + col * 3) % len(panes)]
            c = tuple(int(c[i] * 0.45 + (70, 104, 210)[i] * 0.55) for i in range(3))
            pt.fill(pt.mask('rect', [x, y, x + 25, y + 25]) * glass, c, emissive=True, mottle=0.08)
    pt.fill(pt.mask('rect', [sx0, sy1 - 40, sx1, sy1]) * glass, (66, 140, 70), emissive=True, mottle=0.1)
    pt.fill(pt.mask('ellipse', [576, sy0 + 14, 640, sy0 + 72]) * glass, (255, 214, 96), emissive=True)
    for row, y in enumerate(range(sy0 - 10, sy1, 26)):
        pt.crease([(sx0, y), (sx1, y)], width=2, amount=0.75)
    for x in range(sx0, sx1, 26):
        pt.crease([(x, sy0), (x, sy1)], width=2, amount=0.75)
    cx, cy = 608, 214
    for k in range(9):
        a = math.pi * (0.1 + 0.8 * k / 8)
        pts = [(cx + math.cos(a + 0.4 * math.sin(t * 3)) * t * 66, cy + 10 + math.sin(a) * t * 90) for t in [i / 12 for i in range(13)]]
        m = pt.mask('line', pts, width=5) * glass
        pt.shade(pt.mask('line', pts, width=8) * glass, 0.8)
        pt.fill(m, (255, 228, 150), emissive=True)
    body = pt.mask('ellipse', [cx - 28, cy - 18, cx + 28, cy + 24])
    pt.shade(pt.mask('ellipse', [cx - 31, cy - 21, cx + 31, cy + 27]), 0.8)
    pt.fill(body, (255, 228, 150), emissive=True)
    for mx in (cx - 15, cx + 15):
        pt.fill(pt.mask('ellipse', [mx - 12, cy - 6, mx + 12, cy + 18]), (180, 86, 52), emissive=True)
    for ex in (cx - 12, cx + 12):
        tx = ex + (ex - cx)
        pt.crease([(ex, cy - 18), (tx, cy - 46)], width=6, amount=0.8)
        pt.fill(pt.mask('line', [(ex, cy - 18), (tx, cy - 46)], width=3), (255, 228, 150), emissive=True)
        pt.fill(pt.mask('ellipse', [tx - 9, cy - 58, tx + 9, cy - 40]), (255, 255, 255), emissive=True)
        pt.fill(pt.mask('ellipse', [tx - 3, cy - 52, tx + 3, cy - 46]), (20, 18, 30), emissive=True)
    pt.glow(glass, 0.18, colour=(200, 220, 255))

    # ---------------------------------------------------------- timeline (back wall)
    box(pt, 704, 112, 890, 262, 0.03, (112, 70, 40), contact=False, grain=(84, 48, 28))
    pt.contact(pt.mask('rect', [704, 112, 890, 262]), radius=8, amount=0.35)
    pt.fill(pt.mask('rect', [714, 120, 880, 144]), (66, 38, 24), facing=0.8)
    pt.text((797, 132), 'TIMELINE', 17, (255, 214, 96))
    for i, kind in enumerate(['noodles', 'fork', 'string', 'counting']):
        tx = 722 + i * 40
        box(pt, tx, 156, tx + 34, 204, 0.02, (246, 234, 206), contact=False)
        if kind == 'noodles':
            pt.fill(pt.mask('chord', [tx + 4, 172, tx + 30, 198], a0=0, a1=180), (200, 74, 58))
            for x in range(tx + 8, tx + 28, 5):
                pt.fill(pt.mask('line', [(x, 178), (x - 2, 168), (x + 1, 162)], width=2), (236, 196, 96))
        elif kind == 'fork':
            pt.fill(pt.mask('rect', [tx + 15, 176, tx + 19, 198]), (170, 176, 190))
            pt.fill(pt.mask('rect', [tx + 8, 172, tx + 26, 177]), (170, 176, 190))
            for x in (tx + 8, tx + 15, tx + 22):
                pt.fill(pt.mask('rect', [x, 160, x + 3, 174]), (170, 176, 190))
        elif kind == 'string':
            pt.fill(pt.mask('line', [(tx + 5, 198), (tx + 11, 168), (tx + 18, 194), (tx + 26, 162), (tx + 29, 182)], width=3), (176, 120, 60))
        else:
            pt.fill(pt.mask('rect', [tx + 8, 164, tx + 26, 198]), (234, 222, 196), facing=0.9)
            for y in range(168, 196, 5):
                pt.crease([(tx + 8, y), (tx + 15, y)], width=1.5, amount=0.7)
    pt.fill(pt.mask('rect', [722, 224, 872, 228]), (250, 232, 186), facing=1.1)
    pt.fill(pt.mask('poly', [(870, 218), (882, 226), (870, 234)]), (250, 232, 186), facing=1.1)
    pt.text((722, 246), 'OLDEST', 11, (246, 214, 150), anchor='lm')
    pt.text((880, 246), 'NEWEST', 11, (246, 214, 150), anchor='rm')

    # ---------------------------------------------------------- sacred topology (back wall, right)
    box(pt, 914, 98, 1030, 262, 0.03, (92, 60, 40), contact=False)
    pt.contact(pt.mask('rect', [914, 98, 1030, 262]), radius=8, amount=0.35)
    case = pt.mask('rect', [924, 108, 1020, 252])
    pt.fill(case, (52, 80, 104), facing=0.8, grad=((0, 1), 0.35))
    for i, (kx, ky) in enumerate(((950, 144), (994, 178), (950, 216))):
        col = [(240, 220, 160), (230, 90, 70), (120, 190, 230)][i]
        if i == 1:
            pts = [(kx + 20 * math.sin(t), ky + 16 * math.sin(t) * math.cos(t)) for t in [j / 40 * math.tau for j in range(41)]]
        else:
            pts = [(kx + 7 * (math.sin(t) + 2 * math.sin(2 * t)) / 1.3, ky + 7 * (math.cos(t) - 2 * math.cos(2 * t)) / 1.3)
                   for t in [j / 50 * math.tau for j in range(51)]]
        noodles(pt, [pts], col, 4)
    pt.glow(pt.mask('poly', [(930, 112), (960, 112), (930, 160)]), 0.18)

    # ---------------------------------------------------------- left wall: paintings, the door
    def wall_quad(x0, x1, y0, y1, k=0.17):
        return [(x0, y0 + (BL - x0) * -k * 0.5), (x1, y0 + (BL - x1) * -k * 0.5),
                (x1, y1 + (BL - x1) * k), (x0, y1 + (BL - x0) * k)]
    fq = wall_quad(96, 186, 92, 172)
    pt.contact(pt.mask('poly', fq), radius=6, amount=0.3)
    pt.fill(pt.mask('poly', fq), (226, 178, 70), facing=0.8)
    iq = wall_quad(105, 177, 102, 162)
    pt.fill(pt.mask('poly', iq), (70, 46, 60), facing=0.8)
    sphere(pt, 142, 128, 17, (244, 200, 160), hi=False)
    pt.fill(pt.mask('ellipse', [136, 132, 148, 144]), (160, 40, 40))
    pt.fill(pt.mask('line', [(110, 156), (128, 146), (140, 138)], width=3), (252, 226, 150), emissive=True)
    sq = wall_quad(92, 190, 190, 300)
    pt.contact(pt.mask('poly', sq), radius=6, amount=0.3)
    pt.fill(pt.mask('poly', sq), (226, 178, 70), facing=0.8)
    pt.fill(pt.mask('poly', wall_quad(101, 181, 200, 290)), (40, 70, 96), facing=0.8)
    for r in range(8, 32, 6):
        pts = [(140 + r * math.cos(math.radians(a)), 250 + r * 0.8 * math.sin(math.radians(a))) for a in range(r * 9, r * 9 + 260, 10)]
        pt.fill(pt.mask('line', pts, width=2), (252, 226, 150))
    pt.fill(pt.mask('poly', [(138, 250), (144, 250), (150, 210), (146, 208)]), (210, 216, 226))
    door = [(0, 236), (78, 262), (78, 520), (0, 572)]
    pt.fill(pt.mask('poly', door), (126, 80, 48), facing=0.7, grad=((0, 1), 0.2))
    pt.fill(pt.mask('poly', [(8, 262), (68, 280), (68, 506), (8, 548)]), (144, 92, 56), facing=0.75)
    pt.crease([(68, 280), (68, 506), (8, 548)], width=2, amount=0.5)
    sphere(pt, 58, 392, 7, (236, 196, 90))
    pt.fill(pt.mask('poly', [(16, 300), (50, 310), (50, 346), (16, 334)]), (244, 240, 226), facing=0.9)
    pt.text((33, 323), '913', 12, (70, 50, 50))

    # ---------------------------------------------------------- right wall: archway (closed) and wardrobe
    arch_o = [(1068, 348), (1068, 140), (1080, 104), (1102, 84), (1128, 80), (1150, 92), (1162, 118), (1162, 420)]
    pt.fill(pt.mask('poly', arch_o), (206, 176, 126), facing=0.66)
    arch_i = [(1076, 352), (1076, 144), (1086, 112), (1104, 96), (1126, 92), (1144, 102), (1154, 124), (1154, 412)]
    pt.crease(arch_i + [arch_i[0]], width=1.5, amount=0.22)
    pt.crease([(1068, 348), (1068, 140), (1080, 104), (1102, 84)], width=2.5, amount=0.35)
    ward = [(1176, 74), (1300, 50), (1300, 580), (1176, 470)]
    pt.contact(pt.mask('poly', ward), radius=12, amount=0.5)
    pt.fill(pt.mask('poly', ward), (124, 76, 44), facing=0.62, grad=((0, 1), 0.3))
    pt.fill(pt.mask('poly', [(1184, 92), (1300, 72), (1300, 556), (1184, 460)]), (142, 88, 52), facing=0.66,
            grad=((0, 1), 0.3))
    pt.strokes(pt.mask('poly', ward), 160, 40, (96, 56, 32), alpha=0.35, angle=math.pi / 2, jitter=0.05)
    pt.crease([(1184, 92), (1184, 460)], width=2, amount=0.5)
    sphere(pt, 1200, 280, 7, (236, 196, 90))

    # ---------------------------------------------------------- the sod table (left)
    tq = [(96, 404), (452, 386), (476, 438), (78, 466)]
    pt.contact(pt.mask('poly', [(80, 470), (480, 444), (500, 540), (84, 560)]), radius=16, amount=0.55)
    for lx, ly in ((92, 500), (270, 486), (452, 476)):
        box(pt, lx, ly - 30, lx + 14, ly + 40, 0.03, (90, 56, 34), contact=False)
    apron = pt.mask('poly', [(78, 466), (476, 438), (476, 470), (78, 500)])
    pt.fill(apron, (104, 64, 38), facing=0.75, grad=((0, 1), 0.3))
    pt.strokes(apron, 120, 30, (74, 44, 26), alpha=0.35, angle=-0.07, jitter=0.04)
    pt.crease([(78, 466), (476, 438)], width=3, amount=0.6)
    top = pt.mask('poly', tq)
    pt.fill(top, (88, 154, 62), facing=1.1, mottle=0.12, mscale=3)
    pt.strokes(top, 1800, 5, (60, 116, 44), alpha=0.6, angle=-math.pi / 2, jitter=0.4)
    pt.strokes(top, 900, 4, (150, 210, 100), alpha=0.55, angle=-math.pi / 2, jitter=0.4)
    for (hx0, hy0, hx1, hy1) in ((132, 396, 214, 430), (290, 388, 360, 418)):
        hill = pt.mask('ellipse', [hx0, hy0, hx1, hy1])
        pt.fill(hill, (98, 168, 72), facing=1.25, mottle=0.08)
        pt.shade(hill * np.clip((pt.yy - (hy0 + hy1) / 2) / ((hy1 - hy0) / 2), 0, 1), 0.35)
    pt.fill(pt.mask('line', [(220, 452), (252, 428), (300, 436), (342, 416)], width=4), (196, 52, 40), facing=1.1)
    for vx, vy in ((172, 434), (186, 440), (268, 418), (318, 434), (330, 428)):
        pt.fill(pt.mask('rect', [vx, vy - 8, vx + 4, vy]), (248, 242, 226), facing=1.1)
        pt.crease([(vx + 5, vy), (vx + 8, vy - 1)], width=1.5, amount=0.5)
    box(pt, 378, 396, 404, 414, 0.06, (246, 242, 230), contact=False)
    pt.fill(pt.mask('poly', [(374, 396), (391, 382), (408, 394)]), (204, 62, 52), facing=1.1)
    # audio-story handset
    pt.contact(pt.mask('rect', [96, 412, 146, 438]), radius=5, amount=0.6)
    box(pt, 98, 414, 140, 434, 0.08, (52, 48, 56), contact=False)
    pt.fill(pt.mask('rect', [94, 404, 146, 414]), (70, 66, 80), facing=1.0)
    pt.glow(pt.mask('line', [(96, 405), (144, 405)], width=1.5), 0.5)
    pt.fill(pt.mask('ellipse', [112, 418, 126, 430]), (190, 180, 160), facing=1.0)
    # pamphlet holder
    pt.fill(pt.mask('poly', [(412, 378), (446, 374), (450, 404), (416, 408)]), (210, 206, 196), facing=0.9)
    pt.fill(pt.mask('poly', [(418, 370), (442, 366), (444, 396), (420, 400)]), (252, 248, 236), facing=1.1)
    pt.crease([(422, 376), (438, 373)], width=2, amount=0.0)
    pt.fill(pt.mask('line', [(422, 376), (438, 373)], width=2), (210, 60, 50))
    for k in range(4):
        pt.crease([(422, 382 + k * 5), (438, 379 + k * 5)], width=1, amount=0.5)

    # ---------------------------------------------------------- spaghetti sculpture on its plinth
    pt.contact(pt.mask('ellipse', [566, 470, 730, 512]), radius=14, amount=0.6)
    box(pt, 586, 420, 694, 482, 0.07, (236, 232, 222), contact=False)
    box(pt, 576, 482, 704, 492, 0.06, (220, 214, 204), contact=False)
    pt.text((640, 454), 'SPAGHETTI', 12, (120, 110, 100))
    strands = []
    for k in range(44):
        a0 = rng.uniform(0, math.tau)
        pts = []
        for i in range(34):
            t = i / 33
            yy = 418 - t * 150
            rad = 40 * (1 - t) + 17 + 9 * math.sin(t * 9 + k)
            pts.append((640 + rad * math.cos(a0 + t * 7), yy + 6 * math.sin(a0 + t * 7)))
        strands.append(pts)
    noodles(pt, strands, width=3)
    for mx, my, r in ((618, 282, 12), (662, 286, 12), (640, 334, 11), (606, 378, 10), (678, 366, 10)):
        sphere(pt, mx, my, r, (156, 76, 46))
    for ex, sx in ((604, -1), (676, 1)):
        noodles(pt, [[(640 + sx * 18, 276), (ex, 248)]], width=4)
        pt.shade(pt.mask('ellipse', [ex - 12, 230, ex + 12, 254]), 0.9)
        pt.fill(pt.mask('ellipse', [ex - 10, 232, ex + 10, 252]), (255, 255, 255), facing=1.2)
        pt.fill(pt.mask('ellipse', [ex - 2, 238, ex + 6, 246]), (24, 20, 30))

    # ---------------------------------------------------------- paragraph spinner on its table
    pt.contact(pt.mask('poly', [(830, 470), (1070, 456), (1090, 520), (836, 530)]), radius=16, amount=0.55)
    for lx, ly in ((842, 432), (1052, 432), (948, 432)):
        box(pt, lx, ly, lx + 12, ly + 54, 0.02, (96, 60, 36), contact=False)
    box(pt, 830, 414, 1070, 432, 0.09, (130, 80, 48), contact=False, grain=(96, 56, 32))
    box(pt, 864, 262, 1032, 416, 0.07, (98, 62, 38), contact=False, grain=(74, 44, 26))
    pt.fill(pt.mask('rect', [872, 270, 1024, 294]), (66, 38, 24), facing=0.8)
    pt.text((948, 282), 'PARAGRAPH', 15, (255, 214, 96))
    for i, w in enumerate(['THE', 'FORKS', 'SEEM', 'BLAND']):
        y = 302 + i * 28
        pt.fill(pt.mask('rect', [876, y - 2, 1020, y + 24]), (40, 24, 16), facing=0.6)
        cylinder(pt, pt.mask('rect', [880, y, 1016, y + 21]), (246, 236, 214), axis='h')
        pt.text((948, y + 11), w, 15, (54, 36, 30))
        sphere(pt, 1030, y + 10, 6, (220, 196, 128))

    paint.set_warp(lambda x, y: warp(x - 70, y + 16))
    # ---------------------------------------------------------- scales of pasta
    pt.contact(pt.mask('poly', [(920, 534), (1180, 520), (1200, 590), (930, 590)]), radius=16, amount=0.55)
    for lx in (930, 1164):
        box(pt, lx, 520, lx + 13, 590, 0.02, (96, 60, 36), contact=False)
    box(pt, 920, 500, 1180, 520, 0.09, (130, 80, 48), contact=False, grain=(96, 56, 32))
    brass = (232, 184, 70)
    pt.contact(pt.mask('ellipse', [1016, 484, 1084, 504]), radius=5, amount=0.6)
    box(pt, 1024, 486, 1076, 498, 0.08, brass, contact=False)
    cylinder(pt, pt.mask('rect', [1044, 388, 1056, 488]), brass)
    cylinder(pt, pt.mask('poly', [(978, 406), (1122, 398), (1122, 404), (978, 412)]), brass, axis='h')
    sphere(pt, 1050, 382, 10, brass)
    for px_, py_ in ((982, 409), (1118, 401)):
        pt.crease([(px_, py_), (px_ - 20, py_ + 46)], width=1.5, amount=0.6)
        pt.crease([(px_, py_), (px_ + 20, py_ + 46)], width=1.5, amount=0.6)
        pan = pt.mask('chord', [px_ - 28, py_ + 34, px_ + 28, py_ + 62], a0=0, a1=180)
        cylinder(pt, pan, brass)
    for k in range(6):
        sphere(pt, 1106 + k * 5, 432 - (k % 2) * 5, 4, (244, 204, 112), hi=False)
    box(pt, 970, 432, 994, 444, 0.08, (160, 160, 172), contact=False)

    paint.set_warp(warp)

    # ---------------------------------------------------------- the puzzle box on a side table
    pt.contact(pt.mask('ellipse', [452, 548, 600, 590]), radius=14, amount=0.55)
    cylinder(pt, pt.mask('rect', [514, 532, 532, 590]), (110, 70, 42))
    top_m = pt.mask('ellipse', [460, 512, 586, 542])
    pt.fill(top_m, (136, 86, 50), facing=1.1, mottle=0.05)
    pt.fill(pt.mask('chord', [460, 512, 586, 548], a0=0, a1=180) * (1 - top_m), (100, 62, 36), facing=0.7)
    box(pt, 476, 476, 568, 520, 0.08, (164, 104, 54), grain=(126, 76, 38))
    for i, c in enumerate([(196, 160, 96)] * 3):
        sphere(pt, 499 + i * 23, 496, 9, c)
    pt.fill(pt.mask('poly', [(494, 499), (500, 491), (503, 493), (497, 501)]), (252, 226, 150))
    pt.fill(pt.mask('poly', [(516, 492), (522, 496), (528, 492), (528, 500), (522, 496), (516, 500)]), (252, 226, 150))
    pt.fill(pt.mask('ellipse', [540, 491, 550, 501]), (252, 226, 150))

    # ---------------------------------------------------------- the lamps
    for lx in (420, 880):
        pt.crease([(lx, -40), (lx, 40)], width=3, amount=0.8)
        shade_m = pt.mask('poly', [(lx - 12, 36), (lx + 12, 36), (lx + 44, 66), (lx - 44, 66)])
        pt.fill(shade_m, (70, 120, 80), facing=0.6, mottle=0.03)
        pt.shade(shade_m * np.clip((pt.xx - lx) / 46, 0, 1), 0.5)
        pt.glow(pt.mask('line', [(lx - 8, 40), (lx - 36, 62)], width=2), 0.5)
        bulb = pt.mask('ellipse', [lx - 38, 60, lx + 38, 72])
        pt.fill(bulb, (255, 246, 214), emissive=True)
        cone = pt.mask('poly', [(lx - 40, 68), (lx + 40, 68), (lx + 210, 560), (lx - 210, 560)])
        pt.glow(cone * np.clip(1 - (pt.yy - 68) / 500, 0, 1), 0.14, blur=8)

    # ---------------------------------------------------------- finish: a bit more lamplight on the floor
    for lx in (420, 880):
        pool = pt.mask('ellipse', [lx - 260, 420, lx + 260, 600])
        pt.glow(pool, 0.12, colour=(255, 214, 150), blur=30)
    paint.set_warp(None)
    return pt


def interface(im, scale):
    """The verb strip below the room, at the given scale."""
    from PIL import ImageDraw, ImageFont
    d = ImageDraw.Draw(im)
    d.fontmode = '1'
    S = scale
    d.rectangle([0, VH * S, W * S, H * S], fill=(12, 8, 18))
    d.line([(0, VH * S), (W * S, VH * S)], fill=(90, 50, 64), width=max(1, int(2 * S)))
    f = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', int(24 * S))
    d.text((W * S / 2, (VH + 18) * S), 'Talk to Khuc', font=f, fill=(150, 236, 236), anchor='mm')
    verbs = [['Open', 'Pick up', 'Push'], ['Close', 'Look at', 'Pull'], ['Talk to', 'Use', 'Walk to']]
    for r, row in enumerate(verbs):
        for c, v in enumerate(row):
            col = (160, 248, 248) if v == 'Talk to' else (48, 168, 168)
            d.text(((36 + c * 192) * S, (VH + 64 + r * 54) * S), v, font=f, fill=col)
    for n in range(8):
        x = 632 + (n % 4) * 156
        y = VH + 44 + (n // 4) * 88
        d.rectangle([(x + 4) * S, (y + 2) * S, (x + 150) * S, (y + 84) * S], fill=(30, 22, 40))
    return im
