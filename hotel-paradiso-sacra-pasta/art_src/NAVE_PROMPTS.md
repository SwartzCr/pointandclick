# The Nave: prompts for every scene and sprite

Copy-paste prompts for Nano Banana (Google AI Studio) for everything the Nave needs. The prompts
match the game as it is now: the tapestry has replaced the wardrobe, the village gets dug up, and
Chuk opens the puzzle box himself.

## How to use these

1. **Attach the current room** (`assets/rooms/nave_bg0.png`, or your last generated background) to
   every prompt as a reference image, so colours, lighting and outlines match.
2. **Start every prompt with the style line**, then paste the piece's prompt.
3. **Separate pieces go on flat magenta (#FF00FF)**, one thing per image, seen from the same angle
   as in the room. I cut out the magenta, shrink each piece to its slot and place it.
4. **Size.** The room is 640×288 in the game; generate it larger (e.g. 1280×576 or 1920×864, about
   20:9). For pieces, the size in the game is given; any size works as long as the shape (the aspect
   ratio) matches, with the thing filling the frame.
5. **No changing words.** Fixed signs can be painted in. If lettering comes out garbled, ask for
   the sign blank and I'll letter it. The ultraviolet versions, the glowing writing, the
   pressed-in buttons and the window words are made by me; don't generate them.
6. **PNG if you can, JPEG is fine.** A state change of the same thing (for example the tapestry
   ruined) works best as an edit of the first image: attach it and ask for only that change.

**Style line** (paste first):

```
Hand-painted background art for a 1990s point-and-click adventure game, in the style of early-90s VGA adventure games like Day of the Tentacle and Sam & Max. Bold dark outlines, chunky shapes, a slightly crooked cartoon perspective, warm lamplight, rich texture. Match the colours, lighting and line style of the attached reference image exactly.
```

---

## 1. The background

Everything that never changes, with the changing pieces left out or in their plain starting state.

```
The interior of a converted hotel room turned into a quirky shrine-museum to pasta, seen from the front at a slight height, looking at the back wall. Wide 20:9 frame. No people.

Dark wooden ceiling beams slope down to both sides. Two green enamel lamps hang on long cords at about one third and two thirds across, casting warm pools of light. Cream wallpaper with faint stripes and a tiny fork motif, above dark wood wainscoting. Worn orange-brown floorboards, with cool blue-green light on the floor from a stained-glass window in the middle. The lower middle of the floor is open, so people can walk across the room in front of the back wall.

Left to right:
- Top left: a gold-framed portrait of a face taking its very first bite of spaghetti, eyes closed in bliss.
- Left wall: a wooden door with a small brass plate reading "913" and a round brass knob.
- Back wall: a wooden board labelled "WEIRD SAUCE" holding three tall glass sauce dispensers, red, green and yellow, with copper pipes running into one chrome spout above a small white bowl.
- Front left: a long wooden table covered in real green grass sod, with a tiny model world on a raised tray: small green hills, a winding red river of marinara, a tiny white temple and dozens of tiny white houses. An old black telephone and a small empty wooden leaflet holder stand at its back right corner.
- Back wall: a gold-framed painting of a glowing golden meatball like a sun, rays all round, on deep purple. Next to it, an empty gold picture frame (a separate painting goes in it).
- Under the paintings: a small wall shelf of crocheted pasta shapes in yarn, and below it a small wooden side table, its top empty (a puzzle box goes on it).
- Centre: a tall arched stained-glass window showing a friendly flying creature made of spaghetti with two meatballs and two eyes on stalks, against a blue patchwork sky. In front of it, a white plinth labelled "SPAGHETTI" topped by a twisting tower of spaghetti with meatballs and two eyes on noodle stalks.
- Right of centre, on the back wall: a wooden board labelled "TIMELINE" with four empty square frames in a row and an arrow underneath from "OLDEST" to "NEWEST". Below it, a long low wooden cabinet with four small blank pale windows in a row, and a small plaque reading "PARAGRAPH".
- Right wall: a round-topped archway, open, with a dark stairway going down and purple light coming up from below. A patch of plaster around it has crumbled.
- Front right: a brass balance scale on a small wooden table, one pan heaped with golden elbow macaroni, the other empty.
- Far right edge: plain wallpapered wall and wainscoting, with nothing on it (a tapestry hangs there, made separately).
```

---

## 2. Pieces that change (each on flat magenta #FF00FF)

### 2.1 The tapestry (replaces the wardrobe)

At the right edge of the room, on the right wall, seen at an angle. About 46×190 in the game: tall
and narrow (about 1:4).

**Intact** (the start):
```
On a flat magenta (#FF00FF) background, nothing else in the image: a tall, narrow woven wall tapestry hanging from a wooden rod with knobbed ends, seen at a slight angle as if hanging on a right-hand side wall. Deep red cloth with a woven gold border and a gold fringe along the bottom. Woven in gold in the middle: the Flying Spaghetti Monster, a friendly tangle of noodles with two brown meatballs and two eyes on stalks. Below it, the woven words "R'AMEN". One loose gold thread hangs down from the bottom hem, clearly visible. Old and a little faded, but whole. Tall and narrow, about 1:4.
```

**Ruined** (after you pull the thread): attach the intact image and ask:
```
Edit this image: the loose thread has been pulled out, unravelling the tapestry. A long ragged gap now runs up the middle from the bottom hem to just below the meatballs, with the weave pulled apart and loose red and gold threads dangling from both sides. Most of the noodles are gone; the eyes and meatballs are still there at the top. The gap is see-through: fill it with flat magenta (#FF00FF). Keep everything else the same: the rod, the border, the angle and the size.
```

### 2.2 The tiny village, dug up

On the sod table's tray (95–190, 164–200). About 95×36: wide and shallow (about 8:3).

**Intact:** painted into the background.

**Ruined** (after the tiny folk dig for the whip-it):
```
On a flat magenta (#FF00FF) background: the top of a small model landscape on a raised wooden tray covered in green sod, seen from the front at a slight height, the same tray as on the sod table in the reference. The tiny village on it has been completely dug up: small holes everywhere with heaps of brown earth beside them, tiny white houses knocked onto their sides with their red roofs fallen off, the little white temple leaning badly, and the red marinara river spilled into the holes. A few tiny villagers sit proudly in the rubble. Wide and shallow, about 8:3.
```

### 2.3 The archway panel

It fills the archway on the right wall (about 43×117 inside the arch): tall, narrow, round-topped.

**Closed** (the start; fades away when you're ordained):
```
On a flat magenta (#FF00FF) background: a round-topped plaster panel shaped exactly to fill a narrow stone archway, the same colour and texture as the wall's plaster, so it looks like a blank wall. A few faint cracks. Tall and narrow, about 3:8.
```

### 2.4 The puzzle box (Chuk's reliquary)

On the small side table under the paintings (232–280, 138–190). About 48×52, almost square.

**Shut** (the start):
```
On a flat magenta (#FF00FF) background: a small ornate wooden box on its own, seen from the front at a slight height. Three brass buttons on its lid, each shaped like a pasta: a penne tube on the left, a farfalle bow in the middle and a scallop shell on the right. A tiny brass plate on the front. Almost square.
```

**Open** (after Chuk opens it): attach the shut image and ask:
```
Edit this image: the lid is now tipped open and back, showing a velvet-lined inside, deep red, empty. The three pasta buttons are on the lid, so they tip back with it. Keep the same size and angle.
```

**The golden rigatone** (sits in the open box; also the inventory icon). About 16×10:
```
On a flat magenta (#FF00FF) background: a single rigatone pasta tube made of shining gold, with ridges along it, lying on its side. Wide, about 3:2.
```

**Sauced rigatone** (inventory icon only): attach the rigatone and ask:
```
Edit this image: the same golden rigatone, now dripping with a messy red-and-green sauce.
```

### 2.5 The Timeline tiles, drawer and pendant

The board on the back wall. Each tile is about 18×19, almost square.

**The four tiles** (generate as one row on magenta; I'll cut them apart):
```
On a flat magenta (#FF00FF) background: four small square wooden picture tiles in a row with gaps between them, each painted with a simple bold icon: 1) a steaming bowl of noodles, 2) a dinner fork, 3) a loose twist of string, 4) an old bone carved with tally marks. Unlit, warm wood.
```

**Tiles lit** (optional): attach the row and ask:
```
Edit this image: the same four tiles now glowing warm gold, as if lit from behind.
```

**The drawer, open** (pulled out under the board; 435–465, 136–152; about 30×16, 2:1):
```
On a flat magenta (#FF00FF) background: a small shallow wooden drawer pulled out towards us, seen from slightly above, with a brass handle on its front. Empty inside. Wide, about 2:1.
```

**The UV pendant** (lies in the drawer; also the inventory icon; about 18×8 in the drawer):
```
On a flat magenta (#FF00FF) background: a small violet crystal pendant on a fine silver chain, glowing faintly purple, lying flat with the chain curled beside it.
```

### 2.6 The Paragraph Spinner windows

Four small windows on the cabinet under the Timeline, each about 20×24. I write the words, so
only the blank window is needed.

```
On a flat magenta (#FF00FF) background: one small upright window from a wooden slot-machine-style cabinet: a pale cream panel behind glass in a brass frame, blank, with nothing written on it. Slightly taller than wide, about 5:6.
```

### 2.7 The Spinning Fork painting

In the empty gold frame on the back wall (240–277, 86–138), about 37×52, portrait.

```
On a flat magenta (#FF00FF) background: a gold-framed painting of a silver fork twirling a swirl of spaghetti against a dark blue swirling background. Portrait, about 5:7.
```

Animation: attach that image and ask for the inside turned on by an eighth of a turn each time,
seven times (8 frames in all), keeping the frame identical:
```
Edit this image: keep the gold frame exactly the same. Rotate the fork and the spaghetti swirl inside the painting by one eighth of a turn clockwise.
```

### 2.8 The pamphlets

In the leaflet holder on the sod table (195–210, 153–170), about 15×17.

```
On a flat magenta (#FF00FF) background: a small stack of folded cream paper leaflets standing upright, the front one titled "Spaghetti Theory" in red. Slightly taller than wide.
```

### 2.9 The pasta rosary beads (inventory icon)

The beads are made from the string and the macaroni, so they only appear in your inventory and on
the bellhop.

```
On a flat magenta (#FF00FF) background: a loop of dried elbow macaroni threaded on a gold string like rosary beads, with a bigger macaroni medallion hanging at the bottom, hanging straight down.
```

### 2.10 Inventory icons still needed

Each one on its own on magenta, filling the frame (shown at about 60×36):

```
On a flat magenta (#FF00FF) background: a small steel whipped-cream charger canister (a "whip-it"), silver, lying on its side, a little bit of earth stuck to it.
```
```
On a flat magenta (#FF00FF) background: a long loose gold thread, coiled in a loop, with a frayed end.
```
```
On a flat magenta (#FF00FF) background: a folded cream leaflet titled "Spaghetti Theory" in red.
```

---

## 3. What I make myself (don't generate)

- The ultraviolet look of the room and every piece, and the glowing writing ("SAUCE THY
  OFFERING", "THE WORD IS SPUN", "FIRST CAME THE STRING", "SPIN UNTIL IT GLOWS", "NOT A WALL",
  "THE KEEPER KNOWS").
- The words in the Paragraph Spinner windows, and the pressed-in buttons.
- Chuk and the bellhop: they have their own sprite sheets.
