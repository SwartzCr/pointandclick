# Hotel Paradiso: Sacra Pasta

A two-room point-and-click sequel to *Hotel Paradiso, Room 714*, made as an
[Adventure Game Studio](https://www.adventuregamestudio.co.uk/) 3.6.1 game at 640×400. It
runs in ScummVM (2.9 or newer), where it was tested, and should also run in the AGS 3.6.1 engine.

The clowns finally carried you up to the party on the ninth floor. Room 913 has been
turned into **the Nave**, a workshop of string, noodles and old inventions, kept by
Chuk, Keeper of the Archway, who wears a colander. The real party is in **the Crypt**
behind the wall: an arcade, a crocheted Flying Spaghetti Monster, and a Pope Seat that
nobody has sat in all night. Dinner is served when the Pope decrees it. There is no Pope.

## Play

**In ScummVM:** choose **Add Game...**, pick the `dist/` folder and start
*Unknown AGS game (sacrapasta.ags)*. ScummVM asks you to report it as an unknown game;
that's expected for a new game.

**In AGS:** run `dist/sacrapasta.ags` with the AGS 3.6.1 engine (`ags sacrapasta.ags`).

**Controls:** the LucasArts 3×3 verb grid. Click a verb, then a thing. Or just click a
thing and the obvious verb happens; the sentence line says which, and that verb lights
up. Right-click anything (or an inventory item) to look at it. To use an item on
something, click it (that picks **Use**), then the thing. To wear an item, click it and
then click yourself; it leaves your pockets while you wear it, and **Pick up** on yourself
takes it off again. Clicking a pamphlet twice reads it. Keys: O, C, T, P, L, U, W, S
(push), Y (pull) pick verbs, Esc cancels, F5/F7 save and load.

## The rooms

**The Nave** (room 913). A tapestry, a sod table you can play God on (with an old
handset playing audio stories and a pamphlet of Spaghetti Theory), the Weird Sauce
wall piece, the paintings *Glutenous Truth*, *First Taste* and the *Spinning Fork*
(which spins), a crocheted pasta display, a stained-glass painted flat, the Timeline
of Ancient Technology, the Sacred Topology display, the spaghetti sculpture, the
Paragraph Spinner, the Scales of Pasta, a puzzle box, and a wall that isn't one.

**The Crypt.** The CONFESS 3Button cabinet, the Classic Computer, the Trackball
cabinet (the ball is a meatball), the Rex Seat with its T. rex game, the Pasta
Identification wall, the yarn monster, the curtained staff area, and the Pope Seat with
its crank and lasagna hat.

**The UV pendant** is the game's trick: wearing it bathes either room in ultraviolet
and shows writing that isn't there otherwise. Some of it is decoration, some of it is
the answer.

<details><summary>Walkthrough (spoilers)</summary>

1. Talk to Chuk. To be ordained you need to **wear the beads**, **speak the Word** and
   **bring a sauced golden offering**. If you're stuck, tell him so: he gives a nudge
   for the next step.
2. **Beads:** pull the loose thread on the tapestry (which ruins it). Use the
   string on the Scales of Pasta to thread its elbow macaroni into rosary beads, and
   use them on yourself.
3. Pick up the pamphlet from the sod table and read it: string came first, then
   counting, then noodles, then the fork; the Word shows itself under UV light.
4. **Timeline:** press the tiles oldest first: string, counting (the tally bone),
   noodles, fork. A drawer opens; take the UV pendant and put it on.
5. **The Word:** under UV, pull the lever by each window of the Paragraph Spinner
   until its word glows: ALL PASTA IS HOLY.
6. **The telephone:** pick it up a few times to hear its three stories: the Creation,
   the First Supper (the sauce recipe) and the Prophecy of the Tiny Folk.
7. **A whip-it:** use the sod table to play God and show the tiny folk the prophecy's
   signs in order: raise a mountain, part the marinara river, then (wearing the
   pendant) make a purple star shine. They're yours to command: you send them digging,
   and they bring you a whip-it canister, digging up their whole village to find it.
8. **The puzzle box:** it's Chuk's, and he won't let you touch its buttons. Try, and he
   asks for a whip-it. Give him the canister and he says "Oh fine, I'll do it myself",
   walks over and opens it. Take the golden rigatone.
9. **The sauce:** the First Supper says a pump of red for each of the Noodly One's eyes
   (two), green for each of his noses (none) and one yellow. Push the red dispenser
   twice and the yellow once, then use the rigatone on the bowl. (Chuk tastes a wrong
   mix, says what's off, licks it clean and gives it back.)
   Then talk to Chuk, say "ALL PASTA IS HOLY", and give him the sauced rigatone.
   The wall opens and he goes to play T. rex in the Crypt.
8. In the Crypt, use the Classic Computer; it boots HOTEL.EXE, a tiny Hotel Paradiso,
   with the guest back in his bathrobe in Room 714. Read the newspaper on the floor
   (LOG OFF, top right, or Esc, to leave). Then turn the labels on the
   Pasta Identification wall to FUSILLI, ORECCHIETTE, FARFALLE, RIGATONI. WORTHY lights
   up and Chuk goes to the Pope Seat's crank.
9. Play CONFESS (the 3Button cabinet) and confess three sins from Room 714. Don't
   confess the pineapple. Pick up the token.
10. Put the token in the Pope Seat and sit in it. Chuk cranks the hat down; decree
    "Let there be dinner!"

</details>

## How it's built

There's no AGS editor involved: the AGS editor only runs on Windows, so the game is
compiled from Python. `tools/agsbuild/` writes the AGS 3.6.1 data formats directly,
ported from the AGS sources: the main game data (`game28.dta`, from the editor's
`DataFileWriter.cs`), room files (`room_file.cpp`), the sprite file (`spritefile.cpp`),
WFN bitmap fonts and the CLIB package that makes the `.ags` file. Scripts are compiled
by `agscc`, the command-line AGS script compiler that ships in the AGS source tree.

| Path | Contents |
|---|---|
| `src/game.asc`, `src/game.ash` | The whole game script: the verb interface, the conversation picker, both rooms' puzzles, the intro and the ending |
| `tools/art_people.py` | The guest (in the bellhop uniform from Room 714, with or without the beads and pendant) and Chuk, drawn procedurally |
| `tools/art_rooms.py` | Both rooms, their UV versions, the title screen, and every object, plus the hotspot, walkable and walk-behind masks painted alongside |
| `tools/art_ui.py` | Cursor and inventory icons |
| `tools/sound.py` | All sound effects and the three pieces of music, synthesised with numpy |
| `tools/make_assets.py` | Writes `assets/` (PNG sprites and masks, WAV audio, WFN fonts, `manifest.json`) |
| `tools/build.py` | Numbers sprites and views, generates the script headers, compiles the scripts and writes `dist/sacrapasta.ags` |
| `tools/agsbuild/` | The AGS file-format writers |
| `assets/` | Generated art, audio and fonts (committed, so building doesn't need to regenerate them) |
| `dist/sacrapasta.ags` | The built game |

Some details:

* **The interface** is a single 640×112 overlay below the room. The script redraws it
  into a dynamic sprite only when something changes (the hover target, the verb, the
  inventory). Overlays don't survive a room change, so it's recreated after one.
  Conversations reuse the same strip: `Choose()` draws up to five lines and polls the
  mouse until one is clicked. There are no AGS GUIs or dialog topics at all.
* **Rooms and objects** are addressed by generated constants (`R_NAVE`, `H_NAVE_SAUCE`,
  `O_CRYPT_SEAT`, `S_NAVE_DRUM1_W0`...) in `_Things.ash`, which `build.py` writes from
  the room descriptions, so the art and the script can't disagree about numbering.
  All the puzzle logic is in the global script; room scripts are empty.
* **State.** Every room's object graphics and visibility are rebuilt from script
  variables when the room is entered, so a new game is just resetting the variables.
* **UV light.** Each room has a second background frame with the room desaturated to
  violet and the hidden writing painted in. Wearing the pendant switches to it, tints
  the characters and most objects, and swaps in special UV sprites for the spinner
  drums, the puzzle box buttons and the wall panel.
* **Hi-res pixel art.** Everything is drawn with flat shapes at 1:1 and outlined with a
  one-pixel dark edge; the characters are 48×104. Text uses bitmap fonts rendered from
  DejaVu Sans (Bitstream Vera licence) without antialiasing.
* The status pixel in the bottom-right corner of the interface (almost black) tells an
  automated playtest whether the game is waiting for a click, a conversation choice,
  or busy.

## Building

You need Python 3 with Pillow, numpy and scipy, and the AGS 3.6.1 sources for the script
compiler:

```
git clone -b v3.6.1.30 https://github.com/adventuregamestudio/ags ~/ags
make -C ~/ags/Compiler                      # builds agscc

cd hotel-paradiso-sacra-pasta
make AGS=~/ags                              # writes dist/sacrapasta.ags
make assets                                 # optional: regenerate assets/ (needs the DejaVu fonts)
```
