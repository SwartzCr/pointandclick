"""Khuc, from his sprite sheet (art_src/khuc_sheet.jpg, figures on magenta).

Top row: front, back, facing right, facing left, two head close-ups.
Bottom row: four walking frames facing right, arms raised, hunched from
behind (playing T. rex), turning a crank. The bottom row is drawn smaller
than the top, so each row gets its own scale to bring him to KH px tall.
"""
import os
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

from guest_sprite import _shrink

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, '..', 'art_src', 'khuc_sheet.jpg')
KH = 110                       # standing height in game pixels (the bellhop is 100)
TOP_H, BOTTOM_H = 395, 310     # a standing Khuc's height on each row of the sheet

_cut = None


def _figures():
    a = np.asarray(Image.open(SRC).convert('RGB')).astype(int)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    mag = (r - g > 70) & (b - g > 70) & (r > 120) & (b > 120)
    fg = ndimage.binary_opening(~mag, iterations=2)
    lab, n = ndimage.label(fg)
    objs = ndimage.find_objects(lab)
    sizes = ndimage.sum(fg, lab, range(1, n + 1))
    figs = []
    for i in range(n):
        if sizes[i] < 3000:
            continue
        sl = objs[i]
        m = ndimage.binary_erosion(lab[sl] == i + 1, iterations=2)
        rgba = np.dstack([a[sl], m * 255]).astype(np.uint8)
        row = 0 if sl[0].start < 300 else 1
        figs.append((row, sl[1].start, Image.fromarray(rgba, 'RGBA')))
    figs.sort(key=lambda t: (t[0], t[1]))
    top = [f for r_, _, f in figs if r_ == 0]
    bottom = [f for r_, _, f in figs if r_ == 1]
    return top, bottom


def _scaled(im, sheet_h):
    """Shrink a figure by its row's scale (so poses keep their relative size)."""
    h = max(1, round(im.height * KH / sheet_h))
    w = max(1, round(im.width * KH / sheet_h))
    big = Image.new('RGBA', (im.width, im.height))
    big.alpha_composite(im)
    # _shrink scales to guest_sprite.ART_H; do it by hand here for our own height
    import guest_sprite as GS
    keep = GS.ART_H
    GS.ART_H = h
    out = _shrink(big)
    GS.ART_H = keep
    return out


def cut():
    global _cut
    if _cut is None:
        top, bottom = _figures()
        front, back, right, left, head, head_talk = top
        walk = bottom[0:4]
        raise_, play, crank = bottom[4], bottom[5], bottom[6]
        _cut = {
            'front': _scaled(front, TOP_H), 'back': _scaled(back, TOP_H), 'side': _scaled(right, TOP_H),
            'walk': [_scaled(w, BOTTOM_H) for w in walk],
            'raise': _scaled(raise_, BOTTOM_H), 'play': _scaled(play, BOTTOM_H), 'crank': _scaled(crank, BOTTOM_H),
        }
    return {k: (v.copy() if isinstance(v, Image.Image) else [x.copy() for x in v]) for k, v in _cut.items()}


def _frame(im, bob=0, pad=2):
    """Put a figure in a frame with its feet on the bottom row, centred."""
    w = im.width + 2 * pad
    f = Image.new('RGBA', (w + (w % 2), im.height + pad), (0, 0, 0, 0))
    f.alpha_composite(im, (pad, pad - bob))
    return f


def _mouth(im, view):
    """Open his mouth: a small dark gap under the moustache."""
    im = im.copy()
    a = np.asarray(im)
    # find the face: the skin pixels in the upper part of the figure
    r, g, b = a[..., 0].astype(int), a[..., 1].astype(int), a[..., 2].astype(int)
    skin = (r > 150) & (g > 100) & (b > 70) & (r - b > 35) & (a[..., 3] > 0)
    top = int(im.height * 0.28)
    ys, xs = np.nonzero(skin[:top])
    if not len(xs):
        return im
    fy0, fy1 = ys.min(), ys.max()
    if view == 'front':
        cx = int(np.median(xs))
    else:
        cx = int(np.percentile(xs, 80))
    my = fy0 + int((fy1 - fy0) * 0.78)
    d = ImageDraw.Draw(im)
    d.rectangle([cx - 1, my, cx + 1, my + 1], fill=(60, 20, 22, 255))
    return im


def views():
    """Frame lists in the shape make_assets expects."""
    c = cut()
    stand = {k: _frame(c[k]) for k in ('front', 'back', 'side')}
    walk_side = [_frame(w) for w in c['walk']]
    # front and back: the robe hides his legs, so the walk is a gentle bob
    walk_front = [_frame(c['front'], bob=b) for b in (1, 0, 1, 0)]
    walk_back = [_frame(c['back'], bob=b) for b in (1, 0, 1, 0)]
    talk_front = [stand['front'], _frame(_mouth(c['front'], 'front'))]
    talk_side = [stand['side'], _frame(_mouth(c['side'], 'side'))]
    play = [_frame(c['play'], bob=b) for b in (0, 1, 0, 1)]
    return dict(stand=stand, walk_side=walk_side, walk_front=walk_front, walk_back=walk_back,
                talk_front=talk_front, talk_side=talk_side, play=play,
                raise_=_frame(c['raise']), crank=_frame(c['crank']))


if __name__ == '__main__':
    v = views()
    frames = [v['stand']['front'], v['stand']['back'], v['stand']['side']] + v['walk_side'] + \
             [v['talk_front'][1], v['talk_side'][1], v['raise_'], v['play'][0], v['crank']]
    W = sum(f.width + 4 for f in frames)
    H = max(f.height for f in frames)
    sheet = Image.new('RGBA', (W, H + 4), (90, 80, 100, 255))
    x = 2
    for f in frames:
        sheet.alpha_composite(f, (x, H + 2 - f.height))
        x += f.width + 4
    sheet.resize((sheet.width * 3, sheet.height * 3), Image.NEAREST).save('/tmp/claude-0/bh/khuc_sheet.png')
