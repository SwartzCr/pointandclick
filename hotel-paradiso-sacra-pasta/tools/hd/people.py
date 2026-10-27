"""The guest and Khuc, redrawn at twice the size with cartoon proportions
(big heads, big eyes, bulbous noses) and full shading."""
import math
from PIL import Image, ImageDraw
from shade import Layer as _Layer, rgba, mask_of


class Layer(_Layer):
    def paint(self, mask, base, **kw):
        kw.setdefault('dither', False)
        kw['bands'] = kw.get('bands', 6) + 1
        super().paint(mask, base, **kw)

SKIN = (242, 186, 144)
HAIR = (104, 60, 36)
RED = (196, 34, 46)
GOLD = (236, 190, 70)
NAVY = (50, 50, 92)
SHOE = (46, 38, 50)
WHITE = (252, 248, 240)
INK = (30, 18, 34)


def _taper(cx0, y0, w0, cx1, y1, w1):
    return [(cx0 - w0 / 2, y0), (cx0 + w0 / 2, y0), (cx1 + w1 / 2, y1), (cx1 - w1 / 2, y1)]


def _limb(d, pts, w0, w1):
    """A tapering curved limb through a list of points."""
    n = len(pts)
    left, right = [], []
    for i, (x, y) in enumerate(pts):
        w = w0 + (w1 - w0) * i / (n - 1)
        if i < n - 1:
            dx, dy = pts[i + 1][0] - x, pts[i + 1][1] - y
        else:
            dx, dy = x - pts[i - 1][0], y - pts[i - 1][1]
        l = math.hypot(dx, dy) or 1
        nx, ny = -dy / l * w / 2, dx / l * w / 2
        left.append((x + nx, y + ny))
        right.append((x - nx, y - ny))
    d.polygon(left + right[::-1], fill=255)
    for (x, y), w in ((pts[0], w0), (pts[-1], w1)):
        d.ellipse([x - w / 2, y - w / 2, x + w / 2, y + w / 2], fill=255)


def eye(L, cx, cy, w, h, look=(2, 1), lid=0.0):
    L.shape(WHITE, lambda d: d.ellipse([cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2], fill=255),
            radius=6, bands=4, outline=2, outline_color=INK)
    px, py = cx + look[0], cy + look[1] + 1
    d = ImageDraw.Draw(L.im)
    d.ellipse([px - w * 0.22, py - h * 0.24, px + w * 0.22, py + h * 0.24], fill=rgba(INK))
    d.ellipse([px - w * 0.12 - 1, py - h * 0.16, px - w * 0.12 + 2, py - h * 0.16 + 3], fill=rgba(WHITE))
    if lid > 0:      # heavy lids for Khuc's serene look
        d.chord([cx - w / 2 - 1, cy - h / 2 - 1, cx + w / 2 + 1, cy + h / 2 + 1], 180, 360, fill=rgba(SKIN_K))
        d.line([(cx - w / 2, cy), (cx + w / 2, cy)], fill=rgba(INK), width=2)


SKIN_K = (220, 160, 110)


def guest(beads=False, pendant=False, talk=False):
    W, H = 120, 236
    L = Layer(W, H)
    cx = 60
    # shoes and legs
    for sx in (-15, 15):
        L.shape(NAVY, lambda d, sx=sx: d.polygon(_taper(cx + sx * 0.7, 150, 22, cx + sx, 218, 17), fill=255),
                radius=7, bands=5)
    for sx in (-17, 17):
        L.shape(SHOE, lambda d, sx=sx: d.ellipse([cx + sx - 15 + (4 if sx > 0 else -4), 212, cx + sx + 15 + (4 if sx > 0 else -4), 232], fill=255),
                radius=7, bands=5, spec=True)
    # back arm (viewer's right), in shade
    L.shape(RED, lambda d: _limb(d, [(cx + 26, 100), (cx + 36, 126), (cx + 38, 152)], 18, 15), radius=7, bands=5)
    L.shape(GOLD, lambda d: d.ellipse([cx + 29, 148, cx + 47, 160], fill=255), radius=4, bands=4, spec=True)
    L.shape(SKIN, lambda d: d.ellipse([cx + 30, 154, cx + 46, 172], fill=255), radius=6, bands=5)
    # torso: short bellhop jacket, flared at the hem
    L.shape(RED, lambda d: d.polygon([(cx - 26, 98), (cx + 26, 98), (cx + 30, 140), (cx + 34, 158), (cx - 34, 158),
                                      (cx - 30, 140)], fill=255), radius=16, bands=6)
    L.shape(GOLD, lambda d: d.polygon([(cx - 34, 152), (cx + 34, 152), (cx + 34, 160), (cx - 34, 160)], fill=255),
            radius=3, bands=4, spec=True, outline=1)
    for by in (112, 124, 136):
        for bx in (-9, 9):
            L.shape(GOLD, lambda d, bx=bx, by=by: d.ellipse([cx + bx - 3, by - 3, cx + bx + 3, by + 3], fill=255),
                    radius=3, bands=3, spec=True, outline=1)
    # epaulettes
    for sx in (-1, 1):
        L.shape(GOLD, lambda d, sx=sx: d.ellipse([cx + sx * 30 - 10, 94, cx + sx * 30 + 10, 104], fill=255),
                radius=4, bands=4, spec=True)
    # neck and collar
    L.shape(SKIN, lambda d: d.rectangle([cx - 8, 82, cx + 8, 100], fill=255), radius=5, bands=4)
    L.shape(RED, lambda d: d.rounded_rectangle([cx - 15, 92, cx + 15, 104], 4, fill=255), radius=5, bands=4)
    L.shape(GOLD, lambda d: d.rectangle([cx - 15, 92, cx + 15, 95], fill=255), radius=2, bands=3, outline=1)
    if beads:
        for i in range(13):
            t = i / 12
            bx = cx - 18 + 36 * t
            by = 104 + 20 * math.sin(math.pi * t)
            L.shape((252, 222, 148), lambda d, bx=bx, by=by: d.ellipse([bx - 4, by - 3, bx + 4, by + 3], fill=255),
                    radius=3, bands=3, outline=1)
        L.shape((252, 222, 148), lambda d: d.ellipse([cx - 7, 120, cx + 7, 134], fill=255), radius=5, bands=4, outline=1)
    if pendant:
        py = 126 if not beads else 138
        L.line([(cx - 12, 102), (cx, py - 6), (cx + 12, 102)], (110, 90, 140), 1)
        L.shape((176, 100, 250), lambda d: d.polygon([(cx, py - 7), (cx + 6, py), (cx, py + 10), (cx - 6, py)], fill=255),
                radius=4, bands=4, spec=True, outline=1)
    # front arm (viewer's left), bent with the hand on the hip
    L.shape(RED, lambda d: _limb(d, [(cx - 26, 100), (cx - 38, 124), (cx - 30, 146)], 19, 15), radius=7, bands=5)
    L.shape(GOLD, lambda d: d.ellipse([cx - 37, 140, cx - 21, 152], fill=255), radius=4, bands=4, spec=True)
    L.shape(SKIN, lambda d: d.ellipse([cx - 30, 142, cx - 14, 158], fill=255), radius=6, bands=5)
    # head: a big oval, ears, a bulbous nose and big eyes
    for sx in (-1, 1):
        L.shape(SKIN, lambda d, sx=sx: d.ellipse([cx + sx * 31 - 7, 44, cx + sx * 31 + 7, 62], fill=255), radius=5, bands=4)
    L.shape(SKIN, lambda d: d.ellipse([cx - 32, 14, cx + 32, 90], fill=255), radius=24, bands=6)
    # hair: a swoop with a few spikes
    L.shape(HAIR, lambda d: d.polygon([(cx - 34, 46), (cx - 36, 28), (cx - 26, 12), (cx - 8, 4), (cx + 14, 6),
                                       (cx + 30, 14), (cx + 36, 30), (cx + 34, 46), (cx + 28, 30), (cx + 18, 26),
                                       (cx + 4, 30), (cx - 10, 24), (cx - 20, 32), (cx - 28, 30)], fill=255),
            radius=9, bands=5)
    # pillbox hat, at a jaunty angle
    hat = mask_of((W, H), lambda d: d.polygon([(cx + 2, 8), (cx + 30, 2), (cx + 32, 16), (cx + 4, 22)], fill=255))
    L.paint(hat, RED, radius=6, bands=5)
    L.shape(GOLD, lambda d: d.polygon([(cx + 3, 17), (cx + 31, 11), (cx + 32, 16), (cx + 4, 22)], fill=255),
            radius=2, bands=3, outline=1, spec=True)
    L.shape(RED, lambda d: d.ellipse([cx + 1, 0, cx + 31, 10], fill=255), radius=4, bands=4, outline=1)
    # face
    eye(L, cx - 13, 48, 18, 22, look=(2, 1))
    eye(L, cx + 13, 48, 18, 22, look=(2, 1))
    d = ImageDraw.Draw(L.im)
    d.line([(cx - 22, 34), (cx - 6, 36)], fill=rgba(HAIR), width=3)
    d.line([(cx + 6, 35), (cx + 22, 32)], fill=rgba(HAIR), width=3)
    L.shape(SKIN, lambda d: d.ellipse([cx - 6, 54, cx + 10, 70], fill=255), radius=7, bands=5, spec=True)
    if talk:
        L.shape((140, 40, 50), lambda d: d.ellipse([cx - 10, 74, cx + 12, 86], fill=255), radius=4, bands=3,
                outline=2, outline_color=INK)
        d.ellipse([cx - 3, 80, cx + 7, 86], fill=rgba((230, 110, 120)))
    else:
        d.arc([cx - 14, 66, cx + 14, 80], 20, 160, fill=rgba(INK), width=2)
        d.line([(cx + 12, 73), (cx + 15, 71)], fill=rgba(INK), width=2)
    return L.im


ROBE = (240, 226, 186)
STOLE = (204, 44, 40)
METAL = (196, 204, 216)


def khuc(talk=False):
    W, H = 128, 250
    L = Layer(W, H)
    cx = 64
    for sx in (-12, 12):
        L.shape((130, 82, 46), lambda d, sx=sx: d.ellipse([cx + sx - 13, 236, cx + sx + 13, 248], fill=255), radius=5, bands=4)
    # robe: a bell with round shoulders
    L.shape(ROBE, lambda d: d.polygon([(cx - 10, 98), (cx + 10, 98), (cx + 26, 104), (cx + 32, 116), (cx + 42, 240),
                                       (cx - 42, 240), (cx - 32, 116), (cx - 26, 104)], fill=255),
            radius=26, bands=6)
    for k in (-1, 1):   # folds
        L.line([(cx + k * 10, 150), (cx + k * 16, 236)], (200, 182, 140), 2)
    # stole with little golden forks
    for sx in (-1, 1):
        L.shape(STOLE, lambda d, sx=sx: d.polygon([(cx + sx * 6, 104), (cx + sx * 16, 104), (cx + sx * 20, 196),
                                                   (cx + sx * 9, 196)], fill=255), radius=5, bands=5)
        for y in (130, 160):
            fx = cx + sx * 13
            L.line([(fx, y), (fx, y + 12)], GOLD, 2)
            L.line([(fx - 4, y), (fx + 4, y)], GOLD, 2)
            for t in (-4, 0, 4):
                L.line([(fx + t, y - 6), (fx + t, y)], GOLD, 1)
    L.shape((150, 30, 30), lambda d: d.rectangle([cx - 30, 150, cx + 30, 156], fill=255), radius=3, bands=4, outline=1)
    # hands folded into big droopy sleeves that meet in the middle
    for sx in (-1, 1):
        L.shape(ROBE, lambda d, sx=sx: _limb(d, [(cx + sx * 30, 112), (cx + sx * 34, 132), (cx + sx * 12, 148)], 22, 30),
                radius=11, bands=5)
    L.shape(SKIN_K, lambda d: d.ellipse([cx - 9, 138, cx + 9, 154], fill=255), radius=5, bands=4)
    # neck
    L.shape(SKIN_K, lambda d: d.rectangle([cx - 9, 90, cx + 9, 104], fill=255), radius=4, bands=4)
    # head
    for sx in (-1, 1):
        L.shape(SKIN_K, lambda d, sx=sx: d.ellipse([cx + sx * 27 - 7, 54, cx + sx * 27 + 7, 72], fill=255), radius=5, bands=4)
    L.shape(SKIN_K, lambda d: d.ellipse([cx - 28, 30, cx + 28, 100], fill=255), radius=22, bands=6)
    L.shape((40, 34, 40), lambda d: d.polygon([(cx - 12, 88), (cx + 12, 88), (cx + 4, 112), (cx - 4, 112)], fill=255),
            radius=5, bands=4)                                                     # goatee
    L.shape((40, 34, 40), lambda d: d.polygon([(cx - 14, 80), (cx - 2, 78), (cx + 2, 78), (cx + 14, 80), (cx + 10, 84),
                                               (cx - 10, 84)], fill=255), radius=3, bands=3)  # moustache
    eye(L, cx - 11, 60, 16, 18, look=(0, 2), lid=1)
    eye(L, cx + 11, 60, 16, 18, look=(0, 2), lid=1)
    L.shape(SKIN_K, lambda d: d.ellipse([cx - 7, 62, cx + 7, 78], fill=255), radius=6, bands=5, spec=True)
    if talk:
        L.shape((120, 40, 40), lambda d: d.ellipse([cx - 6, 84, cx + 6, 92], fill=255), radius=3, bands=3, outline=1)
    # the colander, worn as a hat
    L.shape(METAL, lambda d: d.chord([cx - 36, 4, cx + 36, 70], 180, 360, fill=255), radius=14, bands=6, spec=True)
    L.shape(METAL, lambda d: d.ellipse([cx - 44, 30, cx + 44, 44], fill=255), radius=5, bands=5, spec=True)
    for sx in (-1, 1):
        L.shape(METAL, lambda d, sx=sx: d.rounded_rectangle([cx + sx * 44 - 8, 30, cx + sx * 44 + 8, 36], 3, fill=255),
                radius=3, bands=3, outline=1)
    d = ImageDraw.Draw(L.im)
    for row, y in enumerate((14, 22, 30)):
        n = 5 + row * 2
        for k in range(n):
            x = cx - (n - 1) * 5 + k * 10
            d.ellipse([x - 2, y - 1, x + 2, y + 2], fill=rgba((70, 76, 92)))
    return L.im
