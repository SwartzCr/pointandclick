"""A 'screenshot' of Hotel Paradiso (the first game) on the Crypt's Classic Computer.

Drawn with Hotel Paradiso's own art code (hotel-paradiso-scummc/tools/art.py):
Room 714 with the guest in his bathrobe, under a SCUMM-style verb bar, shown on
a beige monitor that fills the screen.
"""
import os
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
HP = os.path.join(HERE, '..', '..', 'hotel-paradiso-scummc', 'tools')


def _hp_art():
    sys.path.insert(0, HP)
    try:
        import importlib
        return importlib.import_module('art')
    finally:
        sys.path.remove(HP)


def game_frame():
    """320x200: the room, the guest, a sentence line and the verbs, as in Hotel Paradiso."""
    art = _hp_art()
    room = art.render()
    guest = art.actor_front(outfit='robe').convert('RGBA')
    a = np.asarray(guest).copy()
    mag = (a[..., 0] == 255) & (a[..., 1] == 0) & (a[..., 2] == 255)
    a[mag, 3] = 0
    guest = Image.fromarray(a, 'RGBA')
    img = Image.new('RGB', (320, 200), (0, 0, 0))
    img.paste(room, (0, 0))
    img.paste(guest, (150, 136 - guest.height), guest)
    d = ImageDraw.Draw(img)
    f = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf', 8)
    d.text((160, 150), 'Walk to', font=f, fill=(90, 220, 220), anchor='mm')
    verbs = [['Open', 'Pick up', 'Push'], ['Close', 'Look at', 'Pull'], ['Talk to', 'Use', 'Walk to']]
    for r, row in enumerate(verbs):
        for c, v in enumerate(row):
            d.text((8 + c * 52, 160 + r * 12), v, font=f, fill=(40, 160, 160))
    for n in range(8):
        x, y = 168 + (n % 4) * 37, 158 + (n // 4) * 20
        d.rectangle([x, y, x + 34, y + 17], fill=(28, 20, 40))
    return img


def screen(w=640, h=400):
    """The monitor: a beige CRT bezel round the game frame, on a dark desk."""
    im = Image.new('RGBA', (w, h), (14, 10, 18, 255))
    d = ImageDraw.Draw(im)
    bx0, by0, bx1, by1 = 70, 14, 570, 370
    d.rounded_rectangle([bx0, by0, bx1, by1], 22, fill=(214, 204, 172, 255), outline=(120, 110, 90, 255), width=3)
    d.rounded_rectangle([bx0 + 14, by0 + 12, bx1 - 14, by1 - 40], 16, fill=(40, 38, 34, 255))
    sx0, sy0 = 92, 24
    frame = game_frame().resize((456, 285), Image.NEAREST)
    # a little CRT: scanlines and a green-ish glass tint
    fa = np.asarray(frame).astype(float)
    fa[1::2] *= 0.78
    fa = fa * np.array([0.95, 1.0, 0.95])
    frame = Image.fromarray(np.clip(fa, 0, 255).astype(np.uint8)).convert('RGBA')
    im.alpha_composite(frame, (sx0, sy0))
    d.rounded_rectangle([sx0, sy0, sx0 + 455, sy0 + 284], 10, outline=(26, 24, 22, 255), width=4)
    d.text((bx0 + 30, by1 - 26), 'PASTA-PC 386', fill=(110, 100, 80, 255))
    d.ellipse([bx1 - 50, by1 - 30, bx1 - 38, by1 - 18], fill=(80, 220, 90, 255))
    d.rectangle([250, by1, 390, by1 + 14], fill=(190, 180, 150, 255))
    return im


if __name__ == '__main__':
    screen().save('/tmp/claude-0/nb/hp_screen.png')
