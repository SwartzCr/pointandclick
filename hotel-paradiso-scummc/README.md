# Hotel Paradiso, Room 714

A one-room point-and-click adventure written in [ScummC](https://github.com/AlbanBedel/scummc)
and compiled to SCUMM v6 bytecode, the engine behind *Day of the Tentacle*. It runs in ScummVM.

You wake up in Room 714 long after check-out. The door only opens with your key card,
and you have no idea where you put it.

## Play

Prebuilt game files are in `dist/`. In ScummVM choose **Add Game...**, select the `dist/`
folder and start it.

ScummVM has no generic "SCUMM v6" entry, so the files are named and encrypted like
*Day of the Tentacle*'s to load the v6 engine. ScummVM reports the version as unknown;
that's expected.

**Controls:** click a verb, then an object. Right-click an object to look at it.
To use an inventory item on something, click **Use**, the item, then the object.
F5 opens the menu, `.` skips a line of dialogue.

## The room

Ten pieces of furniture you can interact with: door, TV, curtains, minibar, lamp, phone,
nightstand, painting, wall safe and bed. The three things you can take (candy bar,
matchbook, key card) are objects of their own, clickable only while you can see them.
Each object has its own verb code and answers the verbs that make sense for it; anything
else gets a stock reply.

<details><summary>Walkthrough (spoilers)</summary>

1. Open the nightstand and pick up the matchbook inside.
2. Look at the matchbook: too dark. Use the lamp, then look again. The code is 714.
3. Pull the painting to reveal the wall safe. Calling the front desk hints at this too.
4. Open the safe and pick up the key card.
5. Use the key card with the door.

</details>

## Source layout

| Path | Contents |
|---|---|
| `src/hotel.sch` | Shared declarations: verbs, actor, global variables, colour constants |
| `src/interface.scc` | `ResRoom`: boot (`main`), verb bar, live sentence line, input handler, sentence handler, stock replies, text inventory |
| `src/hotel.scc` | `Hotel`: the room, its objects and their verb code, the phone call, the ending |
| `assets/` | Generated art and data the sources reference (committed, so Python isn't needed to build) |
| `tools/art.py` | Procedural pixel art: the room in every object state, costume frames, cursor |
| `tools/make_assets.py` | Writes `assets/`: one shared 256-colour palette, object state images, costume + `.scost`, font sheet, walk boxes |
| `dist/` | Prebuilt `tentacle.000` / `tentacle.001` |

## How it works

* **Interface.** `mouseWatch` runs every frame and rebuilds the sentence line with SCUMM's
  string codes (`%v{curVerb} %n{hoverObj}`), which the engine expands when it draws the verb.
* **Actions.** A room click queues `doSentence(verb, object, 0, item)`. The engine then runs
  `sentenceHandler`, which walks the player over and starts the object's own verb code if it
  has an entry for that verb, or `defaultAction` if not. The inventory item rides along as
  `objB`, so objects can tell "Use" from "Use key card with".
* **State.** Opening things, the lamp, the TV and the safe are object states with their own
  images. The candy bar, matchbook and key card are drawn as part of their container's
  "open" image, but they're separate objects with `parent` and `parent_state` set, so the
  engine only lets the cursor find them while the container is in the state that shows
  them. Each is declared before its container so the cursor finds the item first. The safe sits on the same spot as the painting and starts "untouchable" (engine
  class 32); moving the painting swaps which of the two the cursor finds.
* **Palette.** v6 rooms share one 256-colour palette between background, objects and
  costumes. Indices 0..15 hold the EGA colours used for text and verbs; the art is packed
  in after them, and the costume's 16 local colours are mapped onto room indices with
  `palette(...)` in `guest.scost`.

## Building

You need ScummC built from source, plus GNU make. Python 3 with Pillow is only needed to
regenerate `assets/`.

```
git clone https://github.com/AlbanBedel/scummc ~/scummc
cd ~/scummc && ./configure --disable-gtk --disable-sdl --release && make

cd hotel-paradiso-scummc
make SCUMMC=~/scummc/build.vm/<your-target>     # writes build/tentacle.000 and .001
make assets                                      # optional: regenerate assets/
```

`SCUMMC` must point at the directory containing `scc`, `sld`, `cost` and `char`.

**If ScummC's build fails with "No rule to make target 'scc_help.h'"**: it generates
help text with `xsltproc` from `man/*.xml`, but the XML lives in `man/tools/`. Install
`xsltproc` and symlink the files up a level:

```
cd ~/scummc && for f in man/tools/*.xml; do ln -sf tools/$(basename $f) man/; done
```

## ScummC notes

Things that weren't obvious from the docs, in case you extend this:

* The preprocessor only supports plain `#define NAME value`, not macros with arguments.
* Declare forward-referenced objects one per line (`object door;`), and define scripts
  before the objects that call them.
* `cost` files only accept `/* */` comments, and `palette()` takes a comma-separated list
  (brackets are only for ranges like `[16-31]`).
* `actorPrintCenter()` clears the overhead flag, so call it before `actorPrintOverhead()`.
* `print*` calls share state with talk text; don't end a one-off caption with `printEnd()`,
  or it becomes the new default for dialogue.
