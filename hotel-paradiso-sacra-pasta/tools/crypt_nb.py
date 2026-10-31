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
SLOTS = [288, 318, 349, 381]           # the four shape recesses on the board (centres)
SLOT_Y = (92, 115)
COMPARTMENT = (302, 132, 366, 145)     # the brass plate that opens on the crank
# the second picture of the Crypt (v2-A): CONFESS as a confessional, the T. Rex skull cabinet,
# the new Pasta Identification board, the computer switched off and the throne with a crank
# socket. It's the same room drawn a little wider, so it's lined up on base.jpg and the
# pieces are pasted in.
V2 = ('v2-A-confess-computer-trex-board-throne.png', [[1.0219, -0.0025, 58.128], [-0.0, 0.9054, 3.7787]])
SCREEN = (352, 158, 378, 179)          # the computer's screen
NAMES = ['OTTINI', 'TORTINI', 'ANELLI', 'NODINI']   # the new pastas: eights, twists, rings, knots


def _pal(im):
    """Snap to a 256-colour palette made from the room itself."""
    global _palette
    try:
        _palette
    except NameError:
        q = Image.open(SRC).convert('RGB').resize((W, VIEW_H), Image.LANCZOS).quantize(
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
    base = Image.open(SRC).convert('RGB').resize((W, VIEW_H), Image.LANCZOS)

    # lift the hat out: inpaint the wall behind it, keep the cut-out as a sprite
    hx0, hy0, hx1, hy1 = HAT
    hat_mask = np.zeros((VIEW_H, W), np.uint8)
    hat_region = np.asarray(base.crop(HAT)).astype(int)
    # the hat is pale gold/cream; the wall is dark purple-grey
    lum = hat_region.sum(-1)
    m = (lum > 300) | ((hat_region[..., 0] - hat_region[..., 2]) > 40)
    from scipy import ndimage
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

    # ---------- the second picture's pieces, pasted over the first
    nw = cv2.imread(os.path.join(os.path.dirname(SRC), V2[0]))
    nw = cv2.warpAffine(nw, np.array(V2[1], np.float32), (1536, 688), flags=cv2.INTER_LANCZOS4,
                        borderMode=cv2.BORDER_REPLICATE)
    nw = Image.fromarray(cv2.cvtColor(nw, cv2.COLOR_BGR2RGB)).resize((W, VIEW_H), Image.LANCZOS)
    sc.v2 = nw

    def paste(src_box, at, cut_out=None, feather=2):
        x0, y0, x1, y1 = src_box
        piece = nw.crop(src_box)
        m = Image.new('L', piece.size, 0)
        ImageDraw.Draw(m).rectangle([feather, feather, piece.width - 1 - feather, piece.height - 1], fill=255)
        if cut_out:
            for bx in cut_out:
                ImageDraw.Draw(m).rectangle([bx[0] - x0, bx[1] - y0, bx[2] - x0, bx[3] - y0], fill=0)
        m = m.filter(ImageFilter.GaussianBlur(feather))
        filled.paste(piece, at, m)
    # the confessional: moved left a little so it covers all of the old CONFESS cabinet
    paste((25, 86, 127, 288), (10, 86))
    edge = nw.crop((25, 100, 26, 288))
    for x in (8, 9):
        filled.paste(edge, (x, 100))
    paste((194, 118, 308, 288), (194, 118))                    # the T. Rex skull cabinet
    paste((266, 70, 406, 154), (266, 70), feather=1)           # the Pasta Identification board
    # first, paint out what's left of the old, wider throne (its gold side and crank)
    fa_ = np.asarray(filled).copy()
    strip = fa_[150:264, 540:561].astype(int)
    gold = (strip[..., 0] > 110) & (strip[..., 0] > strip[..., 2] + 30)
    grey = (np.abs(strip[..., 0] - strip[..., 2]) < 25) & (strip.sum(-1) > 150) & (strip.sum(-1) < 420)
    tm = np.zeros(fa_.shape[:2], np.uint8)
    tm[150:264, 540:561] = (gold | grey) * 255
    tm = cv2.dilate(tm, np.ones((5, 5), np.uint8))
    fill_ = cv2.inpaint(cv2.cvtColor(fa_, cv2.COLOR_RGB2BGR), tm, 5, cv2.INPAINT_TELEA)
    fill_ = cv2.cvtColor(fill_, cv2.COLOR_BGR2RGB).astype(float)
    tex = np.random.default_rng(9).normal(0, 3, fill_.shape[:2] + (1,))
    fa_ = np.where((tm > 0)[..., None], np.clip(fill_ + tex, 0, 255), fa_).astype(np.uint8)
    filled = Image.fromarray(fa_)
    paste((455, 112, 547, 262), (455, 112), cut_out=[(455, 112, 482, 180), (455, 180, 465, 205)])   # the throne, socket and all
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
    sc.obj('oCompartment', 'brass plate', {'shut': shut, 'open': hollow}, cx0, cy1 + 1, baseline=1)
    import icon_art
    crank_spr = icon_art.item('iCrank', 26, 10)
    sc.obj('oCrank', 'crank', {'on': crank_spr}, (cx0 + cx1 - crank_spr.width) // 2, cy1, visible=False, baseline=2)
    sc.uv(lambda im, dd: glow_text(im, (335, 157), 'ASK THE COMPUTER', 8, (120, 255, 200)))

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
    # with the crank: the old picture's crank, moved onto the new socket
    old = np.asarray(base.convert('RGB')).astype(int)
    kx0, ky0, kx1, ky1 = CRANK_BOX
    reg = old[ky0:ky1, kx0:kx1]
    iron = (np.abs(reg[..., 2] - reg[..., 0]) < 40) & (reg.sum(-1) < 400)          # grey, not gold
    crank_px = np.dstack([reg.astype(np.uint8), (iron * 255).astype(np.uint8)])
    with_crank = empty.copy()
    with_crank.alpha_composite(Image.fromarray(crank_px, 'RGBA'), (kx0 - sx0 - 7, ky0 - sy0 + 4))
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
    scr = nw.crop(SCREEN).convert('RGBA')
    sc.obj('oScreen', 'screen', {'off': scr}, SCREEN[0], SCREEN[3], baseline=1, clickable=False)
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
