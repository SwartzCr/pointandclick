"""Shared drawing helpers for the procedural pixel art."""
import math
import random
from PIL import Image, ImageDraw, ImageFilter, ImageChops, ImageFont

OUTLINE = (34, 22, 30, 255)
CLEAR = (0, 0, 0, 0)


def rgba(c, a=255):
    return tuple(c[:3]) + (a,)


def canvas(w, h, fill=CLEAR):
    return Image.new('RGBA', (w, h), fill)


def mix(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def shade(c, f):
    """f < 1 darkens, f > 1 lightens towards white."""
    if f <= 1:
        return tuple(int(v * f) for v in c[:3])
    return mix(c, (255, 255, 255), f - 1)


def outline(im, color=OUTLINE, thick=1):
    """Draw a 1px dark outline around everything opaque in `im`."""
    a = im.getchannel('A').point(lambda v: 255 if v > 0 else 0)
    grown = a
    for _ in range(thick):
        grown = grown.filter(ImageFilter.MaxFilter(3))
    ring = ImageChops.subtract(grown, a)
    base = Image.new('RGBA', im.size, color)
    out = Image.new('RGBA', im.size, CLEAR)
    out.paste(base, (0, 0), ring)
    out.alpha_composite(im)
    return out


def limb(d, p0, p1, w, col, cap=True):
    """Thick segment from p0 to p1 with round ends."""
    (x0, y0), (x1, y1) = p0, p1
    dx, dy = x1 - x0, y1 - y0
    ln = math.hypot(dx, dy) or 1
    nx, ny = -dy / ln * w / 2, dx / ln * w / 2
    d.polygon([(x0 + nx, y0 + ny), (x1 + nx, y1 + ny), (x1 - nx, y1 - ny), (x0 - nx, y0 - ny)],
              fill=col)
    if cap:
        r = w / 2 - 0.3
        d.ellipse([x0 - r, y0 - r, x0 + r, y0 + r], fill=col)
        d.ellipse([x1 - r, y1 - r, x1 + r, y1 + r], fill=col)


def vgrad(d, box, top, bottom, steps=None, dither=True):
    """Vertical gradient with ordered dithering between bands."""
    x0, y0, x1, y1 = box
    h = y1 - y0 + 1
    for y in range(y0, y1 + 1):
        t = (y - y0) / max(1, h - 1)
        if dither:
            # 2x2 bayer between the two nearest of 8 bands
            band = t * 7
            lo = int(band)
            frac = band - lo
            c_lo = mix(top, bottom, lo / 7)
            c_hi = mix(top, bottom, min(7, lo + 1) / 7)
            for x in range(x0, x1 + 1):
                thr = [0.125, 0.625, 0.875, 0.375][(x & 1) + 2 * (y & 1)]
                d.point((x, y), fill=rgba(c_hi if frac > thr else c_lo))
        else:
            d.line([(x0, y), (x1, y)], fill=rgba(mix(top, bottom, t)))


def dither_rect(d, box, c1, c2, pattern=0.5):
    x0, y0, x1, y1 = box
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            thr = [0.125, 0.625, 0.875, 0.375][(x & 1) + 2 * (y & 1)]
            d.point((x, y), fill=rgba(c2 if pattern > thr else c1))


def noise(d, box, base, amount, rnd, density=0.25):
    x0, y0, x1, y1 = box
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if rnd.random() < density:
                d.point((x, y), fill=rgba(shade(base, 1 + rnd.uniform(-amount, amount))))


FONT_PATH = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
_fonts = {}


def font(size):
    if size not in _fonts:
        _fonts[size] = ImageFont.truetype(FONT_PATH, size)
    return _fonts[size]


def text(d, xy, s, size, fill, anchor='la'):
    d.fontmode = '1'
    d.text(xy, s, font=font(size), fill=rgba(fill), anchor=anchor)
