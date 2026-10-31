# The title card and the ending cards

The cards in the game are 16:9 (1376×768 shrunk to 640×358, with the captions in the strip
below), saved in `art_src/cards/` and built by `tools/cards.py`. The wrecked Nave is the Nave's
own 20:9 shape. No captions in the pictures.

**Style line** (paste first in every prompt; attach the Nave or the Crypt picture as the reference):

```
Hand-painted background art for a 1990s point-and-click adventure game, in the style of early-90s VGA adventure games like Day of the Tentacle and Sam & Max. Bold dark outlines, chunky shapes, a slightly crooked cartoon perspective, rich texture. Match the colours, lighting, line style and characters of the attached reference images exactly. Wide 20:9 picture, no captions or speech bubbles.
```

## Title card (`title`)

```
A title screen. At night, a tall, crooked old hotel seen from the street, with HOTEL PARADISO in glowing pink neon letters on its roof and one lit window high up with the number 714. Below the hotel, a small stone chapel door is set into its foundations, warm candlelight spilling out of it and up the steps. Rising behind the hotel like a sunrise, filling the sky, is a gentle, smiling flying spaghetti monster god: a tangle of golden noodles, two big meatballs, two eyes on stalks, its noodly appendages spreading over the rooftop like rays of light. Across the lower middle of the picture, big chunky golden title lettering with a dark outline: "SACRA PASTA". Keep the bottom sixth of the picture plain dark street so menu text can sit near it.
```

If the lettering comes out garbled, ask for the same picture with no lettering and an empty band
across the lower middle; I'll put the title in myself.

## Ending 1: room service

**1a: carried off** (`end_roomservice`)

```
A long hotel corridor at night, patterned red carpet, rows of numbered doors, wall sconces. Three circus clowns working as room service (one in a yellow suit with blue dots and orange hair, one in a green suit with yellow dots and purple hair, one in a blue suit with pink dots and yellow hair) march away from us down the corridor in a cheerful parade. Held stiff and horizontal over their heads they carry the bellhop, wearing a tall papal mitre made of pasta and a macaroni rosary, and Chuk, in his cream robe with a colander on his head, his arms folded. Outside every door sits a silver room-service tray with a domed cover. Halfway down the corridor, a small white duck peers out of an ice bucket.
```
Attach the bellhop, Chuk and clown sheets as references.

**1b: the next morning** (`end_roomservice_after`)

```
A neat, empty hotel room in morning light, the bed freshly made with the sheets folded down. On the pillow lies a metal kitchen colander next to a tall papal mitre made of pasta, and a single mint. A room-service tray with an empty plate sits on the dresser. A red clown nose has rolled under the bedside table.
```

## Ending 2: free play

**2a**: the Crypt full of clowns. You're painting it on `crypt_final_for_clowns.png`.

**2b: the petition** (`end_freeplay_petition`), optional

```
Close-up in the Crypt: Chuk, in his cream robe and colander hat, stands holding a clipboard with a petition and a pen, looking defeated. Behind him the clowns' backs are hunched over the glowing arcade cabinets. Chuk's clipboard shows a single line with no signatures. Next to him the T. Rex cabinet's high-score screen lists only "HONK".
```

## Ending 3: the party

**3a**: done (`v3-W-wrecked.png`).

**3b: the tiny folk rebuilding** (`end_party_tiny`), optional

```
A close-up of the tabletop miniature village from the Nave, the morning after a party: tiny thatched houses knocked over, a red party cup lying on its side like a fallen tower, spilled sauce running through the streets. Little villagers, about thumb-sized, are busy rebuilding with scaffolding of uncooked spaghetti. In the middle of the village square they have dug up a small silver whipped-cream charger and are holding it up over their heads in triumph.
```

## THE END card (`the_end`), optional, shared by all three endings

```
Dawn over the crooked HOTEL PARADISO, seen from a distance across the rooftops of the town. The pink neon sign is switching off. Above the hotel, the smiling flying spaghetti monster god is drifting away into a pink and gold morning sky, waving one noodly appendage goodbye. Leave the upper middle of the sky clear for the words THE END.
```
