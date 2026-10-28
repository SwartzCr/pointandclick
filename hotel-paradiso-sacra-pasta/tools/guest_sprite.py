"""The guest, from a turnaround sheet of pixel art.

art_src/bellhop_front_back.jpg holds the front and back views and
art_src/bellhop_sides.jpg the two side views, all on magenta. Each view is
keyed, scaled to 100 px tall, reduced to a small palette and given a hard
edge. Every frame the game needs comes from those views:

- standing: the view itself (west is AGS's mirror of the east-facing view)
- walking: front/back lift each leg in turn; the side view scissors the legs
  (a darker copy swings back as the far leg) and the body bobs
- talking: the mouth opens
- the beads and the UV pendant are drawn on at the collar
"""
import math
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.join(HERE, '..', 'art_src')

ART_H = 150               # the views are scaled to this height (the painted Nave is drawn big)
FW, FH = 72, ART_H + 4    # the AGS frame, feet on the bottom row
INK = (20, 12, 16, 255)

# landmarks in each view, measured at 100 px tall (x, y); scaled to ART_H below
LAND100 = {
    'front': dict(hip=61, legs=(9, 31), split=20, mouth=(20, 21), collar=(19, 27)),
    'back': dict(hip=61, legs=(9, 31), split=20, mouth=None, collar=(19, 27)),
    'side': dict(hip=62, legs=(0, 25), split=None, mouth=(17, 21), collar=(13, 27)),
}



def _sc(v):
    k = ART_H / 100
    if v is None:
        return None
    if isinstance(v, tuple):
        return tuple(int(round(t * k)) for t in v)
    return int(round(v * k))


LAND = {view: {key: (val if key == 'split' and val is None else _sc(val)) for key, val in d.items()}
        for view, d in LAND100.items()}

_views = None


def _figures(name):
    """The figures on one sheet, left to right, keyed off the magenta."""
    a = np.asarray(Image.open(os.path.join(ART, name)).convert('RGB')).astype(int)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    # magenta (and the JPEG's pinkish fringe) is background
    mag = (r - g > 70) & (b - g > 70) & (r > 120) & (b > 120)
    fg = ndimage.binary_opening(~mag, iterations=2)
    lab, n = ndimage.label(fg)
    objs = ndimage.find_objects(lab)
    sizes = ndimage.sum(fg, lab, range(1, n + 1))
    figs = []
    for i in range(n):
        if sizes[i] < 20000:
            continue
        sl = objs[i]
        m = ndimage.binary_erosion(lab[sl] == i + 1, iterations=2)   # drop the fringe
        rgba = np.dstack([a[sl], m * 255]).astype(np.uint8)
        figs.append((sl[1].start, Image.fromarray(rgba, 'RGBA')))
    return [f for _, f in sorted(figs, key=lambda t: t[0])]


def _shrink(im):
    w = round(im.width * ART_H / im.height)
    # scale colour and alpha separately so the background doesn't bleed in
    a = np.asarray(im).astype(float)
    alpha = a[..., 3:] / 255
    pre = Image.fromarray((a[..., :3] * alpha).astype(np.uint8))
    cov = Image.fromarray((alpha[..., 0] * 255).astype(np.uint8))
    pre = np.asarray(pre.resize((w, ART_H), Image.LANCZOS)).astype(float)
    cov = np.asarray(cov.resize((w, ART_H), Image.LANCZOS)).astype(float) / 255
    rgb = np.clip(pre / np.maximum(cov, 1e-3)[..., None], 0, 255).astype(np.uint8)
    out = Image.fromarray(rgb).quantize(28, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).convert('RGBA')
    out.putalpha(Image.fromarray(np.where(cov >= 0.5, 255, 0).astype(np.uint8)))
    return out


def views():
    global _views
    if _views is None:
        front, back = _figures('bellhop_front_back.jpg')
        left, right = _figures('bellhop_sides.jpg')
        _views = {'front': _shrink(front), 'back': _shrink(back), 'side': _shrink(right)}
    return {k: v.copy() for k, v in _views.items()}


# ---------------------------------------------------------------- pieces
def _skin(a):
    r, g, b = a[..., 0].astype(int), a[..., 1].astype(int), a[..., 2].astype(int)
    return (r > 150) & (g > 95) & (b > 60) & (r - b > 40)


def _split(art, view):
    """Torso (with arms and hands) and the leg layer(s)."""
    L = LAND[view]
    a = np.asarray(art).copy()
    h, w = a.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    op = a[..., 3] > 0
    x0, x1 = L['legs']
    legs = op & (yy >= L['hip']) & (xx >= x0) & (xx < x1)
    if view == 'side':
        # the hand and cuff hang in front of the thigh: keep them on the torso
        dark = a[..., :3].astype(int).sum(-1) < 120
        legs &= ~_skin(a) & ~((yy < _sc(70)) & dark)
        hand = ndimage.binary_dilation(op & (yy >= L['hip']) & (yy < _sc(74)) & _skin(a), iterations=1)
        legs &= ~hand

    def layer(m):
        b = np.zeros_like(a)
        b[m] = a[m]
        return Image.fromarray(b, 'RGBA')

    torso = layer(op & ~legs)
    if L['split'] is None:
        return torso, [layer(legs)]
    return torso, [layer(legs & (xx < L['split'])), layer(legs & (xx >= L['split']))]


def _swing(leg, hip, amount, lift):
    """Swing a leg from the hip: rows shift sideways more the lower they are,
    and the foot lifts."""
    a = np.asarray(leg)
    out = np.zeros_like(a)
    h = a.shape[0]
    for y in range(hip, h):
        t = (y - hip) / max(1, h - 1 - hip)
        dx = int(round(amount * t))
        ny = y - int(round(lift * t))
        row = np.roll(a[y], dx, axis=0)
        if dx > 0:
            row[:dx] = 0
        elif dx < 0:
            row[dx:] = 0
        m = row[:, 3] > 0
        out[ny][m] = row[m]
    return Image.fromarray(out, 'RGBA')


def _talk(art, view):
    x, y = LAND[view]['mouth']
    d = ImageDraw.Draw(art)
    if view == 'front':
        d.rectangle([x - 3, y, x + 2, y + 2], fill=(70, 20, 24, 255))
        d.rectangle([x - 2, y + 2, x + 1, y + 2], fill=(170, 60, 60, 255))
    else:
        d.rectangle([x, y, x + 3, y + 2], fill=(70, 20, 24, 255))
    return art


def _neck(art, kind, view):
    """Beads and pendant, drawn as on the old sprite."""
    import art_people
    P = {k: art_people._P(v) for k, v in art_people.GUEST.items()}
    k = ART_H / 100
    lay = Image.new('RGBA', (int(art.width / k) + 2, int(art.height / k) + 2), (0, 0, 0, 0))
    cx, y = LAND100[view]['collar']
    art_people._neckwear(ImageDraw.Draw(lay), P, cx, y, kind, view)
    lay = lay.resize((int(lay.width * k), int(lay.height * k)), Image.NEAREST)
    art.alpha_composite(lay.crop((0, 0, art.width, art.height)))
    return art


def _outline(im):
    a = im.getchannel('A')
    ring = Image.eval(a.filter(ImageFilter.MaxFilter(3)), lambda v: v)
    out = Image.new('RGBA', im.size, (0, 0, 0, 0))
    out.paste(Image.new('RGBA', im.size, INK), (0, 0), ring)
    out.alpha_composite(im)
    return out


# ---------------------------------------------------------------- frames
def guest_frame(direction, phase=0.0, walking=False, talk=False, kind=None, blink=False):
    """direction: front, side (facing east) or back. Same signature as before."""
    art = views()[direction]
    L = LAND[direction]
    torso, legs = _split(art, direction)
    bob = 0
    if walking:
        s = math.sin(phase * 2 * math.pi)
        bob = int(round(abs(s)))
        if direction == 'side':
            leg = legs[0]
            near = _swing(leg, L['hip'], 7 * s, max(0, -s) * 3)
            far = _swing(leg, L['hip'], -7 * s, max(0, s) * 3)
            far = ImageEnhance.Brightness(far).enhance(0.62)
            legs = [far, near]
        else:
            legs = [_swing(legs[0], L['hip'], 0, max(0, s) * 4), _swing(legs[1], L['hip'], 0, max(0, -s) * 4)]
    lay = Image.new('RGBA', art.size, (0, 0, 0, 0))
    for leg in legs:
        lay.alpha_composite(leg)
    if walking:
        lay = _outline(lay)
    body = Image.new('RGBA', art.size, (0, 0, 0, 0))
    body.alpha_composite(lay)
    body.alpha_composite(torso)
    if talk and L['mouth']:
        body = _talk(body, direction)
    if kind:
        body = _neck(body, kind, direction)
    frame = Image.new('RGBA', (FW, FH), (0, 0, 0, 0))
    frame.alpha_composite(body, ((FW - art.width) // 2, FH - ART_H - bob))
    return frame


def guest_seated():
    """For the Pope Seat: the front view's upper body over short seated legs (48x80)."""
    art = views()['front']
    art = art.resize((round(art.width * 100 / ART_H), 100), Image.LANCZOS)
    art.putalpha(art.getchannel('A').point(lambda v: 255 if v >= 128 else 0))
    hip = LAND100['front']['hip']
    FW = 48
    upper = art.crop((0, 0, art.width, hip + 10))
    im = Image.new('RGBA', (FW, 80), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    ox = (FW - art.width) // 2
    for x in (ox + 10, ox + 21):
        d.rectangle([x - 1, 68, x + 9, 79], fill=INK)
        d.rectangle([x, 68, x + 8, 75], fill=(170, 26, 24, 255))
        d.rectangle([x, 76, x + 8, 78], fill=(40, 26, 22, 255))
    im.alpha_composite(upper, (ox, 80 - (hip + 10) - 6))
    return im


if __name__ == '__main__':
    import sys
    sys.path.insert(0, HERE)
    sheet = Image.new('RGBA', (FW * 12, FH * 3), (90, 80, 100, 255))
    for r, dr in enumerate(('side', 'front', 'back')):
        frames = [guest_frame(dr)] + [guest_frame(dr, (i + 1) / 8, True) for i in range(8)]
        frames += [guest_frame(dr, talk=True), guest_frame(dr, kind={'beads': True, 'uv': True})]
        for k, f in enumerate(frames):
            sheet.alpha_composite(f, (k * FW, r * FH))
    sheet.alpha_composite(guest_seated(), (11 * FW, 0))
    out = sys.argv[1] if len(sys.argv) > 1 else '/tmp/claude-0/bh/sheet.png'
    sheet.resize((sheet.width * 3, sheet.height * 3), Image.NEAREST).save(out)
