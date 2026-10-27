"""Renders the 1280x800 test of the Nave (with characters and the interface)."""
import sys, time
from PIL import Image
import nave, people

def place(bg, spr, x, y, scale=1.0):
    from PIL import ImageDraw, ImageFilter
    sh = Image.new('RGBA', bg.size, (0, 0, 0, 0))
    w = 70 * scale
    ImageDraw.Draw(sh).ellipse([x - w / 2 + 8, y - 10, x + w / 2 + 14, y + 8], fill=(40, 16, 50, 110))
    bg.alpha_composite(sh.filter(ImageFilter.GaussianBlur(3)))
    if scale != 1.0:
        spr = spr.resize((int(spr.width * scale), int(spr.height * scale)), Image.NEAREST)
    bg.alpha_composite(spr, (int(x - spr.width / 2), int(y - spr.height)))

t = time.time()
bg = nave.nave()
room = bg.copy()
place(room, people.khuc(), 1136, 452, 0.92)
place(room, people.guest(talk=True), 820, 566, 1.0)
nave.interface(room)
room.save(sys.argv[1] if len(sys.argv) > 1 else '/tmp/claude-0/nave_hd.png')
bg.save('/tmp/claude-0/nave_hd_bg.png')
print('%.1fs' % (time.time() - t))

# side by side with the current 640x400 art, same crop, the old one doubled
old = Image.open('../../assets/rooms/nave_bg0.png').convert('RGBA')
for name, x, y in (('guest_front_talk1', 410, 283), ('khuc_front_stand', 568, 226)):
    spr = Image.open('../../assets/sprites/%s.png' % name)
    old.alpha_composite(spr, (x - spr.width // 2, y - spr.height))
old2 = old.resize((1280, 800), Image.NEAREST)
crop = (440, 20, 1240, 580)
cmp_ = Image.new('RGBA', (1600 + 20, 560), (20, 14, 24, 255))
cmp_.alpha_composite(old2.crop(crop), (0, 0))
cmp_.alpha_composite(room.crop(crop), (820, 0))
cmp_.save('/tmp/claude-0/nave_compare.png')
