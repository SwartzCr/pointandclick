"""The guest (the bellhop) from his generated sprite sheets, all on magenta:

  bellhop_walk_side.jpg  top: stand front, back, right, left; bottom: 6-frame walk right
  bellhop_walk_fb.jpg    top: 4-frame walk towards us; bottom: 4-frame walk away
  bellhop_actions.jpg    top: reach, bend, push, sit, sit with an arm raised; bottom: heads
  bellhop_extras.jpg     top: wearing the beads (front, back, right, left);
                         middle: wearing the pendant (torsos); bottom: the two necklaces

Each row is scaled so a standing bellhop is ART_H px tall. The beads and the
pendant are lifted off the 'wearing' figures by colour and laid over every
frame of the matching view, lined up on the hat.
"""
import os
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

from guest_sprite import ART_H, _talk as _talk_old   # noqa: F401  (kept for reference)

HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.join(HERE, '..', 'art_src')
STAND_H = {'bellhop_walk_side.jpg': 336, 'bellhop_walk_fb.jpg': 330,
           'bellhop_actions.jpg': 340, 'bellhop_extras.jpg': 304}
FW = 104                          # frame width (wide enough for a full stride)
FH = ART_H + 4

_cache = {}


def _sheet(name):
    if name not in _cache:
        a = np.asarray(Image.open(os.path.join(ART, name)).convert('RGB')).astype(int)
        r, g, b = a[..., 0], a[..., 1], a[..., 2]
        mag = (r - g > 60) & (b - g > 60) & (r > 110) & (b > 110)
        fg = ndimage.binary_opening(~mag, iterations=1)
        lab, n = ndimage.label(fg)
        objs = ndimage.find_objects(lab)
        sizes = ndimage.sum(fg, lab, range(1, n + 1))
        figs = []
        for i in range(n):
            if sizes[i] < 400:
                continue
            sl = objs[i]
            y0, y1 = max(0, sl[0].start - 4), sl[0].stop + 4
            x0, x1 = max(0, sl[1].start - 4), sl[1].stop + 4
            crop = a[y0:y1, x0:x1]
            cm = mag[y0:y1, x0:x1]
            # only magenta connected to the crop's border is background
            l2, _ = ndimage.label(cm)
            edge = set(np.unique(np.concatenate([l2[0], l2[-1], l2[:, 0], l2[:, -1]]))) - {0}
            alpha = ~np.isin(l2, list(edge))
            # enclosed gaps (between an arm and the body) are background too
            sizes2 = ndimage.sum(cm, l2, range(1, l2.max() + 1)) if l2.max() else []
            holes = [k + 1 for k, sz in enumerate(sizes2) if sz >= 15]
            alpha &= ~np.isin(l2, holes)
            alpha = ndimage.binary_erosion(alpha, iterations=1)
            rgba = np.dstack([crop, alpha * 255]).astype(np.uint8)
            figs.append((y0, x0, Image.fromarray(rgba, 'RGBA')))
        # group into rows by top edge
        figs.sort(key=lambda t: t[0])
        rows, cur = [], []
        for f in figs:
            if cur and f[0] - cur[0][0] > 120:
                rows.append(cur)
                cur = []
            cur.append(f)
        rows.append(cur)
        _cache[name] = [[f[2] for f in sorted(r, key=lambda t: t[1])] for r in rows]
    return _cache[name]


def _scale(im, sheet):
    k = ART_H / STAND_H[sheet]
    w, h = max(1, round(im.width * k)), max(1, round(im.height * k))
    a = np.asarray(im).astype(float)
    al = a[..., 3:] / 255
    pre = Image.fromarray((a[..., :3] * al).astype(np.uint8)).resize((w, h), Image.LANCZOS)
    cov = Image.fromarray((al[..., 0] * 255).astype(np.uint8)).resize((w, h), Image.LANCZOS)
    pre, cov = np.asarray(pre).astype(float), np.asarray(cov).astype(float) / 255
    rgb = np.clip(pre / np.maximum(cov, 1e-3)[..., None], 0, 255).astype(np.uint8)
    out = Image.fromarray(rgb).quantize(40, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).convert('RGBA')
    out.putalpha(Image.fromarray(np.where(cov >= 0.5, 255, 0).astype(np.uint8)))
    return out


def _hat(im):
    """(top y, centre x) of the hat: the top of the figure."""
    a = np.asarray(im)[..., 3] > 0
    ys = np.nonzero(a.any(1))[0]
    top = ys[0]
    band = a[top:top + max(3, im.height // 20)]
    xs = np.nonzero(band.any(0))[0]
    return top, (xs[0] + xs[-1]) / 2


GOLD, GOLD_DK, GOLD_HI = (232, 178, 52, 255), (150, 98, 24, 255), (255, 230, 130, 255)
SILVER, VIOLET, VIOLET_HI = (225, 222, 235, 255), (150, 70, 230, 255), (230, 200, 255, 255)


STAND_H['bellhop_necklaces.jpg'] = 336
_necks = None


def necklace_overlays():
    import cast_v2
    global _necks
    if _necks is None:
        _necks = cast_v2.necklaces()
    return _necks


def necklace_overlays_v1():
    """{(kind, view): (overlay at game scale, hat top, hat cx)}: the necklaces lifted
    off the 'wearing' figures by comparing them with the matching plain figure."""
    global _necks
    if _necks is None:
        _necks = {}
        neck = _sheet('bellhop_necklaces.jpg')
        plain = _sheet('bellhop_walk_side.jpg')[0]
        for row, kind in ((0, 'beads'), (1, 'uv')):
            for i, view in enumerate(('front', 'back', 'side')):
                w, p = neck[row][i], plain[i]
                a = np.asarray(w.resize(p.size, Image.LANCZOS)).astype(int)
                b = np.asarray(p).astype(int)
                r, g, bb = a[..., 0], a[..., 1], a[..., 2]
                diff = np.abs(a[..., :3] - b[..., :3]).sum(-1)
                if kind == 'beads':
                    col = (r > 140) & (g > 95) & (bb < 120) & (r - bb > 60)
                    m = (diff > 90) & col
                    minsz = 40
                else:
                    mn = np.minimum(np.minimum(r, g), bb)
                    mx = np.maximum(np.maximum(r, g), bb)
                    col = ((mn > 140) & (mx - mn < 80)) | ((bb > 140) & (bb - g > 40))
                    m = (diff > 50) & col
                    minsz = 6
                m &= a[..., 3] > 0
                lab, n = ndimage.label(ndimage.binary_dilation(m, iterations=2))
                if n:
                    sizes = ndimage.sum(m, lab, range(1, n + 1))
                    m &= np.isin(lab, [k + 1 for k, sz in enumerate(sizes) if sz >= minsz])
                k = ART_H / STAND_H['bellhop_walk_side.jpg']
                W2, H2 = max(1, round(p.width * k)), max(1, round(p.height * k))
                rgb = np.where(m[..., None], a[..., :3], 0).astype(np.uint8)
                cov = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).resize((W2, H2), Image.BOX)).astype(float) / 255
                pre = np.asarray(Image.fromarray(rgb).resize((W2, H2), Image.BOX)).astype(float)
                colr = np.clip(pre / np.maximum(cov, 1e-3)[..., None], 0, 255).astype(np.uint8)
                ov = Image.fromarray(np.dstack([colr, np.where(cov > (0.25 if kind == 'beads' else 0.12), 255, 0).astype(np.uint8)]), 'RGBA')
                ref = _scale(p, 'bellhop_walk_side.jpg')
                top, cx = _hat(ref)
                _necks[(kind, view)] = (ov, top, cx)
    return _necks


def _wear_drawn(fig, view, kind):
    """Draw the beads (a gold macaroni chain with a medallion) and the UV pendant
    (a silver chain with a violet crystal) at the neck, in the style of the
    generated necklaces."""
    if not kind:
        return fig
    fig = fig.copy()
    d = ImageDraw.Draw(fig)
    top, cx = _hat(fig)
    H = ART_H
    neck = top + 0.255 * H
    a = np.asarray(fig)[..., 3] > 0
    row = int(neck + 0.08 * H)
    xs = np.nonzero(a[row])[0]
    front_x = xs[-1] if len(xs) else cx
    if view == 'front':
        if kind.get('uv'):
            w, dep = 0.06 * H, 0.15 * H
            pts = [(cx - w + 2 * w * t, neck + 2 + dep * (1 - (2 * t - 1) ** 2)) for t in np.linspace(0, 1, 13)]
            d.line(pts, fill=SILVER, width=1)
            gx, gy = cx, neck + 2 + dep + 2
            d.polygon([(gx, gy - 3), (gx + 3, gy), (gx, gy + 4), (gx - 3, gy)], fill=VIOLET)
            d.point((gx - 1, gy - 1), fill=VIOLET_HI)
        if kind.get('beads'):
            w, dep = 0.09 * H, 0.11 * H
            for t in np.linspace(0, 1, 11):
                x, y = cx - w + 2 * w * t, neck + dep * (1 - (2 * t - 1) ** 2)
                d.ellipse([x - 1.6, y - 1.3, x + 1.6, y + 1.3], fill=GOLD, outline=GOLD_DK)
            my = neck + dep + 4
            d.ellipse([cx - 4, my - 4, cx + 4, my + 4], fill=GOLD, outline=GOLD_DK)
            d.arc([cx - 2, my - 2, cx + 2, my + 2], 40, 320, fill=GOLD_DK)
            d.point((cx - 2, my - 2), fill=GOLD_HI)
    elif view == 'side':
        fx = front_x - 3
        if kind.get('uv'):
            d.line([(fx - 6, neck + 1), (fx - 1, neck + 0.12 * H)], fill=SILVER, width=1)
            gx, gy = fx, neck + 0.12 * H + 2
            d.polygon([(gx, gy - 3), (gx + 2, gy), (gx, gy + 3), (gx - 2, gy)], fill=VIOLET)
        if kind.get('beads'):
            for t in np.linspace(0, 1, 6):
                x, y = fx - 7 + 6 * t, neck + 0.09 * H * t
                d.ellipse([x - 1.5, y - 1.2, x + 1.5, y + 1.2], fill=GOLD, outline=GOLD_DK)
            my = neck + 0.09 * H + 3
            d.ellipse([fx - 3, my - 3, fx + 3, my + 3], fill=GOLD, outline=GOLD_DK)
    else:   # back: just the string across the nape
        if kind.get('beads'):
            for t in np.linspace(0, 1, 7):
                x, y = cx - 6 + 12 * t, neck - 1 + 1.5 * (1 - (2 * t - 1) ** 2)
                d.ellipse([x - 1.4, y - 1.1, x + 1.4, y + 1.1], fill=GOLD, outline=GOLD_DK)
        elif kind.get('uv'):
            d.arc([cx - 6, neck - 3, cx + 6, neck + 2], 20, 160, fill=SILVER)
    return fig


def _wear(fig, view, kind):
    """Lay the generated necklaces over a frame, lined up on the hat."""
    if not kind:
        return fig
    fig = fig.copy()
    top, cx = _hat(fig)
    for k in ('uv', 'beads'):
        if kind.get(k):
            ov, otop, ocx = necklace_overlays()[(k, view)]
            fig.alpha_composite(ov, (int(round(cx - ocx)), int(round(top - otop))))
    return fig


def _frame(fig):
    f = Image.new('RGBA', (FW, FH), (0, 0, 0, 0))
    if fig.width > FW:
        fig = fig.crop(((fig.width - FW) // 2, 0, (fig.width - FW) // 2 + FW, fig.height))
    f.alpha_composite(fig, ((FW - fig.width) // 2, FH - fig.height))
    return f


def _talk(fig, view):
    """Open the mouth: a small dark gap under the nose."""
    fig = fig.copy()
    a = np.asarray(fig)
    r, g, b = a[..., 0].astype(int), a[..., 1].astype(int), a[..., 2].astype(int)
    skin = (r > 170) & (g > 110) & (b > 80) & (r - b > 40) & (a[..., 3] > 0)
    top, cx = _hat(fig)
    head = skin[top:top + int(0.27 * ART_H)]
    ys, xs = np.nonzero(head)
    if not len(xs):
        return fig
    fy1 = ys.max() + top
    if view == 'front':
        mx = int(np.median(xs))
    else:
        mx = int(np.percentile(xs, 85)) - 2
    my = fy1 - 5
    d = ImageDraw.Draw(fig)
    d.rectangle([mx - 2, my, mx + 1, my + 2], fill=(70, 20, 24, 255))
    d.rectangle([mx - 1, my + 2, mx, my + 2], fill=(170, 60, 60, 255))
    return fig


def frames():
    """All frames (the second set of sheets, art_src/cast_v2): stand, walk, poses.
    poses: reach, bend, push, pull, sit, sit with an arm raised."""
    import cast_v2
    stand, walk, poses, _ = cast_v2.bellhop()
    return stand, walk, poses


def frames_v1():
    """All frames, as {name: image} plus ordered lists for the views."""
    side = _sheet('bellhop_walk_side.jpg')
    fb = _sheet('bellhop_walk_fb.jpg')
    act = _sheet('bellhop_actions.jpg')
    S = lambda f, s: _scale(f, s)
    stand = {'front': S(side[0][0], 'bellhop_walk_side.jpg'), 'back': S(side[0][1], 'bellhop_walk_side.jpg'),
             'side': S(side[0][2], 'bellhop_walk_side.jpg')}
    walk = {'side': [S(f, 'bellhop_walk_side.jpg') for f in side[1]],
            'front': [S(f, 'bellhop_walk_fb.jpg') for f in fb[0]],
            'back': [S(f, 'bellhop_walk_fb.jpg') for f in fb[1]]}
    poses = [S(f, 'bellhop_actions.jpg') for f in act[0]]       # reach, bend, push, sit, sit + arm up
    return stand, walk, poses


def guest_views(spr):
    """The AGS views for the guest in every outfit; spr(name, image) registers a sprite."""
    import cast_v2
    stand, walk, poses, talk = cast_v2.bellhop()
    outfits = {'': {}, 'B': {'beads': True}, 'U': {'uv': True}, 'BU': {'beads': True, 'uv': True}}
    views = []
    for tag, kind in outfits.items():
        sfx = ('_' + tag) if tag else ''
        w = {}
        for dr in ('front', 'side', 'back'):
            w[dr] = [spr('guest%s_%s_stand' % (sfx, dr), _frame(_wear(stand[dr], dr, kind)))]
            w[dr] += [spr('guest%s_%s_walk%d' % (sfx, dr, i), _frame(_wear(f, dr, kind))) for i, f in enumerate(walk[dr])]
        loops = [[(f, 0, False) for f in w['front']], [(f, 0, True) for f in w['side']],
                 [(f, 0, False) for f in w['side']], [(f, 0, False) for f in w['back']]]
        views.append(dict(name='VGUEST' + tag, loops=loops))
        tf = [w['front'][0], spr('guest%s_front_talk1' % sfx, _frame(_wear(cast_v2.talk_frame(stand['front'], talk['front']), 'front', kind)))]
        ts = [w['side'][0], spr('guest%s_side_talk1' % sfx, _frame(_wear(cast_v2.talk_frame(stand['side'], talk['side']), 'side', kind)))]
        tl = [[(f, 0, False) for f in tf], [(f, 0, True) for f in ts], [(f, 0, False) for f in ts],
              [(w['back'][0], 0, False)]]
        views.append(dict(name='VGTALK' + tag, loops=tl))
    # gestures: reach, bend, push (side view; loop 1 is the mirror for facing left)
    g = [spr('guest_gesture%d' % k, _frame(p)) for k, p in enumerate(poses[:3])]
    views.append(dict(name='VGESTURE', loops=[[(f, 0, False) for f in g], [(f, 0, True) for f in g],
                                               [(f, 0, False) for f in g], [(f, 0, False) for f in g]]))
    return views


def seated(decree=False):
    """The guest sitting (for the Pope Seat), at the Crypt's scale."""
    poses = frames()[2]
    p = poses[5 if decree else 4]
    k = 0.62
    p = p.resize((round(p.width * k), round(p.height * k)), Image.LANCZOS)
    p.putalpha(p.getchannel('A').point(lambda v: 255 if v >= 128 else 0))
    return p


def icons():
    """Inventory icons (48x40) for the beads and the pendant, from the bottom row of the extras sheet."""
    a = np.asarray(Image.open(os.path.join(ART, 'bellhop_extras.jpg')).convert('RGB')).astype(int)
    out = {}
    for script, box in (('iBeads', (490, 575, 650, 755)), ('iPendant', (750, 580, 870, 750))):
        x0, y0, x1, y1 = box
        c = a[y0:y1, x0:x1]
        r, g, b = c[..., 0], c[..., 1], c[..., 2]
        mn = np.minimum(np.minimum(r, g), b)
        crystal = (b > 180) & (g < 160) & (b - r > 15)
        if script == 'iPendant':
            fgm = (mn > 150) | crystal
        else:
            fgm = ((r - b > 40) & (g > 60)) | ((r + g + b) < 240)
        lab, n = ndimage.label(fgm)
        if n:
            sizes = ndimage.sum(fgm, lab, range(1, n + 1))
            fgm = np.isin(lab, [i + 1 for i, sz in enumerate(sizes) if sz >= 20])
        c = c.copy()
        ys, xs = np.nonzero(fgm)
        c, fgm = c[ys.min():ys.max() + 1, xs.min():xs.max() + 1], fgm[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
        s = min(44 / c.shape[1], 36 / c.shape[0])
        w, h = max(1, round(c.shape[1] * s)), max(1, round(c.shape[0] * s))
        rgb = np.where(fgm[..., None], c, 0).astype(np.uint8)
        cov = np.asarray(Image.fromarray((fgm * 255).astype(np.uint8)).resize((w, h), Image.BOX)).astype(float) / 255
        pre = np.asarray(Image.fromarray(rgb).resize((w, h), Image.BOX)).astype(float)
        col = np.clip(pre / np.maximum(cov, 1e-3)[..., None], 0, 255).astype(np.uint8)
        im = Image.fromarray(np.dstack([col, np.where(cov > 0.2, 255, 0).astype(np.uint8)]), 'RGBA')
        icon = Image.new('RGBA', (48, 40), (0, 0, 0, 0))
        if script == 'iPendant':
            # the generated chain is too fine to survive shrinking: redraw it, keep the crystal
            d = ImageDraw.Draw(icon)
            pts = [(24 + 11 * np.sin(t) * (0.55 + 0.45 * np.cos(t / 2) ** 2), 18 - 15 * np.cos(t) ** 1 * 1.0)
                   for t in np.linspace(-np.pi, np.pi, 40)]
            d.line(pts, fill=(205, 205, 220, 255), width=1)
            d.line([(p[0] + 0.5, p[1]) for p in pts[::3]], fill=(250, 250, 255, 255), width=1)
            a2 = np.asarray(im)
            cm = (a2[..., 3] > 0) & (a2[..., 2] > 170) & (a2[..., 1] < 170)
            lab2, n2 = ndimage.label(cm)
            if n2:
                cm = lab2 == (np.argmax(ndimage.sum(cm, lab2, range(1, n2 + 1))) + 1)
                cm = ndimage.binary_dilation(cm, iterations=1) & (a2[..., 3] > 0)
            ys2, xs2 = np.nonzero(cm)
            if len(xs2):
                gm = Image.fromarray((cm * 255).astype(np.uint8))
                gem = im.copy()
                gem.putalpha(gm)
                gem = gem.crop((xs2.min(), ys2.min(), xs2.max() + 1, ys2.max() + 1))
                gem = gem.resize((round(gem.width * 1.5), round(gem.height * 1.5)), Image.NEAREST)
                icon.alpha_composite(gem, (24 - gem.width // 2, 39 - gem.height))
        else:
            icon.alpha_composite(im, ((48 - im.width) // 2, (40 - im.height) // 2))
        out[script] = icon
    return out


if __name__ == '__main__':
    stand, walk, poses = frames()
    outfits = [{}, {'beads': True}, {'uv': True}, {'beads': True, 'uv': True}]
    rows = []
    for kind in outfits:
        row = [_frame(_wear(stand[d], d, kind)) for d in ('front', 'back', 'side')]
        rows.append(row)
    rows.append([_frame(f) for f in walk['side']])
    rows.append([_frame(f) for f in walk['front'] + walk['back']])
    rows.append([_frame(p) for p in poses] + [_frame(_talk(stand['front'], 'front')), _frame(_talk(stand['side'], 'side'))])
    W = max(len(r) for r in rows) * FW
    sheet = Image.new('RGBA', (W, FH * len(rows)), (90, 80, 100, 255))
    for j, r in enumerate(rows):
        for i, f in enumerate(r):
            sheet.alpha_composite(f, (i * FW, j * FH))
    ic = icons()
    sheet.alpha_composite(ic['iBeads'], (W - 110, 10))
    sheet.alpha_composite(ic['iPendant'], (W - 55, 10))
    sheet.resize((sheet.width * 2, sheet.height * 2), Image.NEAREST).save('/tmp/claude-0/bh/guest_sheet.png')
