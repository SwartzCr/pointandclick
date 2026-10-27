"""The guest (same person as in Room 714, still in the bellhop uniform) and
Khuc, the keeper of the archway. Frames are 48x104 with the feet on the
bottom row; everything is drawn with a few flat tones and then outlined.

Directions follow AGS loop order: 0 down (front), 1 left, 2 right, 3 up
(back). Left is the right-facing art mirrored.
"""
import math
from PIL import Image, ImageDraw
from art_common import canvas, outline, limb, rgba, shade, mix

FW, FH = 48, 104
CX = 24

GUEST = {
    'skin': (232, 176, 136), 'skin_dk': (196, 136, 100), 'hair': (78, 46, 30),
    'hair_hi': (118, 74, 46), 'eye': (24, 20, 28), 'white': (250, 246, 240),
    'mouth': (130, 44, 44), 'tongue': (210, 90, 90),
    'coat': (176, 30, 40), 'coat_dk': (126, 18, 30), 'coat_hi': (208, 60, 66),
    'gold': (232, 190, 74), 'gold_dk': (170, 124, 40),
    'leg': (44, 44, 70), 'leg_dk': (30, 30, 50), 'shoe': (22, 20, 26), 'shoe_hi': (70, 66, 80),
    'hat': (176, 30, 40), 'hat_dk': (126, 18, 30),
    'beads': (250, 222, 150), 'beads_dk': (204, 160, 84), 'string': (120, 90, 60),
    'uv': (190, 120, 255), 'uv_hi': (240, 220, 255),
}

KHUC = {
    'skin': (214, 160, 112), 'skin_dk': (176, 122, 82), 'hair': (30, 26, 30),
    'hair_hi': (60, 54, 60), 'eye': (24, 20, 28), 'white': (250, 246, 240),
    'mouth': (120, 50, 46), 'tongue': (200, 90, 90),
    'robe': (238, 222, 176), 'robe_dk': (196, 176, 128), 'robe_hi': (252, 242, 212),
    'stole': (196, 40, 36), 'stole_dk': (140, 24, 24), 'gold': (232, 190, 74),
    'colander': (200, 206, 214), 'colander_dk': (130, 138, 150), 'colander_hi': (244, 246, 250),
    'sandal': (120, 76, 40), 'leg': (214, 160, 112), 'leg_dk': (176, 122, 82),
    'meatball': (130, 64, 40),
}


def _P(c):
    return rgba(c)


# ---------------------------------------------------------------- skeleton
def _walk_pose(phase, side):
    """Return leg and arm offsets for a walk phase in [0,1).
    For side view: legs swing forward/back; for front/back: legs lift."""
    s = math.sin(phase * 2 * math.pi)
    c = math.cos(phase * 2 * math.pi)
    return s, c


def _head_front(d, P, cx, top, talk=False, blink=False, hat=True):
    # ears
    d.ellipse([cx - 11, top + 9, cx - 6, top + 16], fill=P['skin_dk'])
    d.ellipse([cx + 6, top + 9, cx + 11, top + 16], fill=P['skin_dk'])
    # face
    d.ellipse([cx - 9, top + 1, cx + 9, top + 22], fill=P['skin'])
    d.rectangle([cx - 8, top + 15, cx + 8, top + 17], fill=P['skin'])
    # hair
    d.chord([cx - 10, top - 1, cx + 10, top + 14], 180, 360, fill=P['hair'])
    d.polygon([(cx - 10, top + 6), (cx - 7, top + 6), (cx - 8, top + 12), (cx - 10, top + 11)], fill=P['hair'])
    d.polygon([(cx + 10, top + 6), (cx + 7, top + 6), (cx + 8, top + 12), (cx + 10, top + 11)], fill=P['hair'])
    d.polygon([(cx - 6, top + 5), (cx + 2, top + 5), (cx - 3, top + 9)], fill=P['hair'])   # fringe
    d.line([(cx - 4, top + 2), (cx + 3, top + 2)], fill=P['hair_hi'])
    # eyes
    if blink:
        d.line([(cx - 6, top + 12), (cx - 3, top + 12)], fill=P['eye'])
        d.line([(cx + 3, top + 12), (cx + 6, top + 12)], fill=P['eye'])
    else:
        d.rectangle([cx - 6, top + 10, cx - 3, top + 13], fill=P['white'])
        d.rectangle([cx + 3, top + 10, cx + 6, top + 13], fill=P['white'])
        d.rectangle([cx - 5, top + 11, cx - 4, top + 13], fill=P['eye'])
        d.rectangle([cx + 4, top + 11, cx + 5, top + 13], fill=P['eye'])
        d.line([(cx - 6, top + 9), (cx - 3, top + 9)], fill=P['hair'])
        d.line([(cx + 3, top + 9), (cx + 6, top + 9)], fill=P['hair'])
    # nose
    d.line([(cx, top + 13), (cx + 1, top + 16)], fill=P['skin_dk'])
    # mouth
    if talk:
        d.ellipse([cx - 3, top + 17, cx + 3, top + 21], fill=P['mouth'])
        d.rectangle([cx - 1, top + 20, cx + 1, top + 20], fill=P['tongue'])
    else:
        d.line([(cx - 3, top + 18), (cx + 3, top + 18)], fill=P['mouth'])
        d.point((cx + 4, top + 17), fill=P['mouth'])


def _head_side(d, P, cx, top, talk=False):
    """Facing east."""
    d.ellipse([cx - 9, top + 1, cx + 8, top + 22], fill=P['skin'])
    d.polygon([(cx + 7, top + 11), (cx + 11, top + 15), (cx + 7, top + 16)], fill=P['skin'])   # nose
    d.ellipse([cx - 4, top + 9, cx, top + 15], fill=P['skin_dk'])                            # ear
    d.chord([cx - 10, top - 1, cx + 9, top + 14], 180, 360, fill=P['hair'])
    d.polygon([(cx - 10, top + 6), (cx - 1, top + 6), (cx - 4, top + 9), (cx - 9, top + 16), (cx - 10, top + 14)],
              fill=P['hair'])
    d.polygon([(cx + 1, top + 5), (cx + 9, top + 5), (cx + 8, top + 8)], fill=P['hair'])
    d.line([(cx - 5, top + 2), (cx + 3, top + 2)], fill=P['hair_hi'])
    d.rectangle([cx + 3, top + 10, cx + 5, top + 13], fill=P['white'])
    d.rectangle([cx + 4, top + 11, cx + 5, top + 13], fill=P['eye'])
    d.line([(cx + 2, top + 9), (cx + 6, top + 9)], fill=P['hair'])
    if talk:
        d.polygon([(cx + 4, top + 17), (cx + 8, top + 17), (cx + 7, top + 20), (cx + 4, top + 19)], fill=P['mouth'])
    else:
        d.line([(cx + 4, top + 18), (cx + 7, top + 18)], fill=P['mouth'])


def _head_back(d, P, cx, top):
    d.ellipse([cx - 11, top + 9, cx - 6, top + 16], fill=P['skin_dk'])
    d.ellipse([cx + 6, top + 9, cx + 11, top + 16], fill=P['skin_dk'])
    d.ellipse([cx - 9, top + 1, cx + 9, top + 22], fill=P['skin'])
    d.ellipse([cx - 10, top - 1, cx + 10, top + 20], fill=P['hair'])
    d.line([(cx - 5, top + 3), (cx + 4, top + 3)], fill=P['hair_hi'])
    d.line([(cx - 2, top + 8), (cx + 2, top + 14)], fill=P['hair_hi'])


def _pillbox(d, P, cx, top, side=False):
    w = 6 if side else 7
    x = cx - w - (1 if side else 0)
    d.rectangle([x, top - 5, x + 2 * w, top + 1], fill=P['hat'])
    d.rectangle([x, top - 1, x + 2 * w, top + 1], fill=P['gold'])
    d.line([(x + 1, top - 4), (x + 2 * w - 2, top - 4)], fill=shade(P['hat'], 1.25))


def _neckwear(d, P, cx, y, kind, view):
    """Beads (macaroni on a string) and/or the UV pendant."""
    if kind.get('beads'):
        if view == 'back':
            d.arc([cx - 8, y - 3, cx + 8, y + 5], 200, 340, fill=P['string'])
        elif view == 'side':
            for i in range(4):
                d.ellipse([cx + 1 + i, y + 2 + i * 3, cx + 4 + i, y + 4 + i * 3], fill=P['beads'])
            d.ellipse([cx + 3, y + 13, cx + 7, y + 17], fill=P['beads_dk'])
        else:
            pts = []
            for i in range(9):
                t = i / 8
                px = cx - 8 + 16 * t
                py = y + 1 + 9 * math.sin(math.pi * t)
                pts.append((px, py))
            for px, py in pts:
                d.ellipse([px - 1.5, py - 1.5, px + 1.5, py + 1.5], fill=P['beads'])
                d.point((px, py + 1), fill=P['beads_dk'])
            d.ellipse([cx - 3, y + 10, cx + 3, y + 16], fill=P['beads'])   # big macaroni medal
            d.arc([cx - 2, y + 11, cx + 2, y + 15], 0, 360, fill=P['beads_dk'])
    if kind.get('uv'):
        if view == 'back':
            return
        px = cx + (5 if view == 'side' else 0)
        py = y + (14 if kind.get('beads') else 9)
        if view != 'side':
            d.line([(cx - 6, y), (px, py - 3)], fill=(90, 70, 120))
            d.line([(cx + 6, y), (px, py - 3)], fill=(90, 70, 120))
        d.polygon([(px, py - 3), (px + 3, py + 1), (px, py + 6), (px - 3, py + 1)], fill=P['uv'])
        d.point((px - 1, py), fill=P['uv_hi'])


def _guest_body_front(d, P, phase, walking, back=False, kind=None):
    s = math.sin(phase * 2 * math.pi) if walking else 0
    # legs
    lift_l = max(0, s) * 4
    lift_r = max(0, -s) * 4
    for x, lift, col in ((CX - 6, lift_l, P['leg']), (CX + 6, lift_r, P['leg'])):
        limb(d, (x, 62), (x, 97 - lift), 9, col)
        d.rectangle([x - 5, 97 - lift, x + 5, 102 - lift], fill=P['shoe'])
        d.line([(x - 4, 98 - lift), (x + 2, 98 - lift)], fill=P['shoe_hi'])
    d.rectangle([CX - 10, 58, CX + 10, 66], fill=P['leg'])
    # arms
    swing = s * 3
    for sgn in (-1, 1):
        sh = (CX + sgn * 12, 33)
        el = (CX + sgn * 14, 47 + sgn * swing * 0.5)
        ha = (CX + sgn * 14, 59 + sgn * swing)
        limb(d, sh, el, 8, P['coat_dk'] if sgn > 0 else P['coat'])
        limb(d, el, ha, 7, P['coat_dk'] if sgn > 0 else P['coat'])
        d.rectangle([ha[0] - 3, ha[1] - 1, ha[0] + 3, ha[1] + 1], fill=P['gold'])     # cuff
        d.ellipse([ha[0] - 3, ha[1] + 1, ha[0] + 3, ha[1] + 7], fill=P['skin'])
    # torso: short bellhop jacket
    d.rounded_rectangle([CX - 12, 28, CX + 12, 62], 5, fill=P['coat'])
    d.rectangle([CX + 6, 32, CX + 12, 60], fill=P['coat_dk'])
    d.rectangle([CX - 12, 32, CX - 9, 58], fill=P['coat_hi'])
    if back:
        d.line([(CX, 40), (CX, 62)], fill=P['coat_dk'])
        d.rectangle([CX - 12, 56, CX + 12, 59], fill=P['coat_dk'])
    else:
        for y in (35, 41, 47, 53):
            d.rectangle([CX - 6, y, CX - 5, y + 1], fill=P['gold'])
            d.rectangle([CX + 5, y, CX + 6, y + 1], fill=P['gold'])
        d.polygon([(CX - 4, 28), (CX + 4, 28), (CX, 33)], fill=P['skin_dk'])   # collar v
        d.rectangle([CX - 12, 58, CX + 12, 60], fill=P['gold'])                # hem trim
    # epaulettes
    d.rectangle([CX - 15, 29, CX - 9, 32], fill=P['gold'])
    d.rectangle([CX + 9, 29, CX + 15, 32], fill=P['gold'])
    # neck
    d.rectangle([CX - 3, 23, CX + 3, 29], fill=P['skin_dk'])
    d.rectangle([CX - 6, 26, CX + 6, 29], fill=P['coat'])                     # high collar
    d.line([(CX - 6, 26), (CX + 6, 26)], fill=P['gold'])
    if kind:
        _neckwear(d, P, CX, 30, kind, 'back' if back else 'front')


def _guest_body_side(d, P, phase, walking, kind=None):
    """Facing east. phase in [0,1)."""
    s = math.sin(phase * 2 * math.pi) if walking else 0
    c = math.cos(phase * 2 * math.pi) if walking else 1
    hip = (CX, 62)

    def leg(sw, col, shoe):
        knee = (CX + sw * 7, 80 - abs(sw) * 1)
        lift = max(0, math.sin(phase * 2 * math.pi + (0 if col == P['leg'] else math.pi))) * 3 if walking else 0
        foot = (CX + sw * 11, 97 - lift)
        limb(d, hip, knee, 9, col)
        limb(d, knee, foot, 8, col)
        d.polygon([(foot[0] - 4, foot[1] + 1), (foot[0] + 7, foot[1] + 1), (foot[0] + 7, foot[1] + 5),
                   (foot[0] - 4, foot[1] + 5)], fill=shoe)
        d.line([(foot[0] - 2, foot[1] + 2), (foot[0] + 4, foot[1] + 2)], fill=P['shoe_hi'])

    leg(-s, P['leg_dk'], P['shoe'])            # back leg
    # back arm
    sh = (CX, 33)
    limb(d, sh, (CX - s * 6, 47), 7, P['coat_dk'])
    limb(d, (CX - s * 6, 47), (CX - s * 9, 58), 6, P['coat_dk'])
    d.ellipse([CX - s * 9 - 3, 58, CX - s * 9 + 3, 64], fill=P['skin_dk'])
    # torso
    d.rounded_rectangle([CX - 8, 28, CX + 9, 62], 5, fill=P['coat'])
    d.rectangle([CX - 8, 32, CX - 5, 60], fill=P['coat_dk'])
    for y in (36, 43, 50):
        d.rectangle([CX + 7, y, CX + 8, y + 1], fill=P['gold'])
    d.rectangle([CX - 8, 58, CX + 9, 60], fill=P['gold'])
    leg(s, P['leg'], P['shoe'])                # front leg
    # front arm
    el = (CX + s * 6, 47)
    ha = (CX + s * 9, 58)
    limb(d, sh, el, 8, P['coat'])
    limb(d, el, ha, 7, P['coat'])
    d.rectangle([ha[0] - 3, ha[1] - 1, ha[0] + 3, ha[1] + 1], fill=P['gold'])
    d.ellipse([ha[0] - 3, ha[1] + 1, ha[0] + 3, ha[1] + 7], fill=P['skin'])
    d.rectangle([CX - 4, 29, CX + 3, 32], fill=P['gold'])                      # epaulette
    d.rectangle([CX - 2, 23, CX + 3, 29], fill=P['skin_dk'])
    d.rectangle([CX - 4, 26, CX + 6, 29], fill=P['coat'])
    d.line([(CX - 4, 26), (CX + 6, 26)], fill=P['gold'])
    if kind:
        _neckwear(d, P, CX, 30, kind, 'side')


def guest_frame(direction, phase=0.0, walking=False, talk=False, kind=None, blink=False):
    """direction: 'front', 'side' (east), 'back'."""
    P = {k: _P(v) for k, v in GUEST.items()}
    im = canvas(FW, FH)
    d = ImageDraw.Draw(im)
    bob = (abs(math.sin(phase * 2 * math.pi)) * 1.5) if walking else 0
    body = canvas(FW, FH)
    bd = ImageDraw.Draw(body)
    if direction == 'side':
        _guest_body_side(bd, P, phase, walking, kind)
    else:
        _guest_body_front(bd, P, phase, walking, back=(direction == 'back'), kind=kind)
    head = canvas(FW, FH)
    hd = ImageDraw.Draw(head)
    top = 5
    if direction == 'front':
        _head_front(hd, P, CX, top, talk=talk, blink=blink)
        _pillbox(hd, P, CX + 2, top + 1)
    elif direction == 'side':
        _head_side(hd, P, CX, top, talk=talk)
        _pillbox(hd, P, CX, top + 1, side=True)
    else:
        _head_back(hd, P, CX, top)
        _pillbox(hd, P, CX - 2, top + 1)
    im.alpha_composite(body, (0, int(-bob)))
    im.alpha_composite(head, (0, int(-bob)))
    return outline(im)


def guest_seated():
    """Sitting on the pope seat, facing the viewer: drawn into the seat object."""
    P = {k: _P(v) for k, v in GUEST.items()}
    im = canvas(FW, 80)
    d = ImageDraw.Draw(im)
    # thighs towards viewer, shins down
    for x in (CX - 7, CX + 7):
        d.rectangle([x - 5, 50, x + 5, 62], fill=P['leg'])
        limb(d, (x, 62), (x, 74), 9, P['leg_dk'])
        d.rectangle([x - 5, 74, x + 5, 79], fill=P['shoe'])
    d.rounded_rectangle([CX - 12, 24, CX + 12, 56], 5, fill=P['coat'])
    d.rectangle([CX + 6, 28, CX + 12, 54], fill=P['coat_dk'])
    for y in (31, 37, 43, 49):
        d.rectangle([CX - 6, y, CX - 5, y + 1], fill=P['gold'])
        d.rectangle([CX + 5, y, CX + 6, y + 1], fill=P['gold'])
    for sgn in (-1, 1):
        limb(d, (CX + sgn * 12, 29), (CX + sgn * 15, 44), 8, P['coat'])
        limb(d, (CX + sgn * 15, 44), (CX + sgn * 12, 54), 7, P['coat'])
        d.ellipse([CX + sgn * 12 - 3, 52, CX + sgn * 12 + 3, 58], fill=P['skin'])
    d.rectangle([CX - 15, 25, CX - 9, 28], fill=P['gold'])
    d.rectangle([CX + 9, 25, CX + 15, 28], fill=P['gold'])
    d.rectangle([CX - 3, 19, CX + 3, 25], fill=P['skin_dk'])
    d.rectangle([CX - 6, 22, CX + 6, 25], fill=P['coat'])
    _head_front(d, P, CX, 1, talk=False)
    return outline(im)


# ---------------------------------------------------------------- Khuc
def _colander(d, P, cx, top, view):
    """A colander worn as a hat."""
    if view == 'side':
        d.chord([cx - 11, top - 6, cx + 11, top + 12], 180, 360, fill=P['colander'])
        d.rectangle([cx - 12, top + 2, cx + 12, top + 4], fill=P['colander_dk'])
        d.rectangle([cx + 10, top + 1, cx + 16, top + 3], fill=P['colander_dk'])   # handle
        for i, x in enumerate(range(cx - 7, cx + 8, 4)):
            d.point((x, top - 2 + (i % 2)), fill=P['colander_dk'])
        d.line([(cx - 6, top - 4), (cx + 2, top - 4)], fill=P['colander_hi'])
    else:
        d.chord([cx - 12, top - 6, cx + 12, top + 12], 180, 360, fill=P['colander'])
        d.rectangle([cx - 13, top + 2, cx + 13, top + 4], fill=P['colander_dk'])
        d.rectangle([cx - 17, top + 1, cx - 12, top + 3], fill=P['colander_dk'])
        d.rectangle([cx + 12, top + 1, cx + 17, top + 3], fill=P['colander_dk'])
        for row, y in enumerate((top - 3, top)):
            for x in range(cx - 8 + row * 2, cx + 9, 4):
                d.point((x, y), fill=P['colander_dk'])
        d.line([(cx - 7, top - 5), (cx - 1, top - 5)], fill=P['colander_hi'])


def _khuc_head(d, P, cx, top, view, talk=False):
    if view == 'side':
        d.ellipse([cx - 9, top + 1, cx + 8, top + 22], fill=P['skin'])
        d.polygon([(cx + 7, top + 11), (cx + 10, top + 14), (cx + 7, top + 15)], fill=P['skin'])
        d.ellipse([cx - 4, top + 9, cx, top + 15], fill=P['skin_dk'])
        d.polygon([(cx - 9, top + 4), (cx + 6, top + 4), (cx - 8, top + 14)], fill=P['hair'])
        d.rectangle([cx + 3, top + 11, cx + 5, top + 12], fill=P['eye'])
        d.line([(cx + 2, top + 9), (cx + 6, top + 9)], fill=P['hair'])
        # small beard
        d.polygon([(cx - 1, top + 18), (cx + 7, top + 18), (cx + 4, top + 25), (cx, top + 23)], fill=P['hair'])
        if talk:
            d.line([(cx + 4, top + 18), (cx + 7, top + 19)], fill=P['mouth'])
        _colander(d, P, cx, top + 3, 'side')
    elif view == 'back':
        d.ellipse([cx - 9, top + 1, cx + 9, top + 22], fill=P['skin'])
        d.ellipse([cx - 10, top + 2, cx + 10, top + 19], fill=P['hair'])
        _colander(d, P, cx, top + 3, 'front')
    else:
        d.ellipse([cx - 11, top + 9, cx - 6, top + 16], fill=P['skin_dk'])
        d.ellipse([cx + 6, top + 9, cx + 11, top + 16], fill=P['skin_dk'])
        d.ellipse([cx - 9, top + 1, cx + 9, top + 22], fill=P['skin'])
        d.rectangle([cx - 9, top + 4, cx + 9, top + 7], fill=P['hair'])
        # eyes (serene, half-closed)
        d.line([(cx - 6, top + 11), (cx - 3, top + 11)], fill=P['eye'])
        d.line([(cx + 3, top + 11), (cx + 6, top + 11)], fill=P['eye'])
        d.line([(cx - 6, top + 12), (cx - 3, top + 12)], fill=P['eye'])
        d.line([(cx + 3, top + 12), (cx + 6, top + 12)], fill=P['eye'])
        d.line([(cx, top + 13), (cx + 1, top + 15)], fill=P['skin_dk'])
        # moustache + goatee
        d.line([(cx - 4, top + 17), (cx + 4, top + 17)], fill=P['hair'])
        d.polygon([(cx - 3, top + 20), (cx + 3, top + 20), (cx, top + 26)], fill=P['hair'])
        if talk:
            d.rectangle([cx - 2, top + 18, cx + 2, top + 20], fill=P['mouth'])
        _colander(d, P, cx, top + 3, 'front')


def khuc_frame(direction, phase=0.0, walking=False, talk=False, pose=None):
    P = {k: _P(v) for k, v in KHUC.items()}
    im = canvas(FW, FH)
    d = ImageDraw.Draw(im)
    s = math.sin(phase * 2 * math.pi) if walking else 0
    top = 5
    if direction == 'side':
        # sandals peeking out
        for sw, col in ((-s, P['leg_dk']), (s, P['leg'])):
            fx = CX + sw * 8
            d.rectangle([fx - 3, 92, fx + 2, 98], fill=col)
            d.rectangle([fx - 4, 98, fx + 6, 101], fill=P['sandal'])
        d.polygon([(CX - 9, 28), (CX + 9, 28), (CX + 13 + s * 2, 96), (CX - 13 + s * 2, 96)], fill=P['robe'])
        d.polygon([(CX - 9, 28), (CX - 4, 28), (CX - 8 + s * 2, 96), (CX - 13 + s * 2, 96)], fill=P['robe_dk'])
        d.polygon([(CX + 2, 29), (CX + 7, 29), (CX + 9, 70), (CX + 4, 70)], fill=P['stole'])   # stole end
        d.rectangle([CX - 10, 56, CX + 10, 59], fill=P['stole_dk'])                           # rope belt
        limb(d, (CX, 33), (CX + 4 + s * 4, 48), 9, P['robe_hi'])
        limb(d, (CX + 4 + s * 4, 48), (CX + 8 + s * 5, 58), 8, P['robe_hi'])
        d.ellipse([CX + 5 + s * 5, 57, CX + 11 + s * 5, 63], fill=P['skin'])
        _khuc_head(d, P, CX, top, 'side', talk)
    else:
        back = direction == 'back'
        for x, lift in ((CX - 6, max(0, s) * 3), (CX + 6, max(0, -s) * 3)):
            d.rectangle([x - 3, 92 - lift, x + 3, 98 - lift], fill=P['leg'])
            d.rectangle([x - 5, 98 - lift, x + 5, 101 - lift], fill=P['sandal'])
        d.polygon([(CX - 11, 28), (CX + 11, 28), (CX + 16, 96), (CX - 16, 96)], fill=P['robe'])
        d.polygon([(CX + 5, 28), (CX + 11, 28), (CX + 16, 96), (CX + 8, 96)], fill=P['robe_dk'])
        if not back:
            d.polygon([(CX - 7, 28), (CX - 3, 28), (CX - 4, 76), (CX - 8, 76)], fill=P['stole'])
            d.polygon([(CX + 3, 28), (CX + 7, 28), (CX + 8, 76), (CX + 4, 76)], fill=P['stole'])
            for y in (40, 52, 64):                   # little golden forks on the stole
                d.line([(CX - 6, y), (CX - 6, y + 5)], fill=P['gold'])
                d.line([(CX + 6, y), (CX + 6, y + 5)], fill=P['gold'])
                d.line([(CX - 7, y), (CX - 5, y)], fill=P['gold'])
                d.line([(CX + 5, y), (CX + 7, y)], fill=P['gold'])
        d.rectangle([CX - 12, 56, CX + 12, 59], fill=P['stole_dk'])
        if pose == 'hands':                          # hands folded in sleeves
            d.rounded_rectangle([CX - 12, 40, CX + 12, 52], 4, fill=P['robe_hi'])
            d.line([(CX, 41), (CX, 51)], fill=P['robe_dk'])
        elif pose == 'raise':                        # one arm raised in blessing
            limb(d, (CX - 11, 33), (CX - 18, 46), 9, P['robe_hi'])
            limb(d, (CX - 18, 46), (CX - 17, 58), 8, P['robe_hi'])
            d.ellipse([CX - 20, 57, CX - 14, 63], fill=P['skin'])
            limb(d, (CX + 11, 33), (CX + 19, 24), 9, P['robe_hi'])
            limb(d, (CX + 19, 24), (CX + 20, 12), 8, P['robe_hi'])
            d.ellipse([CX + 17, 6, CX + 23, 13], fill=P['skin'])
        else:
            for sgn in (-1, 1):
                sw = sgn * s * 2
                limb(d, (CX + sgn * 11, 33), (CX + sgn * 16, 47 + sw), 9, P['robe_hi'])
                limb(d, (CX + sgn * 16, 47 + sw), (CX + sgn * 16, 58 + sw), 8, P['robe_hi'])
                d.ellipse([CX + sgn * 16 - 3, 57 + sw, CX + sgn * 16 + 3, 63 + sw], fill=P['skin'])
        _khuc_head(d, P, CX, top, 'back' if back else 'front', talk)
    bob = abs(s) * 1.5 if walking else 0
    out = canvas(FW, FH)
    out.alpha_composite(im, (0, int(-bob)))
    return outline(out)


def khuc_playing(frame=0):
    """Seen from behind, hunched at the Rex cabinet, elbows working."""
    P = {k: _P(v) for k, v in KHUC.items()}
    im = canvas(FW, 80)
    d = ImageDraw.Draw(im)
    d.polygon([(CX - 12, 24), (CX + 12, 24), (CX + 15, 70), (CX - 15, 70)], fill=P['robe'])
    d.polygon([(CX + 4, 24), (CX + 12, 24), (CX + 15, 70), (CX + 7, 70)], fill=P['robe_dk'])
    d.rectangle([CX - 13, 52, CX + 13, 55], fill=P['stole_dk'])
    jig = [0, 2, -1, 1][frame % 4]
    limb(d, (CX - 11, 30), (CX - 17, 42 + jig), 9, P['robe_hi'])
    limb(d, (CX + 11, 30), (CX + 17, 42 - jig), 9, P['robe_hi'])
    d.ellipse([CX - 10, 2, CX + 10, 24], fill=P['hair'])
    _colander(d, P, CX, 6 + (1 if frame % 2 else 0), 'front')
    return outline(im)


def khuc_crank(frame=0):
    """Standing side-on (facing west, towards the seat) turning a crank."""
    P = {k: _P(v) for k, v in KHUC.items()}
    im = khuc_frame('side').transpose(Image.FLIP_LEFT_RIGHT)
    return im
