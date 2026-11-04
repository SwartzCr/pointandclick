"""Every line of dialogue, description and on-screen text in the game, as one Markdown file
you can edit (DIALOGUE.md), and the way back in.

    python3 tools/dialogue.py export     # writes DIALOGUE.md and tools/dialogue_map.json
    python3 tools/dialogue.py import     # puts edited DIALOGUE.md lines back into the sources

Each line in DIALOGUE.md starts with an ID in backticks (`s123`). Only the text after the
speaker's colon is read back in, so change the words and leave the ID and the speaker alone.
The map remembers where each ID came from and what it said when exported, so an import only
touches lines you changed, and refuses if the source moved underneath it (export again then).
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
GAME = os.path.join(ROOT, 'src', 'game.asc')
NAMES = [os.path.join(HERE, f) for f in ('nave_v3.py', 'crypt_v3.py', 'hotel_mini.py')]
MD = os.path.join(ROOT, 'DIALOGUE.md')
MAP = os.path.join(HERE, 'dialogue_map.json')

LIT = re.compile(r'"((?:[^"\\]|\\.)*)"')
FUNC = re.compile(r'^(?:void|bool|int|String|function)\s+(\w+)\s*\(', re.M)

SPEAKERS = [('cKhuc.Say', 'Chuk'), ('cClown1.Say', 'Clown'), ('cClown2.Say', 'Clown'),
            ('cClown3.Say', 'Clown'), ('cMini.Say', 'Guest'), ('player.Say', 'Bellhop'),
            ('Narrate(', 'Narration'), ('Gustav(', 'Gustav'), ('Choose(', 'Choice'),
            ('ShowNote(', 'Note')]

# technical strings: puzzle words and verb names the code compares against
SKIP = re.compile(r'^(|%s %s|[A-Z]+|Open|Close|Push|Pull|Pick up|Look at|Talk to|Use|Walk to|'
                  r'Use %s with|penne|farfalle|shell)$')

TITLES = {
    'Sentence': 'The sentence line', 'DrawUI': 'The menu', 'ReadPamphlet': 'The Spaghetti Theory pamphlet',
    'TalkKhucNave': 'Talking to Chuk in the Nave', 'TalkKhucCrypt': 'Talking to Chuk in the Crypt',
    'KhucHint': 'Chuk\'s hints (Nave)', 'CryptHint': 'Chuk\'s hints (Crypt)', 'Ceremony': 'The ordination',
    'ShowEnding': 'The ending cards', 'ReadNewspaper': 'The Daily Noodle', 'CallGustav': 'Gustav on the phone',
    'EndRoomService': 'Ending: room service for all', 'EndFreePlay': 'Ending: all games are free play',
    'EndParty': 'Ending: let\'s party', 'SitPope': 'The Pope Seat and the papal request',
    'NaveHot': 'The Nave: things in the room', 'NaveObj': 'The Nave: objects',
    'CryptHot': 'The Crypt: things in the room', 'CryptObj': 'The Crypt: objects',
    'HotelHot': 'HOTEL.EXE: things in the room', 'HotelObj': 'HOTEL.EXE: objects',
    'LookItem': 'Looking at things in your pockets', 'UseOnSelf': 'Using things on yourself',
    'SelfAction': 'Clicking on yourself', 'Stock': 'Stock replies', 'on_event': 'Arriving in rooms',
    'GiveKhuc': 'Giving things to Chuk', 'top': 'Game settings', 'PlayRex': 'T. Rex', 'PlayTrackball': 'MEATBALL MADNESS',
    'Confess': 'CONFESS', 'ConfessGame': 'CONFESS', 'DoAction': 'Doing things',
}


def unescape(t):
    return t.replace('\\"', '"').replace('\\\\', '\\')


def escape(t):
    return t.replace('\\', '\\\\').replace('"', '\\"')


def speaker(line_before):
    best, pos = 'Text', -1
    for key, who in SPEAKERS:
        p = line_before.rfind(key)
        if p > pos:
            best, pos = who, p
    if best == 'Text':
        m = re.search(r'\b(a|b)\s*=\s*$', line_before)
        if m:
            best = 'Card title' if m.group(1) == 'a' else 'Card text'
    return best


def export():
    src = open(GAME, encoding='utf-8').read()
    funcs = [(m.start(), m.group(1)) for m in FUNC.finditer(src)]
    entries, sections = [], []
    for m in LIT.finditer(src):
        text = m.group(1)
        if SKIP.match(text) or not re.search('[a-z]', text) and len(text) < 3:
            continue
        fn = 'top'
        for p, name in funcs:
            if p < m.start():
                fn = name
        ls = src.rfind('\n', 0, m.start()) + 1
        before = src[ls:m.start()]
        if '//' in before:
            continue                      # inside a comment
        # in a call spanning lines, look back to the statement's start
        st = max(src.rfind(';', 0, m.start()), src.rfind('{', 0, m.start()), src.rfind('}', 0, m.start()))
        who = speaker(src[st + 1:m.start()])
        if who == 'Note' and src[st + 1:m.start()].count('"') >= 2:
            who = 'Note text'
        elif who == 'Note':
            who = 'Note title'
        entries.append(dict(id='s%03d' % (len(entries) + 1), file='game', start=m.start(1), end=m.end(1),
                            orig=text, fn=fn, who=who))
    for path in NAMES:
        s = open(path, encoding='utf-8').read()
        for m in re.finditer(r"sc\.(?:hotspot|obj)\('\w+', '((?:[^'\\]|\\.)*)'", s):
            entries.append(dict(id='n%03d' % (len([e for e in entries if e['id'][0] == 'n']) + 1),
                                file=os.path.basename(path), start=m.start(1), end=m.end(1),
                                orig=m.group(1), fn='names:' + os.path.basename(path), who='Name'))
    out = ['# Hotel Paradiso: Sacra Pasta — all the words', '',
           'Every line of dialogue, description and on-screen text, in the order it appears in the game\'s',
           'script, grouped by where it\'s used. Edit the words after the colon; leave the `ID` and the',
           'speaker as they are. Then upload the file and ask for it to be imported.', '',
           '- `[` is a line break (`[[` leaves an empty line), used in notes and long lines.',
           '- `%s` and `%d` are filled in by the game (a name, a number): keep them, in the same order.',
           '- **Choice** lines are what you can pick in a conversation menu.',
           '- Hover names (the last sections) are what shows when the mouse is over something.', '']
    last = None
    for e in entries:
        if e['fn'] != last:
            last = e['fn']
            if last.startswith('names:'):
                room = {'nave_v3.py': 'the Nave', 'crypt_v3.py': 'the Crypt', 'hotel_mini.py': 'HOTEL.EXE'}[last[6:]]
                out += ['', '## Hover names in %s' % room, '']
            else:
                t = TITLES.get(last, re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', last))
                if t not in sections:
                    sections.append(t)
                    out += ['', '## %s' % t, '']
                else:
                    out += ['', '## %s (continued)' % t, '']
        text = unescape(e['orig']) if e['file'] == 'game' else e['orig'].replace("\\'", "'")
        out.append('- `%s` **%s:** %s' % (e['id'], e['who'], text))
    open(MD, 'w', encoding='utf-8').write('\n'.join(out) + '\n')
    json.dump(entries, open(MAP, 'w'), indent=0)
    print('%d lines -> %s' % (len(entries), MD))


def import_(md=MD):
    entries = {e['id']: e for e in json.load(open(MAP))}
    new = {}
    for line in open(md, encoding='utf-8'):
        m = re.match(r'^- `([sn]\d+)` \*\*[^*]*:\*\* ?(.*?)\s*$', line)
        if m:
            new[m.group(1)] = m.group(2)
    files = {'game': GAME}
    files.update({os.path.basename(p): p for p in NAMES})
    changed = 0
    for fname, path in files.items():
        src = open(path, encoding='utf-8').read()
        todo = []
        for e in entries.values():
            if e['file'] != fname or e['id'] not in new:
                continue
            if fname == 'game':
                txt = escape(new[e['id']])
            else:
                txt = new[e['id']].replace("'", "\\'")
            if txt == e['orig']:
                continue
            if src[e['start']:e['end']] != e['orig']:
                sys.exit('%s has changed since the export (%s); export again first' % (e['id'], fname))
            todo.append((e['start'], e['end'], txt))
        for a, b, txt in sorted(todo, reverse=True):
            src = src[:a] + txt + src[b:]
        if todo:
            open(path, 'w', encoding='utf-8').write(src)
            changed += len(todo)
            print('%s: %d lines changed' % (os.path.basename(path), len(todo)))
    missing = [i for i in entries if i not in new]
    if missing:
        print('not in the file (left as they were):', ' '.join(missing[:20]), '...' if len(missing) > 20 else '')
    print('%d lines changed in all' % changed)
    if changed:
        export()


if __name__ == '__main__':
    if sys.argv[1:2] == ['import']:
        import_(*sys.argv[2:3])
    else:
        export()
