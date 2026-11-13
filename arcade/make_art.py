"""The pictures for the arcade launcher's cards, and its icon.

    python3 arcade/make_art.py <out dir> <Do Not Disturb's game/gui/main_menu image>

Writes <out>/art/hotel-paradiso.png, sacra-pasta.png, do-not-disturb.png and
<out>/AppIcon.iconset/ (turn that into AppIcon.icns with `iconutil -c icns`).
"""
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')


def main(out, vn_menu):
    os.makedirs(os.path.join(out, 'art'), exist_ok=True)
    sys.path.insert(0, os.path.join(ROOT, 'hotel-paradiso-scummc', 'tools'))
    import art
    art.render_title().convert('RGB').resize((1280, 576), Image.NEAREST).save(os.path.join(out, 'art', 'hotel-paradiso.png'))
    sacra = Image.open(os.path.join(ROOT, 'hotel-paradiso-sacra-pasta', 'assets', 'rooms', 'title_bg0.png')).convert('RGB')
    sacra.crop((0, 0, 640, 288)).resize((1280, 576), Image.NEAREST).save(os.path.join(out, 'art', 'sacra-pasta.png'))
    vn = Image.open(vn_menu).convert('RGB')
    vn.thumbnail((1600, 900))
    vn.save(os.path.join(out, 'art', 'do-not-disturb.png'))

    # the icon: the middle of the Sacra Pasta title, on a rounded square
    side = 288
    sq = sacra.crop((320 - side // 2, 0, 320 + side // 2, side)).resize((1024, 1024), Image.NEAREST)
    mask = Image.new('L', (1024, 1024), 0)
    ImageDraw.Draw(mask).rounded_rectangle([40, 40, 984, 984], radius=180, fill=255)
    icon = Image.new('RGBA', (1024, 1024), (0, 0, 0, 0))
    icon.paste(sq, (0, 0), mask)
    iconset = os.path.join(out, 'AppIcon.iconset')
    os.makedirs(iconset, exist_ok=True)
    for s in (16, 32, 128, 256, 512):
        icon.resize((s, s), Image.LANCZOS).save(os.path.join(iconset, 'icon_%dx%d.png' % (s, s)))
        icon.resize((s * 2, s * 2), Image.LANCZOS).save(os.path.join(iconset, 'icon_%dx%d@2x.png' % (s, s)))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
