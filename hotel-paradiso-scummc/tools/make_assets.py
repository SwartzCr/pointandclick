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


# --------------------------------------------------------------------------- more sound effects
def _noise_burst(rnd, out, t0, ms, level, lp_a, decay):
    import math
    lp = LowPass(lp_a)
    n = int(RATE * ms / 1000)
    i0 = int(t0 * RATE)
    for k in range(n):
        if 0 <= i0 + k < len(out):
            out[i0 + k] += level * lp(rnd.uniform(-1, 1)) * math.exp(-decay * k / n)


def build_fridge_sound():
    """The minibar door: the handle clicks, the latch lets go with a second,
    sharper click, and the rubber seal unsticks with a soft pop."""
    import random
    rnd = random.Random(11)
    out = [0.0] * int(RATE * 0.55)
    _add(out, 0.02, _tick(rnd, 0.7, freq=2300, ms=18))      # handle
    _add(out, 0.11, _tick(rnd, 1.0, freq=3400, ms=14))      # latch
    _add(out, 0.115, _tick(rnd, 0.5, freq=1500, ms=30))
    _add(out, 0.19, _thud(rnd, 0.35, freq=180, ms=90))      # the seal lets go
    _noise_burst(rnd, out, 0.19, 160, 1.4, 0.05, 6)         # a puff of cold air
    write_voc('fridge', normalize(out, 0.9))


def build_drawer_sound():
    """A wooden drawer sliding out: rough wood-on-wood friction that speeds up
    and slows down, then a soft bump as it reaches the end of its runners."""
    import math
    import random
    rnd = random.Random(12)
    out = [0.0] * int(RATE * 0.62)
    body = Resonator(420, 0.97)
    body2 = Resonator(1100, 0.95)
    lp = LowPass(0.3)
    i0, i1 = int(0.02 * RATE), int(0.48 * RATE)
    grain = 0.0
    for i in range(i0, i1):
        u = (i - i0) / (i1 - i0)
        speed = math.sin(math.pi * u) ** 0.6                 # pull, glide, slow down
        if rnd.random() < 0.012 + 0.02 * speed:
            grain = 1.0                                      # stick-slip catches
        grain *= 0.993
        x = lp(rnd.uniform(-1, 1)) * (0.4 + grain) * speed
        out[i] += 3.0 * body(x) + 1.6 * body2(x) + 0.25 * x
    _add(out, 0.47, _thud(rnd, 0.9, freq=150, ms=120))       # the end stop
    _add(out, 0.47, _tick(rnd, 0.3, freq=900, ms=30))
    write_voc('drawer', normalize(out, 0.9))


def build_cabinet_sound():
    """The medicine cabinet: the magnetic catch lets go with a click, then the
    small mirrored door swings out on a dry, rising-and-falling hinge creak."""
    import math
    import random
    rnd = random.Random(13)
    out = [0.0] * int(RATE * 0.75)
    _add(out, 0.02, _tick(rnd, 0.5, freq=2800, ms=16))      # magnet lets go
    _add(out, 0.025, _tick(rnd, 0.4, freq=1200, ms=25))
    ring = Resonator(1450, 0.985)
    ring2 = Resonator(2900, 0.98)
    i0, i1 = int(0.10 * RATE), int(0.62 * RATE)
    phase = 0.0
    for i in range(i0, i1):
        u = (i - i0) / (i1 - i0)
        rate = 140 + 260 * math.sin(math.pi * u) + 30 * math.sin(u * 40)   # stick-slip pulses
        phase += rate / RATE
        x = 0.0
        if phase >= 1.0:
            phase -= 1.0
            x = 1.0 + rnd.uniform(-0.3, 0.3)
        env = min(1.0, u / 0.08) * min(1.0, (1 - u) / 0.15)
        out[i] += env * (20 * ring(x) + 10 * ring2(x))
    _add(out, 0.64, _tick(rnd, 0.35, freq=1800, ms=20))     # door stops against its stay
    write_voc('cabinet', normalize(out, 0.85))


def build_bed_sound():
    """Covers thrown back: two quick swishes of cotton and a softer settle,
    band-limited noise with a lumpy envelope."""
    import math
    import random
    rnd = random.Random(14)
    out = [0.0] * int(RATE * 0.85)
    hp_prev = 0.0
    lp = LowPass(0.45)
    swishes = ((0.02, 0.22, 1.0), (0.18, 0.30, 0.8), (0.45, 0.35, 0.45))
    for i in range(len(out)):
        t = i / RATE
        env = 0.0
        for t0, d, a in swishes:
            if t0 <= t < t0 + d:
                u = (t - t0) / d
                env += a * math.sin(math.pi * u) ** 1.5
        x = rnd.uniform(-1, 1)
        hp = x - hp_prev                                  # tilt toward the hiss of fabric
        hp_prev = x * 0.6
        crinkle = 1.0 + (0.8 if rnd.random() < 0.004 else 0.0)
        out[i] += env * lp(hp) * crinkle
    write_voc('bed', normalize(out, 0.8))


# ---- a tiny synthesiser for the two pieces of music
def _midi(n):
    return 440.0 * 2 ** ((n - 69) / 12)


def _voice(out, t0, dur, freq, level, kind):
    import math
    i0 = int(t0 * RATE)
    n = int(dur * RATE)
    tail = int(0.08 * RATE)
    for k in range(n + tail):
        i = i0 + k
        if i >= len(out):
            break
        t = k / RATE
        rel = 1.0 if k < n else 1 - (k - n) / tail
        w = 2 * math.pi * freq * t
        if kind == 'vibes':           # vibraphone: bright sine with tremolo, long decay
            v = (math.sin(w) + 0.25 * math.sin(4 * w)) * math.exp(-2.2 * t) * (0.85 + 0.15 * math.sin(2 * math.pi * 5.5 * t))
            a = min(1.0, k / 40)
        elif kind == 'epiano':        # electric piano: sine + soft bell partial
            v = (math.sin(w) + 0.35 * math.sin(2 * w) * math.exp(-6 * t)) * math.exp(-3.0 * t)
            a = min(1.0, k / 60)
        elif kind == 'bass':          # upright-ish bass: rounded triangle, plucked
            ph = (freq * t) % 1.0
            v = (4 * abs(ph - 0.5) - 1) * 0.7 + 0.3 * math.sin(w)
            v *= math.exp(-2.5 * t)
            a = min(1.0, k / 30)
        elif kind == 'calliope':      # steam calliope: breathy square-ish pipe with wide vibrato
            vib = 1 + 0.012 * math.sin(2 * math.pi * 6.5 * t)
            ww = 2 * math.pi * freq * vib * t
            s = math.sin(ww) + 0.45 * math.sin(3 * ww) + 0.2 * math.sin(2 * ww)
            v = max(-1.2, min(1.2, 1.4 * s))
            a = min(1.0, k / 120)
        elif kind == 'organ':         # fairground band organ: clean flue pipes, gentle vibrato
            vib = 1 + 0.004 * math.sin(2 * math.pi * 5.2 * t)
            ww = 2 * math.pi * freq * vib * t
            v = math.sin(ww) + 0.45 * math.sin(2 * ww) + 0.12 * math.sin(3 * ww)
            v *= 0.92 + 0.08 * math.sin(2 * math.pi * 7 * t)       # a little tremolant
            a = min(1.0, k / 160)
        elif kind == 'glock':         # glockenspiel: struck bar, one inharmonic partial
            v = (math.sin(w) + 0.3 * math.sin(2.76 * w) * math.exp(-9 * t)) * math.exp(-4.5 * t)
            a = min(1.0, k / 8)
        elif kind == 'tuba':          # oom: round low brass
            v = (math.sin(w) + 0.5 * math.sin(2 * w) + 0.2 * math.sin(3 * w)) * math.exp(-4 * t)
            a = min(1.0, k / 150)
        else:
            raise ValueError(kind)
        out[i] += level * v * a * rel


def _drum(out, rnd, t0, kind, level):
    import math
    i0 = int(t0 * RATE)
    if kind == 'shaker':
        n, lp = int(0.05 * RATE), LowPass(0.8)
        for k in range(n):
            if i0 + k < len(out):
                x = rnd.uniform(-1, 1)
                out[i0 + k] += level * (x - lp(x)) * math.sin(math.pi * k / n)
    elif kind == 'rim':
        _add(out, t0, _tick(rnd, level, freq=1700, ms=30))
    elif kind == 'kick':
        _add(out, t0, _thud(rnd, level, freq=70, ms=160))
    elif kind == 'snare':
        n, lp = int(0.12 * RATE), LowPass(0.5)
        for k in range(n):
            if i0 + k < len(out):
                out[i0 + k] += level * (lp(rnd.uniform(-1, 1)) * 1.5 + 0.4 * math.sin(2 * math.pi * 190 * k / RATE)) * math.exp(-28 * k / RATE)
    elif kind == 'woodblock':
        _add(out, t0, _tick(rnd, level, freq=1050, ms=45))
    elif kind == 'cymbal':
        n = int(0.25 * RATE)
        for k in range(n):
            if i0 + k < len(out):
                x = rnd.uniform(-1, 1)
                out[i0 + k] += level * x * 0.5 * math.exp(-12 * k / RATE)


def build_theme_music():
    """The title screen: an original lounge tune for the Hotel Paradiso, a
    bossa-tinged eight bars in F at 120bpm (16s). Vibraphone melody,
    electric piano chords, plucked bass, shaker and rim clicks."""
    import random
    rnd = random.Random(15)
    beat = 0.5
    out = [0.0] * int(RATE * (32 * beat + 0.6))
    melody = [  # (midi, beats); None = rest
        (69, 1), (72, .5), (76, 1.5), (74, 1),
        (72, 1), (69, .5), (65, 1.5), (None, 1),
        (70, 1), (74, .5), (77, 1.5), (76, 1),
        (74, .5), (72, .5), (70, 1), (67, 2),
        (69, 1), (72, .5), (76, 1.5), (79, 1),
        (77, 1), (74, .5), (70, 1.5), (69, 1),
        (67, 1), (70, 1), (76, 1), (74, .5), (72, .5),
        (77, 3), (None, 1),
    ]
    t = 0.0
    for n, d in melody:
        if n:
            _voice(out, t, d * beat * 0.95, _midi(n), 0.34, 'vibes')
        t += d * beat
    chords = [  # one per bar, bar 7 split
        ((53, 57, 60, 64), 41), ((50, 53, 57, 60), 38), ((55, 58, 62, 65), 43), ((52, 55, 58, 60), 36),
        ((53, 57, 60, 64), 41), ((53, 57, 58, 62), 34), ((55, 58, 62, 65), 43), ((53, 57, 60, 62), 41),
    ]
    for bar, (notes, root) in enumerate(chords):
        b0 = bar * 4 * beat
        if bar == 6:
            parts = [((55, 58, 62, 65), 43, 0, 2), ((52, 55, 58, 60), 36, 2, 2)]
        else:
            parts = [(notes, root, 0, 4)]
        for ns, r, start, length in parts:
            s0 = b0 + start * beat
            for hit, dur in ((0, 0.9), (1.5, 0.4), (3, 0.6)):
                if hit < length:
                    for nn in ns:
                        _voice(out, s0 + hit * beat, dur * beat, _midi(nn), 0.09, 'epiano')
            _voice(out, s0, 1.4 * beat, _midi(r), 0.42, 'bass')                 # root
            if length > 2:
                _voice(out, s0 + 1.5 * beat, 0.4 * beat, _midi(r + 7), 0.32, 'bass')  # fifth
                _voice(out, s0 + 2 * beat, 1.4 * beat, _midi(r + 7), 0.38, 'bass')
                _voice(out, s0 + 3.5 * beat, 0.4 * beat, _midi(r), 0.3, 'bass')
            else:
                _voice(out, s0 + 1.5 * beat, 0.4 * beat, _midi(r + 7), 0.32, 'bass')
        for e in range(8):
            _drum(out, rnd, b0 + e * beat / 2, 'shaker', 0.10 if e % 2 else 0.16)
        for hit in (1.5, 3):
            _drum(out, rnd, b0 + hit * beat, 'rim', 0.35)
    write_voc('theme', normalize(out, 0.9))


def build_clown_music():
    """Room service arrives: an original merry-go-round waltz in the style of a
    fairground band organ. 16 bars of 3/4 in C at 168bpm (~17s): flute pipes
    doubled by a glockenspiel, oom-pah-pah tuba and chords, a cymbal crash at
    each phrase and woodblock ticks. Every voice is clean sine partials kept
    below the 5.5kHz ceiling of an 11kHz sound, with no clipping."""
    import random
    rnd = random.Random(16)
    beat = 60 / 168
    bars = 16
    out = [0.0] * int(RATE * (bars * 3 * beat + 0.8))
    melody = [  # (midi, beats), three beats a bar
        (76, 2), (79, 1),   (84, 2), (83, 1),   (81, 1), (79, 1), (76, 1),   (74, 3),
        (74, 2), (77, 1),   (83, 2), (81, 1),   (79, 1), (77, 1), (74, 1),   (72, 3),
        (76, 2), (79, 1),   (84, 2), (88, 1),   (84, 1), (81, 1), (77, 1),   (81, 3),
        (79, 2), (76, 1),   (77, 1), (76, 1), (74, 1),   (71, 1), (74, 1), (77, 1),   (72, 2), (None, 1),
    ]
    t = 0.0
    for n, d in melody:
        if n:
            _voice(out, t, d * beat * 0.92, _midi(n), 0.26, 'organ')
            _voice(out, t, d * beat * 0.92, _midi(n - 12), 0.10, 'organ')    # a lower rank of pipes
            _voice(out, t, min(d, 1) * beat, _midi(n), 0.16, 'glock')
        t += d * beat
    harmony = ['C', 'C', 'C', 'G7', 'G7', 'G7', 'G7', 'C',
               'C', 'C7', 'F', 'F', 'C', 'Dm', 'G7', 'C']
    roots = {'C': 36, 'C7': 36, 'F': 41, 'Dm': 38, 'G7': 43}
    pahs = {'C': (60, 64, 67), 'C7': (58, 60, 64), 'F': (60, 65, 69), 'Dm': (62, 65, 69), 'G7': (59, 62, 65)}
    for bar, ch in enumerate(harmony):
        b0 = bar * 3 * beat
        root = roots[ch] + (7 if bar % 2 else 0)
        if root > 45:
            root -= 12
        _voice(out, b0, 0.9 * beat, _midi(root), 0.42, 'tuba')                  # oom
        for p in (1, 2):                                                        # pah, pah
            for nn in pahs[ch]:
                _voice(out, b0 + p * beat, 0.5 * beat, _midi(nn), 0.07, 'organ')
            _drum(out, rnd, b0 + p * beat, 'woodblock', 0.14)
        _drum(out, rnd, b0, 'kick', 0.35)
        if bar % 8 == 0:
            _drum(out, rnd, b0, 'cymbal', 0.22)
    write_voc('clowns', normalize(out, 0.8))


def build_gameover_music():
    """The game-over screen: an original, woozy but cheerful loop (12s). A warm
    open-fifth drone with a gentle pulse, a music box with a lilting tune in
    D major that tumbles down and bounces back up, a light tipsy pitch wobble,
    and a soft whoosh that circles every 0.8s, in time with the spinning room."""
    import math
    import random
    rnd = random.Random(17)
    length = 12.0
    out = [0.0] * int(RATE * length)
    n_s = len(out)

    def wobble(t):          # semitones: a slow sag and a seasick waver
        return -0.25 * (1 - math.cos(2 * math.pi * t / length)) / 2 + 0.15 * math.sin(2 * math.pi * 0.7 * t)

    # drone: D2 and A2, an open fifth, each doubled a hair apart for a gentle pulse
    for i in range(n_s):
        t = i / RATE
        swell = 0.75 + 0.25 * math.sin(2 * math.pi * t / 6 - 1.2)
        fade = min(1.0, t / 0.6)
        v = (math.sin(2 * math.pi * 73.4 * t) + math.sin(2 * math.pi * 73.1 * t)
             + 0.6 * math.sin(2 * math.pi * 110.0 * t) + 0.4 * math.sin(2 * math.pi * 146.8 * t))
        out[i] += 0.08 * v * swell * fade

    # music box: struck tines, each note's pitch follows the wobble as it rings
    # a lilting tune in D major, then a quick tumble down an arpeggio that
    # bounces straight back up: (start time, midi)
    tune = [78, 81, 86, 85, 81, 78, 76, 79, 83, 81, 78, 74, 78, 81, 86, 88, 86, 83, 81, 79]
    tumble = [81, 78, 74, 69, 74, 78, 81, 86]
    sched = [(k * 0.5, n) for k, n in enumerate(tune)] + [(10.0 + k * 0.2, n) for k, n in enumerate(tumble)]
    for t0, n in sched:
        f0 = _midi(n)
        i0 = int(t0 * RATE)
        ph = 0.0
        for k in range(int(1.6 * RATE)):
            i = i0 + k
            if i >= n_s:
                break
            t = k / RATE
            f = f0 * 2 ** (wobble(i / RATE) / 12)
            ph += 2 * math.pi * f / RATE
            v = (math.sin(ph) + 0.25 * math.sin(3 * ph) * math.exp(-12 * t)) * math.exp(-2.6 * t)
            out[i] += 0.24 * v * min(1.0, k / 20)

    # the whoosh: filtered noise sweeping up and down, once per turn of the room
    res = Resonator(600, 0.96)
    for i in range(n_s):
        t = i / RATE
        cyc = (t % 0.8) / 0.8
        f = 350 + 900 * math.sin(math.pi * cyc)
        res.a1 = 2 * 0.96 * math.cos(2 * math.pi * f / RATE)
        out[i] += 0.2 * res(rnd.uniform(-1, 1)) * math.sin(math.pi * cyc) ** 2

    # soften the ends so the loop doesn't click
    for k in range(int(0.05 * RATE)):
        g = k / (0.05 * RATE)
        out[k] *= g
        out[-1 - k] *= g
    write_voc('gameover', normalize(out, 0.8))


def build_phone_sounds():
    """The rotary phone. phone_dial: the dial is wound to 0 and whirs back with
    ten pulse clicks, one ring in the earpiece, then the click of the front
    desk picking up (2.7s). phone_hang: the receiver going down on its cradle."""
    import math
    import random
    rnd = random.Random(21)
    out = [0.0] * int(RATE * 2.75)
    # winding the dial round: a ratchety scrape
    for k in range(8):
        _add(out, 0.02 + k * 0.035, _tick(rnd, 0.25, freq=3200, ms=10))
    # spring return: a governor whirr with ten evenly spaced pulse clicks
    i0, i1 = int(0.34 * RATE), int(1.36 * RATE)
    whirr = Resonator(700, 0.9)
    for i in range(i0, i1):
        u = (i - i0) / (i1 - i0)
        out[i] += 0.25 * whirr(rnd.uniform(-1, 1)) * (1 - 0.3 * u) * (0.7 + 0.3 * math.sin(2 * math.pi * 55 * i / RATE))
    for k in range(10):
        _add(out, 0.36 + k * 0.1, _tick(rnd, 0.7, freq=1900, ms=14))
    _add(out, 1.37, _thud(rnd, 0.35, freq=220, ms=60))        # the dial stops
    # one ring, heard down the line: 440 + 480 Hz, faint and a little band-limited
    lp = LowPass(0.5)
    i0, i1 = int(1.5 * RATE), int(2.35 * RATE)
    for i in range(i0, i1):
        t = (i - i0) / RATE
        env = min(1.0, t / 0.02) * min(1.0, (i1 - i) / (0.02 * RATE))
        out[i] += 0.32 * env * lp(math.sin(2 * math.pi * 440 * t) + math.sin(2 * math.pi * 480 * t))
    # picked up at the other end
    _add(out, 2.5, _tick(rnd, 0.9, freq=1400, ms=30))
    _add(out, 2.51, _thud(rnd, 0.3, freq=300, ms=50))
    write_voc('phone_dial', normalize(out, 0.85))

    out = [0.0] * int(RATE * 0.4)
    _add(out, 0.01, _tick(rnd, 0.6, freq=2500, ms=12))       # receiver touches the cradle
    _add(out, 0.03, _thud(rnd, 1.0, freq=160, ms=180))       # and settles with a clunk
    _add(out, 0.035, _tick(rnd, 0.5, freq=1100, ms=40))
    _add(out, 0.09, _tick(rnd, 0.3, freq=3000, ms=10))       # the bell inside gives a tiny ding
    write_voc('phone_hang', normalize(out, 0.85))


def _modal(out, t0, modes, level, attack_ms=1.0, rnd=None):
    """Strike something: add a set of decaying sine modes at t0.
    modes: (frequency Hz, decay time s, amplitude). Each starts at a random
    phase so repeated strikes don't sound machine-identical."""
    import math
    import random
    rnd = rnd or random.Random(0)
    i0 = int(t0 * RATE)
    att = max(1, int(attack_ms * RATE / 1000))
    for f, tau, a in modes:
        ph = rnd.uniform(0, 2 * math.pi)
        n = int(min(6 * tau, 2.0) * RATE)
        w = 2 * math.pi * f / RATE
        for k in range(n):
            i = i0 + k
            if i >= len(out):
                break
            out[i] += level * a * math.exp(-k / (tau * RATE)) * min(1.0, k / att) * math.sin(ph + w * k)


def build_clown_sounds():
    """knock: three knuckle raps on a hollow hotel door, each a soft "thock"
    exciting a handful of short wooden modes, with a little natural variation.
    honk: a rubber-bulb clown horn squeezed twice: a buzzy reed through the
    resonances of a brass bell, the pitch jumping up as the bulb is squeezed
    and sagging as it empties."""
    import math
    import random
    rnd = random.Random(22)

    # ---- knock
    out = [0.0] * int(RATE * 0.9)
    door = [(96, .060, .55), (141, .050, 1.0), (229, .034, .75), (372, .024, .5),
            (611, .015, .35), (987, .010, .22), (1690, .006, .14)]
    for t0, a in ((0.030, 1.0), (0.205, 0.82), (0.375, 0.95)):
        detune = 1 + rnd.uniform(-0.03, 0.03)
        _modal(out, t0, [(f * detune, tau, amp) for f, tau, amp in door], a, attack_ms=1.5, rnd=rnd)
        # the knuckle itself: a few ms of muffled noise
        lp = LowPass(0.35)
        i0 = int(t0 * RATE)
        n = int(0.005 * RATE)
        for k in range(n):
            out[i0 + k] += 0.6 * a * lp(rnd.uniform(-1, 1)) * math.sin(math.pi * k / n)
    write_voc('knock', normalize(out, 0.9))

    # ---- honk
    out = [0.0] * int(RATE * 0.8)
    for t0, dur, f0, lvl in ((0.0, 0.30, 340, 1.0), (0.37, 0.26, 318, 0.9)):
        bell = [Resonator(820, 0.965), Resonator(1520, 0.96), Resonator(2650, 0.95)]
        breath = LowPass(0.4)
        i0, n = int(t0 * RATE), int(dur * RATE)
        ph = 0.0
        for k in range(n):
            t, u = k / RATE, k / n
            f = f0 * (0.84 + 0.18 * (1 - math.exp(-t / 0.025)) - 0.06 * u) * (1 + 0.004 * rnd.uniform(-1, 1))
            ph += 2 * math.pi * f / RATE
            # band-limited sawtooth reed: harmonics up to the 5.5kHz ceiling
            src = 0.0
            h = 1
            while h * f < 5000:
                src += math.sin(h * ph) / h
                h += 1
            src += 0.15 * breath(rnd.uniform(-1, 1))
            env = min(1.0, t / 0.012) * min(1.0, (n - k) / (0.045 * RATE))
            v = 0.25 * src + 24 * bell[0](src) + 16 * bell[1](src) + 9 * bell[2](src)
            if i0 + k < len(out):
                out[i0 + k] += lvl * env * v
    write_voc('honk', normalize(out, 0.85))


def build_line_sounds():
    """chop: three quick taps of a razor blade on glass, each with a little
    scrape. sniff: a quick nasal inhale. swoop: the room tilts, a woozy slide
    down and back up with a seasick wobble."""
    import math
    import random
    rnd = random.Random(23)
    out = [0.0] * int(RATE * 0.75)
    glass = Resonator(3300, 0.97)
    glass2 = Resonator(2100, 0.96)
    for t0 in (0.02, 0.22, 0.42):
        i0 = int(t0 * RATE)
        for k in range(int(0.004 * RATE)):
            x = rnd.uniform(-1, 1)
            if i0 + k < len(out):
                out[i0 + k] += x
        lp = LowPass(0.7)
        for k in range(int(0.07 * RATE)):                    # the blade drawn across
            i = i0 + int(0.03 * RATE) + k
            if i < len(out):
                out[i] += 0.12 * lp(rnd.uniform(-1, 1)) * math.sin(math.pi * k / (0.07 * RATE))
    for i in range(len(out)):
        x = out[i]
        out[i] = 0.5 * x + 4 * glass(x) + 2.5 * glass2(x)
    write_voc('chop', normalize(out, 0.85))

    out = [0.0] * int(RATE * 0.55)
    nose = Resonator(1800, 0.9)
    hiss = LowPass(0.6)
    for i in range(len(out)):
        u = i / len(out)
        env = math.sin(math.pi * min(1.0, u / 0.85)) ** 0.7 if u < 0.85 else 0.0
        env *= 0.6 + 0.4 * u                                   # gets sharper as it goes
        nose.a1 = 2 * 0.9 * math.cos(2 * math.pi * (1300 + 1400 * u) / RATE)
        x = rnd.uniform(-1, 1)
        out[i] += env * (0.5 * hiss(x) + 2.5 * nose(x))
    write_voc('sniff', normalize(out, 0.8))

    out = [0.0] * int(RATE * 1.4)
    ph = ph2 = 0.0
    for i in range(len(out)):
        t = i / RATE
        u = t / 1.4
        f = 520 * 2 ** ((-0.9 * math.sin(math.pi * u) + 0.12 * math.sin(2 * math.pi * 5 * t)))  # slide down and back
        ph += 2 * math.pi * f / RATE
        ph2 += 2 * math.pi * f * 1.5 / RATE
        env = math.sin(math.pi * u) ** 0.8
        out[i] += env * (math.sin(ph) + 0.35 * math.sin(ph2) + 0.15 * math.sin(2 * ph))
    write_voc('swoop', normalize(out, 0.7))


def build_unscrew_sound():
    """The mirror door coming off (about 2.1s): two screws backed out, each a
    few gritty turns of thread friction (tight and crunchy at first, looser
    after) with the click of the screwdriver re-seating between turns; one
    screw drops and bounces on the porcelain sink; then the mirror door lifts
    off its hinges with a bright glass tink at 1.75s."""
    import math
    import random
    rnd = random.Random(24)
    out = [0.0] * int(RATE * 2.15)

    def turn(t0, dur, tight):
        metal = [Resonator(1250, 0.975), Resonator(2350, 0.97), Resonator(3550, 0.96)]
        body = Resonator(460, 0.95)
        i0, n = int(t0 * RATE), int(dur * RATE)
        ph = 0.0
        for k in range(n):
            u = k / n
            rate = (55 if tight else 85) + 110 * u                  # stick-slip speeds up as it gives
            ph += rate * (1 + 0.25 * rnd.uniform(-1, 1)) / RATE
            x = 0.0
            if ph >= 1.0:
                ph -= 1.0
                x = rnd.uniform(0.6, 1.0)
            x += 0.18 * rnd.uniform(-1, 1)                          # grit in the thread
            env = math.sin(math.pi * u) ** 0.8 * (1.4 if tight and u < 0.15 else 1.0)
            if i0 + k < len(out):
                out[i0 + k] += env * (14 * metal[0](x) + 9 * metal[1](x) + 5 * metal[2](x) + 10 * body(x))
        if tight:                                                    # the first crack as it breaks free
            _add(out, t0, _tick(rnd, 0.9, freq=1800, ms=25))

    for s0 in (0.04, 0.74):                                         # two screws
        for k, (dt, dur) in enumerate(((0.0, 0.17), (0.21, 0.14), (0.39, 0.12))):
            _add(out, s0 + dt - 0.015, _tick(rnd, 0.35, freq=2700, ms=10))   # driver re-seats
            turn(s0 + dt, dur, tight=(k == 0))
    # the second screw drops onto the sink: bounces closer and closer together
    screw = [(2930, .050, 1.0), (4380, .030, .55), (1840, .040, .35)]
    for t0, a in ((1.36, 1.0), (1.48, 0.6), (1.565, 0.38), (1.62, 0.24), (1.655, 0.15), (1.675, 0.1)):
        _modal(out, t0, screw, 0.45 * a, attack_ms=0.3, rnd=rnd)
    # the mirror door lifts off: a bright tink of plate glass and a soft knock of its frame
    _modal(out, 1.75, [(1660, .22, 1.0), (2890, .16, .7), (4120, .11, .45), (4960, .07, .25)], 0.5,
           attack_ms=0.3, rnd=rnd)
    _add(out, 1.755, _thud(rnd, 0.25, freq=260, ms=70))
    write_voc('unscrew', normalize(out, 0.85))


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
    build_fridge_sound()
    build_drawer_sound()
    build_cabinet_sound()
    build_bed_sound()
    build_theme_music()
    build_clown_music()
    build_gameover_music()
    build_phone_sounds()
    build_clown_sounds()
    build_line_sounds()
    build_unscrew_sound()
    print(f'assets written to {os.path.normpath(OUT)} ({len(pal.colors)} palette entries used)')


if __name__ == '__main__':
    main()
