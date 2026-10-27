"""The guest, from a single piece of pixel art (art_src/bellhop.png).

The source is an upscaled pixel-art picture (about 7.2 screen pixels per art
pixel, not quite on an even grid), so it is first sampled back down to its
native 40x100 pixels and its palette tidied. Every frame the game needs is
then made from that one picture:

- side (facing east) is the picture itself; west is the mirror, done by AGS
- walking swings the two legs from the hip and bobs the body
- talking opens the mouth
- front reuses the three-quarter view; back paints the face over with hair
  and drops the frogging from the chest
- the beads and the UV pendant are drawn on top, as before
"""
import math
import os
import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, '..', 'art_src', 'bellhop.png')

FW, FH = 48, 104          # the AGS frame, feet on the bottom row
OX, OY = 4, 4             # where the 40x100 art sits in the frame

# landmarks in the native art (x, y)
HIP_Y = 74                # legs start here
LEG_SPLIT = 24            # columns < this are the far leg, >= the near leg
BELL = (17, 87)           # left of x and above y (below the hip) is the hand and bell
MOUTH = (27, 33)          # left end of the smile
COLLAR = (22, 40)         # centre of the collar

_native = None


def _merge_palette(a, tol=14):
    """Snap colours within tol of a more common colour onto it."""
    flat = a[..., :3].reshape(-1, 3)
    op = a[..., 3].reshape(-1) > 0
    cols, counts = np.unique(flat[op], axis=0, return_counts=True)
    order = np.argsort(-counts)
    keep = []
    remap = {}
    for k in order:
        c = cols[k].astype(int)
        for kc in keep:
            if np.abs(c - kc).max() <= tol:
                remap[tuple(c)] = kc
                break
        else:
            keep.append(c)
            remap[tuple(c)] = c
    out = a.copy()
    for idx in np.nonzero(op)[0]:
        out.reshape(-1, 4)[idx, :3] = remap[tuple(flat[idx].astype(int))]
    return out


def native():
    """The art at its own resolution: 40x100 RGBA, hard alpha, tidy palette."""
    global _native
    if _native is not None:
        return _native.copy()
    im = np.asarray(Image.open(SRC).convert('RGBA')).astype(float)
    H, W = im.shape[:2]
    px, py = 7.22, 7.32              # measured pitch of the art pixels
    ox, oy = 6.25 - px, 6.25 - py    # and where the grid starts
    xs, ys = np.arange(ox, W, px), np.arange(oy, H, py)
    out = np.zeros((len(ys), len(xs), 4))
    for j, y0 in enumerate(ys):
        for i, x0 in enumerate(xs):
            a, b = max(0, int(round(y0 + 1.8))), int(round(y0 + py - 1.8))
            c, d = max(0, int(round(x0 + 1.8))), int(round(x0 + px - 1.8))
            blk = im[a:b, c:d].reshape(-1, 4)
            if len(blk):
                out[j, i] = np.median(blk, 0)
    out[..., 3] = np.where(out[..., 3] > 128, 255, 0)
    out[out[..., 3] == 0] = 0
    img = Image.fromarray(out.astype(np.uint8), 'RGBA')
    img = img.crop(img.getbbox())
    arr = _merge_palette(np.asarray(img).copy())
    # near-black → one black
    dark = (arr[..., :3].astype(int).sum(-1) < 40) & (arr[..., 3] > 0)
    arr[dark, :3] = (12, 8, 16)
    _native = Image.fromarray(arr, 'RGBA')
    return _native.copy()


# ---------------------------------------------------------------- pieces
def _split(art):
    """Torso (with arms and bell), far leg, near leg."""
    a = np.asarray(art).copy()
    h, w = a.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    legs = (yy >= HIP_Y) & ~((xx < BELL[0]) & (yy < BELL[1]))
    far = legs & (xx < LEG_SPLIT)
    near = legs & (xx >= LEG_SPLIT)
    def layer(m):
        b = np.zeros_like(a)
        b[m] = a[m]
        return Image.fromarray(b, 'RGBA')
    return layer(~legs), layer(far), layer(near)


def _swing(leg, amount, lift):
    """Swing a leg from the hip: rows shift sideways in proportion to their
    distance below the hip, and the foot lifts."""
    a = np.asarray(leg)
    out = np.zeros_like(a)
    h = a.shape[0]
    for y in range(HIP_Y, h):
        t = (y - HIP_Y) / (h - HIP_Y)
        dx = int(round(amount * t))
        ny = y - int(round(lift * t))
        row = np.roll(a[y], dx, axis=0)
        if dx > 0:
            row[:dx] = 0
        elif dx < 0:
            row[dx:] = 0
        m = row[:, 3] > 0
        out[ny][m] = row[m]
    # keep the thigh tops joined to the hip
    return Image.fromarray(out, 'RGBA')


def _talk(art):
    d = ImageDraw.Draw(art)
    x, y = MOUTH
    d.rectangle([x + 1, y, x + 5, y + 2], fill=(12, 8, 16, 255))
    d.rectangle([x + 2, y + 1, x + 4, y + 1], fill=(170, 40, 46, 255))
    return art


def _back(art):
    """Turn him round: hair over the face, a plain back to the jacket."""
    a = np.asarray(art).copy()
    h, w = a.shape[:2]
    op = a[..., 3] > 0
    hair = np.array([121, 44, 22])
    hair_dk = np.array([90, 30, 14])
    red = np.array([213, 34, 27])
    border = np.zeros_like(op)
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        border |= op & ~np.roll(np.roll(op, dy, 0), dx, 1)
    for y in range(18, 38):
        for x in range(0, w):
            if not op[y, x] or border[y, x]:
                continue
            a[y, x, :3] = hair_dk if (x % 6 == 0 and y > 22) else hair
    # frogging and buttons on the chest become plain jacket
    for y in range(40, 70):
        for x in range(14, 36):
            r, g, b = a[y, x, :3].astype(int)
            if op[y, x] and not border[y, x] and r > 200 and g > 120:
                a[y, x, :3] = red
    # a strip of neck under the hair
    a[37:39, 18:30][op[37:39, 18:30] & ~border[37:39, 18:30], :3] = (230, 160, 125)
    return Image.fromarray(a, 'RGBA')


def _neck(art, kind, view):
    """Beads and pendant, drawn the same way as the old sprite did."""
    import art_people
    P = {k: art_people._P(v) for k, v in art_people.GUEST.items()}
    d = ImageDraw.Draw(art)
    cx, y = COLLAR
    art_people._neckwear(d, P, cx, y, kind, 'back' if view == 'back' else 'front')
    return art


# ---------------------------------------------------------------- frames
def guest_frame(direction, phase=0.0, walking=False, talk=False, kind=None, blink=False):
    """Same signature as art_people.guest_frame. direction: front, side, back."""
    art = native()
    if direction == 'back':
        art = _back(art)
    torso, far, near = _split(art)
    bob = 0
    if walking:
        s = math.sin(phase * 2 * math.pi)
        bob = int(round(abs(s)))
        if direction == 'side':
            far = _swing(far, -4 * s, max(0, s) * 2)
            near = _swing(near, 4 * s, max(0, -s) * 2)
        else:
            far = _swing(far, 0, max(0, s) * 3)
            near = _swing(near, 0, max(0, -s) * 3)
    from art_common import outline
    legs = Image.new('RGBA', art.size, (0, 0, 0, 0))
    legs.alpha_composite(far)
    legs.alpha_composite(near)
    if walking:
        legs = outline(legs, color=(12, 8, 16, 255))   # close the steps the swing opens
    body = Image.new('RGBA', art.size, (0, 0, 0, 0))
    body.alpha_composite(legs)
    body.alpha_composite(torso)
    if talk and direction != 'back':
        body = _talk(body)
    if kind:
        body = _neck(body, kind, direction)
    frame = Image.new('RGBA', (FW, FH), (0, 0, 0, 0))
    frame.alpha_composite(body, (OX, OY - bob))
    return frame


def guest_seated():
    """For the Pope Seat: the upper body over a pair of short seated legs (48x80)."""
    art = native()
    upper = art.crop((0, 0, art.width, HIP_Y))
    # the bell hangs below the hip; sitting, it rests in his lap
    im = Image.new('RGBA', (FW, 80), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for x in (OX + 14, OX + 26):
        d.rectangle([x - 1, 70, x + 9, 79], fill=(12, 8, 16, 255))
        d.rectangle([x, 70, x + 8, 75], fill=(18, 3, 72, 255))
        d.rectangle([x, 76, x + 8, 78], fill=(115, 21, 13, 255))
    im.alpha_composite(upper, (OX, 80 - HIP_Y - 8))
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
    sheet.resize((sheet.width * 3, sheet.height * 3), Image.NEAREST).save('/tmp/claude-0/sprite/sheet.png')
