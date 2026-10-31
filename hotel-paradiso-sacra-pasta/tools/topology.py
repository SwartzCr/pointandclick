"""The four Sacred Topology shapes Chuk brings out of the staff room, and the Pope Seat's
crank: drawn here so the inventory icons and the shapes on the Pasta Identification board
match. Pale marble, not pasta-coloured, so you can't tell which pasta each one 'is'."""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

SHAPES = ['trefoil', 'infinity', 'mobius', 'torus']
NAMES = {'trefoil': 'three-lobed knot', 'infinity': 'figure-eight loop', 'mobius': 'twisted band',
         'torus': 'stone ring'}
MARBLE, MARBLE_HI, MARBLE_DK, EDGE = (222, 214, 196), (248, 244, 232), (160, 150, 136), (52, 40, 44)


def _tube(d, pts, w, S):
    d.line(pts, fill=EDGE, width=int(w * S) + 2 * S, joint='curve')
    d.line(pts, fill=MARBLE, width=int(w * S), joint='curve')
    hi = [(x - 0.25 * w * S, y - 0.25 * w * S) for x, y in pts]
    d.line(hi, fill=MARBLE_HI, width=max(1, int(w * S * 0.3)), joint='curve')


def shape(name, w, h):
    """The shape on a transparent w x h canvas (drawn 4x bigger, then shrunk)."""
    S = 4
    im = Image.new('RGBA', (w * S, h * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cx, cy = w * S / 2, h * S / 2
    r = min(w, h) * S * 0.42
    tw = max(2.0, min(w, h) * 0.13)
    if name == 'trefoil':
        pts = [(cx + r * 0.33 * (math.sin(t) + 2 * math.sin(2 * t)), cy + r * 0.33 * (math.cos(t) - 2 * math.cos(2 * t)))
               for t in np.linspace(0, 2 * math.pi, 240)]
        _tube(d, pts, tw, S)
        # redraw one crossing on top, so it reads as a knot
        seg = pts[30:60]
        _tube(d, seg, tw, S)
    elif name == 'infinity':
        rx = w * S * 0.46
        pts = [(cx + rx * math.cos(t) / (1 + math.sin(t) ** 2), cy + rx * math.sin(t) * math.cos(t) / (1 + math.sin(t) ** 2) * 1.2)
               for t in np.linspace(0, 2 * math.pi, 240)]
        _tube(d, pts, tw, S)
        _tube(d, pts[50:75], tw, S)
    elif name == 'mobius':
        # a flat ribbon round an ellipse, its width going through zero once: the half-twist
        a, b, bw = w * S * 0.36, h * S * 0.28, min(w, h) * S * 0.13
        ts = np.linspace(0, 2 * math.pi, 160)

        def edge(t, sgn):
            x, y = cx + a * math.cos(t), cy + b * math.sin(t)
            nx, ny = b * math.cos(t), a * math.sin(t)
            n = math.hypot(nx, ny)
            off = sgn * bw * (0.25 + 0.75 * abs(math.cos(t / 2))) * (1 if math.cos(t / 2) >= 0 else -1)
            return x + nx / n * off, y + ny / n * off
        for k in range(len(ts) - 1):
            t0, t1 = ts[k], ts[k + 1]
            poly = [edge(t0, 1), edge(t1, 1), edge(t1, -1), edge(t0, -1)]
            c = math.cos(t0 / 2) * math.sin(t0)
            d.polygon(poly, fill=MARBLE_HI if math.cos(t0 / 2) > 0 else MARBLE_DK)
        d.line([edge(t, 1) for t in ts], fill=EDGE, width=S)
        d.line([edge(t, -1) for t in ts], fill=EDGE, width=S)
    else:   # torus
        a, b = w * S * 0.44, h * S * 0.34
        d.ellipse([cx - a, cy - b, cx + a, cy + b], fill=MARBLE, outline=EDGE, width=S)
        d.ellipse([cx - a * 0.8, cy - b * 0.85, cx + a * 0.6, cy + b * 0.2], fill=MARBLE_HI)
        d.ellipse([cx - a * 0.45, cy - b * 0.3, cx + a * 0.45, cy + b * 0.22], fill=MARBLE_DK, outline=EDGE, width=S)
        d.ellipse([cx - a * 0.4, cy - b * 0.25, cx + a * 0.4, cy + b * 0.12], fill=(0, 0, 0, 0))
    out = im.resize((w, h), Image.LANCZOS)
    a = np.asarray(out).copy()
    a[..., 3] = np.where(a[..., 3] > 110, 255, 0)
    return Image.fromarray(a, 'RGBA')


def crank(w, h):
    S = 4
    im = Image.new('RGBA', (w * S, h * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    iron, iron_hi, wood = (78, 76, 92), (140, 140, 158), (150, 96, 50)
    cx, cy, r = w * S * 0.3, h * S * 0.5, min(w, h) * S * 0.3
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=iron, outline=EDGE, width=S)
    d.ellipse([cx - r * 0.35, cy - r * 0.35, cx + r * 0.35, cy + r * 0.35], fill=iron_hi)
    ex, ey = w * S * 0.78, h * S * 0.75
    d.line([(cx, cy), (ex, ey)], fill=EDGE, width=int(r * 0.45) + 2 * S)
    d.line([(cx, cy), (ex, ey)], fill=iron, width=int(r * 0.45))
    d.rounded_rectangle([ex - 2 * S, ey - 5 * S, ex + 3 * S, ey + 4 * S], 2 * S, fill=wood, outline=EDGE, width=S)
    out = im.resize((w, h), Image.LANCZOS)
    a = np.asarray(out).copy()
    a[..., 3] = np.where(a[..., 3] > 110, 255, 0)
    return Image.fromarray(a, 'RGBA')
