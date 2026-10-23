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
DEFAULT = dict(tv=0, curtains=0, minibar=0, drawer=0, lamp=0, safe=0, door=0, uniform=0,
               table_matchbook=0, table_candy=0, table_keycard=0, table_uniform=0)

# Coffee table on the floor, x 120..192, top surface y 105..116. Items set down on it sit in four
# 16-pixel slots across the top (x 128, 144, 160, 176; y 104..120).
TABLE_X0, TABLE_X1 = 120, 192


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


def draw_dresser_tv(img, d, tv):
    # dresser
    rect(d, 72, 64, 130, FLOOR_Y, 'wood_dk')
    rect(d, 72, 64, 130, 67, 'wood_hi')
    for y in (69, 78, 87):
        rect(d, 75, y, 127, y + 7, 'wood')
        rect(d, 75, y, 127, y + 1, 'wood_hi')
        rect(d, 98, y + 3, 104, y + 4, 'brass')
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


def draw_bed(img, d, s_uniform=0):
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
    if s_uniform:
        # bellhop uniform folded on the blanket, pillbox hat beside it
        rect(d, 266, 98, 286, 110, 'red_dk')
        rect(d, 266, 98, 286, 108, 'red')
        rect(d, 275, 98, 277, 110, 'red_dk')
        for y in (100, 103, 106):
            put(img, 276, y, 'brass')
        rect(d, 266, 98, 270, 101, 'brass')      # epaulette
        rect(d, 282, 98, 286, 101, 'brass')
        rect(d, 287, 102, 295, 109, 'red')
        rect(d, 287, 106, 295, 107, 'brass')
        rect(d, 287, 108, 295, 109, 'red_dk')
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
    for x, y in ((x0 + 10, 108), (x0 + 30, 111), (x0 + 48, 108), (x0 + 22, 114), (x0 + 56, 113)):
        rect(d, x, y, x + 7, y + 1, 'wood_hi')               # grain
    rect(d, x0, 116, x1, 120, 'wood_dk')                     # front edge
    rect(d, x0, 116, x1, 117, 'wood_hi')
    # things set down on it, one per slot
    if s['table_matchbook']:
        rect(d, 131, 110, 141, 114, 'match')
        rect(d, 132, 111, 136, 112, 'match_hi')
    if s['table_candy']:
        rect(d, 146, 110, 158, 114, 'candy')
        rect(d, 150, 110, 155, 114, 'candy2')
    if s['table_keycard']:
        rect(d, 162, 110, 174, 115, 'card')
        rect(d, 162, 112, 174, 113, 'card_dk')
        rect(d, 164, 113, 167, 114, 'white')
    if s['table_uniform']:
        rect(d, 177, 107, 190, 115, 'red')
        rect(d, 177, 113, 190, 115, 'red_dk')
        rect(d, 183, 107, 184, 115, 'red_dk')
        put(img, 183, 109, 'brass'); put(img, 183, 112, 'brass')
        rect(d, 177, 107, 180, 109, 'brass')
        rect(d, 187, 107, 190, 109, 'brass')


def render(state=None):
    s = dict(DEFAULT)
    if state:
        s.update(state)
    img = Image.new('RGB', (W, H))
    d = ImageDraw.Draw(img)
    draw_wall(img, d)
    draw_floor(img, d)
    draw_door(img, d, s['door'])
    draw_dresser_tv(img, d, s['tv'])
    draw_window(img, d, s['curtains'])
    draw_minibar(img, d, s['minibar'])
    draw_nightstand(img, d, s['drawer'])
    draw_lamp(img, d, s['lamp'])
    draw_phone(img, d)
    draw_bed(img, d, s['uniform'])
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
