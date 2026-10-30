"""The Nave on the third Nano Banana room (art_src/nave-nb/v3.png, 1536x688).

This room already has the tapestry, the empty Timeline tiles, the Paragraph
Spinner and an open archway painted in. Pieces it doesn't have (the puzzle box,
the tile pictures) are taken from the previous Nave (nave_nb) and placed here;
the rest (the closed archway, the ruined tapestry, the dug-up village, the
spinner windows) are stand-ins drawn here until real art arrives. Object and
hotspot names match the other Nave builders, so the script doesn't change.
"""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
from scipy import ndimage

from art_common import canvas, rgba, text
from art_rooms import Scene, glow_text, W, H, VIEW_H, WORDS, ANSWER, TILES, TILE_NAMES, BUTTONS, BUTTON_UV
from nave_painted import uv_of, glow_layer
import nave_muse as NM
from nave_muse import keyed, fit, warp, tiny, tiny_width
import nave_nb as OLD

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, '..', 'art_src', 'nave-nb', 'v3.png')
INK = (46, 30, 24)

# ----------------------------------------------------------------- layout (640x288)
ARCH_OPEN = (563, 100, 610, 262)                  # the dark opening inside the arch
TAPESTRY = (464, 68, 538, 200)                    # rod, cloth, fringe and the loose thread
VILLAGE = (112, 170, 224, 254)                    # the model village on its tray, and the dug-up earth
BOX_TABLE = [(16, 196), (44, 186), (80, 188), (80, 224), (92, 226), (92, 236), (88, 240), (88, 278), (80, 280),
             (64, 288), (4, 288), (4, 236), (16, 232)]
LEAFLETS = (224, 202, 264, 216)
BOX_AT = (268, 202)                               # bottom-left of the puzzle box on its little table
BOX_W = 32
SPIN = (414, 181, 493, 201)                       # the strip of four spinner windows
TILE_BOXES = [(370, 106, 391, 129), (395, 106, 417, 129), (421, 106, 442, 129), (447, 106, 468, 129)]
FORK_QUAD = [(73, 55), (100, 59), (100, 107), (73, 110)]
SCULPTURE = [(296, 268), (296, 196), (306, 160), (330, 150), (352, 160), (354, 268)]


SPIN_WORDS = {'F1': ('SOME', 'FORKS', 'LOOK', 'RAW'), 'F2': ('NO', 'BREAD', 'SEEM', 'BLAND'),
              'F3': ('ALL', 'PASTA', 'IS', 'HOLY'), 'F4': ('THE', 'SAUCE', 'FEEL', 'SOGGY')}
WINDOW_BOXES = [(426, 182, 441, 203), (442, 182, 457, 203), (459, 182, 474, 203), (475, 182, 491, 203)]


def tone(bgr, smooth=True):
    """Shared look for the room and its state pictures: smooth the generator's speckle at full
    size, shrink, then lift the shadows and brighten a little."""
    import cv2
    if smooth:
        bgr = cv2.bilateralFilter(bgr, 7, 28, 5)
    im = Image.fromarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)).resize((W, VIEW_H), Image.LANCZOS)
    a = np.asarray(im).astype(np.float32) / 255
    a = a ** 0.8                                   # lift the darks
    a = np.clip(a * 1.06, 0, 1)
    im = Image.fromarray((a * 255 + 0.5).astype(np.uint8))
    im = ImageEnhance.Color(im).enhance(1.05)
    return im.filter(ImageFilter.UnsharpMask(radius=0.8, percent=35, threshold=3))


def load():
    import cv2
    im = tone(cv2.imread(SRC))
    # paint out the generator's sparkle in the bottom-right corner with the floor beside it
    im.paste(im.crop((582, 258, 608, 288)), (608, 258))
    im.paste(im.crop((582, 258, 590, 288)), (632, 258))
    return im


# the three state pictures, each lined up on v3.png (affine fits from SIFT matches, 1552 -> 1536 wide)
VARIANTS = {
    'A': ('v3-A-fork-box-tiles.png', [[0.9913, 0.0007, -1.2742], [0.0002, 1.0012, 2.0247]]),   # fork painting, box table, lit tiles, open drawer, closed arch
    'B': ('v3-B-pendant.png', [[0.991, -0.0005, -0.6506], [-0.0001, 0.9998, 2.0197]]),          # the same with the pendant in the drawer
    'C': ('v3-C-ruins.png', [[0.99, -0.0002, -0.0663], [0.0, 0.9911, 2.599]]),                  # village dug up, tapestry ruined
    'D': ('v3-D-box-open-scales-empty.png', [[0.998, 0.0007, -6.6169], [-0.0004, 1.0084, 0.1291]]),  # box open and empty, scales empty
    'E': ('v3-E-rigatone.png', [[0.9984, 0.0, -6.8929], [-0.0002, 1.0076, 0.0263]]),             # box open, golden rigatone inside
    # the Paragraph Spinner's words, four to a picture (and no little table by the sculpture)
    'F1': ('v3-F1-some-forks-look-raw.png', [[0.9999, -0.0018, -6.9143], [0.0006, 1.0093, -0.7931]]),
    'F2': ('v3-F2-no-bread-seem-bland.png', [[0.9989, -0.0007, -7.0147], [0.0003, 1.0118, 0.6126]]),
    'F3': ('v3-F3-all-pasta-is-holy.png', [[0.998, -0.0013, -6.0896], [0.0007, 1.0095, -0.8741]]),
    'F4': ('v3-F4-the-sauce-feel-soggy.png', [[0.9989, 0.001, -7.4198], [-0.0005, 1.0103, -0.4606]]),
}
_var = {}


def sharp_variant(k):
    """A state picture shrunk without smoothing, for small lettering."""
    import cv2
    name, M = VARIANTS[k]
    im = cv2.imread(os.path.join(os.path.dirname(SRC), name))
    w = cv2.warpAffine(im, np.array(M, np.float32), (1536, 688), flags=cv2.INTER_LANCZOS4,
                       borderMode=cv2.BORDER_REPLICATE)
    return tone(w, smooth=False).convert('RGBA')


def variant(k, full_colour=False):
    """A state picture, lined up with the room and shrunk the same way (snapped to the room's
    palette unless full_colour)."""
    if full_colour:
        variant(k)
        return _var[k + '*'].copy()
    if k not in _var:
        import cv2
        name, M = VARIANTS[k]
        im = cv2.imread(os.path.join(os.path.dirname(SRC), name))
        w = cv2.warpAffine(im, np.array(M, np.float32), (1536, 688), flags=cv2.INTER_LANCZOS4,
                           borderMode=cv2.BORDER_REPLICATE)
        im = tone(w)
        _var[k + '*'] = im.convert('RGBA')
        _var[k] = quantized(im).convert('RGBA')
    return _var[k].copy()


def cut(base, var, box, thresh=60, grow=2):
    """What var changed inside box: (sprite with only the changed pixels, x0, y0) cropped to them."""
    a = np.asarray(base.crop(box).convert('RGB')).astype(int)
    b = np.asarray(var.crop(box).convert('RGB')).astype(int)
    m = np.abs(a - b).sum(-1) > thresh
    m = ndimage.binary_opening(m, iterations=1)
    m = ndimage.binary_dilation(m, iterations=grow)
    m = ndimage.binary_closing(m, iterations=2)
    m = ndimage.binary_fill_holes(m)
    spr = var.crop(box)
    spr.putalpha(Image.fromarray((m * 255).astype(np.uint8)))
    bb = spr.getbbox()
    return spr.crop(bb), box[0] + bb[0], box[1] + bb[1]


_pal = None


def quantized(im):
    """The game is 32-bit, so the room keeps its full colour (no 256-colour palette)."""
    return im.convert('RGB')


def _old_quantized(im):
    global _pal
    if _pal is None:
        q = load().quantize(256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
        _pal = Image.new('P', (1, 1))
        _pal.putpalette(q.getpalette())
        NM._pal = _pal
    return im.convert('RGB').quantize(palette=_pal, dither=Image.Dither.NONE).convert('RGB')


def to_pal(im):
    q = quantized(im).convert('RGBA')
    q.putalpha(im.getchannel('A').point(lambda v: 255 if v >= 128 else 0))
    return q


def scaled(im, f):
    return im.resize((max(1, round(im.width * f)), max(1, round(im.height * f))), Image.LANCZOS)


def old_room():
    """The previous Nave at 640x288, for the pieces this one lacks."""
    return OLD.room_image('base.jpg').convert('RGBA')


# ----------------------------------------------------------------- stand-ins
def arch_panel(orig):
    """Plaster filling the arch's dark opening."""
    box = ARCH_OPEN
    a = np.asarray(orig.crop(box).convert('RGB')).astype(int)
    lum = a.mean(-1)
    dark = (lum < 120) & (a[..., 2] >= a[..., 0] - 10)
    m = ndimage.binary_closing(dark, iterations=2)
    m = ndimage.binary_fill_holes(m)
    lab, n = ndimage.label(m)
    if n:
        sizes = ndimage.sum(m, lab, range(1, n + 1))
        m = lab == (1 + int(np.argmax(sizes)))
    m = ndimage.binary_dilation(m, iterations=1)
    rng = np.random.default_rng(11)
    base = np.array([214, 200, 172], float)
    h, w = m.shape
    shade = np.linspace(0.92, 0.8, h)[:, None, None]
    noise = rng.normal(0, 6, (h, w, 1))
    px = np.clip(base * shade + noise, 0, 255)
    im = Image.fromarray(np.dstack([px.astype(np.uint8), (m * 255).astype(np.uint8)]), 'RGBA')
    d = ImageDraw.Draw(im)
    ys, xs = np.nonzero(m)
    cx = int(xs.mean())
    for pts in (((cx - 6, 40), (cx - 2, 52), (cx - 5, 66)), ((cx + 8, 90), (cx + 4, 104), (cx + 9, 118))):
        d.line(pts, fill=(150, 136, 112, 255))
    im.putalpha(Image.fromarray((m * 255).astype(np.uint8)))
    bb = im.getbbox()
    return to_pal(im.crop(bb)), box[0] + bb[0], box[1] + bb[1]


def ruined_tapestry(orig):
    """The tapestry with its thread pulled: a ragged gap up the middle, threads dangling."""
    x0, y0, x1, y1 = TAPESTRY
    a = np.asarray(orig.crop(TAPESTRY)).copy()
    wall = np.asarray(orig.crop((x1 + 2, y0, x1 + 8, y1)))      # the wallpaper just right of it
    rng = np.random.default_rng(5)
    cx, top, bot = 31, 50, 96                                     # local: the middle of the cloth
    for y in range(top, bot + 1):
        half = int(2 + (y - top) * 0.22 + rng.integers(0, 3))
        for x in range(cx - half, cx + half + 1):
            a[y, x] = wall[y, (x - cx) % wall.shape[1]]
    # the loose thread under the fringe is gone (it's in the bellhop's pocket)
    tx, ty = 504 - x0, 167 - y0
    a[ty:, tx:tx + 9] = np.asarray(orig.crop((496, 167, 505, y1)))
    out = Image.fromarray(a, 'RGBA')
    d = ImageDraw.Draw(out)
    red, gold = (150, 40, 44, 255), (220, 176, 80, 255)
    for k in range(7):
        x = cx - 9 + k * 3 + int(rng.integers(-1, 2))
        y = top + 4 + int(rng.integers(0, 30))
        d.line([(x, y), (x + int(rng.integers(-2, 3)), y + 6 + int(rng.integers(0, 10)))], fill=red if k % 2 else gold)
    return out


def ruined_village(orig):
    vx0, vy0, vx1, vy1 = VILLAGE
    ruin = orig.crop(VILLAGE)
    rd = ImageDraw.Draw(ruin)
    dirt, dirt_hi, hole = (112, 74, 44, 255), (150, 104, 62, 255), (46, 28, 18, 255)
    for hx, hy, r in ((140, 200, 5), (156, 208, 4), (176, 196, 4), (196, 206, 5), (214, 198, 4), (168, 212, 3),
                      (186, 201, 3), (132, 210, 4)):
        x, y = hx - vx0, hy - vy0
        rd.ellipse([x - r - 2, y - r // 2 - 2, x + r + 2, y + r // 2 + 2], fill=dirt)
        rd.ellipse([x - r, y - r // 2, x + r, y + r // 2], fill=hole)
        rd.point([(x - r - 1, y - r // 2 - 2), (x + r, y - r // 2 - 1), (x + 1, y - r // 2 - 3)], fill=dirt_hi)
    for hx, hy, w, h, roof in ((150, 204, 5, 3, (170, 50, 40, 255)), (205, 199, 4, 3, (150, 60, 40, 255)),
                               (182, 208, 5, 3, (170, 50, 40, 255)), (222, 206, 4, 2, (150, 60, 40, 255))):
        x, y = hx - vx0, hy - vy0
        rd.rectangle([x, y, x + w, y + h], fill=(230, 226, 214, 255))
        rd.line([(x, y + h), (x + w, y + h)], fill=(140, 130, 120, 255))
        rd.polygon([(x + w + 2, y - 1), (x + w + 5, y + 1), (x + w + 3, y + 3)], fill=roof)
    return ruin


def no_leaflets(orig):
    """The table top with the leaflets gone: the wood just left of them, carried across."""
    x0, y0, x1, y1 = LEAFLETS
    col = orig.crop((x0 - 3, y0, x0 - 1, y1))
    patch = Image.new('RGBA', (x1 - x0, y1 - y0))
    for k in range(0, x1 - x0, 2):
        patch.paste(col, (k, 0))
    return patch


# ----------------------------------------------------------------- the room
def nave():
    sc = Scene('nave')
    room_rgb = quantized(load())
    room = Image.new('RGBA', (W, H), (0, 0, 0, 255))
    room.paste(room_rgb, (0, 0))
    orig = room.copy()
    old = old_room()

    A, B, C = variant('A'), variant('B'), variant('C')
    # the leaflets live on as the pamphlet object; the table under them is bare (from A)
    pam = orig.crop(LEAFLETS)
    room.paste(A.crop(LEAFLETS), LEAFLETS[:2])
    # Chuk's little table by the door, with his puzzle box on it (from A), painted into the room
    m = Image.new('L', A.size, 0)
    ImageDraw.Draw(m).polygon(BOX_TABLE, fill=255)
    room.paste(A, (0, 0), m)
    # the little empty table by the sculpture goes (the F pictures don't have it)
    TB = (258, 186, 314, 252)
    fm = Image.new('L', A.size, 0)
    ImageDraw.Draw(fm).rectangle([TB[0] + 3, TB[1] + 3, TB[2] - 1, TB[3] - 3], fill=255)
    fm = fm.filter(ImageFilter.GaussianBlur(2))
    room.paste(variant('F1'), (0, 0), fm)
    orig_with_table = room.copy()
    sc.bg = room
    sc.d = ImageDraw.Draw(room)

    # ---------- hotspots (later ones are drawn over earlier ones)
    F = 262                                        # where people stand: the front of the floor
    sc.hotspot('hWallpaper', 'wallpaper strips', (420, F), [('rect', [0, 30, 640, 244])])
    sc.hotspot('hSauce', 'Weird Sauce', (222, F), [('rect', [140, 82, 225, 171])])
    sc.hotspot('hRedSauce', 'red dispenser', (222, F), [('rect', [149, 99, 166, 131])])
    sc.hotspot('hGreenSauce', 'green dispenser', (222, F), [('rect', [171, 99, 188, 131])])
    sc.hotspot('hYellowSauce', 'yellow dispenser', (222, F), [('rect', [194, 99, 211, 131])])
    sc.hotspot('hBowl', 'sauce bowl', (222, F), [('rect', [165, 151, 195, 168])])
    sc.hotspot('hGlutenous', 'painting "Glutenous Truth"', (256, F), [('rect', [233, 90, 278, 129])])
    flat = [(287, 172), (287, 100), (295, 82), (308, 70), (322, 65), (336, 70), (349, 82), (357, 100), (357, 172)]
    sc.hotspot('hFlat', 'stained-glass flat', (322, F), [('poly', flat)])
    sc.hotspot('hTimeline', 'timeline of ancient technology', (418, F), [('rect', [366, 82, 468, 149])])
    arch = [(560, 262), (560, 118), (566, 104), (576, 96), (586, 94), (597, 98), (607, 108), (613, 122), (613, 262)]
    sc.hotspot('hArch', 'archway', (586, 266), [('poly', arch)])
    sc.hotspot('hTopology', 'sacred topology display', (450, F), [])          # not in this room
    sc.hotspot('hCrochet', 'crocheted pasta display', (256, F), [('rect', [229, 129, 283, 165])])
    sc.hotspot('hFirstTaste', 'painting "First Taste"', (90, F), [('rect', [13, 41, 58, 111])])
    sc.hotspot('hDoor', 'door', (112, 266), [('rect', [50, 116, 107, 258])])
    sod = [(122, 182), (232, 182), (268, 196), (268, 244), (122, 244)]
    sc.hotspot('hSodTable', 'sod table', (190, F), [('poly', sod)])
    sc.hotspot('hHandset', 'telephone handset', (250, F), [('rect', [229, 175, 271, 201])])
    sc.hotspot('hSculpture', 'spaghetti sculpture', (325, 274), [('poly', SCULPTURE)])
    sc.hotspot('hSpinner', 'paragraph spinner', (453, F), [('rect', [412, 164, 500, 244])])
    sc.hotspot('hScales', 'scales of pasta', (382, F), [('rect', [352, 160, 410, 244])])

    # ---------- A1: the archway, plastered over until you're ordained (from A)
    panel, ax0, ay0 = cut(orig, A, (538, 80, 620, 262))
    panel_uv = uv_of(panel)
    lay = canvas(*panel.size)
    for k, wtxt in enumerate(('NOT', 'A', 'WALL')):
        text(ImageDraw.Draw(lay), (panel.width // 2, panel.height // 2 - 16 + k * 15), wtxt, 10, (255, 120, 220), anchor='mm')
    glow_layer(lay, panel_uv, 2)
    panel_uv.putalpha(panel.getchannel('A'))
    sc.obj('oArchPanel', 'wall', {'closed': panel, 'uv': panel_uv}, ax0, ay0 + panel.height, baseline=1)

    # ---------- A2: the tapestry (in the painting), and its ruin (from C)
    tx0, ty0, tx1, ty1 = TAPESTRY
    rag, rx, ry = cut(orig, C, TAPESTRY)
    ruined = orig.crop(TAPESTRY)
    ruined.alpha_composite(rag, (rx - tx0, ry - ty0))
    sc.obj('oTapestry', 'tapestry', {'closed': orig.crop(TAPESTRY), 'ruined': ruined}, tx0, ty1, baseline=1)
    beads = to_pal(fit(keyed('A7-rosary-beads.png'), 12, 30))
    sc.obj('oBeads', 'pasta rosary beads', {'on': beads}, 500, 140, visible=False, baseline=2)

    # ---------- the tiny village after the whip-it dig (from C), dirt on the floor and all
    ruin, vx, vy = cut(orig, C, VILLAGE)
    sc.obj('oRuins', 'tiny village', {'on': ruin, 'uv': uv_of(ruin)}, vx, vy + ruin.height,
           visible=False, baseline=1, clickable=False)

    # ---------- A3: the pamphlets on the sod table
    sc.obj('oPamphlet', 'Spaghetti Theory pamphlet', {'on': pam}, LEAFLETS[0], LEAFLETS[3], baseline=1)

    # ---------- A4: the Paragraph Spinner's four windows, each word painted (from the F pictures)
    sharp = {k: sharp_variant(k) for k in SPIN_WORDS}

    def window(k, i, uv=False, correct=False):
        im = sharp[k].crop(WINDOW_BOXES[i])
        if not uv:
            return im
        u = uv_of(im)
        if correct:
            a = np.asarray(im.convert('L')).astype(int)
            inner = np.zeros_like(a, bool)
            inner[3:-3, 3:-3] = True
            ink = (a < a[inner].mean() - 35) & inner          # the dark letters on the pale barrel
            lay = canvas(*im.size)
            px = lay.load()
            for y, x in zip(*np.nonzero(ink)):
                px[int(x), int(y)] = (200, 255, 140, 255)
            glow_layer(lay, u, 2.0, 0.5, crisp=True)
        return u

    for i in range(4):
        sprites = {}
        for k, words in SPIN_WORDS.items():
            j = WORDS[i].index(words[i])
            sprites['w%d' % j] = window(k, i)
            sprites['u%d' % j] = window(k, i, uv=True, correct=(j == ANSWER[i]))
        b = WINDOW_BOXES[i]
        sc.obj('oDrum%d' % (i + 1), 'window', sprites, b[0], b[3], baseline=1,
               state={0: 'w0', 1: 'w0', 2: 'w1', 3: 'w2'}[i])
    sc.uv(lambda im, dd: glow_text(im, (453, 210), 'SPIN UNTIL IT GLOWS', 8, (180, 255, 120)))

    # ---------- A6: the puzzle box on Chuk's little table (from A), its buttons and the golden rigatone
    BOXR = (14, 184, 82, 242)
    bmask = Image.new('L', (W, H), 0)
    ImageDraw.Draw(bmask).polygon([(16, 196), (44, 186), (80, 188), (80, 232), (56, 240), (16, 236)], fill=255)
    box_closed = orig_with_table.crop(BOXR)
    box_closed.putalpha(bmask.crop(BOXR))
    D, E = variant('D'), variant('E')
    opened, ox, oy = cut(orig_with_table, D, (0, 140, 110, 248))
    x0, y0 = min(BOXR[0], ox), min(BOXR[1], oy)
    x1, y1 = max(BOXR[2], ox + opened.width), BOXR[3]
    box_closed_c = canvas(x1 - x0, y1 - y0)
    box_closed_c.alpha_composite(box_closed, (BOXR[0] - x0, BOXR[1] - y0))
    box_open = canvas(x1 - x0, y1 - y0)
    box_open.alpha_composite(opened.crop((0, 0, opened.width, min(opened.height, y1 - oy))), (ox - x0, oy - y0))
    sc.obj('oBox', 'puzzle box', {'closed': box_closed_c, 'open': box_open,
                                   'uvclosed': uv_of(box_closed_c), 'uvopen': uv_of(box_open)},
           x0, y1, baseline=2)
    BTNS = [(29, 193, 41, 201), (41, 187, 54, 196), (57, 188, 70, 198)]       # penne, bow, shell on the lid

    def button_sprite(i, pressed=False, uv=False):
        im = orig_with_table.crop(BTNS[i])
        if pressed:
            dark = ImageEnhance.Brightness(im).enhance(0.6)
            base_ = orig_with_table.crop((BTNS[i][0] - 1, BTNS[i][1], BTNS[i][2] - 1, BTNS[i][3]))
            base_.alpha_composite(dark, (1, 1))
            im = base_
        if uv:
            im = uv_of(im)
        return im

    for i, kind in enumerate(BUTTONS):
        b = BTNS[i]
        sc.obj('oBtn%d' % (i + 1), '%s button' % kind,
               {'up': button_sprite(i), 'down': button_sprite(i, pressed=True), 'uv': button_sprite(i, uv=True)},
               b[0], b[3], baseline=3)
    rig, rx, ry = cut(D, E, (0, 140, 110, 248), thresh=80)          # the rigatone, glowing, in the open box
    sc.obj('oRigatone', 'golden rigatone', {'on': rig}, rx, ry + rig.height, visible=False, baseline=3)
    # the Scales of Pasta with their macaroni gone (made into beads), from D
    emp, ex, ey = cut(orig, D, (350, 150, 416, 215))
    sc.obj('oScales', 'scales of pasta', {'empty': emp}, ex, ey + emp.height, visible=False, baseline=1, clickable=False)

    # ---------- A5: Timeline tiles (lit, from A; unlit = the same pictures, dimmed), drawer, pendant
    def tile_sprite(i, on):
        t = A.crop(TILE_BOXES[i])
        if not on:
            t = ImageEnhance.Color(t).enhance(0.45)
            t = ImageEnhance.Brightness(t).enhance(0.8)
            t = to_pal(t)
        return t

    for i, kind in enumerate(TILES):
        b = TILE_BOXES[i]
        sc.obj('oTile%d' % (i + 1), TILE_NAMES[kind], {'off': tile_sprite(i, False), 'on': tile_sprite(i, True)},
               b[0], b[3], baseline=1)
    DRAWER = (366, 130, 468, 158)
    sc.obj('oDrawer', 'drawer', {'open': A.crop(DRAWER)}, DRAWER[0], DRAWER[3], visible=False, baseline=2)
    pend, px, py = cut(A, B, (378, 132, 442, 158))
    full = variant('B', full_colour=True).crop((px, py, px + pend.width, py + pend.height))
    full.putalpha(pend.getchannel('A'))
    pend = full                                   # keep its purple: the room's palette has none
    sc.obj('oPendant', 'UV pendant', {'on': pend}, px, py + pend.height, visible=False, baseline=3)

    # ---------- A8: the Spinning Fork, in the empty frame by the door (from A)
    fork, fx, fy = cut(orig, A, (60, 40, 112, 120))
    frames = {('f%d' % k): fork for k in range(8)}
    sc.obj('oFork', 'painting "Spinning Fork"', frames, fx, fy + fork.height, baseline=1, state='f0')
    sc.fork_frames = ['f%d' % k for k in range(8)]

    # ---------- writing that only ultraviolet light shows
    sc.uv(lambda im, dd: glow_text(im, (258, 172), 'THE KEEPER KNOWS', 8, (255, 200, 120)))
    sc.uv(lambda im, dd: glow_text(im, (182, 77), 'SAUCE THY OFFERING', 8, (120, 255, 160)))
    sc.uv(lambda im, dd: glow_text(im, (322, 56), 'THE WORD IS SPUN', 9, (255, 240, 120)))
    sc.uv(lambda im, dd: glow_text(im, (190, 252), 'FIRST CAME THE STRING', 8, (120, 230, 255)))

    # ---------- walkable floor and walk-behinds
    sc.wd.polygon([(0, 288), (0, 274), (50, 264), (108, 252), (130, 248), (560, 248), (566, 264),
                   (612, 264), (640, 272), (640, 288)], fill=0)
    sc.wd.polygon([(96, 288), (96, 262), (108, 252), (130, 248), (290, 248), (290, 270),
                   (358, 270), (358, 248), (560, 248), (566, 264), (612, 264), (640, 272), (640, 288)], fill=1)
    sc.walkbehind('poly', SCULPTURE, 268)
    return sc
