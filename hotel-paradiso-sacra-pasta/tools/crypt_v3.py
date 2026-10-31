"""The Crypt on the newer pictures (art_src/crypt-nb/v2-*.png, 1376x768, all framed alike).

The room is picture A (the booth shut, the T. Rex skull, the empty board, the computer off,
the throne with an empty crank socket) shrunk to 640 wide and cropped to the 288-pixel view,
with the arcade cabinet's face from picture C. Everything that changes is cut from the three
pictures:
  A  booth shut, board empty, computer off, throne's socket
  B  booth half open, the board's drawer out with the crank in it, the computer on
  C  booth open, the board full of shapes, the cabinet's new face, the token on the floor
Object and hotspot names and order match crypt_nb, so the game script works with either.
"""
import os
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage

from art_common import canvas, rgba
from art_rooms import Scene, glow_text, W, H, VIEW_H
import topology

HERE = os.path.dirname(os.path.abspath(__file__))
DIR = os.path.join(HERE, '..', 'art_src', 'crypt-nb')
PICS = {'A': 'v2-A-confess-computer-trex-board-throne.png', 'B': 'v2-B-booth-open-drawer-trackball.png',
        'C': 'v2-C-booth-open-board-filled-meatball-coin.png',
        'D': 'v3-D-trex-highscore-insertcoin.png', 'E': 'v3-E-trex-off.png',
        'F': 'v3-F-trex-scores-toothgenius.png'}
REX_SCREEN = (222, 149, 254, 178)      # the T. Rex cabinet's screen
MEAT_SCREEN = (590, 114, 640, 192)     # the arcade cabinet's screen and controls
K = W / 1376                           # 1376 -> 640
TOP = 52                               # rows of the shrunk picture above the view

# ----------------------------------------------------------------- layout (room pixels)
BOOTH = (0, 38, 110, 288)
SLOTS = [(273, 59, 304, 89), (308, 59, 338, 89), (341, 59, 371, 89), (376, 59, 405, 89)]
DRAWER_SHUT = (302, 107, 376, 126)
DRAWER = (299, 103, 378, 138)          # the drawer pulled out (picture B)
SCREEN = (352, 131, 394, 172)          # the computer, on (picture B)
SEAT = (476, 96, 576, 260)
SOCKET = (551, 211)                    # the crank socket on the throne's side
HAT = (520, 10, 572, 88)               # the lasagna hat, lifted out of the picture
HAT_LOWERED_BOTTOM = 160               # where its bottom ends up, on the seated guest's head
COIN = (118, 266, 150, 288)            # the token CONFESS pays out (picture C)
CABINET = (558, 70, 640, 288)          # the arcade cabinet (its face from picture C)
SPARKLE = (596, 258, 632, 288)         # the generator's mark, painted out
SHAPE_ORDER = ['infinity', 'mobius', 'torus', 'trefoil']   # what picture C shows in slots 1..4

_cache = {}


def pic(k, full=False):
    """Picture k at room scale (RGB), or at full size (full=True)."""
    key = (k, full)
    if key not in _cache:
        im = Image.open(os.path.join(DIR, PICS[k])).convert('RGB')
        if not full:
            im = im.resize((W, round(im.height * K)), Image.LANCZOS)
            im = im.filter(ImageFilter.UnsharpMask(radius=0.8, percent=40, threshold=3))
            im = im.crop((0, TOP, W, TOP + VIEW_H))
        _cache[key] = im
    return _cache[key].copy()


def full_box(box):
    """A room box in full-size picture pixels."""
    x0, y0, x1, y1 = box
    return (round(x0 / K), round((y0 + TOP) / K), round(x1 / K), round((y1 + TOP) / K))


def diff_mask(a, b, box, thresh=60, grow=2):
    """Where b differs from a inside box (a solid mask)."""
    x0, y0, x1, y1 = box
    d = np.abs(np.asarray(a.crop(box)).astype(int) - np.asarray(b.crop(box)).astype(int)).sum(-1) > thresh
    d = ndimage.binary_opening(d, iterations=1)
    d = ndimage.binary_closing(ndimage.binary_dilation(d, iterations=grow), iterations=2)
    return ndimage.binary_fill_holes(d)


def rgba_of(im, mask=None):
    out = im.convert('RGBA')
    if mask is not None:
        out.putalpha(Image.fromarray((mask * 255).astype(np.uint8)))
    return out


def shape_icons():
    """Inventory icons for the four shapes, cut from picture C's board at full size."""
    from art_ui import ICON_W, ICON_H
    A, C = pic('A', True), pic('C', True)
    names = {'infinity': 'iInfinity', 'mobius': 'iMobius', 'torus': 'iTorus', 'trefoil': 'iTrefoil'}
    out = {}
    for k, shape in enumerate(SHAPE_ORDER):
        box = full_box(SLOTS[k])
        m = diff_mask(A, C, box, thresh=80, grow=1)
        spr = rgba_of(C.crop(box), m)
        spr = spr.crop(spr.getbbox())
        s = min((ICON_W - 4) / spr.width, (ICON_H - 4) / spr.height)
        spr = spr.resize((round(spr.width * s), round(spr.height * s)), Image.LANCZOS)
        a = np.asarray(spr).copy()
        a[..., 3] = np.where(a[..., 3] > 120, 255, 0)
        spr = Image.fromarray(a, 'RGBA')
        icon = canvas(ICON_W, ICON_H)
        icon.alpha_composite(spr, ((ICON_W - spr.width) // 2, (ICON_H - spr.height) // 2))
        out[names[shape]] = icon
    return out


def crypt():
    sc = Scene('crypt')
    A, B, C = pic('A'), pic('B'), pic('C')

    # ---------- the room: A, with C's arcade cabinet, the sparkle painted out and the hat lifted
    room = A.copy()
    room.paste(C.crop(CABINET), CABINET[:2])
    bgr = cv2.cvtColor(np.asarray(room), cv2.COLOR_RGB2BGR)
    sm = np.zeros(bgr.shape[:2], np.uint8)
    reg = np.asarray(room.crop(SPARKLE)).astype(int)
    sm[SPARKLE[1]:SPARKLE[3], SPARKLE[0]:SPARKLE[2]] = ((reg.min(-1) > 105) * 255).astype(np.uint8)
    sm = cv2.dilate(sm, np.ones((7, 7), np.uint8))
    bgr = cv2.inpaint(bgr, sm, 4, cv2.INPAINT_TELEA)
    # the hat: pale cream and orange against the dark wall
    hx0, hy0, hx1, hy1 = HAT
    hr = cv2.cvtColor(bgr[hy0:hy1, hx0:hx1], cv2.COLOR_BGR2RGB).astype(int)
    m = (hr.sum(-1) > 330) | ((hr[..., 0] - hr[..., 2]) > 50)
    m = ndimage.binary_fill_holes(ndimage.binary_closing(m, iterations=2))
    lab, n = ndimage.label(m)
    if n:
        m = lab == 1 + int(np.argmax(ndimage.sum(m, lab, range(1, n + 1))))
    m = ndimage.binary_dilation(m, iterations=1)
    hat = Image.fromarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)).crop(HAT).convert('RGBA')
    hat.putalpha(Image.fromarray((m * 255).astype(np.uint8)))
    hb = hat.getbbox()
    hat = hat.crop(hb)
    hat_x, hat_y = hx0 + hb[0], hy0 + hb[1]
    hm = np.zeros(bgr.shape[:2], np.uint8)
    hm[hy0:hy1, hx0:hx1] = m * 255
    hm = cv2.dilate(hm, np.ones((3, 3), np.uint8))
    bgr = cv2.inpaint(bgr, hm, 5, cv2.INPAINT_TELEA)
    fa = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB).astype(float)
    noise = np.random.default_rng(7).normal(0, 5, fa.shape[:2] + (1,))
    fa = np.where((hm > 0)[..., None], np.clip(fa + noise, 0, 255), fa)
    room = Image.fromarray(fa.astype(np.uint8))
    sc.hat_pos = (hat_x, hat_y + hat.height)

    bg = Image.new('RGBA', (W, H), (0, 0, 0, 255))
    bg.paste(room, (0, 0))
    orig = bg.copy()
    sc.bg = bg
    sc.d = ImageDraw.Draw(bg)

    # ---------- hotspots, in the same order as crypt_nb
    sc.hotspot('hArch', 'archway', (152, 230),
               [('poly', [(122, 226), (122, 72), (134, 54), (152, 46), (170, 52), (184, 70), (186, 226)])])
    sc.hotspot('hYarn', 'yarn monster', (230, 262), [('rect', [180, 0, 268, 108])])
    sc.hotspot('hPastaWall', 'Pasta Identification', (337, 250), [('rect', [264, 34, 412, 128])])
    sc.hotspot('hStaff', 'staff room', (462, 242), [('rect', [426, 54, 500, 236])])
    sc.hotspot('h3Button', 'CONFESS booth', (128, 262), [('rect', [0, 38, 108, 288])])
    sc.hotspot('hTrackball', 'MEATBALL MADNESS', (562, 268), [('rect', [570, 74, 640, 288])])
    sc.hotspot('hComputer', 'Classic Computer', (372, 250), [('rect', [342, 128, 406, 240])])
    sc.hotspot('hRex', 'T. Rex cabinet', (318, 262), [('rect', [194, 108, 302, 254])])

    # ---------- the Pasta Identification board: empty recesses (A), shapes cut from C
    shapes = {}
    for k, shape in enumerate(SHAPE_ORDER):
        msk = diff_mask(A, C, SLOTS[k], thresh=80, grow=1)
        shapes[shape] = rgba_of(C.crop(SLOTS[k]), msk)
    for k in range(4):
        empty = orig.crop(SLOTS[k])
        sprites = {'empty': empty}
        for shape in topology.SHAPES:              # the script's order: trefoil infinity mobius torus
            im = empty.copy()
            im.alpha_composite(shapes[shape])
            sprites[shape] = im
        sc.obj('oSlot%d' % (k + 1), 'recess', sprites, SLOTS[k][0], SLOTS[k][3], baseline=1)

    # ---------- the drawer: shut as in the room; out (B), and the crank in it as its own sprite
    out_ = B.crop(DRAWER).convert('RGBA')
    a_ = np.asarray(out_.convert('RGB')).astype(int)
    lum = a_.sum(-1)
    inner = np.zeros(lum.shape, bool)
    inner[3:18, 8:72] = True                      # the drawer's dark inside
    crankpx = inner & (lum > np.median(lum[inner]) + 70)
    lab, n = ndimage.label(ndimage.binary_closing(crankpx, iterations=1))
    if n:
        crankpx = lab == 1 + int(np.argmax(ndimage.sum(crankpx, lab, range(1, n + 1))))
    crankpx = ndimage.binary_dilation(crankpx, iterations=1) & inner
    hole = ndimage.binary_dilation(crankpx, iterations=1) & inner
    dark = inner & ~hole & (lum < np.median(lum[inner]) + 15)
    ea = np.asarray(out_).copy()
    ea[hole, :3] = np.clip(np.median(ea[dark][:, :3], 0)[None, :]
                           + np.random.default_rng(4).normal(0, 4, hole.sum())[:, None], 0, 255).astype(np.uint8)
    empty_drawer = Image.fromarray(ea, 'RGBA')
    shut = orig.crop(DRAWER)
    sc.obj('oCompartment', 'drawer', {'shut': shut, 'open': empty_drawer}, DRAWER[0], DRAWER[3], baseline=1)
    sc.obj('oCrank', 'crank', {'on': rgba_of(out_, crankpx)}, DRAWER[0], DRAWER[3], visible=False, baseline=2)
    sc.uv(lambda im, dd: glow_text(im, (337, 146), 'ASK THE COMPUTER', 8, (120, 255, 200)))

    # ---------- the staff room: an open doorway (no curtain any more)
    door = orig.crop((426, 54, 500, 236))
    sc.obj('oCurtain', 'staff room', {'closed': door, 'open': door}, 426, 236, baseline=2, clickable=False)

    # ---------- the token CONFESS pays out, on the floor (C)
    msk = diff_mask(A, C, COIN, thresh=70, grow=1)
    sc.obj('oToken', 'arcade token', {'on': rgba_of(C.crop(COIN), msk)}, COIN[0], COIN[3], visible=False,
           baseline=COIN[3])

    # ---------- the Pope Seat: the socket as painted; with the crank; with the guest in it
    sx0, sy0, sx1, sy1 = SEAT
    empty = orig.crop(SEAT)
    # just the throne, not the wall or the arcade cabinet beside it
    ea = np.asarray(empty).copy()
    t = np.asarray(A.crop(SEAT)).astype(int)
    gold = (t[..., 0] > 110) & (t[..., 0] - t[..., 2] > 40)
    red = (t[..., 0] > 90) & (t[..., 0] - t[..., 1] > 45) & (t[..., 1] < 70)
    body = ndimage.binary_closing(gold | red, iterations=3)
    body = ndimage.binary_fill_holes(body)
    lab, n = ndimage.label(body)
    if n:
        body = lab == 1 + int(np.argmax(ndimage.sum(body, lab, range(1, n + 1))))
    body = ndimage.binary_dilation(body, iterations=1)
    ea[..., 3] = body * 255
    empty = Image.fromarray(ea, 'RGBA')
    # the crank: the old Crypt picture's, in the socket
    old = Image.open(os.path.join(DIR, 'base.jpg')).convert('RGB').resize((W, VIEW_H), Image.LANCZOS)
    kx0, ky0, kx1, ky1 = 527, 203, 552, 232
    reg = np.asarray(old.crop((kx0, ky0, kx1, ky1))).astype(int)
    iron = (np.abs(reg[..., 2] - reg[..., 0]) < 40) & (reg.sum(-1) < 400)
    crank = rgba_of(old.crop((kx0, ky0, kx1, ky1)), iron)
    crank = crank.resize((round(crank.width * 1.12), round(crank.height * 1.12)), Image.LANCZOS)
    with_crank = empty.copy()
    with_crank.alpha_composite(crank, (SOCKET[0] - sx0 - 4, SOCKET[1] - sy0 - 3))
    import guest_sheet

    def sit(base, decree=False):
        im = base.copy()
        pose = guest_sheet.seated(decree)
        pose = pose.resize((round(pose.width * 1.15), round(pose.height * 1.15)), Image.LANCZOS)
        a = np.asarray(pose).copy()
        a[..., 3] = np.where(a[..., 3] > 120, 255, 0)
        pose = Image.fromarray(a, 'RGBA')
        im.alpha_composite(pose, (522 - sx0 - pose.width // 2, 246 - sy0 - pose.height))
        return im
    sc.obj('oSeat', 'Pope Seat', {'empty': empty, 'crank': with_crank, 'seated': sit(with_crank),
                                  'decree': sit(with_crank, True), 'seatednc': sit(empty)},
           sx0, sy1, baseline=250)

    # ---------- the computer: off as in the room; on (B), once Chuk plugs it in
    sc.obj('oScreen', 'screen', {'on': B.crop(SCREEN).convert('RGBA')}, SCREEN[0], SCREEN[3],
           baseline=1, clickable=False, visible=False)
    sc.obj('oHat', 'pasta pope hat', {'on': hat}, hat_x, hat_y + hat.height, baseline=251)

    # ---------- the CONFESS booth: shut (A), half open (B) and open (C)
    sc.obj('oBooth', 'CONFESS booth', {'shut': orig.crop(BOOTH), 'ajar': B.crop(BOOTH).convert('RGBA'),
                                       'open': C.crop(BOOTH).convert('RGBA')},
           BOOTH[0], BOOTH[3], baseline=1, clickable=False)

    # ---------- the cabinets' screens: T. Rex playing (A), off (E), HIGH SCORE (D), the table (F);
    # the meatball cabinet INSERT COIN (D) and in play (C, as in the room)
    D, E, F = pic('D'), pic('E'), pic('F')
    sc.obj('oRexScreen', 'screen', {k: im.crop(REX_SCREEN).convert('RGBA') for k, im in
                                    (('play', A), ('off', E), ('high', D), ('scores', F))},
           REX_SCREEN[0], REX_SCREEN[3], baseline=1, clickable=False)
    sc.obj('oMeatScreen', 'screen', {'coin': D.crop(MEAT_SCREEN).convert('RGBA'),
                                     'game': orig.crop(MEAT_SCREEN)},
           MEAT_SCREEN[0], MEAT_SCREEN[3], baseline=1, clickable=False)

    sc.uv(lambda im, dd: glow_text(im, (526, 268), 'THE CRANK NEEDS', 8, (255, 160, 80)))
    sc.uv(lambda im, dd: glow_text(im, (526, 280), 'A SECOND PAIR OF HANDS', 8, (255, 160, 80)))
    sc.uv(lambda im, dd: glow_text(im, (224, 116), 'THE SAUCE IS WITHIN', 8, (120, 255, 160)))

    # ---------- walkable floor
    sc.wd.polygon([(108, 288), (108, 240), (122, 228), (186, 228), (196, 240), (204, 258), (302, 258),
                   (310, 246), (420, 246), (428, 238), (500, 238), (500, 246), (476, 262), (580, 262),
                   (570, 288)], fill=1)
    return sc


if __name__ == '__main__':
    sc = crypt()
    im = sc.bg.copy()
    for o in sc.objects:
        if o['visible']:
            s = o['sprites'][o['state']]
            im.alpha_composite(s, (o['x'], o['y'] - s.height))
    im.save('/tmp/claude-0/run/crypt_v3.png')
