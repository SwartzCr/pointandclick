/* Hotel Paradiso, Room 714 - shared declarations.
 *
 * Included by every .scc file. ScummC compiles each file separately and the
 * linker (sld) resolves these names to the same variables, verbs and rooms.
 */

#include <scummVars6.s>

// Verb bar, laid out like the classic LucasArts 3x3 grid
verb Open, PickUp, Push;
verb Close, LookAt, Pull;
verb TalkTo, Use, WalkTo;

// The sentence line is a verb too ("Look at lamp")
verb SntcLine;

// Never shown: what a plain left click does to an object (open it, pick it
// up, use it...). Each object's verb code maps it onto its usual action.
verb Default;

// Title screen menu
verb NewGame, QuitGame;

// Text inventory: each carried item is a verb in the right-hand column
verb invMatchbook, invCandy, invUniform, invTowel, invSoap, invShaver;
verb invScrewdriver, invPowder, invMirror, invWallet, invDollar;

actor guest;
actor clownA, clownB, clownC;   // room service

// Interface state
int curVerb;       // verb the next room click will use
int withItem;      // inventory verb chosen for "Use X with ..."
int hoverObj;      // room object under the cursor
int hoverInv;      // inventory verb under the cursor
bit gameOver;
bit titleMode;     // on the title screen: only the menu responds

// Puzzle state
bit lampOn, tvOn, curtainsOpen, minibarOpen, drawerOpen;
bit safeOpen, knowsCode;
bit hasMatchbook, hasCandy, hasUniform;
bit tookMatchbook, tookCandy;
bit ateCandy;                       // party prep 1: something in my stomach
bit hasScrewdriver, tookScrewdriver, hasPowder, tookPowder;
bit hasMirror, mirrorRemoved;
int tableMirrorState;               // 0 not on the table, 1 bare, 2 powder, 3..6 three, two, one, no lines
int linesDone;                      // 1: ready to party, 2: the room goes psychedelic, 3: bed, game over
bit tripping;                       // the colour-cycling script is running
bit readyToParty;                   // party prep 3: pre-gamed
bit hasWallet, tookWallet, hasDollar, bedOpen;   // wallet under the bed covers, its dollar bill
bit wearingUniform, tookUniform, dresserOpen;
bit hasTowel, hasSoap, tookTowel, tookSoap;
bit hasShaver, tookShaver;
bit bathCurtainOpen, cabinetOpen;
bit hotelVisited, bathroomVisited;
bit tvAd;
int phoneCalls;

// EGA colours, kept at palette indices 0..15 by tools/make_assets.py
#define C_BLACK   0
#define C_TEAL    3
#define C_GREY    7
#define C_DKGREY  8
#define C_CYAN   11
#define C_YELLOW 14
#define C_WHITE  15

// Engine object class: findObject() skips objects that have it
#define UNTOUCHABLE 32
#define SET_CLASS   0x80

room Hotel;
room Bathroom;
room Title;
room GameOver;

// The resource room: charset, costume and all the global scripts
room ResRoom {
    script refreshInventory();
    script showInterface(int show);
    script readMatchbook();
    script showGameVerbs(int on);
    script startNewGame();
    script startTrip();
    script stopTrip();
    script hideAllVerbs();
}
