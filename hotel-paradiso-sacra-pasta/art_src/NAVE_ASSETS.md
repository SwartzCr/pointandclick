# The Nave: art assets

This is everything the Nave needs, written so each piece can be generated on its own and then
composed into the room. `nave_layout.png` (next to this file) shows where each piece goes. The
codes on that picture (F1, A4, …) match the headings below. Positions are in the room's 640×288
pixels; for 1280×576, double them.

## How to generate

- **One style for everything.** Paste the style line below at the start of every prompt, so the
  pieces match.
- **The room first, then the pieces.** Generate the background, then make each separate piece from
  it if your tool allows (img2img, a reference image or inpainting), so the colours and the
  lighting agree.
- **Separate pieces go on flat magenta (#FF00FF).** Draw them straight on, from the same angle as
  in the room, with nothing else in the picture. I cut out the magenta, scale each piece to its
  slot and place it.
- **Size.** Generate the room at 1280×576 or larger (20:9). Pieces can be any size, as long as the
  thing fills the frame and its shape matches the slot (a tall slot needs a tall image).
- **No writing that changes.** Signs that never change ("WEIRD SAUCE", "TIMELINE", "PARAGRAPH",
  "SPAGHETTI", "913") can be painted in, but image tools often garble lettering. If they come out
  wrong, leave them blank and I'll add the words. The words on the barrels and all the ultraviolet
  writing are always added by me.
- **Things I make myself, so don't generate them:** the ultraviolet version of every piece and of
  the room, the pressed buttons, the lit timeline tiles (unless you want a nicer glow; see A5), and
  the barrel words.

**Style line:**

> Hand-painted background art for a 1990s point-and-click adventure game, in the style of early-90s
> VGA adventure games like Day of the Tentacle and Sam & Max. Bold dark outlines, chunky shapes, a
> slightly crooked cartoon perspective, warm lamplight, rich texture, no people.

---

## The background (everything fixed)

> The interior of a converted hotel room turned into a quirky shrine-museum to pasta, seen from the
> front at a slight height, looking at the back wall. Dark wooden ceiling beams slope down to both
> sides. Two green enamel lamps hang on long cords at about one third and two thirds across, and
> cast warm pools of light. The walls are cream wallpaper with faint stripes and a repeating motif
> of tiny forks, above dark wood wainscoting. The floor is worn orange-brown planks, and cool blue
> and green light spills onto it from a stained-glass window in the middle. The lower middle of the
> floor is open, so people can walk across the room in front of the back wall.

Leave these **empty**, because they're separate pieces:
- the **archway** on the right: show it **open**, with a dark stairway going down and purple light
  coming up from below (A1 is the plaster panel that fills it);
- the **pamphlet holder** on the sod table: show it **empty** (A3);
- the **barrel faces** of the Paragraph Spinner: **blank, no words** (A4).

Paint these in their **starting state**, because I cut them out of the background:
- the **wardrobe** shut (A2);
- the **timeline tiles** unlit, with the little drawer under the board **shut** (A5);
- the **puzzle box** shut, with its three buttons up (A6);
- the **Spinning Fork** painting (A8).

### Fixed scenery, left to right

- **F1 "First Taste"** (left wall, top; about 4–51, 45–119). A gold-framed portrait of a face taking
  its very first bite of spaghetti, with eyes closed in bliss.
- **F2 Door 913** (left wall; 66–127, 90–201). A wooden door with a small brass plate reading "913"
  and a round knob. It's the way in, so it should be about one and a quarter times the height of a
  person standing at the back of the room.
- **F3 Weird Sauce** (back wall; 142–206, 78–176). A wooden board labelled "WEIRD SAUCE" holding
  three tall glass sauce dispensers (red, green and yellow). Copper pipes run down from them into
  one chrome spout, which drips into a small white bowl below.
- **F4 "Glutenous Truth"** (back wall; 210–270, 86–134). A gold-framed painting of a glowing golden
  meatball like a sun, rays all round, on deep purple.
- **F5 Crocheted pasta shelf** (under F4; 205–272, 136–157). A small wall shelf of crocheted pasta
  shapes in yarn: a shell, a bow and a rolled noodle.
- **F6 Stained-glass flat** (back wall, centre; 284–361, 39–176). A tall arched window of stained
  glass showing a friendly flying creature made of spaghetti, with two meatballs and two eyes on
  stalks, against a blue patchwork sky with a yellow sun.
- **F7 Spaghetti sculpture** (in front of F6; 292–352, 96–224). A white plinth labelled
  "SPAGHETTI", topped by a tall twisting tower of spaghetti studded with meatballs, with two eyes on
  noodle stalks at the top.
- **F8 Sacred Topology case** (back wall, under the Timeline; 384–503, 140–207). A low wooden
  display case with a glass front holding three knotted noodles: a trefoil knot, an infinity loop
  and a pretzel knot.
- **F9 Sod table** (front left, running off the bottom edge; 0–208, 200–288). A long wooden table
  covered with real green grass sod, with a tiny model world on top: small hills, a winding red
  river of marinara, and dozens of tiny white houses.
- **F10 Telephone** (on the sod table, back right corner; 126–162, 201–231). An old black telephone
  with a handset, used for audio stories.
- **F11 Scales of Pasta** (front right, running off the edges; 505–640, 178–288). A brass balance
  scale on a small wooden table, one pan heaped with golden pasta and the other empty.
- **The pamphlet holder** (on the sod table; about 163–190, 205–222). A small, empty wooden box
  that holds leaflets.

---

## Pieces that change (separate images on magenta)

### A1 The archway panel

Where: it fills the archway on the right wall (537–580, 91–208), 43×117: tall, narrow, round-topped.
- **Closed** (the start): a plaster panel filling the arch exactly, the same colour and texture as
  the arch's stone, so it looks like a blank wall. Generate this.
- **Gone:** when you're ordained it fades out and the background's open stairway shows. Nothing to
  generate.
- **Ultraviolet:** "NOT A WALL" glows on it. I make this.

### A2 The wardrobe

Where: at the right edge, cut off by the frame (589–640, 70–260), 51×190: tall and narrow.
- **Shut** (the start, painted into the background): a tall dark wooden wardrobe or cupboard door,
  seen at an angle on the right wall, with a brass knob.
- **Open:** the same wardrobe with its door swung open towards us, showing a dark inside with a
  clothes rail and two hanging robes, one purple and one gold. The rosary beads (A7) hang inside,
  so leave a gap near the top of the inside. Generate this.

### A3 The pamphlets

Where: standing in the empty holder on the sod table (163–186, 186–208), 23×22.
- **There** (the start): a small stack of folded paper leaflets titled "Spaghetti Theory", cream
  paper with a red title. Generate this.
- **Taken:** hidden; the empty holder in the background shows.

### A4 The Paragraph Spinner

Where: front centre (332–490, 218–288). The spinner is part of the background: four wooden barrels
side by side on a stand, each turning on a horizontal axle with a brass knob, above a plaque
reading "PARAGRAPH".
- **Barrel faces:** blank and pale, with nothing written on them. Each face is about 28 px wide and
  20 px tall at 640×288. I write the words (THE / ALL / NO / SOME, FORKS / SAUCES / NOODLES /
  CHEESES, and so on), and the right ones glow under ultraviolet.
- **Optional:** a separate "turning" image of a single barrel, blurred as if spinning, 30×40 on
  magenta. I'd show it for a moment while a barrel turns.

### A5 The Timeline of Ancient Technology, its drawer and the UV pendant

Where: the board on the back wall (382–498, 76–139). The board is part of the background: a wooden
board labelled "TIMELINE", with four square picture tiles in a row and an arrow underneath running
from "OLDEST" to "NEWEST".
- **The four tiles,** left to right (each about 24×24): a bowl of noodles; a dinner fork; a twist of
  string; a bone carved with tally marks.
- **Tiles unlit** (the start): painted into the background.
- **Tiles lit** (optional): the same four tiles glowing warm gold, as if lit from behind, as one
  image of the row of tiles (110×26, on magenta). If you skip it, I brighten the tiles myself.
- **The drawer, open:** a small wooden drawer pulled out from under the board (424–458, 138–150),
  34×12: a shallow tray with a brass handle, empty inside. Generate this. When it's shut, it's
  just a line under the board in the background.
- **The UV pendant:** a small violet crystal on a fine silver chain, glowing faintly. It lies in the
  open drawer. Generate it on magenta, any size (I shrink it to about 12×12). The same image
  becomes its inventory icon.

### A6 The puzzle box, its buttons and the golden rigatone

Where: on a small round side table, front centre-left (222–291, 232–270). The table is part of the
background.
- **Shut** (the start, painted into the background): a small wooden box with three brass buttons on
  its lid, each shaped like a pasta: a penne tube (left), a farfalle bow (middle) and a shell
  (right).
- **Open:** the same box with its lid tipped back, showing an empty velvet-lined inside. Generate
  this, the same size and angle as the shut box. The buttons are on the lid, so they tip back with
  it.
- **Buttons pressed:** I make these (darker, pushed in by a pixel).
- **The golden rigatone:** a single rigatone made of shining gold, ridged and tube-shaped. It sits
  in the open box. Generate it on magenta (I shrink it to about 16×9). It's also an inventory icon,
  with a second version **covered in red-and-green "Weird Sauce"** for after you sauce it.

### A7 The pasta rosary beads

Where: hanging from the rail inside the open wardrobe (about 609–625, 106–140), 16×34.
- A loop of dried elbow macaroni threaded on a string like rosary beads, with a bigger macaroni
  medallion at the bottom. Generate it on magenta, hanging straight down. It's also an inventory
  icon.
- **Taken:** hidden.

### A8 The Spinning Fork painting

Where: left wall, under "First Taste" (8–50, 126–182), 42×56.
- A gold-framed painting of a fork twirling spaghetti against a dark blue swirl.
- **Animation:** it loops, with the fork and the noodle swirl turning round. Generate 4 or 8 frames
  of the inside of the painting (the same frame each time), the fork a quarter (or an eighth) of a
  turn further on each time. If that's too hard, generate one frame and I'll keep rotating the
  middle, as now.

---

## Not part of this list

- **The ultraviolet look** of the room and every piece, and the glowing writing ("SAUCE THY
  OFFERING", "THE WORD IS SPUN", "FIRST CAME THE STRING", "SPIN UNTIL IT GLOWS", "NOT A WALL"):
  I make these.
- **Characters** (the bellhop and Chuk): separate sprites. The room only needs open floor for them.
- **The Crypt:** a list like this one can follow if you want it.
