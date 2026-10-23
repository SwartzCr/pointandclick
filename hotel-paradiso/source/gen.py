"""Builds the ScummGEN game folder for "Hotel Paradiso" (a one-room SCUMM v6 adventure).

Run:  python3 gen.py <outdir>
Then: scummgen <outdir>/   (writes tentacle.000 / tentacle.001 into the cwd)
"""
import os
import shutil
import struct
import sys
from xml.sax.saxutils import escape

from PIL import Image

import art

OUT = sys.argv[1] if len(sys.argv) > 1 else 'game'
HERE = os.path.dirname(os.path.abspath(__file__))
MAGENTA = (255, 0, 255)


# --------------------------------------------------------------------------- helpers
def write_bmp(path, pixels, width, height, palette, bpp=8):
    """Indexed BMP exactly as ScummGEN's reader expects: 40-byte header, palette
    right after it, bottom-up rows padded to 32 bits, nColors filled in."""
    ncol = len(palette)
    row_bits = width * bpp
    row_bytes = ((row_bits + 31) // 32) * 4
    data = bytearray()
    for y in range(height - 1, -1, -1):
        row = bytearray(row_bytes)
        for x in range(width):
            v = pixels[y * width + x]
            bit = x * bpp
            byte_i, shift = bit // 8, 8 - bpp - (bit % 8)
            row[byte_i] |= (v & ((1 << bpp) - 1)) << shift
        data += row
    pal = b''.join(struct.pack('<BBBB', b, g, r, 0) for (r, g, b) in palette)
    off = 14 + 40 + len(pal)
    hdr = struct.pack('<2sIHHI', b'BM', off + len(data), 0, 0, off)
    info = struct.pack('<IiiHHIIiiII', 40, width, height, 1, bpp, 0, len(data), 2835, 2835, ncol, 0)
    with open(path, 'wb') as f:
        f.write(hdr + info + pal + data)


def save_indexed(path, img, transparent=None):
    """Save an RGB image as 8-bit BMP. If `transparent` is given that colour is
    forced to palette index 0."""
    w, h = img.size
    px = list(img.getdata())
    colors = []
    if transparent is not None:
        colors.append(transparent)
    for c in px:
        if c not in colors:
            colors.append(c)
    assert len(colors) <= 256, (path, len(colors))
    idx = {c: i for i, c in enumerate(colors)}
    write_bmp(path, [idx[c] for c in px], w, h, colors, 8)


def xml(path, root, body):
    def emit(v, ind):
        out = []
        for k, val in v:
            if isinstance(val, list):
                out.append(f'{ind}<{k}>')
                out += emit(val, ind + '  ')
                out.append(f'{ind}</{k}>')
            else:
                if isinstance(val, bool):
                    val = 'true' if val else 'false'
                out.append(f'{ind}<{k}>{escape(str(val))}</{k}>')
        return out
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write('\n'.join([f'<{root}>'] + emit(body, '  ') + [f'</{root}>']) + '\n')


def script_dir(path, name, src_file):
    os.makedirs(path, exist_ok=True)
    shutil.copy(os.path.join(HERE, 'scripts', src_file), os.path.join(path, src_file))
    xml(os.path.join(path, 'script.xml'), 'script', [('name', name), ('scriptName', src_file)])


def palette_xml(path, transparent):
    xml(os.path.join(path, 'palette.xml'), 'palette', [('transparent', transparent)])


def image_dir(path, name, img, transparent=None):
    os.makedirs(path, exist_ok=True)
    save_indexed(os.path.join(path, name + '.bmp'), img, transparent)
    xml(os.path.join(path, 'image.xml'), 'image', [('name', name), ('bitmapName', name + '.bmp')])


# --------------------------------------------------------------------------- charset
def build_charset(path):
    """Proportional font with a baked drop shadow, from font8x8 (public domain).
    Pixel value 1 = text colour, 2 = shadow colour (both set from scripts)."""
    glyphs = {}
    src = open(os.path.join(HERE, 'font8x8_basic.h')).read()
    rows = [l for l in src.splitlines() if l.strip().startswith('{ 0x')]
    for code, line in enumerate(rows):
        vals = [int(v, 16) for v in line.split('{')[1].split('}')[0].split(',')]
        glyphs[code] = vals
    chars = []
    cell_w, cell_h = 10, 9
    cols = 16
    sheet_w = cols * cell_w
    first, last = 32, 126
    n = last - first + 1
    sheet_h = ((n + cols - 1) // cols) * cell_h
    px = [0] * (sheet_w * sheet_h)
    for i, code in enumerate(range(first, last + 1)):
        g = glyphs[code]
        used = [x for x in range(8) for y in range(8) if g[y] >> x & 1]
        if code == 32:
            x0, x1 = 0, 2
        else:
            x0, x1 = min(used), max(used)
        width = (x1 - x0 + 1) + 2   # glyph + shadow column + spacing
        cx, cy = (i % cols) * cell_w, (i // cols) * cell_h
        for y in range(8):
            for x in range(8):
                if g[y] >> x & 1:
                    sx, sy = cx + (x - x0), cy + y
                    if px[(sy + 1) * sheet_w + sx + 1] == 0:
                        px[(sy + 1) * sheet_w + sx + 1] = 2
                    px[sy * sheet_w + sx] = 1
        chars.append(('char', [('id', code), ('x', cx), ('y', cy), ('width', width), ('height', cell_h),
                               ('xOffset', 0), ('yOffset', 0)]))
    os.makedirs(path, exist_ok=True)
    pal = [(0, 0, 0), (255, 255, 255), (40, 40, 40)] + [(0, 0, 0)] * 13
    write_bmp(os.path.join(path, 'font.bmp'), px, sheet_w, sheet_h, pal, 4)
    xml(os.path.join(path, 'charset.xml'), 'charset',
        [('name', 'font'), ('bitmapName', 'font.bmp'), ('fontHeight', cell_h)] + chars)


# --------------------------------------------------------------------------- costume
def build_costume(path):
    """The player: a guest in a bathrobe. All frames go on one sheet."""
    frames = [
        art.actor_front(0),          # 0 front stand
        art.actor_front(1),          # 1 front walk a
        art.actor_front(2),          # 2 front walk b
        art.actor_back(0),           # 3 back stand
        art.actor_back(1),           # 4 back walk a
        art.actor_back(2),           # 5 back walk b
        art.actor_side(0),           # 6 side stand
        art.actor_side(1),           # 7 side walk 1
        art.actor_side(2),           # 8 side walk 2
        art.actor_side(3),           # 9 side walk 3
        art.actor_front(0, True),    # 10 front talk
        art.actor_side(0, True),     # 11 side talk
    ]
    sheet = Image.new('RGB', (art.FW * len(frames), art.FH), MAGENTA)
    for i, f in enumerate(frames):
        sheet.paste(f, (i * art.FW, 0))
    os.makedirs(path, exist_ok=True)
    save_indexed(os.path.join(path, 'guest.bmp'), sheet, MAGENTA)
    palette_xml(path, True)

    def anim(name, loop, east, south, north):
        return ('anim', [('name', name), ('loop', loop),
                         ('west', [('command', c) for c in east]),
                         ('east', [('command', c) for c in east]),
                         ('south', [('command', c) for c in south]),
                         ('north', [('command', c) for c in north])])

    anims = [
        anim('none', False, [6], [0], [3]),
        anim('init', False, [6], [0], [3]),
        anim('walk', True, [7, 6, 9, 8], [1, 0, 2, 0], [4, 3, 5, 3]),
        anim('stand', False, [6], [0], [3]),
        anim('talkStart', True, [11, 6, 11, 11, 6], [10, 0, 10, 10, 0], [3]),
        anim('talkStop', False, [6], [0], [3]),
    ]
    frame_nodes = []
    for i in range(len(frames)):
        frame_nodes.append(('frame', [('bitmapName', 'guest.bmp'), ('x', i * art.FW), ('y', 0),
                                      ('width', art.FW), ('height', art.FH),
                                      ('xOffset', -art.FW // 2), ('yOffset', -art.FH)]))
    xml(os.path.join(path, 'costume.xml'), 'costume',
        [('name', 'guest'), ('mirror', True)] + anims + frame_nodes)


# --------------------------------------------------------------------------- room
# name, display name, rect (x, y, w, h), walk-to point, facing, state renders
OBJECTS = [
    ('door', 'door', (16, 16, 48, 80), (40, 104), 'north', [dict(door=1)]),
    ('tv', 'TV', (80, 16, 48, 48), (100, 104), 'north', [dict(tv=1)]),
    ('curtains', 'curtains', (128, 0, 72, 72), (164, 104), 'north', [dict(curtains=1)]),
    ('minibar', 'minibar', (144, 72, 32, 24), (132, 106), 'east', [dict(minibar=1), dict(minibar=2)]),
    ('lamp', 'lamp', (200, 32, 16, 40), (190, 108), 'east', [dict(lamp=1)]),
    ('phone', 'phone', (216, 56, 16, 16), (192, 108), 'east', []),
    ('nightstand', 'nightstand', (200, 72, 32, 24), (190, 108), 'east', [dict(drawer=1), dict(drawer=2)]),
    ('painting', 'painting', (248, 8, 48, 40), (230, 139), 'east', []),
    ('safe', 'wall safe', (248, 8, 48, 40), (230, 139), 'east', [dict(safe=1), dict(safe=2), dict(safe=3)]),
    ('bed', 'bed', (232, 48, 88, 88), (240, 139), 'east', []),
]


def build_room(path):
    os.makedirs(path, exist_ok=True)
    bg = art.render()
    image_dir(os.path.join(path, 'background'), 'background', bg)
    palette_xml(path, False)
    script_dir(os.path.join(path, 'script'), 'hotel', 'hotel.sgc')

    # walk boxes: open floor in front of the furniture, and a strip in front of the bed
    def box(name, ul, ur, lr, ll):
        return ('box', [('name', name), ('ulx', ul[0]), ('uly', ul[1]), ('urx', ur[0]), ('ury', ur[1]),
                        ('lrx', lr[0]), ('lry', lr[1]), ('llx', ll[0]), ('lly', ll[1]),
                        ('mask', 0), ('flags', 0), ('scale', 255)])
    xml(os.path.join(path, 'map.xml'), 'map', [
        box('floorBack', (10, 100), (230, 100), (230, 136), (8, 136)),
        box('floorFront', (8, 136), (312, 136), (312, 142), (6, 142)),
    ])

    obj_names = []
    for name, disp, (x, y, w, h), (hx, hy), facing, states in OBJECTS:
        assert x % 8 == 0 and w % 8 == 0 and y % 8 == 0 and h % 8 == 0, name
        opath = os.path.join(path, 'objects', name)
        os.makedirs(opath, exist_ok=True)
        imgs = []
        for i, st in enumerate(states):
            iname = f'state{i + 1}'
            crop = art.render(st).crop((x, y, x + w, y + h))
            image_dir(os.path.join(opath, iname), iname, crop)
            imgs.append(('image', iname))
        if imgs:
            palette_xml(opath, False)
        xml(os.path.join(opath, 'object.xml'), 'object',
            [('name', name), ('displayName', disp), ('hotspotX', hx), ('hotspotY', hy),
             ('x', x), ('y', y), ('width', w), ('height', h), ('actorDir', facing)] + imgs)
        obj_names.append(name)

    # mouse cursor lives in the room as an object image (never drawn on screen)
    opath = os.path.join(path, 'objects', 'cursor')
    image_dir(os.path.join(opath, 'state1'), 'state1', art.cursor_image(), MAGENTA)
    palette_xml(opath, True)
    xml(os.path.join(opath, 'object.xml'), 'object',
        [('name', 'cursor'), ('displayName', ''), ('hotspotX', 0), ('hotspotY', 0),
         ('x', 0), ('y', 0), ('width', 16), ('height', 16), ('actorDir', 'south'), ('image', 'state1')])
    obj_names.append('cursor')

    xml(os.path.join(path, 'room.xml'), 'room',
        [('name', 'hotel'), ('background', 'background'), ('script', 'script')] +
        [('object', n) for n in obj_names])


def main():
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    build_room(os.path.join(OUT, 'rooms', 'hotel'))
    build_charset(os.path.join(OUT, 'charsets', 'font'))
    build_costume(os.path.join(OUT, 'costumes', 'guest'))
    script_dir(os.path.join(OUT, 'scripts', 'main'), 'main', 'main.sgc')
    xml(os.path.join(OUT, 'game.xml'), 'game', [
        ('name', 'tentacle'),
        ('description', 'Hotel Paradiso - a one-room SCUMM adventure'),
        ('key', 105),
        ('room', 'hotel'),
        ('costume', 'guest'),
        ('script', 'main'),
        ('charset', 'font'),
    ])
    print('game folder written to', OUT)


if __name__ == '__main__':
    main()
