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
    """16x16, four frames of rolling (the herb flecks go round)."""
    import math
    im = canvas(16, 16)
    d = ImageDraw.Draw(im)
    d.ellipse([0, 0, 15, 15], fill=P['meat'], outline=P['meat_dk'])
    d.ellipse([3, 2, 8, 6], fill=P['meat_hi'])
    d.point((4, 3), fill=P['bread_hi'])
    d.arc([1, 1, 14, 14], 20, 160, fill=P['meat_dk'])
    for k in range(3):
        a = frame * math.pi / 2 + k * 2 * math.pi / 3
        x, y = round(7.5 + 4.2 * math.cos(a)), round(7.5 + 4.2 * math.sin(a))
        d.rectangle([x, y, x + 1, y], fill=P['herb'])
        d.point((x, y + 1), fill=P['meat_dk'])
    return im


def splat():
    im = canvas(28, 10)
    d = ImageDraw.Draw(im)
    d.ellipse([0, 4, 27, 9], fill=P['sauce'])
    d.ellipse([7, 1, 20, 8], fill=P['meat'], outline=P['meat_dk'])
    for x in (1, 25, 12, 5):
        d.point((x, 3), fill=P['sauce_hi'])
    return im


# ------------------------------------------------------------------ what's in the way
def fork():
    """A fork stuck tines-down in the table: 9 wide, 36 tall."""
    im = canvas(9, 36)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([2, 0, 6, 20], radius=2, fill=P['steel'])
    d.line([(3, 1), (3, 19)], fill=P['steel_hi'])
    d.line([(6, 1), (6, 20)], fill=P['steel_dk'])
    d.rectangle([0, 20, 8, 24], fill=P['steel'])
    d.line([(0, 20), (8, 20)], fill=P['steel_hi'])
    for x in (0, 3, 5, 8):
        d.line([(x, 24), (x, 35)], fill=P['steel'])
    d.line([(8, 21), (8, 35)], fill=P['steel_dk'])
    return im


def colander():
    """An upturned colander: 30 wide, 18 tall."""
    im = canvas(30, 18)
    d = ImageDraw.Draw(im)
    d.pieslice([1, 1, 28, 34], 180, 360, fill=P['steel'], outline=P['steel_dk'])
    d.rectangle([0, 15, 29, 17], fill=P['steel_dk'])
    d.line([(1, 15), (28, 15)], fill=P['steel_hi'])
    d.arc([5, 4, 24, 30], 200, 260, fill=P['steel_hi'])
    for x, y in ((7, 8), (12, 5), (17, 5), (22, 8), (9, 12), (14, 10), (19, 10), (24, 12), (5, 13)):
        d.point((x, y), fill=P['ink'])
    d.rectangle([12, 0, 17, 1], fill=P['steel_dk'])
    return im


def parmesan():
    """A tumbling pile of parmesan: 28 wide, 20 tall."""
    im = canvas(28, 20)
    d = ImageDraw.Draw(im)
    d.polygon([(0, 19), (7, 8), (13, 11), (19, 3), (27, 19)], fill=P['cheese'], outline=P['cheese_dk'])
    d.polygon([(17, 19), (21, 10), (27, 19)], fill=P['cheese_dk'])
    d.polygon([(3, 19), (8, 13), (11, 19)], fill=P['cheese_hi'])
    for x, y in ((6, 14), (12, 16), (18, 9), (22, 15), (14, 13), (9, 17)):
        d.point((x, y), fill=P['cheese_dk'])
    d.rectangle([3, 1, 4, 2], fill=P['cheese_hi'])
    d.rectangle([24, 4, 25, 5], fill=P['cheese'])
    return im


def bread():
    """A loaf of garlic bread: 42 wide, 12 tall."""
    im = canvas(42, 12)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 1, 41, 11], radius=5, fill=P['bread'], outline=P['bread_dk'])
    d.line([(4, 3), (37, 3)], fill=P['bread_hi'])
    d.line([(4, 10), (37, 10)], fill=P['bread_dk'])
    for x in range(6, 38, 7):
        d.line([(x, 2), (x + 3, 8)], fill=P['bread_dk'])
        d.point((x + 2, 6), fill=P['garlic'])
        d.point((x + 4, 4), fill=P['garlic'])
    return im


def bowl():
    """The finish: a big bowl of spaghetti and sauce, 54 wide, 26 tall."""
    im = canvas(54, 26)
    d = ImageDraw.Draw(im)
    d.pieslice([0, -18, 53, 25], 0, 180, fill=P['bowl'], outline=P['bowl_dk'])
    d.rectangle([18, 23, 35, 25], fill=P['bowl_dk'])
    d.ellipse([2, 0, 51, 9], fill=P['noodle'])
    d.ellipse([14, 1, 39, 7], fill=P['sauce'])
    d.point((21, 2), fill=P['sauce_hi'])
    d.point((22, 2), fill=P['sauce_hi'])
    for x in range(5, 50, 6):
        d.point((x, 6), fill=P['bowl_dk'])
    return im


def bowl_full():
    """The bowl with the meatball landed in the spaghetti."""
    im = bowl()
    m = meatball(0)
    im.alpha_composite(m, (19, -5 if False else 0))
    im2 = canvas(54, 30)
    im2.alpha_composite(bowl(), (0, 4))
    m = meatball(1)
    im2.alpha_composite(m, (19, 0))
    d = ImageDraw.Draw(im2)
    # a few strands of spaghetti draped over it
    for x0, x1 in ((18, 26), (27, 36), (22, 31)):
        d.arc([x0, 5, x1, 15], 200, 340, fill=P['noodle'])
    d.point((24, 14), fill=P['sauce'])
    return im2


def finale():
    """The close-up at the end: the meatball sitting on a heap of spaghetti, full screen."""
    import math
    import random
    im = sky()
    px = im.load()
    d = ImageDraw.Draw(im)
    # sunburst behind the bowl
    cx, cy = 160, 64
    for k in range(16):
        a0 = k * math.pi / 8
        a1 = a0 + math.pi / 16
        d.polygon([(cx, cy), (cx + 260 * math.cos(a0), cy + 260 * math.sin(a0)),
                   (cx + 260 * math.cos(a1), cy + 260 * math.sin(a1))], fill=P['sky_lo'])
    # the tablecloth
    g = ground()
    for x in range(0, W, 32):
        im.alpha_composite(g, (x, GROUND))
    # the bowl, big
    d.pieslice([70, 40, 250, 150], 0, 180, fill=P['bowl'], outline=P['bowl_dk'])
    d.rectangle([120, 142, 200, 147], fill=P['bowl_dk'])
    d.arc([78, 50, 242, 140], 20, 160, fill=P['bowl_dk'])
    d.line([(96, 104), (110, 112)], fill=(255, 255, 255))
    # the heap of spaghetti
    rnd = random.Random(5)
    d.ellipse([74, 70, 246, 106], fill=P['noodle'])
    d.ellipse([96, 50, 224, 96], fill=P['noodle'])
    for _ in range(70):
        x = rnd.randint(84, 236)
        y = rnd.randint(58, 100)
        if ((x - 160) / 80) ** 2 + ((y - 82) / 26) ** 2 < 1:
            d.arc([x - 7, y - 3, x + 7, y + 4], rnd.choice([0, 180]), rnd.choice([150, 330]), fill=P['cheese_dk'])
    # strands over the rim
    for x in (88, 118, 196, 226):
        d.line([(x, 92), (x - 2, 106), (x + 1, 116)], fill=P['noodle'])
    # the sauce, and the meatball on top
    d.ellipse([118, 52, 202, 80], fill=P['sauce'])
    d.ellipse([130, 56, 160, 66], fill=P['sauce_hi'])
    for x in (126, 196):
        d.line([(x, 72), (x, 84)], fill=P['sauce'], width=2)
    # the meatball, drawn big at the same pixel size as everything else
    mb = canvas(46, 44)
    md = ImageDraw.Draw(mb)
    md.ellipse([0, 0, 45, 43], fill=P['meat_dk'])
    md.ellipse([1, 0, 41, 37], fill=P['meat'])
    md.ellipse([8, 6, 22, 15], fill=P['meat_hi'])
    md.ellipse([11, 8, 15, 11], fill=P['bread_hi'])
    rr = random.Random(9)
    for _ in range(26):
        x, y = rr.randint(6, 39), rr.randint(6, 38)
        if ((x - 22.5) / 20) ** 2 + ((y - 21.5) / 19) ** 2 < 1:
            md.rectangle([x, y, x + 1, y], fill=rr.choice([P['herb'], P['meat_dk'], P['meat_hi']]))
    im.alpha_composite(mb, (137, 16))
    # a basil leaf and some steam and sparkle
    d.polygon([(176, 30), (192, 24), (186, 36)], fill=P['herb'])
    d.line([(176, 30), (190, 27)], fill=(110, 170, 80))
    for k, x in enumerate((122, 160, 198)):
        for t in range(0, 22, 2):
            d.point((x + int(3 * math.sin((t + k * 4) / 3)), 14 - t // 2 + 0), fill=(250, 246, 236))
    for x, y in ((60, 30), (262, 40), (44, 70), (280, 84), (100, 20)):
        d.line([(x - 3, y), (x + 3, y)], fill=P['sun'])
        d.line([(x, y - 3), (x, y + 3)], fill=P['sun'])
    return im


def sprites():
    """{sprite name: image}, all doubled."""
    out = {'mm_sky': big(sky()), 'mm_hills': big(hills()), 'mm_ground': big(ground()),
           'mm_splat': big(splat()), 'mm_bowl': big(bowl()),
           'mm_fork': big(fork()), 'mm_colander': big(colander()), 'mm_parmesan': big(parmesan()),
           'mm_bread': big(bread()), 'mm_bowlfull': big(bowl_full()), 'mm_finale': big(finale())}
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
