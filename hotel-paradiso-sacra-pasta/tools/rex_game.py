"""T. REX RUN, the arcade game in the Crypt's T. Rex cabinet: a three-lane runner seen from behind
the T. Rex. Boulders, cycads and low-flying pterodactyls come down the jungle track, and then the
sky goes red and the meteors start to fall.

Drawn like MEATBALL MADNESS: flat colours, hard edges and 2x2 ordered dither, at half size and
doubled. The game itself is in src/game.asc (RexGame); this makes its sprites.

Geometry (before doubling): the play area is 320x144, the horizon is at HY, and the track runs
from TRACK_FAR at the horizon to TRACK_NEAR at the bottom, three lanes wide. Everything on the
track is drawn at its full size (as it is at the bottom of the screen) and the game scales it
down by how far up the screen it is.
"""
import math
import random
from PIL import Image, ImageDraw

S = 2
W, H = 320, 144
HY = 44                                     # the horizon
TRACK_NEAR = (40, 280)                      # the track's edges at the bottom of the screen
TRACK_FAR = (152, 168)                      # ... and at the horizon

P = {
    'sky_hi': (54, 46, 104), 'sky': (112, 70, 130), 'sky_lo': (236, 140, 100), 'sun': (252, 214, 130),
    'red_hi': (60, 14, 22), 'red': (150, 32, 30), 'red_lo': (246, 120, 50),
    'volcano': (70, 44, 60), 'volcano_dk': (46, 28, 44), 'lava': (252, 120, 40), 'lava_hi': (255, 214, 110),
    'smoke': (120, 98, 120), 'smoke_hi': (156, 132, 150),
    'far': (52, 90, 70), 'far_dk': (36, 66, 52),
    'grass': (88, 150, 64), 'grass_dk': (78, 138, 58), 'grass_hi': (130, 186, 84),
    'dirt': (178, 124, 74), 'dirt_dk': (150, 100, 58), 'dirt_hi': (206, 156, 100), 'line': (236, 214, 160),
    'leaf': (60, 132, 66), 'leaf_dk': (34, 92, 50), 'leaf_hi': (110, 176, 84), 'trunk': (118, 80, 50), 'trunk_dk': (82, 54, 34),
    'rex': (84, 150, 72), 'rex_dk': (50, 104, 52), 'rex_hi': (136, 196, 100), 'rex_belly': (200, 214, 140),
    'claw': (240, 236, 220), 'eye': (255, 230, 90),
    'rock': (138, 130, 124), 'rock_dk': (92, 86, 84), 'rock_hi': (182, 176, 166),
    'ptero': (176, 92, 70), 'ptero_dk': (120, 56, 46), 'ptero_hi': (226, 150, 110), 'wing': (210, 120, 88),
    'meteor': (110, 70, 56), 'fire': (252, 150, 40), 'fire_hi': (255, 236, 140), 'fire_dk': (214, 64, 30),
    'crater': (60, 40, 36), 'shadow': (40, 26, 30), 'heart': (232, 50, 70), 'heart_dk': (150, 20, 40),
    'ink': (24, 16, 22), 'white': (255, 255, 255),
}


def big(im):
    return im.resize((im.width * S, im.height * S), Image.NEAREST)


def canvas(w, h):
    return Image.new('RGBA', (w, h), (0, 0, 0, 0))


def dither(px, x0, y0, x1, y1, a, b, level):
    bayer = [[0, 2], [3, 1]]
    for y in range(y0, y1):
        for x in range(x0, x1):
            px[x, y] = P[b] + (255,) if bayer[y % 2][x % 2] < level else P[a] + (255,)


def edges(y):
    """The track's left and right edge at row y (y >= HY)."""
    u = (y - HY) / (H - HY)
    return (TRACK_FAR[0] + (TRACK_NEAR[0] - TRACK_FAR[0]) * u, TRACK_FAR[1] + (TRACK_NEAR[1] - TRACK_FAR[1]) * u)


# ------------------------------------------------------------------ the sky (two of them)
def sky(red=False):
    im = Image.new('RGBA', (W, HY + 2), P['sky'] + (255,))
    px = im.load()
    hi, mid, lo = ('red_hi', 'red', 'red_lo') if red else ('sky_hi', 'sky', 'sky_lo')
    for y in range(HY + 2):
        if y < 22:
            dither(px, 0, y, W, y + 1, hi, mid, round(4 * y / 22))
        else:
            dither(px, 0, y, W, y + 1, mid, lo, min(4, round(4 * (y - 22) / 20)))
    d = ImageDraw.Draw(im)
    if not red:
        d.ellipse([214, 18, 246, 50], fill=P['sun'])
    else:
        # streaks of meteors already in the sky
        for x, y, l in ((40, 6, 14), (110, 14, 10), (230, 4, 18), (286, 16, 9)):
            d.line([(x, y), (x + l, y + l // 2)], fill=P['fire_hi'])
            d.point((x + l, y + l // 2), fill=P['white'])
    # the volcano, smoking
    d.polygon([(72, HY + 1), (104, 16), (118, 16), (154, HY + 1)], fill=P['volcano'])
    d.polygon([(110, 16), (118, 16), (154, HY + 1), (132, HY + 1)], fill=P['volcano_dk'])
    d.rectangle([104, 14, 118, 17], fill=P['lava'])
    d.line([(108, 18), (100, 30)], fill=P['lava'])
    d.line([(114, 18), (120, 32)], fill=P['lava'])
    d.point((110, 15), fill=P['lava_hi'])
    for k, (x, y, r) in enumerate(((108, 8, 5), (114, 3, 6), (104, 0, 4), (122, -2, 5))):
        d.ellipse([x - r, y - r, x + r, y + r], fill=P['smoke_hi'] if k % 2 else P['smoke'])
    # a far line of jungle along the horizon
    for x in range(W):
        h = 3 + 2 * math.sin(x / 5) + 2 * math.sin(x / 13 + 1)
        d.line([(x, HY + 1 - h), (x, HY + 1)], fill=P['far'])
        if x % 3 == 0:
            d.point((x, HY + 1), fill=P['far_dk'])
    return im


# ------------------------------------------------------------------ the ground, four frames of motion
def ground(phase):
    """The track and the grass either side, from the horizon down (320 x 100). `phase` 0..3
    moves the stripes towards you, so cycling the frames looks like running."""
    gh = H - HY
    im = Image.new('RGBA', (W, gh), (0, 0, 0, 255))
    px = im.load()
    for yy in range(gh):
        y = HY + yy
        # depth of this row; stripes are evenly spaced in depth, so they bunch up near the horizon
        z = 60.0 / max(0.6, y - HY + 0.6)
        band = int(z * 8 + phase * 0.5) % 2
        l, r = edges(y)
        lane_w = (r - l) / 3
        for x in range(W):
            if l <= x < r:
                c = 'dirt' if band else 'dirt_dk'
                # the lane lines: dashed, on the bands
                for k in (1, 2):
                    lx = l + lane_w * k
                    if abs(x - lx) < max(0.5, lane_w * 0.035) and band:
                        c = 'line'
                # pebbles near the edges
                if x - l < lane_w * 0.08 or r - x <= lane_w * 0.08:
                    c = 'dirt_hi'
            else:
                c = 'grass' if band else 'grass_dk'
            px[x, yy] = P[c] + (255,)
    return im


def jungle_side(flip=False):
    """Big ferns and a palm at the edge of the picture, in front of the grass (static)."""
    im = canvas(70, H)
    d = ImageDraw.Draw(im)
    # palm trunk
    for y in range(20, H):
        x = 18 + int(6 * math.sin(y / 30))
        d.line([(x, y), (x + 7, y)], fill=P['trunk'])
        if y % 5 == 0:
            d.line([(x, y), (x + 7, y)], fill=P['trunk_dk'])
    cx, cy = 22, 20
    for a in (-170, -140, -110, -70, -40, -10, 20):
        ar = math.radians(a)
        for t in range(0, 40):
            x = cx + t * math.cos(ar)
            y = cy + t * math.sin(ar) + (t * t) / 70
            w = max(1, int(5 - t / 10))
            d.ellipse([x - w, y - w / 2, x + w, y + w / 2], fill=P['leaf'] if t % 6 < 4 else P['leaf_dk'])
    # ferns at the foot
    for k, x0 in enumerate((0, 20, 38)):
        base = H - 2
        for a in range(-160, -15, 18):
            ar = math.radians(a)
            l = 22 + (k * 7) % 10
            pts = [(x0 + 10 + t * math.cos(ar), base - 30 + k * 6 + t * math.sin(ar) + t * t / 40) for t in range(0, l, 2)]
            d.line(pts, fill=P['leaf_hi'] if k == 1 else P['leaf'], width=2)
    if flip:
        im = im.transpose(Image.FLIP_LEFT_RIGHT)
    return im


# ------------------------------------------------------------------ the T. Rex, from behind
def poly(d, pts, fill, outline=None):
    d.polygon(pts, fill=fill)
    if outline:
        d.line(pts + [pts[0]], fill=outline)


def thighs(d, cx, frame, lift, col, dk, hi, claw, H=54, spread=11):
    """Big drumstick thighs either side of the hips, legs pumping."""
    left_up = frame in (0, 1)
    for side, up in ((-1, left_up), (1, not left_up)):
        x = cx + side * spread
        knee = 40 - lift - (3 if up else 0)
        foot = H - 1 - (6 if up else 0)
        # shin and foot first (behind the thigh)
        d.polygon([(x - 3, knee), (x + 3, knee), (x + 2, foot - 2), (x - 2, foot - 2)], fill=dk)
        d.rectangle([x - 5, foot - 3, x + 5, foot], fill=dk)
        if up:
            d.line([(x - 4, foot), (x + 4, foot)], fill=claw)
        else:
            for cxx in (x - 4, x, x + 4):
                d.point((cxx, foot), fill=claw)
        # the thigh: a drumstick, wide at the hip
        d.polygon([(x - 8, 28 - lift), (x + 8, 28 - lift), (x + 5, knee + 2), (x - 4, knee + 2)], fill=dk)
        d.polygon([(x - 7, 28 - lift), (x + 6, 28 - lift), (x + 4, knee), (x - 3, knee)], fill=col)
        d.line([(x - 5 * side, 30 - lift), (x - 3 * side, knee - 2)], fill=hi if side < 0 else dk)


def rex(frame):
    """56x54, running away from us: one body seen three-quarters from behind, the tail swinging
    towards us and the head turned back in profile to look over its shoulder. Four frames."""
    G, D, Hh = P['rex'], P['rex_dk'], P['rex_hi']
    im = canvas(56, 54)
    d = ImageDraw.Draw(im)
    lift = (0, 1, 0, 1)[frame]
    sw = (-1, 0, 1, 0)[frame]
    thighs(d, 30, frame, lift, G, D, Hh, P['claw'], spread=10)
    # one continuous body: tail tip (near, bottom) -> hips -> back -> neck -> head (left, turned)
    body = [(30 + sw * 7, 52), (24, 34 - lift), (18, 26 - lift), (16, 18 - lift), (20, 12 - lift),
            (28, 10 - lift), (38, 14 - lift), (44, 22 - lift), (44, 32 - lift), (36, 36 - lift)]
    poly(d, body, G, D)
    d.polygon([(30 + sw * 7, 52), (24, 34 - lift), (18, 26 - lift), (21, 26 - lift), (27, 34 - lift)], fill=D)
    d.line([(38, 16 - lift), (42, 26 - lift)], fill=Hh)
    for k, y in enumerate(range(12, 44, 5)):
        x = 30 + int(sw * 7 * max(0, y - 34) / 18) + (0 if y > 30 else int((30 - y) * 0.2))
        d.point((x, y - lift), fill=D)
        d.point((x, y - lift - 1), fill=D)
    # neck curling round, and the head in profile facing left (looking back over the shoulder)
    poly(d, [(18, 14 - lift), (22, 10 - lift), (20, 4 - lift), (14, 6 - lift)], G, D)
    hx, hy = 0, -1 - lift
    head = [(hx + 2, hy + 6), (hx + 6, hy + 3), (hx + 18, hy + 2), (hx + 23, hy + 5), (hx + 23, hy + 11), (hx + 18, hy + 14), (hx + 3, hy + 13), (hx, hy + 10)]
    poly(d, head, G, D)
    d.polygon([(hx + 3, hy + 13), (hx + 18, hy + 14), (hx + 23, hy + 11), (hx + 20, hy + 11), (hx + 2, hy + 11)], fill=D)
    d.line([(hx + 1, hy + 10), (hx + 19, hy + 10)], fill=P['ink'])
    for x in range(hx + 2, hx + 17, 3):
        d.point((x, hy + 9), fill=P['claw'])
        d.point((x + 1, hy + 11), fill=P['claw'])
    d.point((hx + 4, hy + 5), fill=P['ink'])
    d.rectangle([hx + 15, hy + 4, hx + 16, hy + 5], fill=P['eye'])
    d.point((hx + 16, hy + 5), fill=P['ink'])
    d.line([(hx + 13, hy + 3), (hx + 18, hy + 3)], fill=D)
    # the tiny arm
    d.line([(17, 20 - lift), (12, 23 - lift), (13, 25 - lift)], fill=D, width=2)
    return im


# ------------------------------------------------------------------ things on the track (full size)
def boulder():
    im = canvas(40, 30)
    d = ImageDraw.Draw(im)
    d.ellipse([0, 4, 39, 30], fill=P['rock_dk'])
    d.ellipse([1, 2, 36, 27], fill=P['rock'])
    d.ellipse([6, 5, 18, 12], fill=P['rock_hi'])
    d.line([(22, 10), (27, 18), (24, 24)], fill=P['rock_dk'])
    d.line([(10, 18), (15, 22)], fill=P['rock_dk'])
    d.ellipse([2, 26, 38, 30], fill=P['shadow'])
    return im


def cycad():
    """A spiky cycad bush: 44x36."""
    im = canvas(44, 36)
    d = ImageDraw.Draw(im)
    d.ellipse([10, 30, 34, 36], fill=P['shadow'])
    d.rectangle([18, 20, 26, 33], fill=P['trunk'])
    for k in range(0, 26, 3):
        d.line([(18, 20 + k // 2), (26, 20 + k // 2)], fill=P['trunk_dk'])
    for a in range(-180, 1, 20):
        ar = math.radians(a)
        pts = [(22 + t * math.cos(ar), 20 + t * math.sin(ar) * 0.9 + t * t / 60) for t in range(0, 22, 2)]
        d.line(pts, fill=P['leaf_dk'] if (a // 20) % 2 else P['leaf'], width=3)
        x, y = pts[-1]
        d.point((x, y), fill=P['leaf_hi'])
    return im


def ptero(frame):
    """A pterodactyl skimming the ground towards us: 56x30, two frames of flapping."""
    im = canvas(56, 30)
    d = ImageDraw.Draw(im)
    d.ellipse([16, 25, 40, 30], fill=P['shadow'])
    up = frame == 0
    wy = 2 if up else 16
    # wings
    d.polygon([(26, 12), (0, wy), (6, wy + 4), (24, 16)], fill=P['wing'])
    d.polygon([(30, 12), (55, wy), (49, wy + 4), (32, 16)], fill=P['wing'])
    d.line([(26, 12), (0, wy)], fill=P['ptero_dk'])
    d.line([(30, 12), (55, wy)], fill=P['ptero_dk'])
    # body and head (coming at us, so mostly the head and that crest)
    d.ellipse([22, 8, 34, 20], fill=P['ptero'])
    d.polygon([(25, 10), (28, 0), (31, 10)], fill=P['ptero_dk'])
    d.polygon([(25, 15), (28, 23), (31, 15)], fill=P['ptero_hi'])
    d.point((25, 12), fill=P['eye'])
    d.point((31, 12), fill=P['eye'])
    return im


def crater(frame):
    """Where a meteor came down: a smoking hole with fire round it, 48x22, two frames."""
    im = canvas(48, 22)
    d = ImageDraw.Draw(im)
    d.ellipse([0, 8, 47, 22], fill=P['dirt_dk'])
    d.ellipse([5, 10, 42, 20], fill=P['crater'])
    rnd = random.Random(7 + frame)
    for k in range(9):
        x = 4 + k * 5 + rnd.randint(-1, 1)
        h = rnd.randint(6, 14)
        y = 13 + int(4 * math.sin(k))
        d.polygon([(x - 3, y), (x, y - h), (x + 3, y)], fill=P['fire'])
        d.polygon([(x - 1, y), (x, y - h // 2), (x + 1, y)], fill=P['fire_hi'])
    d.ellipse([18, 12, 30, 17], fill=P['meteor'])
    d.point((22, 13), fill=P['fire_hi'])
    return im


def meteor(frame):
    """A falling meteor with its fiery tail above it: 26x46, two frames."""
    im = canvas(26, 46)
    d = ImageDraw.Draw(im)
    rnd = random.Random(3 + frame)
    for k in range(14):
        y = 30 - k * 2
        w = max(1, 8 - k // 2 + rnd.randint(-1, 1))
        x = 13 + rnd.randint(-1, 1)
        d.ellipse([x - w, y - 2, x + w, y + 2], fill=P['fire_dk'] if k > 8 else P['fire'])
    d.ellipse([5, 28, 21, 44], fill=P['fire_hi'])
    d.ellipse([7, 30, 19, 42], fill=P['meteor'])
    d.point((10, 33), fill=P['fire_hi'])
    d.point((15, 38), fill=P['fire'])
    return im


def target():
    """The warning on the track where a meteor's going to land: 48x14."""
    im = canvas(48, 14)
    d = ImageDraw.Draw(im)
    d.ellipse([0, 0, 47, 13], outline=P['fire_dk'], width=2)
    d.ellipse([10, 3, 37, 10], outline=P['fire'])
    d.line([(23, 0), (23, 13)], fill=P['fire_dk'])
    d.line([(0, 6), (47, 6)], fill=P['fire_dk'])
    return im


def heart(full=True):
    im = canvas(9, 8)
    d = ImageDraw.Draw(im)
    c = P['heart'] if full else P['ink']
    o = P['heart_dk'] if full else P['heart_dk']
    for (x, y) in ((1, 0), (2, 0), (5, 0), (6, 0)):
        pass
    pts = ['.XX.XX...', 'XXXXXXX..', 'XXXXXXX..', '.XXXXX...', '..XXX....', '...X.....']
    for y, row in enumerate(pts):
        for x, ch in enumerate(row):
            if ch == 'X':
                im.putpixel((x + 1, y + 1), c + (255,))
    for y in range(8):
        for x in range(9):
            if im.getpixel((x, y))[3] == 0:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    xx, yy = x + dx, y + dy
                    if 0 <= xx < 9 and 0 <= yy < 8 and im.getpixel((xx, yy))[:3] == c and im.getpixel((xx, yy))[3]:
                        im.putpixel((x, y), o + (255,))
                        break
    if full:
        im.putpixel((2, 2), (255, 180, 190, 255))
    return im


def arrow(left):
    """A hint arrow for the click-left / click-right controls: 14x14."""
    im = canvas(14, 14)
    d = ImageDraw.Draw(im)
    pts = [(12, 1), (2, 7), (12, 13)] if left else [(1, 1), (11, 7), (1, 13)]
    d.polygon(pts, fill=(255, 255, 255, 150), outline=(20, 10, 24, 200))
    return im


def dir_arrow(left, bright):
    """The big arrow beside the T. Rex showing which way a click will take it: 26x22.
    Two brightnesses: resting, and the moment of the click."""
    im = canvas(26, 22)
    d = ImageDraw.Draw(im)
    pts = [(1, 11), (12, 1), (12, 6), (24, 6), (24, 16), (12, 16), (12, 21)]
    if not left:
        pts = [(25 - x, y) for x, y in pts]
    fill = (255, 236, 120, 255) if bright else (255, 214, 90, 200)
    d.polygon(pts, fill=fill, outline=(40, 20, 16, 255))
    d.line([pts[1], pts[2]] if left else [pts[1], pts[2]], fill=(255, 255, 220, 255))
    return im


def cursor():
    """A pointer that shows up on any background: 11x11 crosshair ring, white with a dark edge."""
    im = canvas(11, 11)
    d = ImageDraw.Draw(im)
    d.ellipse([1, 1, 9, 9], outline=(20, 10, 24, 255), width=3)
    d.ellipse([2, 2, 8, 8], outline=(255, 255, 255, 255))
    d.point((5, 5), fill=(255, 255, 255, 255))
    return im


# ------------------------------------------------------------------ the victory screen
def rot(pts, cx, cy, deg):
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    return [(cx + (x - cx) * c - (y - cy) * s, cy + (x - cx) * s + (y - cy) * c) for x, y in pts]


def tf(pts, ox, oy, k, flip=False):
    out = []
    for x, y in pts:
        if flip:
            x = 146 - x
        out.append((ox + x * k, oy + y * k))
    return out


def rex_profile(d, ox, oy, k=1.0, pose='roar', cols=None, flip=False, stride=0):
    """Draws the T. Rex facing right with its feet on y = oy + 80*k. 146*k wide.
    pose: 'roar' (head thrown up, jaws wide), 'stand' (jaws shut), 'run' (leaning forward)."""
    G, D, Hh, B = cols or (P['rex'], P['rex_dk'], P['rex_hi'], (170, 200, 120))
    T = lambda pts: tf(pts, ox, oy, k, flip)
    lean = -6 if pose == 'run' else 0
    body_pts = [(0, 40), (28, 31), (60, 24), (80, 23), (96, 26), (104, 30),
                (106, 40), (100, 48), (88, 53), (72, 54), (58, 50), (30, 45), (0, 42)]
    body_pts = rot(body_pts, 70, 50, lean)
    # far leg, behind everything (darker), swung opposite to the near one
    s = stride
    far = [(66, 34), (80, 34), (82, 48), (74 - s, 60), (70 - s, 74), (64 - s, 74), (66 - s, 58), (62, 46)]
    far_foot = [(58 - s, 74), (78 - s, 74), (80 - s, 80), (56 - s, 80)]
    d.polygon(T(rot(far, 70, 50, lean)), fill=D)
    d.polygon(T(far_foot), fill=D)
    # body and tail
    d.polygon(T(body_pts), fill=G, outline=D)
    # back stripe and belly light
    d.line(T(rot([(20, 35), (60, 27), (90, 27)], 70, 50, lean)), fill=D, width=max(1, int(k)))
    d.line(T(rot([(60, 50), (86, 50), (98, 46)], 70, 50, lean)), fill=B, width=max(1, int(k)))
    for x in range(30, 96, 9):                      # a few stripes across the back
        p = rot([(x, 27 + (6 if x < 50 else 0) * (50 - x) / 20), (x + 4, 33)], 70, 50, lean)
        d.line(T(p), fill=D)
    # neck and head
    pivot = rot([(104, 30)], 70, 50, lean)[0]
    head = [(100, 26), (108, 16), (122, 11), (140, 13), (147, 18), (146, 23), (128, 26), (112, 30), (104, 34)]
    jaw = [(110, 30), (126, 27), (144, 26), (142, 30), (128, 33), (114, 36)]
    hdeg = {'roar': -28, 'stand': -4, 'run': 4}[pose]
    jaw_open = {'roar': 26, 'stand': 0, 'run': 8}[pose]
    head = rot([(x, y + (rot([(0, 0)], 0, 0, 0)[0][1])) for x, y in head], 70, 50, lean)
    jaw = rot(jaw, 70, 50, lean)
    head = rot(head, pivot[0], pivot[1], hdeg)
    jaw = rot(rot(jaw, 112, 31, jaw_open), pivot[0], pivot[1], hdeg)
    d.polygon(T(jaw), fill=G, outline=D)
    if jaw_open:
        # the inside of the mouth, between the jaws
        mouth = [head[6], head[5], jaw[2], jaw[1]]
        d.polygon(T(mouth), fill=(120, 26, 36))
        for t in range(5):                           # teeth along both jaws
            u = 0.2 + t * 0.17
            ux = head[6][0] + (head[5][0] - head[6][0]) * u
            uy = head[6][1] + (head[5][1] - head[6][1]) * u
            lx = jaw[1][0] + (jaw[2][0] - jaw[1][0]) * u
            ly = jaw[1][1] + (jaw[2][1] - jaw[1][1]) * u
            d.polygon(T([(ux - 1, uy), (ux + 1, uy), (ux, uy + 2.5)]), fill=P['claw'])
            d.polygon(T([(lx - 1, ly), (lx + 1, ly), (lx, ly - 2.5)]), fill=P['claw'])
    d.polygon(T(head), fill=G, outline=D)
    # neck filling the gap between head and shoulders
    d.polygon(T([rot([(98, 28)], 70, 50, lean)[0], head[1], head[0], jaw[5], rot([(106, 42)], 70, 50, lean)[0]]), fill=G)
    # eye, brow, nostril
    e = rot(rot([(124, 16)], 70, 50, lean), pivot[0], pivot[1], hdeg)[0]
    br = rot(rot([(119, 13), (128, 13)], 70, 50, lean), pivot[0], pivot[1], hdeg)
    n = rot(rot([(142, 16)], 70, 50, lean), pivot[0], pivot[1], hdeg)[0]
    ex, ey = T([e])[0]
    d.rectangle([ex - k * 0.8, ey - k * 0.8, ex + k * 0.8, ey + k * 0.8], fill=P['eye'])
    d.point((ex + k * 0.5, ey), fill=P['ink'])
    d.line(T(br), fill=D, width=max(1, int(k)))
    nx, ny = T([n])[0]
    d.point((nx, ny), fill=P['ink'])
    # the tiny arm
    arm = rot([(100, 42), (106, 48), (110, 47)], 70, 50, lean)
    if pose == 'roar':
        arm = rot([(100, 42), (106, 46), (109, 42)], 70, 50, lean)
    d.line(T(arm), fill=D, width=max(1, int(1.5 * k)))
    # near leg: big drumstick thigh, shin, foot with claws
    near = [(60, 30), (82, 30), (86, 44), (80 + s, 56), (84 + s, 72), (78 + s, 74), (72 + s, 58), (64, 50)]
    d.polygon(T(rot(near, 70, 50, lean)), fill=G, outline=D)
    d.line(T(rot([(66, 34), (78, 34)], 70, 50, lean)), fill=Hh)
    foot = [(74 + s, 74), (94 + s, 74), (96 + s, 80), (72 + s, 80)]
    d.polygon(T(foot), fill=G, outline=D)
    for cx in (90, 94):
        x, y = T([(cx + s, 80)])[0]
        d.point((x, y), fill=P['claw'])


def _vsky(px, top, mid, low, y1=40, y2=100):
    for y in range(H):
        if y < y1:
            dither(px, 0, y, W, y + 1, top, mid, round(4 * y / y1))
        else:
            dither(px, 0, y, W, y + 1, mid, low, min(4, round(4 * (y - y1) / (y2 - y1))))


def _streaks(d, pts, col=None):
    for x, y, l in pts:
        d.line([(x, y), (x + l, y + l // 2)], fill=col or P['fire'])
        d.point((x + l, y + l // 2), fill=P['white'])


# --- A: roaring on the rock at sunrise (the same scene as now, new T. Rex)


def victory():
    im = Image.new('RGBA', (W, H), (0, 0, 0, 255))
    _vsky(im.load(), 'red', 'red_lo', 'sun', 50, 120)
    d = ImageDraw.Draw(im)
    d.ellipse([88, 14, 232, 158], fill=P['fire_hi'])
    for y in range(40, 140, 7):                     # bands across the sun
        d.line([(80, y), (240, y)], fill=P['sun'])
    _streaks(d, [(20, 14, 16), (250, 8, 20), (286, 34, 12), (40, 44, 10)], P['fire_hi'])
    ink = (30, 14, 20)
    for x in range(W):
        h = 18 + 6 * math.sin(x / 11) + 3 * math.sin(x / 5 + 1)
        d.line([(x, H - h), (x, H)], fill=ink)
    for x0 in (14, 40, 280, 304):                    # palm silhouettes
        d.line([(x0, H - 20), (x0 + 3, H - 64)], fill=ink, width=3)
        for a in (-160, -125, -90, -55, -20):
            ar = math.radians(a)
            pts = [(x0 + 3 + t * math.cos(ar), H - 64 + t * math.sin(ar) + t * t / 40) for t in range(0, 20, 2)]
            d.line(pts, fill=ink, width=2)
    rex_profile(d, 86, 44, 0.98, 'roar', cols=(ink, ink, ink, ink))
    return im


# --- C: striding away from a smoking crater, looking pleased with itself


def sprites():
    """{sprite name: image}, all doubled."""
    out = {'rex_sky': big(sky(False)), 'rex_skyred': big(sky(True)),
           'rex_side_l': big(jungle_side(False)), 'rex_side_r': big(jungle_side(True)),
           'rex_boulder': big(boulder()), 'rex_cycad': big(cycad()),
           'rex_ptero0': big(ptero(0)), 'rex_ptero1': big(ptero(1)),
           'rex_crater0': big(crater(0)), 'rex_crater1': big(crater(1)),
           'rex_meteor0': big(meteor(0)), 'rex_meteor1': big(meteor(1)),
           'rex_target': big(target()), 'rex_heart': big(heart(True)), 'rex_heartx': big(heart(False)),
           'rex_arrow_l': big(arrow(True)), 'rex_arrow_r': big(arrow(False)),
           'rex_dir_l': big(dir_arrow(True, False)), 'rex_dir_r': big(dir_arrow(False, False)),
           'rex_dir_l_on': big(dir_arrow(True, True)), 'rex_dir_r_on': big(dir_arrow(False, True)),
           'rex_cursor': big(cursor()), 'rex_victory': big(victory())}
    for k in range(4):                       # numbered in order: the game adds 0..3 to the first
        out['rex_ground%d' % k] = big(ground(k))
    for k in range(4):
        out['rex_run%d' % k] = big(rex(k))
    return out


NAMES = ['rex_sky', 'rex_skyred', 'rex_side_l', 'rex_side_r', 'rex_ground0', 'rex_ground1', 'rex_ground2',
         'rex_ground3', 'rex_run0', 'rex_run1', 'rex_run2', 'rex_run3', 'rex_boulder', 'rex_cycad', 'rex_ptero0',
         'rex_ptero1', 'rex_crater0', 'rex_crater1', 'rex_meteor0', 'rex_meteor1', 'rex_target', 'rex_heart',
         'rex_heartx', 'rex_arrow_l', 'rex_arrow_r', 'rex_dir_l', 'rex_dir_r', 'rex_dir_l_on', 'rex_dir_r_on',
         'rex_cursor', 'rex_victory']


def preview(path, red=False, phase=0):
    """A mock-up of one frame of the game, for checking the art."""
    sp = {k: v for k, v in sprites().items()}
    im = Image.new('RGBA', (640, 288))
    im.alpha_composite(sp['rex_skyred' if red else 'rex_sky'], (0, 0))
    im.alpha_composite(sp['rex_ground%d' % phase], (0, HY * 2))
    im.alpha_composite(sp['rex_side_l'], (0, 0))
    im.alpha_composite(sp['rex_side_r'], (640 - sp['rex_side_r'].width, 0))

    def put(name, lane, y):
        s = sp[name]
        u = (y / 2 - HY) / (H - HY)
        l, r = edges(y / 2)
        cx = (l + (r - l) * (lane + 0.5) / 3) * 2
        w, h = max(1, int(s.width * u)), max(1, int(s.height * u))
        im.alpha_composite(s.resize((w, h), Image.NEAREST), (int(cx - w / 2), int(y - h)))
    put('rex_boulder', 0, 140)
    put('rex_cycad', 2, 180)
    put('rex_ptero0', 1, 120)
    if red:
        put('rex_crater0', 2, 230)
        put('rex_target', 0, 200)
        im.alpha_composite(sp['rex_meteor0'], (100, 40))
    put('rex_run0', 1, 284)
    for k in range(3):
        im.alpha_composite(sp['rex_heart'], (16 + k * 22, 40))
    im.save(path)


if __name__ == '__main__':
    preview('/tmp/claude-0/rex_prev.png')
    preview('/tmp/claude-0/rex_prev_red.png', True, 2)
