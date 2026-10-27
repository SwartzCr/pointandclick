// Hotel Paradiso: Sacra Pasta -- global script header

// verbs, in the order of the 3x3 grid
#define V_NONE   0
#define V_OPEN   1
#define V_PICKUP 2
#define V_PUSH   3
#define V_CLOSE  4
#define V_LOOK   5
#define V_PULL   6
#define V_TALK   7
#define V_USE    8
#define V_WALK   9

// what the cursor is over
#define T_NONE 0
#define T_HOT  1
#define T_OBJ  2
#define T_CHAR 3
#define T_INV  4

#define UI_Y 288

import void ShowNote(String title, String body, int style);
import int  Choose(String a, String b, String c, String d, String e);
import void Narrate(int x, int y, int color, String text);
