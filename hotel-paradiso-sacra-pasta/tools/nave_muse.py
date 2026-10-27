"""The Nave, composed from separately generated art (art_src/nave-vga/).

The room picture (nave-room-640x288.png) holds everything fixed, with the
puzzle pieces in their starting state. The other states are separate images
on magenta; they're keyed, scaled (or warped into the room's perspective) to
their places, and reduced to the room's own VGA palette so they match.
Object and hotspot names and their order are the same as in the other Nave
builders, so the game script works with any of them.
"""
import math
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance

from art_common import canvas, outline, rgba, text, CLEAR
from art_rooms import Scene, glow_text, W, H, VIEW_H, WORDS, ANSWER, TILES, TILE_NAMES, BUTTONS, BUTTON_UV
from nave_painted import GLYPHS, uv_of, glow_layer

HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.join(HERE, '..', 'art_src', 'nave-vga')
INK = (46, 30, 24)


def A(name):
    return os.path.join(ART, name)


# ----------------------------------------------------------------- image helpers
_pal = None


def palette_image():
    """The room's own palette, for reducing the pieces to the same colours."""
    global _pal
    if _pal is None:
        room = Image.open(A('nave-room-640x288.png'))
        if room.mode != 'P':
            room = room.convert('RGB').quantize(256)
        _pal = Image.new('P', (1, 1))
        _pal.putpalette(room.getpalette())
    return _pal


def to_palette(im):
    """Snap an RGBA sprite's colours onto the room palette (no dither, hard alpha)."""
    a = im.getchannel('A').point(lambda v: 255 if v >= 128 else 0)
    rgb = im.convert('RGB').quantize(palette=palette_image(), dither=Image.Dither.NONE).convert('RGB')
    out = rgb.convert('RGBA')
    out.putalpha(a)
    return out


def keyed(name):
    """Load a piece and cut out its magenta background (and magenta fringes)."""
    im = np.asarray(Image.open(A(name)).convert('RGBA')).astype(int)
    r, g, b = im[..., 0], im[..., 1], im[..., 2]
    magenta = (r > 150) & (b > 150) & (g < 110) & (np.abs(r - b) < 90)
    # only the magenta that's connected to the border is background; violet or
    # pink inside the object (the pendant's crystal) stays
    from scipy import ndimage
    lab, n = ndimage.label(magenta)
    edge = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    bg = np.isin(lab, list(edge))
    im[bg, 3] = 0
    out = Image.fromarray(im.astype(np.uint8), 'RGBA')
    # pull back one pixel where magenta bled into the edge
    alpha = out.getchannel('A').filter(ImageFilter.MinFilter(3))
    out.putalpha(alpha)
    return out.crop(out.getbbox())


def fit(im, w, h):
    """Scale to w x h (smooth downscale, then hard alpha)."""
    return im.resize((max(1, int(w)), max(1, int(h))), Image.LANCZOS)


def _coeffs(dst, src):
    """Perspective coefficients mapping output points dst to input points src."""
    m = []
    for (x, y), (u, v) in zip(dst, src):
        m.append([x, y, 1, 0, 0, 0, -u * x, -u * y])
        m.append([0, 0, 0, x, y, 1, -v * x, -v * y])
    A_ = np.array(m, dtype=float)
    B = np.array([c for p in src for c in p], dtype=float)
    return np.linalg.solve(A_, B).tolist()


def warp(im, quad):
    """Warp the whole of im onto quad (tl, tr, br, bl) given in room pixels.
    Returns (sprite, left, top)."""
    xs = [p[0] for p in quad]
    ys = [p[1] for p in quad]
    x0, y0 = int(math.floor(min(xs))), int(math.floor(min(ys)))
    x1, y1 = int(math.ceil(max(xs))), int(math.ceil(max(ys)))
    w, h = x1 - x0, y1 - y0
    # supersample, then shrink, so detail averages instead of aliasing
    S = 4
    dst = [((x - x0) * S, (y - y0) * S) for x, y in quad]
    src = [(0, 0), (im.width, 0), (im.width, im.height), (0, im.height)]
    big = im.transform((w * S, h * S), Image.PERSPECTIVE, _coeffs(dst, src), Image.BICUBIC)
    return big.resize((w, h), Image.LANCZOS), x0, y0


def tiny(im, cx, cy, s, colour, spacing=1):
    widths = [len(GLYPHS[c][0]) for c in s]
    w = sum(widths) + spacing * (len(s) - 1)
    x = int(round(cx - w / 2))
    y = int(round(cy - 2.5))
    px = im.load()
    for ch, cw in zip(s, widths):
        for r, row in enumerate(GLYPHS[ch]):
            for c, bit in enumerate(row):
                if bit == '1' and 0 <= x + c < im.width and 0 <= y + r < im.height:
                    px[x + c, y + r] = rgba(colour)
        x += cw + spacing


def tiny_width(s, spacing=1):
    return sum(len(GLYPHS[c][0]) for c in s) + spacing * (len(s) - 1)


# ----------------------------------------------------------------- layout (room pixels, 640x288)
HOLE = [(520, 101), (546, 103), (566, 100), (584, 101), (587, 117), (579, 128), (578, 150),
        (575, 168), (573, 190), (570, 206), (560, 211), (540, 210), (522, 206), (516, 186),
        (518, 160), (519, 125)]
WARDROBE = [(586, 60), (640, 48), (640, 288), (586, 281)]          # its front, as seen
DRAWER_SHUT = (460, 139, 500, 158)
TILE_BOXES = [(461, 103, 475, 123), (475, 103, 489, 123), (488, 102, 501, 122), (501, 103, 514, 121)]
BOX = (168, 233, 240, 264)
BTN_BOXES = [(185, 239, 199, 252), (199, 240, 214, 252), (213, 239, 229, 253)]
BARRELS = [(275, 241), (303, 241), (332, 241), (360, 241)]        # centres of the four faces
PAMPH_BOX = (152, 190, 182, 210)
FORK_QUAD = [(13, 116), (67, 112), (72, 174), (17, 183)]           # the painting's canvas
SOD = [(0, 204), (70, 198), (150, 186), (214, 176), (222, 188), (142, 288), (0, 288)]
SCALES = [(398, 246), (420, 233), (452, 226), (453, 196), (463, 196), (464, 226), (500, 230),
          (532, 242), (548, 288), (392, 288)]


def nave():
    sc = Scene('nave')
    room_img = Image.open(A('nave-room-640x288.png')).convert('RGBA')
    assert room_img.size == (W, VIEW_H), room_img.size
    room = Image.new('RGBA', (W, H), (0, 0, 0, 255))
    room.paste(room_img, (0, 0))
    orig = room.copy()
    sc.bg = room
    sc.d = ImageDraw.Draw(room)

    # ---------- hotspots (later ones are drawn over earlier ones)
    sc.hotspot('hWallpaper', 'wallpaper strips', (420, 205), [('rect', [100, 18, 520, 194])])
    sc.hotspot('hSauce', 'Weird Sauce', (225, 203), [('rect', [186, 48, 246, 172])])
    sc.hotspot('hGlutenous', 'painting "Glutenous Truth"', (400, 203), [('rect', [372, 50, 433, 113])])
    flat = [(255, 162), (255, 60), (268, 38), (290, 24), (310, 20), (332, 24), (352, 38), (365, 60), (365, 162)]
    sc.hotspot('hFlat', 'stained-glass flat', (350, 206), [('poly', flat)])
    sc.hotspot('hTimeline', 'timeline of ancient technology', (472, 207), [('rect', [457, 84, 518, 140])])
    sc.hotspot('hArch', 'archway', (500, 210), [('poly', HOLE)])
    sc.hotspot('hTopology', 'sacred topology display', (410, 203), [('rect', [367, 150, 453, 198])])
    sc.hotspot('hCrochet', 'crocheted pasta display', (400, 203), [('rect', [366, 113, 453, 141])])
    sc.hotspot('hFirstTaste', 'painting "First Taste"', (218, 202), [('rect', [8, 10, 70, 98])])
    sc.hotspot('hDoor', 'door', (218, 202), [('poly', [(88, 78), (152, 85), (152, 186), (88, 198)])])
    sc.hotspot('hHandset', 'telephone handset', (218, 202), [('rect', [157, 164, 203, 189])])
    sc.hotspot('hSodTable', 'sod table', (218, 202), [('poly', SOD)])
    sc.hd.rectangle([157, 164, 203, 189], fill=[h[0] for h in sc.hotspots].index('hHandset') + 1)
    sc.hotspot('hSculpture', 'spaghetti sculpture', (350, 206), [('rect', [284, 92, 340, 204])])
    sc.hotspot('hSpinner', 'paragraph spinner', (246, 214), [('rect', [250, 214, 395, 288])])
    sc.hotspot('hScales', 'scales of pasta', (398, 211), [('poly', SCALES)])

    # ---------- A1: the archway, closed by a stone slab fitted into the hole
    slab = keyed('A1-archway-panel.png')
    xs, ys = [p[0] for p in HOLE], [p[1] for p in HOLE]
    ax0, ay0, ax1, ay1 = min(xs) - 2, min(ys) - 3, max(xs) + 2, max(ys) + 2
    # stretch the slab past its round top so it fills the jagged hole
    slab = slab.crop((0, int(slab.height * 0.12), slab.width, slab.height))
    panel = fit(slab, ax1 - ax0, ay1 - ay0)
    m = Image.new('L', panel.size, 0)
    ImageDraw.Draw(m).polygon([(x - ax0, y - ay0) for x, y in HOLE], fill=255)
    m = m.filter(ImageFilter.MaxFilter(3))
    flat_panel = Image.new('RGBA', panel.size, CLEAR)
    flat_panel.paste(panel.convert('RGB'), (0, 0), m)
    d = ImageDraw.Draw(flat_panel)
    edge = [(x - ax0, y - ay0) for x, y in HOLE]
    d.line(edge + [edge[0]], fill=rgba((60, 50, 46)), width=1)
    panel = to_palette(flat_panel)
    panel_uv = uv_of(panel)
    lay = canvas(*panel.size)
    for k, wtxt in enumerate(('NOT', 'A', 'WALL')):
        text(ImageDraw.Draw(lay), (panel.width // 2, 40 + k * 15), wtxt, 10, (255, 120, 220), anchor='mm')
    glow_layer(lay, panel_uv, 2)
    panel_uv.putalpha(panel.getchannel('A'))
    sc.obj('oArchPanel', 'wall', {'closed': panel, 'uv': panel_uv}, ax0, ay1, baseline=1)

    # ---------- A2: the wardrobe; open = the open wardrobe warped onto its front
    wb = [p for p in WARDROBE]
    wx0 = min(p[0] for p in wb)
    wy0 = min(p[1] for p in wb)
    wy1 = max(p[1] for p in wb)
    ward = orig.crop((wx0, wy0, W, wy1))
    opened, ox, oy = warp(keyed('A2-wardrobe-open-room-consistent.png'), WARDROBE)
    ward_open = ward.copy()
    ward_open.alpha_composite(to_palette(opened), (ox - wx0, oy - wy0))
    sc.obj('oWardrobe', 'wardrobe', {'closed': ward, 'open': ward_open}, wx0, wy1, baseline=200)
    beads = to_palette(fit(keyed('A7-rosary-beads.png'), 12, 30))
    sc.obj('oBeads', 'pasta rosary beads', {'on': beads}, 606, 132, visible=False, baseline=201)

    # ---------- A3: pamphlets standing in their holder on the sod table
    pam = to_palette(fit(keyed('A3-pamphlets.png'), 19, 22))
    sc.obj('oPamphlet', 'Spaghetti Theory pamphlet', {'on': pam}, 158, 205, baseline=288)

    # ---------- A4: a paper label on each barrel's face, carrying the word
    def drum_sprite(i, word, uv=False, correct=False):
        cx, cy = BARRELS[i]
        sp = 1 if tiny_width(word) <= 23 else 0
        lw = max(tiny_width(word, sp) + 4, 15)
        im = canvas(lw, 9)
        dd = ImageDraw.Draw(im)
        dd.rectangle([0, 0, lw - 1, 8], fill=rgba((236, 222, 186)))
        dd.line([(0, 8), (lw - 1, 8)], fill=rgba((150, 120, 84)))
        dd.line([(0, 0), (lw - 1, 0)], fill=rgba((250, 242, 220)))
        if uv:
            im = uv_of(im)
            if correct:
                lay = canvas(*im.size)
                tiny(lay, lw / 2, 4.5, word, (200, 255, 140), sp)
                glow_layer(lay, im, 2.0, 0.5, crisp=True)
            else:
                tiny(im, lw / 2, 4.5, word, (120, 90, 160), sp)
        else:
            tiny(im, lw / 2, 4.5, word, INK, sp)
        return im

    for i in range(4):
        sprites = {}
        for j, wtxt in enumerate(WORDS[i]):
            sprites['w%d' % j] = drum_sprite(i, wtxt)
            sprites['u%d' % j] = drum_sprite(i, wtxt, uv=True, correct=(j == ANSWER[i]))
        # every word gets the same anchor: centred on the face
        lefts = {k: BARRELS[i][0] - v.width // 2 for k, v in sprites.items()}
        width = max(v.width for v in sprites.values())
        padded = {}
        for k, v in sprites.items():
            c = canvas(width, 9)
            c.alpha_composite(v, ((width - v.width) // 2, 0))
            padded[k] = c
        sc.obj('oDrum%d' % (i + 1), 'drum', padded, BARRELS[i][0] - width // 2, BARRELS[i][1] + 5, baseline=287,
               state={0: 'w0', 1: 'w0', 2: 'w1', 3: 'w2'}[i])
    sc.uv(lambda im, dd: glow_text(im, (322, 208), 'SPIN UNTIL IT GLOWS', 8, (180, 255, 120)))

    # ---------- A6: the puzzle box, its buttons and the golden rigatone
    bx0, by0, bx1, by1 = BOX
    box_closed = orig.crop(BOX)
    opened = keyed('A6-puzzle-box-open.png')
    ow = bx1 - bx0
    oh = 60
    open_spr = to_palette(fit(opened, ow, oh))
    canvas_h = max(oh, by1 - by0)
    box_open = canvas(ow, canvas_h)
    box_open.alpha_composite(open_spr, (0, canvas_h - oh))
    box_closed_c = canvas(ow, canvas_h)
    box_closed_c.alpha_composite(box_closed, (0, canvas_h - (by1 - by0)))
    sc.obj('oBox', 'puzzle box', {'closed': box_closed_c, 'open': box_open,
                                   'uvclosed': uv_of(box_closed_c), 'uvopen': uv_of(box_open)},
           bx0, by1, baseline=287)

    def button_sprite(i, pressed=False, uv=None):
        b = BTN_BOXES[i]
        im = orig.crop(b)
        if pressed:
            dark = ImageEnhance.Brightness(im).enhance(0.6)
            base = orig.crop(b)
            base.alpha_composite(dark, (0, 1))
            im = base
        if uv:
            im = uv_of(im)
            lay = canvas(*im.size)
            tiny(lay, im.width / 2, im.height / 2, uv, (255, 255, 120))
            glow_layer(lay, im, 2.0, 0.5, crisp=True)
        return im

    for i, kind in enumerate(BUTTONS):
        b = BTN_BOXES[i]
        sc.obj('oBtn%d' % (i + 1), '%s button' % kind,
               {'up': button_sprite(i), 'down': button_sprite(i, pressed=True), 'uv': button_sprite(i, uv=BUTTON_UV[i])},
               b[0], b[3], baseline=288)
    rig = to_palette(fit(keyed('A6-golden-rigatone.png'), 18, 11))
    sc.obj('oRigatone', 'golden rigatone', {'on': rig}, 198, 252, visible=False, baseline=288)

    # ---------- A5: Timeline tiles, the drawer and the pendant
    lit = keyed('A5-timeline-tiles-lit-room-consistent.png')
    quarter = lit.width / 4

    def tile_sprite(i, on):
        b = TILE_BOXES[i]
        base = orig.crop(b)
        if not on:
            return base
        t = lit.crop((int(i * quarter), 0, int((i + 1) * quarter), lit.height))
        t = to_palette(fit(t, b[2] - b[0], b[3] - b[1]))
        base.alpha_composite(t)
        return base

    for i, kind in enumerate(TILES):
        b = TILE_BOXES[i]
        sc.obj('oTile%d' % (i + 1), TILE_NAMES[kind], {'off': tile_sprite(i, False), 'on': tile_sprite(i, True)},
               b[0], b[3], baseline=1)
    dx0, dy0, dx1, dy1 = DRAWER_SHUT
    drawer, qx, qy = warp(keyed('A5-drawer-open.png'), [(dx0 - 2, dy0 + 2), (dx1 + 2, dy0 - 1), (dx1 + 4, dy1 + 9), (dx0 - 4, dy1 + 6)])
    drawer = to_palette(drawer)
    sc.obj('oDrawer', 'drawer', {'open': drawer}, qx, qy + drawer.height, visible=False, baseline=2)
    pend = to_palette(fit(keyed('A5-uv-pendant.png'), 20, 9))
    sc.obj('oPendant', 'UV pendant', {'on': pend}, 470, 156, visible=False, baseline=3)

    # ---------- A8: the Spinning Fork, four frames warped onto the painting's canvas
    frames = {}
    for k in range(4):
        f = Image.open(A('A8-spinning-fork-frame%d.png' % (k + 1))).convert('RGBA')
        inner = f.crop((int(f.width * 0.09), int(f.height * 0.16), int(f.width * 0.91), int(f.height * 0.84)))
        spr, fx, fy = warp(inner, FORK_QUAD)
        m = Image.new('L', spr.size, 0)
        ImageDraw.Draw(m).polygon([(x - fx, y - fy) for x, y in FORK_QUAD], fill=255)
        base = orig.crop((fx, fy, fx + spr.width, fy + spr.height))
        base.paste(to_palette(spr), (0, 0), m)
        frames['f%d' % (2 * k)] = base
        frames['f%d' % (2 * k + 1)] = base
    sc.obj('oFork', 'painting "Spinning Fork"', frames, fx, fy + spr.height, baseline=1, state='f0')
    sc.fork_frames = ['f%d' % k for k in range(8)]

    # ---------- writing that only ultraviolet light shows
    sc.uv(lambda im, dd: glow_text(im, (216, 180), 'SAUCE THY OFFERING', 8, (120, 255, 160)))
    sc.uv(lambda im, dd: glow_text(im, (310, 12), 'THE WORD IS SPUN', 9, (255, 240, 120)))
    sc.uv(lambda im, dd: glow_text(im, (84, 236), 'FIRST CAME THE STRING', 8, (120, 230, 255)))

    # ---------- walkable floor and walk-behinds
    wd = sc.wd
    wd.polygon([(214, 196), (366, 199), (452, 199), (505, 200), (512, 214), (402, 216), (396, 220),
                (252, 216), (250, 234), (186, 236), (200, 212)], fill=1)
    wd.polygon(SOD, fill=0)
    sc.walkbehind('poly', SOD, 287)
    sc.walkbehind('rect', [164, 232, 252, 288], 286)
    sc.walkbehind('rect', [250, 214, 396, 288], 286)
    sc.walkbehind('poly', SCALES, 286)
    return sc


def icons():
    """Inventory icons (48x40) from the same art."""
    out = {}
    for script, name in (('iBeads', 'A7-rosary-beads.png'), ('iPamphlet', 'A3-pamphlets.png'),
                         ('iPendant', 'A5-uv-pendant.png'), ('iRigatone', 'A6-golden-rigatone.png'),
                         ('iSauced', 'A6-golden-rigatone-sauced.png')):
        im = keyed(name)
        s = min(44 / im.width, 36 / im.height)
        im = fit(im, im.width * s, im.height * s)
        c = canvas(48, 40)
        c.alpha_composite(to_palette(im), ((48 - im.width) // 2, (40 - im.height) // 2))
        out[script] = c
    return out


if __name__ == '__main__':
    sc = nave()
    sc.bg.save('/tmp/claude-0/muse/bg_test.png')
