"""MEATBALL MADNESS, the arcade game in the Crypt's trackball cabinet: a meatball rolls along a
dinner table, hopping over a fork, a colander, a parmesan avalanche and a loaf of garlic bread,
until it rolls into the bowl.

Drawn like the first Hotel Paradiso: flat colours, hard edges and 2x2 ordered dither, at half
size and doubled. The game itself is in src/game.asc (MeatballGame); this makes its sprites.
"""
from PIL import Image, ImageDraw

S = 2                     # every pixel here is 2x2 on screen
W, H = 320, 144           # the play area, before doubling (640x288)
GROUND = 120              # where the meatball rolls, before doubling

P = {
    'sky_hi': (64, 40, 96), 'sky': (120, 64, 112), 'sky_lo': (214, 112, 96), 'sun': (252, 210, 120),
    'hill': (230, 190, 90), 'hill_dk': (196, 150, 60), 'hill_hi': (248, 222, 140),
    'bottle': (46, 92, 60), 'bottle_dk': (28, 60, 40), 'label': (230, 214, 170),
    'candle': (236, 228, 204), 'flame': (252, 196, 80), 'flame_hi': (255, 246, 190),
    'cloth_r': (190, 40, 46), 'cloth_w': (238, 228, 214), 'cloth_dk': (120, 22, 30), 'cloth_sh': (200, 186, 172),
    'wood': (110, 64, 36), 'wood_dk': (70, 38, 22),
    'meat': (140, 66, 40), 'meat_dk': (92, 40, 24), 'meat_hi': (196, 112, 70), 'herb': (70, 120, 52),
    'steel': (196, 200, 206), 'steel_dk': (120, 126, 134), 'steel_hi': (240, 242, 246),
    'cheese': (246, 226, 150), 'cheese_dk': (214, 184, 96), 'cheese_hi': (255, 248, 208),
    'bread': (214, 150, 70), 'bread_dk': (160, 98, 40), 'bread_hi': (242, 196, 120), 'garlic': (90, 140, 60),
    'bowl': (238, 236, 230), 'bowl_dk': (176, 172, 168), 'sauce': (196, 44, 36), 'sauce_hi': (236, 96, 70),
    'noodle': (246, 214, 120), 'ink': (36, 22, 30),
}


def big(im):
    return im.resize((im.width * S, im.height * S), Image.NEAREST)


def dither(px, x0, y0, x1, y1, a, b, level):
    bayer = [[0, 2], [3, 1]]
    for y in range(y0, y1):
        for x in range(x0, x1):
            px[x, y] = P[b] if bayer[y % 2][x % 2] < level else P[a]


def canvas(w, h):
    return Image.new('RGBA', (w, h), (0, 0, 0, 0))


# ------------------------------------------------------------------ backgrounds
def sky():
    """The far layer (doesn't scroll): a sunset over a table that goes on forever."""
    im = Image.new('RGBA', (W, H), P['sky'] + (255,))
    px = im.load()
    bands = [('sky_hi', 'sky', 0, 40), ('sky', 'sky_lo', 40, 80)]
    for a, b, y0, y1 in bands:
        for y in range(y0, y1):
            dither(px, 0, y, W, y + 1, a, b, round(4 * (y - y0) / (y1 - y0)))
    d = ImageDraw.Draw(im)
    d.ellipse([228, 52, 268, 92], fill=P['sun'])
    for y in range(80, H):
        d.line([(0, y), (W, y)], fill=P['sky_lo'])
    return im


def hills():
    """The middle layer (scrolls slowly, tiles every 320): hills of spaghetti on the horizon."""
    im = canvas(W, H)
    d = ImageDraw.Draw(im)
    import math
    for x in range(W):
        h = 18 + 8 * math.sin(x * 2 * math.pi / 160) + 5 * math.sin(x * 2 * math.pi / 64 + 1)
        top = int(GROUND - 18 - h)
        d.line([(x, top), (x, GROUND)], fill=P['hill'])
        if (x // 3) % 2 == 0:
            d.point((x, top), fill=P['hill_hi'])
    px = im.load()
    # noodle squiggles
    for k in range(0, W, 7):
        for t in range(6):
            x, y = (k + t) % W, GROUND - 14 - (k * 13 % 20) + (t % 3)
            if px[x, y][3]:
                px[x, y] = P['hill_dk']
    # wine bottles and candles stood about on the far table
    for x in (40, 150, 262):
        d.rectangle([x, GROUND - 46, x + 9, GROUND - 6], fill=P['bottle'])
        d.rectangle([x + 3, GROUND - 58, x + 6, GROUND - 46], fill=P['bottle'])
        d.rectangle([x + 1, GROUND - 34, x + 8, GROUND - 24], fill=P['label'])
        d.line([(x + 9, GROUND - 46), (x + 9, GROUND - 6)], fill=P['bottle_dk'])
    for x in (98, 206):
        d.rectangle([x, GROUND - 30, x + 4, GROUND - 6], fill=P['candle'])
        d.rectangle([x + 1, GROUND - 35, x + 3, GROUND - 31], fill=P['flame'])
        d.point((x + 2, GROUND - 33), fill=P['flame_hi'])
    return im


def ground():
    """The near layer (scrolls at full speed, tiles every 32): the checked tablecloth."""
    im = canvas(32, H - GROUND)
    px = im.load()
    for y in range(H - GROUND):
        for x in range(32):
            sq = ((x // 8) + (y // 6)) % 2
            px[x, y] = P['cloth_r'] if sq else P['cloth_w']
    dither(px, 0, 0, 32, 2, 'cloth_dk', 'cloth_r', 1)
    for x in range(0, 32, 8):
        for y in range(2, H - GROUND, 6):
            if ((x // 8) + (y // 6)) % 2 == 0:
                px[x, y] = P['cloth_sh']
    return im


# ------------------------------------------------------------------ the meatball
def meatball(frame):
    """12x12, four frames of rolling (the herb flecks go round)."""
    im = canvas(12, 12)
    d = ImageDraw.Draw(im)
    d.ellipse([0, 0, 11, 11], fill=P['meat'], outline=P['meat_dk'])
    d.ellipse([2, 2, 6, 5], fill=P['meat_hi'])
    import math
    for k in range(3):
        a = frame * math.pi / 2 + k * 2 * math.pi / 3
        x, y = 6 + 3.2 * math.cos(a), 6 + 3.2 * math.sin(a)
        d.point((round(x), round(y)), fill=P['herb'])
        d.point((round(x) + 1, round(y)), fill=P['meat_dk'])
    return im


def splat():
    im = canvas(22, 8)
    d = ImageDraw.Draw(im)
    d.ellipse([0, 3, 21, 7], fill=P['sauce'])
    d.ellipse([5, 1, 15, 6], fill=P['meat'], outline=P['meat_dk'])
    for x in (1, 19, 9):
        d.point((x, 2), fill=P['sauce_hi'])
    return im


# ------------------------------------------------------------------ what's in the way
def fork():
    """A fork stuck tines-down in the table: 7 wide, 28 tall."""
    im = canvas(7, 28)
    d = ImageDraw.Draw(im)
    d.rectangle([2, 0, 4, 15], fill=P['steel'])
    d.line([(2, 0), (2, 15)], fill=P['steel_hi'])
    d.rectangle([0, 15, 6, 18], fill=P['steel'])
    for x in (0, 2, 4, 6):
        d.line([(x, 18), (x, 27)], fill=P['steel'])
    d.line([(6, 15), (6, 27)], fill=P['steel_dk'])
    d.line([(4, 1), (4, 14)], fill=P['steel_dk'])
    return im


def colander():
    """An upturned colander: 24 wide, 14 tall."""
    im = canvas(24, 14)
    d = ImageDraw.Draw(im)
    d.pieslice([1, 1, 22, 26], 180, 360, fill=P['steel'], outline=P['steel_dk'])
    d.rectangle([0, 12, 23, 13], fill=P['steel_dk'])
    d.line([(3, 9), (20, 9)], fill=P['steel_hi'])
    for x, y in ((6, 6), (10, 4), (14, 4), (18, 6), (8, 10), (12, 10), (16, 10)):
        d.point((x, y), fill=P['ink'])
    d.rectangle([10, 0, 13, 1], fill=P['steel_dk'])
    return im


def parmesan():
    """A tumbling pile of parmesan: 22 wide, 16 tall."""
    im = canvas(22, 16)
    d = ImageDraw.Draw(im)
    d.polygon([(0, 15), (6, 6), (11, 9), (15, 2), (21, 15)], fill=P['cheese'], outline=P['cheese_dk'])
    d.polygon([(13, 15), (16, 8), (21, 15)], fill=P['cheese_dk'])
    for x, y in ((5, 11), (9, 13), (14, 7), (17, 12), (11, 11)):
        d.point((x, y), fill=P['cheese_hi'])
    d.rectangle([2, 0, 3, 1], fill=P['cheese_hi'])        # a crumb in mid-air
    return im


def bread():
    """A loaf of garlic bread: 34 wide, 10 tall."""
    im = canvas(34, 10)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 1, 33, 9], radius=4, fill=P['bread'], outline=P['bread_dk'])
    d.line([(3, 3), (30, 3)], fill=P['bread_hi'])
    for x in range(5, 31, 6):
        d.line([(x, 2), (x + 2, 6)], fill=P['bread_dk'])
        d.point((x + 1, 5), fill=P['garlic'])
    return im


def bowl():
    """The finish: a big bowl of spaghetti and sauce, 44 wide, 22 tall."""
    im = canvas(44, 22)
    d = ImageDraw.Draw(im)
    d.pieslice([0, -14, 43, 21], 0, 180, fill=P['bowl'], outline=P['bowl_dk'])
    d.rectangle([14, 19, 29, 21], fill=P['bowl_dk'])
    d.ellipse([2, 0, 41, 8], fill=P['noodle'])
    d.ellipse([12, 1, 31, 6], fill=P['sauce'])
    d.point((18, 2), fill=P['sauce_hi'])
    for x in range(4, 40, 5):
        d.point((x, 5), fill=P['bowl_dk'])
    return im


def sprites():
    """{sprite name: image}, all doubled."""
    out = {'mm_sky': big(sky()), 'mm_hills': big(hills()), 'mm_ground': big(ground()),
           'mm_splat': big(splat()), 'mm_bowl': big(bowl()),
           'mm_fork': big(fork()), 'mm_colander': big(colander()), 'mm_parmesan': big(parmesan()),
           'mm_bread': big(bread())}
    for k in range(4):
        out['mm_ball%d' % k] = big(meatball(k))
    return out


if __name__ == '__main__':
    sp = sprites()
    im = sp['mm_sky'].copy()
    for x in (0, 640):
        im.alpha_composite(sp['mm_hills'].crop((0, 0, 640 - 0, 288)), (0, 0))
    for x in range(0, 640, 64):
        im.alpha_composite(sp['mm_ground'], (x, GROUND * S))
    gy = GROUND * S
    for name, x in (('mm_fork', 140), ('mm_colander', 230), ('mm_parmesan', 330), ('mm_bread', 420), ('mm_bowl', 540)):
        s = sp[name]
        im.alpha_composite(s, (x, gy - s.height + (6 if name == 'mm_bowl' else 0)))
    b = sp['mm_ball0']
    im.alpha_composite(b, (60, gy - b.height))
    im.alpha_composite(sp['mm_ball1'], (90, gy - b.height - 40))
    im.save('/tmp/claude-0/run/mm_preview.png')
