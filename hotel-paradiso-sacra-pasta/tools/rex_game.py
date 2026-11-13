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
def rex(frame):
    """44x46, running away from us: four frames (legs and tail swap sides)."""
    im = canvas(44, 46)
    d = ImageDraw.Draw(im)
    sw = (-1, 0, 1, 0)[frame]                # tail sway
    lift = (0, 1, 0, 1)[frame]               # body bob
    left_up = frame in (0, 1)
    # legs: big thighs, one lifted
    for side, up in ((-1, left_up), (1, not left_up)):
        x = 22 + side * 9
        top = 26 - lift
        foot = 44 - (5 if up else 0)
        d.ellipse([x - 7, top, x + 7, top + 14], fill=P['rex_dk'])
        d.ellipse([x - 6, top, x + 5, top + 12], fill=P['rex'])
        d.rectangle([x - 3, top + 10, x + 3, foot - 2], fill=P['rex_dk'])
        d.rectangle([x - 5, foot - 3, x + 5, foot], fill=P['rex_dk'])
        if up:
            d.line([(x - 4, foot), (x + 4, foot)], fill=P['claw'])
    # body: a big pear seen from behind
    d.ellipse([9, 8 - lift, 35, 36 - lift], fill=P['rex_dk'])
    d.ellipse([10, 8 - lift, 33, 34 - lift], fill=P['rex'])
    # back stripes
    for k, y in enumerate((14, 19, 24, 29)):
        w = 6 - abs(k - 1)
        d.line([(22 - w, y - lift), (22 + w, y - lift)], fill=P['rex_dk'])
    d.line([(14, 12 - lift), (14, 26 - lift)], fill=P['rex_hi'])
    # the tiny arms poking out at the sides
    d.line([(9, 18 - lift), (6, 21 - lift)], fill=P['rex_dk'], width=2)
    d.line([(34, 18 - lift), (37, 21 - lift)], fill=P['rex_dk'], width=2)
    # head on top, turned a little so one eye shows
    d.ellipse([14, 0 - lift, 31, 13 - lift], fill=P['rex_dk'])
    d.ellipse([15, 0 - lift, 29, 11 - lift], fill=P['rex'])
    d.point((28, 5 - lift), fill=P['eye'])
    d.point((28, 6 - lift), fill=P['ink'])
    # the tail, coming towards us and swinging
    d.polygon([(17, 30 - lift), (27, 30 - lift), (22 + sw * 5, 45)], fill=P['rex_dk'])
    d.polygon([(18, 30 - lift), (25, 30 - lift), (22 + sw * 5, 43)], fill=P['rex'])
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


def sprites():
    """{sprite name: image}, all doubled."""
    out = {'rex_sky': big(sky(False)), 'rex_skyred': big(sky(True)),
           'rex_side_l': big(jungle_side(False)), 'rex_side_r': big(jungle_side(True)),
           'rex_boulder': big(boulder()), 'rex_cycad': big(cycad()),
           'rex_ptero0': big(ptero(0)), 'rex_ptero1': big(ptero(1)),
           'rex_crater0': big(crater(0)), 'rex_crater1': big(crater(1)),
           'rex_meteor0': big(meteor(0)), 'rex_meteor1': big(meteor(1)),
           'rex_target': big(target()), 'rex_heart': big(heart(True)), 'rex_heartx': big(heart(False)),
           'rex_arrow_l': big(arrow(True)), 'rex_arrow_r': big(arrow(False))}
    for k in range(4):                       # numbered in order: the game adds 0..3 to the first
        out['rex_ground%d' % k] = big(ground(k))
    for k in range(4):
        out['rex_run%d' % k] = big(rex(k))
    return out


NAMES = ['rex_sky', 'rex_skyred', 'rex_side_l', 'rex_side_r', 'rex_ground0', 'rex_ground1', 'rex_ground2',
         'rex_ground3', 'rex_run0', 'rex_run1', 'rex_run2', 'rex_run3', 'rex_boulder', 'rex_cycad', 'rex_ptero0',
         'rex_ptero1', 'rex_crater0', 'rex_crater1', 'rex_meteor0', 'rex_meteor1', 'rex_target', 'rex_heart',
         'rex_heartx', 'rex_arrow_l', 'rex_arrow_r']


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
