# sudoku.py -- PythonExtra 01.00 / fx-CG50
# One-file playable Sudoku with unique-solution generator.

import gint, time, random

# ---------- layout ----------
BW = 216
CS = 24
PX = BW + 8
W, H = 384, 216

# ---------- colors (with fallback) ----------
try:
    CURSOR_COL = gint.C_RGB(31, 8, 8)
except Exception:
    CURSOR_COL = gint.C_RED

# ---------- input helpers ----------
_HAS_OPT = None

def _poll():
    global _HAS_OPT
    if _HAS_OPT is None:
        _HAS_OPT = hasattr(gint, 'getkey_opt')
    if not _HAS_OPT:
        return gint.getkey()
    try:
        ev = gint.getkey_opt(0, 30)
    except Exception:
        _HAS_OPT = False
        return gint.getkey()
    return ev

def _ticks_add(t, delta):
    try:
        return time.ticks_add(t, delta)
    except AttributeError:
        return t + delta

# ---------- random helpers ----------
def _rnd(n):
    if n <= 1:
        return 0
    bits = 1
    while (1 << bits) < n:
        bits += 1
    while True:
        v = random.getrandbits(bits)
        if v < n:
            return v

def _shuffle(a):
    for i in range(len(a) - 1, 0, -1):
        j = _rnd(i + 1)
        a[i], a[j] = a[j], a[i]

# ---------- drawing primitives ----------
def clear():
    gint.dclear(gint.C_WHITE)

def txt(x, y, s, col=None):
    if col is None:
        col = gint.C_BLACK
    gint.dtext(x, y, col, s)

def txtc(x, y, s, col=None):
    if col is None:
        col = gint.C_BLACK
    try:
        gint.dtext_opt(x, y, col, gint.C_NONE,
                       gint.DTEXT_CENTER, gint.DTEXT_MIDDLE, s, -1)
    except Exception:
        gint.dtext(x - len(s) * 3, y, col, s)

def bold(x, y, s, col=None):
    if col is None:
        col = gint.C_BLACK
    gint.dtext(x, y, col, s)
    gint.dtext(x + 1, y, col, s)

def line(x1, y1, x2, y2, col=None):
    if col is None:
        col = gint.C_BLACK
    gint.dline(x1, y1, x2, y2, col)

def rect(x1, y1, x2, y2, col):
    gint.drect(x1, y1, x2, y2, col)

def border(x1, y1, x2, y2, w, col):
    gint.drect_border(x1, y1, x2, y2, gint.C_NONE, w, col)

def px(x, y, col):
    gint.dpixel(x, y, col)

# ---------- mini font for pencil notes (3x5) ----------
DIG = (
    0b111, 0b101, 0b101, 0b101, 0b111,
    0b010, 0b110, 0b010, 0b010, 0b111,
    0b111, 0b001, 0b111, 0b100, 0b111,
    0b111, 0b001, 0b111, 0b001, 0b111,
    0b101, 0b101, 0b111, 0b001, 0b001,
    0b111, 0b100, 0b111, 0b001, 0b111,
    0b111, 0b100, 0b111, 0b101, 0b111,
    0b111, 0b001, 0b010, 0b010, 0b010,
    0b111, 0b101, 0b111, 0b101, 0b111,
    0b111, 0b101, 0b111, 0b001, 0b111,
)

def draw_note(n, x, y, col=None):
    if col is None:
        col = gint.C_BLACK
    base = n * 5
    for r in range(5):
        bits = DIG[base + r]
        for c in range(3):
            if bits & (1 << (2 - c)):
                px(x + c, y + r, col)

# ---------- sudoku core ----------
def valid(b, r, c, n):
    br, bc = (r // 3) * 3, (c // 3) * 3
    for i in range(9):
        if b[r * 9 + i] == n or b[i * 9 + c] == n:
            return False
        if b[(br + i // 3) * 9 + bc + i % 3] == n:
            return False
    return True

def _is_solved(b):
    for i in range(81):
        if b[i] == 0:
            return False
    mask = 0x3FE
    for r in range(9):
        seen = 0
        for c in range(9):
            seen |= 1 << b[r * 9 + c]
        if seen != mask:
            return False
    for c in range(9):
        seen = 0
        for r in range(9):
            seen |= 1 << b[r * 9 + c]
        if seen != mask:
            return False
    for br in range(0, 9, 3):
        for bc in range(0, 9, 3):
            seen = 0
            for k in range(9):
                seen |= 1 << b[(br + k // 3) * 9 + bc + k % 3]
            if seen != mask:
                return False
    return True

def solve_count(b, limit=2):
    best = -1
    best_c = 10
    for i in range(81):
        if b[i] == 0:
            r, c = i // 9, i % 9
            cnt = 0
            for n in range(1, 10):
                if valid(b, r, c, n):
                    cnt += 1
            if cnt == 0:
                return 0
            if cnt < best_c:
                best_c = cnt
                best = i
                if cnt == 1:
                    break
    if best == -1:
        return 1 if _is_solved(b) else 0
    total = 0
    r, c = best // 9, best % 9
    for n in range(1, 10):
        if valid(b, r, c, n):
            b[best] = n
            total += solve_count(b, limit - total)
            b[best] = 0
            if total >= limit:
                return total
    return total

def full_board():
    nums = list(range(1, 10))
    _shuffle(nums)
    bands      = [0, 1, 2]
    stacks     = [0, 1, 2]
    band_rows  = [0, 1, 2]
    stack_cols = [0, 1, 2]
    _shuffle(bands)
    _shuffle(stacks)
    _shuffle(band_rows)
    _shuffle(stack_cols)
    b = bytearray(81)
    for r in range(9):
        rr = bands[r // 3] * 3 + band_rows[r % 3]
        for c in range(9):
            cc = stacks[c // 3] * 3 + stack_cols[c % 3]
            v = (3 * (rr % 3) + rr // 3 + cc) % 9
            b[r * 9 + c] = nums[v]
    return b

def make_puzzle(diff):
    targets = {1: 43, 2: 35, 3: 28}
    target = targets[diff]
    b = full_board()
    cells = list(range(81))
    _shuffle(cells)
    removed = 0
    deadline = time.ticks_ms() + 20000
    for i in cells:
        if time.ticks_ms() > deadline:
            break
        if 81 - removed <= target:
            break
        old = b[i]
        if old == 0:
            continue
        b[i] = 0
        if solve_count(bytearray(b)) != 1:
            b[i] = old
        else:
            removed += 1
    return b

# ---------- drawing ----------
def cell_xy(r, c):
    return c * CS, r * CS

def draw_grid():
    rect(0, 0, BW - 1, BW - 1, gint.C_WHITE)
    for i in range(10):
        if i == 0 or i == 9:
            w = 2
        elif i % 3 == 0:
            w = 3
        else:
            w = 1
        x = i * CS
        x0 = max(0, min(BW - w, x - (w // 2)))
        gint.drect(x0, 0, x0 + w - 1, BW - 1, gint.C_BLACK)
        gint.drect(0, x0, BW - 1, x0 + w - 1, gint.C_BLACK)

def draw_cell(board, given, notes, r, c):
    x, y = cell_xy(r, c)
    v = board[r * 9 + c]
    rect(x + 2, y + 2, x + CS - 3, y + CS - 3, gint.C_WHITE)
    if v:
        s = str(v)
        if given[r * 9 + c]:
            bold(x + 8, y + 7, s)
        else:
            txt(x + 8, y + 7, s, gint.C_BLUE)
    else:
        m = notes[r * 9 + c]
        for n in range(1, 10):
            if m & (1 << n):
                ox = ((n - 1) % 3) * 7 + 2
                oy = ((n - 1) // 3) * 7 + 2
                draw_note(n, x + ox, y + oy)

def draw_cursor(r, c):
    x, y = cell_xy(r, c)
    border(x + 1, y + 1, x + CS - 2, y + CS - 2, 2, CURSOR_COL)

def draw_panel(diff, elapsed, pencil, solved):
    rect(PX, 0, W - 1, H - 1, gint.C_WHITE)
    line(PX, 0, PX, H - 1)
    txt(PX + 8, 6, "SUDOKU")
    names = {1: "Easy", 2: "Medium", 3: "Hard"}
    txt(PX + 8, 26, "Level: " + names[diff])
    m, s = divmod(elapsed // 1000, 60)
    txt(PX + 8, 42, "Time: %02d:%02d" % (m, s))
    txt(PX + 8, 58, "Pencil: " + ("ON" if pencil else "OFF"))
    txt(PX + 8, 84, "F1 Pencil")
    txt(PX + 8, 98, "F2 Reset")
    txt(PX + 8, 112, "F3 New")
    txt(PX + 8, 126, "F4 Level")
    txt(PX + 8, 140, "EXIT Stop")
    if solved:
        txt(PX + 8, 170, "SOLVED!", gint.C_GREEN)

def draw_all(board, given, notes, r, c, diff, elapsed, pencil, solved):
    clear()
    draw_grid()
    for rr in range(9):
        for cc in range(9):
            draw_cell(board, given, notes, rr, cc)
    draw_cursor(r, c)
    draw_panel(diff, elapsed, pencil, solved)
    gint.dupdate()

# ---------- input ----------
def make_keymap():
    m = {}
    for n in range(1, 10):
        try:
            m[getattr(gint, "KEY_%d" % n)] = n
        except AttributeError:
            pass
    for name in ("KEY_0", "KEY_DEL"):
        try:
            m[getattr(gint, name)] = 0
        except AttributeError:
            pass
    return m

KEYMAP = make_keymap()

# ---------- dialogs ----------
def confirm(question):
    clear()
    txtc(W // 2, H // 2 - 40, question)
    txtc(W // 2, H // 2, "EXE = Yes")
    txtc(W // 2, H // 2 + 24, "AC = No")
    gint.dupdate()
    while True:
        try:
            ev = gint.getkey()
        except KeyboardInterrupt:
            return False
        if ev.key == gint.KEY_EXE:
            return True
        # Other keys: ignore

def _handle_confirm(question, start, solved_at):
    t0 = time.ticks_ms()
    yes = confirm(question)
    t1 = time.ticks_ms()
    if solved_at is None:
        start = _ticks_add(start, time.ticks_diff(t1, t0))
    return yes, start, solved_at

# ---------- screens ----------
def menu():
    clear()
    txtc(W // 2, 30, "SUDOKU")
    txtc(W // 2, 70, "F1  Easy")
    txtc(W // 2, 95, "F2  Medium")
    txtc(W // 2, 120, "F3  Hard")
    txtc(W // 2, 160, "EXIT  Quit")
    gint.dupdate()
    while True:
        try:
            ev = gint.getkey()
        except KeyboardInterrupt:
            continue
        if ev.key == gint.KEY_F1:
            return 1
        if ev.key == gint.KEY_F2:
            return 2
        if ev.key == gint.KEY_F3:
            return 3
        if ev.key == gint.KEY_EXIT:
            return 0

def _generating_screen(diff):
    names = {1: "Easy", 2: "Medium", 3: "Hard"}
    clear()
    txtc(W // 2, H // 2 - 16, "Generating...")
    txtc(W // 2, H // 2 + 12, names[diff])
    txtc(W // 2, H // 2 + 48, "AC = Cancel")
    gint.dupdate()

def _new_game(diff):
    _generating_screen(diff)
    try:
        return make_puzzle(diff)
    except KeyboardInterrupt:
        return None

# ---------- game ----------
def play(diff):
    board = _new_game(diff)
    if board is None:
        return 1
    orig = bytearray(board)
    given = bytearray([1 if v else 0 for v in board])
    notes = [0] * 81
    r = c = 0
    pencil = False
    start = time.ticks_ms()
    solved = False
    solved_at = None
    while True:
        try:
            now = time.ticks_ms()
            elapsed = time.ticks_diff(
                solved_at if solved_at is not None else now, start)
            draw_all(board, given, notes, r, c, diff, elapsed, pencil, solved)
            ev = _poll()
            if ev is None:
                time.sleep_ms(10)
                continue
            try:
                k = ev.key
            except AttributeError:
                time.sleep_ms(10)
                continue

            if k == gint.KEY_EXIT:
                yes, start, solved_at = _handle_confirm(
                    "Quit game?", start, solved_at)
                if yes:
                    return 0
            elif k == gint.KEY_F1:
                pencil = not pencil
            elif k == gint.KEY_F2:
                board = bytearray(orig)
                notes = [0] * 81
                solved = False
                solved_at = None
                start = time.ticks_ms()
            elif k == gint.KEY_F3:
                yes, start, solved_at = _handle_confirm(
                    "New game?", start, solved_at)
                if yes:
                    new_board = _new_game(diff)
                    if new_board is not None:
                        board = new_board
                        orig = bytearray(board)
                        given = bytearray([1 if v else 0 for v in board])
                        notes = [0] * 81
                        solved = False
                        solved_at = None
                        start = time.ticks_ms()
            elif k == gint.KEY_F4:
                yes, start, solved_at = _handle_confirm(
                    "Back to menu?", start, solved_at)
                if yes:
                    return 1
            elif k == gint.KEY_LEFT and c > 0:
                c -= 1
            elif k == gint.KEY_RIGHT and c < 8:
                c += 1
            elif k == gint.KEY_UP and r > 0:
                r -= 1
            elif k == gint.KEY_DOWN and r < 8:
                r += 1
            elif k in KEYMAP:
                n = KEYMAP[k]
                idx = r * 9 + c
                if given[idx]:
                    pass
                elif n == 0:
                    board[idx] = 0
                    notes[idx] = 0
                elif pencil:
                    if board[idx] == 0:
                        notes[idx] ^= 1 << n
                else:
                    if board[idx] == n:
                        board[idx] = 0
                    else:
                        board[idx] = n
                        notes[idx] = 0
            if not solved and _is_solved(board):
                solved = True
                solved_at = time.ticks_ms()
        except KeyboardInterrupt:
            continue

# ---------- entry ----------
def main():
    gint.dclear(gint.C_WHITE)
    gint.dupdate()
    while True:
        try:
            d = menu()
            if d == 0:
                break
            r = play(d)
            if r == 0:
                break
        except KeyboardInterrupt:
            continue

main()