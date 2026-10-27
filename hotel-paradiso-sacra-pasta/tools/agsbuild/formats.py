"""Writers for the AGS 3.6.1 data formats: the sprite file (acsprset.spr),
room files (roomN.crm), WFN bitmap fonts and the CLIB package (.ags).

Ported from the AGS 3.6.1 sources: Common/ac/spritefile.cpp,
Common/game/room_file.cpp, Common/font/wfnfont.cpp and the editor's
DataFileWriter.cs. Pixels of 32-bit images are stored as little-endian
0xAARRGGBB words, i.e. B, G, R, A bytes.
"""
import time
import numpy as np
from PIL import Image

from .binio import W
from . import lzss

MASK = (255, 0, 255)


def argb_bytes(im, opaque=False):
    """RGBA PIL image -> AGS 32-bit pixel data (BGRA byte order). Fully
    transparent pixels become magic pink with zero alpha."""
    a = np.asarray(im.convert('RGBA'), dtype=np.uint8).copy()
    if opaque:
        a[..., 3] = 255
    else:
        clear = a[..., 3] == 0
        a[clear] = (255, 0, 255, 0)
    return a[..., [2, 1, 0, 3]].tobytes()


# ------------------------------------------------------------------ sprites
SPRF_VERSION = 12            # kSprfVersion_StorageFormats
SPR_COMPRESS_LZW = 2


def write_sprite_file(sprites):
    """sprites: list indexed by sprite number of RGBA images (or None)."""
    w = W()
    w.i16(SPRF_VERSION)
    w.raw(b' Sprite File ')
    w.i8(SPR_COMPRESS_LZW)
    w.i32(int(time.time()) & 0x7FFFFFFF)       # SpriteFileIDCheck
    w.i32(len(sprites) - 1)                    # last slot
    w.i8(0)                                    # storage flags
    w.zeros(3)
    for im in sprites:
        if im is None:
            w.i16(0)                           # empty slot
            continue
        data = argb_bytes(im)
        comp = lzss.compress(data)
        w.i8(4)                                # bpp
        w.i8(0)                                # format: as-is
        w.i8(0)                                # palette count - 1
        w.i8(SPR_COMPRESS_LZW)
        w.i16(im.width)
        w.i16(im.height)
        w.i32(len(comp))
        w.raw(comp)
    return w.bytes()


# ------------------------------------------------------------------ rooms
ROOM_VERSION = 33            # kRoomVersion_3508
MAX_ROOM_HOTSPOTS = 50
MAX_ROOM_REGIONS = 16
MAX_WALK_AREAS = 16
MAX_WALK_BEHINDS = 16
NOT_VECTOR_SCALED = -10000
OBJF_NOINTERACT = 0x01


def _lzw_image(w, im):
    """save_lzw(): 256 RGB+filler palette entries (unused at 32-bit), the
    uncompressed size, compressed size and the LZSS stream of
    [stride, height, pixels]."""
    hdr = W()
    hdr.i32(im.width * 4)
    hdr.i32(im.height)
    raw = hdr.bytes() + argb_bytes(im, opaque=True)
    comp = lzss.compress(raw)
    w.zeros(256 * 4)
    w.i32(len(raw))
    w.i32(len(comp))
    w.raw(comp)


def _cpackbitl(line):
    """AGS's RLE for 8-bit masks (Common/util/compress.cpp, cpackbitl)."""
    out = bytearray()
    size = len(line)
    cnt = 0
    while cnt < size:
        i = cnt
        j = i + 1
        jmax = i + 126
        if jmax >= size:
            jmax = size - 1
        if i == size - 1:
            out += bytes((0, line[i]))
            cnt += 1
        elif line[i] == line[j]:
            while j < jmax and line[j] == line[j + 1]:
                j += 1
            out += bytes(((i - j) & 0xFF, line[i]))
            cnt += j - i + 1
        else:
            while j < jmax and line[j] != line[j + 1]:
                j += 1
            out.append((j - i) & 0xFF)
            out += line[i:j + 1]
            cnt += j - i + 1
    return bytes(out)


def _rle_mask(w, mask):
    """save_rle_bitmap8(): size, packed pixels, dummy palette."""
    w.i16(mask.width)
    w.i16(mask.height)
    w.raw(_cpackbitl(bytes(np.asarray(mask, dtype=np.uint8).tobytes())))
    w.zeros(256 * 3)


def _interactions(w, names):
    w.i32(len(names))
    for n in names:
        w.lstr(n)


def _props(w, props=None):
    props = props or {}
    w.i32(2)                                   # kPropertyVersion_340
    w.i32(len(props))
    for k, v in props.items():
        w.lstr(k)
        w.lstr(v)


class Room:
    """A room. Masks are 'P' or 'L' images of the room size holding area
    numbers (0 = none)."""

    def __init__(self, number, backgrounds, walk, hotspot_mask, walkbehind=None,
                 regions=None):
        self.number = number
        self.backgrounds = backgrounds
        self.width, self.height = backgrounds[0].size
        self.walk = walk
        self.hotspot_mask = hotspot_mask
        blank = Image.new('L', (self.width, self.height), 0)
        self.walkbehind = walkbehind or blank
        self.regions = regions or blank
        self.hotspots = [dict(name='', script='hHotspot0', walkto=(0, 0))]
        self.objects = []
        self.walkbehind_baselines = []
        self.bg_anim_speed = 5
        self.bg_anim = False
        self.script = None
        self.edges = (0, self.height - 1, 0, self.width - 1)  # top, bottom, left, right
        self.game_id = 0
        self.scaling = {}                      # walk area -> (far, near) percent

    def add_hotspot(self, script, name, walkto=(0, 0)):
        self.hotspots.append(dict(name=name, script=script, walkto=walkto))
        return len(self.hotspots) - 1

    def add_object(self, script, name, sprite, x, y, visible=True, baseline=0,
                   clickable=True):
        self.objects.append(dict(script=script, name=name, sprite=sprite, x=x, y=y,
                                 visible=visible, baseline=baseline,
                                 clickable=clickable))
        return len(self.objects) - 1

    def _main_block(self):
        w = W()
        w.i32(4)                               # background bpp
        wb = self.walkbehind_baselines + [0] * (MAX_WALK_BEHINDS - len(self.walkbehind_baselines))
        w.i16(len(wb))
        for b in wb:
            w.i16(b)
        hs = self.hotspots + [dict(name='', script='hHotspot%d' % i, walkto=(0, 0))
                              for i in range(len(self.hotspots), MAX_ROOM_HOTSPOTS)]
        w.i32(len(hs))
        for h in hs:
            w.i16(h['walkto'][0]); w.i16(h['walkto'][1])
        for h in hs:
            w.lstr(h['name'])
        for h in hs:
            w.lstr(h['script'])
        w.i32(0)                               # legacy poly-point areas
        top, bottom, left, right = self.edges
        w.i16(top); w.i16(bottom); w.i16(left); w.i16(right)
        w.i16(len(self.objects))
        for o in self.objects:
            w.i16(o['sprite']); w.i16(o['x']); w.i16(o['y'])
            w.i16(self.number); w.i16(1 if o['visible'] else 0)
        w.i32(0)                               # legacy interaction vars
        w.i32(MAX_ROOM_REGIONS)
        _interactions(w, [])                   # room events
        for _ in hs:
            _interactions(w, [])
        for _ in self.objects:
            _interactions(w, [])
        for _ in range(MAX_ROOM_REGIONS):
            _interactions(w, [])
        for o in self.objects:
            w.i32(o['baseline'])
        w.i16(self.width)
        w.i16(self.height)
        for o in self.objects:
            w.i16(0 if o['clickable'] else OBJF_NOINTERACT)
        w.i16(1)                               # mask resolution
        w.i32(MAX_WALK_AREAS)
        far = [0] * MAX_WALK_AREAS
        near = [NOT_VECTOR_SCALED] * MAX_WALK_AREAS
        for a, (f, n) in self.scaling.items():
            far[a] = f - 100
            near[a] = n - 100
        for v in far:
            w.i16(v)
        for _ in range(MAX_WALK_AREAS):
            w.i16(0)                           # area-specific player view
        for v in near:
            w.i16(v)
        for _ in range(MAX_WALK_AREAS):
            w.i16(-1)                          # top (computed by engine)
        for _ in range(MAX_WALK_AREAS):
            w.i16(-1)                          # bottom
        w.zeros(11)                            # legacy password
        w.i8(0)                                # startup music
        w.i8(0)                                # save/load disabled
        w.i8(0)                                # player character off
        w.i8(0)                                # player view
        w.i8(0)                                # music volume
        w.i8(0 if self.bg_anim else 1)         # flags: bg frame locked
        w.zeros(4)                             # reserved
        w.i16(0)                               # message count
        w.i32(self.game_id)
        w.i16(0)                               # legacy room animations
        for _ in range(MAX_WALK_AREAS):
            w.i16(0)
        for _ in range(MAX_ROOM_REGIONS):
            w.i16(0)                           # region light
        for _ in range(MAX_ROOM_REGIONS):
            w.i32(0)                           # region tint
        _lzw_image(w, self.backgrounds[0])
        _rle_mask(w, self.regions)
        _rle_mask(w, self.walk)
        _rle_mask(w, self.walkbehind)
        _rle_mask(w, self.hotspot_mask)
        return w.bytes()

    def write(self):
        w = W()
        w.i16(ROOM_VERSION)
        w.block(1, self._main_block())
        if self.script:
            w.block(7, self.script)
        if self.objects:
            b = W(); b.i8(len(self.objects))
            for o in self.objects:
                b.lstr(o['name'])
            w.block(5, b.bytes())
            b = W(); b.i8(len(self.objects))
            for o in self.objects:
                b.lstr(o['script'])
            w.block(9, b.bytes())
        if len(self.backgrounds) > 1:
            b = W()
            b.i8(len(self.backgrounds))
            b.i8(self.bg_anim_speed)
            for _ in self.backgrounds:
                b.i8(1)                        # palette shared
            for im in self.backgrounds[1:]:
                _lzw_image(b, im)
            w.block(6, b.bytes())
        b = W()
        b.i32(1)
        _props(b)
        for _ in range(MAX_ROOM_HOTSPOTS):
            _props(b)
        for _ in self.objects:
            _props(b)
        w.block(8, b.bytes())
        b = W(); b.i32(1); b.lstr('textencoding'); b.lstr('65001')
        w.block(0, b.bytes(), 'ext_sopts')
        w.i8(0xFF)
        return w.bytes()


# ------------------------------------------------------------------ fonts
def write_wfn(glyphs):
    """glyphs: list of 256 (or fewer) 'L'/'1' images, nonzero = ink."""
    data = W()
    offsets = []
    base = 15 + 2
    for g in glyphs:
        offsets.append(base + data.pos())
        gw, gh = g.size
        data.i16(gw)
        data.i16(gh)
        px = np.asarray(g.convert('L')) > 0
        rowbytes = (gw + 7) // 8
        for y in range(gh):
            row = bytearray(rowbytes)
            for x in range(gw):
                if px[y, x]:
                    row[x // 8] |= 0x80 >> (x % 8)
            data.raw(bytes(row))
    w = W()
    w.raw(b'WGT Font File  ')
    w.i16(base + data.pos())
    w.raw(data.bytes())
    for o in offsets:
        w.i16(o)
    return w.bytes()


# ------------------------------------------------------------------ package
def write_clib(assets, path, libname):
    """assets: list of (name, bytes). Writes a single-file CLIB v30 package."""
    hdr = W()

    def header(offsets):
        h = W()
        h.i32(0)                               # options
        h.i32(1)
        h.cstr(libname)
        h.i32(len(assets))
        for (name, data), off in zip(assets, offsets):
            h.cstr(name)
            h.i8(0)
            h.i64(off)
            h.i64(len(data))
        return h.bytes()

    start = len(b'CLIB\x1a') + 2
    hlen = len(header([0] * len(assets)))
    offsets = []
    pos = start + hlen
    for _, data in assets:
        offsets.append(pos)
        pos += len(data)
    hdr.raw(b'CLIB\x1a')
    hdr.i8(30)
    hdr.i8(0)
    hdr.raw(header(offsets))
    with open(path, 'wb') as f:
        f.write(hdr.bytes())
        for _, data in assets:
            f.write(data)
