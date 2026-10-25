#!/usr/bin/env python3
"""Generate every bitmap and data file the ScummC sources reference.

    python3 tools/make_assets.py [assets_dir]

Writes (all into assets/):
  room.bmp              320x144 background of Room 714, 8-bit; its palette IS the room palette
  bathroom.bmp          the bathroom background, same palette
  bathroom.box          the bathroom's walk boxes
  flush.voc, tv.voc,    sound effects (toilet flush, TV chatter, keypad safe opening),
  safe.voc              built into SOUN resources by `soun`
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
    'safe':       ((248, 8, 48, 40), [dict(safe=i) for i in range(1, 6)]),
    'dresser':    ((72, 64, 56, 32), [dict(dresser=1), dict(dresser=2)]),
    'bed':        ((232, 48, 88, 88), [dict(bed=1), dict(bed=2)]),
}
# things set down on the coffee table, one slot each
# (the mirror has six: bare, with the powder, then three, two, one and no lines)
for _item, (_x, _w) in art.TABLE_SLOTS.items():
    _n = 6 if _item == 'mirror' else 1
    OBJECT_STATES['table_' + _item] = ((_x, 104, _w, 16),
                                       [{'table_' + _item: i} for i in range(1, _n + 1)])

# Bathroom object states, cropped from art.render_bathroom(). Must match the
# object declarations in src/bathroom.scc.
BATH_OBJECT_STATES = {
    'curtain': ((16, 8, 96, 72), [dict(curtain=1)]),
    'mirror':  ((192, 16, 32, 40), [dict(cabinet=i) for i in range(1, 5)]),
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
        'carriedE': art.actor_lying(o),
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
{extra}"""

# Extra animations for the player: lying flat, carried overhead by clowns
PLAYER_EXTRA = """
anim carried = {
    E = { body(carriedE) }; W = { body(carriedW) };
    S = { body(carriedE) }; N = { body(carriedW) };
};
"""

# Extra animations for the clowns: walking and standing with their arms up,
# holding the player overhead
CLOWN_EXTRA = """
anim carryWalk = {
    E = { body(upWalkE1, upE, upWalkE3, upWalkE2) };
    W = { body(upWalkW1, upW, upWalkW3, upWalkW2) };
    S = { body(upWalkS1, upS, upWalkS2, upS) };
    N = { body(upWalkN1, upN, upWalkN2, upN) };
};

anim carryStand = {
    E = { body(upE) }; W = { body(upW) };
    S = { body(upS) }; N = { body(upN) };
};
"""


def clown_frames(name):
    n = name
    f = {
        'standS': art.clown_front(n, 0), 'walkS1': art.clown_front(n, 1), 'walkS2': art.clown_front(n, 2),
        'standN': art.clown_back(n, 0), 'walkN1': art.clown_back(n, 1), 'walkN2': art.clown_back(n, 2),
        'standE': art.clown_side(n, 0), 'walkE1': art.clown_side(n, 1),
        'walkE2': art.clown_side(n, 2), 'walkE3': art.clown_side(n, 3),
        'talkS': art.clown_front(n, 0, talk=True), 'talkE': art.clown_side(n, 0, talk=True),
        'upS': art.clown_front(n, 0, True), 'upWalkS1': art.clown_front(n, 1, True),
        'upWalkS2': art.clown_front(n, 2, True),
        'upN': art.clown_back(n, 0, True), 'upWalkN1': art.clown_back(n, 1, True),
        'upWalkN2': art.clown_back(n, 2, True),
        'upE': art.clown_side(n, 0, True), 'upWalkE1': art.clown_side(n, 1, True),
        'upWalkE2': art.clown_side(n, 2, True), 'upWalkE3': art.clown_side(n, 3, True),
    }
    for k in [k for k in f if 'E' in k]:
        f[k.replace('E', 'W')] = ImageOps.mirror(f[k])
    return f


def build_costume(pal, name, outfit, title, frames=None, extra=PLAYER_EXTRA):
    if frames is None:
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
                  im.width, im.height, local, 8)
        pics.append(f'picture {pic} = {{\n    path = "{name}/{pic}.bmp",\n'
                    f'    position = {{ {-im.width // 2}, {-im.height} }}\n}};')
    with open(os.path.join(OUT, name + '.scost'), 'w') as f:
        f.write(SCOST.format(title=title, palette=', '.join(map(str, room_idx)),
                             pictures='\n\n'.join(pics), extra=extra))


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


# --------------------------------------------------------------------------- sound
# Sound effects are synthesized here, pure Python (no numpy), and written as
# 8-bit unsigned PCM at 11025 Hz in Creative Voice Files for ScummC's `soun -voc`.
RATE = 11025


def write_voc(name, samples):
    """samples: floats in -1..1."""
    data = bytes(max(0, min(255, int(round(128 + 127 * v)))) for v in samples)
    rate_byte = 256 - 1000000 // RATE
    block = bytes([1]) + struct.pack('<I', len(data) + 2)[:3] + bytes([rate_byte, 0]) + data
    hdr = b'Creative Voice File\x1a' + struct.pack('<HHH', 26, 0x010A, 0x1129)
    with open(os.path.join(OUT, name + '.voc'), 'wb') as f:
        f.write(hdr + block + bytes([0]))


class Resonator:
    """Two-pole band-pass resonator: rings at `freq` and dies away at rate `r`."""
    def __init__(self, freq, r):
        import math
        self.a1 = 2 * r * math.cos(2 * math.pi * freq / RATE)
        self.a2 = -r * r
        self.gain = 1 - r
        self.y1 = self.y2 = 0.0

    def __call__(self, x):
        y = self.gain * x + self.a1 * self.y1 + self.a2 * self.y2
        self.y2, self.y1 = self.y1, y
        return y


def normalize(samples, peak=0.9):
    m = max(abs(v) for v in samples) or 1.0
    return [v * peak / m for v in samples]


def build_flush_sound():
    """A toilet flush: filtered noise that swells, gurgles and drains away."""
    import math
    import random
    rnd = random.Random(714)
    n = int(RATE * 1.6)
    out, lp, lp2 = [], 0.0, 0.0
    for i in range(n):
        t = i / RATE
        env = min(1.0, t / 0.08) * (1.0 if t < 0.7 else max(0.0, 1 - (t - 0.7) / 0.9))
        lp += 0.25 * (rnd.uniform(-1, 1) - lp)            # rushing water
        lp2 += 0.04 * (rnd.uniform(-1, 1) - lp2)          # low rumble
        gurgle = math.sin(2 * math.pi * (180 + 60 * math.sin(t * 9)) * t) * (0.25 if t > 0.9 else 0)
        out.append(env * (0.9 * lp + 1.6 * lp2 + gurgle * env) * 100 / 127)
    write_voc('flush', out)


def build_tv_sound():
    """Two seconds of indistinct TV chatter: a few voices babbling in made-up
    syllables (a pitched buzz shaped by vowel formants), squeezed through a
    small TV speaker with a little hiss."""
    import math
    import random
    rnd = random.Random(1987)
    n = int(RATE * 2.0)
    mix = [0.0] * n
    vowels = [(730, 1090), (530, 1840), (270, 2290), (570, 840), (440, 1020), (660, 1720), (300, 870)]
    for pitch, level, start in ((118, 1.0, 0.0), (186, 0.6, 0.35), (152, 0.45, 0.9)):
        i = int(start * RATE)
        phase = 0.0
        while i < n:
            # one word of 1-3 syllables, then a pause
            for _ in range(rnd.randint(1, 3)):
                dur = int(RATE * rnd.uniform(0.07, 0.17))
                f1, f2 = rnd.choice(vowels)
                r1, r2 = Resonator(f1, 0.97), Resonator(f2, 0.96)
                fric = rnd.random() < 0.35
                lift = rnd.uniform(-0.15, 0.2)
                for k in range(dur):
                    if i >= n:
                        break
                    u = k / dur
                    env = math.sin(math.pi * u) ** 0.6
                    f0 = pitch * (1 + lift * (1 - u) + 0.04 * math.sin(i / 200))
                    phase = (phase + f0 / RATE) % 1.0
                    src = 2 * phase - 1                         # buzzy glottal source
                    v = r1(src) * 1.4 + r2(src) * 0.9
                    if fric and u < 0.3:                        # "s"/"t" at the start
                        v += rnd.uniform(-1, 1) * 0.25 * (1 - u / 0.3)
                    mix[i] += v * env * level
                    i += 1
                i += int(RATE * rnd.uniform(0.01, 0.05))
            i += int(RATE * rnd.uniform(0.08, 0.22))
    # small speaker: high-pass the boom out, low-pass the edge off, add hiss
    out, hp_x, hp_y, lp = [], 0.0, 0.0, 0.0
    for i, x in enumerate(mix):
        hp_y = 0.93 * (hp_y + x - hp_x)
        hp_x = x
        lp += 0.55 * (hp_y - lp)
        v = math.tanh(lp * 1.3) + rnd.uniform(-1, 1) * 0.03
        t = i / RATE
        v *= min(1.0, t / 0.06) * min(1.0, (2.0 - t) / 0.2)
        out.append(v)
    write_voc('tv', normalize(out, 0.85))


class LowPass:
    def __init__(self, a):
        self.a, self.y = a, 0.0

    def __call__(self, x):
        self.y += self.a * (x - self.y)
        return self.y


def _add(out, t0, gen):
    i0 = int(t0 * RATE)
    for k, v in enumerate(gen):
        if 0 <= i0 + k < len(out):
            out[i0 + k] += v


def _tick(rnd, level, freq=2600, ms=14):
    """A small dry mechanical tick: a 2ms noise burst through a quickly damped filter."""
    import math  # noqa: F401
    rz, n = Resonator(freq, 0.94), int(RATE * ms / 1000)
    for k in range(n):
        x = rnd.uniform(-1, 1) if k < 22 else 0.0
        yield level * rz(x) * 14 * (1 - k / n)


def _thud(rnd, level, freq=95, ms=180):
    """A heavy low impact: a decaying sine with a burst of muffled noise."""
    import math
    lp, n = LowPass(0.08), int(RATE * ms / 1000)
    for k in range(n):
        t = k / RATE
        env = math.exp(-t * 26)
        yield level * env * (math.sin(2 * math.pi * freq * t) + 1.5 * lp(rnd.uniform(-1, 1)) * math.exp(-t * 60))


def _tone(freq, ms, level, square=False):
    import math
    n = int(RATE * ms / 1000)
    for k in range(n):
        v = math.sin(2 * math.pi * freq * k / RATE)
        if square:
            v = math.copysign(min(1.0, abs(v) * 3), v)
        env = min(1.0, k / 40) * min(1.0, (n - k) / 80)
        yield level * v * env


def build_safe_sound():
    """The safe opening, as an electronic hotel safe: three keypad beeps (7, 1,
    4), an "accepted" chime, a motor driving the bolt back into a clunk, then a
    soft puff of air as the door springs open (at about 1.4s)."""
    import math
    import random
    rnd = random.Random(2)
    out = [0.0] * int(RATE * 2.0)
    # three key presses, each a short beep with a soft button click
    for t0, f in ((0.04, 1336), (0.26, 1209), (0.48, 1336)):
        _add(out, t0, _tick(rnd, 0.25, freq=3000, ms=8))
        _add(out, t0 + 0.01, _tone(f, 95, 0.35, square=True))
    # accepted: a rising two-note chime
    _add(out, 0.70, _tone(1046, 85, 0.35))
    _add(out, 0.79, _tone(1568, 140, 0.35))
    # the motor drives the bolt back: a whirr that winds up and stops
    lp = LowPass(0.25)
    i0, i1 = int(0.98 * RATE), int(1.30 * RATE)
    phase, phase2 = 0.0, 0.0
    for i in range(i0, i1):
        u = (i - i0) / (i1 - i0)
        phase = (phase + (95 + 40 * u) / RATE) % 1.0
        phase2 = (phase2 + (620 + 300 * u) / RATE) % 1.0
        whine = math.sin(2 * math.pi * phase2) * 0.35
        buzz = lp(2 * phase - 1)
        env = min(1.0, u / 0.1) * min(1.0, (1 - u) / 0.08)
        out[i] += env * 0.55 * (buzz + whine) * (0.8 + 0.2 * math.sin(2 * math.pi * 38 * i / RATE))
    _add(out, 1.30, _thud(rnd, 0.7, freq=140, ms=120))      # bolt hits its stop
    _add(out, 1.30, _tick(rnd, 0.5, freq=1200, ms=40))
    # the door pops open on its spring: a soft puff of air
    lp_air = LowPass(0.06)
    i0, i1 = int(1.42 * RATE), int(1.85 * RATE)
    for i in range(i0, i1):
        u = (i - i0) / (i1 - i0)
        out[i] += 0.9 * math.exp(-u * 5) * min(1.0, u / 0.05) * lp_air(rnd.uniform(-1, 1)) * 4
    write_voc('safe', normalize(out, 0.9))


def main():
    os.makedirs(os.path.join(OUT, 'objects'), exist_ok=True)
    pal = Palette()
    bg = art.render()
    bath = art.render_bathroom()
    title = art.render_title()
    gameover = art.render_gameover()
    crops = {}
    for name, ((x, y, w, h), states) in OBJECT_STATES.items():
        assert x % 8 == 0 and w % 8 == 0, name
        crops[name] = [art.render(st).crop((x, y, x + w, y + h)) for st in states]
    # the game-over screen's spinning room: frame 0 is the background, the
    # rest are the full-screen states of its "spinner" object
    crops['gameover_spin'] = [art.render_gameover(f) for f in range(1, art.GAMEOVER_FRAMES)]
    for name, ((x, y, w, h), states) in BATH_OBJECT_STATES.items():
        assert x % 8 == 0 and w % 8 == 0 and y % 8 == 0 and h % 8 == 0, name
        crops['bath_' + name] = [art.render_bathroom(st).crop((x, y, x + w, y + h)) for st in states]
    # Both rooms share one palette, so the costumes look the same in each
    for c in pixels(bg) + pixels(bath) + pixels(title) + pixels(gameover):
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
    for n in art.CLOWNS:
        build_costume(pal, n, None, 'a room-service clown', clown_frames(n), CLOWN_EXTRA)

    full = pal.full()
    write_bmp(os.path.join(OUT, 'room.bmp'), [pal.index[c] for c in pixels(bg)], art.W, art.H, full)
    write_bmp(os.path.join(OUT, 'bathroom.bmp'), [pal.index[c] for c in pixels(bath)], art.W, art.H, full)
    write_bmp(os.path.join(OUT, 'title.bmp'), [pal.index[c] for c in pixels(title)], art.W, art.H, full)
    write_bmp(os.path.join(OUT, 'gameover.bmp'), [pal.index[c] for c in pixels(gameover)], art.W, art.H, full)
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
    build_tv_sound()
    build_safe_sound()
    print(f'assets written to {os.path.normpath(OUT)} ({len(pal.colors)} palette entries used)')


if __name__ == '__main__':
    main()
