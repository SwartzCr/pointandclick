"""The Nave on the Nano Banana room (art_src/nave-nb/).

base.jpg is the room (1536x688, shrunk here to 640x288) with every puzzle
piece in its starting state; numbered variants are the same room with one
thing changed, and the changed part is cut out as that object's other state.
Pieces no variant covers yet come from the Muse set (art_src/nave-vga/),
keyed, warped into place and snapped to this room's palette. Object and
hotspot names and order match the other Nave builders.
"""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance

from art_common import canvas, rgba, text, CLEAR
from art_rooms import Scene, glow_text, W, H, VIEW_H, WORDS, ANSWER, TILES, TILE_NAMES, BUTTONS, BUTTON_UV
from nave_painted import uv_of, glow_layer
import nave_muse as NM
from nave_muse import keyed, fit, warp, tiny, tiny_width

HERE = os.path.dirname(os.path.abspath(__file__))
NB = os.path.join(HERE, '..', 'art_src', 'nave-nb')
INK = (46, 30, 24)


def _load(name):
    im = Image.open(os.path.join(NB, name)).convert('RGB')
    im = im.resize((W, VIEW_H), Image.LANCZOS)
    return im.filter(ImageFilter.UnsharpMask(radius=1.0, percent=70, threshold=2))


HR = '01-archway-closed-hr.jpg'      # the same room, archway closed, at 6144x2752
_rooms = {}


def room_image(name):
    if os.environ.get('NAVE_TEST') and name in ('base.jpg', '01-archway-closed.jpg'):
        # a trial room: shown as it is, with no puzzle pieces cut from it
        return Image.open(os.environ['NAVE_TEST']).convert('RGB').resize((W, VIEW_H), Image.LANCZOS).filter(
            ImageFilter.UnsharpMask(radius=1.0, percent=70, threshold=2))
    """The room at 640x288. When the high-resolution closed-arch picture is there,
    everything comes from it (crisper), except the open archway itself, which only
    the original base shows; the '1.' label in its corner is painted out."""
    if name in _rooms:
        return _rooms[name].copy()
    if not os.path.exists(os.path.join(NB, HR)):
        _rooms[name] = _load(name)
        return _rooms[name].copy()
    hr = _load(HR)
    # paint out the label in the bottom-left corner with the floor next to it
    hr.paste(hr.crop((22, 262, 40, 288)), (0, 262))
    if name == '01-archway-closed.jpg':
        _rooms[name] = hr
    elif name == 'base.jpg':
        old_base, old_closed = _load('base.jpg'), _load('01-archway-closed.jpg')
        m = changed(old_base, old_closed, ARCH_BOX).filter(ImageFilter.MaxFilter(5))
        full = Image.new('L', (W, VIEW_H), 0)
        full.paste(m, ARCH_BOX[:2])
        out = hr.copy()
        out.paste(old_base, (0, 0), full)
        _rooms[name] = out
    else:
        _rooms[name] = _load(name)
    return _rooms[name].copy()


_room_pal = None


def quantized(im):
    """Reduce to the room's 256-colour palette (made once from the base room)."""
    global _room_pal
    if _room_pal is None:
        _room_pal = room_image('base.jpg').quantize(256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
        p = Image.new('P', (1, 1))
        p.putpalette(_room_pal.getpalette())
        NM._pal = p                      # the Muse pieces snap to this palette too
    return im.convert('RGB').quantize(palette=NM.palette_image(), dither=Image.Dither.NONE).convert('RGB')


def changed(base, variant, box, thresh=70):
    """Mask of what a variant changed inside box (room pixels)."""
    a = np.asarray(base.crop(box)).astype(int)
    b = np.asarray(variant.crop(box)).astype(int)
    m = Image.fromarray(((np.abs(a - b).sum(-1) > thresh) * 255).astype(np.uint8))
    m = m.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.MinFilter(3))
    # fill holes so the cut-out is solid
    from scipy import ndimage
    return Image.fromarray((ndimage.binary_fill_holes(np.asarray(m) > 0) * 255).astype(np.uint8))


# ----------------------------------------------------------------- layout (640x288)
ARCH_BOX = (512, 60, 600, 222)                # where the closed-arch variant differs
WARDROBE = [(596, 66), (640, 52), (640, 288), (596, 286)]
BOX = (232, 150, 280, 190)
BTN_BOXES = [(237, 166, 248, 180), (248, 167, 261, 179), (259, 166, 273, 180)]
WINDOWS = [(374, 160, 394, 184), (410, 160, 430, 184), (446, 160, 466, 184), (483, 160, 503, 184)]
TILE_BOXES = [(411, 105, 429, 124), (430, 105, 448, 124), (450, 105, 467, 124), (469, 105, 487, 124)]
FORK_QUAD = [(240, 86), (277, 86), (277, 138), (240, 138)]
SCALES = [(545, 160), (612, 160), (612, 252), (545, 252)]


def nave():
    sc = Scene('nave')
    base = room_image('base.jpg')
    room_rgb = quantized(base)
    room = Image.new('RGBA', (W, H), (0, 0, 0, 255))
    room.paste(room_rgb, (0, 0))
    orig = room.copy()
    sc.bg = room
    sc.d = ImageDraw.Draw(room)
    to_pal = lambda im: (lambda q: (q.putalpha(im.getchannel('A').point(lambda v: 255 if v >= 128 else 0)), q)[1])(
        quantized(im).convert('RGBA'))

    # ---------- hotspots (later ones are drawn over earlier ones)
    sc.hotspot('hWallpaper', 'wallpaper strips', (420, 236), [('rect', [80, 40, 590, 208])])
    sc.hotspot('hSauce', 'Weird Sauce', (178, 246), [('rect', [82, 72, 148, 164])])
    sc.hotspot('hRedSauce', 'red dispenser', (178, 246), [('rect', [91, 96, 109, 130])])
    sc.hotspot('hGreenSauce', 'green dispenser', (178, 246), [('rect', [110, 96, 127, 130])])
    sc.hotspot('hYellowSauce', 'yellow dispenser', (178, 246), [('rect', [128, 96, 142, 130])])
    sc.hotspot('hBowl', 'sauce bowl', (178, 246), [('rect', [111, 146, 132, 162])])
    sc.hotspot('hGlutenous', 'painting "Glutenous Truth"', (200, 238), [('rect', [168, 78, 226, 140])])
    flat = [(290, 172), (290, 90), (300, 70), (315, 58), (330, 50), (345, 58), (360, 70), (370, 90), (370, 172)]
    sc.hotspot('hFlat', 'stained-glass flat', (370, 232), [('poly', flat)])
    sc.hotspot('hTimeline', 'timeline of ancient technology', (450, 234), [('rect', [408, 86, 500, 144])])
    arch = [(522, 212), (522, 110), (528, 96), (540, 87), (548, 84), (556, 87), (566, 96), (572, 110), (572, 212)]
    sc.hotspot('hArch', 'archway', (548, 220), [('poly', arch)])
    sc.hotspot('hTopology', 'sacred topology display', (450, 234), [])          # not in this room
    sc.hotspot('hCrochet', 'crocheted pasta display', (200, 238), [('rect', [168, 138, 226, 158])])
    sc.hotspot('hFirstTaste', 'painting "First Taste"', (100, 250), [('rect', [16, 12, 72, 98])])
    sc.hotspot('hDoor', 'door', (60, 272), [('rect', [12, 98, 76, 270])])
    sc.hotspot('hHandset', 'telephone handset', (180, 248), [('rect', [154, 156, 188, 180])])
    sod = [(96, 182), (150, 166), (218, 160), (218, 236), (96, 238)]
    sc.hotspot('hSodTable', 'sod table', (160, 248), [('poly', sod)])
    sc.hd.rectangle([154, 156, 188, 180], fill=[h[0] for h in sc.hotspots].index('hHandset') + 1)  # handset over the table
    sc.hotspot('hSculpture', 'spaghetti sculpture', (325, 232), [('rect', [302, 92, 348, 220])])
    sc.hotspot('hSpinner', 'paragraph spinner', (436, 236), [('rect', [358, 144, 516, 228])])
    sc.hotspot('hScales', 'scales of pasta', (535, 236), [('poly', SCALES)])

    # ---------- A1: the archway, closed by the variant with the arch filled in
    closed = room_image('01-archway-closed.jpg')
    if os.environ.get('NAVE_TEST'):
        closed = _load('01-archway-closed.jpg')
        base_for_arch = _load('base.jpg')
    else:
        base_for_arch = base
    m = changed(base_for_arch, closed, ARCH_BOX)
    piece = quantized(closed.crop(ARCH_BOX)).convert('RGBA')
    piece.putalpha(m)
    panel = piece.crop(m.getbbox())
    ax0, ay0 = ARCH_BOX[0] + m.getbbox()[0], ARCH_BOX[1] + m.getbbox()[1]
    panel_uv = uv_of(panel)
    lay = canvas(*panel.size)
    for k, wtxt in enumerate(('NOT', 'A', 'WALL')):
        text(ImageDraw.Draw(lay), (panel.width // 2, panel.height // 2 - 16 + k * 15), wtxt, 10, (255, 120, 220), anchor='mm')
    glow_layer(lay, panel_uv, 2)
    panel_uv.putalpha(panel.getchannel('A'))
    sc.obj('oArchPanel', 'wall', {'closed': panel, 'uv': panel_uv}, ax0, ay0 + panel.height, baseline=1)

    # ---------- A2: the wardrobe (open = Muse's open wardrobe warped onto its front)
    wx0, wy0 = min(p[0] for p in WARDROBE), min(p[1] for p in WARDROBE)
    wy1 = max(p[1] for p in WARDROBE)
    ward = orig.crop((wx0, wy0, W, wy1))
    opened, ox, oy = warp(keyed('A2-wardrobe-open-room-consistent.png'), WARDROBE)
    ward_open = ward.copy()
    ward_open.alpha_composite(to_pal(opened), (ox - wx0, oy - wy0))
    sc.obj('oWardrobe', 'wardrobe', {'closed': ward, 'open': ward_open}, wx0, wy1, baseline=200)
    beads = to_pal(fit(keyed('A7-rosary-beads.png'), 12, 30))
    sc.obj('oBeads', 'pasta rosary beads', {'on': beads}, 612, 130, visible=False, baseline=201)
    # the robes inside, cut from the open wardrobe so they can be pointed at
    for script, name, (x0, y0, x1, y1) in (('oRobe', 'purple robe', (623, 112, 630, 184)),
                                           ('oGoldRobe', 'gold robe', (612, 126, 623, 213))):
        sc.obj(script, name, {'on': ward_open.crop((x0 - wx0, y0 - wy0, x1 - wx0, y1 - wy0))},
               x0, y1, visible=False, baseline=202)

    # ---------- A3: pamphlets in the holder next to the telephone
    pam = to_pal(fit(keyed('A3-pamphlets.png'), 15, 17))
    sc.obj('oPamphlet', 'Spaghetti Theory pamphlet', {'on': pam}, 195, 170, baseline=1)

    # ---------- A4: the Paragraph Spinner's four windows, each showing a word
    def drum_sprite(i, word, uv=False, correct=False):
        x0, y0, x1, y1 = WINDOWS[i]
        im = orig.crop(WINDOWS[i])
        face = NM.palette_image()  # noqa: keep the palette loaded
        dd = ImageDraw.Draw(im)
        dd.rectangle([1, 7, im.width - 2, 16], fill=rgba((240, 226, 190)))
        dd.line([(1, 16), (im.width - 2, 16)], fill=rgba((170, 140, 100)))
        sp = 1 if tiny_width(word) <= im.width - 3 else 0
        if uv:
            im = uv_of(im)
            if correct:
                lay = canvas(*im.size)
                tiny(lay, im.width / 2, 11.5, word, (200, 255, 140), sp)
                glow_layer(lay, im, 2.0, 0.5, crisp=True)
            else:
                tiny(im, im.width / 2, 11.5, word, (120, 90, 160), sp)
        else:
            tiny(im, im.width / 2, 11.5, word, INK, sp)
        return im

    for i in range(4):
        sprites = {}
        for j, wtxt in enumerate(WORDS[i]):
            sprites['w%d' % j] = drum_sprite(i, wtxt)
            sprites['u%d' % j] = drum_sprite(i, wtxt, uv=True, correct=(j == ANSWER[i]))
        x0, y0, x1, y1 = WINDOWS[i]
        sc.obj('oDrum%d' % (i + 1), 'window', sprites, x0, y1, baseline=1,
               state={0: 'w0', 1: 'w0', 2: 'w1', 3: 'w2'}[i])
    sc.uv(lambda im, dd: glow_text(im, (436, 214), 'SPIN UNTIL IT GLOWS', 8, (180, 255, 120)))

    # ---------- A6: the puzzle box, its buttons and the golden rigatone
    bx0, by0, bx1, by1 = BOX
    box_closed = orig.crop(BOX)
    open_spr = to_pal(fit(keyed('A6-puzzle-box-open.png'), bx1 - bx0, 52))
    ch = max(52, by1 - by0)
    box_open = canvas(bx1 - bx0, ch)
    box_open.alpha_composite(open_spr, (0, ch - 52))
    box_closed_c = canvas(bx1 - bx0, ch)
    box_closed_c.alpha_composite(box_closed, (0, ch - (by1 - by0)))
    sc.obj('oBox', 'puzzle box', {'closed': box_closed_c, 'open': box_open,
                                   'uvclosed': uv_of(box_closed_c), 'uvopen': uv_of(box_open)},
           bx0, by1, baseline=1)

    def button_sprite(i, pressed=False, uv=None):
        b = BTN_BOXES[i]
        im = orig.crop(b)
        if pressed:
            dark = ImageEnhance.Brightness(im).enhance(0.6)
            base_ = orig.crop(b)
            base_.alpha_composite(dark, (1, 0))
            im = base_
        if uv:
            im = uv_of(im)          # no numbers any more: Khuc knows the order
        return im

    for i, kind in enumerate(BUTTONS):
        b = BTN_BOXES[i]
        sc.obj('oBtn%d' % (i + 1), '%s button' % kind,
               {'up': button_sprite(i), 'down': button_sprite(i, pressed=True), 'uv': button_sprite(i, uv=BUTTON_UV[i])},
               b[0], b[3], baseline=2)
    rig = to_pal(fit(keyed('A6-golden-rigatone.png'), 16, 10))
    sc.obj('oRigatone', 'golden rigatone', {'on': rig}, 248, 176, visible=False, baseline=2)

    # ---------- A5: Timeline tiles, the drawer and the pendant
    lit = keyed('A5-timeline-tiles-lit-room-consistent.png')
    q = lit.width / 4

    def tile_sprite(i, on):
        b = TILE_BOXES[i]
        t = orig.crop(b)
        if on:
            g = to_pal(fit(lit.crop((int(i * q), 0, int((i + 1) * q), lit.height)), b[2] - b[0], b[3] - b[1]))
            t.alpha_composite(g)
        return t

    for i, kind in enumerate(TILES):
        b = TILE_BOXES[i]
        sc.obj('oTile%d' % (i + 1), TILE_NAMES[kind], {'off': tile_sprite(i, False), 'on': tile_sprite(i, True)},
               b[0], b[3], baseline=1)
    drawer = to_pal(fit(keyed('A5-drawer-open.png'), 30, 16))
    sc.obj('oDrawer', 'drawer', {'open': drawer}, 435, 152, visible=False, baseline=2)
    pend = to_pal(fit(keyed('A5-uv-pendant.png'), 18, 8))
    sc.obj('oPendant', 'UV pendant', {'on': pend}, 441, 147, visible=False, baseline=3)

    # ---------- A8: the Spinning Fork, Muse's four frames warped onto the canvas
    frames = {}
    for k in range(4):
        f = Image.open(os.path.join(NM.ART, 'A8-spinning-fork-frame%d.png' % (k + 1))).convert('RGBA')
        inner = f.crop((int(f.width * 0.09), int(f.height * 0.08), int(f.width * 0.91), int(f.height * 0.92)))
        spr, fx, fy = warp(inner, FORK_QUAD)
        frames['f%d' % (2 * k)] = frames['f%d' % (2 * k + 1)] = to_pal(spr)
    sc.obj('oFork', 'painting "Spinning Fork"', frames, fx, fy + spr.height, baseline=1, state='f0')
    sc.fork_frames = ['f%d' % k for k in range(8)]

    # ---------- writing that only ultraviolet light shows
    sc.uv(lambda im, dd: glow_text(im, (256, 142), 'THE KEEPER KNOWS', 8, (255, 200, 120)))
    sc.uv(lambda im, dd: glow_text(im, (115, 172), 'SAUCE THY OFFERING', 8, (120, 255, 160)))
    sc.uv(lambda im, dd: glow_text(im, (330, 40), 'THE WORD IS SPUN', 9, (255, 240, 120)))
    sc.uv(lambda im, dd: glow_text(im, (157, 250), 'FIRST CAME THE STRING', 8, (120, 230, 255)))

    # ---------- walkable floor and walk-behinds
    if os.environ.get('NAVE_TEST'):
        blank = Image.new('RGBA', (1, 1), (0, 0, 0, 0))
        for o in sc.objects:
            o['sprites'] = {k: blank for k in o['sprites']}
        sc.wd.polygon([(40, 288), (150, 245), (640, 245), (640, 288)], fill=1)
        return sc
    sc.wd.polygon([(20, 288), (40, 272), (90, 244), (220, 240), (232, 224), (300, 224), (352, 226),
                   (358, 232), (516, 232), (540, 216), (570, 216), (560, 254), (612, 258), (628, 288)], fill=1)
    sc.walkbehind('poly', SCALES, 252)
    return sc
