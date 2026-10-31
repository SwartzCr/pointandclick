"""Inventory icons from generated art (art_src/icons/<item>.png, one item on magenta each).

The magenta is keyed out, the generator's little sparkle in the bottom-right corner is
dropped, and the item is cropped and shrunk to fit the inventory slot."""
import os
import numpy as np
from PIL import Image
from scipy import ndimage

from art_ui import ICON_W, ICON_H

HERE = os.path.dirname(os.path.abspath(__file__))
DIR = os.path.join(HERE, '..', 'art_src', 'icons')


def item(name, w, h):
    """The item itself, fitted inside w x h (no padding), for placing in a room."""
    im = load(os.path.join(DIR, name + '.png'), w, h, pad=False)
    return im


def load(path, w=ICON_W - 2, h=ICON_H - 2, pad=True):
    im = Image.open(path).convert('RGB')
    a = np.asarray(im).astype(int)
    mag = (np.abs(a[..., 0] - 255) + a[..., 1] + np.abs(a[..., 2] - 255)) < 150
    # pinkish halo pixels next to magenta (soft glows, antialiasing) count as background too
    pinkish = (a[..., 0] > 200) & (a[..., 2] > 200) & (a[..., 1] < 140)
    fg = ~(mag | pinkish)
    fg = ndimage.binary_opening(fg, iterations=2)
    lab, n = ndimage.label(fg)
    H, Wd = fg.shape
    keep = np.zeros_like(fg)
    for k in range(1, n + 1):
        ys, xs = np.nonzero(lab == k)
        if xs.mean() > Wd * 0.9 and ys.mean() > H * 0.85:     # the corner sparkle
            continue
        if len(xs) < 40:
            continue
        keep |= lab == k
    rgba = np.dstack([a.astype(np.uint8), (keep * 255).astype(np.uint8)])
    out = Image.fromarray(rgba, 'RGBA')
    out = out.crop(out.getbbox())
    s = min(w / out.width, h / out.height)
    out = out.resize((max(1, round(out.width * s)), max(1, round(out.height * s))), Image.LANCZOS)
    o = np.asarray(out).copy()
    o[..., 3] = np.where(o[..., 3] > 120, 255, 0)
    out = Image.fromarray(o, 'RGBA')
    if not pad:
        return out
    icon = Image.new('RGBA', (ICON_W, ICON_H), (0, 0, 0, 0))
    icon.alpha_composite(out, ((ICON_W - out.width) // 2, (ICON_H - out.height) // 2))
    return icon


def icons():
    out = {}
    if os.path.isdir(DIR):
        for f in sorted(os.listdir(DIR)):
            if f.endswith('.png'):
                out[f[:-4]] = load(os.path.join(DIR, f))
    return out
