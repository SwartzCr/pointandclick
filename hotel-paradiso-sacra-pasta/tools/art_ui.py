"""Cursor and inventory icons."""
import math
from PIL import Image, ImageDraw
from art_common import canvas, outline, rgba, shade, text, limb

ICON_W, ICON_H = 48, 40


def cursor():
    im = canvas(21, 21)
    d = ImageDraw.Draw(im)
    for (a, b) in (((10, 0), (10, 7)), ((10, 13), (10, 20)), ((0, 10), (7, 10)), ((13, 10), (20, 10))):
        d.line([a, b], fill=(255, 255, 255, 255))
    return outline(im, (20, 20, 30, 255))


def blank(w=1, h=1):
    return canvas(w, h)


def _icon():
    return canvas(ICON_W, ICON_H), None


def icon_beads():
    im = canvas(ICON_W, ICON_H)
    d = ImageDraw.Draw(im)
    for i in range(16):
        a = math.pi * 2 * i / 16
        x, y = 24 + 15 * math.sin(a), 18 - 11 * math.cos(a)
        d.ellipse([x - 3, y - 2, x + 3, y + 2], fill=rgba((250, 222, 150)))
        d.arc([x - 2, y - 1, x + 2, y + 2], 200, 340, fill=rgba((204, 160, 84)))
    d.ellipse([18, 26, 30, 38], fill=rgba((250, 222, 150)))
    d.arc([20, 28, 28, 36], 0, 360, fill=rgba((204, 160, 84)))
    return outline(im)


def icon_pamphlet():
    im = canvas(ICON_W, ICON_H)
    d = ImageDraw.Draw(im)
    d.polygon([(10, 6), (36, 2), (40, 34), (14, 38)], fill=rgba((250, 246, 230)))
    d.line([(14, 10), (34, 7)], fill=rgba((200, 60, 50)), width=2)
    for k in range(5):
        d.line([(15, 15 + k * 4), (35, 12 + k * 4)], fill=rgba((110, 110, 120)))
    d.ellipse([28, 26, 36, 32], fill=rgba((250, 222, 140)))
    return outline(im)


def icon_pendant():
    im = canvas(ICON_W, ICON_H)
    d = ImageDraw.Draw(im)
    d.arc([8, -6, 40, 22], 20, 160, fill=rgba((150, 130, 180)), width=2)
    d.polygon([(24, 16), (32, 25), (24, 38), (16, 25)], fill=rgba((170, 100, 240)))
    d.polygon([(24, 16), (28, 25), (24, 38)], fill=rgba((200, 150, 255)))
    d.point((21, 23), fill=rgba((250, 240, 255)))
    return outline(im)


def icon_rigatone(sauced=False):
    im = canvas(ICON_W, ICON_H)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([6, 14, 40, 30], 6, fill=rgba((250, 206, 70)))
    for x in range(10, 38, 4):
        d.line([(x, 15), (x, 29)], fill=rgba((214, 160, 40)))
    d.ellipse([34, 14, 42, 30], fill=rgba((150, 100, 30)))
    d.ellipse([36, 17, 40, 27], fill=rgba((90, 60, 20)))
    if sauced:
        d.polygon([(8, 14), (36, 14), (34, 20), (28, 18), (22, 23), (16, 18), (10, 21)], fill=rgba((200, 40, 30)))
        d.ellipse([20, 22, 24, 27], fill=rgba((200, 40, 30)))
        d.point((14, 16), fill=rgba((255, 140, 120)))
    return outline(im)


def icon_token():
    im = canvas(ICON_W, ICON_H)
    d = ImageDraw.Draw(im)
    d.ellipse([12, 6, 36, 34], fill=rgba((200, 160, 60)))
    d.ellipse([14, 8, 34, 32], fill=rgba((240, 200, 90)))
    d.ellipse([18, 12, 30, 28], fill=rgba((220, 180, 70)))
    text(d, (24, 20), 'FSM', 7, (150, 110, 40), anchor='mm')
    return outline(im)


def icon_whipit():
    """A whip-it: a small steel cream charger."""
    im = canvas(ICON_W, ICON_H)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([10, 13, 34, 27], 7, fill=rgba((176, 182, 194)))
    d.polygon([(34, 15), (40, 18), (40, 22), (34, 25)], fill=rgba((150, 156, 168)))
    d.rectangle([40, 18, 43, 22], fill=rgba((120, 126, 138)))
    d.line([(14, 16), (31, 16)], fill=rgba((236, 240, 248)), width=2)
    d.line([(14, 24), (31, 24)], fill=rgba((120, 126, 138)))
    return outline(im)


ICONS = {
    'iBeads': ('pasta rosary beads', icon_beads),
    'iPamphlet': ('pamphlet', icon_pamphlet),
    'iPendant': ('UV pendant', icon_pendant),
    'iRigatone': ('golden rigatone', lambda: icon_rigatone(False)),
    'iSauced': ('sauced rigatone', lambda: icon_rigatone(True)),
    'iToken': ('arcade token', icon_token),
    'iWhipit': ('whip-it canister', icon_whipit),
}
