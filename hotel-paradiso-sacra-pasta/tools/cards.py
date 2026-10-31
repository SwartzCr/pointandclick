"""The title screen and the ending cards, from the painted pictures in art_src/cards
(16:9, shrunk to 640 wide; the generator's sparkle in the corner painted out)."""
import os
import numpy as np
import cv2
from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
DIR = os.path.join(HERE, '..', 'art_src', 'cards')
CARD_W, CARD_H = 640, 358


def unsparkle(im):
    """Paint out the generator's sparkle in the bottom-right corner (full size, 1376x768): the
    pixels around (1320, 715) that are paler and greyer than their surroundings."""
    a = np.asarray(im.convert('RGB')).copy()
    x0, y0, x1, y1 = 1284, 680, 1356, 752
    reg = a[y0:y1, x0:x1].astype(int)
    bg = cv2.medianBlur(a[y0 - 20:y1 + 16, x0 - 20:x1 + 20], 31)[20:-16, 20:-20].astype(int)
    lum, blum = reg.mean(-1), bg.mean(-1)
    yy, xx = np.mgrid[y0:y1, x0:x1]
    star = ((lum - blum > 25) & (np.ptp(reg, -1) < 30)) | ((np.abs(xx - 1320) + np.abs(yy - 715)) < 22)
    star &= (np.abs(xx - 1320) + np.abs(yy - 715)) < 36
    m = np.zeros(a.shape[:2], np.uint8)
    m[y0:y1, x0:x1] = star * 255
    m = cv2.dilate(m, np.ones((7, 7), np.uint8))
    bgr = cv2.inpaint(cv2.cvtColor(a, cv2.COLOR_RGB2BGR), m, 6, cv2.INPAINT_TELEA)
    return Image.fromarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))


def card(im):
    im = unsparkle(im.convert('RGB').crop((0, 0, 1376, 768)))
    im = im.resize((CARD_W, CARD_H), Image.LANCZOS)
    return im.filter(ImageFilter.UnsharpMask(radius=0.8, percent=40, threshold=3)).convert('RGBA')


def load(name):
    return card(Image.open(os.path.join(DIR, name)))


def cards():
    """{sprite name: image} for the ending cards."""
    import crypt_v3
    return {'card_roomservice': load('end_roomservice.png'),
            'card_freeplay': card(crypt_v3.pic('H', True)),
            'card_tinyfolk': load('end_party_tiny.png'),
            'card_end': load('the_end.png')}


def title():
    """The title room: the painted title card across the top, black below; the menu is
    written over the dark street at the bottom of the picture."""
    import art_rooms as R
    from PIL import ImageDraw
    sc = R.title()
    sc.bg.paste((0, 0, 0, 255), (0, 0, sc.bg.width, sc.bg.height))
    sc.bg.paste(load('title.png'), (0, 0))
    return sc
