"""Cel-shaded cartoon drawing toolkit, resolution-independent.

The look follows the LucasArts cartoon games of the early 90s (Sam & Max,
Day of the Tentacle): flat colour fills, a hard-edged shadow band on the side
of each shape that faces away from the light (the upper left), a crisp
highlight only on shiny things, and thick dark outlines. Big surfaces like
walls and floors get banded, dithered gradients instead.

All drawing code is written in "design" coordinates for a 1280x800 screen.
Everything goes through SD, a drawing proxy that multiplies coordinates and
line widths by the global scale S, so the same scene renders natively at
1280x800 (S = 1) or 640x400 (S = 0.5), with no resampling.
"""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops, ImageFont
from scipy import ndimage

S = 1.0
LIGHT2 = np.array([-0.6, -0.8])          # where the light comes from, in screen space
SHADOW_TINT = np.array([60, 30, 96], dtype=np.float32)
LIGHT_TINT = np.array([255, 238, 184], dtype=np.float32)
BAYER4 = (np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) + 0.5) / 16
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'


def set_scale(s):
    global S
    S = s


def px(v):
    """A design-space length in real pixels (at least 1)."""
    return max(1, int(round(v * S)))


def rsize(w, h):
    return int(round(w * S)), int(round(h * S))


def rgba(c, a=255):
    return tuple(int(v) for v in c[:3]) + (a,)


def tone(base, t):
    """t in [0,1]: 0 deep shadow, 0.6 the base colour, 1 highlight."""
    base = np.asarray(base[:3], dtype=np.float32)
    dark = base * 0.5 + SHADOW_TINT * 0.24
    light = base * 0.6 + LIGHT_TINT * 0.4
    if t < 0.6:
        c = dark + (base - dark) * (t / 0.6)
    else:
        c = base + (light - base) * ((t - 0.6) / 0.4)
    return tuple(int(v) for v in np.clip(c, 0, 255))


def ramp(base, t):
    base = np.asarray(base[:3], dtype=np.float32)
    dark = base * 0.5 + SHADOW_TINT * 0.24
    light = base * 0.6 + LIGHT_TINT * 0.4
    t = t[..., None]
    lo = dark + (base - dark) * np.clip(t / 0.6, 0, 1)
    hi = base + (light - base) * np.clip((t - 0.6) / 0.4, 0, 1)
    return np.where(t < 0.6, lo, hi)


def quantize(t, bands, dither=True):
    h, w = t.shape
    if dither:
        th = np.tile(BAYER4, (h // 4 + 1, w // 4 + 1))[:h, :w]
        return np.clip(np.floor(t * bands + th) / bands, 0, 1)
    return np.clip(np.round(t * bands) / bands, 0, 1)


# ------------------------------------------------------------------ scaled drawing
class SD:
    """ImageDraw with design coordinates."""

    def __init__(self, im):
        self.d = ImageDraw.Draw(im)
        self.d.fontmode = '1'

    @staticmethod
    def _pts(pts):
        if not pts:
            return pts
        if isinstance(pts[0], (tuple, list)):
            return [(x * S, y * S) for x, y in pts]
        return [v * S for v in pts]

    def _box(self, b):
        x0, y0, x1, y1 = [v * S for v in b]
        return [min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)]

    def polygon(self, pts, fill=None, outline=None):
        self.d.polygon(self._pts(pts), fill=fill, outline=outline)

    def rectangle(self, b, fill=None, outline=None, width=1):
        self.d.rectangle(self._box(b), fill=fill, outline=outline, width=px(width))

    def rounded_rectangle(self, b, r, fill=None):
        self.d.rounded_rectangle(self._box(b), r * S, fill=fill)

    def ellipse(self, b, fill=None, outline=None, width=1):
        self.d.ellipse(self._box(b), fill=fill, outline=outline, width=px(width))

    def chord(self, b, a0, a1, fill=None):
        self.d.chord(self._box(b), a0, a1, fill=fill)

    def pieslice(self, b, a0, a1, fill=None):
        self.d.pieslice(self._box(b), a0, a1, fill=fill)

    def arc(self, b, a0, a1, fill=None, width=1):
        self.d.arc(self._box(b), a0, a1, fill=fill, width=px(width))

    def line(self, pts, fill=None, width=1, joint=None):
        self.d.line(self._pts(pts), fill=fill, width=px(width), joint=joint)

    def point(self, xy, fill=None):
        x, y = xy
        if S >= 1:
            self.d.point((x * S, y * S), fill=fill)
        else:
            self.d.point((x * S, y * S), fill=fill)

    def text(self, xy, s, size, fill, anchor='la', shadow=None):
        f = ImageFont.truetype(FONT, max(7, int(round(size * S))))
        x, y = xy[0] * S, xy[1] * S
        if shadow is not None:
            o = max(1, int(round(2 * S)))
            self.d.text((x + o, y + o), s, font=f, fill=rgba(shadow), anchor=anchor)
        self.d.text((x, y), s, font=f, fill=rgba(fill), anchor=anchor)


def D(im):
    return SD(im)


def mask_of(size, draw_fn):
    """size is a real size (from rsize); draw_fn gets an SD."""
    m = Image.new('L', size, 0)
    draw_fn(SD(m))
    return m


def grow(m, width):
    g = m
    for _ in range(width):
        g = g.filter(ImageFilter.MaxFilter(3))
    return g


def outline_mask(m, width=2):
    a = m.point(lambda v: 255 if v > 127 else 0)
    return ImageChops.subtract(grow(a, width), a)


def _shift(m, dx, dy):
    """Sample the boolean mask at (x + dx, y + dy), outside = False."""
    out = np.zeros_like(m)
    h, w = m.shape
    dx, dy = int(round(dx)), int(round(dy))
    ys = slice(max(0, -dy), min(h, h - dy))
    yd = slice(max(0, dy), min(h, h + dy))
    xs = slice(max(0, -dx), min(w, w - dx))
    xd = slice(max(0, dx), min(w, w + dx))
    out[ys, xs] = m[yd, xd]
    return out


class Layer:
    """An RGBA canvas (design size w x h) that shaded shapes are painted onto."""

    def __init__(self, w, h):
        self.size = rsize(w, h)
        self.im = Image.new('RGBA', self.size, (0, 0, 0, 0))

    def paint(self, mask, base, radius=10, outline=3, spec=False, level=0.6, shadow=True,
              outline_color=None, away=None, **_ignored):
        """Cel-shade a shape: flat base, a shadow band `radius`*0.5 wide on
        the side away from the light, an optional highlight, an outline."""
        m = np.asarray(mask) > 127
        if not m.any():
            return
        lx, ly = LIGHT2 if away is None else -np.asarray(away)
        col = np.zeros(m.shape + (4,), dtype=np.uint8)
        col[m, :3] = tone(base, level)
        if shadow:
            k = max(1.0, radius * 0.55 * S)
            k = min(k, 22 * S)
            # a pixel is in shadow when stepping away from the light leaves the shape
            sh = m & ~_shift(m, -lx * k, -ly * k)
            # soften the stair-steps of the band into a hand-drawn edge
            sh = ndimage.binary_opening(sh, iterations=1) if k > 2 else sh
            col[sh, :3] = tone(base, max(0.0, level - 0.32))
            if k >= 6 * S and radius >= 14:
                core = m & ~_shift(m, -lx * k * 0.35, -ly * k * 0.35)
                col[core, :3] = tone(base, max(0.0, level - 0.48))
        if spec:
            h = max(1.0, radius * 0.22 * S)
            hl = m & ~_shift(m, lx * h, ly * h)
            hl &= ~ndimage.binary_dilation(~m, iterations=max(1, int(h * 0.6)))
            col[hl, :3] = tone(base, 0.95)
            # a little glint
            d = ndimage.distance_transform_edt(m)
            yy, xx = np.nonzero(m)
            if len(yy):
                score = d[yy, xx] * 0.0 + (xx * lx + yy * ly) * -1
                i = np.argmin(score)
                gx, gy = xx[i] - lx * (radius * 0.5 * S) * -1, yy[i] - ly * (radius * 0.5 * S) * -1
                gx = xx[i] + (-lx) * radius * 0.45 * S
                gy = yy[i] + (-ly) * radius * 0.45 * S
                r = max(1, radius * 0.12 * S)
                ys_, xs_ = np.ogrid[:m.shape[0], :m.shape[1]]
                dot = ((xs_ - gx) ** 2 + (ys_ - gy) ** 2 <= r * r) & m
                col[dot, :3] = (255, 252, 240)
        col[m, 3] = 255
        self.im.alpha_composite(Image.fromarray(col, 'RGBA'))
        if outline:
            oc = outline_color or tuple(np.clip(np.asarray(base[:3]) * 0.16 + np.array([18, 8, 22]), 0, 255))
            ring = outline_mask(mask, px(outline))
            self.im.paste(Image.new('RGBA', mask.size, rgba(oc)), (0, 0), ring)

    def shape(self, base, draw_fn, **kw):
        m = mask_of(self.size, draw_fn)
        self.paint(m, base, **kw)
        return m

    def line(self, pts, color, width=2):
        SD(self.im).line(pts, fill=rgba(color), width=width, joint='curve')

    def over(self, other, xy=(0, 0)):
        self.im.alpha_composite(other.im if isinstance(other, Layer) else other, xy)


def linear_shade(size, mask, base, angle=0.0, lo=0.3, hi=0.85, bands=7, dither=True, noise=0.0, seed=1):
    """A flat surface with a banded gradient (walls and floors). size is real."""
    w, h = size
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    ca, sa = math.cos(angle), math.sin(angle)
    proj = xx * ca + yy * sa
    m = np.asarray(mask) > 127
    if not m.any():
        return Image.new('RGBA', size, (0, 0, 0, 0))
    pmin, pmax = proj[m].min(), proj[m].max()
    t = lo + (hi - lo) * (1 - (proj - pmin) / max(1, pmax - pmin))
    if noise:
        rng = np.random.default_rng(seed)
        t = t + ndimage.gaussian_filter(rng.normal(0, noise, (h, w)), 1.2 * S)
    tq = quantize(np.clip(t, 0, 1), bands, dither)
    col = ramp(base, tq)
    out = np.zeros((h, w, 4), dtype=np.uint8)
    out[..., :3] = np.clip(col, 0, 255)
    out[..., 3] = m * 255
    return Image.fromarray(out, 'RGBA')


def light_pool(im, cx, cy, rx, ry, strength=0.25, color=(255, 214, 140)):
    """A pool of light (design coordinates), banded and dithered."""
    cx, cy, rx, ry = cx * S, cy * S, rx * S, ry * S
    a = np.asarray(im, dtype=np.float32).copy()
    h, w = a.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    r = np.sqrt(((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2)
    k = quantize(np.clip(1 - r, 0, 1), 5) * strength
    c = np.array(color, dtype=np.float32)
    a[..., :3] = a[..., :3] * (1 - k[..., None]) + (a[..., :3] * 0.8 + c * 0.5) * k[..., None]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), im.mode)


def vignette(im, strength=0.35):
    a = np.asarray(im, dtype=np.float32).copy()
    h, w = a.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    r = np.sqrt(((xx - w / 2) / (w * 0.62)) ** 2 + ((yy - h * 0.45) / (h * 0.75)) ** 2)
    k = quantize(np.clip(r - 0.55, 0, 1) * 1.6, 5) * strength
    tint = np.array([40, 20, 60], dtype=np.float32)
    a[..., :3] = a[..., :3] * (1 - k[..., None]) + tint * k[..., None]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), im.mode)


def cast_shadow(im, mask, strength=0.4, offset=(14, 8)):
    """A hard-edged cast shadow (cartoon style), offset down and right."""
    s = ImageChops.offset(mask, px(offset[0]), px(offset[1]))
    k = (np.asarray(s, dtype=np.float32) / 255 > 0.5) * strength
    a = np.asarray(im, dtype=np.float32).copy()
    tint = np.array([60, 26, 80], dtype=np.float32)
    a[..., :3] = a[..., :3] * (1 - k[..., None]) + tint * 0.5 * k[..., None]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), im.mode)


def wonky(im, lean=0.06, sway=4.0, cx=None):
    """Crooked, hand-drawn perspective: verticals lean out towards the top
    and the room sways a little."""
    a = np.asarray(im)
    h, w = a.shape[:2]
    cx = w / 2 if cx is None else cx * S
    sway = sway * S
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    f = 1 + lean * (1 - yy / h) ** 1.5
    src_x = cx + (xx - cx) / f + sway * np.sin(yy / h * math.pi * 1.3)
    src_y = yy + sway * 0.6 * np.sin(xx / w * math.pi * 2)
    out = np.empty_like(a)
    for c in range(a.shape[2]):
        out[..., c] = ndimage.map_coordinates(a[..., c], [src_y, src_x], order=0, mode='nearest')
    return Image.fromarray(out, im.mode)
