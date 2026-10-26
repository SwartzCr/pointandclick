# Hotel Paradiso, Room 714

A one-room point-and-click adventure written in [ScummC](https://github.com/AlbanBedel/scummc)
and compiled to SCUMM v6 bytecode, the engine behind *Day of the Tentacle*. It runs in ScummVM.

You wake up in Room 714 at nine at night, and the big party up on the ninth floor is
tonight. You're in no state to go: you won't leave the room until you've eaten something,
you're in costume, and you've pre-gamed.

## Play

**In a browser:** https://swartzcr.github.io/pointandclick/ (click **Play**). Every push to
`main` rebuilds it: `.github/workflows/pages.yml` compiles ScummVM's WebAssembly port
(SCUMM engine only, at a pinned commit) on GitHub's runners and adds the game files from
`dist/` and the landing page in `web/`. It checks the result in headless Chromium and
publishes it to GitHub Pages. Saved games stay in your browser's storage. Browsers only
allow sound after you've clicked on the page.

**In ScummVM:** prebuilt game files are in `dist/`. In ScummVM choose **Add Game...**, select the `dist/`
folder and start it.

ScummVM has no generic "SCUMM v6" entry, so the files are named and encrypted like
*Day of the Tentacle*'s to load the v6 engine. ScummVM reports the version as unknown;
that's expected.

The game opens on a title screen: click **New game** (or press `n`) to start, or **Quit**.
Finishing the game, or losing it, brings you back to it.

**Controls:** click a verb, then an object. Or just click an object without picking a
verb, and you'll do the obvious thing with it: open (or close) doors, drawers, the minibar
and the safe, pick items up, use the phone, lamp, TV and toilet, pull the painting. With
no verb chosen, the sentence line shows what a click will do ("Open minibar", "Pick up
candy bar"), and just the item's name over the inventory.
Right-click an object to look at it.
To use an inventory item on something, click **Use**, the item, then the object.
To eat the candy, just **Use** it. To use another item on yourself (put on the
uniform), click **Use**, the item, then either yourself or the item again.
F5 opens the menu, `.` skips a line of dialogue.

## The rooms

**Room 714.** Twelve pieces of furniture you can interact with: door, TV, dresser,
curtains, minibar, lamp, phone, nightstand, painting, wall safe, bed and coffee table.
The things you can take (candy bar, matchbook, bellhop uniform, and the screwdriver and
little bag of powder in the safe) are objects of their own, clickable only while you can
see them. Your wallet is hidden under the bed covers.

There's a bellhop uniform folded in the dresser's top drawer. Take it and use it on
yourself to put it on: the player switches to a second costume with its own full set of walking and
talking frames. **Use** it again to take it off. It's a costume party, so you need it on
to leave.

The coffee table can't be picked up, but three things can be put down on it ("Use matches
with coffee table") and picked back up later: the matchbook and the candy bar at either end,
and the cabinet mirror across the middle. It's where the pre-game happens: the mirror goes
on the table, the powder goes on the mirror, the razor
chops it into three lines, and the rolled-up dollar bill from your wallet does one. The
wallet is hidden under the bed covers; picking it up gets you the dollar.

**The bathroom**, through the doorway on the left wall: a tub with a shower curtain that
opens and closes, a bath mat, a toilet that flushes (animated, with a sound), a sink, a
mirror that opens into a medicine cabinet with a shaving kit inside, a towel and a bar of
soap. The towel, soap and shaving kit can be taken, and the screwdriver takes the mirror
door off the cabinet. Walk through the doorway on the right
to go back.

The inventory holds up to ten items in two columns of five, so it uses short labels
("matches", "razor" for the shaving kit, "driver" for the screwdriver); the objects in the rooms keep their
full names.

Each object has its own verb code and answers the verbs that make sense for it; anything
else gets a stock reply.

<details><summary>Walkthrough (spoilers)</summary>

The door tells you what's missing, and so does the front desk on the phone.

1. **Eat.** Open the minibar, take the candy bar, and use it.
2. **Get in costume.** Open the dresser, take the bellhop uniform, and use it on yourself.
3. **Pre-game.**
   1. Open the nightstand and take the matchbook. Turn on the lamp and look at the
      matchbook: the safe code is 714.
   2. Pull the painting to reveal the wall safe, open it, and take the screwdriver and the
      little bag of powder.
   3. In the bathroom, use the screwdriver with the mirror to take the mirror door off.
   4. Back in the bedroom, use the mirror with the coffee table, the powder with the
      mirror, and the razor (from the medicine cabinet) with the powder.
   5. Open the bed to pull back the covers and pick up your wallet; you take the dollar
      bill out of it straight away.
   6. Use the dollar bill with the three lines. One is enough. A second turns the room
      psychedelic (you can still go to the party); a third sends you to bed instead, and
      that's game over.
4. Open the door. Or, once you're ready, call the front desk instead: Gustav sends up
   "room service", and three clowns carry you to the party.

</details>

## Source layout

| Path | Contents |
|---|---|
| `src/hotel.sch` | Shared declarations: verbs, actor, global variables, colour constants |
| `src/interface.scc` | `ResRoom`: boot (`main`), verb bar, live sentence line, input handler, sentence handler, stock replies, text inventory |
| `src/hotel.scc` | `Hotel`: Room 714, its objects and their verb code, the phone call, the ending |
| `src/bathroom.scc` | `Bathroom`: the bathroom, its objects, the flush animation |
| `src/title.scc` | `Title`: the title screen (its menu lives in `interface.scc`) |
| `src/gameover.scc` | `GameOver`: the screen after the third line |
| `assets/` | Generated art and data the sources reference (committed, so Python isn't needed to build) |
| `tools/art.py` | Procedural pixel art: the rooms in every object state, the title screen, costume frames, cursor |
| `tools/make_assets.py` | Writes `assets/`: one shared 256-colour palette, both room backgrounds, object state images, both costumes + `.scost` files, font sheet, walk boxes, every sound effect and both pieces of music |
| `dist/` | Prebuilt `tentacle.000` / `tentacle.001` |
| `web/` | The browser version's landing page, `compat.js` (browser fixes loaded before ScummVM) and the Chromium/Firefox smoke test (built by `.github/workflows/pages.yml`) |

## How it works

* **Title screen.** `main` sets up the verbs, hides the verb bar, shows the two menu
  verbs and goes to the `Title` room; while `titleMode` is set the input handler only
  listens to the menu. **New game** swaps the menu for the verb bar and starts the
  bedroom. The ending calls `restartGame()`, which has the engine reset every variable,
  bit, object state and the inventory and run `main` again, so each new game starts clean.
* **Room service.** Calling the desk once you're ready runs `clownService`: three clown
  actors (`clown1`..`clown3.scost`, one suit colour each, sharing one animation set) walk
  in through the door. They switch to `carryWalk`/`carryStand`, with their arms up. The
  player gets the `carried` animation (a 52x14 lying-down picture, in both outfits) for
  walking, standing and talking, plus `setActorElevation()` to lift them to the clowns'
  hands. Everyone walks out of the door and the normal ending plays.
* **Too many lines.** The second line starts `tripColors`, a global script that keeps
  calling `setRoomRGBIntensity()` with a new red/green/blue scale every 9 frames. Scales
  above 255 brighten a channel, so the room flips between lurid tints. It only touches
  palette entries 16..255, so the EGA text and verb colours stay put, and because it's
  global it keeps going in the bathroom (a room change reloads the palette, and the next
  tick tints it again). The third line walks you to the bed and goes to the `GameOver`
  room, which shows a few captions and then calls `restartGame()`, like the ending. The
  bedroom spins behind the bed there: `tools/art.py` renders eight full-screen frames,
  the room enlarged and rotated 45 degrees further each time (nearest-neighbour, so no new
  colours), dimmed with a dither, with stars orbiting the guest's head. Frame 0 is the
  background and the other seven are states of a full-screen `spinner` object, which a
  loop steps through every 6 ticks.
* **Default action.** Each object has code for a hidden verb, `DefaultVerb`, that just
  sets `defaultVerb` to what a plain click should do (`Open`, `PickUp`, `Use`...). Things
  that open and close answer `isOpen ? Close : Open`. `queryDefault` runs that code with
  `startObject()`, which the engine executes immediately. It uses the "recursive" flag so
  it doesn't stop a script the object is already running. `mouseWatch` asks every frame
  and shows "%v{defaultVerb} %n{hoverObj}". A click asks again and sends that verb with
  `doSentence()`.
* **Interface.** `mouseWatch` runs every frame and rebuilds the sentence line with SCUMM's
  string codes (`%v{curVerb} %n{hoverObj}`), which the engine expands when it draws the verb.
* **Actions.** A room click queues `doSentence(verb, object, 0, item)`. The engine then runs
  `sentenceHandler`, which walks the player over and starts the object's own verb code if it
  has an entry for that verb, or `defaultAction` if not. The inventory item is handed to the
  object as `objB`, so objects can tell "Use" from "Use razor with". It travels in a global,
  `sentenceItem`, rather than as the sentence's second object, because the engine silently
  drops a sentence whose two objects have the same number. Inventory items are verbs,
  numbered separately from room objects, so they can collide: the screwdriver's number is
  the bathroom mirror's.
* **State.** Opening things, the lamp, the TV and the safe are object states with their own
  images. The candy bar, matchbook, uniform and wallet are drawn as part of their container's
  "open" image, but they're separate objects with `parent` and `parent_state` set, so the
  engine only lets the cursor find them while the container is in the state that shows
  them. Each is declared before its container so the cursor finds the item first. The
  screwdriver and the bag in the safe (and the shaving kit, which shows both with the
  cabinet door open and with it unscrewed) can't use `parent_state`, which names just one
  state: the safe has an open image for each combination of what's left inside, and a
  script switches each item between clickable and untouchable to match. The safe sits on the same spot as the painting and starts "untouchable" (engine
  class 32); moving the painting swaps which of the two the cursor finds.
* **Coffee table.** The table is a hole in the walk boxes, with a margin of half a sprite
  width on each side, so the player is never drawn over it while standing behind its
  front edge (SCUMM has no depth sorting between actors and the background without
  z-plane masks). Each of the three items has a slot object on the table top (16 pixels
  wide at the ends, 64 for the mirror in the middle); it starts untouchable and is shown
  and made clickable when the item is set down. The mirror's slot has four images: bare,
  with the powder, three lines, two lines.
* **Costume swap.** `guest.scost` (bathrobe) and `bellhop.scost` (uniform) are drawn by the
  same code in `tools/art.py` with a different outfit, and declare the same animations
  (`init`, `walk`, `stand`, `talkStart`, `talkStop`). That lets `wearUniform` call
  `setActorCostume()` on the player at any time: the actor keeps its walk and talk frame
  numbers and just draws them from the other costume. Both are loaded and locked at boot.
* **Two rooms.** Each room is its own `room` block with its own background and walk
  boxes. The doorways handle **Walk to** themselves (the input handler runs an object's
  WalkTo code if it has any), and call `startRoom()`. Object states and classes are global
  in SCUMM, so each room's `entry()` only places the player at the right doorway; Room
  714's first-visit setup and intro run once.
* **Sounds.** `tools/make_assets.py` synthesizes every sound effect in plain Python and
  writes 8-bit PCM `.voc` files, which ScummC's `soun` tool wraps into SOUN resources:
  the toilet flush (the toilet alternates between two object states while it plays), two
  seconds of indistinct TV chatter when the TV is switched on (with the weather report
  shown on screen), and the safe opening, as an electronic hotel safe (three keypad beeps, an
  "accepted" chime, the motor pulling the bolt back, and a puff of air as the door
  springs open, with the door's image switching at that moment). Opening things has
  sounds too: the minibar's latch and seal, a wooden drawer sliding out (nightstand and
  dresser), the medicine cabinet's magnet catch and hinge creak, and the bed covers
  rustling.
* **Music.** The same file has a tiny synthesiser (vibraphone, electric piano, plucked
  bass, band-organ pipes, glockenspiel, tuba and a few drums). It plays two original pieces, also stored as
  sound effects. The title screen has a lounge tune in F, which `loopTheme` restarts
  whenever it ends; the room's `exit()` stops it when a game starts. The clowns get a
  merry-go-round waltz, in the style of a fairground band organ, that loops from the knock
  at the door until they carry you out. The game-over screen loops a woozy but
  cheerful 12 seconds: a warm open-fifth drone with a gentle pulse, and a D major music
  box that tumbles down and bounces back up with a tipsy wobble. A whoosh circles every
  0.8s, in time with the spinning room.
* **Palette.** v6 rooms share one 256-colour palette between background, objects and
  costumes. Indices 0..15 hold the EGA colours used for text and verbs; the art is packed
  in after them, and the costume's 16 local colours are mapped onto room indices with
  `palette(...)` in `guest.scost`. Both rooms are given the same palette, so the
  costumes need only one mapping.

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
