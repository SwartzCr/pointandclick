"""Writes everything in assets/: sprites, room backgrounds and masks, fonts,
sounds and music, plus manifest.json, which tools/build.py turns into the
game. Needs Python 3 with Pillow, numpy and scipy, and the DejaVu Sans fonts.

    python3 tools/make_assets.py
"""
import json
import os
import shutil
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(__file__))
import art_people as P
import guest_sprite as G
import nave_painted as NP
import nave_muse as NM
import art_rooms as R
import art_ui as U
import sound as S
from agsbuild import formats

ROOT = os.path.join(os.path.dirname(__file__), '..', 'assets')

sprites = {}          # name -> image (insertion order = sprite number order)


def spr(name, im):
    if name in sprites:
        raise SystemExit('duplicate sprite %s' % name)
    sprites[name] = im
    return name


# ------------------------------------------------------------------ characters
NECK = {'': {}, 'B': {'beads': True}, 'U': {'uv': True}, 'BU': {'beads': True, 'uv': True}}


def guest_views():
    views = []
    for tag, kind in NECK.items():
        sfx = ('_' + tag) if tag else ''
        walk = {}
        for dr, n in (('front', 6), ('side', 8), ('back', 6)):
            frames = [spr('guest%s_%s_stand' % (sfx, dr), G.guest_frame(dr, kind=kind))]
            for i in range(n):
                frames.append(spr('guest%s_%s_walk%d' % (sfx, dr, i),
                                  G.guest_frame(dr, (i + 1) / n, walking=True, kind=kind)))
            walk[dr] = frames
        loops = [[(f, 0, False) for f in walk['front']],
                 [(f, 0, True) for f in walk['side']],
                 [(f, 0, False) for f in walk['side']],
                 [(f, 0, False) for f in walk['back']]]
        views.append(dict(name='VGUEST' + tag, loops=loops))
        talk = {}
        for dr in ('front', 'side'):
            talk[dr] = [spr('guest%s_%s_talk%d' % (sfx, dr, k), G.guest_frame(dr, talk=bool(k), kind=kind))
                        for k in range(2)]
        talk['back'] = [walk['back'][0]]
        tl = [[(f, 0, False) for f in talk['front']],
              [(f, 0, True) for f in talk['side']],
              [(f, 0, False) for f in talk['side']],
              [(f, 0, False) for f in talk['back']]]
        views.append(dict(name='VGTALK' + tag, loops=tl))
    return views


def khuc_views():
    import khuc_sprite as K
    v = K.views()
    st = v['stand']
    walk = {'front': [spr('khuc_front_stand', st['front'])] + [spr('khuc_front_walk%d' % i, f) for i, f in enumerate(v['walk_front'])],
            'side': [spr('khuc_side_stand', st['side'])] + [spr('khuc_side_walk%d' % i, f) for i, f in enumerate(v['walk_side'])],
            'back': [spr('khuc_back_stand', st['back'])] + [spr('khuc_back_walk%d' % i, f) for i, f in enumerate(v['walk_back'])]}
    loops = [[(f, 0, False) for f in walk['front']],
             [(f, 0, True) for f in walk['side']],
             [(f, 0, False) for f in walk['side']],
             [(f, 0, False) for f in walk['back']]]
    talkf = [walk['front'][0], spr('khuc_front_talk1', v['talk_front'][1])]
    talks = [walk['side'][0], spr('khuc_side_talk1', v['talk_side'][1])]
    tl = [[(f, 0, False) for f in talkf], [(f, 0, True) for f in talks], [(f, 0, False) for f in talks],
          [(walk['back'][0], 0, False)]]
    play = [spr('khuc_play%d' % k, f) for k, f in enumerate(v['play'])]
    raise_ = spr('khuc_raise', v['raise_'])
    crank = spr('khuc_crank', v['crank'])
    blank = spr('blank_char', Image.new('RGBA', (2, 2), (0, 0, 0, 0)))
    return [dict(name='VKHUC', loops=loops), dict(name='VKTALK', loops=tl),
            dict(name='VKPLAY', loops=[[(f, 2, False) for f in play]] * 4),
            dict(name='VKRAISE', loops=[[(raise_, 0, False)]] * 4),
            dict(name='VKCRANK', loops=[[(crank, 0, False)], [(crank, 0, True)], [(crank, 0, False)], [(crank, 0, False)]]),
            dict(name='VBLANK', loops=[[(blank, 0, False)]] * 4)]


# ------------------------------------------------------------------ fonts
def make_font(path, size, ascii_only=True):
    ft = ImageFont.truetype(path, size)
    asc, desc = ft.getmetrics()
    h = asc + desc
    glyphs = []
    for c in range(128):
        ch = chr(c) if c >= 32 else ' '
        w = max(1, int(round(ft.getlength(ch))))
        im = Image.new("1", (w, h), 0)
        d = ImageDraw.Draw(im)
        d.fontmode = '1'
        d.text((0, 0), ch, font=ft, fill=1)
        glyphs.append(im)
    return formats.write_wfn(glyphs)


def save_png(im, rel):
    p = os.path.join(ROOT, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    im.save(p)
    return rel


def main():
    if os.path.isdir(ROOT):
        shutil.rmtree(ROOT)
    os.makedirs(ROOT)
    manifest = dict(views=[], rooms={}, inventory=[], fonts=[], audio=[], sprites=[])

    spr('cursor', U.cursor())
    spr('blank', U.blank())
    manifest['views'] += guest_views()
    manifest['views'] += khuc_views()

    painted_icons = NM.icons()
    for script, (name, fn) in U.ICONS.items():
        icon = painted_icons[script] if script in painted_icons else fn()
        manifest['inventory'].append(dict(script=script, name=name, sprite=spr('inv_' + script, icon)))

    rooms = [(1, NM.nave()), (2, R.crypt()), (3, R.title())]
    for num, sc in rooms:
        bgs = [save_png(sc.bg, 'rooms/%s_bg0.png' % sc.name)]
        if sc.uv_marks:
            bgs.append(save_png(sc.uv_frame(), 'rooms/%s_bg1.png' % sc.name))
        objs = []
        for o in sc.objects:
            names = {}
            for state, im in o['sprites'].items():
                names[state] = spr('%s_%s_%s' % (sc.name, o['script'], state), im)
            objs.append(dict(script=o['script'], name=o['name'], x=o['x'], y=o['y'], visible=o['visible'],
                             baseline=o['baseline'], clickable=o['clickable'], state=o['state'], sprites=names))
        manifest['rooms'][str(num)] = dict(
            name=sc.name, bg=bgs,
            walk=save_png(sc.walk, 'rooms/%s_walk.png' % sc.name),
            hot=save_png(sc.hot, 'rooms/%s_hot.png' % sc.name),
            wb=save_png(sc.wb, 'rooms/%s_wb.png' % sc.name),
            wb_baselines=sc.wb_baselines,
            hotspots=[[s, n, list(w)] for s, n, w in sc.hotspots],
            objects=objs)
    spr('plate', R.ending_plate())

    fonts = [('font0.wfn', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 12, 'none'),
             ('font1.wfn', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 12, 'auto'),
             ('font2.wfn', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 12, 'none'),
             ('font3.wfn', '/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf', 12, 'none')]
    os.makedirs(os.path.join(ROOT, 'fonts'))
    for fname, path, size, outl in fonts:
        with open(os.path.join(ROOT, 'fonts', fname), 'wb') as f:
            f.write(make_font(path, size))
        manifest['fonts'].append(dict(file='fonts/' + fname, outline=outl))

    os.makedirs(os.path.join(ROOT, 'audio'))
    for name, fn in S.EFFECTS.items():
        rel = 'audio/%s.wav' % name
        with open(os.path.join(ROOT, rel), 'wb') as f:
            f.write(S.wav_bytes(fn()))
        manifest['audio'].append(dict(script=name, file=rel, type=2, repeat=False))
    for name, fn in S.MUSIC.items():
        rel = 'audio/%s.wav' % name
        with open(os.path.join(ROOT, rel), 'wb') as f:
            f.write(S.wav_bytes(fn(), vol=0.6))
        manifest['audio'].append(dict(script=name, file=rel, type=1, repeat=True))

    for name, im in sprites.items():
        save_png(im, 'sprites/%s.png' % name)
    manifest['sprites'] = list(sprites)
    manifest['fork_frames'] = [s for s in sprites if s.startswith('nave_oFork_')]
    with open(os.path.join(ROOT, 'manifest.json'), 'w') as f:
        json.dump(manifest, f, indent=1)
    print('%d sprites, %d views, %d rooms' % (len(sprites), len(manifest['views']), len(rooms)))


if __name__ == '__main__':
    main()
