# Battleship - pass and play (2 players, 1 calculator)
# For PythonExtra on Casio fx-CG50 / Graph 90+E, uses the gint module.
#
# Controls
#   Arrows : move cursor
#   F1     : rotate ship (placement)
#   EXE    : place ship / fire / continue
#   F2     : peek at your own fleet during your turn
#   EXIT   : quit

from gint import *

# ---------------------------------------------------------------- colours
def rgb(r, g, b):
    # gint colours are 5-6-5, so each channel is 0..31
    try:
        return C_RGB(r, g, b)
    except NameError:
        return C_BLUE

BG = C_WHITE
INK = C_BLACK
WATER = rgb(6, 14, 24)
GRIDLINE = rgb(12, 20, 28)
SHIP = rgb(16, 16, 16)
SUNK = rgb(14, 0, 0)
HIT = C_RED
MISS = C_WHITE
CURSOR = rgb(31, 28, 0)
OK = rgb(4, 24, 4)
BAD = C_RED

# ---------------------------------------------------------------- settings
N = 10          # grid size
CELL = 20       # pixels per cell
GX, GY = 8, 12  # top-left of the grid
PX = 226        # left edge of the side panel

SHIPS = [("Carrier", 5), ("Battleship", 4), ("Cruiser", 3),
         ("Submarine", 3), ("Destroyer", 2)]

LETTERS = "ABCDEFGHIJ"


class Quit(Exception):
    pass


# ---------------------------------------------------------------- helpers
def text(x, y, s, c=INK, center=False):
    if center:
        try:
            dtext_opt(x, y, c, C_NONE, DTEXT_CENTER, DTEXT_TOP, s, -1)
            return
        except Exception:
            x = x - len(s) * 3
    dtext(x, y, c, s)


def readkey():
    # getkey() blocks and returns a KeyEvent with a .key attribute
    # (not a bare code, not a tuple).
    ev = getkey()
    k = ev.key
    if k == KEY_EXIT:
        raise Quit()
    return k


def frame(x1, y1, x2, y2, c, w=2):
    drect(x1, y1, x2, y1 + w - 1, c)
    drect(x1, y2 - w + 1, x2, y2, c)
    drect(x1, y1, x1 + w - 1, y2, c)
    drect(x2 - w + 1, y1, x2, y2, c)


def cell_xy(x, y):
    x1 = GX + x * CELL
    y1 = GY + y * CELL
    return x1, y1, x1 + CELL - 1, y1 + CELL - 1


# ---------------------------------------------------------------- state
def new_game():
    g = {}
    # ship_at[p][y][x] = index of ship, or -1
    g["ship_at"] = [[[-1] * N for _ in range(N)] for _ in range(2)]
    # shots[p][y][x] = shots received by player p: 0 none, 1 miss, 2 hit
    g["shots"] = [[[0] * N for _ in range(N)] for _ in range(2)]
    g["hp"] = [[s[1] for s in SHIPS] for _ in range(2)]
    return g


# ---------------------------------------------------------------- drawing
def draw_board(g, p, reveal, cursor=None, preview=None, preview_ok=True):
    """Draw player p's board.
    reveal=True  -> show ships (own fleet view)
    reveal=False -> firing view: only hits/misses (and sunk ships)"""
    ship_at = g["ship_at"][p]
    shots = g["shots"][p]
    hp = g["hp"][p]
    for y in range(N):
        for x in range(N):
            x1, y1, x2, y2 = cell_xy(x, y)
            s = ship_at[y][x]
            shot = shots[y][x]
            col = WATER
            if s >= 0 and reveal:
                col = SHIP
            if s >= 0 and hp[s] == 0:
                col = SUNK
            drect(x1, y1, x2, y2, col)
            frame(x1, y1, x2, y2, GRIDLINE, 1)
            if shot == 2:
                drect(x1 + 4, y1 + 4, x2 - 4, y2 - 4, HIT)
            elif shot == 1:
                drect(x1 + 8, y1 + 8, x2 - 8, y2 - 8, MISS)
    if preview:
        c = OK if preview_ok else BAD
        for (x, y) in preview:
            x1, y1, x2, y2 = cell_xy(x, y)
            drect(x1 + 1, y1 + 1, x2 - 1, y2 - 1, c)
    if cursor:
        x1, y1, x2, y2 = cell_xy(cursor[0], cursor[1])
        frame(x1, y1, x2, y2, CURSOR, 3)


def coord(x, y):
    return LETTERS[x] + str(y + 1)


def draw_fleet_status(g, p, y0):
    """List player p's ships with sunk/afloat status."""
    hp = g["hp"][p]
    for i, (name, ln) in enumerate(SHIPS):
        yy = y0 + i * 14
        if hp[i] == 0:
            text(PX, yy, name + " SUNK", HIT)
        else:
            text(PX, yy, name + " " + str(ln), INK)


# ---------------------------------------------------------------- screens
def pass_screen(p, what):
    dclear(BG)
    text(198, 50, "PLAYER " + str(p + 1), INK, True)
    text(198, 90, what, INK, True)
    text(198, 130, "Pass the calculator", INK, True)
    text(198, 170, "Press EXE when ready", INK, True)
    dupdate()
    while readkey() != KEY_EXE:
        pass


def ship_cells(cx, cy, ln, horiz):
    if horiz:
        return [(cx + i, cy) for i in range(ln)]
    return [(cx, cy + i) for i in range(ln)]


def place_fleet(g, p):
    ship_at = g["ship_at"][p]
    cx, cy = 0, 0
    horiz = True
    for idx, (name, ln) in enumerate(SHIPS):
        while True:
            # keep the ship inside the grid
            if horiz and cx > N - ln:
                cx = N - ln
            if not horiz and cy > N - ln:
                cy = N - ln
            cells = ship_cells(cx, cy, ln, horiz)
            free = all(ship_at[y][x] < 0 for (x, y) in cells)

            dclear(BG)
            draw_board(g, p, True, None, cells, free)
            text(PX, 12, "PLAYER " + str(p + 1), INK)
            text(PX, 32, "Place ship:", INK)
            text(PX, 48, name + " (" + str(ln) + ")", INK)
            text(PX, 84, "Arrows: move", INK)
            text(PX, 100, "F1: rotate", INK)
            text(PX, 116, "EXE: place", INK)
            if not free:
                text(PX, 150, "Ships overlap!", BAD)
            dupdate()

            k = readkey()
            if k == KEY_LEFT and cx > 0:
                cx -= 1
            elif k == KEY_RIGHT:
                cx += 1
                if cx > N - 1:
                    cx = N - 1
            elif k == KEY_UP and cy > 0:
                cy -= 1
            elif k == KEY_DOWN:
                cy += 1
                if cy > N - 1:
                    cy = N - 1
            elif k == KEY_F1:
                horiz = not horiz
            elif k == KEY_EXE and free:
                for (x, y) in cells:
                    ship_at[y][x] = idx
                break

    # let the player look at the finished layout before hiding it
    dclear(BG)
    draw_board(g, p, True)
    text(PX, 12, "PLAYER " + str(p + 1), INK)
    text(PX, 40, "Fleet ready!", INK)
    text(PX, 70, "Press EXE", INK)
    dupdate()
    while readkey() != KEY_EXE:
        pass


def fire_at(g, attacker, x, y):
    """Returns (message, game_over) or None if already shot there."""
    d = 1 - attacker
    if g["shots"][d][y][x] != 0:
        return None
    s = g["ship_at"][d][y][x]
    if s < 0:
        g["shots"][d][y][x] = 1
        return ("MISS", False)
    g["shots"][d][y][x] = 2
    g["hp"][d][s] -= 1
    if g["hp"][d][s] == 0:
        over = all(h == 0 for h in g["hp"][d])
        return ("You sunk the " + SHIPS[s][0] + "!", over)
    return ("HIT!", False)


def take_turn(g, p):
    """Player p fires once. Returns True if p won."""
    d = 1 - p
    cx, cy = 0, 0
    peek = False
    msg = ""
    while True:
        dclear(BG)
        if peek:
            draw_board(g, p, True)
            text(PX, 12, "YOUR FLEET", INK)
            text(PX, 30, "Red = hit on you", INK)
            text(PX, 46, "White = enemy miss", INK)
            draw_fleet_status(g, p, 76)
            text(PX, 170, "F2: back", INK)
        else:
            draw_board(g, d, False, (cx, cy))
            text(PX, 12, "PLAYER " + str(p + 1) + " - FIRE", INK)
            text(PX, 30, "Target: " + coord(cx, cy), INK)
            draw_fleet_status(g, d, 56)
            text(PX, 140, "EXE: fire", INK)
            text(PX, 156, "F2: my fleet", INK)
            if msg:
                text(PX, 176, msg, BAD)
        dupdate()

        k = readkey()
        if k == KEY_F2:
            peek = not peek
            continue
        if peek:
            continue
        if k == KEY_LEFT and cx > 0:
            cx -= 1
        elif k == KEY_RIGHT and cx < N - 1:
            cx += 1
        elif k == KEY_UP and cy > 0:
            cy -= 1
        elif k == KEY_DOWN and cy < N - 1:
            cy += 1
        elif k == KEY_EXE:
            res = fire_at(g, p, cx, cy)
            if res is None:
                msg = "Already fired!"
                continue
            text_msg, over = res
            # show the result
            dclear(BG)
            draw_board(g, d, False, (cx, cy))
            text(PX, 12, "PLAYER " + str(p + 1), INK)
            text(PX, 30, coord(cx, cy) + ":", INK)
            col = INK if text_msg == "MISS" else HIT
            text(PX, 56, text_msg, col)
            draw_fleet_status(g, d, 96)
            text(PX, 180, "Press EXE", INK)
            dupdate()
            while readkey() != KEY_EXE:
                pass
            return over


def victory(g, p):
    dclear(BG)
    text(198, 60, "PLAYER " + str(p + 1) + " WINS!", HIT, True)
    text(198, 100, "All enemy ships sunk.", INK, True)
    text(198, 150, "EXE: play again", INK, True)
    text(198, 170, "EXIT: quit", INK, True)
    dupdate()
    while readkey() != KEY_EXE:
        pass


# ---------------------------------------------------------------- main
def play():
    g = new_game()
    for p in (0, 1):
        pass_screen(p, "Place your ships")
        place_fleet(g, p)
    p = 0
    while True:
        pass_screen(p, "Your turn to fire")
        if take_turn(g, p):
            victory(g, p)
            return
        p = 1 - p


def main():
    try:
        while True:
            play()
    except Quit:
        pass


main()
