"""HOTEL.EXE: a tiny Hotel Paradiso playable on the Crypt's Classic Computer.

Room 714 is drawn with the first game's own art code (hotel-paradiso-scummc/
tools/art.py) at exactly twice its 320x144 size, so it fills the 640x288 room
view, with a CRT edge round it. The guest appears as he was then, in his
bathrobe (cMini, frames from the same art code at 2x). A newspaper lies on the
floor; reading it gives the answer to the Crypt's Pasta Identification wall.
"""
import os
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from art_rooms import Scene, W, H, VIEW_H
from art_common import canvas, rgba, outline

HERE = os.path.dirname(os.path.abspath(__file__))
HP = os.path.join(HERE, '..', '..', 'hotel-paradiso-scummc', 'tools')
_art = None


def hp_art():
    global _art
    if _art is None:
        sys.path.insert(0, HP)
        keep = sys.dont_write_bytecode
        sys.dont_write_bytecode = True      # don't touch the first game's tracked __pycache__
        try:
            import importlib
            _art = importlib.import_module('art')
        finally:
            sys.path.remove(HP)
            sys.dont_write_bytecode = keep
    return _art


def x2(im):
    return im.resize((im.width * 2, im.height * 2), Image.NEAREST)


def keyed(im):
    a = np.asarray(im.convert('RGBA')).copy()
    mag = (a[..., 0] == 255) & (a[..., 1] == 0) & (a[..., 2] == 255)
    a[mag, 3] = 0
    return Image.fromarray(a, 'RGBA')


def newspaper():
    """A folded newspaper lying on the carpet (20x9 at 1x, drawn 2x)."""
    im = canvas(22, 10)
    d = ImageDraw.Draw(im)
    d.polygon([(1, 8), (3, 1), (20, 0), (21, 7)], fill=rgba((232, 226, 206)))
    d.polygon([(1, 8), (21, 7), (20, 9), (2, 9)], fill=rgba((186, 180, 160)))
    d.line([(4, 2), (12, 2)], fill=rgba((40, 36, 40)))               # masthead
    for y in (4, 6):
        d.line([(4, y), (18, y - 0.5)], fill=rgba((130, 126, 120)))
    d.rectangle([14, 2, 18, 4], fill=rgba((150, 140, 120)))          # a little photo
    return x2(outline(im, (40, 24, 30, 255)))


def crt(im, top=0):
    """The CRT's scanlines (odd screen rows darker), for a sprite placed at screen row top."""
    a = np.asarray(im.convert('RGBA')).astype(float)
    start = 1 - (top % 2)
    a[start::2, :, :3] *= 0.86
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), 'RGBA')


def tv_channel(k):
    """The TV screen (29x21 at 1x): 0 weather, 1 cooking show, 2 tiny bellhop, 3 static."""
    art = hp_art()
    if k == 0:
        return art.render({'tv': 1}).convert('RGB').crop((85, 39, 114, 60))
    im = Image.new('RGB', (29, 21), (20, 24, 40))
    d = ImageDraw.Draw(im)
    if k == 1:          # a cooking show: a man in a colander over a pot
        d.rectangle([0, 0, 28, 20], fill=(150, 90, 60))
        d.rectangle([0, 14, 28, 20], fill=(90, 60, 40))
        d.ellipse([9, 3, 17, 11], fill=(232, 180, 140))
        d.pieslice([8, 0, 18, 8], 180, 360, fill=(200, 205, 215))
        d.rectangle([9, 11, 17, 17], fill=(240, 232, 210))
        d.rectangle([18, 11, 26, 16], fill=(60, 60, 70))
        d.line([(19, 10), (21, 8), (23, 10)], fill=(250, 220, 120))
        d.rectangle([0, 18, 28, 20], fill=(200, 40, 40))
    elif k == 2:        # a tiny bellhop at a tiny computer, in a tiny purple crypt
        d.rectangle([0, 0, 28, 20], fill=(60, 40, 90))
        d.rectangle([0, 15, 28, 20], fill=(40, 30, 60))
        d.rectangle([17, 8, 25, 14], fill=(200, 190, 160))
        d.rectangle([18, 9, 24, 12], fill=(60, 180, 90))
        d.rectangle([8, 7, 11, 15], fill=(190, 30, 30))
        d.rectangle([8, 4, 11, 7], fill=(232, 180, 140))
        d.rectangle([8, 3, 11, 4], fill=(190, 30, 30))
    else:               # static
        rng = np.random.default_rng(7)
        a = (rng.random((21, 29)) * 200 + 30).astype(np.uint8)
        im = Image.fromarray(np.stack([a, a, a], -1))
    return im


def hotel():
    art = hp_art()
    sc = Scene('hotel')
    room = x2(art.render({'tv': 1}).convert('RGB')).convert('RGBA')   # the TV on, showing the weather
    # a CRT: faint scanlines, darkened rounded corners
    a = np.asarray(room).astype(float)
    a[1::2, :, :3] *= 0.86
    yy, xx = np.mgrid[0:VIEW_H, 0:W]
    dx = np.clip(np.abs(xx - W / 2) - (W / 2 - 40), 0, None) / 40
    dy = np.clip(np.abs(yy - VIEW_H / 2) - (VIEW_H / 2 - 40), 0, None) / 40
    corner = np.clip(np.sqrt(dx ** 2 + dy ** 2), 0, 1) ** 2
    a[..., :3] *= (1 - 0.85 * corner)[..., None]
    room = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), 'RGBA')
    sc.bg = Image.new('RGBA', (W, H), (0, 0, 0, 255))
    sc.bg.paste(room, (0, 0))
    sc.d = ImageDraw.Draw(sc.bg)
    d = sc.d
    # a LOG OFF button in the top-right corner, and the program's name
    f = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf', 10)
    d.rectangle([556, 6, 628, 22], fill=rgba((214, 204, 172)), outline=rgba((90, 80, 64)))
    d.text((592, 14), 'LOG OFF', font=f, fill=rgba((60, 40, 30)), anchor='mm')
    d.text((14, 14), 'HOTEL.EXE', font=f, fill=rgba((200, 255, 200)), anchor='lm')

    # hotspots (Room 714 at 2x)
    sc.hotspot('hDoor', 'door', (100, 226), [('rect', [30, 36, 130, 190])])
    sc.hotspot('hBathroom', 'bathroom', (60, 226), [('poly', [(0, 20), (28, 34), (28, 210), (0, 224)])])
    sc.hotspot('hTv', 'TV', (200, 210), [('rect', [164, 70, 236, 136])])
    sc.hotspot('hDresser', 'dresser', (200, 210), [('rect', [144, 130, 256, 190])])
    sc.hotspot('hCurtains', 'curtains', (330, 210), [('rect', [266, 12, 390, 148])])
    sc.hotspot('hMinibar', 'minibar', (320, 210), [('rect', [286, 148, 352, 190])])
    sc.hotspot('hLamp', 'lamp', (430, 210), [('rect', [398, 80, 436, 140])])
    sc.hotspot('hPhone', 'phone', (440, 210), [('rect', [436, 122, 464, 140])])
    sc.hotspot('hNightstand', 'nightstand', (430, 210), [('rect', [400, 140, 464, 192])])
    sc.hotspot('hPainting', 'painting', (520, 210), [('rect', [496, 32, 592, 80])])
    sc.hotspot('hBed', 'bed', (450, 250), [('rect', [470, 90, 640, 264])])
    sc.hotspot('hTable', 'coffee table', (320, 270), [('rect', [224, 206, 416, 258])])
    sc.hotspot('hLogoff', 'LOG OFF', (520, 210), [('rect', [556, 6, 628, 22])])

    sc.obj('oNewspaper', 'newspaper', {'on': newspaper()}, 66, 214, baseline=214)   # slid under the door

    # things that change: the TV's channels, the lamp, the curtains (cut from the first game's art)
    sc.obj('oTv', 'TV', {('c%d' % k): crt(x2(tv_channel(k)), 78) for k in range(4)}, 170, 120, baseline=1,
           clickable=False, state='c0')
    def region(state, box):
        x0, y0, x1, y1 = box
        return crt(x2(art.render(dict({'tv': 1}, **state)).convert('RGB').crop(box)), y0 * 2)
    lamp_box = (198, 30, 218, 70)
    sc.obj('oLamp', 'lamp', {'off': region({}, lamp_box), 'on': region({'lamp': 1}, lamp_box)},
           lamp_box[0] * 2, lamp_box[3] * 2, baseline=1, clickable=False, state='off')
    cur_box = (132, 6, 196, 74)
    opened = region({'curtains': 1}, cur_box)
    # a huge purple face looking in through the window: the player, outside the game
    face = Image.new('RGBA', opened.size, (0, 0, 0, 0))
    fd = ImageDraw.Draw(face)
    cx, cy = opened.width // 2, opened.height // 2 + 6
    fd.ellipse([cx - 30, cy - 38, cx + 30, cy + 40], fill=(150, 90, 220, 70))
    for ex in (cx - 12, cx + 12):
        fd.ellipse([ex - 6, cy - 14, ex + 6, cy - 6], fill=(230, 220, 255, 150))
        fd.ellipse([ex - 2, cy - 12, ex + 2, cy - 8], fill=(30, 20, 50, 200))
    fd.arc([cx - 14, cy + 6, cx + 14, cy + 22], 20, 160, fill=(230, 220, 255, 140), width=3)
    glass = Image.new('L', opened.size, 0)
    ImageDraw.Draw(glass).rectangle([24, 8, opened.width - 26, 132], fill=255)
    face.putalpha(Image.fromarray((np.asarray(face.getchannel('A')).astype(int) * np.asarray(glass) // 255).astype(np.uint8)))
    with_face = opened.copy()
    with_face.alpha_composite(face)
    sc.obj('oCurtains', 'curtains', {'closed': region({}, cur_box), 'open': with_face},
           cur_box[0] * 2, cur_box[3] * 2, baseline=1, clickable=False, state='closed')

    sc.wd.polygon([(20, 196), (466, 196), (466, 286), (20, 286)], fill=1)
    sc.wd.rectangle([220, 206, 420, 258], fill=0)                 # coffee table
    return sc


def loading_screens():
    """640x400 frames: Hotel Paradiso's title on the CRT, with a loading bar filling up."""
    art = hp_art()
    title = x2(art.render_title().convert('RGB')).convert('RGBA')
    base = Image.new('RGBA', (W, H), (0, 0, 0, 255))
    base.paste(title, (0, 0))
    a = np.asarray(base).astype(float)
    a[1:VIEW_H:2, :, :3] *= 0.86
    base = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), 'RGBA')
    f = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf', 14)
    g = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf', 10)
    out = []
    for frac, label in ((0.0, 'LOADING...'), (0.2, 'LOADING...'), (0.45, 'LOADING CLOWNS...'),
                        (0.6, 'LOADING CLOWNS...'), (0.85, 'LOADING DUCK...'), (1.0, 'READY.')):
        im = base.copy()
        d = ImageDraw.Draw(im)
        d.text((W // 2, 318), 'HOTEL PARADISO - ROOM 714', font=f, fill=rgba((255, 120, 170)), anchor='mm')
        d.text((W // 2, 342), label, font=g, fill=rgba((200, 255, 200)), anchor='mm')
        d.rectangle([200, 356, 440, 366], outline=rgba((200, 255, 200)))
        if frac > 0:
            d.rectangle([203, 359, 203 + int(234 * frac), 363], fill=rgba((200, 255, 200)))
        d.text((W // 2, 388), 'C:\\GAMES\\HOTEL.EXE', font=g, fill=rgba((120, 160, 120)), anchor='mm')
        out.append(im)
    return out


def views(spr):
    """VMINI / VMINITALK: the guest in his bathrobe, from Hotel Paradiso's art at 2x."""
    art = hp_art()
    k = lambda im: x2(keyed(im))
    front = [spr('mini_front%d' % s, k(art.actor_front(s, outfit='robe'))) for s in range(3)]
    back = [spr('mini_back%d' % s, k(art.actor_back(s, outfit='robe'))) for s in range(3)]
    side = [spr('mini_side%d' % s, k(art.actor_side(s, outfit='robe'))) for s in range(4)]
    tf = spr('mini_front_talk', k(art.actor_front(0, talk=True, outfit='robe')))
    ts = spr('mini_side_talk', k(art.actor_side(0, talk=True, outfit='robe')))
    walk_fb = lambda fr: [fr[0], fr[1], fr[0], fr[2], fr[0]]
    loops = [[(f, 0, False) for f in walk_fb(front)],
             [(f, 0, True) for f in [side[0]] + side],
             [(f, 0, False) for f in [side[0]] + side],
             [(f, 0, False) for f in walk_fb(back)]]
    talk = [[(front[0], 0, False), (tf, 0, False)],
            [(side[0], 0, True), (ts, 0, True)],
            [(side[0], 0, False), (ts, 0, False)],
            [(back[0], 0, False)]]
    return [dict(name='VMINI', loops=loops), dict(name='VMINITALK', loops=talk)]


if __name__ == '__main__':
    sc = hotel()
    im = sc.bg.copy()
    for o in sc.objects:
        s = o['sprites'][o['state']]
        im.alpha_composite(s, (o['x'], o['y'] - s.height))
    im.save('/tmp/claude-0/nb/hotel_mini.png')
