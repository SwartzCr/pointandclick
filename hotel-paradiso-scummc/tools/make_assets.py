#!/usr/bin/env python3
"""Generate every bitmap and data file the ScummC sources reference.

    python3 tools/make_assets.py [assets_dir]

Writes (all into assets/):
  room.bmp              320x144 background of Room 714, 8-bit; its palette IS the room palette
  bathroom.bmp          the bathroom background, same palette
  bathroom.box          the bathroom's walk boxes
  flush.voc             toilet flush sound, built into a SOUN resource by `soun`
  objects/<obj>_<n>.bmp state images for the objects (indices into the room palette)
  cursor.bmp            16x16 cursor, index 0 = transparent
  hotel.box             walk boxes (raw BOXD block; the matrix is built at runtime)
  font.bmp              bordered glyph sheet for ScummC's `char` tool
  guest/*.bmp           player costume frames (bathrobe), 16 local colours each
  guest.scost           costume description for ScummC's `cost` tool
  bellhop/*.bmp         the same frames in the bellhop uniform
  bellhop.scost

SCUMM v6 rooms have one 256-colour palette shared by the background, object
images and costumes. Indices 0..15 hold the EGA colours so scripts can use them
for text and verbs; everything drawn in tools/art.py is packed in after that.
"""
import os
import struct
import sys

from PIL import Image, ImageOps

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import art  # noqa: E402

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), '..', 'assets')
HERE = os.path.dirname(os.path.abspath(__file__))
MAGENTA = (255, 0, 255)

EGA = [(0, 0, 0), (0, 0, 171), (0, 171, 0), (0, 171, 171), (171, 0, 0), (171, 0, 171), (171, 87, 0),
       (171, 171, 171), (87, 87, 87), (87, 87, 255), (87, 255, 87), (87, 255, 255), (255, 87, 87),
       (255, 87, 255), (255, 255, 87), (255, 255, 255)]

# Object image states, cropped from art.render(). Must match the object
# declarations in src/hotel.scc (x, y, w, h).
OBJECT_STATES = {
    'door':       ((16, 16, 48, 80), [dict(door=1)]),
    'tv':         ((80, 16, 48, 48), [dict(tv=1)]),
    'curtains':   ((128, 0, 72, 72), [dict(curtains=1)]),
    'minibar':    ((144, 72, 32, 24), [dict(minibar=1), dict(minibar=2)]),
    'lamp':       ((200, 32, 16, 40), [dict(lamp=1)]),
    'nightstand': ((200, 72, 32, 24), [dict(drawer=1), dict(drawer=2)]),
    'safe':       ((248, 8, 48, 40), [dict(safe=1), dict(safe=2), dict(safe=3)]),
    'dresser':    ((72, 64, 56, 32), [dict(dresser=1), dict(dresser=2)]),
}
# items set down on the coffee table, one 16-pixel slot each
for _item in art.TABLE_SLOTS:
    OBJECT_STATES['table_' + _item] = ((art.table_slot_x(_item), 104, 16, 16), [{'table_' + _item: 1}])

# Bathroom object states, cropped from art.render_bathroom(). Must match the
# object declarations in src/bathroom.scc.
BATH_OBJECT_STATES = {
    'curtain': ((16, 8, 96, 72), [dict(curtain=1)]),
    'mirror':  ((192, 16, 32, 40), [dict(cabinet=1)]),
    'toilet':  ((128, 48, 40, 56), [dict(flush=1), dict(flush=2)]),
    'towel':   ((248, 32, 40, 40), [dict(towel=1)]),
    'soap':    ((184, 56, 16, 8), [dict(soap=1)]),
}

# Walk boxes (ul, ur, lr, ll). Box 0 is the engine's dummy box.
# The coffee table (x 112..208, y 105..128) is a hole in the floor. Boxes keep the
# player's feet half a sprite-width (12px) clear of it on the sides, so the
# player is never drawn over the table while standing behind its front edge.
BOXES = [
    ((10, 100), (230, 100), (230, 108), (8, 108)),     # behind the table
    ((8, 108), (100, 108), (100, 136), (8, 136)),      # left of the table
    ((220, 108), (230, 108), (230, 136), (220, 136)),  # right of the table
    ((100, 130), (220, 130), (220, 136), (100, 136)),  # in front of the table
    ((8, 136), (312, 136), (312, 142), (6, 142)),      # strip in front of the bed
]

# Bathroom: keep the player's feet in front of the tub (left) and free to walk
# right up to the toilet and sink.
BATH_BOXES = [
    ((8, 114), (116, 114), (116, 142), (6, 142)),      # in front of the tub
    ((116, 106), (304, 106), (312, 142), (116, 142)),  # toilet, sink, towel, door
]


def write_bmp(path, idx, w, h, palette, bpp=8):
    row_bytes = ((w * bpp + 31) // 32) * 4
    data = bytearray()
    for y in range(h - 1, -1, -1):
        row = bytearray(row_bytes)
        for x in range(w):
            bit = x * bpp
            row[bit // 8] |= (idx[y * w + x] & ((1 << bpp) - 1)) << (8 - bpp - bit % 8)
        data += row
    pal = b''.join(struct.pack('<BBBB', b, g, r, 0) for (r, g, b) in palette)
    off = 14 + 40 + len(pal)
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    with open(path, 'wb') as f:
        f.write(struct.pack('<2sIHHI', b'BM', off + len(data), 0, 0, off))
        f.write(struct.pack('<IiiHHIIiiII', 40, w, h, 1, bpp, 0, len(data), 2835, 2835, len(palette), len(palette)))
        f.write(pal + data)


def pixels(img):
    return list(img.get_flattened_data() if hasattr(img, 'get_flattened_data') else img.getdata())


class Palette:
    def __init__(self):
        self.colors = list(EGA)
        self.index = {}

    def add(self, c):
        if c not in self.index:
            self.index[c] = len(self.colors)
            self.colors.append(c)
            assert len(self.colors) <= 256, 'room palette overflow'
        return self.index[c]

    def full(self):
        return self.colors + [(0, 0, 0)] * (256 - len(self.colors))


def actor_frames(outfit):
    """Every costume picture, keyed by its name in the .scost. West = mirrored east."""
    o = outfit
    f = {
        'standS': art.actor_front(0, outfit=o), 'walkS1': art.actor_front(1, outfit=o),
        'walkS2': art.actor_front(2, outfit=o),
        'standN': art.actor_back(0, outfit=o), 'walkN1': art.actor_back(1, outfit=o),
        'walkN2': art.actor_back(2, outfit=o),
        'standE': art.actor_side(0, outfit=o), 'walkE1': art.actor_side(1, outfit=o),
        'walkE2': art.actor_side(2, outfit=o), 'walkE3': art.actor_side(3, outfit=o),
        'talkS': art.actor_front(0, True, outfit=o), 'talkE': art.actor_side(0, True, outfit=o),
    }
    for k in [k for k in f if k.endswith('E') or k[-2] == 'E']:
        f[k.replace('E', 'W')] = ImageOps.mirror(f[k])
    return f


SCOST = """/* Generated by tools/make_assets.py - the player: {title}.
 * Picture pixels are local colours 0..15 (0 = transparent); palette() maps
 * them onto room palette indices. */
palette({palette});

{pictures}

limb body;

anim init = {{
    E = {{ body(standE) }}; W = {{ body(standW) }};
    S = {{ body(standS) }}; N = {{ body(standN) }};
}};

anim walk = {{
    E = {{ body(walkE1, standE, walkE3, walkE2) }};
    W = {{ body(walkW1, standW, walkW3, walkW2) }};
    S = {{ body(walkS1, standS, walkS2, standS) }};
    N = {{ body(walkN1, standN, walkN2, standN) }};
}};

anim stand = {{
    E = {{ body(standE) }}; W = {{ body(standW) }};
    S = {{ body(standS) }}; N = {{ body(standN) }};
}};

anim talkStart = {{
    E = {{ body(talkE, standE, talkE, talkE, standE) }};
    W = {{ body(talkW, standW, talkW, talkW, standW) }};
    S = {{ body(talkS, standS, talkS, talkS, standS) }};
    N = {{ body(standN) }};
}};

anim talkStop = {{
    E = {{ body(standE) }}; W = {{ body(standW) }};
    S = {{ body(standS) }}; N = {{ body(standN) }};
}};
"""


def build_costume(pal, name, outfit, title):
    frames = actor_frames(outfit)
    local = [MAGENTA]
    for im in frames.values():
        for c in pixels(im):
            if c not in local:
                local.append(c)
    assert len(local) <= 16, len(local)
    local += [(0, 0, 0)] * (16 - len(local))
    room_idx = [0] + [pal.add(c) for c in local[1:]]
    lidx = {c: i for i, c in enumerate(local)}
    pics = []
    for pic, im in frames.items():
        write_bmp(os.path.join(OUT, name, pic + '.bmp'), [lidx[c] for c in pixels(im)],
                  art.FW, art.FH, local, 8)
        pics.append(f'picture {pic} = {{\n    path = "{name}/{pic}.bmp",\n'
                    f'    position = {{ {-art.FW // 2}, {-art.FH} }}\n}};')
    with open(os.path.join(OUT, name + '.scost'), 'w') as f:
        f.write(SCOST.format(title=title, palette=', '.join(map(str, room_idx)),
                             pictures='\n\n'.join(pics)))


def build_font():
    """Bordered glyph sheet: each glyph sits in a 1px box of the last palette
    colour; glyphs are read left to right, top to bottom, starting at ' '."""
    rows = [l for l in open(os.path.join(HERE, 'font8x8_basic.h')).read().splitlines()
            if l.strip().startswith('{ 0x')]
    glyphs = [[int(v, 16) for v in r.split('{')[1].split('}')[0].split(',')] for r in rows]
    gh = 9                    # 8 rows + drop shadow
    per_row, sheet_w = 24, 24 * 13
    codes = list(range(32, 127))
    nrows = (len(codes) + per_row - 1) // per_row
    sheet_h = 1 + nrows * (gh + 3)
    px = [0] * (sheet_w * sheet_h)
    BORDER = 3
    for i, code in enumerate(codes):
        g = glyphs[code]
        used = [x for x in range(8) for y in range(8) if g[y] >> x & 1]
        x0, x1 = (0, 2) if code == 32 else (min(used), max(used))
        gw = (x1 - x0 + 1) + 2            # glyph + shadow column + spacing
        bx, by = (i % per_row) * 13, 1 + (i // per_row) * (gh + 3)
        for x in range(bx, bx + gw + 2):
            px[by * sheet_w + x] = BORDER
            px[(by + gh + 1) * sheet_w + x] = BORDER
        for y in range(by, by + gh + 2):
            px[y * sheet_w + bx] = BORDER
            px[y * sheet_w + bx + gw + 1] = BORDER
        for y in range(8):
            for x in range(8):
                if g[y] >> x & 1:
                    sx, sy = bx + 1 + (x - x0), by + 1 + y
                    if px[(sy + 1) * sheet_w + sx + 1] == 0:
                        px[(sy + 1) * sheet_w + sx + 1] = 2
                    px[sy * sheet_w + sx] = 1
    write_bmp(os.path.join(OUT, 'font.bmp'), px, sheet_w, sheet_h,
              [(0, 0, 0), (255, 255, 255), (40, 40, 40), (255, 0, 255)], 8)


def build_boxes(name, boxes):
    def box(ul, ur, lr, ll, scale=255):
        return struct.pack('<8hBBH', *ul, *ur, *lr, *ll, 0, 0, scale)
    body = struct.pack('<H', len(boxes) + 1) + box(*[(-32000, -32000)] * 4)
    body += b''.join(box(*b) for b in boxes)
    with open(os.path.join(OUT, name), 'wb') as f:
        f.write(b'BOXD' + struct.pack('>I', 8 + len(body)) + body)


def build_flush_sound():
    """A toilet flush: filtered noise that swells, gurgles and drains away.
    8-bit unsigned PCM at 11025 Hz in a Creative Voice File, for `soun -voc`."""
    import math
    import random
    rnd = random.Random(714)
    rate = 11025
    n = int(rate * 1.6)
    samples, lp, lp2 = [], 0.0, 0.0
    for i in range(n):
        t = i / rate
        env = min(1.0, t / 0.08) * (1.0 if t < 0.7 else max(0.0, 1 - (t - 0.7) / 0.9))
        lp += 0.25 * (rnd.uniform(-1, 1) - lp)            # rushing water
        lp2 += 0.04 * (rnd.uniform(-1, 1) - lp2)          # low rumble
        gurgle = math.sin(2 * math.pi * (180 + 60 * math.sin(t * 9)) * t) * (0.25 if t > 0.9 else 0)
        v = env * (0.9 * lp + 1.6 * lp2 + gurgle * env)
        samples.append(max(0, min(255, int(128 + 100 * v))))
    data = bytes(samples)
    rate_byte = 256 - 1000000 // rate
    block = bytes([1]) + struct.pack('<I', len(data) + 2)[:3] + bytes([rate_byte, 0]) + data
    hdr = b'Creative Voice File\x1a' + struct.pack('<HHH', 26, 0x010A, 0x1129)
    with open(os.path.join(OUT, 'flush.voc'), 'wb') as f:
        f.write(hdr + block + bytes([0]))


def main():
    os.makedirs(os.path.join(OUT, 'objects'), exist_ok=True)
    pal = Palette()
    bg = art.render()
    bath = art.render_bathroom()
    crops = {}
    for name, ((x, y, w, h), states) in OBJECT_STATES.items():
        assert x % 8 == 0 and w % 8 == 0, name
        crops[name] = [art.render(st).crop((x, y, x + w, y + h)) for st in states]
    for name, ((x, y, w, h), states) in BATH_OBJECT_STATES.items():
        assert x % 8 == 0 and w % 8 == 0 and y % 8 == 0 and h % 8 == 0, name
        crops['bath_' + name] = [art.render_bathroom(st).crop((x, y, x + w, y + h)) for st in states]
    # Both rooms share one palette, so the costumes look the same in each
    for c in pixels(bg) + pixels(bath):
        pal.add(c)
    for ims in crops.values():
        for im in ims:
            for c in pixels(im):
                pal.add(c)
    cursor = art.cursor_image()
    for c in pixels(cursor):
        if c != MAGENTA:
            pal.add(c)
    build_costume(pal, 'guest', 'robe', 'a guest in a bathrobe')
    build_costume(pal, 'bellhop', 'bellhop', 'the same guest in the bellhop uniform')

    full = pal.full()
    write_bmp(os.path.join(OUT, 'room.bmp'), [pal.index[c] for c in pixels(bg)], art.W, art.H, full)
    write_bmp(os.path.join(OUT, 'bathroom.bmp'), [pal.index[c] for c in pixels(bath)], art.W, art.H, full)
    for name, ims in crops.items():
        for i, im in enumerate(ims):
            write_bmp(os.path.join(OUT, 'objects', f'{name}_{i + 1}.bmp'),
                      [pal.index[c] for c in pixels(im)], im.width, im.height, full)
    write_bmp(os.path.join(OUT, 'cursor.bmp'),
              [0 if c == MAGENTA else pal.index[c] for c in pixels(cursor)], 16, 16, full)
    build_font()
    build_boxes('hotel.box', BOXES)
    build_boxes('bathroom.box', BATH_BOXES)
    build_flush_sound()
    print(f'assets written to {os.path.normpath(OUT)} ({len(pal.colors)} palette entries used)')


if __name__ == '__main__':
    main()
