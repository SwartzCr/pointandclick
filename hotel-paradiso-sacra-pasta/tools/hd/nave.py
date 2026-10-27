"""The Nave at 1280x800 (room view 1280x576), shaded LucasArts-style."""
import math
import random
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from shade import (Layer, rgba, mask_of, linear_shade, light_pool, vignette, soft_shadow, wonky,
                   quantize, ramp)

W, H, VH = 1280, 800, 576
BL, BR, BB = 192, 1088, 296          # back wall left, right, bottom
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
INK = (40, 22, 30)


def fx_left(y):
    return BL - (y - BB) * (BL + 80) / (VH - BB)


def fx_right(y):
    return BR + (y - BB) * (W + 80 - BR) / (VH - BB)


def sign(d, xy, s, size, color, anchor='mm', shadow=(40, 20, 20)):
    f = ImageFont.truetype(FONT, size)
    d.fontmode = '1'
    x, y = xy
    d.text((x + 2, y + 2), s, font=f, fill=rgba(shadow), anchor=anchor)
    d.text((x, y), s, font=f, fill=rgba(color), anchor=anchor)


def box(L, x0, y0, x1, y1, depth, base, radius=4, bands=6, vp=640, outline=2):
    """A box seen from slightly above: front face, top face and the side
    that faces the middle of the room."""
    cxm = (x0 + x1) / 2
    dy = -depth * 0.55
    dx = (vp - cxm) / 640 * depth * 0.7
    top = [(x0, y0), (x1, y0), (x1 + dx, y0 + dy), (x0 + dx, y0 + dy)]
    L.shape(base, lambda d: d.polygon(top, fill=255), radius=radius, bands=bands, flat=0.6, outline=outline,
            light=np.array([-0.3, -0.2, 0.93]))
    if dx > 0:
        side = [(x1, y0), (x1 + dx, y0 + dy), (x1 + dx, y1 + dy), (x1, y1)]
    else:
        side = [(x0, y0), (x0 + dx, y0 + dy), (x0 + dx, y1 + dy), (x0, y1)]
    if abs(dx) > 1:
        L.shape(base, lambda d: d.polygon(side, fill=255), radius=radius, bands=bands, flat=0.6, outline=outline,
                light=np.array([0.9 if dx < 0 else -0.2, 0.3, 0.3]))
    L.shape(base, lambda d: d.rectangle([x0, y0, x1, y1], fill=255), radius=radius, bands=bands, flat=0.6,
            outline=outline)
    return top


def frame(L, box_, gold=(222, 176, 70), inner=(60, 40, 60), width=10):
    x0, y0, x1, y1 = box_
    L.shape(gold, lambda d: (d.rectangle([x0, y0, x1, y1], fill=255),
                             d.rectangle([x0 + width, y0 + width, x1 - width, y1 - width], fill=0)),
            radius=5, bands=5, spec=True)
    L.shape(inner, lambda d: d.rectangle([x0 + width, y0 + width, x1 - width, y1 - width], fill=255),
            radius=30, bands=5, outline=1)


def meatball(L, cx, cy, r):
    L.shape((150, 74, 46), lambda d: d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=255), radius=r,
            bands=5, spec=True, outline=2)
    d = ImageDraw.Draw(L.im)
    rnd = random.Random(int(cx * 7 + cy))
    for _ in range(int(r)):
        a, rr = rnd.uniform(0, math.tau), rnd.uniform(0, r * 0.8)
        d.point((cx + math.cos(a) * rr, cy + math.sin(a) * rr), fill=rgba((110, 50, 34)))


def noodle(L, pts, color=(250, 222, 140), width=4):
    d = ImageDraw.Draw(L.im)
    d.line(pts, fill=rgba((150, 104, 50)), width=width + 2, joint='curve')
    d.line(pts, fill=rgba(color), width=width, joint='curve')
    hi = [(x - 1, y - 1) for x, y in pts]
    d.line(hi, fill=rgba((255, 246, 200)), width=max(1, width // 3))


def nave():
    rnd = random.Random(913)
    bg = Image.new('RGBA', (W, H), (0, 0, 0, 255))
    size = (W, H)

    # ---------------------------------------------------------- shell
    wall = (238, 212, 164)
    back = mask_of(size, lambda d: d.rectangle([BL, 0, BR, BB], fill=255))
    bg.alpha_composite(linear_shade(size, back, wall, angle=math.pi / 2, lo=0.62, hi=0.8, bands=8, noise=0.01))
    lwall = mask_of(size, lambda d: d.polygon([(0, 0), (BL, 0), (BL, BB), (fx_left(VH), VH), (0, VH)], fill=255))
    bg.alpha_composite(linear_shade(size, lwall, (214, 182, 132), angle=0, lo=0.36, hi=0.62, bands=7))
    rwall = mask_of(size, lambda d: d.polygon([(W, 0), (BR, 0), (BR, BB), (fx_right(VH), VH), (W, VH)], fill=255))
    bg.alpha_composite(linear_shade(size, rwall, (214, 182, 132), angle=math.pi, lo=0.3, hi=0.55, bands=7))
    floor = mask_of(size, lambda d: d.polygon([(BL, BB), (BR, BB), (fx_right(VH), VH), (fx_left(VH), VH)], fill=255))
    bg.alpha_composite(linear_shade(size, floor, (176, 104, 58), angle=-math.pi / 2, lo=0.3, hi=0.66, bands=8, noise=0.02))
    d = ImageDraw.Draw(bg)
    # floorboards converging on the back wall
    for i in range(-14, 15):
        xb = 640 + i * 46
        xf = 640 + i * 46 * 2.3
        d.line([(xb, BB), (xf, VH)], fill=rgba((122, 70, 40)), width=2)
    for k in range(9):
        y = BB + (VH - BB) * (k / 9) ** 1.4
        d.line([(fx_left(y), y), (fx_right(y), y)], fill=rgba((140, 82, 46)), width=1)
    for _ in range(140):                                     # knots and grain
        y = rnd.uniform(BB + 6, VH - 4)
        x = rnd.uniform(fx_left(y), fx_right(y))
        d.line([(x, y), (x + rnd.uniform(6, 20), y)], fill=rgba((150, 88, 50)), width=1)
    # wallpaper strips with little forks, lit from the left
    L = Layer(W, H)
    for i, x in enumerate(range(BL + 4, BR - 4, 36)):
        col = (246, 226, 182) if i % 2 else (232, 204, 150)
        m = mask_of(size, lambda dd, x=x: dd.rectangle([x, 24, x + 33, BB - 26], fill=255))
        bg.alpha_composite(linear_shade(size, m, col, angle=math.pi / 2, lo=0.58, hi=0.78, bands=6))
        for y in range(44 + (i % 2) * 22, BB - 40, 44):
            c = rgba(tuple(int(v * 0.8) for v in col))
            d.line([(x + 16, y), (x + 16, y + 15)], fill=c, width=2)
            for t in (-5, 0, 5):
                d.line([(x + 16 + t, y - 6), (x + 16 + t, y)], fill=c, width=1)
            d.line([(x + 11, y), (x + 21, y)], fill=c, width=2)
    # crown moulding and wainscot
    box(L, BL, 0, BR, 22, 6, (150, 96, 56), radius=3)
    box(L, BL, BB - 26, BR, BB - 2, 8, (146, 92, 54), radius=3)
    for x in range(BL + 30, BR - 20, 74):
        L.shape((146, 92, 54), lambda dd, x=x: dd.rectangle([x, BB - 22, x + 54, BB - 6], fill=255), radius=3, bands=4,
                outline=1, flat=0.5)
    bg.alpha_composite(L.im)
    L = Layer(W, H)

    # ---------------------------------------------------------- Weird Sauce
    box(L, 220, 68, 392, 264, 10, (128, 76, 44))
    box(L, 230, 76, 382, 104, 4, (70, 40, 26))
    for bx, col in ((246, (210, 40, 32)), (294, (90, 170, 56)), (342, (248, 178, 40))):
        L.shape(col, lambda dd, bx=bx: dd.rounded_rectangle([bx, 118, bx + 30, 174], 8, fill=255), radius=12, bands=6,
                spec=True)
        L.shape((216, 222, 232), lambda dd, bx=bx: dd.rectangle([bx + 8, 102, bx + 22, 120], fill=255), radius=5,
                bands=4, spec=True)
        L.shape((200, 130, 80), lambda dd, bx=bx: dd.rectangle([bx + 12, 174, bx + 18, 196], fill=255), radius=3,
                bands=4, outline=1)
    L.shape((200, 130, 80), lambda dd: dd.rectangle([258, 192, 360, 200], fill=255), radius=3, bands=4)
    L.shape((190, 196, 210), lambda dd: dd.ellipse([288, 190, 320, 222], fill=255), radius=14, bands=6, spec=True)
    L.shape((190, 196, 210), lambda dd: dd.polygon([(298, 220), (310, 220), (312, 244), (296, 244)], fill=255),
            radius=4, bands=4, spec=True)
    L.shape((70, 44, 30), lambda dd: dd.ellipse([346, 200, 378, 232], fill=255), radius=14, bands=5)
    L.shape((236, 216, 166), lambda dd: dd.ellipse([351, 205, 373, 227], fill=255), radius=8, bands=4, outline=1)
    L.line([(362, 216), (370, 206)], (120, 30, 30), 2)
    L.shape((236, 236, 244), lambda dd: dd.rectangle([278, 246, 330, 258], fill=255), radius=3, bands=4, spec=True)
    L.shape((190, 40, 30), lambda dd: dd.ellipse([298, 246, 310, 254], fill=255), radius=4, bands=3, outline=0)
    sign(ImageDraw.Draw(L.im), (306, 90), 'WEIRD SAUCE', 18, (255, 212, 90))

    # ---------------------------------------------------------- Glutenous Truth + crochet shelf
    frame(L, (406, 68, 494, 184), inner=(46, 30, 72))
    L.shape((250, 206, 120), lambda dd: dd.ellipse([424, 100, 476, 152], fill=255), radius=24, bands=6, spec=True)
    for a in range(0, 360, 30):
        r = math.radians(a)
        L.line([(450 + 32 * math.cos(r), 126 + 32 * math.sin(r)), (450 + 40 * math.cos(r), 126 + 40 * math.sin(r))],
               (255, 236, 160), 2)
    box(L, 400, 216, 500, 226, 10, (130, 82, 50), radius=2)
    yarn = [(250, 220, 140), (240, 196, 110), (232, 120, 64), (130, 180, 84)]
    for i in range(6):
        bx = 406 + i * 16
        L.shape(yarn[i % 4], lambda dd, bx=bx: dd.ellipse([bx, 196, bx + 14, 216], fill=255), radius=6, bands=4)
        ImageDraw.Draw(L.im).arc([bx + 3, 199, bx + 11, 213], 0, 360, fill=rgba((150, 90, 60)))

    # ---------------------------------------------------------- the stained-glass flat
    sx0, sx1, sy0, sy1 = 512, 704, 28, 292
    L.shape((84, 60, 50), lambda dd: (dd.rectangle([sx0 - 8, sy0 + 48, sx1 + 8, sy1], fill=255),
                                      dd.pieslice([sx0 - 8, sy0 - 8, sx1 + 8, sy0 + 112], 180, 360, fill=255)),
            radius=6, bands=5)
    glass = Image.new('RGBA', size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glass)
    panes = [(70, 100, 200), (210, 60, 70), (246, 196, 70), (70, 160, 96), (150, 80, 186), (236, 128, 50)]
    for row, y in enumerate(range(sy0, sy1, 30)):
        for col, x in enumerate(range(sx0, sx1, 30)):
            c = panes[(row * 2 + col * 3) % len(panes)]
            c = tuple(int(c[i] * 0.45 + (70, 100, 200)[i] * 0.55) for i in range(3))
            gd.rectangle([x, y, x + 29, y + 29], fill=rgba(c))
    gd.rectangle([sx0, sy1 - 46, sx1, sy1], fill=rgba((60, 136, 70)))
    gd.ellipse([sx0 + 56, sy0 + 16, sx1 - 56, sy0 + 92], fill=rgba((250, 214, 96)))
    clip = mask_of(size, lambda dd: (dd.rectangle([sx0, sy0 + 52, sx1, sy1 - 2], fill=255),
                                     dd.pieslice([sx0, sy0, sx1, sy0 + 104], 180, 360, fill=255)))
    a = np.asarray(glass).copy()
    a[..., 3] = np.minimum(a[..., 3], np.asarray(clip))
    glass = Image.fromarray(a)
    edges = glass.convert('RGB').filter(ImageFilter.FIND_EDGES).convert('L').point(lambda v: 255 if v > 30 else 0)
    edges = Image.composite(edges, Image.new('L', size, 0), clip)
    glass.paste(Image.new('RGBA', size, (44, 36, 44, 255)), (0, 0), edges)
    # the Noodly One, in pale amber glass with a lead outline of its own
    mon = Image.new('RGBA', size, (0, 0, 0, 0))
    md = ImageDraw.Draw(mon)
    cx, cy = 608, 168
    for k in range(9):
        a_ = math.pi * (0.1 + 0.8 * k / 8)
        pts = [(cx + math.cos(a_ + 0.4 * math.sin(t * 3)) * t * 80, cy + 12 + math.sin(a_) * t * 100)
               for t in [i / 12 for i in range(13)]]
        md.line(pts, fill=rgba((252, 226, 150)), width=6, joint='curve')
    md.ellipse([cx - 32, cy - 20, cx + 32, cy + 28], fill=rgba((252, 226, 150)))
    for mx in (cx - 18, cx + 18):
        md.ellipse([mx - 14, cy - 8, mx + 14, cy + 20], fill=rgba((176, 84, 52)))
    for ex in (cx - 14, cx + 14):
        tx = ex + (ex - cx)
        md.line([(ex, cy - 20), (tx, cy - 52)], fill=rgba((252, 226, 150)), width=4)
        md.ellipse([tx - 10, cy - 64, tx + 10, cy - 44], fill=rgba((255, 255, 255)))
        md.ellipse([tx - 4, cy - 58, tx + 4, cy - 50], fill=rgba((20, 20, 30)))
    ma = mon.getchannel('A')
    ring = ma.filter(ImageFilter.MaxFilter(5))
    ring = Image.composite(ring, Image.new('L', size, 0), clip)
    glass.paste(Image.new('RGBA', size, (44, 36, 44, 255)), (0, 0), ring)
    glass.alpha_composite(mon)
    # light coming through: brighter towards the top, a sheen across it
    ga = np.asarray(glass, dtype=np.float32)
    yy = np.arange(H)[:, None]
    k = quantize(np.clip(1 - (yy - sy0) / (sy1 - sy0), 0, 1) * np.ones((1, W)), 5) * 0.25
    ga[..., :3] = ga[..., :3] * (1 - k[..., None]) + 255 * k[..., None]
    glass = Image.fromarray(np.clip(ga, 0, 255).astype(np.uint8))
    L.over(glass)

    # ---------------------------------------------------------- timeline
    box(L, 724, 80, 928, 232, 10, (110, 68, 40))
    box(L, 732, 88, 920, 112, 4, (66, 38, 24))
    sign(ImageDraw.Draw(L.im), (826, 100), 'TIMELINE', 18, (255, 212, 90))
    L.shape((250, 232, 186), lambda dd: dd.rectangle([742, 190, 906, 194], fill=255), radius=2, bands=3, outline=1)
    L.shape((250, 232, 186), lambda dd: dd.polygon([(906, 182), (920, 192), (906, 202)], fill=255), radius=3, bands=3,
            outline=1)
    ds = ImageDraw.Draw(L.im)
    sign(ds, (744, 208), 'OLDEST', 12, (246, 214, 150), anchor='la')
    sign(ds, (914, 208), 'NEWEST', 12, (246, 214, 150), anchor='ra')
    tiles = ['noodles', 'fork', 'string', 'counting']
    for i, kind in enumerate(tiles):
        tx = 742 + i * 44
        box(L, tx, 124, tx + 38, 176, 4, (250, 238, 210), radius=3)
        if kind == 'string':
            noodle(L, [(tx + 6, 168), (tx + 12, 140), (tx + 20, 164), (tx + 28, 134), (tx + 32, 156)],
                   (176, 120, 60), 3)
        elif kind == 'counting':
            L.shape((240, 230, 206), lambda dd, tx=tx: dd.rounded_rectangle([tx + 8, 132, tx + 30, 170], 6, fill=255),
                    radius=6, bands=4, outline=1)
            for y in range(138, 166, 6):
                L.line([(tx + 8, y), (tx + 16, y)], (80, 60, 50), 2)
        elif kind == 'noodles':
            L.shape((206, 80, 60), lambda dd, tx=tx: dd.chord([tx + 4, 140, tx + 34, 172], 0, 180, fill=255), radius=8,
                    bands=4, outline=1)
            for x in range(tx + 9, tx + 30, 6):
                ImageDraw.Draw(L.im).arc([x - 4, 134, x + 4, 158], 180, 360, fill=rgba((236, 196, 96)), width=2)
        else:
            L.shape((200, 204, 216), lambda dd, tx=tx: (dd.rectangle([tx + 17, 148, tx + 21, 170], fill=255),
                                                         dd.rectangle([tx + 9, 142, tx + 29, 148], fill=255),
                                                         [dd.rectangle([x, 130, x + 3, 146], fill=255) for x in (tx + 9, tx + 17, tx + 26)]),
                    radius=2, bands=4, spec=True, outline=1)
    box(L, 790, 232, 860, 248, 4, (80, 48, 30), radius=2)
    L.shape((236, 196, 90), lambda dd: dd.rectangle([818, 238, 832, 242], fill=255), radius=2, bands=3, outline=1)

    # ---------------------------------------------------------- sacred topology
    box(L, 952, 60, 1076, 232, 8, (90, 60, 40))
    L.shape((50, 76, 100), lambda dd: dd.rectangle([962, 70, 1066, 222], fill=255), radius=40, bands=5, outline=1)
    for i, (kx, ky) in enumerate(((988, 110), (1040, 146), (988, 186))):
        col = [(240, 220, 160), (230, 90, 70), (120, 190, 230)][i]
        if i == 1:
            pts = [(kx + 22 * math.sin(t), ky + 18 * math.sin(t) * math.cos(t)) for t in [j / 40 * math.tau for j in range(41)]]
        else:
            pts = [(kx + 8 * (math.sin(t) + 2 * math.sin(2 * t)) / 1.4, ky + 8 * (math.cos(t) - 2 * math.cos(2 * t)) / 1.4)
                   for t in [j / 50 * math.tau for j in range(51)]]
        noodle(L, pts, col, 4)
    ImageDraw.Draw(L.im).line([(966, 76), (1000, 76)], fill=rgba((160, 200, 230)), width=2)

    bg.alpha_composite(L.im)
    L = Layer(W, H)

    # ---------------------------------------------------------- left wall: paintings and the door
    def lwall_poly(x0, x1, y0, y1):
        # a rectangle on the left wall, skewed by the perspective
        k = 0.12
        return [(x0, y0 + (BL - x0) * k), (x1, y0 + (BL - x1) * k), (x1, y1 - (BL - x1) * k * 0.3),
                (x0, y1 - (BL - x0) * k * 0.3)]
    fl = lwall_poly(84, 170, 40, 120)
    L.shape((222, 176, 70), lambda dd: dd.polygon(fl, fill=255), radius=5, bands=5, spec=True)
    L.shape((70, 46, 60), lambda dd: dd.polygon(lwall_poly(94, 160, 52, 110), fill=255), radius=20, bands=5, outline=1)
    L.shape((244, 200, 160), lambda dd: dd.ellipse([110, 64, 144, 102], fill=255), radius=14, bands=5)
    L.shape((160, 40, 40), lambda dd: dd.ellipse([122, 84, 134, 96], fill=255), radius=4, bands=3, outline=1)
    noodle(L, [(100, 104), (116, 98), (128, 90)], width=3)
    # the Spinning Fork, mid-spin
    sf = lwall_poly(84, 176, 138, 258)
    L.shape((222, 176, 70), lambda dd: dd.polygon(sf, fill=255), radius=5, bands=5, spec=True)
    L.shape((40, 70, 96), lambda dd: dd.polygon(lwall_poly(94, 166, 150, 248), fill=255), radius=24, bands=5, outline=1)
    for r in range(8, 34, 6):
        ImageDraw.Draw(L.im).arc([130 - r, 200 - r * 0.8, 130 + r, 200 + r * 0.8], r * 9, r * 9 + 260,
                                 fill=rgba((252, 226, 150)), width=2)
    L.shape((210, 216, 226), lambda dd: dd.polygon([(128, 200), (134, 200), (140, 158), (136, 157)], fill=255),
            radius=2, bands=3, spec=True, outline=1)
    # the door you came in by
    door = [(0, 220), (74, 246), (74, 486), (0, 540)]
    L.shape((128, 80, 48), lambda dd: dd.polygon(door, fill=255), radius=8, bands=6)
    L.shape((146, 94, 58), lambda dd: dd.polygon([(8, 244), (64, 262), (64, 474), (8, 514)], fill=255), radius=8,
            bands=6, outline=1)
    L.shape((236, 196, 90), lambda dd: dd.ellipse([52, 360, 64, 374], fill=255), radius=5, bands=4, spec=True)
    L.shape((244, 240, 226), lambda dd: dd.polygon([(16, 280), (48, 290), (48, 322), (16, 312)], fill=255), radius=3,
            bands=4, outline=1)
    sign(ImageDraw.Draw(L.im), (32, 302), '913', 13, (60, 40, 40), shadow=(210, 200, 190))

    # ---------------------------------------------------------- right wall: archway (closed) and wardrobe
    arch = [(1100, 312), (1100, 116), (1112, 80), (1132, 60), (1156, 56), (1176, 68), (1188, 92), (1188, 400)]
    L.shape((196, 162, 116), lambda dd: dd.polygon(arch, fill=255), radius=10, bands=5, flat=0.4)
    inner = [(1108, 318), (1108, 120), (1118, 92), (1134, 74), (1154, 70), (1170, 80), (1180, 98), (1180, 392)]
    L.shape((190, 156, 112), lambda dd: dd.polygon(inner, fill=255), radius=4, bands=4, flat=0.8, outline=1,
            outline_color=(150, 120, 86))
    ward = [(1192, 60), (1280, 40), (1280, 560), (1192, 456)]
    L.shape((120, 74, 44), lambda dd: dd.polygon(ward, fill=255), radius=10, bands=6)
    L.shape((140, 88, 52), lambda dd: dd.polygon([(1202, 76), (1280, 60), (1280, 540), (1202, 448)], fill=255),
            radius=10, bands=6, outline=1)
    L.shape((236, 196, 90), lambda dd: dd.ellipse([1214, 220, 1226, 234], fill=255), radius=5, bands=4, spec=True)

    bg.alpha_composite(L.im)

    # ---------------------------------------------------------- floor furniture (with cast shadows)
    shadows = mask_of(size, lambda dd: (
        dd.polygon([(72, 470), (472, 440), (500, 520), (80, 556)], fill=255),           # sod table
        dd.ellipse([560, 452, 740, 500], fill=255),                                       # pedestal
        dd.polygon([(836, 452), (1080, 440), (1110, 500), (840, 520)], fill=255),        # spinner table
        dd.polygon([(924, 520), (1184, 506), (1220, 576), (930, 576)], fill=255),        # scales
        dd.ellipse([460, 540, 600, 576], fill=255)))                                      # side table
    bg = soft_shadow(bg, shadows, strength=0.5, blur=8, offset=(14, 8))
    L = Layer(W, H)

    # sod table with a tiny world
    top = [(88, 380), (452, 360), (472, 412), (72, 440)]
    L.shape((102, 64, 40), lambda dd: dd.polygon([(72, 440), (472, 412), (472, 444), (72, 476)], fill=255), radius=6,
            bands=5, flat=0.5)
    for lx in (84, 256, 448):
        ly = 476 - (lx - 72) * 32 / 400
        L.shape((88, 54, 34), lambda dd, lx=lx, ly=ly: dd.rectangle([lx, ly - 6, lx + 12, ly + 44], fill=255),
                radius=5, bands=4)
    L.shape((80, 150, 60), lambda dd: dd.polygon(top, fill=255), radius=10, bands=6, flat=0.5)
    dg = ImageDraw.Draw(L.im)
    grass = [(110, 184, 74), (70, 130, 50), (130, 200, 90)]
    for _ in range(2600):
        u, v = rnd.random(), rnd.random()
        x = (88 + 364 * u) * (1 - v) + (72 + 400 * u) * v
        y = (380 - 20 * u) * (1 - v) + (440 - 28 * u) * v
        dg.line([(x, y), (x + rnd.uniform(-1, 1), y - rnd.uniform(1, 4))], fill=rgba(rnd.choice(grass)))
    L.shape((96, 164, 70), lambda dd: dd.ellipse([124, 370, 210, 408], fill=255), radius=16, bands=5)
    L.shape((106, 172, 76), lambda dd: dd.ellipse([284, 362, 356, 394], fill=255), radius=14, bands=5)
    noodle(L, [(220, 428), (252, 404), (300, 412), (340, 392)], (206, 56, 44), 4)   # river of marinara
    for vx, vy in ((168, 410), (182, 416), (264, 392), (316, 410), (328, 404)):
        L.shape((246, 240, 226), lambda dd, vx=vx, vy=vy: dd.rectangle([vx, vy - 8, vx + 4, vy], fill=255), radius=2,
                bands=3, outline=1)
    box(L, 376, 372, 404, 392, 8, (244, 240, 230), radius=2)
    L.shape((206, 64, 54), lambda dd: dd.polygon([(372, 372), (392, 358), (410, 370)], fill=255), radius=3, bands=3,
            outline=1)
    # the audio-story handset
    L.shape((48, 44, 52), lambda dd: dd.rounded_rectangle([96, 392, 140, 414], 4, fill=255), radius=6, bands=4)
    L.shape((70, 66, 78), lambda dd: dd.rounded_rectangle([92, 378, 146, 392], 6, fill=255), radius=6, bands=5, spec=True)
    L.shape((190, 180, 160), lambda dd: dd.ellipse([110, 396, 126, 410], fill=255), radius=6, bands=3, outline=1)
    L.line([(140, 404), (156, 416), (150, 424)], (48, 44, 52), 2)
    # pamphlet holder with the pamphlet
    L.shape((210, 206, 196), lambda dd: dd.polygon([(412, 352), (448, 348), (452, 380), (416, 384)], fill=255), radius=4,
            bands=4, spec=True)
    L.shape((252, 248, 236), lambda dd: dd.polygon([(418, 344), (444, 340), (446, 372), (420, 376)], fill=255), radius=3,
            bands=3, outline=1)
    L.line([(422, 350), (440, 347)], (210, 60, 50), 2)
    for k in range(4):
        L.line([(422, 356 + k * 5), (440, 353 + k * 5)], (110, 110, 120), 1)

    # spaghetti sculpture on its plinth
    box(L, 584, 412, 696, 476, 12, (236, 232, 222))
    box(L, 576, 476, 704, 486, 10, (220, 214, 204), radius=2)
    sign(ImageDraw.Draw(L.im), (640, 446), 'SPAGHETTI', 13, (120, 110, 100), shadow=(250, 248, 240))
    sculpt = Layer(W, H)
    strands = []
    for k in range(46):
        a0 = rnd.uniform(0, math.tau)
        pts = []
        for i in range(36):
            t = i / 35
            yy = 404 - t * 150
            rad = 40 * (1 - t) + 18 + 10 * math.sin(t * 9 + k)
            pts.append((640 + rad * math.cos(a0 + t * 7), yy + 6 * math.sin(a0 + t * 7)))
        strands.append(pts)
    for pts in strands:
        col = rnd.choice([(250, 222, 140), (240, 206, 118), (230, 192, 104)])
        noodle(sculpt, pts, col, 3)
    for mx, my, r in ((616, 270, 13), (664, 274, 13), (640, 324, 12), (604, 366, 11), (680, 354, 11)):
        meatball(sculpt, mx, my, r)
    for ex, sx in ((602, -1), (678, 1)):
        noodle(sculpt, [(640 + sx * 20, 262), (ex, 236)], width=4)
        sculpt.shape((255, 255, 255), lambda dd, ex=ex: dd.ellipse([ex - 11, 218, ex + 11, 240], fill=255), radius=8,
                     bands=4, outline=2)
        ImageDraw.Draw(sculpt.im).ellipse([ex - 4 + 2, 225, ex + 4 + 2, 233], fill=rgba((24, 20, 30)))
    L.over(sculpt)

    # paragraph spinner cabinet on its table
    box(L, 836, 400, 1080, 418, 24, (128, 80, 48))
    for lx, ly in ((844, 418), (1066, 418), (954, 418)):
        L.shape((96, 60, 36), lambda dd, lx=lx, ly=ly: dd.rectangle([lx, ly, lx + 10, ly + 46], fill=255), radius=4,
                bands=4)
    box(L, 872, 248, 1040, 402, 14, (96, 60, 36))
    box(L, 872, 248, 1040, 274, 4, (66, 38, 24), radius=2)
    sign(ImageDraw.Draw(L.im), (956, 261), 'PARAGRAPH', 16, (255, 212, 90))
    words = ['THE', 'FORKS', 'SEEM', 'BLAND']
    for i, w in enumerate(words):
        y = 282 + i * 30
        L.shape((40, 24, 16), lambda dd, y=y: dd.rectangle([884, y - 2, 1028, y + 26], fill=255), radius=3, bands=3,
                outline=1)
        L.shape((248, 238, 216), lambda dd, y=y: dd.rectangle([888, y, 1024, y + 22], fill=255), radius=11, bands=6,
                outline=1, light=np.array([0.0, -0.9, 0.44]))
        sign(ImageDraw.Draw(L.im), (956, y + 11), w, 17, (50, 34, 30), shadow=(250, 240, 220))
        L.shape((216, 196, 130), lambda dd, y=y: dd.rectangle([1032, y + 4, 1046, y + 16], fill=255), radius=4, bands=4,
                spec=True, outline=1)

    # scales of pasta
    box(L, 924, 490, 1184, 508, 26, (128, 80, 48))
    for lx, ly in ((934, 508), (1170, 508)):
        L.shape((96, 60, 36), lambda dd, lx=lx, ly=ly: dd.rectangle([lx, ly, lx + 12, ly + 60], fill=255), radius=5, bands=4)
    gold = (232, 186, 72)
    L.shape(gold, lambda dd: dd.polygon([(1024, 488), (1080, 488), (1068, 474), (1036, 474)], fill=255), radius=6, bands=5,
            spec=True)
    L.shape(gold, lambda dd: dd.rectangle([1046, 380, 1058, 478], fill=255), radius=5, bands=5, spec=True)
    L.shape(gold, lambda dd: dd.polygon([(980, 398), (1124, 390), (1124, 396), (980, 404)], fill=255), radius=3, bands=4,
            spec=True)
    L.shape(gold, lambda dd: dd.ellipse([1042, 370, 1062, 390], fill=255), radius=8, bands=5, spec=True)
    for px, py in ((984, 401), (1120, 393)):
        L.line([(px, py), (px - 20, py + 46)], (190, 190, 200), 2)
        L.line([(px, py), (px + 20, py + 46)], (190, 190, 200), 2)
        L.shape(gold, lambda dd, px=px, py=py: dd.chord([px - 28, py + 34, px + 28, py + 62], 0, 180, fill=255), radius=8,
                bands=5, spec=True)
    for k in range(6):
        ImageDraw.Draw(L.im).arc([1104 + k * 5, 418 - (k % 2) * 6, 1116 + k * 5, 430 - (k % 2) * 6], 0, 300,
                                 fill=rgba((244, 204, 112)), width=3)
    box(L, 972, 424, 996, 436, 4, (160, 160, 172), radius=2)

    # side table with the puzzle box
    L.shape((120, 76, 46), lambda dd: dd.rectangle([514, 520, 530, 576], fill=255), radius=6, bands=4)
    L.shape((128, 80, 48), lambda dd: dd.ellipse([464, 502, 580, 530], fill=255), radius=10, bands=6, flat=0.4)
    box(L, 476, 466, 568, 508, 12, (164, 104, 54))
    for i, kind in enumerate(('penne', 'farfalle', 'shell')):
        bx = 490 + i * 26
        L.shape((70, 46, 30), lambda dd, bx=bx: dd.ellipse([bx, 476, bx + 20, 496], fill=255), radius=8, bands=3, outline=1)
        L.shape((196, 160, 96), lambda dd, bx=bx: dd.ellipse([bx + 2, 477, bx + 18, 493], fill=255), radius=7, bands=4,
                spec=True, outline=0)
        pc = rgba((252, 226, 150))
        db = ImageDraw.Draw(L.im)
        if kind == 'penne':
            db.polygon([(bx + 5, 489), (bx + 12, 480), (bx + 15, 482), (bx + 8, 491)], fill=pc)
        elif kind == 'farfalle':
            db.polygon([(bx + 4, 481), (bx + 10, 485), (bx + 16, 481), (bx + 16, 490), (bx + 10, 486), (bx + 4, 490)], fill=pc)
        else:
            db.chord([bx + 5, 480, bx + 15, 490], 0, 360, fill=pc)

    bg.alpha_composite(L.im)

    # ---------------------------------------------------------- light and finish
    bg = light_pool(bg, 600, 470, 520, 150, strength=0.18)
    bg = light_pool(bg, 620, 360, 150, 46, strength=0.16, color=(170, 190, 255))
    bg = light_pool(bg, 610, 160, 260, 200, strength=0.12, color=(255, 236, 190))
    bg = vignette(bg, 0.32)
    bg = wonky(bg, lean=0.045, sway=3.0)
    ImageDraw.Draw(bg).rectangle([0, VH, W, H], fill=(0, 0, 0, 255))
    return bg


def interface(im, words=None):
    """The verb strip at double size, as the game would draw it."""
    d = ImageDraw.Draw(im)
    d.rectangle([0, VH, W, H], fill=(12, 8, 18, 255))
    d.line([(0, VH), (W, VH)], fill=(90, 50, 64, 255), width=2)
    f = ImageFont.truetype(FONT, 22)
    d.fontmode = '1'
    sent = 'Talk to Khuc'
    d.text((W // 2, VH + 18), sent, font=f, fill=(150, 236, 236, 255), anchor='mm')
    verbs = [['Open', 'Pick up', 'Push'], ['Close', 'Look at', 'Pull'], ['Talk to', 'Use', 'Walk to']]
    for r, row in enumerate(verbs):
        for c, v in enumerate(row):
            col = (160, 248, 248) if v == 'Talk to' else (48, 168, 168)
            d.text((36 + c * 192, VH + 64 + r * 54), v, font=f, fill=rgba(col))
    for n in range(8):
        x = 632 + (n % 4) * 156
        y = VH + 44 + (n // 4) * 88
        d.rectangle([x + 4, y + 2, x + 150, y + 84], fill=(30, 22, 40, 255))
    return im
