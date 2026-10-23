# Hotel Paradiso, Room 714

A one-room point-and-click adventure built natively for the SCUMM v6 engine with
[ScummGEN](https://github.com/sronsse/scummgen). It runs in ScummVM like a LucasArts game.

You wake up in Room 714 long after check-out. The door only opens with your key card,
and you have no idea where you put it.

## Play it

1. Put `tentacle.000` and `tentacle.001` (from `game/`) in a folder.
2. In ScummVM: **Add Game...**, pick that folder, and confirm.

ScummVM has no generic "SCUMM v6" entry, so the files are named like Day of the Tentacle's
to load the v6 engine. ScummVM will say the version is unknown; that's expected.

Controls: pick a verb, then click an object. Right-click an object to look at it.
To use an inventory item on something, click **Use**, the item, then the object.

## The room (10 interactable objects)

door, TV, curtains, minibar, lamp, phone, nightstand, painting, wall safe, bed

Each one has its own SCUMM verb script and responds to the verbs that make sense for it;
the rest get a generic reply.

<details><summary>Walkthrough (spoilers)</summary>

1. Open the nightstand, pick up the matchbook.
2. Look at the matchbook: too dark. Use the lamp, then look again: the code is 714.
3. Pull the painting to reveal the wall safe. (The phone hints at this too.)
4. Open the safe, pick up the key card.
5. Use the key card with the door.

</details>

## Source layout

| Path | What it is |
|---|---|
| `source/scripts/main.sgc` | Global script: boot, verb bar, sentence line, input handler, inventory, default replies |
| `source/scripts/hotel.sgc` | Room script: entry, all 10 object verb tables, phone call, ending |
| `source/art.py` | Procedural pixel art: room in every object state, player costume frames, cursor |
| `source/gen.py` | Writes the ScummGEN game folder (XML, 8-bit BMPs, walkboxes, charset, costume) |
| `source/build.sh` | Regenerates the folder and runs `scummgen` |
| `source/game/` | The generated ScummGEN input folder, ready to compile as-is |
| `scummgen-fixes.patch` | Two fixes ScummGEN needs on a modern compiler / to run in ScummVM |

## Rebuilding

```
# ScummGEN needs flex, bison, autotools and libxml2-dev
git clone https://github.com/sronsse/scummgen && cd scummgen
git apply ../scummgen-fixes.patch
autoreconf -fi && ./configure && make
cd ../source && ./build.sh        # writes build/out/tentacle.000 and .001
```

`build.sh` looks for scummgen at `$HOME/src/scummgen/src/scummgen`; set `SCUMMGEN=/path/to/scummgen` to override. ScummGEN must be run from its build tree because it loads its `libscumm/` folder next to the binary.

### About the ScummGEN patch

* `Map.hpp`: `Box::setID` was declared as returning a value but never did. Modern GCC treats
  that as undefined behaviour and the tool segfaults while preparing walkboxes.
* `DOBJ.cpp`: room objects were written to the index with owner 0. The engine expects owner 15
  ("owned by the room"); without it ScummVM can't find object code, names or images.
