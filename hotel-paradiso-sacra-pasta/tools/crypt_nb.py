"""The Crypt on the Nano Banana room (art_src/crypt-nb/base.jpg, shrunk to 640x288).

The changing parts are cut from the picture: the four label plates on the
Pasta Identification board (words drawn on), the WORTHY panel, the STAFF
curtain, the Pope Seat (with and without its crank, and with the guest in it) and the
lasagna hat, which is lifted out of the picture (the wall behind it is
filled in) so it can be lowered. Object and hotspot names and order match
art_rooms.crypt(), so the game script works with either.
"""
import os
import numpy as np
import cv2
from scipy import ndimage
from PIL import Image, ImageDraw, ImageFilter

from art_common import canvas, rgba
from art_rooms import Scene, glow_text, W, H, VIEW_H
from nave_painted import glow_layer
from nave_muse import tiny, tiny_width, keyed, fit
import nave_muse as NM

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, '..', 'art_src', 'crypt-nb', 'base.jpg')

PLATES = [287, 319, 350, 382]          # label plate centres on the board (y 120..128)
PLATE_Y = (120, 129)
WORTHY_BOX = (300, 131, 367, 143)
CURTAIN = (413, 88, 481, 222)
SEAT = (466, 118, 560, 252)
HAT = (506, 50, 554, 134)              # the hanging lasagna hat
HAT_LOWERED_BOTTOM = 168               # where its bottom ends up, on the seated guest's head
CRANK_BOX = (527, 203, 552, 232)       # the crank on the seat's side (painted in; it starts missing)
SLOTS = [288, 318, 349, 381]           # the four shape recesses on the painted board (centres)
SLOT_Y = (92, 115)
COMPARTMENT = (302, 132, 366, 145)     # the brass plate that opens on the crank
SCREEN = (352, 158, 378, 179)          # the computer's screen
NAMES = ['OTTINI', 'TORTINI', 'ANELLI', 'NODINI']   # the new pastas: eights, twists, rings, knots


# the second picture of the Crypt: CONFESS as a confessional booth, the T. Rex skull cabinet,
# the new Pasta Identification board, the computer switched off and the throne with a crank
# socket. It's the same room, drawn 2% narrower and 10% taller, so it's stretched to line up
# with base.jpg and just those pieces are pasted in.
V2 = ('v2-A-confess-computer-trex-board-throne.png', [[1.0219, -0.0025, 58.128], [-0.0, 0.9054, 3.7787]])
# a second picture framed exactly like v2-A: the booth half open, the board's drawer open with
# the crank in it, and a new back glass, screen and trackball for the arcade cabinet
V2B = 'v2-B-booth-open-drawer-trackball.png'
BOOTH_SRC, BOOTH_AT = (20, 80, 136, 288), (6, 80)
DRAWER = (296, 127, 376, 155)                  # the board's drawer, pulled out
_composed = {}


def v2_aligned(name=None):
    nw = cv2.imread(os.path.join(os.path.dirname(SRC), name or V2[0]))
    nw = cv2.warpAffine(nw, np.array(V2[1], np.float32), (1536, 688), flags=cv2.INTER_LANCZOS4,
                        borderMode=cv2.BORDER_REPLICATE)
    return Image.fromarray(cv2.cvtColor(nw, cv2.COLOR_BGR2RGB)).resize((W, VIEW_H), Image.LANCZOS)


def composed(alt=False):
    """base.jpg with the second picture's five pieces pasted in (alt: the booth half open and
    the drawer out with the crank in it, from v2-B), and the arcade cabinet's new face."""
    if alt in _composed:
        return _composed[alt].copy()
    old = Image.open(SRC).convert('RGB').resize((W, VIEW_H), Image.LANCZOS)
    nw = v2_aligned()
    nb = v2_aligned(V2B)
    O = np.asarray(old).astype(float)
    N = np.asarray(nw).astype(float)
    NB = np.asarray(nb).astype(float)
    # the two pictures are lit a little differently: match the new one's colours to the old,
    # channel by channel, over the whole room
    for c in range(3):
        mu, sd = N[..., c].mean(), N[..., c].std()
        N[..., c] = (N[..., c] - mu) / sd * O[..., c].std() + O[..., c].mean()
        NB[..., c] = (NB[..., c] - mu) / sd * O[..., c].std() + O[..., c].mean()
    if alt:
        N = NB
    out = O.copy()

    def paste(box, at=None, keep=None, feather=4):
        """The new picture's box, at `at`, blended in: colours matched again to the old picture
        along the patch's edge, and the edge feathered. keep(mask) can trim the mask."""
        x0, y0, x1, y1 = box
        ax, ay = at or (x0, y0)
        w, h = x1 - x0, y1 - y0
        src = N[y0:y1, x0:x1].copy()
        dst = out[ay:ay + h, ax:ax + w]
        band = np.zeros((h, w), bool)
        band[:3], band[-3:], band[:, :3], band[:, -3:] = True, True, True, True
        for c in range(3):
            src[..., c] += (dst[..., c][band].mean() - src[..., c][band].mean())
        m = np.zeros((h, w), np.uint8)
        m[feather:h - feather, feather:w - feather] = 255
        if keep is not None:
            m = keep(m, x0, y0)
        m = cv2.GaussianBlur(m, (0, 0), feather / 2).astype(float)[..., None] / 255
        out[ay:ay + h, ax:ax + w] = dst * (1 - m) + src * m

    # the confessional is narrower than the old CONFESS cabinet, so it moves left a little
    # to cover it; the wall and floor around it come along
    paste(BOOTH_SRC, BOOTH_AT, feather=6)
    # the T. Rex skull, with the wall and floor around it
    paste((190, 114, 314, 286), feather=6)
    # the board, and the computer (switched off)
    paste((264, 68, 408, 156), feather=2)
    paste((336, 148, 398, 234), feather=2)

    # the throne with its socket, up to the arcade cabinet; left of x 478 the old curtain
    # stays, apart from the throne's own arm, button and leg
    def throne(m, x0, y0):
        reg = N[y0:y0 + m.shape[0], x0:x0 + m.shape[1]]
        gold = (reg[..., 0] > 120) & (reg[..., 0] - reg[..., 2] > 45)
        button = (reg[..., 0] > 160) & (reg[..., 1] < 90)
        part = ndimage.binary_dilation(ndimage.binary_fill_holes(gold | button), iterations=1)
        cut = 478 - x0
        m[:, :cut] = np.where(part[:, :cut], m[:, :cut], 0)
        poly = Image.new('L', (m.shape[1], m.shape[0]), 0)
        ImageDraw.Draw(poly).polygon([(0, 0), (550 - x0, 0), (550 - x0, m.shape[0]), (0, m.shape[0])], fill=255)
        return np.minimum(m, np.asarray(poly))
    paste((452, 108, 572, 262), keep=throne, feather=3)
    # between the new throne and the arcade cabinet, the old picture still has the edge of the
    # old, wider throne and its crank: paint those out so it's just wall and floor
    x0, x1, y0, y1 = 545, 562, 150, 262
    strip = out[y0:y1, x0:x1]
    gold = (strip[..., 0] > 110) & (strip[..., 0] - strip[..., 2] > 30)
    iron = (np.abs(strip[..., 0] - strip[..., 2]) < 25) & (strip.sum(-1) > 150) & (strip.sum(-1) < 420)
    cab = np.zeros_like(gold)
    for y in range(y1 - y0):                       # leave the arcade cabinet alone
        edge = 557 if y + y0 < 198 else (558 if y + y0 < 214 else 570)
        cab[y, max(0, edge - x0):] = True
    tm = np.zeros((VIEW_H, W), np.uint8)
    tm[y0:y1, x0:x1] = ((gold | iron) & ~cab) * 255
    tm = cv2.dilate(tm, np.ones((3, 3), np.uint8))
    tm[:, 550:] &= 255                              # (keep within the strip)
    bgr = cv2.cvtColor(np.clip(out, 0, 255).astype(np.uint8), cv2.COLOR_RGB2BGR)
    fixed = cv2.cvtColor(cv2.inpaint(bgr, tm, 4, cv2.INPAINT_TELEA), cv2.COLOR_BGR2RGB).astype(float)
    out = np.where((tm > 0)[..., None], fixed, out)
    # the arcade cabinet keeps its body; its back glass, screen and trackball come from v2-B.
    # First the old meatball (and its glow) is painted out where the new parts won't cover it.
    reg = out[165:192, 566:596]
    orange = (reg[..., 0] > 120) & (reg[..., 0] - reg[..., 2] > 40)
    tm = np.zeros((VIEW_H, W), np.uint8)
    tm[165:192, 566:596] = orange * 255
    tm = cv2.dilate(tm, np.ones((3, 3), np.uint8))
    bgr = cv2.cvtColor(np.clip(out, 0, 255).astype(np.uint8), cv2.COLOR_RGB2BGR)
    out = cv2.cvtColor(cv2.inpaint(bgr, tm, 3, cv2.INPAINT_TELEA), cv2.COLOR_BGR2RGB).astype(float)
    nbi = Image.fromarray(np.clip(NB, 0, 255).astype(np.uint8))
    for src, dst in (((558, 110, 596, 131), (576, 109, 614, 130)),     # back glass
                     ((569, 148, 606, 186), (591, 147, 627, 187)),     # screen
                     ((552, 186, 606, 206), (566, 186, 620, 206))):    # control panel, trackball
        p = np.asarray(nbi.crop(src).resize((dst[2] - dst[0], dst[3] - dst[1]), Image.LANCZOS)).astype(float)
        m = np.zeros(p.shape[:2], np.uint8)
        m[1:-1, 1:-1] = 255
        m = cv2.GaussianBlur(m, (0, 0), 0.8).astype(float)[..., None] / 255
        out[dst[1]:dst[3], dst[0]:dst[2]] = out[dst[1]:dst[3], dst[0]:dst[2]] * (1 - m) + p * m
    out = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))
    _composed[alt] = out
    return out.copy()


def _pal(im):
    """Snap to a 256-colour palette made from the room itself."""
    global _palette
    try:
        _palette
    except NameError:
        q = composed().quantize(
            256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
        _palette = Image.new('P', (1, 1))
        _palette.putpalette(q.getpalette())
    a = im.getchannel('A') if im.mode == 'RGBA' else None
    out = im.convert('RGB').quantize(palette=_palette, dither=Image.Dither.NONE).convert('RGBA')
    if a is not None:
        out.putalpha(a.point(lambda v: 255 if v >= 128 else 0))
    return out


def crypt():
    sc = Scene('crypt')
    old_base = Image.open(SRC).convert('RGB').resize((W, VIEW_H), Image.LANCZOS)
    base = composed()

    # lift the hat out: inpaint the wall behind it, keep the cut-out as a sprite
    hx0, hy0, hx1, hy1 = HAT
    hat_mask = np.zeros((VIEW_H, W), np.uint8)
    hat_region = np.asarray(base.crop(HAT)).astype(int)
    # the hat is pale gold/cream; the wall is dark purple-grey
    lum = hat_region.sum(-1)
    m = (lum > 300) | ((hat_region[..., 0] - hat_region[..., 2]) > 40)
    m[70:] = False                     # below this is the throne's finial, not the hat
    m = ndimage.binary_closing(m, iterations=2)
    m = ndimage.binary_fill_holes(m)
    lab, n = ndimage.label(m)
    if n:
        sizes = ndimage.sum(m, lab, range(1, n + 1))
        m = lab == (np.argmax(sizes) + 1)
    m = ndimage.binary_dilation(m, iterations=1)
    hat_mask[hy0:hy1, hx0:hx1] = m * 255
    bgr = cv2.cvtColor(np.asarray(base), cv2.COLOR_RGB2BGR)
    filled = cv2.inpaint(bgr, cv2.dilate(hat_mask, np.ones((3, 3), np.uint8)), 4, cv2.INPAINT_TELEA)
    filled = Image.fromarray(cv2.cvtColor(filled, cv2.COLOR_BGR2RGB))
    # a little stone texture back over the smeared patch
    noise = np.random.default_rng(7).normal(0, 6, (VIEW_H, W, 1))
    fa = np.asarray(filled).astype(float)
    pm = (cv2.dilate(hat_mask, np.ones((3, 3), np.uint8)) > 0)[..., None]
    fa = np.where(pm, np.clip(fa + noise, 0, 255), fa)
    filled = Image.fromarray(fa.astype(np.uint8))
    hat = base.crop(HAT).convert('RGBA')
    hat.putalpha(Image.fromarray((m * 255).astype(np.uint8)))
    hat = _pal(hat.crop(hat.getbbox()))
    hbx0, hby0 = hx0 + Image.fromarray((m * 255).astype(np.uint8)).getbbox()[0], hy0 + Image.fromarray((m * 255).astype(np.uint8)).getbbox()[1]

    room_rgb = _pal(filled.convert('RGBA'))
    room = Image.new('RGBA', (W, H), (0, 0, 0, 255))
    room.paste(room_rgb, (0, 0))
    orig = room.copy()
    sc.bg = room
    sc.d = ImageDraw.Draw(room)
    sc.hat_pos = (hbx0, hby0 + hat.height)

    # ---------- hotspots, in the same order as art_rooms.crypt()
    sc.hotspot('hArch', 'archway', (160, 226),
               [('poly', [(132, 215), (132, 100), (142, 84), (160, 74), (178, 84), (188, 100), (190, 215)])])
    sc.hotspot('hYarn', 'yarn monster', (232, 262), [('rect', [185, 22, 275, 132])])
    sc.hotspot('hPastaWall', 'Pasta Identification', (335, 240), [('rect', [268, 72, 402, 150])])
    sc.hotspot('hStaff', 'staff area', (446, 236), [('rect', [413, 76, 481, 222])])
    sc.hotspot('h3Button', 'CONFESS booth', (124, 256), [('rect', [8, 88, 112, 288])])
    sc.hotspot('hTrackball', 'Trackball cabinet', (548, 266), [('poly', [(560, 104), (640, 92), (640, 288), (560, 288)])])
    sc.hotspot('hComputer', 'Classic Computer', (365, 242), [('rect', [337, 150, 394, 232])])
    sc.hotspot('hRex', 'T. Rex cabinet', (300, 262), [('rect', [200, 122, 292, 272])])

    # ---------- the Pasta Identification board: names, empty recesses, a plate that opens (stand-in)
    import topology
    cx0, cy0, cx1, cy1 = COMPARTMENT
    orig = room.copy()

    def slot_sprite(k):
        cxs = SLOTS[k]
        box = (cxs - 12, SLOT_Y[0], cxs + 13, SLOT_Y[1] + 1)
        return orig.crop(box), box

    shapes = {n: topology.shape(n, 24, 21) for n in topology.SHAPES}
    for k in range(4):
        empty_slot, box = slot_sprite(k)
        sprites = {'empty': empty_slot}
        for n in topology.SHAPES:
            im = empty_slot.copy()
            im.alpha_composite(shapes[n], ((im.width - shapes[n].width) // 2, 1))
            sprites[n] = im
        sc.obj('oSlot%d' % (k + 1), 'recess', sprites, box[0], box[3], baseline=1)
    # the compartment: shut as painted; open shows a dark hollow with the crank in it
    shut = orig.crop(COMPARTMENT)
    hollow = shut.copy()
    hd_ = ImageDraw.Draw(hollow)
    hd_.rectangle([0, 0, hollow.width - 1, hollow.height - 1], fill=(30, 18, 14, 255), outline=(110, 74, 30, 255))
    # open: the drawer pulled out (v2-B), with the crank in it as its own sprite on top
    alt = _pal(composed(alt=True).convert('RGBA'))
    dx0, dy0, dx1, dy1 = DRAWER
    full = alt.crop(DRAWER)
    a_ = np.asarray(full.convert('RGB')).astype(int)
    lum = a_.sum(-1)
    inner = np.zeros(lum.shape, bool)
    inner[2:15, 9:70] = True                    # the drawer's dark inside
    crankpx = inner & (lum > np.median(lum[inner]) + 70)
    crankpx = ndimage.binary_closing(crankpx, iterations=1)
    lab, n = ndimage.label(crankpx)
    if n:
        sizes = ndimage.sum(crankpx, lab, range(1, n + 1))
        crankpx = lab == 1 + int(np.argmax(sizes))          # just the crank, not the plates' edges
    crankpx = ndimage.binary_dilation(crankpx, iterations=1) & inner
    # the empty drawer: the crank's pixels filled with the drawer's dark inside
    ea_ = np.asarray(full.convert('RGBA')).copy()
    hole = ndimage.binary_dilation(crankpx, iterations=1) & inner
    dark = inner & ~hole & (lum < np.median(lum[inner]) + 15)
    fillc = np.median(ea_[dark][:, :3], 0)
    noise = np.random.default_rng(4).normal(0, 4, hole.sum())[:, None]
    ea_[hole, :3] = np.clip(fillc[None, :] + noise, 0, 255).astype(np.uint8)
    empty_dr = Image.fromarray(ea_, 'RGBA')
    crank_in = full.copy()
    crank_in.putalpha(Image.fromarray((crankpx * 255).astype(np.uint8)))
    hollow = empty_dr
    sc.obj('oCompartment', 'drawer', {'shut': orig.crop(DRAWER), 'open': hollow}, dx0, dy1, baseline=1)
    import icon_art
    sc.obj('oCrank', 'crank', {'on': crank_in}, dx0, dy1, visible=False, baseline=2)
    sc.uv(lambda im, dd: glow_text(im, (335, 157), 'ASK THE COMPUTER', 8, (120, 255, 200)))

    # ---------- the CONFESS booth: shut as painted, and half open (v2-B) while you play
    bx0, by0 = BOOTH_AT
    bbox = (bx0, by0, bx0 + BOOTH_SRC[2] - BOOTH_SRC[0], VIEW_H)
    sc.obj('oBooth', 'CONFESS booth', {'shut': orig.crop(bbox), 'ajar': alt.crop(bbox)},
           bbox[0], bbox[3], baseline=1, clickable=False)

    # ---------- the STAFF curtain: closed as painted; open shows a little storeroom
    cx0, cy0, cx1, cy1 = CURTAIN
    closed = orig.crop(CURTAIN)
    # open: the same doorway from the curtain-open variant of the room
    var = Image.open(os.path.join(os.path.dirname(SRC), '01-curtain-open.jpg')).convert('RGB').resize((W, VIEW_H), Image.LANCZOS)
    opened = var.crop(CURTAIN).convert('RGBA')
    sc.obj('oCurtain', 'curtain', {'closed': closed, 'open': _pal(opened)}, cx0, cy1, baseline=2)

    # ---------- the arcade token, on the floor by the CONFESS cabinet
    tk = canvas(9, 6)
    td = ImageDraw.Draw(tk)
    td.ellipse([0, 0, 8, 5], fill=rgba((240, 200, 80)))
    td.ellipse([2, 1, 6, 4], fill=rgba((200, 150, 50)))
    td.point((4, 2), fill=rgba((140, 60, 40)))
    sc.obj('oToken', 'arcade token', {'on': tk}, 110, 258, visible=False, baseline=258)

    # ---------- the Pope Seat: missing its crank, with it, and with the guest in it
    sx0, sy0, sx1, sy1 = SEAT
    empty = orig.crop(SEAT)
    # the seat's box overlaps the curtain's edge; leave that to the curtain
    ImageDraw.Draw(empty).rectangle([0, 0, CURTAIN[2] - sx0, 183 - sy0], fill=(0, 0, 0, 0))
    ea = np.asarray(empty).copy()
    zone = ea[183 - sy0:CURTAIN[3] - sy0, :CURTAIN[2] - sx0 + 1]
    red = (zone[..., 0].astype(int) - zone[..., 1] > 50) & (zone[..., 0] < 200)
    zone[red] = 0
    empty = Image.fromarray(ea, 'RGBA')          # the new throne: a socket, no crank
    # with the crank: the old picture's crank, set on the socket
    oldp = np.asarray(old_base.convert('RGB')).astype(int)
    kx0, ky0, kx1, ky1 = CRANK_BOX
    reg = oldp[ky0:ky1, kx0:kx1]
    iron = (np.abs(reg[..., 2] - reg[..., 0]) < 40) & (reg.sum(-1) < 400)          # grey, not gold
    crank_px = Image.fromarray(np.dstack([reg.astype(np.uint8), (iron * 255).astype(np.uint8)]), 'RGBA')
    with_crank = empty.copy()
    with_crank.alpha_composite(crank_px, (kx0 - sx0 - 7, ky0 - sy0 + 4))
    import guest_sheet
    seated = with_crank.copy()
    decree = with_crank.copy()
    for im_, pose in ((seated, guest_sheet.seated()), (decree, guest_sheet.seated(decree=True))):
        im_.alpha_composite(pose, ((empty.width - pose.width) // 2 - 2, 122 - pose.height))
    seated_nc = empty.copy()
    pose = guest_sheet.seated()
    seated_nc.alpha_composite(pose, ((empty.width - pose.width) // 2 - 2, 122 - pose.height))
    sc.obj('oSeat', 'Pope Seat', {'empty': empty, 'crank': with_crank, 'seated': seated, 'decree': decree,
                                  'seatednc': seated_nc}, sx0, sy1, baseline=250)
    # the computer, dark until Chuk plugs it in
    # the room shows the computer switched off; this is its screen on, once Chuk plugs it in
    scr = _pal(old_base.crop(SCREEN).convert('RGBA'))
    sc.obj('oScreen', 'screen', {'on': scr}, SCREEN[0], SCREEN[3], baseline=1, clickable=False, visible=False)
    sc.obj('oHat', 'pasta pope hat', {'on': hat}, hbx0, hby0 + hat.height, baseline=251)

    sc.uv(lambda im, dd: glow_text(im, (512, 262), 'THE CRANK NEEDS', 8, (255, 160, 80)))
    sc.uv(lambda im, dd: glow_text(im, (512, 274), 'A SECOND PAIR OF HANDS', 8, (255, 160, 80)))
    sc.uv(lambda im, dd: glow_text(im, (232, 140), 'THE SAUCE IS WITHIN', 8, (120, 255, 160)))

    # ---------- walkable floor
    sc.wd.polygon([(102, 288), (104, 234), (128, 220), (196, 218), (206, 254), (302, 254), (312, 238),
                   (400, 236), (410, 224), (470, 224), (470, 256), (560, 256), (560, 288)], fill=1)
    return sc


if __name__ == '__main__':
    sc = crypt()
    im = sc.bg.copy()
    for o in sc.objects:
        st = {'oSeat': 'seated', 'oCurtain': 'open'}.get(o['script'], o['state'])
        s = o['sprites'][st]
        im.alpha_composite(s, (o['x'], o['y'] - s.height))
    hat = [o for o in sc.objects if o['script'] == 'oHat'][0]['sprites']['on']
    a = sc.bg.copy()
    for o in sc.objects:
        s = o['sprites'][o['state']]
        if o['visible']:
            a.alpha_composite(s, (o['x'], o['y'] - s.height))
    out = Image.new('RGB', (1280, 1152))
    out.paste(a.crop((0, 0, 640, 288)).resize((1280, 576), Image.NEAREST), (0, 0))
    im.alpha_composite(hat, (sc.hat_pos[0], HAT_LOWERED_BOTTOM - hat.height))
    out.paste(im.crop((0, 0, 640, 288)).resize((1280, 576), Image.NEAREST), (0, 576))
    out.save('/tmp/claude-0/nb/crypt_states.png')
