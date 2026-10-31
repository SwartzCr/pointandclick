# Character sprite sheets: the bellhop, Chuk and the clowns

Prompts for every pose the game uses now (the reworked Crypt and the three endings
included). Each sheet is one image, generated in Nano Banana / Google AI Studio.

## Rules for every sheet

- **Attach the existing sheets as references** (`bellhop_walk_side.jpg` for the bellhop,
  `khuc_sheet.jpg` for Chuk), so the character, colours and pixel style stay the same.
- **Flat magenta background (#FF00FF)**, nothing else in the picture: no floor, no shadows,
  no props unless the prompt names one.
- **Full body, same height, same scale** in every figure on a sheet (heads excepted), feet
  on the same line in each row, and a clear gap between figures so I can cut them apart.
- **Exactly the figures listed, in that order**, left to right.
- Wide sheets, about 16:9 (the old ones are 1376×768). PNG if possible; JPEG is fine.

**Style line** (paste first in every prompt):

```
Pixel art sprite sheet for a 1990s point-and-click adventure game, in the style of early-90s VGA adventure games like Day of the Tentacle and Sam & Max. Bold dark outlines, chunky shapes, clean flat shading. Flat magenta (#FF00FF) background with nothing else on it. Every figure full body, the same height and scale, evenly spaced with clear gaps, feet on one line. Match the character, colours and pixel style of the attached reference sheet exactly.
```

---

## The bellhop

**Character line** (paste after the style line):

```
The character: a young hotel bellhop with short brown hair and a friendly face, in a red bellhop uniform: a red pillbox hat with a gold band, a short red double-breasted jacket with two rows of gold buttons and black cuffs, red trousers with a gold stripe down the side, and brown shoes.
```

### Sheet B1: standing and walking sideways (`bellhop_walk_side`)

```
Two rows. Top row, four standing poses: facing us; facing away from us; facing right in profile; facing left in profile. Bottom row: a six-frame walk cycle facing right, in profile, from one foot forward through to the other, arms swinging.
```

### Sheet B2: walking towards and away (`bellhop_walk_fb`)

```
Two rows of four. Top row: a four-frame walk cycle walking towards us (left foot forward, feet together, right foot forward, feet together). Bottom row: a four-frame walk cycle walking away from us, seen from behind, in the same rhythm.
```

### Sheet B3: actions (`bellhop_actions`)

```
Two rows. Top row, six poses, all facing right in profile unless noted: 1) reaching forward at chest height to take or use something; 2) bending down to pick something up off the floor; 3) pushing something with both hands; 4) pulling something towards himself with both hands, leaning back; 5) sitting on an invisible chair, seen from the front, hands resting on invisible armrests, feet on the ground; 6) the same sitting pose with his right arm raised high, index finger pointing up, making a grand proclamation. Bottom row, four close-ups of his head and hat only, twice the scale: facing us with mouth closed; facing us with mouth open, talking; in right profile with mouth closed; in right profile with mouth open, talking.
```

### Sheet B4: what he wears (`bellhop_extras`)

```
Two rows of four standing poses: facing us, facing away, facing right in profile, facing left in profile. Top row: wearing a rosary made of dried elbow macaroni on a gold string around his neck, with a bigger flat macaroni medallion hanging on his chest. Bottom row: wearing a small violet crystal pendant on a fine silver chain, glowing faintly purple, and the macaroni rosary as well.
```

### Sheet B5: the Crypt and the endings (`bellhop_crypt`), new

```
Two rows. Top row: 1) and 2) a two-frame animation of him standing at an arcade cabinet seen from behind, hands on the controls, leaning in, the second frame with his shoulders moved as if jabbing buttons; 3) and 4) a two-frame animation seen from behind of him rolling a big trackball with both palms, hands moved round between frames; 5) seen from behind, sitting low in a racing-style arcade seat, hands on a small steering wheel. Bottom row: 6) a victory fist pump, facing us, one fist up, mouth open in a cheer; 7) lying stiff and horizontal on his back, arms at his sides, as if being carried off overhead (no one carrying him); 8) facing us holding a red party cup up in a toast, grinning; 9) facing us, slumped and bleary the morning after, hat askew.
```

---

## Chuk

**Character line** (paste after the style line):

```
The character: Chuk, a middle-aged keeper of a pasta shrine, with a short dark beard, thick red-framed glasses and a metal kitchen colander worn as a hat. He wears a long cream robe to his ankles, a dark red stole with gold embroidery and fringed ends hanging down the front, and brown sandals.
```

### Sheet C1: standing, walking sideways, ceremonies (`khuc_sheet`)

The current sheet, regenerate only if you want it refreshed:

```
Two rows. Top row: standing facing us; facing away from us; facing right in profile; facing left in profile; then two close-ups of his head with colander and glasses, twice the scale, facing us, mouth closed and mouth open talking. Bottom row: a four-frame walk cycle facing right in profile; standing facing us with both arms raised high in blessing; seen from behind, hunched forward as if playing an arcade game; facing right, turning a crank handle at waist height with one hand.
```

### Sheet C2: walking towards and away (`chuk_walk_fb`), new

```
Two rows of four. Top row: a four-frame walk cycle walking towards us, robe swinging. Bottom row: a four-frame walk cycle walking away from us, seen from behind.
```

### Sheet C3: games, chores and the endings (`chuk_actions`), new

```
Two rows. Top row: 1) and 2) a two-frame animation, seen from behind, of him sitting low in a racing-style arcade seat, hunched over a small steering wheel, the second frame leaning the other way as if dodging; 3) and 4) a two-frame animation in right profile of him turning a crank handle at waist height, the handle at the top of its turn and then at the bottom; 5) in right profile, leaning forward and pressing a button on a small box at waist height with one finger. Bottom row: 6) in right profile, crouching down to push a plug into a wall socket, a cable in his hand; 7) facing us, carrying an armful of four pale stone shapes against his chest (a ring, a knot, a figure-eight loop and a twisted band); 8) facing us, both hands clutching his colander in horror, mouth wide open; 9) facing us, both fists in the air, cheering; 10) facing us, holding a red party cup, sheepish smile; 11) lying stiff and horizontal on his back, arms folded, as if being carried off overhead (no one carrying him).
```

---

## The clowns

The three room-service clowns from Hotel Paradiso, who arrive in two of the endings. They're
the same three people in different colours, so generate **one set of sheets per clown**:
paste the clown line, then the line for that clown's colours, then the sheet. Attach
`clowns_reference.png` (the first game's clowns, next to this file) as well as any finished
clown sheet, so all three come out as one troupe.

**Clown line** (paste after the style line):

```
The character: a circus clown working as hotel room service. White greasepaint face, round red nose, wide red painted smile, black dot eyes, a big frilly white ruff collar, a baggy one-piece polka-dot clown suit, white gloves, enormous red clown shoes, and a wild puff of clown hair on each side of a bald crown. Cheerful, a little sinister.
```

**Colours** (pick one per set):

```
Clown one: a yellow suit with blue polka dots and bright orange hair.
```
```
Clown two: a green suit with yellow polka dots and purple hair.
```
```
Clown three: a blue suit with pink polka dots and yellow hair.
```

### Sheet K1: standing and walking (`clown1_walk`, `clown2_walk`, `clown3_walk`)

```
Three rows. Top row, four standing poses: facing us; facing away from us; facing right in profile; facing left in profile. Middle row: a six-frame walk cycle facing right, in profile, big floppy shoes slapping, arms swinging. Bottom row: a four-frame walk cycle walking towards us, then a four-frame walk cycle walking away from us, seen from behind.
```

### Sheet K2: the endings (`clown1_actions`, `clown2_actions`, `clown3_actions`)

```
Two rows. Top row: 1) facing us, carrying a silver room-service tray with a domed cloche on one raised hand, the other hand on the hip; 2) facing us, both arms straight up overhead, hands open, as if carrying someone above his head (no one there); 3) the same, mid-stride, one foot forward; 4) facing us, shouting with arms flung wide, mouth wide open; 5) facing us, honking a small bicycle horn. Bottom row: 6) and 7) a two-frame animation of him standing at an arcade cabinet seen from behind, hands on the controls, the second frame jabbing buttons; 8) seen from behind, sitting low in a racing-style arcade seat, hands on a small steering wheel; 9) and 10) two close-ups of his head and ruff, twice the scale, facing us, mouth closed and mouth open, talking.
```

| Clown pose | Where |
|---|---|
| Stand and walk, four directions | in through the Crypt's archway and back out |
| Tray | "Room service for all!": they arrive with room service |
| Arms up overhead (standing and mid-stride) | carrying the new Pope and Chuk away |
| Shouting, arms wide | "ROOM SERVICE!", "FREE PLAY!" |
| Horn | a honk as they arrive (optional) |
| Arcade (standing, racing seat) | "All games are free play!": taking over CONFESS, MEATBALL MADNESS and T. Rex |
| Talking heads | their lines |

---

## How each pose is used

| Pose | Where |
|---|---|
| Bellhop stand / walk in four directions | everywhere |
| Talking heads | all his lines |
| Reach, bend, push, pull | using, picking up, pushing and pulling things |
| Sit, sit with arm raised | the Pope Seat, and the papal request |
| Macaroni rosary, UV pendant | after you make the beads / put on the pendant |
| Arcade (standing, trackball, racing seat) | CONFESS, MEATBALL MADNESS, the Rex Seat |
| Fist pump | winning MEATBALL MADNESS and T. Rex |
| Lying stiff | room-service ending: carried off by the clowns |
| Party cup, morning after | party ending |
| Chuk stand / walk in four directions | the Nave and the Crypt (he walks to the archway, the box, the staff room, the computer and the Pope Seat) |
| Chuk arms raised | the ordination, "FREE PLAY!" |
| Chuk in the racing seat | playing T. Rex until you beat him |
| Chuk turning the crank | lowering the papal hat |
| Chuk pressing a button | opening his puzzle box himself |
| Chuk crouching with the plug | plugging in the Crypt's computer |
| Chuk carrying the shapes | bringing the shapes out of the staff room |
| Chuk in horror | "What have you done!" (room service) |
| Chuk cheering | free-play ending |
| Chuk with a cup | party ending |
| Chuk lying stiff | room-service ending |

Not needed: ultraviolet versions (the game tints the characters), and the bathrobe guest in
HOTEL.EXE (he stays as he was in the first game).
