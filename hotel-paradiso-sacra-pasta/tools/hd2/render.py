"""Render the painted Nave at 1280x800 and 640x400."""
import sys
import numpy as np
from PIL import Image
import paint
import nave2
import cast

OUT = sys.argv[1] if len(sys.argv) > 1 else '/tmp/claude-0'


def render(scale):
    paint.set_scale(scale)
    pt = nave2.nave()
    room = pt.image(256, dither=True)
    full = Image.new('RGB', (int(1280 * scale), int(800 * scale)), (0, 0, 0))
    full.paste(room, (0, 0))
    # characters: a soft contact shadow then the flat sprite
    for spr, x, y in ((cast.guest(), 760, 566), (cast.khuc(), 1170, 560)):
        sh = Image.new('L', full.size, 0)
        from PIL import ImageDraw, ImageFilter
        ImageDraw.Draw(sh).ellipse([(x - 52) * scale, (y - 9) * scale, (x + 52) * scale, (y + 9) * scale], fill=120)
        sh = sh.filter(ImageFilter.GaussianBlur(3 * scale))
        a = np.asarray(sh, np.float32)[..., None] / 255
        arr = np.asarray(full, np.float32)
        arr = arr * (1 - a) + arr * 0.35 * a + np.array([40, 24, 70]) * 0.65 * a * 0.3
        full = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
        spr.paste_into(full, x, y)
    nave2.interface(full, scale)
    return full


if __name__ == '__main__':
    hi = render(1.0)
    hi.save(f'{OUT}/nave_painted_1280x800.png')
    lo = render(0.5)
    lo.save(f'{OUT}/nave_painted_640x400.png')
    lo.resize((1280, 800), Image.NEAREST).save(f'{OUT}/nave_painted_640x400_x2.png')
    print('ok')
