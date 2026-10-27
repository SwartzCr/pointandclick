"""Writer for the AGS 3.6.1 main game data file (game28.dta), ported from the
editor's DataFileWriter.SaveThisGameToFile (Editor/AGS.Editor/DataFileWriter.cs).

The game is described with plain Python objects; anything a field doesn't
mention gets the editor's default for a new game.
"""
import random
from dataclasses import dataclass, field
from typing import List, Optional

from .binio import W

GAME_DATA_VERSION = 3060114          # kGameVersion_361_14
EDITOR_VERSION = '3.6.1.30'
SCRIPT_API_V361 = 3060100
MAX_INV = 301
MAXGLOBALMES = 500
MAXLIPSYNCFRAMES = 20
FONT_OUTLINE_AUTO = -10
GUIMAGIC = 0xcafebeef
GUI_VERSION = 119                    # kGuiVersion_350

# option indices (Common/ac/gamestructdefines.h)
OPT = dict(DEBUGMODE=0, WALKONLOOK=2, DIALOGIFACE=3, ANTIGLIDE=4, TWCUSTOM=5,
           DIALOGGAP=6, NOSKIPTEXT=7, DISABLEOFF=8, ALWAYSSPCH=9, SPEECHTYPE=10,
           PIXPERFECT=11, NOWALKMODE=12, LETTERBOX=13, FIXEDINVCURSOR=14,
           HIRES_FONTS=16, SPLITRESOURCES=17, ROTATECHARS=18, FADETYPE=19,
           HANDLEINVCLICKS=20, MOUSEWHEEL=21, DIALOGNUMBERED=22, DIALOGUPWARDS=23,
           ANTIALIASFONTS=25, THOUGHTGUI=26, TURNTOFACELOC=27, RIGHTLEFTWRITE=28,
           DUPLICATEINV=29, SAVESCREENSHOT=30, PORTRAITSIDE=31, STRICTSCRIPTING=32,
           LEFTTORIGHTEVAL=33, COMPRESSSPRITES=34, STRICTSTRINGS=35, NEWGUIALPHA=36,
           RUNGAMEDLGOPTS=37, NATIVECOORDINATES=38, GLOBALTALKANIMSPD=39,
           SPRITEALPHA=40, SAFEFILEPATHS=41, DIALOGOPTIONSAPI=42, BASESCRIPTAPI=43,
           SCRIPTCOMPATLEV=44, RENDERATSCREENRES=45, RELATIVEASSETRES=46,
           WALKSPEEDABSOLUTE=47, CLIPGUICONTROLS=48, GAMETEXTENCODING=49,
           KEYHANDLEAPI=50, SCALECHAROFFSETS=52, LIPSYNCTEXT=99)

CHF_MANUALSCALING = 1
CHF_NOINTERACT = 4
CHF_NODIAGONAL = 8
CHF_NOLIGHTING = 0x20
CHF_NOTURNING = 0x40
CHF_NOBLOCKING = 0x200
CHF_SCALEMOVESPEED = 0x400
CHF_ANTIGLIDE = 0x20000
SPF_ALPHACHANNEL = 0x10
MCF_STANDARD = 4


@dataclass
class Font:
    data: bytes                       # .wfn file
    size: int = 0                     # 0: size multiplier mode
    multiplier: int = 1
    outline: int = -1                 # -1 none, FONT_OUTLINE_AUTO, or a font number
    outline_thickness: int = 1
    outline_style: int = 0            # 0 squared, 1 rounded
    y_offset: int = 0
    line_spacing: int = 0


@dataclass
class Cursor:
    name: str
    image: int
    hotx: int = 0
    hoty: int = 0
    standard: bool = True


@dataclass
class InvItem:
    script: str
    name: str
    image: int
    cursor: int = 0
    hotx: int = 0
    hoty: int = 0
    start: bool = False


@dataclass
class Frame:
    image: int
    delay: int = 0
    flipped: bool = False


@dataclass
class View:
    name: str
    loops: List[List[Frame]]


@dataclass
class Character:
    script: str
    name: str
    view: int                         # 1-based view numbers, 0 = none
    speech_view: int = 0
    idle_view: int = 0
    room: int = -1
    x: int = 0
    y: int = 0
    speech_color: int = 0xFFFF
    walk_x: int = 4
    walk_y: int = 4
    anim_delay: int = 4
    speech_anim_delay: int = 5
    idle_delay: int = 20
    clickable: bool = True
    solid: bool = False
    diagonal: bool = False
    turn_before_walking: bool = True
    antiglide: bool = False


@dataclass
class AudioClip:
    script: str
    filename: str
    data: bytes
    type: int = 2                     # clip type id (1 music, 2 sound)
    file_type: int = 3                # 1 ogg, 3 wav
    repeat: bool = False
    priority: int = 50
    volume: int = 100


@dataclass
class Game:
    name: str
    width: int
    height: int
    save_folder: str
    fonts: List[Font]
    sprites: list                     # RGBA images, indexed by number
    cursors: List[Cursor]
    inventory: List[InvItem]
    views: List[View]
    characters: List[Character]
    player: int
    global_script: bytes
    dialog_script: bytes
    modules: list = field(default_factory=list)   # other compiled scripts, in order
    audio: List[AudioClip] = field(default_factory=list)
    guid: str = '{a6f0c3d2-6e0b-4c8e-9a51-5ac7a9a5ta01}'
    unique_id: int = 0
    speech_style: int = 0             # LucasArts
    debug: bool = False
    dialog_gui: int = 0
    text_window: int = 0
    rotate_chars: bool = True
    fade_type: int = 0                # fade out and in
    skip_speech: int = 0              # mouse, keyboard or timer
    interface_disabled: int = 2       # unchanged
    global_speech_anim_delay: int = 5
    use_global_speech_delay: bool = False
    text_encoding: int = 65001
    room_names: dict = field(default_factory=dict)

    def write(self):
        return _write_game(self)


def _interactions_none(w):
    w.i32(0)


def _write_game(g: Game):
    w = W()
    w.raw(b'Adventure Creator Game File v2')
    w.i32(GAME_DATA_VERSION)
    w.i32(len(EDITOR_VERSION))
    w.raw(EDITOR_VERSION.encode())
    w.i32(0)                                   # extended engine caps

    # ---- GameSetupStructBase
    w.fixed(g.name[:49], 50)
    w.zeros(2)
    opts = [0] * 100
    o = OPT
    opts[o['DEBUGMODE']] = 1 if g.debug else 0
    opts[o['NOWALKMODE']] = 0
    opts[o['DIALOGGAP']] = 0
    opts[o['DIALOGIFACE']] = g.dialog_gui
    opts[o['STRICTSTRINGS']] = 1
    opts[o['STRICTSCRIPTING']] = 1
    opts[o['NEWGUIALPHA']] = 2                 # proper alpha
    opts[o['SPRITEALPHA']] = 1                 # proper alpha
    opts[o['FIXEDINVCURSOR']] = 1
    opts[o['GLOBALTALKANIMSPD']] = (g.global_speech_anim_delay if g.use_global_speech_delay
                                    else -g.global_speech_anim_delay - 1)
    opts[o['LEFTTORIGHTEVAL']] = 1
    opts[o['MOUSEWHEEL']] = 1
    opts[o['DIALOGNUMBERED']] = 1
    opts[o['PIXPERFECT']] = 1
    opts[o['FADETYPE']] = g.fade_type
    opts[o['SAVESCREENSHOT']] = 0
    opts[o['NOSKIPTEXT']] = g.skip_speech
    opts[o['SPEECHTYPE']] = g.speech_style
    opts[o['TWCUSTOM']] = g.text_window
    opts[o['THOUGHTGUI']] = 0
    opts[o['TURNTOFACELOC']] = 1
    opts[o['ROTATECHARS']] = 1 if g.rotate_chars else 0
    opts[o['NATIVECOORDINATES']] = 1
    opts[o['WALKONLOOK']] = 0
    opts[o['DISABLEOFF']] = g.interface_disabled
    opts[o['SAFEFILEPATHS']] = 1
    opts[o['DIALOGOPTIONSAPI']] = 1
    opts[o['BASESCRIPTAPI']] = SCRIPT_API_V361
    opts[o['SCRIPTCOMPATLEV']] = SCRIPT_API_V361
    opts[o['RENDERATSCREENRES']] = 0
    opts[o['RELATIVEASSETRES']] = 0
    opts[o['WALKSPEEDABSOLUTE']] = 1
    opts[o['CLIPGUICONTROLS']] = 1
    opts[o['GAMETEXTENCODING']] = g.text_encoding
    opts[o['KEYHANDLEAPI']] = 1
    opts[o['SCALECHAROFFSETS']] = 1
    opts[o['COMPRESSSPRITES']] = 2
    for v in opts:
        w.i32(v)
    for _ in range(256):
        w.i8(0)                                # palette uses: game-wide
    for _ in range(256):
        w.zeros(4)                             # palette
    w.i32(len(g.views))
    w.i32(len(g.characters))
    w.i32(g.player)
    w.i32(0)                                   # max score
    w.i16(len(g.inventory) + 1)
    w.zeros(2)
    w.i32(0)                                   # dialogs
    w.i32(0)                                   # numdlgmessage
    w.i32(len(g.fonts))
    w.i32(4)                                   # colour depth: 32-bit
    w.i32(0)                                   # target_win
    w.i32(0)                                   # dialog bullet
    w.i16(0)                                   # inv hotspot dot colour
    w.i16(0)                                   # inv hotspot crosshair colour
    w.i32(g.unique_id or random.randint(1, 0x7FFFFFFF))
    w.i32(0)                                   # GUIs
    w.i32(len(g.cursors))
    w.i32(8)                                   # kGameResolution_Custom
    w.i32(g.width)
    w.i32(g.height)
    w.i32(0)                                   # lipsync default frame
    w.i32(0)                                   # inv hotspot marker sprite
    w.zeros(16 * 4)
    ext_off_pos = w.pos()
    w.i32(0)
    for _ in range(MAXGLOBALMES):
        w.i32(0)
    w.i32(1)                                   # dict != null
    w.i32(0)                                   # globalscript != null
    w.i32(0)                                   # chars != null
    w.i32(1)                                   # compiled_script != null

    w.fixed(g.guid, 40)
    w.fixed('sav', 20)
    w.fixed(g.save_folder[:49], 50)

    for f in g.fonts:
        flags = 0x04                           # report nominal height
        if f.size == 0:
            flags |= 0x01
        w.i32(flags)
        w.i32(f.multiplier if f.size == 0 else f.size * f.multiplier)
        w.i32(f.outline)
        w.i32(f.y_offset)
        w.i32(f.line_spacing)

    w.i32(len(g.sprites))
    for im in g.sprites:
        w.i8(SPF_ALPHACHANNEL if im is not None else 0)

    w.zeros(68)                                # inventory slot 0
    for inv in g.inventory:
        w.fixed(inv.name[:24], 24)
        w.zeros(4)
        w.i32(inv.image)
        w.i32(inv.cursor)
        w.i32(inv.hotx)
        w.i32(inv.hoty)
        w.zeros(5 * 4)
        w.i8(1 if inv.start else 0)
        w.zeros(3)

    for c in g.cursors:
        w.i32(c.image)
        w.i16(c.hotx)
        w.i16(c.hoty)
        w.i16(-1)                              # no animation view
        w.fixed(c.name[:9], 9)
        w.i8(0)
        w.i8(MCF_STANDARD if c.standard else 0)
        w.zeros(3)

    for _ in g.characters:
        _interactions_none(w)
    for _ in g.inventory:
        _interactions_none(w)

    w.i32(0)                                   # parser words
    w.raw(g.global_script)
    w.raw(g.dialog_script)
    w.i32(len(g.modules))
    for m in g.modules:
        w.raw(m)

    # views
    for v in g.views:
        w.i16(len(v.loops))
        for loop in v.loops:
            w.i16(len(loop))
            w.i32(0)                           # loop flags
            for fr in loop:
                w.i32(fr.image)
                w.i16(0); w.i16(0)
                w.i16(fr.delay)
                w.i16(0)
                w.i32(1 if fr.flipped else 0)
                w.i32(-1)                      # sound
                w.i32(0); w.i32(0)

    for i, c in enumerate(g.characters):
        flags = 0
        if not c.clickable:
            flags |= CHF_NOINTERACT
        if not c.diagonal:
            flags |= CHF_NODIAGONAL
        if c.antiglide:
            flags |= CHF_ANTIGLIDE
        if not c.solid:
            flags |= CHF_NOBLOCKING
        if not c.turn_before_walking:
            flags |= CHF_NOTURNING
        w.i32(c.view - 1)                      # defview
        w.i32(c.speech_view - 1)               # talkview
        w.i32(c.view - 1)                      # view
        w.i32(c.room)
        w.i32(0)                               # prevroom
        w.i32(c.x)
        w.i32(c.y)
        w.i32(0)                               # wait
        w.i32(flags)
        w.i16(0)                               # following
        w.i16(0)                               # followinfo
        w.i32(c.idle_view - 1)
        w.i16(c.idle_delay)
        w.i16(0)                               # idleleft
        w.i16(0)                               # transparency
        w.i16(0)                               # baseline
        w.i32(0)                               # activeinv
        w.i32(c.speech_color)
        w.i32(-1)                              # thinkview
        w.i16(-1)                              # blinkview
        w.i16(0); w.i16(0); w.i16(0)           # blink interval/timer/frame
        w.i16(c.walk_y)
        w.i16(0)                               # pic_yoffs
        w.i32(0)                               # z
        w.i32(0)                               # walkwait
        w.i16(c.speech_anim_delay)
        w.i16(5)                               # idle anim speed
        w.i16(0); w.i16(0)                     # blocking w/h
        w.i32(0)                               # index_id
        w.i16(0)                               # pic_xoffs
        w.i16(0)                               # walkwaitcounter
        w.i16(0); w.i16(0); w.i16(0); w.i16(0) # loop, frame, walking, animating
        w.i16(c.walk_x)
        w.i16(c.anim_delay)
        for inv in g.inventory:
            w.i16(1 if (i == g.player and inv.start) else 0)
        w.zeros((MAX_INV - len(g.inventory)) * 2)
        w.i16(0); w.i16(0)                     # actx, acty
        w.fixed(c.name[:40], 40)
        w.fixed(c.script[:20], 20)
        w.i8(1)                                # on
        w.i8(0)

    for _ in range(MAXLIPSYNCFRAMES):
        w.zeros(50)
    # no global messages, no dialogs

    # GUIs (none)
    w.i32(GUIMAGIC)
    w.i32(GUI_VERSION)
    w.i32(0)
    for _ in range(6):                         # buttons, labels, inv windows,
        w.i32(0)                               # sliders, text boxes, list boxes

    # plugins
    w.i32(1)
    w.i32(0)

    # custom property schema and values
    w.i32(2)
    w.i32(0)
    for _ in g.characters:
        w.i32(2); w.i32(0)
    w.i32(1); w.i32(0)                         # inventory slot 0
    for _ in g.inventory:
        w.i32(2); w.i32(0)

    for v in g.views:
        w.cstr(v.name)
    w.i8(0)                                    # inventory slot 0
    for inv in g.inventory:
        w.cstr(inv.script)
    # no dialog names

    # audio clip types: speech (0), music (1), sound (2)
    w.i32(3)
    for tid, chans in ((0, 1), (1, 1), (2, 0)):
        w.i32(tid); w.i32(chans); w.i32(0); w.i32(0); w.i32(0)
    w.i32(len(g.audio))
    for i, a in enumerate(g.audio):
        w.i32(i)
        w.fixed(a.script[:29], 30)
        w.fixed(a.filename[:14], 15)
        w.i8(1)                                # bundled in the game file
        w.i8(a.type)
        w.i8(a.file_type)
        w.i8(1 if a.repeat else 0)
        w.i8(0)
        w.i16(a.priority)
        w.i16(a.volume)
        w.zeros(2)
        w.i32(0)
    w.i32(-1)                                  # score sound

    if g.debug:
        w.i32(len(g.room_names))
        for num, name in sorted(g.room_names.items()):
            w.i32(num)
            w.cstr(name)

    # extensions
    w.patch32(ext_off_pos, w.pos())

    def ext(name, body):
        w.i8(0)
        w.fixed(name, 16)
        w.i64(len(body))
        w.raw(body)

    b = W()
    for f in g.fonts:
        b.i32(f.outline_thickness); b.i32(f.outline_style)
        b.zeros(16)
    ext('v360_fonts', b.bytes())
    b = W()
    for c in g.cursors:
        b.i32(0); b.zeros(12)
    ext('v360_cursors', b.bytes())
    b = W()
    b.lstr(g.name)
    b.lstr(g.save_folder)
    b.i32(len(g.characters))
    for c in g.characters:
        b.lstr(c.script); b.lstr(c.name)
    b.i32(len(g.inventory) + 1)
    b.i32(0)
    for inv in g.inventory:
        b.lstr(inv.name)
    b.i32(len(g.cursors))
    for c in g.cursors:
        b.lstr(c.name)
    b.i32(len(g.audio))
    for a in g.audio:
        b.lstr(a.script); b.lstr(a.filename)
    ext('v361_objnames', b.bytes())
    w.i8(0xFF)
    return w.bytes()


def auto_header(g: Game):
    """The editor's _AutoGenerated.ash, for the script compiler."""
    out = []
    for a in g.audio:
        out.append('import AudioClip %s;' % a.script)
    out.append('enum AudioType {\n  eAudioTypeMusic = 1,\n  eAudioTypeSound = 2\n};')
    out.append('import Character character[%d];' % len(g.characters))
    for c in g.characters:
        out.append('import Character %s;' % c.script)
    for i, c in enumerate(g.characters):
        if c.script.startswith('c') and len(c.script) > 1:
            out.append('#define %s %d' % (c.script[1:].upper(), i))
    out.append('enum CursorMode {\n' + ',\n'.join(
        '  eMode%s = %d' % (c.name, i) for i, c in enumerate(g.cursors)) + '\n};')
    out.append('enum FontType {\n' + ',\n'.join(
        '  eFont%d = %d' % (i, i) for i in range(len(g.fonts))) + '\n};')
    out.append('import InventoryItem inventory[%d];' % (len(g.inventory) + 1))
    for inv in g.inventory:
        out.append('import InventoryItem %s;' % inv.script)
    for i, v in enumerate(g.views):
        out.append('#define %s %d' % (v.name.upper(), i + 1))
    return '\n'.join(out) + '\n'
