"""The two rooms at the party, the title screen and their objects.

Both rooms share one camera: a back wall from x 96 to 544, the floor from
y 148 down to the bottom of the 640x288 view, and the side walls slanting
out towards the viewer. Below y 288 the interface is drawn over the room.

Every room is described by a Scene: it paints the background and, in the
same breath, the hotspot, walkable and walk-behind masks, so the art and the
masks can't drift apart. Objects are separate RGBA sprites placed with AGS
coordinates (x of the left edge, y of the bottom edge).
"""
import math
import random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance, ImageOps
from art_common import (canvas, outline, limb, rgba, shade, mix, vgrad, dither_rect,
                        noise, text, font, CLEAR)
import art_people

W, H = 640, 400
VIEW_H = 288
BACK_L, BACK_R, BACK_B = 96, 544, 148


def floor_x_left(y):
    """x of the left floor/wall seam at screen row y."""
    return BACK_L - (y - BACK_B) * (BACK_L + 40) / (VIEW_H - BACK_B)


def floor_x_right(y):
    return BACK_R + (y - BACK_B) * (W + 40 - BACK_R) / (VIEW_H - BACK_B)


class Scene:
    def __init__(self, name):
        self.name = name
        self.bg = Image.new('RGBA', (W, H), (0, 0, 0, 255))
        self.d = ImageDraw.Draw(self.bg)
        self.hot = Image.new('L', (W, H), 0)
        self.hd = ImageDraw.Draw(self.hot)
        self.walk = Image.new('L', (W, H), 0)
        self.wd = ImageDraw.Draw(self.walk)
        self.wb = Image.new('L', (W, H), 0)
        self.wbd = ImageDraw.Draw(self.wb)
        self.wb_baselines = []
        self.hotspots = []        # (script, name, walkto)
        self.objects = []         # dicts: script, name, sprites{state: img}, x, y, visible, baseline, clickable
        self.uv_marks = []        # callables painting glowing marks on the UV frame
        self.rnd = random.Random(name)

    # -- masks
    def hotspot(self, script, name, walkto, shapes):
        self.hotspots.append((script, name, walkto))
        hid = len(self.hotspots)
        for kind, data in shapes:
            if kind == 'rect':
                self.hd.rectangle(data, fill=hid)
            else:
                self.hd.polygon(data, fill=hid)
        return hid

    def walkbehind(self, shape_kind, data, baseline):
        self.wb_baselines.append(baseline)
        wid = len(self.wb_baselines)
        if shape_kind == 'rect':
            self.wbd.rectangle(data, fill=wid)
        else:
            self.wbd.polygon(data, fill=wid)
        return wid

    def obj(self, script, name, sprites, x, y, visible=True, baseline=0, clickable=True,
            state=None):
        state = state or next(iter(sprites))
        self.objects.append(dict(script=script, name=name, sprites=sprites, x=x, y=y,
                                 visible=visible, baseline=baseline, clickable=clickable,
                                 state=state))

    def uv(self, fn):
        self.uv_marks.append(fn)

    def uv_frame(self):
        """The room under ultraviolet light: everything dim and violet, with
        hidden fluorescent writing showing up."""
        a = np.asarray(self.bg.convert('RGB'), dtype=np.float32)
        lum = (a[..., 0] * 0.3 + a[..., 1] * 0.55 + a[..., 2] * 0.15) * 0.55
        out = np.stack([lum * 0.55, lum * 0.32, lum * 0.95], axis=-1)
        # pale, papery things fluoresce a little
        bright = np.clip(a.min(axis=-1) - 200, 0, None) * 2.5
        out[..., 0] += bright * 0.5
        out[..., 1] += bright * 0.35
        out[..., 2] += bright
        im = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).convert('RGBA')
        d = ImageDraw.Draw(im)
        d.rectangle([0, VIEW_H, W, H], fill=(0, 0, 0, 255))
        for fn in self.uv_marks:
            fn(im, d)
        return im


# ------------------------------------------------------------------ helpers
def glow_text(im, xy, s, size, color, anchor='mm', rot=0):
    """Fluorescent writing for the UV frame: a soft halo plus crisp text."""
    layer = canvas(W, H)
    ld = ImageDraw.Draw(layer)
    text(ld, xy, s, size, color, anchor=anchor)
    if rot:
        layer = layer.rotate(rot, center=xy, resample=Image.NEAREST)
    halo = layer.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(2))
    a = halo.getchannel('A').point(lambda v: v * 0.6)
    halo.putalpha(a)
    im.alpha_composite(halo)
    im.alpha_composite(layer)


def glow_lines(im, pts, color, width=2):
    layer = canvas(W, H)
    ld = ImageDraw.Draw(layer)
    ld.line(pts, fill=rgba(color), width=width, joint='curve')
    halo = layer.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(2))
    halo.putalpha(halo.getchannel('A').point(lambda v: v * 0.6))
    im.alpha_composite(halo)
    im.alpha_composite(layer)


def wood(d, box, base, rnd, vertical=False, grain=0.08):
    x0, y0, x1, y1 = box
    d.rectangle(box, fill=rgba(base))
    if vertical:
        for x in range(x0, x1 + 1, 2):
            if rnd.random() < 0.5:
                d.line([(x, y0), (x, y1)], fill=rgba(shade(base, 1 + rnd.uniform(-grain, grain))))
    else:
        for y in range(y0, y1 + 1, 2):
            if rnd.random() < 0.5:
                d.line([(x0, y), (x1, y)], fill=rgba(shade(base, 1 + rnd.uniform(-grain, grain))))


def frame_box(d, box, color, inner=None, width=3):
    x0, y0, x1, y1 = box
    d.rectangle(box, fill=rgba(shade(color, 0.6)))
    d.rectangle([x0 + 1, y0 + 1, x1 - 1, y1 - 1], fill=rgba(color))
    d.line([(x0 + 1, y0 + 1), (x1 - 1, y0 + 1)], fill=rgba(shade(color, 1.3)))
    d.line([(x0 + 1, y0 + 1), (x0 + 1, y1 - 1)], fill=rgba(shade(color, 1.2)))
    if inner:
        d.rectangle([x0 + width, y0 + width, x1 - width, y1 - width], fill=rgba(inner))


def spaghetti(d, rnd, x0, y0, x1, y1, n, color, wobble=4, steps=10):
    for _ in range(n):
        sx = rnd.uniform(x0, x1)
        pts = []
        for i in range(steps + 1):
            t = i / steps
            pts.append((sx + math.sin(t * 6 + sx) * wobble + rnd.uniform(-1, 1), y0 + (y1 - y0) * t))
        d.line(pts, fill=rgba(color), width=1)


def meatball(d, cx, cy, r, base=(140, 70, 44)):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=rgba(shade(base, 0.7)))
    d.ellipse([cx - r + 1, cy - r, cx + r - 1, cy + r - 2], fill=rgba(base))
    d.point((cx - r // 2, cy - r // 2), fill=rgba(shade(base, 1.4)))


# ------------------------------------------------------------------ shared shell
def shell(sc, wall, wall_dk, floor_a, floor_b, ceiling, plank=True):
    d = sc.d
    # back wall
    vgrad(d, (BACK_L, 0, BACK_R, BACK_B), shade(wall, 0.92), wall)
    # left & right walls (trapezoids)
    d.polygon([(0, 0), (BACK_L, 0), (BACK_L, BACK_B), (floor_x_left(VIEW_H), VIEW_H), (0, VIEW_H)],
              fill=rgba(wall_dk))
    d.polygon([(W, 0), (BACK_R, 0), (BACK_R, BACK_B), (floor_x_right(VIEW_H), VIEW_H), (W, VIEW_H)],
              fill=rgba(shade(wall_dk, 0.92)))
    # floor
    floor = [(BACK_L, BACK_B), (BACK_R, BACK_B), (floor_x_right(VIEW_H), VIEW_H),
             (floor_x_left(VIEW_H), VIEW_H)]
    d.polygon(floor, fill=rgba(floor_a))
    if plank:
        for y in range(BACK_B, VIEW_H):
            t = (y - BACK_B) / (VIEW_H - BACK_B)
            if int(y - BACK_B) % max(3, int(4 + t * 10)) == 0:
                d.line([(floor_x_left(y), y), (floor_x_right(y), y)], fill=rgba(floor_b))
        for i in range(-10, 11):
            xb = W / 2 + i * 32
            xf = W / 2 + i * 32 * 2.1
            d.line([(xb, BACK_B), (xf, VIEW_H)], fill=rgba(shade(floor_b, 1.05)))
    # baseboards and corners
    d.line([(BACK_L, BACK_B), (BACK_R, BACK_B)], fill=rgba(shade(wall_dk, 0.5)), width=2)
    d.line([(BACK_L, BACK_B), (floor_x_left(VIEW_H), VIEW_H)], fill=rgba(shade(wall_dk, 0.5)), width=2)
    d.line([(BACK_R, BACK_B), (floor_x_right(VIEW_H), VIEW_H)], fill=rgba(shade(wall_dk, 0.5)), width=2)
    d.line([(BACK_L, 0), (BACK_L, BACK_B)], fill=rgba(shade(wall_dk, 0.75)))
    d.line([(BACK_R, 0), (BACK_R, BACK_B)], fill=rgba(shade(wall_dk, 0.75)))
    # ceiling beam
    d.rectangle([0, 0, W, 8], fill=rgba(ceiling))
    d.line([(0, 8), (W, 8)], fill=rgba(shade(ceiling, 0.6)))
    d.rectangle([0, VIEW_H, W, H], fill=(0, 0, 0, 255))


def walkable_floor(sc, margin_top=158, front=286, inset=14):
    poly = [(floor_x_left(margin_top) + inset, margin_top), (floor_x_right(margin_top) - inset, margin_top),
            (min(W - 4, floor_x_right(front) - inset), front), (max(4, floor_x_left(front) + inset), front)]
    sc.wd.polygon(poly, fill=1)


# ================================================================== THE NAVE
NAVE_WALL = (236, 214, 168)
NAVE_WALL_DK = (196, 168, 120)
WORDS = [['THE', 'ALL', 'NO', 'SOME'],
         ['FORKS', 'SAUCE', 'PASTA', 'BREAD'],
         ['IS', 'SEEM', 'LOOK', 'FEEL'],
         ['SOGGY', 'HOLY', 'BLAND', 'RAW']]
ANSWER = [1, 2, 0, 1]          # ALL PASTA IS HOLY (short words: the windows are 20 px wide)
TILES = ['noodles', 'fork', 'string', 'counting']   # left to right on the timeline
TILE_NAMES = {'noodles': 'noodle tile', 'fork': 'fork tile', 'string': 'string tile', 'counting': 'tally bone tile'}
BUTTONS = ['penne', 'farfalle', 'shell']            # left to right on the puzzle box
BUTTON_UV = ['2', '3', '1']                         # press order shown under UV light


def nave():
    sc = Scene('nave')
    d = sc.d
    rnd = sc.rnd
    shell(sc, NAVE_WALL, NAVE_WALL_DK, (150, 96, 58), (122, 76, 44), (110, 70, 40))

    # wallpaper strips: alternating pale stripes with a tiny fork motif
    for i, x in enumerate(range(BACK_L + 2, BACK_R - 2, 18)):
        col = (242, 224, 182) if i % 2 else (230, 206, 156)
        d.rectangle([x, 12, x + 17, BACK_B - 12], fill=rgba(col))
        for y in range(20 + (i % 2) * 10, BACK_B - 20, 22):
            c = rgba(shade(col, 0.82))
            d.line([(x + 8, y), (x + 8, y + 7)], fill=c)
            d.line([(x + 6, y), (x + 6, y + 3)], fill=c)
            d.line([(x + 10, y), (x + 10, y + 3)], fill=c)
            d.line([(x + 6, y + 3), (x + 10, y + 3)], fill=c)
    d.rectangle([BACK_L, BACK_B - 12, BACK_R, BACK_B - 1], fill=rgba((140, 92, 56)))   # wainscot
    d.line([(BACK_L, BACK_B - 12), (BACK_R, BACK_B - 12)], fill=rgba((176, 122, 76)))
    sc.hotspot('hWallpaper', 'wallpaper strips', (320, 160),
               [('rect', [BACK_L + 2, 12, BACK_R - 2, BACK_B - 13])])

    # ---------- Weird Sauce (wall piece, back-left)
    x0, y0, x1, y1 = 110, 34, 196, 132
    wood(d, (x0, y0, x1, y1), (112, 66, 40), rnd)
    frame_box(d, (x0, y0, x1, y0 + 14), (60, 36, 24))
    text(d, ((x0 + x1) // 2, y0 + 7), 'WEIRD SAUCE', 9, (250, 210, 90), anchor='mm')
    bottles = [(122, (200, 40, 30)), (146, (90, 150, 50)), (170, (240, 170, 40))]
    for bx, bc in bottles:
        d.rectangle([bx, 58, bx + 14, 86], fill=rgba(shade(bc, 0.7)))
        d.rectangle([bx + 1, 60, bx + 13, 85], fill=rgba(bc))
        d.rectangle([bx + 4, 50, bx + 10, 58], fill=rgba((210, 220, 225)))
        d.line([(bx + 3, 62), (bx + 3, 82)], fill=rgba(shade(bc, 1.4)))
        d.line([(bx + 7, 86), (bx + 7, 96)], fill=rgba((200, 200, 210)), width=2)
    d.line([(129, 96), (177, 96)], fill=rgba((200, 200, 210)), width=2)
    d.rectangle([148, 96, 158, 108], fill=rgba((170, 176, 186)))     # mixing valve
    d.ellipse([146, 98, 160, 112], fill=rgba((150, 156, 166)))
    d.polygon([(151, 112), (155, 112), (156, 122), (150, 122)], fill=rgba((170, 176, 186)))   # spout
    d.ellipse([176, 102, 190, 116], fill=rgba((60, 40, 30)))         # dial
    d.ellipse([178, 104, 188, 114], fill=rgba((220, 200, 150)))
    d.line([(183, 109), (186, 105)], fill=rgba((60, 30, 30)))
    d.rectangle([140, 124, 166, 130], fill=rgba((230, 230, 236)))     # drip tray
    d.ellipse([150, 124, 156, 128], fill=rgba((180, 60, 40)))
    sc.hotspot('hSauce', 'Weird Sauce', (152, 166), [('rect', [x0, y0, x1, y1])])
    sc.uv(lambda im, dd: glow_text(im, (153, 141), 'SAUCE THY OFFERING', 9, (120, 255, 160)))

    # ---------- Glutenous Truth (small painting)
    frame_box(d, (204, 34, 246, 92), (196, 150, 60), inner=(40, 30, 60), width=4)
    d.ellipse([214, 52, 236, 74], fill=rgba((250, 210, 120)))
    d.ellipse([217, 55, 233, 71], fill=rgba((230, 170, 80)))
    for a in range(0, 360, 30):
        r = math.radians(a)
        d.line([(225 + 12 * math.cos(r), 63 + 12 * math.sin(r)), (225 + 16 * math.cos(r), 63 + 16 * math.sin(r))],
               fill=rgba((250, 230, 150)))
    d.line([(220, 60), (230, 60)], fill=rgba((200, 130, 60)))
    d.line([(219, 65), (231, 65)], fill=rgba((200, 130, 60)))
    sc.hotspot('hGlutenous', 'painting "Glutenous Truth"', (225, 160), [('rect', [204, 34, 246, 92])])

    # ---------- the stained-glass painted flat (centre)
    sx0, sx1, sy0, sy1 = 256, 352, 14, 146
    d.rectangle([sx0 - 3, sy0 + 20, sx1 + 3, sy1], fill=rgba((70, 50, 40)))
    d.pieslice([sx0 - 3, sy0 - 3, sx1 + 3, sy0 + 60], 180, 360, fill=rgba((70, 50, 40)))
    pane_cols = [(60, 90, 190), (200, 50, 60), (240, 190, 60), (60, 150, 90), (140, 70, 170), (230, 120, 40)]
    glass = canvas(W, H)
    gd = ImageDraw.Draw(glass)
    gd.rectangle([sx0, sy0 + 26, sx1, sy1 - 2], fill=rgba((60, 90, 190)))
    gd.pieslice([sx0, sy0, sx1, sy0 + 56], 180, 360, fill=rgba((60, 90, 190)))
    for row, y in enumerate(range(sy0, sy1, 16)):
        for col, x in enumerate(range(sx0, sx1, 16)):
            c = pane_cols[(row * 2 + col * 3) % len(pane_cols)]
            c = mix(c, (60, 90, 190), 0.55)
            gd.rectangle([x, y, x + 15, y + 15], fill=rgba(c))
    gd.rectangle([sx0, sy1 - 22, sx1, sy1 - 2], fill=rgba((60, 130, 70)))
    for x in range(sx0 + 4, sx1, 12):
        gd.polygon([(x, sy1 - 22), (x + 6, sy1 - 30), (x + 12, sy1 - 22)], fill=rgba((80, 160, 80)))
    gd.ellipse([sx0 + 30, sy0 + 8, sx1 - 30, sy0 + 44], fill=rgba((250, 210, 90)))
    # the noodly one: body, eyes on stalks, noodle appendages, meatballs
    cx, cy = 304, 82
    for k in range(9):
        a = math.pi * (0.1 + 0.8 * k / 8)
        pts = [(cx + math.cos(a + 0.4 * math.sin(t * 3)) * t * 40, cy + 6 + math.sin(a) * t * 50) for t in
               [i / 10 for i in range(11)]]
        gd.line(pts, fill=rgba((250, 222, 140)), width=3)
    gd.ellipse([cx - 16, cy - 10, cx + 16, cy + 14], fill=rgba((250, 222, 140)))
    for mx in (cx - 9, cx + 9):
        gd.ellipse([mx - 7, cy - 4, mx + 7, cy + 10], fill=rgba((150, 70, 44)))
    for ex in (cx - 7, cx + 7):
        gd.line([(ex, cy - 10), (ex + (ex - cx) // 2, cy - 26)], fill=rgba((250, 222, 140)), width=2)
        gd.ellipse([ex + (ex - cx) // 2 - 5, cy - 32, ex + (ex - cx) // 2 + 5, cy - 22], fill=rgba((255, 255, 255)))
        gd.ellipse([ex + (ex - cx) // 2 - 2, cy - 28, ex + (ex - cx) // 2 + 2, cy - 24], fill=rgba((20, 20, 30)))
    gd.rectangle([sx0, sy0, sx1, sy1], outline=None)
    # clip to the arch
    clip = Image.new('L', (W, H), 0)
    cd_ = ImageDraw.Draw(clip)
    cd_.rectangle([sx0, sy0 + 26, sx1, sy1 - 2], fill=255)
    cd_.pieslice([sx0, sy0, sx1, sy0 + 56], 180, 360, fill=255)
    glass.putalpha(Image.composite(glass.getchannel('A'), Image.new('L', (W, H), 0), clip))
    # lead lines
    mask = glass.getchannel('A')
    edges = glass.convert('RGB').filter(ImageFilter.FIND_EDGES).convert('L').point(lambda v: 255 if v > 40 else 0)
    lead = Image.new('RGBA', (W, H), (40, 34, 40, 255))
    glass.paste(lead, (0, 0), Image.composite(edges, Image.new('L', (W, H), 0), mask))
    sc.bg.alpha_composite(glass)
    d.line([(sx0, sy1), (sx1, sy1)], fill=rgba((50, 36, 30)), width=3)
    sc.hotspot('hFlat', 'stained-glass flat', (304, 162),
               [('rect', [sx0, sy0 + 26, sx1, sy1]), ('poly', [(sx0, sy0 + 28), (sx0 + 20, sy0 + 6), (sx1 - 20, sy0 + 6), (sx1, sy0 + 28)])])
    sc.uv(lambda im, dd: glow_text(im, (304, 132), 'THE WORD IS SPUN', 9, (255, 240, 120)))

    # ---------- timeline of ancient technology (board; tiles + drawer are objects)
    tx0, ty0, tx1, ty1 = 362, 40, 464, 116
    wood(d, (tx0, ty0, tx1, ty1), (96, 60, 36), rnd)
    frame_box(d, (tx0, ty0, tx1, ty0 + 13), (60, 36, 24))
    text(d, ((tx0 + tx1) // 2, ty0 + 7), 'TIMELINE', 9, (250, 210, 90), anchor='mm')
    d.line([(tx0 + 6, 96), (tx1 - 6, 96)], fill=rgba((250, 230, 180)), width=2)
    d.polygon([(tx1 - 6, 92), (tx1 - 2, 96), (tx1 - 6, 100)], fill=rgba((250, 230, 180)))
    text(d, (tx0 + 6, 100), 'OLDEST', 8, (240, 210, 150))
    text(d, (tx1 - 6, 100), 'NEWEST', 8, (240, 210, 150), anchor='ra')
    d.rectangle([396, ty1 - 2, 430, ty1 + 8], fill=rgba((70, 44, 28)))   # drawer front (closed)
    d.rectangle([410, ty1 + 2, 416, ty1 + 4], fill=rgba((220, 190, 90)))
    sc.hotspot('hTimeline', 'timeline of ancient technology', (456, 172), [('rect', [tx0, ty0, tx1, ty1 + 8])])

    # ---------- archway to the Crypt, in the right wall near the back; the panel is an object
    arch_out = [(550, 156), (550, 58), (556, 40), (566, 30), (578, 28), (588, 34), (594, 46), (594, 200)]
    arch_in = [(554, 159), (554, 60), (559, 45), (567, 36), (577, 34), (585, 38), (590, 48), (590, 196)]
    d.polygon(arch_out, fill=rgba((150, 120, 96)))
    d.polygon(arch_in, fill=rgba((26, 16, 36)))
    for i in range(6):                                                 # steps going down into the dark
        y0_ = 120 + i * 13
        d.line([(556, y0_ + i * 2), (588, y0_ + i * 6)], fill=rgba((110, 70, 140)))
    vgrad(d, (558, 60, 586, 110), (40, 20, 60), (80, 44, 110))
    sc.hotspot('hArch', 'archway', (566, 210), [('poly', arch_in)])
    panel = canvas(48, 176)
    pd = ImageDraw.Draw(panel)
    shp = [(x - 548, y - 26) for x, y in arch_out]
    rw = shade(NAVE_WALL_DK, 0.92)
    pd.polygon(shp, fill=rgba(rw))
    pd.line(shp + [shp[0]], fill=rgba(shade(rw, 0.94)))
    # under UV light the panel admits it is not a wall
    pa = np.asarray(panel, dtype=np.float32)
    lum = (pa[..., 0] * 0.3 + pa[..., 1] * 0.55 + pa[..., 2] * 0.15) * 0.55
    uvp = np.stack([lum * 0.55, lum * 0.32, lum * 0.95, pa[..., 3]], axis=-1)
    panel_uv = Image.fromarray(np.clip(uvp, 0, 255).astype(np.uint8), 'RGBA')
    lay = canvas(48, 176)
    ld = ImageDraw.Draw(lay)
    for k, wtxt in enumerate(('NOT', 'A', 'WALL')):
        text(ld, (24, 62 + k * 15), wtxt, 10, (255, 120, 220), anchor='mm')
    halo = lay.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(2))
    panel_uv.alpha_composite(halo)
    panel_uv.alpha_composite(lay)
    clipm = panel.getchannel('A')
    panel_uv.putalpha(clipm)
    sc.obj('oArchPanel', 'wall', {'closed': panel, 'uv': panel_uv}, 548, 201, baseline=1)

    # ---------- sacred topology display: knots in a glass case (back wall, right)
    d.rectangle([476, 30, 538, 116], fill=rgba((80, 56, 40)))
    d.rectangle([480, 34, 534, 112], fill=rgba((40, 60, 80)))
    d.line([(482, 36), (500, 36)], fill=rgba((120, 150, 170)))
    for i, (kx, ky) in enumerate(((494, 56), (520, 74), (494, 94))):
        col = [(240, 220, 160), (230, 90, 70), (120, 190, 230)][i]
        if i == 1:      # figure-eight
            pts = [(kx + 11 * math.sin(t), ky + 9 * math.sin(t) * math.cos(t)) for t in [j / 30 * 2 * math.pi for j in range(31)]]
        else:           # trefoil
            pts = [(kx + 4 * (math.sin(t) + 2 * math.sin(2 * t)) / 1.4, ky + 4 * (math.cos(t) - 2 * math.cos(2 * t)) / 1.4)
                   for t in [j / 40 * 2 * math.pi for j in range(41)]]
        d.line(pts, fill=rgba(col), width=2)
    sc.hotspot('hTopology', 'sacred topology display', (507, 168), [('rect', [476, 30, 538, 116])])

    # ---------- crocheted pasta display: a little shelf under "Glutenous Truth"
    d.rectangle([200, 110, 250, 114], fill=rgba((110, 70, 44)))
    d.line([(200, 115), (250, 115)], fill=rgba((70, 44, 28)))
    yarn_cols = [(250, 220, 140), (240, 200, 120), (230, 120, 60), (120, 170, 80)]
    for i in range(6):
        bx = 202 + i * 8
        c = yarn_cols[i % 4]
        d.ellipse([bx, 101, bx + 7, 110], fill=rgba(c))
        d.arc([bx + 1, 102, bx + 6, 109], 0, 360, fill=rgba(shade(c, 0.75)))
    sc.hotspot('hCrochet', 'crocheted pasta display', (225, 162), [('rect', [200, 98, 250, 116])])

    # ---------- left wall: "First Taste" painting, the Spinning Fork (object), the door
    d.polygon([(42, 26), (84, 20), (84, 58), (42, 62)], fill=rgba((196, 150, 60)))
    d.polygon([(45, 30), (81, 25), (81, 55), (45, 58)], fill=rgba((60, 40, 50)))
    d.ellipse([56, 32, 72, 50], fill=rgba((240, 200, 160)))                # a face
    d.ellipse([61, 41, 67, 47], fill=rgba((150, 40, 40)))                  # mouth open
    d.line([(48, 54), (64, 45)], fill=rgba((250, 222, 140)), width=2)       # a noodle going in
    d.point((60, 38), fill=rgba((30, 20, 20))); d.point((68, 37), fill=rgba((30, 20, 20)))
    sc.hotspot('hFirstTaste', 'painting "First Taste"', (112, 186), [('poly', [(42, 26), (84, 20), (84, 58), (42, 62)])])
    d.polygon([(0, 112), (36, 124), (36, 244), (0, 270)], fill=rgba((120, 76, 46)))
    d.polygon([(4, 122), (32, 131), (32, 238), (4, 258)], fill=rgba((140, 90, 56)))
    d.ellipse([26, 180, 32, 188], fill=rgba((230, 200, 100)))
    d.polygon([(8, 140), (24, 145), (24, 160), (8, 156)], fill=rgba((240, 236, 220)))
    text(d, (16, 151), '913', 7, (40, 30, 30), anchor='mm')
    sc.hotspot('hDoor', 'door', (52, 268), [('poly', [(0, 112), (36, 124), (36, 244), (0, 270)])])

    # ---------- wardrobe on the right wall, at the front (object)
    wardrobe_closed = canvas(46, 236)
    wdd = ImageDraw.Draw(wardrobe_closed)
    wdd.polygon([(0, 12), (45, 0), (45, 235), (0, 186)], fill=rgba((96, 58, 34)))
    wdd.polygon([(4, 18), (45, 7), (45, 228), (4, 184)], fill=rgba((124, 78, 46)))
    wdd.line([(4, 100), (45, 96)], fill=rgba((90, 54, 32)))
    wdd.ellipse([10, 104, 14, 110], fill=rgba((230, 200, 100)))
    wardrobe_open = canvas(46, 236)
    wod = ImageDraw.Draw(wardrobe_open)
    wod.polygon([(0, 12), (45, 0), (45, 235), (0, 186)], fill=rgba((96, 58, 34)))
    wod.polygon([(4, 18), (45, 7), (45, 228), (4, 184)], fill=rgba((40, 26, 18)))
    wod.line([(6, 34), (45, 26)], fill=rgba((160, 160, 170)), width=2)          # rail
    for i, hx in enumerate((22, 34)):                                          # hanging robes
        col = [(110, 40, 120), (200, 170, 60)][i]
        wod.polygon([(hx, 30 - i * 3), (hx + 9, 28 - i * 3), (hx + 11, 120), (hx - 2, 124)], fill=rgba(col))
    door = [(0, 12), (-30, 30), (-30, 200), (0, 186)]
    sc.obj('oWardrobe', 'wardrobe', {'closed': wardrobe_closed, 'open': wardrobe_open}, 596, 272, baseline=273)
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
    sc.obj('oBeads', 'pasta rosary beads', {'on': outline(beads)}, 604, 180, visible=False, baseline=275)

    # ---------- the sod table (left), with a tiny world on it
    t_top = [(44, 190), (226, 180), (236, 206), (36, 220)]
    d.polygon([(36, 220), (236, 206), (236, 222), (36, 238)], fill=rgba((96, 60, 36)))       # front apron
    for lx in (44, 128, 224):                                                              # legs
        ly = 238 - (lx - 36) * 16 / 200
        d.rectangle([lx, ly - 2, lx + 5, ly + 22], fill=rgba((80, 50, 30)))
    d.polygon(t_top, fill=rgba((76, 140, 56)))
    for _ in range(900):                                                                   # grass
        u, v = rnd.random(), rnd.random()
        x = (44 + (226 - 44) * u) * (1 - v) + (36 + (236 - 36) * u) * v
        y = (190 - 10 * u) * (1 - v) + (220 - 14 * u) * v
        d.point((x, y), fill=rgba(rnd.choice([(96, 168, 70), (60, 120, 46), (120, 186, 84)])))
    # tiny world: hills, a river of marinara, little villagers, a tiny temple
    d.ellipse([60, 186, 104, 206], fill=rgba((90, 150, 64)))
    d.ellipse([140, 182, 176, 198], fill=rgba((100, 160, 70)))
    d.line([(110, 214), (126, 202), (150, 206), (170, 196)], fill=rgba((190, 50, 40)), width=2)
    for vx, vy in ((84, 205), (92, 208), (132, 196), (158, 205), (164, 202)):
        d.rectangle([vx, vy - 3, vx + 1, vy], fill=rgba((250, 240, 220)))
        d.point((vx, vy - 4), fill=rgba((230, 180, 140)))
    d.rectangle([188, 186, 202, 196], fill=rgba((240, 236, 226)))
    d.polygon([(186, 186), (195, 180), (204, 186)], fill=rgba((200, 60, 50)))
    # the audio-story handset: an old phone on the table
    d.rectangle([48, 196, 70, 206], fill=rgba((40, 36, 40)))
    d.rounded_rectangle([46, 190, 72, 197], 3, fill=rgba((60, 56, 64)))
    d.ellipse([54, 198, 62, 204], fill=rgba((180, 170, 150)))
    d.line([(70, 202), (78, 208), (74, 212)], fill=rgba((40, 36, 40)))
    sc.hotspot('hHandset', 'telephone handset', (90, 270), [('rect', [44, 188, 76, 208])])
    # pamphlet holder at the right end of the table
    d.polygon([(206, 176), (224, 174), (226, 190), (208, 192)], fill=rgba((200, 196, 186)))
    sc.hotspot('hSodTable', 'sod table', (140, 268),
               [('poly', [(36, 220), (236, 206), (236, 240), (36, 256)]), ('poly', t_top)])
    sc.hd.rectangle([44, 188, 76, 208], fill=sc.hotspots.index(('hHandset', 'telephone handset', (90, 270))) + 1)
    pamph = canvas(14, 18)
    ppd = ImageDraw.Draw(pamph)
    ppd.polygon([(1, 2), (12, 0), (13, 16), (2, 17)], fill=rgba((250, 246, 230)))
    ppd.line([(3, 5), (10, 4)], fill=rgba((200, 60, 50)))
    ppd.line([(3, 8), (10, 7)], fill=rgba((90, 90, 100)))
    ppd.line([(3, 11), (10, 10)], fill=rgba((90, 90, 100)))
    sc.obj('oPamphlet', 'Spaghetti Theory pamphlet', {'on': outline(pamph)}, 209, 190, baseline=239)
    sc.uv(lambda im, dd: glow_text(im, (130, 170), 'FIRST CAME THE STRING', 8, (120, 230, 255)))

    # ---------- spaghetti sculpture on its pedestal (centre)
    px0, px1 = 292, 348
    d.polygon([(px0, 202), (px1, 202), (px1 + 4, 208), (px0 - 4, 208)], fill=rgba((230, 226, 214)))
    d.rectangle([px0, 208, px1, 238], fill=rgba((212, 206, 192)))
    d.rectangle([px1 - 10, 208, px1, 238], fill=rgba((180, 174, 160)))
    d.rectangle([px0 - 4, 236, px1 + 4, 242], fill=rgba((196, 190, 176)))
    text(d, (320, 222), 'SPAGHETTI', 7, (110, 100, 90), anchor='mm')
    sculpt = canvas(W, H)
    scd = ImageDraw.Draw(sculpt)
    # a spiralling tower of noodles rising into a monster with meatball eyes
    for k in range(40):
        a0 = rnd.uniform(0, math.tau)
        pts = []
        for i in range(30):
            t = i / 29
            yy = 202 - t * 70
            rad = 20 * (1 - t) + 9 + 5 * math.sin(t * 9 + k)
            pts.append((320 + rad * math.cos(a0 + t * 7), yy + 3 * math.sin(a0 + t * 7)))
        scd.line(pts, fill=rgba(rnd.choice([(250, 222, 140), (240, 206, 118), (226, 190, 100)])), width=1)
    for mx, my in ((308, 136), (332, 138), (320, 164), (302, 184), (340, 178)):
        meatball(scd, mx, my, 6)
    scd.line([(308, 130), (302, 116)], fill=rgba((250, 222, 140)), width=2)
    scd.line([(332, 132), (338, 116)], fill=rgba((250, 222, 140)), width=2)
    for ex in (301, 339):
        scd.ellipse([ex - 5, 110, ex + 5, 120], fill=rgba((255, 255, 255)))
        scd.ellipse([ex - 2, 113, ex + 2, 117], fill=rgba((20, 20, 30)))
    sc.bg.alpha_composite(outline(sculpt, (70, 50, 30, 255)))
    sc.hotspot('hSculpture', 'spaghetti sculpture', (320, 256),
               [('rect', [286, 106, 354, 242])])
    sc.walkbehind('rect', [284, 104, 356, 242], 242)
    for ex in (301, 339):
        sc.uv(lambda im, dd, ex=ex: glow_lines(im, [(ex - 4, 115), (ex + 4, 115)], (255, 255, 140), 3))

    # ---------- paragraph spinner (back right, on a table); the drums are objects
    d.polygon([(424, 202), (532, 198), (540, 212), (418, 218)], fill=rgba((120, 76, 46)))     # table top
    d.polygon([(418, 218), (540, 212), (540, 218), (418, 224)], fill=rgba((90, 56, 34)))
    for lx, ly in ((422, 224), (532, 218), (486, 221)):
        d.rectangle([lx, ly, lx + 4, ly + 20], fill=rgba((80, 50, 30)))
    d.rectangle([436, 124, 520, 204], fill=rgba((70, 44, 28)))                               # cabinet
    d.rectangle([439, 138, 517, 201], fill=rgba((110, 70, 42)))
    frame_box(d, (436, 124, 520, 137), (60, 36, 24))
    text(d, (478, 130), 'PARAGRAPH', 8, (250, 210, 90), anchor='mm')
    for i in range(4):
        y = 141 + i * 15
        d.rectangle([442, y - 1, 514, y + 13], fill=rgba((40, 26, 18)))
        d.rectangle([516, y + 2, 522, y + 8], fill=rgba((200, 180, 120)))                     # crank knobs
    sc.hotspot('hSpinner', 'paragraph spinner', (404, 228), [('rect', [436, 124, 524, 216])])

    def drum_sprite(word, uv=False, correct=False):
        im = canvas(70, 13)
        dd = ImageDraw.Draw(im)
        base = (246, 236, 214) if not uv else (70, 40, 110)
        for yy in range(13):
            t = abs(yy - 6) / 6
            dd.line([(0, yy), (69, yy)], fill=rgba(shade(base, 1.0 - 0.35 * t * t)))
        if uv and correct:
            lay = canvas(70, 13)
            ld = ImageDraw.Draw(lay)
            text(ld, (35, 7), word, 9, (180, 255, 120), anchor='mm')
            halo = lay.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(1.5))
            im.alpha_composite(halo)
            im.alpha_composite(lay)
        else:
            text(dd, (35, 7), word, 9, (40, 30, 30) if not uv else (110, 80, 150), anchor='mm')
        return im

    for i in range(4):
        sprites = {}
        for j, wtxt in enumerate(WORDS[i]):
            sprites['w%d' % j] = drum_sprite(wtxt)
            sprites['u%d' % j] = drum_sprite(wtxt, uv=True, correct=(j == ANSWER[i]))
        sc.obj('oDrum%d' % (i + 1), 'drum', sprites, 443, 141 + i * 15 + 13, baseline=225,
               state={0: 'w0', 1: 'w0', 2: 'w1', 3: 'w2'}[i])
    sc.uv(lambda im, dd: glow_text(im, (478, 116), 'SPIN UNTIL IT GLOWS', 8, (180, 255, 120)))

    # ---------- scales of pasta (front right)
    d.polygon([(470, 240), (584, 236), (592, 258), (462, 264)], fill=rgba((120, 76, 46)))
    d.polygon([(462, 264), (592, 258), (592, 266), (462, 272)], fill=rgba((90, 56, 34)))
    for lx, ly in ((466, 272), (584, 266)):
        d.rectangle([lx, ly, lx + 5, ly + 16], fill=rgba((80, 50, 30)))
    gold = (220, 180, 70)
    d.rectangle([524, 194, 528, 248], fill=rgba(gold))
    d.polygon([(512, 248), (540, 248), (534, 242), (518, 242)], fill=rgba(shade(gold, 0.8)))
    d.line([(492, 202), (560, 198)], fill=rgba(gold), width=2)
    for px, py in ((492, 202), (560, 198)):
        d.line([(px, py), (px - 10, py + 22)], fill=rgba((180, 180, 190)))
        d.line([(px, py), (px + 10, py + 22)], fill=rgba((180, 180, 190)))
        d.chord([px - 13, py + 16, px + 13, py + 30], 0, 180, fill=rgba(gold))
    d.ellipse([522, 188, 530, 196], fill=rgba(gold))
    for k in range(5):                                                          # a heap of fusilli on one pan
        d.arc([552 + k * 3, 213 - (k % 2) * 3, 558 + k * 3, 219 - (k % 2) * 3], 0, 300, fill=rgba((240, 200, 110)))
    d.rectangle([486, 215, 498, 219], fill=rgba((150, 150, 160)))             # a little brass weight
    sc.hotspot('hScales', 'scales of pasta', (526, 284), [('poly', [(478, 186), (574, 186), (592, 266), (462, 272)])])

    # ---------- puzzle box table (front centre-left) and the box itself (object)
    d.ellipse([232, 252, 286, 266], fill=rgba((110, 70, 42)))
    d.rectangle([254, 262, 262, 286], fill=rgba((80, 50, 30)))
    d.ellipse([244, 280, 272, 288], fill=rgba((70, 44, 28)))
    sc.walkbehind('poly', [(230, 248), (288, 248), (288, 268), (264, 288), (252, 288), (230, 268)], 287)

    def box_sprite(state, uv=False):
        im = canvas(48, 30)
        dd = ImageDraw.Draw(im)
        wood_c = (150, 96, 50) if not uv else (60, 36, 90)
        dd.rectangle([2, 10, 45, 29], fill=rgba(shade(wood_c, 0.8)))
        dd.rectangle([3, 11, 44, 28], fill=rgba(wood_c))
        for x in range(4, 44, 6):
            dd.line([(x, 12), (x + 3, 27)], fill=rgba(shade(wood_c, 0.88)))
        if state == 'closed':
            dd.polygon([(1, 10), (46, 10), (42, 3), (5, 3)], fill=rgba(shade(wood_c, 1.15)))
            dd.line([(5, 3), (42, 3)], fill=rgba(shade(wood_c, 1.3)))
        else:
            dd.polygon([(4, 10), (43, 10), (40, 0), (7, 0)], fill=rgba((40, 26, 18)))   # lid tipped back
            dd.rectangle([5, 8, 42, 11], fill=rgba((30, 20, 14)))
        return outline(im)

    sc.obj('oBox', 'puzzle box', {'closed': box_sprite('closed'), 'open': box_sprite('open'),
                                   'uvclosed': box_sprite('closed', uv=True), 'uvopen': box_sprite('open', uv=True)},
           236, 256, baseline=287)

    def button_sprite(kind, pressed=False, uv=None):
        im = canvas(11, 11)
        dd = ImageDraw.Draw(im)
        dd.ellipse([0, 0, 10, 10], fill=rgba((60, 40, 30) if not uv else (30, 20, 50)))
        dd.ellipse([1, 1 + (1 if pressed else 0), 9, 9], fill=rgba((180, 150, 90) if not uv else (70, 50, 110)))
        pc = (250, 222, 140) if not uv else (110, 90, 150)
        if kind == 'penne':
            dd.polygon([(2, 7), (6, 2), (8, 3), (4, 8)], fill=rgba(pc))
        elif kind == 'farfalle':
            dd.polygon([(2, 3), (5, 5), (8, 3), (8, 7), (5, 5), (2, 7)], fill=rgba(pc))
        else:
            dd.chord([2, 2, 8, 8], 0, 360, fill=rgba(pc))
            dd.arc([3, 3, 7, 7], 200, 340, fill=rgba(shade(pc, 0.7)))
        if uv:
            lay = canvas(11, 11)
            text(ImageDraw.Draw(lay), (5, 5), uv, 9, (255, 255, 120), anchor='mm')
            im.alpha_composite(lay.filter(ImageFilter.MaxFilter(3)).point(lambda v: v * 0.5))
            im.alpha_composite(lay)
        return im

    for i, kind in enumerate(BUTTONS):
        sc.obj('oBtn%d' % (i + 1), '%s button' % kind,
               {'up': button_sprite(kind), 'down': button_sprite(kind, pressed=True),
                'uv': button_sprite(kind, uv=BUTTON_UV[i])},
               243 + i * 12, 253, baseline=288)
    rig = canvas(16, 9)
    rd = ImageDraw.Draw(rig)
    rd.rounded_rectangle([0, 1, 15, 8], 3, fill=rgba((250, 206, 70)))
    for x in range(2, 15, 3):
        rd.line([(x, 2), (x, 7)], fill=rgba((214, 160, 40)))
    rd.ellipse([12, 1, 15, 8], fill=rgba((150, 100, 30)))
    sc.obj('oRigatone', 'golden rigatone', {'on': outline(rig)}, 252, 241, visible=False, baseline=288)

    # ---------- timeline tiles + drawer + pendant (objects)
    def tile_sprite(kind, lit):
        im = canvas(20, 26)
        dd = ImageDraw.Draw(im)
        bgc = (250, 240, 210) if not lit else (255, 226, 110)
        dd.rectangle([0, 0, 19, 25], fill=rgba((60, 36, 24)))
        dd.rectangle([1, 1, 18, 24], fill=rgba(bgc))
        ink = (70, 50, 40)
        if kind == 'string':
            dd.line([(3, 20), (6, 8), (10, 18), (14, 6), (16, 14)], fill=rgba((150, 100, 50)), width=2)
        elif kind == 'counting':                          # a notched bone
            dd.rounded_rectangle([4, 5, 15, 21], 3, fill=rgba((236, 226, 200)))
            for y in range(7, 20, 3):
                dd.line([(4, y), (8, y)], fill=rgba(ink))
        elif kind == 'noodles':                           # a bowl of noodles
            dd.chord([2, 8, 17, 22], 0, 180, fill=rgba((200, 80, 60)))
            for x in range(5, 15, 3):
                dd.arc([x - 2, 6, x + 2, 16], 180, 360, fill=rgba((230, 190, 90)))
        elif kind == 'fork':
            dd.line([(10, 22), (10, 11)], fill=rgba((150, 150, 160)), width=2)
            for x in (6, 10, 14):
                dd.line([(x, 4), (x, 11)], fill=rgba((150, 150, 160)))
            dd.line([(6, 11), (14, 11)], fill=rgba((150, 150, 160)))
        return im

    for i, kind in enumerate(TILES):
        sc.obj('oTile%d' % (i + 1), TILE_NAMES[kind], {'off': tile_sprite(kind, False), 'on': tile_sprite(kind, True)},
               370 + i * 23, 90, baseline=1)
    drawer = canvas(36, 16)
    dd = ImageDraw.Draw(drawer)
    dd.polygon([(0, 0), (35, 0), (35, 15), (0, 15)], fill=rgba((70, 44, 28)))
    dd.rectangle([2, 0, 33, 7], fill=rgba((40, 26, 18)))
    dd.rectangle([14, 10, 20, 12], fill=rgba((220, 190, 90)))
    sc.obj('oDrawer', 'drawer', {'open': outline(drawer)}, 395, 132, visible=False, baseline=2)
    pend = canvas(12, 12)
    pdd = ImageDraw.Draw(pend)
    pdd.line([(1, 1), (6, 4), (11, 1)], fill=rgba((150, 130, 180)))
    pdd.polygon([(6, 3), (9, 6), (6, 11), (3, 6)], fill=rgba((190, 120, 255)))
    pdd.point((5, 5), fill=rgba((240, 220, 255)))
    sc.obj('oPendant', 'UV pendant', {'on': outline(pend)}, 407, 124, visible=False, baseline=3)

    # ---------- the Spinning Fork (a moving painting on the left wall)
    def fork_frame(k):
        im = canvas(46, 64)
        dd = ImageDraw.Draw(im)
        dd.polygon([(0, 8), (44, 0), (44, 56), (0, 62)], fill=rgba((196, 150, 60)))
        dd.polygon([(3, 12), (41, 5), (41, 52), (3, 58)], fill=rgba((40, 70, 90)))
        cx, cy = 22, 31
        for r in range(4, 18, 3):                                       # a swirl of spaghetti
            a0 = k * math.pi / 4 + r * 0.4
            dd.arc([cx - r, cy - r * 0.8, cx + r, cy + r * 0.8], math.degrees(a0), math.degrees(a0) + 260,
                   fill=rgba((250, 222, 140)))
        ang = k * math.pi / 4
        fx, fy = cx + 3 * math.cos(ang), cy + 3 * math.sin(ang)
        dd.line([(fx, fy), (fx + 2, fy - 22)], fill=rgba((210, 214, 222)), width=2)
        for t in (-3, 0, 3):
            dd.line([(fx + t, fy + 4), (fx + t, fy - 2)], fill=rgba((210, 214, 222)))
        return im

    sc.obj('oFork', 'painting "Spinning Fork"', {('f%d' % k): fork_frame(k) for k in range(8)}, 42, 130, baseline=1,
           state='f0')
    sc.fork_frames = ['f%d' % k for k in range(8)]

    # ---------- walkable floor, minus furniture
    walkable_floor(sc)
    wd = sc.wd
    wd.polygon([(30, 214), (244, 198), (244, 244), (30, 262)], fill=0)          # sod table
    wd.rectangle([284, 196, 356, 248], fill=0)                                    # pedestal
    wd.polygon([(412, 196), (546, 190), (546, 232), (412, 238)], fill=0)        # spinner table
    wd.polygon([(456, 234), (600, 228), (600, 274), (456, 280)], fill=0)        # scales table
    wd.ellipse([228, 250, 290, 272], fill=0)                                      # side table
    wd.rectangle([250, 262, 266, 288], fill=0)
    wd.polygon([(590, 200), (640, 200), (640, 288), (590, 288)], fill=0)        # wardrobe
    return sc


# ================================================================== THE CRYPT
CRYPT_WALL = (74, 62, 84)
CRYPT_WALL_DK = (52, 42, 62)
PASTA = ['farfalle', 'fusilli', 'rigatoni', 'orecchiette']
SHAPES = ['fusilli', 'orecchiette', 'farfalle', 'rigatoni']   # what the wall shows, left to right


def stone_blocks(d, box, base, rnd, bw=24, bh=12):
    x0, y0, x1, y1 = box
    for row, y in enumerate(range(y0, y1, bh)):
        off = (row % 2) * bw // 2
        for x in range(x0 - off, x1, bw):
            c = shade(base, 1 + rnd.uniform(-0.08, 0.08))
            d.rectangle([max(x0, x), y, min(x1, x + bw - 2), min(y1, y + bh - 2)], fill=rgba(c))
            d.line([(max(x0, x), y), (min(x1, x + bw - 2), y)], fill=rgba(shade(c, 1.15)))


def candle(d, x, y, h=10):
    d.rectangle([x - 2, y - h, x + 2, y], fill=rgba((240, 232, 210)))
    d.ellipse([x - 2, y - h - 7, x + 2, y - h - 1], fill=rgba((255, 200, 80)))
    d.point((x, y - h - 5), fill=rgba((255, 250, 220)))


def pasta_icon(kind, size=26, col=(246, 214, 130), uv=False):
    im = canvas(size, size)
    d = ImageDraw.Draw(im)
    c = rgba(col)
    dk = rgba(shade(col, 0.72))
    m = size // 2
    if kind == 'farfalle':
        d.polygon([(3, 5), (m, m - 2), (size - 4, 5), (size - 4, size - 6), (m, m + 2), (3, size - 6)], fill=c)
        d.rectangle([m - 2, m - 4, m + 2, m + 4], fill=dk)
        for x in (5, size - 6):
            d.line([(x, 7), (x, size - 8)], fill=dk)
    elif kind == 'fusilli':
        for i in range(6):
            y = 3 + i * (size - 6) / 6
            d.arc([4, y, size - 5, y + 7], 200 if i % 2 else 20, 340 if i % 2 else 160, fill=c, width=3)
        d.line([(m, 3), (m, size - 3)], fill=dk)
    elif kind == 'rigatoni':
        d.rectangle([6, 5, size - 7, size - 6], fill=c)
        d.ellipse([size - 10, 5, size - 4, size - 6], fill=dk)
        for x in range(8, size - 8, 3):
            d.line([(x, 6), (x, size - 7)], fill=dk)
    else:   # orecchiette: little ears
        d.ellipse([4, 6, size - 5, size - 5], fill=c)
        d.ellipse([8, 9, size - 9, size - 8], fill=dk)
        d.arc([6, 7, size - 7, size - 6], 200, 320, fill=rgba(shade(col, 1.2)))
    return outline(im)


def crypt():
    sc = Scene('crypt')
    d = sc.d
    rnd = sc.rnd
    shell(sc, CRYPT_WALL, CRYPT_WALL_DK, (62, 54, 70), (48, 40, 56), (40, 30, 44), plank=False)
    stone_blocks(d, (BACK_L, 10, BACK_R, BACK_B - 1), CRYPT_WALL, rnd)
    # flagstone floor
    for y in range(BACK_B, VIEW_H, 1):
        t = (y - BACK_B) / (VIEW_H - BACK_B)
        if int((y - BACK_B) ** 0.9) % int(6 + t * 12) == 0:
            d.line([(floor_x_left(y), y), (floor_x_right(y), y)], fill=rgba((44, 36, 52)))
    for i in range(-8, 9):
        d.line([(W / 2 + i * 40, BACK_B), (W / 2 + i * 84, VIEW_H)], fill=rgba((48, 40, 58)))
    # side walls in stone
    for y in range(12, VIEW_H, 14):
        d.line([(0, y), (floor_x_left(max(y, BACK_B)) if y > BACK_B else BACK_L, y)], fill=rgba((44, 36, 52)))
        d.line([(W, y), (floor_x_right(max(y, BACK_B)) if y > BACK_B else BACK_R, y)], fill=rgba((44, 36, 52)))

    # ---------- archway back to the Nave (back left), warm light
    ax0, ax1, ay0 = 104, 166, 30
    d.rectangle([ax0 - 5, ay0 + 26, ax1 + 5, BACK_B], fill=rgba((110, 96, 120)))
    d.pieslice([ax0 - 5, ay0 - 5, ax1 + 5, ay0 + 57], 180, 360, fill=rgba((110, 96, 120)))
    vgrad(d, (ax0, ay0 + 26, ax1, BACK_B - 1), (230, 190, 120), (250, 214, 150))
    d.pieslice([ax0, ay0, ax1, ay0 + 52], 180, 360, fill=rgba((226, 186, 116)))
    for i in range(5):
        d.line([(ax0 + 4, 140 - i * 9), (ax1 - 4, 140 - i * 9)], fill=rgba((200, 150, 90)))
    sc.hotspot('hArch', 'archway', (135, 158),
               [('rect', [ax0, ay0 + 26, ax1, BACK_B]), ('poly', [(ax0, ay0 + 28), (ax0 + 14, ay0 + 6), (ax1 - 14, ay0 + 6), (ax1, ay0 + 28)])])

    # ---------- the Flying Spaghetti Monster, crocheted out of yarn, hanging
    fx, fy = 236, 46
    yarn = canvas(W, H)
    yd = ImageDraw.Draw(yarn)
    for k in range(14):
        a = math.pi * (0.05 + 0.9 * k / 13)
        pts = [(fx + math.cos(a) * t * 70 + 6 * math.sin(t * 8 + k), fy + 8 + math.sin(a) * t * 60) for t in
               [i / 16 for i in range(17)]]
        yd.line(pts, fill=rgba(rnd.choice([(250, 222, 140), (236, 200, 110)])), width=2)
    yd.ellipse([fx - 20, fy - 12, fx + 20, fy + 14], fill=rgba((250, 222, 140)))
    for mx in (fx - 11, fx + 11):
        meatball(yd, mx, fy + 2, 8)
    for ex in (fx - 9, fx + 9):
        yd.line([(ex, fy - 10), (ex + (ex - fx), fy - 28)], fill=rgba((250, 222, 140)), width=2)
        yd.ellipse([ex + (ex - fx) - 5, fy - 34, ex + (ex - fx) + 5, fy - 24], fill=rgba((255, 255, 255)))
        yd.ellipse([ex + (ex - fx) - 2, fy - 31, ex + (ex - fx) + 2, fy - 27], fill=rgba((20, 20, 30)))
    yd.line([(fx, 0), (fx, fy - 12)], fill=rgba((180, 180, 180)))
    sc.bg.alpha_composite(outline(yarn, (60, 40, 30, 255)))
    sc.hotspot('hYarn', 'yarn monster', (236, 170), [('rect', [fx - 74, 0, fx + 74, 100])])

    # candles along the wainscot
    for x in (186, 284, 440, 450):
        d.rectangle([x - 6, 120, x + 6, 124], fill=rgba((90, 80, 70)))
        candle(d, x, 120)

    # ---------- Pasta Identification (back wall, centre right)
    bx0, by0, bx1, by1 = 268, 30, 462, 124
    wood(d, (bx0, by0, bx1, by1), (110, 30, 36), rnd)
    frame_box(d, (bx0, by0, bx1, by0 + 13), (70, 18, 22))
    text(d, ((bx0 + bx1) // 2, by0 + 7), 'PASTA IDENTIFICATION', 8, (250, 210, 90), anchor='mm')
    for i, kind in enumerate(SHAPES):
        px = bx0 + 10 + i * 46
        d.rectangle([px + 4, 52, px + 36, 84], fill=rgba((40, 14, 18)))
        sc.bg.alpha_composite(pasta_icon(kind, 28), (px + 6, 54))
        d.rectangle([px - 1, 90, px + 44, 103], fill=rgba((40, 14, 18)))
    sc.hotspot('hPastaWall', 'Pasta Identification', (365, 162), [('rect', [bx0, by0, bx1, by1])])

    def label_sprite(name, lit=False):
        im = canvas(44, 12)
        dd = ImageDraw.Draw(im)
        dd.rectangle([0, 0, 43, 11], fill=rgba((236, 226, 196) if not lit else (255, 236, 140)))
        n = name.upper()
        size = 7 if len(n) <= 8 else 6
        text(dd, (22, 6), n, size, (60, 30, 30), anchor='mm')
        return im

    for i in range(4):
        sprites = {('n%d' % j): label_sprite(PASTA[j]) for j in range(4)}
        sprites.update({('l%d' % j): label_sprite(PASTA[j], lit=True) for j in range(4)})
        sc.obj('oLabel%d' % (i + 1), 'label', sprites, bx0 + 9 + i * 46, 102, baseline=1, state='n%d' % (i % 4))
    worthy = canvas(52, 12)
    wdd = ImageDraw.Draw(worthy)
    wdd.rectangle([0, 0, 51, 11], fill=rgba((255, 230, 110)))
    text(wdd, (26, 6), 'WORTHY', 8, (120, 30, 20), anchor='mm')
    worthy_glow = canvas(60, 20)
    worthy_glow.alpha_composite(worthy.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(3)), (4, 4))
    worthy_glow.alpha_composite(worthy, (4, 4))
    sc.obj('oWorthy', 'WORTHY sign', {'on': worthy_glow}, 335, 136, visible=False, baseline=1, clickable=False)
    sc.uv(lambda im, dd: glow_text(im, (365, 112), 'ASK THE COMPUTER', 8, (120, 255, 200)))

    # ---------- staff area curtain (back right corner)
    cx0, cx1 = 472, 538
    d.rectangle([cx0 - 4, 22, cx1 + 4, 26], fill=rgba((180, 150, 70)))
    d.rectangle([cx0, 26, cx1, BACK_B], fill=rgba((230, 196, 140)))       # warm staff room behind
    d.rectangle([cx0 + 10, 60, cx1 - 10, 100], fill=rgba((200, 200, 206)))   # a big stockpot on a stove
    d.ellipse([cx0 + 14, 50, cx1 - 14, 66], fill=rgba((150, 150, 160)))
    for i in range(4):
        d.arc([cx0 + 20 + i * 10, 30, cx0 + 30 + i * 10, 50], 90, 270, fill=rgba((250, 250, 250)))
    d.rectangle([cx0 + 6, 100, cx1 - 6, BACK_B], fill=rgba((90, 90, 96)))

    def curtain_sprite(opened):
        im = canvas(cx1 - cx0 + 9, BACK_B - 26 + 1)
        dd = ImageDraw.Draw(im)
        w_, h_ = im.size
        red = (150, 24, 40)
        if not opened:
            dd.rectangle([0, 0, w_ - 1, h_ - 1], fill=rgba(red))
            for x in range(2, w_, 8):
                dd.line([(x, 0), (x + 2, h_ - 1)], fill=rgba(shade(red, 0.7)), width=2)
                dd.line([(x + 4, 0), (x + 5, h_ - 1)], fill=rgba(shade(red, 1.25)))
            dd.rectangle([w_ // 2 - 14, 40, w_ // 2 + 14, 52], fill=rgba((250, 236, 200)))
            text(dd, (w_ // 2, 46), 'STAFF', 8, (120, 20, 30), anchor='mm')
        else:
            for side in (0, 1):
                x0 = 0 if side == 0 else w_ - 14
                dd.rectangle([x0, 0, x0 + 13, h_ - 1], fill=rgba(red))
                for x in range(x0 + 2, x0 + 13, 5):
                    dd.line([(x, 0), (x + 1, h_ - 1)], fill=rgba(shade(red, 0.7)), width=2)
        return im

    sc.obj('oCurtain', 'curtain', {'closed': curtain_sprite(False), 'open': curtain_sprite(True)}, cx0 - 4, BACK_B,
           baseline=2)
    sc.hotspot('hStaff', 'staff area', (498, 160), [('rect', [cx0, 26, cx1, BACK_B])])

    # ---------- 3Button arcade cabinet (left wall): the Confessional
    def cabinet(dd, x0, y0, x1, y1, body, screen, marquee, label, lsize=7):
        dd.polygon([(x0, y0 + 10), (x1, y0), (x1, y1), (x0, y1 + 6)], fill=rgba(body))
        dd.polygon([(x0 + 4, y0 + 13), (x1 - 4, y0 + 5), (x1 - 4, y0 + 20), (x0 + 4, y0 + 28)], fill=rgba(marquee))
        text(dd, ((x0 + x1) // 2, y0 + 17), label, lsize, (30, 20, 30), anchor='mm')
        dd.polygon([(x0 + 6, y0 + 34), (x1 - 6, y0 + 26), (x1 - 6, y0 + 66), (x0 + 6, y0 + 72)], fill=rgba((16, 14, 20)))
        dd.polygon([(x0 + 9, y0 + 37), (x1 - 9, y0 + 30), (x1 - 9, y0 + 62), (x0 + 9, y0 + 68)], fill=rgba(screen))
        dd.polygon([(x0, y0 + 78), (x1 + 6, y0 + 70), (x1 + 6, y0 + 82), (x0, y0 + 90)], fill=rgba(shade(body, 1.2)))

    cabinet(d, 18, 92, 82, 232, (60, 40, 110), (40, 20, 30), (240, 200, 90), 'CONFESS')
    text(d, (50, 145), 'SINS?', 8, (255, 90, 90), anchor='mm')
    for i, c in enumerate([(230, 50, 50), (60, 200, 80), (60, 120, 240)]):
        d.ellipse([28 + i * 14, 175 - i * 2, 36 + i * 14, 181 - i * 2], fill=rgba(c))
    sc.hotspot('h3Button', '3Button cabinet', (106, 194), [('poly', [(18, 102), (88, 88), (88, 232), (18, 238)])])
    token = canvas(10, 10)
    tdd = ImageDraw.Draw(token)
    tdd.ellipse([0, 0, 9, 9], fill=rgba((220, 180, 70)))
    tdd.ellipse([2, 2, 7, 7], fill=rgba((250, 220, 120)))
    tdd.point((4, 4), fill=rgba((160, 120, 40)))
    sc.obj('oToken', 'arcade token', {'on': outline(token)}, 52, 213, visible=False, baseline=240)

    # ---------- Trackball cabinet (right wall)
    cabinet(d, 562, 64, 626, 214, (40, 90, 80), (20, 40, 60), (120, 220, 200), 'TRACKBALL', lsize=6)
    d.ellipse([582, 148, 600, 160], fill=rgba((140, 64, 40)))       # it's a meatball
    d.point((587, 151), fill=rgba((200, 120, 90)))
    sc.hotspot('hTrackball', 'Trackball cabinet', (536, 202), [('poly', [(560, 70), (634, 60), (634, 214), (560, 224)])])

    # ---------- the Classic Computer on a desk (centre left)
    d.polygon([(176, 194), (264, 188), (270, 200), (172, 208)], fill=rgba((96, 66, 50)))
    d.polygon([(172, 208), (270, 200), (270, 206), (172, 214)], fill=rgba((70, 48, 36)))
    for lx, ly in ((176, 214), (262, 206)):
        d.rectangle([lx, ly, lx + 4, ly + 20], fill=rgba((60, 40, 30)))
    d.rectangle([196, 150, 244, 190], fill=rgba((206, 196, 170)))
    d.rectangle([200, 154, 240, 180], fill=rgba((20, 26, 22)))
    for i in range(4):
        d.line([(204, 158 + i * 5), (204 + [28, 20, 30, 12][i], 158 + i * 5)], fill=rgba((90, 230, 110)))
    d.rectangle([192, 190, 248, 196], fill=rgba((190, 180, 156)))
    d.polygon([(196, 198), (244, 196), (248, 202), (194, 204)], fill=rgba((180, 170, 146)))     # keyboard
    sc.hotspot('hComputer', 'Classic Computer', (222, 240), [('rect', [190, 146, 250, 206])])
    sc.walkbehind('poly', [(170, 186), (272, 186), (272, 236), (170, 236)], 214)

    # ---------- Rex Seat (front left): a sit-down cabinet with the T. rex game
    rs = canvas(W, H)
    rd = ImageDraw.Draw(rs)
    rd.polygon([(60, 214), (150, 206), (150, 284), (60, 288)], fill=rgba((150, 34, 40)))        # body
    rd.polygon([(64, 218), (146, 211), (146, 222), (64, 230)], fill=rgba((250, 210, 90)))
    text(rd, (105, 220), 'T. REX', 8, (60, 20, 20), anchor='mm')
    rd.polygon([(70, 232), (140, 226), (140, 262), (70, 268)], fill=rgba((16, 14, 20)))
    rd.polygon([(74, 236), (136, 230), (136, 258), (74, 264)], fill=rgba((40, 90, 50)))
    # pixel dinosaur on the screen
    for (x, y) in [(96, 250), (98, 248), (100, 248), (102, 246), (104, 244), (106, 244), (108, 246), (100, 252), (102, 252), (98, 254), (104, 254)]:
        rd.rectangle([x, y, x + 1, y + 1], fill=rgba((200, 250, 160)))
    rd.rectangle([118, 252, 122, 258], fill=rgba((80, 200, 80)))                               # cactus
    rd.polygon([(150, 240), (196, 244), (196, 288), (150, 288)], fill=rgba((40, 36, 44)))       # bench seat
    rd.polygon([(152, 236), (190, 240), (196, 248), (150, 246)], fill=rgba((90, 30, 34)))
    sc.bg.alpha_composite(rs)
    sc.hotspot('hRex', 'Rex Seat', (216, 272), [('poly', [(60, 206), (150, 206), (196, 244), (196, 288), (60, 288)])])

    # ---------- the Pope Seat (front right): a throne with a crank and a button
    ps0, ps1 = 456, 556

    def seat_sprite(credit=False, seated=False):
        im = canvas(ps1 - ps0 + 30, 150)
        dd = ImageDraw.Draw(im)
        gold = (220, 180, 70)
        red = (150, 24, 40)
        # tall back with a pasta halo
        dd.polygon([(14, 30), (86, 30), (82, 104), (18, 104)], fill=rgba(red))
        dd.pieslice([14, 0, 86, 60], 180, 360, fill=rgba(red))
        dd.arc([18, 4, 82, 56], 180, 360, fill=rgba(gold), width=3)
        for k in range(9):
            a = math.pi + math.pi * k / 8
            dd.line([(50 + 30 * math.cos(a), 30 + 26 * math.sin(a)), (50 + 38 * math.cos(a), 30 + 34 * math.sin(a))],
                    fill=rgba((250, 222, 140)), width=2)
        # seat and arms
        dd.rectangle([8, 96, 92, 112], fill=rgba(shade(red, 0.8)))
        dd.rectangle([2, 80, 16, 120], fill=rgba(gold))
        dd.rectangle([84, 80, 98, 120], fill=rgba(gold))
        dd.ellipse([86, 74, 96, 84], fill=rgba((240, 40, 40)))                       # the big button
        dd.rectangle([10, 112, 90, 146], fill=rgba(shade(red, 0.65)))
        for x in (12, 84):
            dd.rectangle([x, 140, x + 6, 149], fill=rgba(gold))
        # coin door with credit light
        dd.rectangle([40, 120, 60, 140], fill=rgba((40, 30, 30)))
        dd.rectangle([47, 124, 53, 126], fill=rgba((20, 20, 20)))
        dd.ellipse([46, 130, 54, 138], fill=rgba((80, 250, 120) if credit else (60, 70, 60)))
        # crank on the right side
        dd.rectangle([98, 92, 104, 98], fill=rgba((150, 150, 160)))
        dd.line([(104, 95), (112, 95), (112, 82)], fill=rgba((170, 170, 180)), width=3)
        dd.ellipse([108, 76, 116, 84], fill=rgba((90, 50, 30)))
        if seated:
            import guest_sprite
            g = guest_sprite.guest_seated()
            im.alpha_composite(g, (26, 40))
        return outline(im)

    sc.obj('oSeat', 'Pope Seat', {'empty': seat_sprite(), 'credit': seat_sprite(credit=True),
                                  'seated': seat_sprite(credit=True, seated=True)},
           ps0 - 6, 286, baseline=270)
    # the pope hat: a lasagna mitre hung on a pulley rope
    hat = canvas(34, 40)
    hd = ImageDraw.Draw(hat)
    hd.line([(17, 0), (17, 8)], fill=rgba((200, 190, 170)))
    hd.polygon([(4, 38), (17, 8), (30, 38)], fill=rgba((250, 214, 130)))
    for y in range(14, 38, 5):                                                   # lasagna ripples
        hd.line([(17 - (y - 8) * 0.43, y), (17 + (y - 8) * 0.43, y)], fill=rgba((214, 160, 80)))
    hd.polygon([(4, 38), (30, 38), (30, 34), (4, 34)], fill=rgba((200, 40, 40)))   # sauce band
    sc.obj('oHat', 'pasta pope hat', {'on': outline(hat)}, 489, 70, baseline=271)
    d.line([(506, 0), (506, 30)], fill=rgba((200, 190, 170)))
    d.ellipse([500, 22, 512, 34], fill=rgba((150, 150, 160)))
    sc.uv(lambda im, dd: glow_text(im, (352, 186), 'THE CRANK NEEDS', 8, (255, 160, 80)))
    sc.uv(lambda im, dd: glow_text(im, (352, 198), 'A SECOND PAIR OF HANDS', 8, (255, 160, 80)))
    sc.uv(lambda im, dd: glow_text(im, (230, 120), 'THE SAUCE IS WITHIN', 9, (120, 255, 160)))
    # glowing tentacle doodles on the side walls
    for side in (0, 1):
        def tentacle(im, dd, side=side):
            x0 = 40 if side == 0 else 600
            sgn = 1 if side == 0 else -1
            pts = [(x0 + sgn * 10 * math.sin(t * 1.3) * (1 - t / 12), 60 + t * 9) for t in [k / 2 for k in range(24)]]
            glow_lines(im, pts, (255, 120, 220), 2)
            for k in range(2, 20, 4):
                px, py = pts[k]
                glow_lines(im, [(px - 2, py), (px + 2, py)], (255, 200, 240), 1)
        sc.uv(tentacle)

    # ---------- walkable floor
    walkable_floor(sc)
    wd = sc.wd
    wd.polygon([(0, 150), (96, 150), (96, 246), (0, 252)], fill=0)               # 3Button
    wd.polygon([(168, 186), (276, 186), (276, 226), (168, 230)], fill=0)        # desk
    wd.polygon([(50, 200), (204, 200), (204, 288), (50, 288)], fill=0)          # rex seat
    wd.polygon([(440, 214), (640, 214), (640, 288), (440, 288)], fill=0)        # pope seat & trackball corner
    wd.polygon([(548, 150), (640, 150), (640, 226), (548, 226)], fill=0)        # trackball
    return sc


# ================================================================== TITLE
def title():
    sc = Scene('title')
    d = sc.d
    rnd = sc.rnd
    vgrad(d, (0, 0, W - 1, VIEW_H - 1), (30, 16, 40), (90, 30, 50))
    # rays
    for k in range(18):
        a = math.pi * k / 17
        d.polygon([(320, 300), (320 + 700 * math.cos(a - 0.03), 300 - 700 * math.sin(a - 0.03)),
                   (320 + 700 * math.cos(a + 0.03), 300 - 700 * math.sin(a + 0.03))],
                  fill=rgba((120, 50, 70) if k % 2 else (100, 40, 64)))
    # the noodly one, big, in stained-glass colours
    mon = canvas(W, H)
    md = ImageDraw.Draw(mon)
    cx, cy = 320, 150
    for k in range(13):
        a = math.pi * (0.05 + 0.9 * k / 12)
        pts = [(cx + math.cos(a + 0.5 * math.sin(t * 4 + k)) * t * 190, cy + 16 + math.sin(a) * t * 150)
               for t in [i / 24 for i in range(25)]]
        md.line(pts, fill=rgba((250, 222, 140)), width=5)
    md.ellipse([cx - 46, cy - 26, cx + 46, cy + 36], fill=rgba((250, 222, 140)))
    for mx in (cx - 24, cx + 24):
        meatball(md, mx, cy + 6, 18)
    for ex in (cx - 18, cx + 18):
        tx = ex + (ex - cx) * 1.2
        md.line([(ex, cy - 22), (tx, cy - 70)], fill=rgba((250, 222, 140)), width=4)
        md.ellipse([tx - 12, cy - 86, tx + 12, cy - 62], fill=rgba((255, 255, 255)))
        md.ellipse([tx - 5, cy - 78, tx + 5, cy - 68], fill=rgba((20, 20, 30)))
    sc.bg.alpha_composite(outline(mon, (60, 30, 30, 255), 2))
    # lettering
    lay = canvas(W, H)
    ld = ImageDraw.Draw(lay)
    text(ld, (320, 22), 'HOTEL PARADISO', 16, (250, 230, 170), anchor='mm')
    big = 'SACRA PASTA'
    text(ld, (320, 238), big, 40, (255, 210, 90), anchor='mm')
    text(ld, (320, 272), 'a sequel to Room 714', 11, (240, 200, 210), anchor='mm')
    shadow = lay.copy()
    shadow = Image.eval(shadow, lambda v: v)
    sh = canvas(W, H)
    sh.paste((50, 20, 20, 255), (0, 0), lay.getchannel('A'))
    sc.bg.alpha_composite(sh.filter(ImageFilter.MaxFilter(5)), (2, 3))
    sc.bg.alpha_composite(lay)
    d.rectangle([0, VIEW_H, W, H], fill=(0, 0, 0, 255))
    return sc


def ending_plate():
    """A heaped plate of spaghetti, for the finale."""
    im = canvas(60, 34)
    d = ImageDraw.Draw(im)
    d.ellipse([0, 14, 59, 33], fill=rgba((240, 240, 246)))
    d.ellipse([6, 17, 53, 30], fill=rgba((220, 220, 230)))
    rnd = random.Random(7)
    for _ in range(60):
        x = rnd.uniform(12, 48)
        y = rnd.uniform(6, 24)
        d.arc([x - 5, y - 3, x + 5, y + 3], rnd.uniform(0, 360), rnd.uniform(0, 360) + 180, fill=rgba((250, 222, 140)))
    d.ellipse([18, 10, 42, 22], fill=rgba((200, 40, 30)))
    for mx, my in ((24, 12), (34, 14), (29, 8)):
        meatball(d, mx, my, 4)
    return outline(im)
