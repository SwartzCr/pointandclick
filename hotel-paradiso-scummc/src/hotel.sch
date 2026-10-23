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

// Text inventory: each carried item is a verb in the right-hand column
verb invMatchbook, invKeycard, invCandy;

actor guest;

// Interface state
int curVerb;       // verb the next room click will use
int withItem;      // inventory verb chosen for "Use X with ..."
int hoverObj;      // room object under the cursor
int hoverInv;      // inventory verb under the cursor
bit gameOver;

// Puzzle state
bit lampOn, tvOn, curtainsOpen, minibarOpen, drawerOpen;
bit safeOpen, knowsCode;
bit hasMatchbook, hasKeycard, hasCandy;
bit tookMatchbook, tookKeycard, tookCandy;
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

// The resource room: charset, costume and all the global scripts
room ResRoom {
    script refreshInventory();
    script showInterface(int show);
    script readMatchbook();
}
