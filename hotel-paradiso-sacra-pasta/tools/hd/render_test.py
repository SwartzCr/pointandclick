"""Renders the Nave test at 1280x800 and 640x400 (with characters and the
interface), plus a side-by-side of the two at the same screen size.

    python3 render_test.py [outdir]
"""
import os
import sys
import time
from PIL import Image, ImageDraw
import shade
import nave
import people

OUT = sys.argv[1] if len(sys.argv) > 1 else '/tmp/claude-0'


def place(bg, spr, x, y):
    """Feet at design point (x, y)."""
    s = shade.S
    sh = Image.new('RGBA', bg.size, (0, 0, 0, 0))
    w = 64
    ImageDraw.Draw(sh).ellipse([(x - w / 2 + 10) * s, (y - 8) * s, (x + w / 2 + 16) * s, (y + 6) * s],
                               fill=(50, 20, 60, 100))
    bg.alpha_composite(sh)
    bg.alpha_composite(spr, (int(x * s - spr.width / 2), int(y * s - spr.height)))


renders = {}
for scale in (1.0, 0.5):
    t = time.time()
    shade.set_scale(scale)
    room = nave.nave()
    place(room, people.khuc(), 1136, 452)
    place(room, people.guest(talk=True), 820, 566)
    nave.interface(room)
    w, h = room.size
    path = os.path.join(OUT, 'nave_cel_%dx%d.png' % (w, h))
    room.save(path)
    renders[scale] = room
    print(path, '%.1fs' % (time.time() - t))

# both at the same displayed size: the 640x400 one doubled with square pixels
lo = renders[0.5].resize((1280, 800), Image.NEAREST)
cmp_ = Image.new('RGBA', (1280 * 2 + 20, 800), (20, 14, 24, 255))
cmp_.alpha_composite(lo, (0, 0))
cmp_.alpha_composite(renders[1.0], (1300, 0))
cmp_.save(os.path.join(OUT, 'nave_cel_compare.png'))
