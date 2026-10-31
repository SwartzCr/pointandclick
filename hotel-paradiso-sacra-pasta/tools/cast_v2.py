"""The second set of character sheets (art_src/cast_v2/*.png, figures on magenta).

figures(name) cuts a sheet into rows of figures (RGBA, the magenta keyed out: only magenta
touching a figure's border, plus enclosed gaps of a decent size, is background; the
generator's little sparkle in the corner is dropped). shrink() brings a figure down to
game size with a hard-edged alpha.
"""
import os
import numpy as np
from PIL import Image
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
DIR = os.path.join(HERE, '..', 'art_src', 'cast_v2')
_cache = {}


def figures(name, min_size=6000):
    if name in _cache:
        return [[f.copy() for f in row] for row in _cache[name]]
    a = np.asarray(Image.open(os.path.join(DIR, name)).convert('RGB')).astype(int)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    mag = (r - g > 70) & (b - g > 70) & (r > 120) & (b > 120)
    H, W = mag.shape
    fg = ndimage.binary_opening(~mag, iterations=2)
    lab, n = ndimage.label(fg)
    objs = ndimage.find_objects(lab)
    sizes = ndimage.sum(fg, lab, range(1, n + 1))
    figs = []
    for i in range(n):
        if sizes[i] < min_size:
            continue
        sl = objs[i]
        cy, cx = (sl[0].start + sl[0].stop) / 2, (sl[1].start + sl[1].stop) / 2
        if cx > W * 0.94 and cy > H * 0.9:              # the sparkle
            continue
        y0, y1 = max(0, sl[0].start - 3), min(H, sl[0].stop + 3)
        x0, x1 = max(0, sl[1].start - 3), min(W, sl[1].stop + 3)
        crop = a[y0:y1, x0:x1]
        cm = mag[y0:y1, x0:x1]
        own = ndimage.binary_dilation(lab[y0:y1, x0:x1] == i + 1, iterations=3)
        l2, _ = ndimage.label(cm)
        edge = set(np.unique(np.concatenate([l2[0], l2[-1], l2[:, 0], l2[:, -1]]))) - {0}
        alpha = ~np.isin(l2, list(edge)) & own
        if l2.max():
            s2 = ndimage.sum(cm, l2, range(1, l2.max() + 1))
            alpha &= ~np.isin(l2, [k + 1 for k, sz in enumerate(s2) if sz >= 40])
        alpha &= ~cm | ~ndimage.binary_dilation(~own, iterations=1)
        alpha = ndimage.binary_erosion(alpha, iterations=1)
        # pinkish fringe on the edge: pull it towards the dark outline
        rgb = crop.copy()
        fringe = alpha & ~ndimage.binary_erosion(alpha, iterations=1) & (rgb[..., 0] - rgb[..., 1] > 60) & (rgb[..., 2] - rgb[..., 1] > 60)
        rgb[fringe] = (30, 20, 24)
        figs.append((y0, x0, y1, Image.fromarray(np.dstack([rgb, alpha * 255]).astype(np.uint8), 'RGBA')))
    figs.sort(key=lambda t: (t[0] + t[2]) / 2)
    rows, cur = [], []
    for f in figs:
        if cur and (f[0] + f[2]) / 2 - (cur[0][0] + cur[0][2]) / 2 > (cur[0][2] - cur[0][0]) * 0.6:
            rows.append(cur)
            cur = []
        cur.append(f)
    rows.append(cur)
    out = [[f[3] for f in sorted(row, key=lambda t: t[1])] for row in rows]
    _cache[name] = out
    return [[f.copy() for f in row] for row in out]


def shrink(im, k):
    """Scale a figure by k, premultiplied, with a hard-edged alpha."""
    w, h = max(1, round(im.width * k)), max(1, round(im.height * k))
    a = np.asarray(im).astype(float)
    al = a[..., 3:] / 255
    pre = Image.fromarray((a[..., :3] * al).astype(np.uint8)).resize((w, h), Image.LANCZOS)
    cov = Image.fromarray((al[..., 0] * 255).astype(np.uint8)).resize((w, h), Image.LANCZOS)
    pre, cov = np.asarray(pre).astype(float), np.asarray(cov).astype(float) / 255
    rgb = np.clip(pre / np.maximum(cov, 1e-3)[..., None], 0, 255).astype(np.uint8)
    return Image.fromarray(np.dstack([rgb, np.where(cov >= 0.5, 255, 0).astype(np.uint8)]), 'RGBA')


def tight(im):
    return im.crop(im.getbbox())


if __name__ == '__main__':
    for f in sorted(os.listdir(DIR)):
        rows = figures(f)
        print(f, [[(x.width, x.height) for x in r] for r in rows])


# ------------------------------------------------------------------ the bellhop
ART_H = 150                      # a standing bellhop, in game pixels
KH = 165                         # a standing Chuk


def _k(h_ref, target):
    return target / h_ref


def bellhop():
    """(stand, walk, poses, talk) at game scale, in the shapes guest_sheet expects.
    poses: reach, bend, push, pull, sit, sit with an arm raised."""
    sw = figures('bellhop_stand_walk_side.png')
    fb = figures('bellhop_walk_fb.png')
    act = figures('bellhop_actions.png')
    tk = figures('bellhop_talk.png')[0]
    k1 = _k(sw[0][0].height, ART_H)
    k2 = _k(fb[0][0].height, ART_H)
    k3 = _k(act[0][0].height, ART_H)
    k4 = _k(tk[0].height, ART_H)
    stand = {'front': shrink(sw[0][0], k1), 'back': shrink(sw[0][1], k1), 'side': shrink(sw[0][2], k1)}
    walk = {'side': [shrink(f, k1) for f in sw[1]],
            'front': [shrink(f, k2) for f in fb[0]],
            'back': [shrink(f, k2) for f in fb[1]]}
    poses = [shrink(f, k3) for f in act[0]]
    talk = {'front': shrink(tk[0], k4), 'side': shrink(tk[1], k4)}
    return stand, walk, poses, talk


def bellhop_extras():
    """The arcade and ending poses: stand at a cabinet (2), at a trackball (2), in a racing
    seat; fist pump, lying flat, toasting, the morning after."""
    rows = figures('bellhop_crypt.png')
    k = _k(rows[1][2].height, ART_H)
    return [shrink(f, k) for f in rows[0]], [shrink(f, k) for f in rows[1]]


def necklaces():
    """{(kind, view): (overlay, hat top, hat cx)} for kind 'beads' / 'uv', view front/back/side:
    the rosary is what the top row adds to the plain figure; the pendant is what the bottom
    row adds to the top row."""
    from guest_sheet import _hat
    neck = figures('bellhop_necklaces.png')
    sw = figures('bellhop_stand_walk_side.png')[0]
    out = {}
    kn = ART_H / neck[0][0].height
    for i, view in enumerate(('front', 'back', 'side')):
        top, bot = shrink(neck[0][i], kn), shrink(neck[1][i], kn)
        plain = shrink(sw[i], ART_H / sw[0].height)
        for kind, w, base in (('beads', top, plain), ('uv', bot, top)):
            b = base.resize(w.size, Image.LANCZOS) if base.size != w.size else base
            a = np.asarray(w).astype(int)
            bb = np.asarray(b).astype(int)
            r, g, bl = a[..., 0], a[..., 1], a[..., 2]
            diff = np.abs(a[..., :3] - bb[..., :3]).sum(-1)
            if kind == 'beads':
                col = (r > 150) & (g > 100) & (bl < 120) & (r - bl > 60)
                m = (diff > 60) & col
                # the medallion's darker inner ring too
                m = ndimage.binary_closing(m, iterations=1)
                minsz = 4
            else:
                mn, mx = np.minimum(np.minimum(r, g), bl), np.maximum(np.maximum(r, g), bl)
                col = ((mn > 150) & (mx - mn < 70)) | ((bl > 120) & (bl - g > 40))
                m = (diff > 50) & col
                minsz = 2
            m &= a[..., 3] > 0
            lab, n = ndimage.label(ndimage.binary_dilation(m, iterations=1))
            if n:
                sizes = ndimage.sum(m, lab, range(1, n + 1))
                m &= np.isin(lab, [j + 1 for j, sz in enumerate(sizes) if sz >= minsz])
            ov = Image.fromarray(np.dstack([a[..., :3], m * 255]).astype(np.uint8), 'RGBA')
            t, cx = _hat(w)
            out[(kind, view)] = (ov, t, cx)
    return out


# ------------------------------------------------------------------ Chuk
def _strip_cabinet(im):
    """Keep Chuk, drop the arcade cabinet he's standing at (brown wood, grey screen)."""
    a = np.asarray(im).copy()
    r, g, b = a[..., 0].astype(int), a[..., 1].astype(int), a[..., 2].astype(int)
    wood = (r > g + 12) & (g > b) & (g > 0.45 * r) & (r < 190) & ~((r > 180) & (g > 160))
    screen = (np.abs(r - g) < 14) & (np.abs(g - b) < 14) & (r < 110) & (r > 40)
    keep = (a[..., 3] > 0) & ~wood & ~screen
    lab, n = ndimage.label(keep)
    if n:
        keep = lab == 1 + int(np.argmax(ndimage.sum(keep, lab, range(1, n + 1))))
    keep = ndimage.binary_fill_holes(keep)
    a[..., 3] = np.where(keep, a[..., 3], 0)
    return tight(Image.fromarray(a, 'RGBA'))


def chuk():
    """Chuk's frames at game scale, as khuc_sprite.views() returns them (unframed)."""
    sh = figures('chuk_sheet.png')
    fb = figures('chuk_walk_fb.png')
    act = figures('chuk_actions.png')
    tk = figures('chuk_talk.png')[0]
    kt = _k(sh[0][0].height, KH)
    kb = _k(sh[1][0].height, KH)
    ka = _k(act[1][4].height, KH)
    return dict(
        front=shrink(sh[0][0], kt), back=shrink(sh[0][1], kt), side=shrink(sh[0][2], kt),
        walk=[shrink(f, kb) for f in sh[1][0:4]],
        walk_front=[shrink(f, _k(fb[0][0].height, KH)) for f in fb[0]],
        walk_back=[shrink(f, _k(fb[1][0].height, KH)) for f in fb[1]],
        raise_=shrink(sh[1][4], kb),
        play=[shrink(sh[0][1], kt)],                      # from behind, at the T. Rex skull
        crank=[shrink(f, ka) for f in act[0][2:4]],
        talk_front=shrink(tk[0], _k(tk[0].height, KH)), talk_side=shrink(tk[1], _k(tk[1].height, KH)),
        extras=dict(button=shrink(act[0][4], ka), plug=shrink(act[1][0], ka), carry=shrink(act[1][1], ka),
                    horror=shrink(act[1][2], ka), cheer=shrink(act[1][3], ka), cup=shrink(act[1][4], ka),
                    lying=shrink(act[1][5], ka), seat=[shrink(f, ka) for f in act[0][0:2]]),
    )


def talk_frame(stand, talk, head=0.25):
    """The standing figure with the talking figure's head on it (sized to match), so only the
    face changes when a character speaks."""
    def hat(im):
        a = np.asarray(im)[..., 3] > 0
        ys = np.nonzero(a.any(1))[0]
        t, h = ys[0], ys[-1] - ys[0]
        xs = np.nonzero(a[t + max(1, int(h * 0.04))])[0]
        return t, xs[0], xs[-1], h
    st, sx0, sx1, sh = hat(stand)
    tt, tx0, tx1, th = hat(talk)
    hd = talk.crop((0, tt, talk.width, tt + int(th * head)))
    k = (sx1 - sx0 + 1) / (tx1 - tx0 + 1)
    hd = shrink(hd, k)
    out = stand.copy()
    cx_s, cx_t = (sx0 + sx1) / 2, (tx0 + tx1) / 2 * k
    out.alpha_composite(hd, (int(round(cx_s - cx_t)), st))
    return out


# ------------------------------------------------------------------ the clowns
CLOWN_H = 140                    # a standing clown, in game pixels (the Crypt shows them at 100%)
# (suit hue, dot hue, hair hue) in degrees; clown 1 keeps the sheet's yellow, blue and orange
CLOWN_COLOURS = {1: None, 2: (125, 52, 285), 3: (218, 325, 52)}


def recolour(im, cols):
    """Swap the suit, polka dots and hair to new hues, keeping each pixel's shading."""
    if cols is None:
        return im
    import colorsys
    a = np.asarray(im).astype(float) / 255
    rgb = a[..., :3]
    mx, mn = rgb.max(-1), rgb.min(-1)
    hsv = np.asarray(Image.fromarray((rgb * 255).astype(np.uint8)).convert('HSV')).astype(float)
    h = hsv[..., 0] * 360 / 255
    sat = (mx - mn) / np.maximum(mx, 1e-3)
    vivid = (sat > 0.35) & (a[..., 3] > 0) & (mx > 0.25)
    # by hue: the orange hair (about 10-27 degrees) sits between the red shoes and nose
    # (below 10) and the yellow suit with its shadows (27-75)
    hair = vivid & (h >= 10) & (h < 27)
    suit = vivid & (h >= 27) & (h < 75)
    dots = vivid & (h >= 190) & (h < 260)
    out = hsv.copy()
    for m, hue in ((suit, cols[0]), (dots, cols[1]), (hair, cols[2])):
        out[..., 0] = np.where(m, hue * 255 / 360, out[..., 0])
    # a vivid green or blue reads as neon: tone the suit down a little
    out[..., 1] = np.where(suit, out[..., 1] * 0.8, out[..., 1])
    out[..., 2] = np.where(suit, out[..., 2] * 0.88, out[..., 2])
    res = np.asarray(Image.fromarray(out.astype(np.uint8), 'HSV').convert('RGB'))
    res = np.where((suit | dots | hair)[..., None], res, (rgb * 255).astype(np.uint8))
    return Image.fromarray(np.dstack([res, (a[..., 3] * 255).astype(np.uint8)]).astype(np.uint8), 'RGBA')


def clown(n):
    """Clown n's frames at game scale: stand (front back right left), walk side (6),
    walk front (4), walk back (4), and actions (tray, arms up, arms up walking, shout, horn)."""
    wk = figures('clown_walk.png', min_size=3000)
    ac = figures('clown_actions.png', min_size=3000)
    cols = CLOWN_COLOURS[n]
    k1 = CLOWN_H / wk[0][0].height
    k2 = CLOWN_H / wk[1][0].height * (wk[1][0].height / wk[0][0].height)
    S = lambda f, k: shrink(recolour(f, cols), k)
    kw2 = CLOWN_H * 0.95 / wk[1][0].height
    kfb = CLOWN_H * 0.92 / wk[2][0].height
    ka = CLOWN_H * 1.15 / ac[0][1].height
    return dict(stand=[S(f, k1) for f in wk[0]], walk_side=[S(f, kw2) for f in wk[1]],
                walk_front=[S(f, kfb) for f in wk[2][:4]], walk_back=[S(f, kfb) for f in wk[2][4:]],
                actions=[S(f, ka) for f in ac[0]])
