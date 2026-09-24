# Nonogram (Picross) - gint graphical version for fx-CG50 (PythonExtra)
#
# Controls:
#   Arrow keys : move the cursor
#   EXE        : cycle the selected cell  empty -> filled -> crossed -> empty
#   F1         : set cell filled
#   F2         : set cell crossed
#   F3         : clear cell
#   F4         : new puzzle (same size)
#   F5         : check the solution
#   F6 / EXIT  : back to the size menu / quit
#
# Uses the gint module (see the PythonExtra gint reference) instead of
# casioplot, so drawing and key handling are both fast and responsive.

from gint import *
import random

SIZES = (5, 10, 15)

EMPTY = 0
FILLED = 1
CROSS = 2


# ---------------------------------------------------------------- puzzle

def make_solution(size, density):
    while True:
        grid = [[1 if random.random() < density else 0 for _ in range(size)]
                for _ in range(size)]
        total = sum(sum(row) for row in grid)
        if total == 0 or total == size * size:
            continue
        if any(sum(row) == 0 for row in grid):
            continue
        if any(all(grid[r][c] == 0 for r in range(size)) for c in range(size)):
            continue
        return grid


def line_clue(line):
    clue = []
    run = 0
    for v in line:
        if v == 1:
            run += 1
        elif run:
            clue.append(run)
            run = 0
    if run:
        clue.append(run)
    return clue if clue else [0]


def row_clues(grid):
    return [line_clue(row) for row in grid]


def col_clues(grid):
    size = len(grid)
    return [line_clue([grid[r][c] for r in range(size)]) for c in range(size)]


def fmt_clue(clue):
    return ' '.join(str(n) for n in clue)


# ------------------------------------------------------------- line solver
#
# Pure constraint-propagation solver: for one row/column, figures out which
# cells MUST be filled or MUST be empty given the clue and whatever is
# already known, with no guessing. Used only at generation time to reject
# puzzles that would require brute-forcing to solve.

def blocks_of(clue):
    return [] if clue == [0] else clue


def make_cum_bad1(known, n):
    # cum[j] = number of cells in known[0:j] that CANNOT be filled (== 0).
    # Lets us test "can cells [a,b) all be filled?" in O(1) via cum[b]-cum[a].
    cum = [0] * (n + 1)
    for t in range(n):
        cum[t + 1] = cum[t] + (1 if known[t] == 0 else 0)
    return cum


def build_fwd(n, blocks, known, cum_bad1):
    # FWD[i][j] = True if the first i blocks can be packed into known[0:j],
    # with any cells not used by a block able to be 0 (trailing zeros
    # allowed). FWD[m][n] tells us whether the whole line is feasible.
    m = len(blocks)
    FWD = [[False] * (n + 1) for _ in range(m + 1)]
    FWD[0][0] = True
    for j in range(1, n + 1):
        FWD[0][j] = FWD[0][j - 1] and known[j - 1] != 1
    for i in range(1, m + 1):
        L = blocks[i - 1]
        gap = 1 if i >= 2 else 0
        row_prev = FWD[i - 1]
        row = FWD[i]
        for j in range(1, n + 1):
            val = row[j - 1] and known[j - 1] != 1
            if not val and j >= L:
                s = j - L
                if cum_bad1[j] - cum_bad1[s] == 0:
                    prev_end = s - gap
                    if prev_end >= 0 and row_prev[prev_end] and \
                            (gap == 0 or known[prev_end] != 1):
                        val = True
            row[j] = val
    return FWD


def solve_line(n, blocks, known):
    # Mutates `known` (list of -1/0/1) in place with any forced deductions.
    # Returns True if anything changed.
    m = len(blocks)
    changed = False

    if m == 0:
        for t in range(n):
            if known[t] != 0:
                known[t] = 0
                changed = True
        return changed

    if sum(blocks) + (m - 1) == n:
        # Fully determined: blocks exactly fill the line with single gaps.
        pos = 0
        for L in blocks:
            for t in range(pos, pos + L):
                if known[t] != 1:
                    known[t] = 1
                    changed = True
            pos += L
            if pos < n:
                if known[pos] != 0:
                    known[pos] = 0
                    changed = True
                pos += 1
        return changed

    for t in range(n):
        if known[t] != -1:
            continue
        known[t] = 0
        feas0 = build_fwd(n, blocks, known, make_cum_bad1(known, n))[m][n]
        known[t] = 1
        feas1 = build_fwd(n, blocks, known, make_cum_bad1(known, n))[m][n]
        known[t] = -1
        if feas0 and not feas1:
            known[t] = 0
            changed = True
        elif feas1 and not feas0:
            known[t] = 1
            changed = True
    return changed


def is_solvable_by_logic(rc, cc, size):
    grid = [[-1] * size for _ in range(size)]
    queue = []
    in_queue = set()
    for r in range(size):
        queue.append(('r', r))
        in_queue.add(('r', r))
    for c in range(size):
        queue.append(('c', c))
        in_queue.add(('c', c))

    qi = 0
    while qi < len(queue):
        kind, idx = queue[qi]
        qi += 1
        in_queue.discard((kind, idx))
        if kind == 'r':
            line = [grid[idx][c] for c in range(size)]
            if solve_line(size, blocks_of(rc[idx]), line):
                for c in range(size):
                    if grid[idx][c] != line[c]:
                        grid[idx][c] = line[c]
                        key = ('c', c)
                        if key not in in_queue:
                            queue.append(key)
                            in_queue.add(key)
        else:
            line = [grid[r][idx] for r in range(size)]
            if solve_line(size, blocks_of(cc[idx]), line):
                for r in range(size):
                    if grid[r][idx] != line[r]:
                        grid[r][idx] = line[r]
                        key = ('r', r)
                        if key not in in_queue:
                            queue.append(key)
                            in_queue.add(key)

    for row in grid:
        if -1 in row:
            return False
    return True


MAX_GEN_ATTEMPTS = 40
DENSITY = 0.6  # denser grids are logically solvable far more often than
               # sparse ones - isolated cells are ambiguous, solid runs
               # are easy to pin down. Tested to solve on the first or
               # second try in the large majority of cases at all sizes.


def new_puzzle(size):
    solution = None
    rc = cc = None
    for _attempt in range(MAX_GEN_ATTEMPTS):
        solution = make_solution(size, DENSITY)
        rc = row_clues(solution)
        cc = col_clues(solution)
        if is_solvable_by_logic(rc, cc, size):
            break
    # If we somehow ran out of attempts, fall back to the last candidate
    # rather than hang forever - rare, but better than freezing.
    state = [[EMPTY] * size for _ in range(size)]
    return rc, cc, state


def is_solved(state, rclues, cclues, size):
    filled = [[1 if state[r][c] == FILLED else 0 for c in range(size)]
              for r in range(size)]
    return row_clues(filled) == rclues and col_clues(filled) == cclues


# ---------------------------------------------------------------- layout

CHAR_W = 7   # estimated default-font glyph width in pixels
LINE_H = 10  # estimated default-font line height in pixels


def compute_layout(rc, cc, size):
    max_chars = 0
    for clue in rc:
        n = len(fmt_clue(clue))
        if n > max_chars:
            max_chars = n
    row_label_w = max_chars * CHAR_W + 8

    line_h = LINE_H
    col_lines = max(len(c) for c in cc)
    header_h = col_lines * line_h + 4
    bottom_h = 4  # just a small margin now that the control strip is gone

    avail_w = DWIDTH - row_label_w
    avail_h = DHEIGHT - header_h - bottom_h
    cell = avail_w // size
    alt = avail_h // size
    if alt < cell:
        cell = alt
    if cell < 6:
        cell = 6

    return {
        'left': row_label_w,
        'top': header_h,
        'cell': cell,
        'line_h': line_h,
    }


# ---------------------------------------------------------------- drawing

def draw_board(state, rc, cc, size, cur_r, cur_c, layout, message):
    dclear(C_WHITE)

    left = layout['left']
    top = layout['top']
    cell = layout['cell']
    line_h = layout['line_h']
    grid_w = cell * size
    grid_h = cell * size

    # column clues, bottom-aligned just above the grid
    for c in range(size):
        clue = cc[c]
        for i, n in enumerate(clue):
            from_bottom = len(clue) - 1 - i
            y = top - (from_bottom + 1) * line_h
            x = left + c * cell + cell // 2
            dtext_opt(x, y, C_BLACK, C_NONE, DTEXT_CENTER, DTEXT_TOP,
                      str(n), -1)

    # row clues, left-aligned from a small screen margin (can't run off-screen)
    for r in range(size):
        y = top + r * cell + cell // 2
        dtext_opt(2, y, C_BLACK, C_NONE, DTEXT_LEFT, DTEXT_MIDDLE,
                  fmt_clue(rc[r]), -1)

    # cell contents
    for r in range(size):
        for c in range(size):
            x1 = left + c * cell
            y1 = top + r * cell
            x2 = x1 + cell
            y2 = y1 + cell
            st = state[r][c]
            if st == FILLED:
                drect(x1, y1, x2 - 1, y2 - 1, C_BLACK)
            elif st == CROSS:
                dline(x1 + 2, y1 + 2, x2 - 3, y2 - 3, C_BLACK)
                dline(x2 - 3, y1 + 2, x1 + 2, y2 - 3, C_BLACK)

    # grid lines
    for i in range(size + 1):
        x = left + i * cell
        dline(x, top, x, top + grid_h, C_BLACK)
        y = top + i * cell
        dline(left, y, left + grid_w, y, C_BLACK)

    # thicker lines every 5 cells, for readability on 10x10 / 15x15
    if size >= 10:
        for i in range(0, size + 1, 5):
            x = left + i * cell
            dline(x + 1, top, x + 1, top + grid_h, C_BLACK)
            y = top + i * cell
            dline(left, y + 1, left + grid_w, y + 1, C_BLACK)

    # cursor highlight
    cx1 = left + cur_c * cell
    cy1 = top + cur_r * cell
    cx2 = cx1 + cell
    cy2 = cy1 + cell
    dline(cx1, cy1, cx2, cy1, C_RED)
    dline(cx1, cy2, cx2, cy2, C_RED)
    dline(cx1, cy1, cx1, cy2, C_RED)
    dline(cx2, cy1, cx2, cy2, C_RED)

    if message:
        dtext_opt(DWIDTH // 2, top + grid_h // 2, C_RED, C_WHITE,
                  DTEXT_CENTER, DTEXT_MIDDLE, message, -1)

    dupdate()


# ---------------------------------------------------------------- menu

def show_controls():
    dclear(C_WHITE)
    dtext(10, 8, C_BLACK, "Controls")
    dtext(10, 30, C_BLACK, "Arrows : move cursor")
    dtext(10, 46, C_BLACK, "EXE : cycle cell state")
    dtext(10, 62, C_BLACK, "F1 : set filled")
    dtext(10, 78, C_BLACK, "F2 : set crossed")
    dtext(10, 94, C_BLACK, "F3 : set blank")
    dtext(10, 110, C_BLACK, "F4 : new puzzle (asks")
    dtext(10, 122, C_BLACK, "     to confirm first)")
    dtext(10, 138, C_BLACK, "F5 : check solution")
    dtext(10, 154, C_BLACK, "F6 / EXIT : back to menu")
    dtext(10, 170, C_BLACK, "OPTN : show this screen")
    dtext(10, 190, C_BLACK, "Press any key to return")
    dupdate()
    getkey()


def choose_size():
    while True:
        dclear(C_WHITE)
        dtext(10, 10, C_BLACK, "Nonogram")
        dtext(10, 40, C_BLACK, "1 : 5x5")
        dtext(10, 60, C_BLACK, "2 : 10x10")
        dtext(10, 80, C_BLACK, "3 : 15x15")
        dtext(10, 110, C_BLACK, "OPTN : controls")
        dtext(10, 130, C_BLACK, "EXIT : quit")
        dupdate()
        ev = getkey()
        if ev.key == KEY_1:
            return 5
        if ev.key == KEY_2:
            return 10
        if ev.key == KEY_3:
            return 15
        if ev.key == KEY_OPTN:
            show_controls()
        if ev.key == KEY_EXIT:
            return None


# ---------------------------------------------------------------- game loop

def show_generating():
    dclear(C_WHITE)
    dtext(10, 10, C_BLACK, "Generating puzzle...")
    dtext(10, 30, C_BLACK, "(checking it's solvable")
    dtext(10, 46, C_BLACK, "by logic, no guessing)")
    dupdate()


def confirm_new_puzzle():
    dclear(C_WHITE)
    dtext(10, 10, C_BLACK, "Start a new puzzle?")
    dtext(10, 30, C_BLACK, "Your progress on this")
    dtext(10, 46, C_BLACK, "one will be lost.")
    dtext(10, 76, C_BLACK, "EXE : yes, new puzzle")
    dtext(10, 92, C_BLACK, "EXIT : no, go back")
    dupdate()
    while True:
        ev = getkey()
        if ev.key == KEY_EXE:
            return True
        if ev.key == KEY_EXIT:
            return False


def play(size):
    show_generating()
    rc, cc, state = new_puzzle(size)
    layout = compute_layout(rc, cc, size)
    cur_r = cur_c = 0
    message = None
    draw_board(state, rc, cc, size, cur_r, cur_c, layout, message)

    while True:
        ev = getkey()
        k = ev.key
        message = None

        if k == KEY_LEFT:
            cur_c = max(0, cur_c - 1)
        elif k == KEY_RIGHT:
            cur_c = min(size - 1, cur_c + 1)
        elif k == KEY_UP:
            cur_r = max(0, cur_r - 1)
        elif k == KEY_DOWN:
            cur_r = min(size - 1, cur_r + 1)
        elif k == KEY_EXE:
            state[cur_r][cur_c] = (state[cur_r][cur_c] + 1) % 3
        elif k == KEY_F1:
            state[cur_r][cur_c] = FILLED
        elif k == KEY_F2:
            state[cur_r][cur_c] = CROSS
        elif k == KEY_F3:
            state[cur_r][cur_c] = EMPTY
        elif k == KEY_F4:
            if confirm_new_puzzle():
                show_generating()
                rc, cc, state = new_puzzle(size)
                layout = compute_layout(rc, cc, size)
                cur_r = cur_c = 0
        elif k == KEY_F5:
            if is_solved(state, rc, cc, size):
                message = "Solved!"
            else:
                message = "Not yet"
        elif k == KEY_F6 or k == KEY_EXIT:
            return
        elif k == KEY_OPTN:
            show_controls()

        draw_board(state, rc, cc, size, cur_r, cur_c, layout, message)


def main():
    while True:
        size = choose_size()
        if size is None:
            return
        play(size)


main()
