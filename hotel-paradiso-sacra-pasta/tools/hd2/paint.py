"""A small 'digital painting' toolkit for LucasArts-style VGA backgrounds.

What it imitates (from Sam & Max Hit the Road and Day of the Tentacle):
backgrounds are painted, not inked. Shapes have no outlines; they read by
value: a lit top, a mid front, a dark side. Light comes from lamps in the
room and falls off with distance, so every surface carries a smooth
gradient. Contact shadows pool under furniture and in corners, and a few
dark creases mark overhangs. The surfaces are mottled and streaked, and the
whole picture is reduced to a 256-colour palette with error diffusion,
which gives the gritty, dithered texture of the originals.

Everything is drawn in design coordinates for a 1280x800 screen and scaled
by S, so the same scene renders at 1280x800 (S = 1) or 640x400 (S = 0.5).
"""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage

S = 1.0
WARP = None      # optional function (x, y) -> (x, y) in design space, for crooked perspective


def set_scale(s):
    global S
    S = s


def set_warp(fn):
    global WARP
    WARP = fn


def P(pts):
    if WARP is not None:
        pts = [WARP(x, y) for x, y in pts]
    return [(x * S, y * S) for x, y in pts]


def ellipse_pts(x0, y0, x1, y1, a0=0, a1=360, n=None):
    cx, cy, rx, ry = (x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) / 2, (y1 - y0) / 2
    n = n or max(16, int((rx + ry) / 3))
    span = (a1 - a0) % 360 or 360
    return [(cx + rx * math.cos(math.radians(a0 + span * i / n)),
             cy + ry * math.sin(math.radians(a0 + span * i / n))) for i in range(n + 1)]


def rect_pts(x0, y0, x1, y1, n=8):
    top = [(x0 + (x1 - x0) * i / n, y0) for i in range(n + 1)]
    right = [(x1, y0 + (y1 - y0) * i / n) for i in range(1, n + 1)]
    bot = [(x1 - (x1 - x0) * i / n, y1) for i in range(1, n + 1)]
    left = [(x0, y1 - (y1 - y0) * i / n) for i in range(1, n)]
    return top + right + bot + left


class Painting:
    def __init__(self, w, h, seed=1):
        self.W, self.H = int(round(w * S)), int(round(h * S))
        self.rgb = np.zeros((self.H, self.W, 3), np.float32)
        self.rng = np.random.default_rng(seed)
        self.lights = []          # (x, y, radius, strength, colour), design coords
        self.ambient = np.array([0.42, 0.40, 0.48], np.float32)
        yy, xx = np.mgrid[0:self.H, 0:self.W].astype(np.float32)
        self.xx, self.yy = xx / S, yy / S
        self._mottle = {}

    # ------------------------------------------------------------ masks
    def mask(self, kind, data, **kw):
        m = Image.new('L', (self.W, self.H), 0)
        d = ImageDraw.Draw(m)
        if kind == 'poly':
            d.polygon(P(data), fill=255)
        elif kind == 'rect':
            d.polygon(P(rect_pts(*data)), fill=255)
        elif kind == 'ellipse':
            d.polygon(P(ellipse_pts(*data)), fill=255)
        elif kind == 'chord':
            d.polygon(P(ellipse_pts(*data, a0=kw['a0'], a1=kw['a1'])), fill=255)
        elif kind == 'line':
            d.line(P(data), fill=255, width=max(1, int(round(kw.get('width', 2) * S))), joint='curve')
        return np.asarray(m, np.float32) / 255.0

    # ------------------------------------------------------------ light
    def light(self, x, y, radius, strength=1.0, colour=(1.0, 0.86, 0.62)):
        self.lights.append((x, y, radius, strength, np.array(colour, np.float32)))

    def lightmap(self, facing=1.0, lift=0.0):
        """Light arriving at each pixel for a surface that faces the
        lights by `facing` (1 = square on, 0.5 = turned away)."""
        key = (round(facing, 3), round(lift, 3), len(self.lights))
        cache = self.__dict__.setdefault('_lm', {})
        if key in cache:
            return cache[key]
        L = np.broadcast_to(self.ambient, (self.H, self.W, 3)).copy()
        for x, y, r, k, c in self.lights:
            d = np.sqrt((self.xx - x) ** 2 + ((self.yy - y) * 1.15) ** 2)
            f = np.clip(1 - d / r, 0, 1) ** 1.6 * k * facing
            L += f[..., None] * c
        cache[key] = L + lift
        return cache[key]

    def mottle(self, scale=6.0, key=None):
        key = key or scale
        if key not in self._mottle:
            n = self.rng.normal(0, 1, (self.H, self.W)).astype(np.float32)
            n = ndimage.gaussian_filter(n, scale * S)
            n /= (n.std() + 1e-6)
            self._mottle[key] = n
        return self._mottle[key]

    # ------------------------------------------------------------ painting
    def fill(self, m, base, facing=1.0, grad=None, mottle=0.05, mscale=6.0, lift=0.0, emissive=False):
        """Paint `base` through mask m, lit by the room's lights.
        grad: ((dx, dy), amount) adds a linear darkening along a direction."""
        base = np.asarray(base, np.float32) / 255.0
        if emissive:
            col = np.broadcast_to(base, (self.H, self.W, 3)).copy()
        else:
            col = base * self.lightmap(facing, lift)
        if grad is not None:
            (gx, gy), amt = grad
            ys, xs = np.nonzero(m > 0.5)
            if len(xs):
                proj = self.xx * gx + self.yy * gy
                p = proj[m > 0.5]
                t = (proj - p.min()) / max(1e-3, p.max() - p.min())
                col *= (1 - amt * np.clip(t, 0, 1))[..., None]
        if mottle:
            col *= (1 + mottle * self.mottle(mscale))[..., None]
        a = m[..., None]
        self.rgb = self.rgb * (1 - a) + np.clip(col, 0, 1.4) * 255 * a

    def shade(self, m, amount, colour=(40, 24, 70), blur=0.0):
        """Darken (multiply towards a cool shadow colour) through mask m."""
        if blur:
            m = ndimage.gaussian_filter(m, blur * S)
        c = np.asarray(colour, np.float32)
        a = np.clip(m * amount, 0, 1)[..., None]
        self.rgb = self.rgb * (1 - a) + (self.rgb * 0.35 + c * 0.65) * a

    def glow(self, m, amount, colour=(255, 230, 170), blur=0.0):
        if blur:
            m = ndimage.gaussian_filter(m, blur * S)
        c = np.asarray(colour, np.float32)
        a = np.clip(m * amount, 0, 1)[..., None]
        self.rgb = self.rgb * (1 - a) + np.maximum(self.rgb, c) * a

    def contact(self, m, radius=10, amount=0.7, below=True):
        """Ambient-occlusion pooling around an object's footprint."""
        g = ndimage.gaussian_filter(m, radius * S)
        if below:
            g = ndimage.shift(g, (radius * 0.4 * S, 0), order=1)
        self.shade(np.clip(g * 1.6, 0, 1) * (1 - m), amount)

    def crease(self, pts, width=2, amount=0.75):
        self.shade(self.mask('line', pts, width=width), amount)

    def strokes(self, m, n, length, colour, alpha=0.35, angle=0.0, jitter=0.4, width=1):
        """Short painterly strokes (wood grain, plaster texture) inside m."""
        im = Image.new('L', (self.W, self.H), 0)
        d = ImageDraw.Draw(im)
        ys, xs = np.nonzero(m > 0.5)
        if not len(xs):
            return
        idx = self.rng.integers(0, len(xs), n)
        for i in idx:
            x, y = xs[i], ys[i]
            a = angle + self.rng.normal(0, jitter)
            l = length * S * self.rng.uniform(0.5, 1.2)
            d.line([(x, y), (x + math.cos(a) * l, y + math.sin(a) * l)], fill=255,
                   width=max(1, int(round(width * S))))
        k = np.asarray(im, np.float32) / 255 * m * alpha
        c = np.asarray(colour, np.float32)
        self.rgb = self.rgb * (1 - k[..., None]) + c * k[..., None]

    def flat(self, m, colour, alpha=1.0):
        c = np.asarray(colour, np.float32)
        a = (m * alpha)[..., None]
        self.rgb = self.rgb * (1 - a) + c * a

    def text(self, xy, s, size, colour, anchor='mm', font='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'):
        from PIL import ImageFont
        im = Image.new('L', (self.W, self.H), 0)
        d = ImageDraw.Draw(im)
        d.fontmode = '1'
        f = ImageFont.truetype(font, max(7, int(round(size * S))))
        x, y = xy
        if WARP is not None:
            x, y = WARP(x, y)
        d.text((x * S, y * S), s, font=f, fill=255, anchor=anchor)
        self.flat(np.asarray(im, np.float32) / 255, colour)

    # ------------------------------------------------------------ output
    def image(self, colours=256, dither=True):
        im = Image.fromarray(np.clip(self.rgb, 0, 255).astype(np.uint8), 'RGB')
        if colours:
            q = im.quantize(colours, method=Image.Quantize.MEDIANCUT,
                            dither=Image.Dither.FLOYDSTEINBERG if dither else Image.Dither.NONE)
            im = q.convert('RGB')
        return im
