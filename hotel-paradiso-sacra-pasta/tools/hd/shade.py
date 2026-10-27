"""Shaded drawing toolkit for the high-resolution art.

The look is borrowed from the LucasArts cartoon games of the early 90s:
every shape is lit from the upper left, shaded in a handful of bands that
shift towards cool purple in the shadows and warm yellow in the highlights,
and finished with a dark outline in a deeper version of its own colour
(not black). Volume comes from the shape itself: the distance from each
pixel to the shape's edge is turned into a dome, the dome into normals, and
the normals into light.
"""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops
from scipy import ndimage

LIGHT = np.array([-0.55, -0.7, 0.62])
LIGHT = LIGHT / np.linalg.norm(LIGHT)
SHADOW_TINT = np.array([58, 30, 92], dtype=np.float32)    # shadows lean violet
LIGHT_TINT = np.array([255, 236, 176], dtype=np.float32)  # highlights lean warm
BAYER4 = (np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) + 0.5) / 16


def rgba(c, a=255):
    return tuple(int(v) for v in c[:3]) + (a,)


def ramp(base, t):
    """t: array in [0,1]; 0 = deep shadow, ~0.6 = base colour, 1 = highlight."""
    base = np.asarray(base[:3], dtype=np.float32)
    dark = base * 0.42 + SHADOW_TINT * 0.28
    light = base * 0.62 + LIGHT_TINT * 0.38
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


def mask_of(size, draw_fn):
    m = Image.new('L', size, 0)
    draw_fn(ImageDraw.Draw(m))
    return m


def outline_mask(m, width=2):
    a = m.point(lambda v: 255 if v > 127 else 0)
    g = a
    for _ in range(width):
        g = g.filter(ImageFilter.MaxFilter(3))
    return ImageChops.subtract(g, a)


def dome_light(mask_arr, radius, flat=0.0, light=LIGHT, vert=0.25):
    """Lambert lighting of a pillow-shaped surface filling mask_arr."""
    d = ndimage.distance_transform_edt(mask_arr)
    x = np.clip(d / max(radius, 1), 0, 1)
    height = np.sqrt(1 - (1 - x) ** 2) * radius
    height = ndimage.gaussian_filter(height, 0.8)
    gy, gx = np.gradient(height)
    nx, ny, nz = -gx, -gy, np.ones_like(gx) * (1.0 + flat * 6)
    n = np.sqrt(nx * nx + ny * ny + nz * nz)
    lam = (nx * light[0] + ny * light[1] + nz * light[2]) / n
    lam = np.clip(lam, 0, 1)
    # a little top-to-bottom falloff inside the shape
    ys = np.nonzero(mask_arr)[0]
    if len(ys):
        y0, y1 = ys.min(), ys.max() + 1
        rows = np.arange(mask_arr.shape[0])[:, None]
        v = 1 - np.clip((rows - y0) / max(1, y1 - y0), 0, 1)
        lam = lam * (1 - vert) + vert * v * lam + vert * 0.5 * v
    return np.clip(lam, 0, 1)


class Layer:
    """An RGBA canvas that shaded shapes are painted onto."""

    def __init__(self, w, h):
        self.w, self.h = w, h
        self.im = Image.new('RGBA', (w, h), (0, 0, 0, 0))

    def paint(self, mask, base, radius=10, bands=6, outline=2, flat=0.0, spec=False, dither=True,
              outline_color=None, gloss=0.0, light=LIGHT, texture=None):
        """Paint a shaded shape. mask: 'L' image of the canvas size."""
        m = np.asarray(mask) > 127
        if not m.any():
            return
        ys, xs = np.nonzero(m)
        y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
        pad = 4
        y0p, x0p = max(0, y0 - pad), max(0, x0 - pad)
        y1p, x1p = min(self.h, y1 + pad), min(self.w, x1 + pad)
        sub = m[y0p:y1p, x0p:x1p]
        lam = dome_light(sub, radius, flat, light)
        t = 0.18 + lam * 0.82
        if texture is not None:
            t = np.clip(t + texture[y0p:y1p, x0p:x1p], 0, 1)
        if spec or gloss:
            s = np.clip((lam - 0.86) / 0.14, 0, 1) ** 2 * (gloss or 1.0)
            t = np.clip(t + s * 0.6, 0, 1)
        tq = quantize(t, bands, dither)
        col = ramp(base, tq)
        if spec:
            hot = lam > 0.97
            col[hot] = np.array([255, 252, 236])
        rgba_arr = np.zeros(sub.shape + (4,), dtype=np.uint8)
        rgba_arr[..., :3] = np.clip(col, 0, 255).astype(np.uint8)
        rgba_arr[..., 3] = sub * 255
        piece = Image.fromarray(rgba_arr, 'RGBA')
        self.im.alpha_composite(piece, (int(x0p), int(y0p)))
        if outline:
            oc = outline_color or tuple(np.clip(np.asarray(base[:3]) * 0.28 + np.array([20, 8, 24]), 0, 255))
            ring = outline_mask(mask, outline)
            self.im.paste(Image.new('RGBA', mask.size, rgba(oc)), (0, 0), ring)

    def shape(self, base, draw_fn, **kw):
        m = mask_of((self.w, self.h), draw_fn)
        self.paint(m, base, **kw)
        return m

    def flat(self, color, draw_fn):
        d = ImageDraw.Draw(self.im)
        draw_fn(d, rgba(color))

    def line(self, pts, color, width=2):
        ImageDraw.Draw(self.im).line(pts, fill=rgba(color), width=width, joint='curve')

    def over(self, other, xy=(0, 0)):
        self.im.alpha_composite(other.im if isinstance(other, Layer) else other, xy)


def linear_shade(size, mask, base, angle=0.0, lo=0.3, hi=0.85, bands=7, dither=True, noise=0.0, seed=1):
    """A flat surface lit by a gradient (for walls and floors)."""
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
        t = t + ndimage.gaussian_filter(rng.normal(0, noise, (h, w)), 1.2)
    tq = quantize(np.clip(t, 0, 1), bands, dither)
    col = ramp(base, tq)
    out = np.zeros((h, w, 4), dtype=np.uint8)
    out[..., :3] = np.clip(col, 0, 255)
    out[..., 3] = m * 255
    return Image.fromarray(out, 'RGBA')


def light_pool(im, cx, cy, rx, ry, strength=0.25, color=(255, 214, 140)):
    """Warm pool of lamplight: brightens the image inside an ellipse, banded."""
    a = np.asarray(im, dtype=np.float32).copy()
    h, w = a.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    r = np.sqrt(((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2)
    k = np.clip(1 - r, 0, 1)
    k = quantize(k, 6) * strength
    c = np.array(color, dtype=np.float32)
    a[..., :3] = a[..., :3] * (1 - k[..., None]) + (a[..., :3] * 0.5 + c * 0.5 + a[..., :3] * 0.3) * k[..., None]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), im.mode)


def vignette(im, strength=0.35):
    a = np.asarray(im, dtype=np.float32).copy()
    h, w = a.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    r = np.sqrt(((xx - w / 2) / (w * 0.62)) ** 2 + ((yy - h * 0.45) / (h * 0.75)) ** 2)
    k = quantize(np.clip(r - 0.55, 0, 1) * 1.6, 6) * strength
    tint = np.array([40, 20, 60], dtype=np.float32)
    a[..., :3] = a[..., :3] * (1 - k[..., None]) + tint * k[..., None]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), im.mode)


def soft_shadow(im, mask, strength=0.45, blur=6, offset=(10, 6)):
    """Darken `im` under a (blurred, offset, banded) shadow mask."""
    s = mask.filter(ImageFilter.GaussianBlur(blur))
    s = ImageChops.offset(s, *offset)
    k = quantize(np.asarray(s, dtype=np.float32) / 255, 4) * strength
    a = np.asarray(im, dtype=np.float32).copy()
    tint = np.array([40, 18, 60], dtype=np.float32)
    a[..., :3] = a[..., :3] * (1 - k[..., None]) + tint * k[..., None] * 0.6
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), im.mode)


def wonky(im, lean=0.06, sway=4.0, cx=None):
    """LucasArts-style crooked perspective: verticals lean out towards the
    top and the whole room sways a little, like it was drawn by hand."""
    a = np.asarray(im)
    h, w = a.shape[:2]
    cx = w / 2 if cx is None else cx
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    f = 1 + lean * (1 - yy / h) ** 1.5
    src_x = cx + (xx - cx) / f + sway * np.sin(yy / h * math.pi * 1.3)
    src_y = yy + sway * 0.6 * np.sin(xx / w * math.pi * 2)
    out = np.empty_like(a)
    for c in range(a.shape[2]):
        out[..., c] = ndimage.map_coordinates(a[..., c], [src_y, src_x], order=0, mode='nearest')
    return Image.fromarray(out, im.mode)
