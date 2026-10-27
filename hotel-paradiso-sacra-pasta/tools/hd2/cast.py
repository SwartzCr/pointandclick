"""Characters in the LucasArts manner: flat fills, outlines drawn in a darker
shade of each part's own colour (not black), fold lines in that darker
tone, one small flat shadow shape per part, and black kept for details
such as eyes. Design coordinates are 1280x800; scale by paint.S."""
import math
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
import paint


def dark(c, k=0.45, tint=(40, 20, 60)):
    return tuple(int(c[i] * k + tint[i] * (1 - k) * 0.5) for i in range(3))


def mid(c, k=0.78):
    return tuple(int(c[i] * k + (60, 40, 90)[i] * (1 - k) * 0.6) for i in range(3))


class Sprite:
    """Drawn into an RGBA layer at the current scale, around an origin."""

    def __init__(self, w, h, ox, oy):
        self.S = paint.S
        self.W, self.H = int(w * self.S), int(h * self.S)
        self.ox, self.oy = ox, oy
        self.rgba = np.zeros((self.H, self.W, 4), np.float32)
        self.ow = max(1, int(round(2 * self.S)))      # outline: 1px at 640, 2px at 1280

    def _pts(self, pts):
        return [((x + self.ox) * self.S, (y + self.oy) * self.S) for x, y in pts]

    def _mask(self, kind, data, width=2):
        m = Image.new('L', (self.W, self.H), 0)
        d = ImageDraw.Draw(m)
        if kind == 'poly':
            d.polygon(self._pts(data), fill=255)
        elif kind == 'ellipse':
            d.polygon(self._pts(paint.ellipse_pts(*data)), fill=255)
        elif kind == 'line':
            d.line(self._pts(data), fill=255, width=max(1, int(round(width * self.S))), joint='curve')
        return np.asarray(m) > 127

    def _put(self, m, c):
        self.rgba[m, :3] = c
        self.rgba[m, 3] = 255

    def part(self, kind, data, colour, outline=True, shadow=None, edge=None):
        """shadow: polygon (design coords) of the flat shadow shape inside this part."""
        m = self._mask(kind, data)
        if outline:
            ring = ndimage.binary_dilation(m, iterations=self.ow)
            self._put(ring, edge or dark(colour))
        self._put(m, colour)
        if shadow is not None:
            sm = self._mask('poly', shadow) & m
            self._put(sm, mid(colour))
        return m

    def line(self, pts, colour, width=2):
        self._put(self._mask('line', pts, width), colour)

    def dot(self, x, y, r, colour):
        self._put(self._mask('ellipse', [x - r, y - r, x + r, y + r]), colour)

    def paste_into(self, img, x, y):
        """Composite onto a PIL RGB image with the sprite's feet at (x, y) design coords."""
        S = self.S
        px, py = int(round(x * S - self.ox * S)), int(round(y * S - self.oy * S))
        a = Image.fromarray(np.clip(self.rgba, 0, 255).astype(np.uint8), 'RGBA')
        img.paste(a, (px, py), a)


# ---------------------------------------------------------------- the guest
def guest():
    """The bellhop from Hotel Paradiso: red jacket with gold buttons and
    epaulettes, pillbox hat, brown hair, navy trousers. Big head, small
    feet, a slouch. Origin = between the feet. About 230 design px tall."""
    s = Sprite(170, 260, 85, 250)
    RED, GOLD, NAVY = (204, 44, 40), (246, 190, 60), (52, 56, 112)
    SKIN, HAIR, SHOE = (250, 196, 150), (124, 70, 36), (60, 40, 34)
    # shoes and legs
    s.part('poly', [(-34, -6), (-6, -8), (-4, 0), (-38, 0)], SHOE)
    s.part('poly', [(6, -8), (36, -8), (40, 0), (4, 0)], SHOE)
    s.part('poly', [(-26, -78), (0, -80), (-4, -8), (-24, -8)], NAVY, shadow=[(-14, -80), (0, -80), (-4, -8), (-12, -8)])
    s.part('poly', [(2, -80), (28, -78), (30, -8), (8, -8)], NAVY, shadow=[(18, -80), (28, -78), (30, -8), (20, -8)])
    s.line([(-14, -60), (-10, -48)], dark(NAVY), 2)
    s.line([(16, -40), (22, -30)], dark(NAVY), 2)
    # jacket: a short bell-shaped body
    body = [(-32, -150), (32, -150), (40, -84), (34, -70), (-34, -70), (-40, -84)]
    s.part('poly', body, RED, shadow=[(14, -150), (32, -150), (40, -84), (34, -70), (16, -70)])
    s.line([(0, -146), (0, -72)], dark(RED), 2)
    for y in (-136, -118, -100, -84):
        s.dot(-8, y, 3.2, GOLD)
        s.dot(8, y, 3.2, GOLD)
    s.line([(-32, -86), (-20, -82)], dark(RED), 2)
    # arms hanging, slightly bent, with hands
    s.part('poly', [(-34, -146), (-46, -140), (-56, -100), (-50, -78), (-40, -80), (-38, -104)], RED,
           shadow=[(-46, -110), (-38, -104), (-40, -80), (-48, -80)])
    s.part('poly', [(34, -146), (46, -140), (56, -100), (50, -78), (40, -80), (38, -104)], RED,
           shadow=[(46, -140), (56, -100), (50, -78), (46, -78)])
    s.part('poly', [(-56, -84), (-40, -84), (-40, -78), (-56, -78)], GOLD)
    s.part('poly', [(40, -84), (56, -84), (56, -78), (40, -78)], GOLD)
    s.part('ellipse', [-58, -80, -40, -62], SKIN)
    s.part('ellipse', [40, -80, 58, -62], SKIN)
    # epaulettes
    for sx in (-1, 1):
        s.part('ellipse', [sx * 40 - 14, -156, sx * 40 + 14, -142], GOLD)
        for k in range(4):
            s.line([(sx * 40 - 10 + k * 7, -144), (sx * 40 - 11 + k * 7, -137)], GOLD, 2)
    # collar, neck
    s.part('poly', [(-12, -160), (12, -160), (14, -148), (-14, -148)], SKIN, shadow=[(-12, -160), (12, -160), (12, -154), (-12, -154)])
    s.part('poly', [(-20, -152), (0, -140), (20, -152), (16, -146), (0, -132), (-16, -146)], GOLD)
    # head: big, slightly pear-shaped
    head = [(-36, -200), (-30, -230), (0, -240), (30, -230), (36, -200), (30, -170), (0, -158), (-28, -168)]
    s.part('poly', head, SKIN, shadow=[(16, -236), (30, -230), (36, -200), (30, -170), (8, -160), (22, -200)])
    s.part('ellipse', [-44, -208, -30, -188], SKIN)        # ear
    s.line([(-40, -202), (-36, -194)], dark(SKIN), 2)
    # hair under the hat, sideburns
    s.part('poly', [(-38, -214), (-34, -236), (0, -246), (34, -236), (36, -214), (24, -224), (4, -220), (-20, -226)], HAIR,
           shadow=[(18, -240), (34, -236), (36, -214), (26, -224)])
    s.part('poly', [(-36, -214), (-28, -214), (-30, -196), (-36, -200)], HAIR)
    # pillbox hat, tipped
    s.part('poly', [(-26, -238), (18, -248), (22, -270), (-20, -262)], RED, shadow=[(6, -246), (18, -248), (22, -270), (10, -266)])
    s.part('poly', [(-26, -240), (18, -250), (19, -244), (-25, -234)], GOLD)
    s.line([(-20, -262), (22, -270)], dark(RED), 2)
    # face: eyes as black dots on whites, big nose, half-smile
    for ex in (-6, 18):
        s.part('ellipse', [ex - 8, -216, ex + 8, -196], (255, 255, 255), edge=dark(SKIN))
        s.dot(ex + 3, -205, 3.4, (0, 0, 0))
    s.line([(-15, -222), (-1, -224)], HAIR, 3)
    s.line([(11, -224), (25, -222)], HAIR, 3)
    s.part('poly', [(4, -200), (16, -190), (14, -182), (2, -184)], SKIN, edge=dark(SKIN))
    s.line([(-8, -176), (6, -172), (20, -178)], dark(SKIN, 0.35), 2)
    s.part('ellipse', [20, -190, 28, -184], (244, 160, 130), outline=False)
    return s


# ---------------------------------------------------------------- Khuc
def khuc():
    """Khuc: a tall, sleepy acolyte of the noodle. Cream robe, red stole
    with little gold forks, a colander for a hat, goatee, hands tucked in
    the sleeves. Origin = feet. About 300 design px tall."""
    s = Sprite(170, 320, 85, 312)
    CREAM, RED, GOLD = (238, 226, 196), (190, 40, 46), (246, 196, 70)
    SKIN, HAIR, STEEL = (214, 160, 116), (40, 34, 40), (190, 196, 210)
    # robe: long trapezoid with a hem that kicks out, sandal toes
    s.part('ellipse', [-30, -8, -8, 2], (130, 84, 50))
    s.part('ellipse', [6, -8, 30, 2], (130, 84, 50))
    robe = [(-30, -214), (30, -214), (44, -60), (52, -6), (-52, -6), (-44, -60)]
    s.part('poly', robe, CREAM, shadow=[(12, -214), (30, -214), (44, -60), (52, -6), (22, -6), (16, -60)])
    for x0, x1 in ((-20, -30), (0, -4), (16, 26)):
        s.line([(x0 * 0.6, -150), (x1, -10)], dark(CREAM, 0.6), 2)
    # sleeves meeting in front, hands hidden
    s.part('poly', [(-32, -210), (-46, -196), (-46, -140), (-6, -126), (0, -140), (-26, -150)], CREAM,
           shadow=[(-46, -160), (-6, -128), (-46, -140)])
    s.part('poly', [(32, -210), (46, -196), (46, -140), (6, -126), (0, -140), (26, -150)], CREAM,
           shadow=[(30, -200), (46, -196), (46, -140), (30, -140)])
    s.part('ellipse', [-12, -142, 12, -124], dark(CREAM, 0.5), outline=False)
    # stole hanging in two strips
    for sx in (-1, 1):
        strip = [(sx * 6, -230), (sx * 20, -228), (sx * 22, -60), (sx * 8, -60)]
        s.part('poly', strip, RED, shadow=[(sx * 14, -228), (sx * 20, -228), (sx * 22, -60), (sx * 16, -60)])
        for y in (-110, -86):
            fx = sx * 15
            s.line([(fx, y), (fx, y + 14)], GOLD, 2)
            s.line([(fx - 4, y - 5), (fx - 4, y), (fx + 4, y), (fx + 4, y - 5)], GOLD, 1.5)
        s.part('poly', [(sx * 8, -60), (sx * 22, -60), (sx * 22, -52), (sx * 8, -52)], GOLD)
    # neck and long face
    s.part('poly', [(-10, -236), (10, -236), (12, -222), (-12, -222)], SKIN)
    face = [(-26, -276), (-24, -300), (0, -306), (24, -300), (26, -276), (18, -246), (0, -234), (-18, -246)]
    s.part('poly', face, SKIN, shadow=[(10, -304), (24, -300), (26, -276), (18, -246), (6, -238), (14, -270)])
    s.part('poly', [(-10, -244), (10, -244), (6, -222), (0, -214), (-6, -222)], HAIR)    # goatee
    s.line([(-14, -250), (-2, -246), (14, -250)], HAIR, 3)                               # moustache
    # sleepy lidded eyes
    for ex in (-11, 11):
        s.part('ellipse', [ex - 8, -280, ex + 8, -266], (255, 255, 255), edge=dark(SKIN))
        s.part('poly', [(ex - 9, -282), (ex + 9, -282), (ex + 9, -273), (ex - 9, -273)], SKIN, outline=False)
        s.line([(ex - 9, -273), (ex + 9, -273)], dark(SKIN, 0.3), 2)
        s.dot(ex + 1, -269, 2.6, (0, 0, 0))
    s.line([(-18, -287), (-4, -285)], HAIR, 3)
    s.line([(4, -285), (18, -287)], HAIR, 3)
    s.part('poly', [(-2, -268), (6, -254), (-4, -252)], SKIN, edge=dark(SKIN))
    # colander hat: a steel bowl with holes and a handle
    s.part('poly', [(-34, -298), (34, -298), (28, -324), (-28, -324)], STEEL, shadow=[(12, -298), (34, -298), (28, -324), (16, -324)])
    s.part('ellipse', [-36, -302, 36, -294], STEEL)
    for k, hx in enumerate(range(-20, 24, 9)):
        s.dot(hx, -310 - (k % 2) * 6, 2.2, dark(STEEL, 0.35))
    for sx in (-1, 1):
        s.part('poly', [(sx * 30, -320), (sx * 44, -318), (sx * 44, -312), (sx * 30, -312)], STEEL)
    return s


if __name__ == '__main__':
    import sys
    paint.set_scale(float(sys.argv[1]) if len(sys.argv) > 1 else 1.0)
    img = Image.new('RGB', (int(400 * paint.S), int(360 * paint.S)), (120, 110, 100))
    guest().paste_into(img, 100, 340)
    khuc().paste_into(img, 280, 340)
    img.save('/tmp/claude-0/cast_test.png')
