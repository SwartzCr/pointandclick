"""The Crypt on the Nano Banana room (art_src/crypt-nb/base.jpg, shrunk to 640x288).

The changing parts are cut from the picture: the four label plates on the
Pasta Identification board (words drawn on), the WORTHY panel, the STAFF
curtain, the Pope Seat (with a credit light and the seated guest) and the
lasagna hat, which is lifted out of the picture (the wall behind it is
filled in) so it can be lowered. Object and hotspot names and order match
art_rooms.crypt(), so the game script works with either.
"""
import os
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFilter

from art_common import canvas, rgba
from art_rooms import Scene, glow_text, W, H, VIEW_H, PASTA
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
COIN = (521, 224)                      # the coin slot on the seat's front


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

    # ---------- the label plates and the WORTHY panel
    gold, gold_lit, ink = (214, 170, 84), (255, 230, 120), (60, 34, 24)

    def label_sprite(name, lit=False):
        n = name.upper()
        sp = 1 if tiny_width(n) <= 28 else 0
        w = 34
        im = canvas(w, PLATE_Y[1] - PLATE_Y[0])
        d = ImageDraw.Draw(im)
        d.rectangle([0, 0, w - 1, im.height - 1], fill=rgba(gold_lit if lit else gold))
        d.line([(0, im.height - 1), (w - 1, im.height - 1)], fill=rgba((130, 92, 40)))
        tiny(im, w / 2, im.height / 2, n, ink, sp)
        return im

    for i in range(4):
        sprites = {('n%d' % j): label_sprite(PASTA[j]) for j in range(4)}
        sprites.update({('l%d' % j): label_sprite(PASTA[j], lit=True) for j in range(4)})
        sc.obj('oLabel%d' % (i + 1), 'label', sprites, PLATES[i] - 17, PLATE_Y[1], baseline=1, state='n%d' % (i % 4))
    wx0, wy0, wx1, wy1 = WORTHY_BOX
    lay = canvas(wx1 - wx0 + 8, wy1 - wy0 + 8)
    ImageDraw.Draw(lay).rectangle([4, 4, lay.width - 5, lay.height - 5], fill=rgba(gold_lit))
    word = canvas(*lay.size)
    big = canvas(30, 7)
    tiny(big, 15, 3.5, 'WORTHY', (150, 30, 20))
    big = big.resize((60, 14), Image.NEAREST)
    word.alpha_composite(big, ((lay.width - 60) // 2, (lay.height - 14) // 2))
    worthy = canvas(*lay.size)
    glow_layer(lay, worthy, 3)
    worthy.alpha_composite(word)
    sc.obj('oWorthy', 'WORTHY sign', {'on': worthy}, wx0 - 4, wy1 + 4, visible=False, baseline=1, clickable=False)
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

    # ---------- the Pope Seat: as painted, with a credit light, and with the guest in it
    sx0, sy0, sx1, sy1 = SEAT
    empty = orig.crop(SEAT)
    # the seat's box overlaps the curtain's edge; leave that to the curtain
    ImageDraw.Draw(empty).rectangle([0, 0, CURTAIN[2] - sx0, 183 - sy0], fill=(0, 0, 0, 0))
    ea = np.asarray(empty).copy()
    zone = ea[183 - sy0:CURTAIN[3] - sy0, :CURTAIN[2] - sx0 + 1]
    red = (zone[..., 0].astype(int) - zone[..., 1] > 50) & (zone[..., 0] < 200)
    zone[red] = 0
    empty = Image.fromarray(ea, 'RGBA')
    credit = empty.copy()
    cxl, cyl = COIN[0] - sx0, COIN[1] - sy0
    cd = ImageDraw.Draw(credit)
    cd.ellipse([cxl - 3, cyl - 3, cxl + 3, cyl + 3], fill=rgba((80, 250, 120)))
    cd.point((cxl - 1, cyl - 1), fill=rgba((220, 255, 220)))
    import guest_sheet
    seated = credit.copy()
    decree = credit.copy()
    for im_, pose in ((seated, guest_sheet.seated()), (decree, guest_sheet.seated(decree=True))):
        im_.alpha_composite(pose, ((empty.width - pose.width) // 2 - 2, 122 - pose.height))
    sc.obj('oSeat', 'Pope Seat', {'empty': empty, 'credit': credit, 'seated': seated, 'decree': decree}, sx0, sy1, baseline=250)
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
