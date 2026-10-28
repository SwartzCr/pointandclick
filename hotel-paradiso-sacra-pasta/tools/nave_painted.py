"""The Nave, built on a painted background (art_src/nave_bg.png, 640x288).

Everything the player changes is an object cut from the painting itself, so it
sits in the picture exactly: the plaster panel in the archway, the wardrobe
door, the pamphlets, the four word barrels of the Paragraph Spinner, the
puzzle box and its three buttons, the Timeline tiles and the Spinning Fork.
Their other states (open, pressed, lit, ultraviolet) are painted over those
cut-outs. Hotspots, the walkable floor and the walk-behinds are traced from
the painting. Object and hotspot names and their order match the old,
code-drawn Nave, so the game script needs only new coordinates.
"""
import math
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance

from art_common import canvas, outline, rgba, shade, text, CLEAR
from art_rooms import (Scene, glow_text, W, H, VIEW_H, WORDS, ANSWER, TILES, TILE_NAMES,
                       BUTTONS, BUTTON_UV)

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, '..', 'art_src', 'nave_bg.png')
INK = (46, 30, 24)

# ----------------------------------------------------------------- a 3x5 font
# The barrels are only ~28 px across, so their words use a tiny pixel font.
GLYPHS = {
    'A': ['010', '101', '111', '101', '101'], 'B': ['110', '101', '110', '101', '110'],
    'C': ['011', '100', '100', '100', '011'], 'D': ['110', '101', '101', '101', '110'],
    'E': ['111', '100', '110', '100', '111'], 'F': ['111', '100', '110', '100', '100'],
    'G': ['011', '100', '101', '101', '011'], 'H': ['101', '101', '111', '101', '101'],
    'K': ['101', '101', '110', '101', '101'], 'L': ['100', '100', '100', '100', '111'],
    'M': ['10001', '11011', '10101', '10001', '10001'], 'N': ['101', '111', '111', '111', '101'],
    'O': ['010', '101', '101', '101', '010'], 'R': ['110', '101', '110', '101', '101'],
    'S': ['011', '100', '010', '001', '110'], 'T': ['111', '010', '010', '010', '010'],
    'W': ['10001', '10001', '10101', '11011', '10001'], 'Y': ['101', '101', '010', '010', '010'],
    'U': ['101', '101', '101', '101', '111'], 'I': ['111', '010', '010', '010', '111'],
    '1': ['010', '110', '010', '010', '111'], '2': ['110', '001', '010', '100', '111'],
    '3': ['110', '001', '010', '001', '110'],
    'P': ['110', '101', '110', '100', '100'],
}


def tiny_width(s):
    return sum(len(GLYPHS[c][0]) + 1 for c in s) - 1


def tiny_text(im, cx, cy, s, colour, scale=1):
    """Draw s centred on (cx, cy) in the 3x5 font."""
    w, h = tiny_width(s) * scale, 5 * scale
    x = int(round(cx - w / 2))
    y = int(round(cy - h / 2))
    px = im.load()
    for ch in s:
        g = GLYPHS[ch]
        for r, row in enumerate(g):
            for c, bit in enumerate(row):
                if bit == '1':
                    for dy in range(scale):
                        for dx in range(scale):
                            X, Y = x + c * scale + dx, y + r * scale + dy
                            if 0 <= X < im.width and 0 <= Y < im.height:
                                px[X, Y] = rgba(colour)
        x += (len(g[0]) + 1) * scale


# ----------------------------------------------------------------- helpers
def uv_of(im):
    """The same ultraviolet treatment as Scene.uv_frame, for one sprite."""
    a = np.asarray(im.convert('RGBA'), dtype=np.float32)
    lum = (a[..., 0] * 0.3 + a[..., 1] * 0.55 + a[..., 2] * 0.15) * 0.55
    out = np.stack([lum * 0.55, lum * 0.32, lum * 0.95, a[..., 3]], axis=-1)
    bright = np.clip(a[..., :3].min(axis=-1) - 200, 0, None) * 2.5
    out[..., 0] += bright * 0.5
    out[..., 1] += bright * 0.35
    out[..., 2] += bright
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), 'RGBA').copy()


def glow_layer(lay, im, blur=1.5, strength=1.0, crisp=False):
    halo = lay.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(blur))
    if strength != 1.0:
        halo.putalpha(halo.getchannel('A').point(lambda v: int(v * strength)))
    im.alpha_composite(halo)
    if crisp:                       # a dark edge so tiny letters stay readable
        edge = lay.filter(ImageFilter.MaxFilter(3))
        dark = Image.new('RGBA', im.size, (20, 10, 30, 255))
        im.paste(dark, (0, 0), edge.getchannel('A'))
    im.alpha_composite(lay)
    return im


def masked(im, poly, offset):
    """Cut im to a polygon given in room coordinates."""
    m = Image.new('L', im.size, 0)
    ImageDraw.Draw(m).polygon([(x - offset[0], y - offset[1]) for x, y in poly], fill=255)
    out = im.copy()
    out.putalpha(m)
    return out


def median_colour(im, box, dark_cut=110):
    a = np.asarray(im.crop(box).convert('RGB')).reshape(-1, 3).astype(int)
    keep = a[a.sum(1) > dark_cut]
    if not len(keep):
        keep = a
    return tuple(int(v) for v in np.median(keep, 0))


# ----------------------------------------------------------------- the room
ARCH_IN = [(539, 206), (539, 122), (541, 110), (546, 101), (553, 95), (559, 93),
           (566, 95), (572, 101), (576, 110), (578, 122), (578, 206)]
BARRELS = [(349, 377), (380, 408), (411, 439), (441, 469)]     # x ranges of the four word faces
TILE_BOXES = [(388, 98, 414, 122), (417, 98, 440, 122), (441, 98, 463, 122), (466, 98, 491, 122)]
BTN_BOXES = [(231, 241, 245, 254), (245, 241, 263, 254), (263, 241, 282, 254)]
BOX_BOX = (222, 232, 291, 270)
WARD_BOX = (589, 70, 640, 260)
FORK_BOX = (8, 126, 50, 182)
PAMPH_BOX = (163, 186, 186, 208)
SOD = [(0, 201), (64, 203), (130, 205), (196, 208), (208, 213), (199, 288), (0, 288)]


def nave():
    sc = Scene('nave')
    paint = Image.open(SRC).convert('RGBA')
    assert paint.size == (W, VIEW_H), paint.size
    room = Image.new('RGBA', (W, H), (0, 0, 0, 255))
    room.paste(paint, (0, 0))
    orig = room.copy()                      # the untouched painting, for cut-outs
    sc.bg = room
    sc.d = ImageDraw.Draw(room)
    d = sc.d

    # ---------- hotspots (later ones are drawn over earlier ones)
    sc.hotspot('hWallpaper', 'wallpaper strips', (420, 212), [('rect', [128, 36, 520, 196])])
    sc.hotspot('hSauce', 'Weird Sauce', (190, 205), [('rect', [142, 78, 206, 176])])
    sc.hotspot('hGlutenous', 'painting "Glutenous Truth"', (240, 210), [('rect', [210, 86, 270, 134])])
    flat = [(284, 176), (284, 80), (290, 62), (302, 47), (322, 39), (342, 47), (354, 62), (361, 80), (361, 176)]
    sc.hotspot('hFlat', 'stained-glass flat', (368, 210), [('poly', flat)])
    sc.hotspot('hTimeline', 'timeline of ancient technology', (440, 212), [('rect', [382, 76, 498, 139])])
    arch_out = [(522, 210), (522, 118), (527, 100), (538, 88), (556, 81), (574, 86), (586, 100), (591, 118), (591, 210)]
    sc.hotspot('hArch', 'archway', (548, 214), [('poly', arch_out)])
    sc.hotspot('hTopology', 'sacred topology display', (440, 212), [('rect', [384, 140, 503, 207])])
    sc.hotspot('hCrochet', 'crocheted pasta display', (240, 210), [('rect', [205, 136, 272, 158])])
    sc.hotspot('hFirstTaste', 'painting "First Taste"', (96, 199), [('rect', [4, 45, 51, 119])])
    sc.hotspot('hDoor', 'door', (96, 199), [('poly', [(66, 92), (126, 98), (126, 200), (66, 199)])])
    sc.hotspot('hHandset', 'telephone handset', (198, 206), [('rect', [126, 201, 162, 231])])
    sc.hotspot('hSodTable', 'sod table', (205, 207), [('poly', SOD)])
    sc.hd.rectangle([126, 201, 162, 231], fill=[h[0] for h in sc.hotspots].index('hHandset') + 1)
    sc.hotspot('hSculpture', 'spaghetti sculpture', (318, 234), [('rect', [292, 96, 352, 224])])
    sc.hotspot('hSpinner', 'paragraph spinner', (318, 250), [('rect', [332, 218, 490, 288])])
    sc.hotspot('hScales', 'scales of pasta', (500, 238),
               [('poly', [(520, 182), (640, 182), (640, 288), (505, 288), (505, 250), (520, 236)])])

    # ---------- the archway: a plaster panel (object) over a way down
    under = Image.new('RGBA', (W, H), (24, 14, 34, 255))
    glow = Image.new('RGBA', (W, H), CLEAR)
    gd = ImageDraw.Draw(glow)
    for k in range(70):                                     # purple light from below
        t = k / 69
        gd.line([(536, 206 - k), (580, 206 - k)], fill=(130, 70, 190, int(150 * (1 - t) ** 1.6)))
    under.alpha_composite(glow)
    ud = ImageDraw.Draw(under)
    for i in range(6):                                      # steps going down into the dark
        y = 206 - i * 9
        ud.line([(540, y), (577, y)], fill=rgba((150, 104, 190)))
        ud.line([(540, y + 1), (577, y + 1)], fill=rgba((50, 30, 66)))
    m = Image.new('L', (W, H), 0)
    ImageDraw.Draw(m).polygon(ARCH_IN, fill=255)
    room.paste(under, (0, 0), m)
    ax0, ay0 = 537, 91
    panel = masked(orig.crop((ax0, ay0, 580, 208)), ARCH_IN, (ax0, ay0))
    panel_uv = uv_of(panel)
    lay = canvas(*panel.size)
    for k, wtxt in enumerate(('NOT', 'A', 'WALL')):
        text(ImageDraw.Draw(lay), (panel.width // 2, 50 + k * 15), wtxt, 10, (255, 120, 220), anchor='mm')
    glow_layer(lay, panel_uv, 2)
    panel_uv.putalpha(panel.getchannel('A'))
    sc.obj('oArchPanel', 'wall', {'closed': panel, 'uv': panel_uv}, ax0, ay0 + panel.height, baseline=1)

    # ---------- the wardrobe (right edge): door shut, or open on a dark inside
    wx0, wy0, wx1, wy1 = WARD_BOX
    ward = orig.crop(WARD_BOX)
    ward_open = ward.copy()
    od = ImageDraw.Draw(ward_open)
    inner = [(603 - wx0, 92 - wy0), (640 - wx0, 88 - wy0), (640 - wx0, 252 - wy0), (603 - wx0, 250 - wy0)]
    od.polygon(inner, fill=rgba((30, 20, 16)))
    od.line([(605 - wx0, 104 - wy0), (640 - wx0, 101 - wy0)], fill=rgba((160, 160, 170)), width=2)   # rail
    for i, hx in enumerate((616, 628)):                                                            # robes
        col = [(110, 40, 120), (200, 170, 60)][i]
        od.polygon([(hx - wx0, 104 - wy0), (hx + 7 - wx0, 103 - wy0), (hx + 9 - wx0, 190 - wy0),
                    (hx - 3 - wx0, 192 - wy0)], fill=rgba(col))
    door_leaf = [(589 - wx0, 86 - wy0), (604 - wx0, 92 - wy0), (604 - wx0, 250 - wy0), (589 - wx0, 258 - wy0)]
    od.polygon(door_leaf, fill=rgba((96, 58, 34)))           # the door, swung towards us
    od.line([door_leaf[0], door_leaf[3]], fill=rgba((60, 36, 22)), width=2)
    od.ellipse([594 - wx0, 168 - wy0, 598 - wx0, 172 - wy0], fill=rgba((230, 200, 100)))
    sc.obj('oWardrobe', 'wardrobe', {'closed': ward, 'open': ward_open}, wx0, wy1, baseline=200)
    beads = canvas(16, 34)
    bd = ImageDraw.Draw(beads)
    bd.line([(8, 0), (8, 3)], fill=rgba((160, 160, 170)))
    for i in range(12):
        a = math.pi * 2 * i / 12
        bx, by = 8 + 6 * math.sin(a), 14 + 11 * (1 - math.cos(a)) / 2 + 3
        bd.ellipse([bx - 2, by - 2, bx + 2, by + 2], fill=rgba((250, 222, 150)))
        bd.point((bx, by + 1), fill=rgba((204, 160, 84)))
    bd.ellipse([4, 26, 12, 33], fill=rgba((250, 222, 150)))
    bd.arc([5, 27, 11, 32], 0, 360, fill=rgba((204, 160, 84)))
    sc.obj('oBeads', 'pasta rosary beads', {'on': outline(beads)}, 609, 140, visible=False, baseline=201)

    # ---------- pamphlets in their holder (the holder stays when they're taken)
    pamph = orig.crop(PAMPH_BOX)
    px0, py0, px1, py1 = PAMPH_BOX
    patch = orig.crop((px1 + 1, py0, px1 + 1 + (px1 - px0), py1))
    room.paste(patch, (px0, py0))
    sc.obj('oPamphlet', 'Spaghetti Theory pamphlet', {'on': pamph}, px0, py1, baseline=205)

    # ---------- the Paragraph Spinner: one object per barrel face
    def drum_sprite(i, word, uv=False, correct=False):
        x0, x1 = BARRELS[i]
        box = (x0, 233, x1 + 1, 257)
        im = orig.crop(box)
        face = median_colour(orig, (x0 + 5, 236, x1 - 5, 254))
        dd = ImageDraw.Draw(im)
        dd.ellipse([2, 3, im.width - 3, im.height - 4], fill=rgba(face))      # blank the old word
        dd.rectangle([1, 7, im.width - 2, im.height - 8], fill=rgba(face))
        cx, cy = im.width / 2, im.height / 2
        if uv:
            im = uv_of(im)
            if correct:
                lay = canvas(*im.size)
                tiny_text(lay, cx, cy, word, (200, 255, 140))
                glow_layer(lay, im, 2.0, 0.5, crisp=True)
            else:
                tiny_text(im, cx, cy, word, (120, 90, 160))
        else:
            tiny_text(im, cx, cy, word, INK)
        return im

    for i in range(4):
        sprites = {}
        for j, wtxt in enumerate(WORDS[i]):
            sprites['w%d' % j] = drum_sprite(i, wtxt)
            sprites['u%d' % j] = drum_sprite(i, wtxt, uv=True, correct=(j == ANSWER[i]))
        sc.obj('oDrum%d' % (i + 1), 'drum', sprites, BARRELS[i][0], 257, baseline=287,
               state={0: 'w0', 1: 'w0', 2: 'w1', 3: 'w2'}[i])
    sc.uv(lambda im, dd: glow_text(im, (409, 214), 'SPIN UNTIL IT GLOWS', 8, (180, 255, 120)))

    # ---------- the puzzle box (closed / open, ordinary / UV) and its buttons
    bx0, by0, bx1, by1 = BOX_BOX
    box_closed = orig.crop(BOX_BOX)
    box_open = box_closed.copy()
    bd = ImageDraw.Draw(box_open)
    bd.polygon([(229 - bx0, 255 - by0), (283 - bx0, 255 - by0), (280 - bx0, 243 - by0), (233 - bx0, 243 - by0)],
               fill=rgba((34, 20, 14)))                                        # the inside
    bd.polygon([(233 - bx0, 243 - by0), (280 - bx0, 243 - by0), (283 - bx0, 233 - by0), (230 - bx0, 233 - by0)],
               fill=rgba((150, 96, 52)))                                       # lid, tipped back
    bd.line([(230 - bx0, 233 - by0), (283 - bx0, 233 - by0)], fill=rgba((214, 160, 96)))
    bd.line([(233 - bx0, 243 - by0), (280 - bx0, 243 - by0)], fill=rgba((70, 44, 28)))
    sc.obj('oBox', 'puzzle box', {'closed': box_closed, 'open': box_open,
                                   'uvclosed': uv_of(box_closed), 'uvopen': uv_of(box_open)},
           bx0, by1, baseline=287)

    def button_sprite(i, pressed=False, uv=None):
        b = BTN_BOXES[i]
        im = orig.crop(b)
        if pressed:
            im = ImageEnhance.Brightness(im).enhance(0.62)
            moved = canvas(*im.size)
            moved.alpha_composite(im, (0, 1))
            base = orig.crop(b)
            base.alpha_composite(moved)
            im = base
        if uv:
            im = uv_of(im)
            lay = canvas(*im.size)
            tiny_text(lay, im.width / 2, im.height / 2, uv, (255, 255, 120))
            glow_layer(lay, im, 2.0, 0.5, crisp=True)
        return im

    for i, kind in enumerate(BUTTONS):
        b = BTN_BOXES[i]
        sc.obj('oBtn%d' % (i + 1), '%s button' % kind,
               {'up': button_sprite(i), 'down': button_sprite(i, pressed=True), 'uv': button_sprite(i, uv=BUTTON_UV[i])},
               b[0], b[3], baseline=288)
    rig = canvas(16, 9)
    rd = ImageDraw.Draw(rig)
    rd.rounded_rectangle([0, 1, 15, 8], 3, fill=rgba((250, 206, 70)))
    for x in range(2, 15, 3):
        rd.line([(x, 2), (x, 7)], fill=rgba((214, 160, 40)))
    rd.ellipse([12, 1, 15, 8], fill=rgba((150, 100, 30)))
    sc.obj('oRigatone', 'golden rigatone', {'on': outline(rig)}, 248, 254, visible=False, baseline=288)

    # ---------- the Timeline tiles (lit when pressed in order), drawer and pendant
    def tile_sprite(i, lit):
        im = orig.crop(TILE_BOXES[i])
        if lit:
            a = np.asarray(im, dtype=np.float32)
            a[..., 0] = np.clip(a[..., 0] * 1.18 + 40, 0, 255)
            a[..., 1] = np.clip(a[..., 1] * 1.12 + 26, 0, 255)
            a[..., 2] = np.clip(a[..., 2] * 0.7, 0, 255)
            im = Image.fromarray(a.astype(np.uint8), 'RGBA').copy()
            ImageDraw.Draw(im).rectangle([0, 0, im.width - 1, im.height - 1], outline=rgba((255, 230, 120)))
        return im

    for i, kind in enumerate(TILES):
        b = TILE_BOXES[i]
        sc.obj('oTile%d' % (i + 1), TILE_NAMES[kind], {'off': tile_sprite(i, False), 'on': tile_sprite(i, True)},
               b[0], b[3], baseline=1)
    drawer = canvas(34, 12)
    dd = ImageDraw.Draw(drawer)
    dd.polygon([(0, 0), (33, 0), (33, 11), (0, 11)], fill=rgba((92, 56, 32)))
    dd.rectangle([2, 0, 31, 5], fill=rgba((34, 20, 14)))
    dd.rectangle([14, 7, 20, 9], fill=rgba((220, 190, 90)))
    sc.obj('oDrawer', 'drawer', {'open': outline(drawer)}, 424, 150, visible=False, baseline=2)
    pend = canvas(12, 12)
    pdd = ImageDraw.Draw(pend)
    pdd.line([(1, 1), (6, 4), (11, 1)], fill=rgba((150, 130, 180)))
    pdd.polygon([(6, 3), (9, 6), (6, 11), (3, 6)], fill=rgba((190, 120, 255)))
    pdd.point((5, 5), fill=rgba((240, 220, 255)))
    sc.obj('oPendant', 'UV pendant', {'on': outline(pend)}, 435, 144, visible=False, baseline=3)

    # ---------- the Spinning Fork: the painting's middle turns
    fx0, fy0, fx1, fy1 = FORK_BOX
    fork = orig.crop(FORK_BOX)
    cx, cy, r = 29 - fx0, 153 - fy0, 12

    def fork_frame(k):
        im = fork.copy()
        disc = Image.new('L', im.size, 0)
        ImageDraw.Draw(disc).ellipse([cx - r, cy - r, cx + r, cy + r], fill=255)
        spun = fork.rotate(-45 * k, resample=Image.NEAREST, center=(cx, cy))
        im.paste(spun, (0, 0), disc)
        return im

    sc.obj('oFork', 'painting "Spinning Fork"', {('f%d' % k): fork_frame(k) for k in range(8)}, fx0, fy1,
           baseline=1, state='f0')
    sc.fork_frames = ['f%d' % k for k in range(8)]

    # ---------- writing that only ultraviolet light shows
    sc.uv(lambda im, dd: glow_text(im, (178, 162), 'SAUCE THY OFFERING', 8, (120, 255, 160)))
    sc.uv(lambda im, dd: glow_text(im, (322, 29), 'THE WORD IS SPUN', 9, (255, 240, 120)))
    sc.uv(lambda im, dd: glow_text(im, (90, 226), 'FIRST CAME THE STRING', 8, (120, 230, 255)))

    # ---------- walkable floor, minus furniture
    wd = sc.wd
    wd.polygon([(64, 195), (128, 196), (208, 199), (600, 199), (640, 204), (640, 288), (0, 288), (0, 250)], fill=1)
    wd.polygon(SOD, fill=0)
    wd.rectangle([0, 0, 63, 288], fill=0)
    wd.rectangle([286, 194, 356, 226], fill=0)                  # plinth
    wd.ellipse([211, 256, 300, 290], fill=0)                    # side table under the box
    wd.rectangle([330, 250, 492, 288], fill=0)                  # spinner base
    wd.polygon([(504, 252), (640, 248), (640, 288), (504, 288)], fill=0)   # scales table
    wd.rectangle([600, 194, 640, 230], fill=0)                  # wardrobe

    # ---------- walk-behinds: things in front of the player
    sc.walkbehind('poly', SOD, 288)
    wb = sc.walkbehind('poly', [(213, 236), (296, 236), (299, 262), (298, 288), (212, 288), (212, 262)], 286)
    sc.walkbehind('rect', [332, 218, 490, 288], 286)
    sc.walkbehind('rect', [288, 94, 354, 224], 224)
    return sc


if __name__ == '__main__':
    sc = nave()
    sc.bg.save('/tmp/claude-0/nave/bg_test.png')
    sc.uv_frame().save('/tmp/claude-0/nave/uv_test.png')
