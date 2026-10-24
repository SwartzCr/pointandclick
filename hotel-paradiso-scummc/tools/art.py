"""Pixel art for the Hotel Paradiso room, drawn procedurally at SCUMM v6 resolution.

render(state) returns a 320x144 RGB image of the room in the given object states.
Object state images are cropped from renders, so every object rectangle must be
self-contained (nothing an object's state changes may spill outside its rect).
"""
from PIL import Image, ImageDraw

W, H = 320, 144
FLOOR_Y = 96

C = {
    # wall
    'wall': (30, 72, 80), 'wall_hi': (38, 88, 96), 'wall_dk': (22, 54, 60), 'wall_dot': (52, 104, 104),
    'crown': (196, 176, 128), 'crown_dk': (140, 120, 82),
    'base': (58, 34, 26), 'base_hi': (88, 54, 38),
    # carpet
    'carpet': (92, 28, 40), 'carpet_dk': (70, 20, 32), 'carpet_hi': (120, 44, 52), 'carpet_gold': (150, 112, 56),
    # wood
    'wood': (108, 66, 38), 'wood_dk': (74, 44, 26), 'wood_hi': (140, 92, 54), 'wood_xdk': (44, 26, 16),
    'brass': (214, 176, 80), 'brass_dk': (150, 112, 40),
    # misc
    'black': (8, 8, 12), 'white': (236, 232, 220), 'cream': (214, 206, 180), 'grey': (120, 124, 128),
    'grey_dk': (64, 68, 74), 'grey_hi': (170, 172, 172),
    'red': (190, 36, 40), 'red_dk': (120, 18, 26), 'red_hi': (226, 82, 72),
    'curtain': (138, 26, 44), 'curtain_dk': (92, 14, 30), 'curtain_hi': (176, 52, 66),
    'sky': (18, 22, 58), 'sky2': (34, 36, 88), 'bldg': (14, 14, 30), 'bldg2': (26, 26, 46),
    'win_y': (240, 210, 110), 'neon': (255, 70, 140), 'moon': (240, 236, 200),
    'tv_body': (46, 40, 36), 'tv_scr': (28, 34, 36), 'tv_glow': (90, 170, 220), 'tv_glow2': (170, 220, 250),
    'tv_glow3': (40, 90, 150),
    'fridge': (196, 192, 176), 'fridge_dk': (150, 146, 132), 'fridge_in': (232, 238, 228), 'fridge_in2': (196, 210, 206),
    'bottle': (60, 130, 70), 'bottle2': (170, 90, 30), 'candy': (200, 40, 40), 'candy2': (240, 200, 60),
    'shade': (226, 196, 140), 'shade_dk': (176, 144, 92), 'shade_lit': (255, 236, 170), 'bulb': (255, 252, 220),
    'glow': (66, 112, 100), 'glow2': (112, 148, 116),
    'phone': (34, 34, 38), 'phone_hi': (78, 78, 86),
    'sheet': (230, 226, 210), 'sheet_dk': (186, 180, 160), 'blanket': (58, 90, 140), 'blanket_dk': (40, 64, 104),
    'blanket_hi': (92, 124, 170), 'pillow': (244, 240, 228),
    'frame_g': (200, 160, 70), 'frame_gd': (140, 104, 40), 'sea': (56, 100, 150), 'sea2': (90, 140, 180),
    'sand': (210, 186, 130), 'sun': (250, 200, 110), 'sky_p': (230, 150, 120),
    'steel': (96, 102, 110), 'steel_dk': (60, 64, 70), 'steel_hi': (150, 156, 164), 'dial': (210, 210, 200),
    'card': (232, 196, 60), 'card_dk': (160, 120, 30), 'safe_in': (30, 32, 36),
    'hall': (250, 222, 160), 'hall2': (220, 184, 120), 'hall3': (170, 130, 80),
    'match': (40, 40, 120), 'match_hi': (240, 220, 200),
    'tag': (222, 40, 60),
    # bathroom
    'tile': (200, 224, 216), 'tile_hi': (226, 240, 234), 'grout': (150, 178, 170),
    'tile_band': (62, 128, 132), 'floor_a': (222, 226, 220), 'floor_b': (150, 176, 180),
    'porcelain': (240, 240, 236), 'porcelain_dk': (188, 192, 194), 'porcelain_sh': (150, 156, 160),
    'chrome': (196, 204, 212), 'chrome_dk': (110, 118, 128),
    'water': (120, 176, 214), 'water_hi': (196, 228, 246), 'water_dk': (64, 116, 168),
    'shower': (156, 202, 222), 'shower_dk': (104, 156, 184), 'shower_hi': (204, 234, 244),
    'mat': (52, 92, 150), 'mat_dk': (36, 66, 116), 'mat_hi': (96, 132, 186),
    'towel': (240, 232, 214), 'towel_dk': (198, 188, 166), 'towel_band': (62, 128, 132),
    'soap': (236, 160, 176), 'soap_hi': (250, 204, 214),
    'glass': (168, 196, 204), 'glass_hi': (222, 238, 242), 'glass_dk': (120, 150, 162),
    'duck': (246, 208, 60), 'duck_beak': (232, 120, 40),
    'bottle_b': (90, 140, 190), 'bottle_w': (236, 236, 230),
}


def rect(d, x0, y0, x1, y1, col):
    """Filled rectangle, inclusive-exclusive like range()."""
    if x1 > x0 and y1 > y0:
        d.rectangle([x0, y0, x1 - 1, y1 - 1], fill=C[col])


def dither(img, x0, y0, x1, y1, a, b, level):
    """2x2 ordered dither between colors a and b. level 0..4 = share of b."""
    bayer = [[0, 2], [3, 1]]
    pa, pb = C[a], C[b]
    px = img.load()
    for y in range(y0, y1):
        for x in range(x0, x1):
            px[x, y] = pb if bayer[y % 2][x % 2] < level else pa


def vgrad(img, x0, y0, x1, y1, a, b):
    h = max(1, y1 - y0)
    for y in range(y0, y1):
        lvl = round(4 * (y - y0) / h)
        dither(img, x0, y, x1, y + 1, a, b, lvl)


def put(img, x, y, col):
    if 0 <= x < img.width and 0 <= y < img.height:
        img.putpixel((x, y), C[col])


# --------------------------------------------------------------------------- room
DEFAULT = dict(tv=0, curtains=0, minibar=0, drawer=0, lamp=0, safe=0, door=0, dresser=0,
               table_matchbook=0, table_candy=0, table_keycard=0, table_uniform=0,
               table_towel=0, table_soap=0)

# Coffee table on the floor, x 112..208, top surface y 105..116. Items set down on it sit in six
# 16-pixel slots across the top (y 104..120), in TABLE_SLOTS order.
TABLE_X0, TABLE_X1 = 112, 208
TABLE_SLOTS = ['matchbook', 'candy', 'keycard', 'uniform', 'towel', 'soap']


def table_slot_x(item):
    return TABLE_X0 + 16 * TABLE_SLOTS.index(item)


def draw_wall(img, d):
    rect(d, 0, 0, W, FLOOR_Y, 'wall')
    # wallpaper stripes with damask dots
    for x in range(0, W, 16):
        rect(d, x + 6, 6, x + 10, FLOOR_Y - 6, 'wall_hi')
        rect(d, x + 5, 6, x + 6, FLOOR_Y - 6, 'wall_dk')
        for y in range(12, FLOOR_Y - 8, 12):
            put(img, x + 13, y, 'wall_dot')
            put(img, x + 12, y + 1, 'wall_dot')
            put(img, x + 14, y + 1, 'wall_dot')
            put(img, x + 13, y + 2, 'wall_dot')
    # crown moulding
    rect(d, 0, 0, W, 4, 'crown')
    rect(d, 0, 4, W, 6, 'crown_dk')
    for x in range(0, W, 4):
        put(img, x, 2, 'crown_dk')
    # baseboard
    rect(d, 0, FLOOR_Y - 6, W, FLOOR_Y, 'base')
    rect(d, 0, FLOOR_Y - 6, W, FLOOR_Y - 5, 'base_hi')


def draw_floor(img, d):
    rect(d, 0, FLOOR_Y, W, H, 'carpet')
    # diamond carpet pattern, rows widen toward the viewer
    row = 0
    y = FLOOR_Y + 3
    step = 6
    while y < H:
        off = (row % 2) * step // 2
        for x in range(-step + off, W + step, step * 2):
            put(img, x, y, 'carpet_gold')
            put(img, x - 1, y, 'carpet_hi')
            put(img, x + 1, y, 'carpet_hi')
        y += 4 + row
        row += 1
        step += 2
    # shadow line under the baseboard
    rect(d, 0, FLOOR_Y, W, FLOOR_Y + 1, 'carpet_dk')


def draw_side_doorway(img, d, right=False, inside='bathroom'):
    """A doorway in the side wall, seen at an angle at the edge of the screen.
    Bedroom: left edge, looking into the bathroom. Bathroom: right edge, back
    into the bedroom."""
    def X(x):
        return W - 1 - x if right else x
    # the side wall itself: a darker strip whose foot slants down to the floor
    for x in range(0, 14):
        foot = 112 - x                     # floor line in perspective
        wall_c = 'grout' if inside == 'bedroom' else 'wall_dk'
        for y in range(0, foot):
            put(img, X(x), y, wall_c)
    # the opening: a parallelogram with a wooden frame
    for x in range(1, 12):
        top, bot = 18 + x // 2, 110 - x
        for y in range(top, bot):
            if x in (1, 11) or y in (top, top + 1):
                c = 'wood_hi' if x == 1 else 'wood_dk'
            elif inside == 'bathroom':
                c = 'tile_hi' if (y // 6 + x // 4) % 2 else 'tile'
                if y > bot - 10:
                    c = 'floor_a' if (x + y) % 4 < 2 else 'floor_b'
            else:
                c = 'wall_hi' if (x + y // 8) % 3 else 'wall'
                if y > bot - 10:
                    c = 'carpet'
            put(img, X(x), y, c)


def draw_door(img, d, st):
    # frame
    rect(d, 14, 18, 66, FLOOR_Y, 'wood_hi')
    rect(d, 16, 20, 64, FLOOR_Y, 'wood_dk')
    if st == 0:
        rect(d, 17, 21, 63, FLOOR_Y, 'wood')
        # panels
        for (px, py, pw, ph) in [(21, 26, 16, 26), (43, 26, 16, 26), (21, 58, 16, 30), (43, 58, 16, 30)]:
            rect(d, px, py, px + pw, py + ph, 'wood_dk')
            rect(d, px + 1, py + 1, px + pw, py + ph, 'wood_hi')
            rect(d, px + 1, py + 1, px + pw - 1, py + ph - 1, 'wood')
        # peephole
        rect(d, 39, 34, 41, 36, 'brass')
        # handle + key-card slot
        rect(d, 55, 55, 61, 57, 'brass')
        rect(d, 56, 57, 58, 59, 'brass_dk')
        rect(d, 56, 46, 61, 53, 'grey_dk')
        rect(d, 57, 47, 60, 49, 'black')
        put(img, 58, 51, 'red_hi')
        # do-not-disturb hanger
        rect(d, 54, 57, 62, 69, 'tag')
        rect(d, 55, 59, 61, 60, 'white')
        rect(d, 55, 62, 60, 63, 'white')
        rect(d, 55, 65, 61, 66, 'white')
        # room number plaque
        rect(d, 34, 22, 46, 25, 'brass')
        for x in (36, 39, 42):
            put(img, x, 23, 'wood_xdk')
    else:
        # open: lit hallway beyond, door swung inward against the frame
        vgrad(img, 17, 21, 63, FLOOR_Y, 'hall', 'hall2')
        rect(d, 17, 80, 63, FLOOR_Y, 'hall3')
        for x in range(20, 63, 8):
            rect(d, x, 82, x + 4, 83, 'hall2')
        rect(d, 30, 30, 50, 60, 'hall2')  # far door
        rect(d, 32, 32, 48, 58, 'hall3')
        rect(d, 37, 24, 43, 27, 'white')  # exit sign glow
        put(img, 39, 25, 'red'); put(img, 41, 25, 'red')
        rect(d, 17, 21, 23, FLOOR_Y, 'wood')
        rect(d, 22, 21, 23, FLOOR_Y, 'wood_dk')


def draw_dresser_tv(img, d, tv, dresser=0):
    """dresser: 0 closed, 1 top drawer open with the bellhop uniform inside,
    2 top drawer open and empty. Everything stays inside x 72..128, y 64..96."""
    rect(d, 72, 64, 128, FLOOR_Y, 'wood_dk')
    rect(d, 72, 64, 128, 67, 'wood_hi')
    for y in (69, 78, 87):
        rect(d, 75, y, 125, y + 7, 'wood')
        rect(d, 75, y, 125, y + 1, 'wood_hi')
        rect(d, 97, y + 3, 103, y + 4, 'brass')
    if dresser:
        # top drawer pulled out toward the viewer: its inside shows above a
        # lowered drawer front that now covers the middle drawer
        rect(d, 74, 68, 126, 77, 'wood_xdk')
        rect(d, 74, 68, 126, 69, 'wood_dk')
        if dresser == 1:
            # folded bellhop jacket with brass buttons, pillbox hat beside it
            rect(d, 86, 69, 106, 77, 'red')
            rect(d, 86, 75, 106, 77, 'red_dk')
            rect(d, 95, 69, 97, 77, 'red_dk')
            for x in (96,):
                put(img, x, 71, 'brass'); put(img, x, 74, 'brass')
            rect(d, 86, 69, 90, 71, 'brass')
            rect(d, 102, 69, 106, 71, 'brass')
            rect(d, 109, 71, 117, 77, 'red')
            rect(d, 109, 74, 117, 75, 'brass')
        rect(d, 73, 77, 127, 85, 'wood')
        rect(d, 73, 77, 127, 78, 'wood_hi')
        rect(d, 73, 84, 127, 85, 'wood_xdk')
        rect(d, 97, 80, 103, 81, 'brass')
    # TV
    rect(d, 80, 34, 122, 64, 'tv_body')
    rect(d, 80, 34, 122, 35, 'grey_dk')
    rect(d, 84, 38, 114, 60, 'black')
    if tv == 0:
        rect(d, 85, 39, 113, 59, 'tv_scr')
        rect(d, 87, 41, 92, 42, 'grey_dk')
        put(img, 88, 43, 'grey_dk')
    else:
        rect(d, 85, 39, 113, 59, 'tv_glow3')
        # weather map: the "Hotel Paradiso Channel"
        rect(d, 86, 40, 112, 46, 'tv_glow')
        rect(d, 88, 41, 102, 42, 'white')
        rect(d, 88, 43, 96, 44, 'tv_glow2')
        for x in range(86, 113, 3):
            put(img, x, 52 + (x // 3) % 2, 'tv_glow')
        rect(d, 90, 49, 97, 55, 'candy2')     # sun icon
        rect(d, 101, 50, 110, 56, 'tv_glow2')  # cloud
        rect(d, 86, 57, 113, 59, 'red')        # ticker
        for x in range(88, 112, 5):
            rect(d, x, 57, x + 3, 58, 'white')
    # knobs + antenna
    rect(d, 116, 40, 120, 44, 'grey')
    rect(d, 116, 48, 120, 52, 'grey')
    rect(d, 116, 56, 120, 58, 'red_hi' if tv else 'grey_dk')
    d.line([(96, 34), (88, 22)], fill=C['grey'])
    d.line([(104, 34), (114, 24)], fill=C['grey'])


def draw_window(img, d, open_):
    # window frame always visible behind curtains
    rect(d, 140, 10, 188, 66, 'cream')
    if open_:
        vgrad(img, 142, 12, 186, 64, 'sky', 'sky2')
        rect(d, 174, 16, 180, 22, 'moon')
        put(img, 174, 16, 'sky'); put(img, 179, 21, 'sky2')
        for (bx, by, bw) in [(142, 40, 10), (152, 32, 8), (160, 44, 12), (172, 36, 9), (181, 46, 5)]:
            rect(d, bx, by, bx + bw, 64, 'bldg' if bx % 2 else 'bldg2')
            for wy in range(by + 3, 62, 4):
                for wx in range(bx + 2, bx + bw - 1, 3):
                    if (wx * 7 + wy * 3) % 5 < 2:
                        put(img, wx, wy, 'win_y')
        rect(d, 153, 28, 160, 31, 'neon')  # neon sign on a roof
        rect(d, 163, 10, 165, 66, 'cream')
        rect(d, 140, 37, 188, 39, 'cream')
        # curtains gathered at the sides
        for (cx0, cx1) in [(134, 146), (182, 194)]:
            rect(d, cx0, 6, cx1, 74, 'curtain')
            for x in range(cx0 + 2, cx1, 4):
                rect(d, x, 8, x + 1, 74, 'curtain_dk')
                rect(d, x + 1, 8, x + 2, 74, 'curtain_hi')
        rect(d, 134, 40, 146, 43, 'brass')
        rect(d, 182, 40, 194, 43, 'brass')
    else:
        rect(d, 134, 6, 194, 74, 'curtain')
        for x in range(136, 194, 6):
            rect(d, x, 8, x + 2, 74, 'curtain_dk')
            rect(d, x + 3, 8, x + 4, 74, 'curtain_hi')
        rect(d, 162, 8, 166, 74, 'curtain_dk')
        # thin moonlight sliver between the curtains
        rect(d, 164, 14, 165, 70, 'sky2')
    # curtain rod
    rect(d, 136, 5, 192, 7, 'brass')
    rect(d, 136, 4, 138, 8, 'brass_dk')
    rect(d, 190, 4, 192, 8, 'brass_dk')


def draw_minibar(img, d, st):
    rect(d, 144, 74, 176, FLOOR_Y, 'fridge_dk')
    if st == 0:
        rect(d, 145, 75, 175, FLOOR_Y - 1, 'fridge')
        rect(d, 170, 79, 172, 91, 'grey')
        rect(d, 148, 77, 166, 81, 'fridge_dk')   # price sticker
        rect(d, 149, 78, 151, 80, 'red')
    else:
        rect(d, 146, 76, 174, FLOOR_Y - 2, 'fridge_in')
        rect(d, 146, 76, 174, 77, 'white')
        rect(d, 146, 85, 174, 86, 'fridge_in2')
        for i, x in enumerate(range(149, 172, 5)):
            rect(d, x, 79, x + 3, 85, 'bottle' if i % 2 else 'bottle2')
            rect(d, x + 1, 78, x + 2, 79, 'grey')
        if st == 1:
            rect(d, 152, 88, 166, 92, 'candy')
            rect(d, 156, 88, 162, 92, 'candy2')
        # door swung out to the right edge
        rect(d, 174, 74, 176, FLOOR_Y, 'fridge')


def draw_nightstand(img, d, st):
    rect(d, 200, 70, 232, FLOOR_Y, 'wood_dk')
    rect(d, 200, 70, 232, 72, 'wood_hi')
    rect(d, 203, 85, 229, FLOOR_Y - 1, 'wood')
    if st == 0:
        rect(d, 203, 75, 229, 83, 'wood')
        rect(d, 203, 75, 229, 76, 'wood_hi')
        rect(d, 213, 78, 219, 80, 'brass')
    else:
        # drawer pulled out toward the viewer
        rect(d, 201, 75, 231, 84, 'wood_xdk')
        rect(d, 201, 82, 231, 88, 'wood_hi')
        rect(d, 201, 87, 231, 88, 'wood_dk')
        rect(d, 213, 84, 219, 86, 'brass')
        if st == 1:
            rect(d, 210, 77, 220, 81, 'match')
            rect(d, 211, 78, 215, 79, 'match_hi')


def draw_lamp(img, d, on):
    # everything for the lamp lives in x 200..216, y 32..72
    if on:
        # soft dithered halo around the bulb, clipped to the lamp's rectangle
        bayer = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]
        for y in range(32, 70):
            for x in range(200, 216):
                dist = ((x - 207.5) ** 2 + ((y - 50) * 0.8) ** 2) ** 0.5
                lvl = max(0, 17 - int(dist * 1.05))
                if bayer[y % 4][x % 4] < lvl:
                    img.putpixel((x, y), C['glow2'] if dist < 6 else C['glow'])
    shade = 'shade_lit' if on else 'shade'
    d.polygon([(204, 40), (212, 40), (215, 52), (201, 52)], fill=C[shade])
    d.line([(201, 52), (215, 52)], fill=C['shade_dk'])
    if on:
        rect(d, 205, 53, 211, 55, 'bulb')
    rect(d, 207, 53, 209, 66, 'brass')
    rect(d, 204, 66, 212, 70, 'brass_dk')


def draw_phone(img, d):
    rect(d, 218, 64, 230, 70, 'phone')
    rect(d, 217, 61, 231, 63, 'phone_hi')
    rect(d, 218, 60, 220, 62, 'phone')
    rect(d, 228, 60, 230, 62, 'phone')
    for x in (221, 224, 227):
        put(img, x, 66, 'grey_hi')
        put(img, x, 68, 'grey_hi')


def draw_bed(img, d):
    # headboard against the wall
    rect(d, 236, 46, 316, 84, 'wood_dk')
    rect(d, 238, 48, 314, 82, 'wood')
    for x in range(244, 312, 12):
        rect(d, x, 52, x + 6, 78, 'wood_hi')
        rect(d, x + 1, 53, x + 6, 78, 'wood')
    rect(d, 236, 46, 316, 48, 'wood_hi')
    # mattress seen in steep perspective toward the viewer
    rect(d, 238, 74, 316, 120, 'sheet')
    rect(d, 244, 76, 274, 86, 'pillow')
    rect(d, 280, 76, 310, 86, 'pillow')
    rect(d, 244, 85, 274, 86, 'sheet_dk')
    rect(d, 280, 85, 310, 86, 'sheet_dk')
    rect(d, 238, 90, 316, 120, 'blanket')
    rect(d, 238, 90, 316, 93, 'sheet')
    for y in range(96, 120, 6):
        rect(d, 238, y, 316, y + 1, 'blanket_dk')
    rect(d, 238, 120, 316, 128, 'blanket_dk')
    rect(d, 238, 120, 316, 121, 'blanket_hi')
    rect(d, 236, 74, 238, 128, 'wood_dk')
    rect(d, 316, 74, 318, 128, 'wood_dk')
    rect(d, 236, 128, 318, 132, 'wood_xdk')


def draw_painting_safe(img, d, st):
    """Painting above the bed (x 248..296, y 16..40). st: 0 painting, 1 safe closed,
    2 safe open with key card, 3 safe open and empty."""
    if st == 0:
        rect(d, 248, 16, 296, 40, 'frame_g')
        rect(d, 249, 17, 295, 39, 'frame_gd')
        rect(d, 251, 19, 293, 37, 'sky_p')
        rect(d, 251, 27, 293, 32, 'sea')
        rect(d, 251, 28, 293, 29, 'sea2')
        rect(d, 251, 32, 293, 37, 'sand')
        rect(d, 266, 23, 272, 27, 'sun')
        d.line([(282, 31), (284, 22)], fill=C['wood_dk'])
        rect(d, 280, 21, 288, 23, 'bottle')
        return
    # wall safe set into the wallpaper
    rect(d, 252, 18, 286, 40, 'steel_dk')
    if st == 1:
        rect(d, 253, 19, 285, 39, 'steel')
        rect(d, 253, 19, 285, 20, 'steel_hi')
        rect(d, 263, 24, 273, 34, 'steel_dk')
        rect(d, 265, 26, 271, 32, 'dial')
        put(img, 268, 26, 'black'); put(img, 268, 27, 'black')
        rect(d, 278, 27, 282, 31, 'steel_hi')
    else:
        rect(d, 254, 20, 284, 38, 'safe_in')
        if st == 2:
            rect(d, 262, 31, 276, 37, 'card')
            rect(d, 262, 33, 276, 34, 'card_dk')
            rect(d, 264, 35, 268, 36, 'white')
        # door swung open to the left
        rect(d, 248, 18, 254, 40, 'steel')
        rect(d, 249, 26, 252, 30, 'dial')
    # painting now hangs crooked to the right of the safe
    d.polygon([(286, 14), (296, 16), (296, 40), (288, 41)], fill=C['frame_g'])
    d.polygon([(288, 17), (294, 18), (294, 38), (289, 39)], fill=C['sky_p'])
    rect(d, 289, 29, 294, 34, 'sea')


def draw_coffee_table(img, d, s):
    x0, x1 = TABLE_X0, TABLE_X1
    rect(d, x0 + 2, 126, x1 + 2, 129, 'carpet_dk')          # shadow on the carpet
    for lx in (x0 + 2, x1 - 6):                              # front legs
        rect(d, lx, 117, lx + 4, 128, 'wood_dk')
        rect(d, lx, 117, lx + 1, 128, 'wood')
    for lx in (x0 + 8, x1 - 12):                             # back legs, shorter
        rect(d, lx, 117, lx + 3, 123, 'wood_xdk')
    d.polygon([(x0 + 4, 105), (x1 - 4, 105), (x1 - 1, 116), (x0, 116)], fill=C['wood'])  # top
    d.line([(x0 + 4, 105), (x1 - 4, 105)], fill=C['wood_hi'])
    for x, y in ((x0 + 10, 108), (x0 + 30, 111), (x0 + 48, 108), (x0 + 22, 114), (x0 + 56, 113),
                 (x0 + 70, 109), (x0 + 80, 113)):
        rect(d, x, y, x + 7, y + 1, 'wood_hi')               # grain
    rect(d, x0, 116, x1, 120, 'wood_dk')                     # front edge
    rect(d, x0, 116, x1, 117, 'wood_hi')
    # things set down on it, one per slot (offsets are relative to the slot)
    if s['table_matchbook']:
        sx = table_slot_x('matchbook')
        rect(d, sx + 3, 110, sx + 13, 114, 'match')
        rect(d, sx + 4, 111, sx + 8, 112, 'match_hi')
    if s['table_candy']:
        sx = table_slot_x('candy')
        rect(d, sx + 2, 110, sx + 14, 114, 'candy')
        rect(d, sx + 6, 110, sx + 11, 114, 'candy2')
    if s['table_keycard']:
        sx = table_slot_x('keycard')
        rect(d, sx + 2, 110, sx + 14, 115, 'card')
        rect(d, sx + 2, 112, sx + 14, 113, 'card_dk')
        rect(d, sx + 4, 113, sx + 7, 114, 'white')
    if s['table_uniform']:
        sx = table_slot_x('uniform')
        rect(d, sx + 1, 107, sx + 14, 115, 'red')
        rect(d, sx + 1, 113, sx + 14, 115, 'red_dk')
        rect(d, sx + 7, 107, sx + 8, 115, 'red_dk')
        put(img, sx + 7, 109, 'brass'); put(img, sx + 7, 112, 'brass')
        rect(d, sx + 1, 107, sx + 4, 109, 'brass')
        rect(d, sx + 11, 107, sx + 14, 109, 'brass')
    if s['table_towel']:
        sx = table_slot_x('towel')
        rect(d, sx + 1, 107, sx + 15, 115, 'towel')
        rect(d, sx + 1, 113, sx + 15, 115, 'towel_dk')
        rect(d, sx + 1, 109, sx + 15, 110, 'towel_band')
    if s['table_soap']:
        sx = table_slot_x('soap')
        rect(d, sx + 4, 110, sx + 12, 114, 'soap')
        rect(d, sx + 5, 110, sx + 11, 111, 'soap_hi')


def render(state=None):
    s = dict(DEFAULT)
    if state:
        s.update(state)
    img = Image.new('RGB', (W, H))
    d = ImageDraw.Draw(img)
    draw_wall(img, d)
    draw_floor(img, d)
    draw_side_doorway(img, d)
    draw_door(img, d, s['door'])
    draw_dresser_tv(img, d, s['tv'], s['dresser'])
    draw_window(img, d, s['curtains'])
    draw_minibar(img, d, s['minibar'])
    draw_nightstand(img, d, s['drawer'])
    draw_lamp(img, d, s['lamp'])
    draw_phone(img, d)
    draw_bed(img, d)
    draw_painting_safe(img, d, s['safe'])
    draw_coffee_table(img, d, s)
    return img


# --------------------------------------------------------------------------- actor
# The player. Frames are 24x52 with feet at the bottom row. Every frame can be
# drawn in either outfit: the bathrobe, or the bellhop uniform found on the bed
# (same body and animation, recoloured, plus buttons and a pillbox hat).
FW, FH = 24, 52
ROBE = {
    'skin': (232, 176, 136), 'skin_dk': (184, 124, 92), 'hair': (70, 42, 30),
    'robe': (238, 236, 228), 'robe_dk': (180, 178, 172), 'belt': (60, 110, 170),
    'leg': (214, 160, 122), 'leg_back': (184, 124, 92), 'slipper': (190, 50, 60),
    'eye': (20, 20, 24), 'mouth': (120, 40, 40), 'stripe': (60, 110, 170),
}
BELLHOP = dict(ROBE, **{
    'robe': (176, 30, 40), 'robe_dk': (118, 16, 28), 'belt': (222, 182, 70),
    'leg': (40, 40, 64), 'leg_back': (26, 26, 44), 'slipper': (16, 16, 20),
    'stripe': (222, 182, 70), 'hat': (176, 30, 40), 'hat_band': (222, 182, 70),
})
OUTFITS = {'robe': ROBE, 'bellhop': BELLHOP}
A = ROBE   # palette used by _r(); switched per frame by _use()


def _use(outfit):
    global A
    A = OUTFITS[outfit]
    return outfit == 'bellhop'


def _frame():
    return Image.new('RGB', (FW, FH), (255, 0, 255))


def _r(d, x0, y0, x1, y1, col):
    if x1 > x0 and y1 > y0:
        d.rectangle([x0, y0, x1 - 1, y1 - 1], fill=A[col])


def actor_front(step=0, talk=False, outfit='robe'):
    bellhop = _use(outfit)
    im = _frame(); d = ImageDraw.Draw(im)
    # legs
    lo = [0, -2, 2][step]
    _r(d, 8, 40, 11, 49 + min(0, lo), 'leg')
    _r(d, 13, 40, 16, 49 - max(0, lo), 'leg')
    _r(d, 6, 49 + min(0, lo), 11, 52 + min(0, lo), 'slipper')
    _r(d, 13, 49 - max(0, lo), 18, 52 - max(0, lo), 'slipper')
    # robe
    _r(d, 5, 18, 19, 42, 'robe')
    _r(d, 4, 20, 6, 36, 'robe_dk')
    _r(d, 18, 20, 20, 36, 'robe_dk')
    _r(d, 11, 18, 13, 30, 'robe_dk')   # lapel opening
    _r(d, 5, 29, 19, 31, 'belt')
    _r(d, 5, 40, 19, 42, 'robe_dk')
    # arms / hands
    sw = [0, 1, -1][step]
    _r(d, 2, 20 + sw, 5, 34 + sw, 'robe')
    _r(d, 19, 20 - sw, 22, 34 - sw, 'robe')
    _r(d, 2, 34 + sw, 5, 37 + sw, 'skin')
    _r(d, 19, 34 - sw, 22, 37 - sw, 'skin')
    # neck + head
    _r(d, 10, 15, 14, 18, 'skin_dk')
    _r(d, 7, 4, 17, 16, 'skin')
    _r(d, 7, 2, 17, 6, 'hair')
    _r(d, 6, 4, 8, 9, 'hair')
    _r(d, 16, 4, 18, 9, 'hair')
    _r(d, 9, 9, 10, 11, 'eye')
    _r(d, 14, 9, 15, 11, 'eye')
    if talk:
        _r(d, 10, 13, 14, 15, 'mouth')
    else:
        _r(d, 10, 13, 14, 14, 'mouth')
    if bellhop:
        for y in (20, 23, 26, 33, 36):          # brass buttons
            _r(d, 11, y, 13, y + 1, 'hat_band')
        _r(d, 8, 0, 16, 4, 'hat')                # pillbox hat
        _r(d, 8, 3, 16, 4, 'hat_band')
    return im


def actor_back(step=0, outfit='robe'):
    bellhop = _use(outfit)
    im = _frame(); d = ImageDraw.Draw(im)
    lo = [0, -2, 2][step]
    _r(d, 8, 40, 11, 49 + min(0, lo), 'leg')
    _r(d, 13, 40, 16, 49 - max(0, lo), 'leg')
    _r(d, 7, 49 + min(0, lo), 11, 52 + min(0, lo), 'slipper')
    _r(d, 13, 49 - max(0, lo), 17, 52 - max(0, lo), 'slipper')
    _r(d, 5, 18, 19, 42, 'robe')
    _r(d, 5, 29, 19, 31, 'belt')
    _r(d, 5, 40, 19, 42, 'robe_dk')
    _r(d, 9, 22, 15, 26, 'stripe')     # monogram
    sw = [0, 1, -1][step]
    _r(d, 2, 20 + sw, 5, 35 + sw, 'robe')
    _r(d, 19, 20 - sw, 22, 35 - sw, 'robe')
    _r(d, 10, 15, 14, 18, 'skin_dk')
    _r(d, 7, 3, 17, 16, 'hair')
    _r(d, 6, 6, 7, 10, 'skin')
    _r(d, 17, 6, 18, 10, 'skin')
    if bellhop:
        _r(d, 8, 0, 16, 4, 'hat')
        _r(d, 8, 3, 16, 4, 'hat_band')
    return im


def actor_side(step=0, talk=False, outfit='robe'):
    """Facing east."""
    bellhop = _use(outfit)
    im = _frame(); d = ImageDraw.Draw(im)
    # legs: 4-step cycle
    leg = [(0, 0), (-3, 3), (0, 0), (3, -3)][step]
    _r(d, 10 + leg[0], 40, 13 + leg[0], 49, 'leg')
    _r(d, 9 + leg[0], 49, 15 + leg[0], 52, 'slipper')
    _r(d, 10 + leg[1], 40, 13 + leg[1], 49, 'leg_back')
    _r(d, 9 + leg[1], 49, 15 + leg[1], 52, 'slipper')
    # robe
    _r(d, 7, 18, 17, 42, 'robe')
    _r(d, 15, 19, 17, 30, 'robe_dk')
    _r(d, 7, 29, 17, 31, 'belt')
    _r(d, 7, 40, 17, 42, 'robe_dk')
    # arm swings
    sw = [0, 2, 0, -2][step]
    _r(d, 10 + sw, 21, 14 + sw, 34, 'robe_dk')
    _r(d, 10 + sw, 34, 14 + sw, 37, 'skin')
    # head
    _r(d, 10, 15, 14, 18, 'skin_dk')
    _r(d, 8, 4, 17, 16, 'skin')
    _r(d, 17, 9, 18, 12, 'skin')       # nose
    _r(d, 7, 2, 16, 6, 'hair')
    _r(d, 7, 6, 11, 11, 'hair')
    _r(d, 14, 8, 15, 10, 'eye')
    if talk:
        _r(d, 14, 13, 17, 15, 'mouth')
    else:
        _r(d, 15, 13, 17, 14, 'mouth')
    if bellhop:
        for y in (21, 25, 33):                   # buttons on the front edge
            _r(d, 15, y, 17, y + 1, 'hat_band')
        _r(d, 8, 0, 15, 4, 'hat')
        _r(d, 8, 3, 15, 4, 'hat_band')
    return im


def cursor_image():
    """16x16 crosshair. Index 0 (magenta) is transparent."""
    im = Image.new('RGB', (16, 16), (255, 0, 255))
    d = ImageDraw.Draw(im)
    for (x0, y0, x1, y1) in [(7, 0, 9, 6), (7, 10, 9, 16), (0, 7, 6, 9), (10, 7, 16, 9)]:
        d.rectangle([x0, y0, x1 - 1, y1 - 1], fill=(8, 8, 12))
    for (x0, y0, x1, y1) in [(8, 1, 8, 5), (8, 11, 8, 15), (1, 8, 5, 8), (11, 8, 15, 8)]:
        d.line([(x0, y0), (x1, y1)], fill=(255, 255, 255))
    return im


# --------------------------------------------------------------------------- bathroom
BATH_DEFAULT = dict(curtain=0, cabinet=0, flush=0, towel=0, soap=0)
BATH_FLOOR_Y = 96


def draw_bath_walls(img, d):
    # tiles with grout, a teal band at dado height, plain upper wall
    rect(d, 0, 0, W, BATH_FLOOR_Y, 'tile')
    for y in range(0, BATH_FLOOR_Y, 8):
        rect(d, 0, y, W, y + 1, 'grout')
        off = 0 if (y // 8) % 2 else 4
        for x in range(off, W, 8):
            rect(d, x, y, x + 1, y + 8, 'grout')
            put(img, x + 2, y + 2, 'tile_hi')
    rect(d, 0, 46, W, 50, 'tile_band')
    rect(d, 0, 0, W, 4, 'crown')
    rect(d, 0, 4, W, 5, 'crown_dk')
    rect(d, 0, BATH_FLOOR_Y - 3, W, BATH_FLOOR_Y, 'porcelain_dk')


def draw_bath_floor(img, d):
    # soft two-tone tiles whose columns converge on the centre of the room
    y = BATH_FLOOR_Y
    row = 0
    while y < H:
        h = 5 + row
        size = 14 + row * 3
        for i in range(-12, 13):
            x = W // 2 + i * size - size // 2
            c = 'floor_a' if (i + row) % 2 else 'floor_b'
            rect(d, max(0, x), y, min(W, x + size), min(H, y + h), c)
            rect(d, max(0, x), y, min(W, x + size), y + 1, 'porcelain_dk')
        y += h
        row += 1
    rect(d, 0, BATH_FLOOR_Y, W, BATH_FLOOR_Y + 1, 'porcelain_sh')


def draw_tub(img, d, curtain_open):
    # tub body against the back wall, x 16..112
    rect(d, 18, 74, 110, 78, 'porcelain')        # rim
    rect(d, 18, 74, 110, 75, 'white')
    rect(d, 20, 78, 108, 104, 'porcelain')       # front panel
    rect(d, 20, 98, 108, 104, 'porcelain_dk')
    rect(d, 20, 78, 22, 104, 'porcelain_dk')
    for fx in (24, 98):                          # claw feet
        rect(d, fx, 104, fx + 6, 109, 'brass')
        rect(d, fx + 1, 108, fx + 5, 110, 'brass_dk')
    # chrome tap and shower head on the wall behind
    rect(d, 92, 60, 104, 63, 'chrome')
    rect(d, 96, 63, 99, 72, 'chrome_dk')
    rect(d, 88, 14, 92, 40, 'chrome_dk')
    rect(d, 82, 14, 96, 18, 'chrome')
    # curtain rod
    rect(d, 16, 9, 112, 11, 'chrome')
    rect(d, 16, 8, 18, 12, 'chrome_dk')
    rect(d, 110, 8, 112, 12, 'chrome_dk')
    if curtain_open:
        # tub interior visible above the rim, with a rubber duck
        rect(d, 22, 70, 106, 74, 'water')
        rect(d, 22, 70, 106, 71, 'water_hi')
        rect(d, 60, 64, 68, 71, 'duck')
        rect(d, 65, 60, 70, 65, 'duck')
        rect(d, 70, 62, 73, 64, 'duck_beak')
        put(img, 67, 61, 'black')
        # curtain bunched at the left end
        for x in range(18, 34, 3):
            rect(d, x, 11, x + 2, 76, 'shower')
            rect(d, x + 2, 11, x + 3, 76, 'shower_dk')
        rect(d, 18, 11, 34, 13, 'shower_hi')
    else:
        for x in range(18, 110, 6):
            rect(d, x, 11, x + 4, 80, 'shower')
            rect(d, x + 4, 11, x + 6, 80, 'shower_dk')
            rect(d, x + 1, 11, x + 2, 80, 'shower_hi')
        for x in range(20, 110, 6):              # rings
            put(img, x, 11, 'chrome_dk')


def draw_mat(img, d):
    rect(d, 34, 113, 94, 120, 'mat')
    rect(d, 34, 113, 94, 114, 'mat_hi')
    rect(d, 34, 119, 94, 120, 'mat_dk')
    for x in range(36, 94, 4):
        put(img, x, 120, 'mat_hi')              # fringe


def draw_toilet(img, d, flush):
    # tank on the wall
    rect(d, 132, 52, 164, 74, 'porcelain')
    rect(d, 132, 52, 164, 55, 'white')
    rect(d, 132, 70, 164, 74, 'porcelain_dk')
    # flush handle: up, or pushed down while flushing
    if flush:
        rect(d, 134, 59, 140, 61, 'chrome')
        rect(d, 138, 61, 140, 64, 'chrome_dk')
    else:
        rect(d, 134, 57, 140, 59, 'chrome')
    # seat ring, lid up against the tank, water in the bowl
    rect(d, 136, 74, 160, 78, 'porcelain_dk')    # raised lid edge
    d.ellipse([132, 76, 164, 90], fill=C['porcelain'])
    d.ellipse([136, 78, 160, 88], fill=C['water'])
    if flush == 1:
        d.arc([139, 79, 157, 87], 20, 200, fill=C['water_hi'])
        d.arc([143, 80, 153, 86], 200, 20, fill=C['water_dk'])
    elif flush == 2:
        d.arc([139, 79, 157, 87], 200, 20, fill=C['water_hi'])
        d.arc([143, 80, 153, 86], 20, 200, fill=C['water_dk'])
        rect(d, 146, 82, 150, 84, 'water_dk')
    else:
        rect(d, 142, 80, 152, 81, 'water_hi')
    # bowl front and pedestal
    rect(d, 138, 88, 158, 100, 'porcelain')
    rect(d, 138, 96, 158, 100, 'porcelain_dk')
    rect(d, 136, 100, 160, 104, 'porcelain_sh')


def draw_sink(img, d, soap):
    rect(d, 198, 92, 218, 100, 'porcelain_sh')   # pedestal foot
    rect(d, 202, 76, 214, 94, 'porcelain')
    rect(d, 202, 76, 204, 94, 'porcelain_dk')
    rect(d, 186, 64, 230, 74, 'porcelain')       # basin
    rect(d, 186, 64, 230, 65, 'white')
    rect(d, 190, 72, 226, 76, 'porcelain_dk')
    rect(d, 194, 65, 222, 68, 'porcelain_sh')    # bowl opening
    rect(d, 206, 57, 210, 65, 'chrome')          # faucet
    rect(d, 204, 57, 214, 59, 'chrome')
    rect(d, 213, 59, 214, 61, 'chrome_dk')
    rect(d, 198, 61, 202, 64, 'chrome_dk')       # taps
    rect(d, 214, 61, 218, 64, 'chrome_dk')
    if soap:
        rect(d, 188, 60, 196, 64, 'soap')
        rect(d, 189, 60, 195, 61, 'soap_hi')


def draw_mirror(img, d, open_):
    # medicine cabinet above the sink, x 192..224, y 16..56
    rect(d, 194, 18, 222, 54, 'chrome_dk')
    if not open_:
        rect(d, 196, 20, 220, 52, 'glass')
        for i in range(6):                       # reflection streaks
            put(img, 200 + i, 24 + i, 'glass_hi')
            put(img, 206 + i, 24 + i, 'glass_hi')
        rect(d, 196, 46, 220, 52, 'glass_dk')
        rect(d, 216, 34, 218, 40, 'chrome')      # finger pull
    else:
        rect(d, 198, 20, 220, 52, 'safe_in')     # cabinet inside
        for y in (30, 42):
            rect(d, 198, y, 220, y + 2, 'porcelain_dk')   # shelves
        rect(d, 201, 22, 204, 30, 'bottle_b')
        rect(d, 206, 24, 209, 30, 'bottle_w')
        rect(d, 211, 23, 214, 30, 'bottle2')
        rect(d, 203, 36, 212, 42, 'shower_hi')   # shower cap
        rect(d, 214, 37, 218, 42, 'red')          # sewing kit
        rect(d, 200, 47, 216, 50, 'bottle_w')    # toothbrush
        rect(d, 192, 18, 198, 54, 'glass')       # door swung open, edge-on
        rect(d, 192, 18, 193, 54, 'chrome_dk')


def draw_towel(img, d, towel):
    rect(d, 250, 36, 286, 38, 'chrome')          # towel bar
    rect(d, 248, 34, 251, 40, 'chrome_dk')
    rect(d, 285, 34, 288, 40, 'chrome_dk')
    if towel:
        rect(d, 254, 36, 282, 70, 'towel')
        rect(d, 254, 36, 282, 40, 'towel_dk')
        rect(d, 254, 58, 282, 62, 'towel_band')
        rect(d, 254, 66, 282, 70, 'towel_dk')
        rect(d, 280, 40, 282, 70, 'towel_dk')


def render_bathroom(state=None):
    s = dict(BATH_DEFAULT)
    if state:
        s.update(state)
    img = Image.new('RGB', (W, H))
    d = ImageDraw.Draw(img)
    draw_bath_walls(img, d)
    draw_bath_floor(img, d)
    draw_side_doorway(img, d, right=True, inside='bedroom')
    draw_tub(img, d, s['curtain'])
    draw_mat(img, d)
    draw_toilet(img, d, s['flush'])
    draw_sink(img, d, s['soap'])
    draw_mirror(img, d, s['cabinet'])
    draw_towel(img, d, s['towel'])
    return img
