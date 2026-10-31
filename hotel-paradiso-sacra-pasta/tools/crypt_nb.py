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
SLOTS = [289, 318, 349, 381]           # the four shape recesses on the board (centres)
SLOT_Y = (92, 115)
BOARD_INNER = (271, 89, 399, 149)      # below the board's title: repainted with the empty recesses
COMPARTMENT = (304, 137, 362, 148)     # the brass plate that opens on the crank
SCREEN = (352, 158, 378, 179)          # the computer's screen
NAMES = ['FUSILLI', 'ORECCHIETTE', 'FARFALLE', 'RIGATONI']


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
    sc.hotspot('h3Button', '3Button cabinet', (120, 252), [('poly', [(8, 100), (100, 104), (102, 288), (8, 288)])])
    sc.hotspot('hTrackball', 'Trackball cabinet', (548, 266), [('poly', [(560, 104), (640, 92), (640, 288), (560, 288)])])
    sc.hotspot('hComputer', 'Classic Computer', (365, 242), [('rect', [337, 150, 394, 232])])
    sc.hotspot('hRex', 'Rex Seat', (300, 262), [('rect', [210, 140, 300, 250])])

    # ---------- the Pasta Identification board: names, empty recesses, a plate that opens (stand-in)
    import topology
    gold, gold_lit, ink = (214, 170, 84), (255, 230, 120), (60, 34, 24)
    bx0, by0, bx1, by1 = BOARD_INNER
    wood = np.asarray(orig.crop((bx0, by0, bx1, by1)).convert('RGB')).astype(float)
    base_c = np.median(wood.reshape(-1, 3), 0)
    rng = np.random.default_rng(3)
    grain = np.clip(base_c[None, None, :] * (0.92 + 0.08 * np.sin(np.arange(by1 - by0)[:, None, None] * 1.7)
                                           + rng.normal(0, 0.025, (by1 - by0, bx1 - bx0, 1))), 0, 255)
    room.paste(Image.fromarray(grain.astype(np.uint8)).convert('RGBA'), (bx0, by0))
    d = ImageDraw.Draw(room)
    rec_dark, rec_rim = (46, 28, 20, 255), (120, 80, 40, 255)
    for cxs in SLOTS:
        d.rounded_rectangle([cxs - 13, SLOT_Y[0], cxs + 13, SLOT_Y[1]], 4, fill=rec_dark, outline=rec_rim)

    def plate(cx, y, txt):
        w = tiny_width(txt) + 6
        x = int(cx - w / 2)
        d.rectangle([x, y, x + w, y + 8], fill=rgba(gold))
        d.line([(x, y + 8), (x + w, y + 8)], fill=rgba((130, 92, 40)))
        tiny(room, x + w / 2 + 0.5, y + 4.5, txt, ink, 1)
    # names under the recesses, staggered so ORECCHIETTE fits
    for k, (cxs, txt) in enumerate(zip(SLOTS, NAMES)):
        plate(cxs, 118 if k % 2 == 0 else 127, txt)
    cx0, cy0, cx1, cy1 = COMPARTMENT
    d.rectangle([cx0, cy0, cx1, cy1], fill=rgba((176, 132, 60)), outline=rgba((110, 74, 30)))
    d.line([(cx0 + 2, cy0 + 2), (cx1 - 2, cy0 + 2)], fill=rgba((230, 196, 110)))
    d.ellipse([(cx0 + cx1) // 2 - 2, cy0 + 4, (cx0 + cx1) // 2 + 2, cy0 + 8], fill=rgba((60, 34, 20)))
    orig = room.copy()

    def slot_sprite(k):
        cxs = SLOTS[k]
        box = (cxs - 13, SLOT_Y[0], cxs + 14, SLOT_Y[1] + 1)
        return orig.crop(box), box

    shapes = {n: topology.shape(n, 24, 21) for n in topology.SHAPES}
    for k in range(4):
        empty_slot, box = slot_sprite(k)
        sprites = {'empty': empty_slot}
        for n in topology.SHAPES:
            im = empty_slot.copy()
            im.alpha_composite(shapes[n], (1, 1))
            sprites[n] = im
        sc.obj('oSlot%d' % (k + 1), 'recess', sprites, box[0], box[3], baseline=1)
    # the compartment: shut as painted; open shows a dark hollow with the crank in it
    shut = orig.crop(COMPARTMENT)
    hollow = shut.copy()
    hd_ = ImageDraw.Draw(hollow)
    hd_.rectangle([0, 0, hollow.width - 1, hollow.height - 1], fill=(30, 18, 14, 255), outline=(110, 74, 30, 255))
    sc.obj('oCompartment', 'brass plate', {'shut': shut, 'open': hollow}, cx0, cy1 + 1, baseline=1)
    sc.obj('oCrank', 'crank', {'on': topology.crank(22, 11)}, cx0 + 18, cy1, visible=False, baseline=2)
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
    with_crank = Image.fromarray(ea, 'RGBA')
    # without the crank: paint it out of the seat's side, leaving a dark socket
    bgr = cv2.cvtColor(np.asarray(with_crank.convert('RGB')), cv2.COLOR_RGB2BGR)
    k0, k1 = CRANK_BOX[0] - sx0, CRANK_BOX[1] - sy0
    reg = bgr[k1:CRANK_BOX[3] - sy0, k0:CRANK_BOX[2] - sx0].astype(int)
    iron = (np.abs(reg[..., 2] - reg[..., 0]) < 40) & (reg.sum(-1) < 400)          # grey, not gold
    cm = np.zeros(bgr.shape[:2], np.uint8)
    cm[k1:CRANK_BOX[3] - sy0, k0:CRANK_BOX[2] - sx0] = iron * 255
    cm = cv2.dilate(cm, np.ones((3, 3), np.uint8))
    filled_seat = cv2.inpaint(bgr, cm, 3, cv2.INPAINT_TELEA)
    no_crank = Image.fromarray(cv2.cvtColor(filled_seat, cv2.COLOR_BGR2RGB)).convert('RGBA')
    no_crank.putalpha(with_crank.getchannel('A'))
    ImageDraw.Draw(no_crank).ellipse([534 - sx0 - 2, 212 - sy0 - 2, 534 - sx0 + 2, 212 - sy0 + 2], fill=(40, 30, 30, 255))
    empty = no_crank
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
    scr = orig.crop(SCREEN)
    ImageDraw.Draw(scr).rectangle([1, 1, scr.width - 2, scr.height - 2], fill=(18, 22, 22, 255))
    ImageDraw.Draw(scr).line([(3, 3), (8, 3)], fill=(50, 58, 58, 255))
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
