# -*- coding: utf-8 -*-
"""
GUANDAN (Tuo La Ji) -- pass-and-play, Casio fx-CG50, PythonExtra + gint.
"""

import random

try:
    from gint import *
    ON_CALC = True
except ImportError:
    ON_CALC = False


# ============== CORE LOGIC ==============

SUIT_NAMES = ['S', 'H', 'D', 'C']
SUIT_COLOR_IS_RED = [False, True, True, False]


def rank_name(rank):
    if rank == 15: return "sJ"
    if rank == 16: return "BJ"
    if rank == 14: return "A"
    if rank == 13: return "K"
    if rank == 12: return "Q"
    if rank == 11: return "J"
    return str(rank)


def rank_char(rank):
    if rank == 15: return "s"
    if rank == 16: return "B"
    if rank == 14: return "A"
    if rank == 13: return "K"
    if rank == 12: return "Q"
    if rank == 11: return "J"
    if rank == 10: return "T"
    return str(rank)


def card_name(card):
    r, s = card
    if r >= 15: return rank_name(r)
    return rank_name(r) + SUIT_NAMES[s]


def _shuffle(seq):
    for i in range(len(seq) - 1, 0, -1):
        j = int(random.random() * (i + 1))
        if j > i: j = i
        seq[i], seq[j] = seq[j], seq[i]


def build_deck():
    deck = []
    for _copy in range(2):
        for s in range(4):
            for r in range(2, 15):
                deck.append((r, s))
        deck.append((15, -1))
        deck.append((16, -1))
    return deck


def keyval(rank, level):
    if rank == 15: return 101
    if rank == 16: return 102
    if rank == level: return 100
    return rank


def is_wildcard(card, level):
    r, s = card
    return r == level and s == 1


def _classify_no_wild(cards, level):
    n = len(cards)
    if n == 0:
        return None
    ranks = sorted(c[0] for c in cards)
    counts = {}
    for r in ranks:
        counts[r] = counts.get(r, 0) + 1
    distinct = sorted(counts.keys())
    countvals = sorted(counts.values())

    if n == 4 and counts.get(15, 0) == 2 and counts.get(16, 0) == 2:
        return ('jokerbomb', 999, n)
    if len(distinct) == 1 and 4 <= n <= 10 and distinct[0] < 15:
        r = distinct[0]
        return ('bomb', (n, keyval(r, level)), n)
    if n >= 5 and len(distinct) == n and 15 not in ranks and 16 not in ranks:
        suits = set(c[1] for c in cards)
        if len(suits) == 1 and distinct == list(range(distinct[0], distinct[0] + n)) \
                and distinct[0] >= 3 and distinct[-1] <= 14:
            return ('straightflush', (n, distinct[-1]), n)
    if n == 1:
        return ('single', keyval(ranks[0], level), n)
    if n == 2 and len(distinct) == 1 and distinct[0] < 15:
        return ('pair', keyval(distinct[0], level), n)
    if n == 3 and len(distinct) == 1 and distinct[0] < 15:
        return ('triple', keyval(distinct[0], level), n)
    if n == 5 and countvals == [2, 3]:
        triple_rank = [r for r, c in counts.items() if c == 3][0]
        return ('fullhouse', keyval(triple_rank, level), n)
    if n >= 5 and len(distinct) == n and 15 not in ranks and 16 not in ranks:
        if distinct == list(range(distinct[0], distinct[0] + n)) \
                and distinct[0] >= 3 and distinct[-1] <= 14:
            return ('straight', (n, distinct[-1]), n)
    if n >= 6 and n % 2 == 0 and all(c == 2 for c in countvals) \
            and len(distinct) == n // 2 and 15 not in ranks and 16 not in ranks:
        if distinct == list(range(distinct[0], distinct[0] + len(distinct))) \
                and distinct[0] >= 3 and distinct[-1] <= 14:
            return ('tractor', (len(distinct), distinct[-1]), n)
    if n >= 6 and n % 3 == 0 and all(c == 3 for c in countvals) \
            and len(distinct) == n // 3 and 15 not in ranks and 16 not in ranks:
        if distinct == list(range(distinct[0], distinct[0] + len(distinct))) \
                and distinct[0] >= 3 and distinct[-1] <= 14:
            return ('airplane', (len(distinct), distinct[-1]), n)
    return None


def _combo_key(combo):
    typ, val, n = combo
    if typ == 'jokerbomb':     return (5, 0, 0)
    if typ == 'bomb':
        v = val[1] if isinstance(val, tuple) else val
        return (4, n, v)
    if typ == 'straightflush':
        return (3, val[0], val[1])
    v = val[1] if isinstance(val, tuple) else val
    return (2, n, v)


def classify(cards, level):
    best = _classify_no_wild(cards, level)
    wilds = [c for c in cards if is_wildcard(c, level)]
    if not wilds:
        return best
    base = [c for c in cards if not is_wildcard(c, level)]
    n_wild = len(wilds)
    if n_wild == 1:
        for r in range(2, 15):
            for s in range(4):
                combo = _classify_no_wild(base + [(r, s)], level)
                if combo is not None and (best is None
                                          or _combo_key(combo) > _combo_key(best)):
                    best = combo
    elif n_wild == 2:
        for r1 in range(2, 15):
            for s1 in range(4):
                for r2 in range(2, 15):
                    for s2 in range(4):
                        combo = _classify_no_wild(base + [(r1, s1), (r2, s2)], level)
                        if combo is not None and (best is None
                                                  or _combo_key(combo) > _combo_key(best)):
                            best = combo
    return best


def is_bomb(combo):
    return combo is not None and combo[0] in ('bomb', 'straightflush', 'jokerbomb')


def bomb_tier(combo):
    typ, val, n = combo
    if typ == 'jokerbomb':     return (9999, 0)
    if typ == 'straightflush': return (55, val[1])
    if typ == 'bomb':          return (n * 10, val[1])
    return (-1, -1)


def _rankpart(combo):
    v = combo[1]
    return v if isinstance(v, int) else v[1]


def can_play(new_combo, table_combo):
    if new_combo is None: return False
    if table_combo is None: return True
    n_bomb = is_bomb(new_combo)
    t_bomb = is_bomb(table_combo)
    if n_bomb and not t_bomb: return True
    if n_bomb and t_bomb:     return bomb_tier(new_combo) > bomb_tier(table_combo)
    if (not n_bomb) and t_bomb: return False
    if new_combo[0] != table_combo[0]: return False
    if new_combo[2] != table_combo[2]: return False
    return _rankpart(new_combo) > _rankpart(table_combo)


def sort_hand(hand, level):
    return sorted(hand, key=lambda c: (keyval(c[0], level), c[1]))


def sort_hand_display(hand, level):
    return sorted(hand, key=lambda c: (-keyval(c[0], level), c[1]))


def best_single(hand, level):
    return max(hand, key=lambda c: keyval(c[0], level))


def has_both_jokers(hand):
    ranks = [c[0] for c in hand]
    return 15 in ranks and 16 in ranks


class Game:
    def __init__(self, tribute_enabled):
        self.tribute_enabled = tribute_enabled
        self.level = [2, 2]
        self.round_leader = int(random.random() * 4)
        if self.round_leader > 3:
            self.round_leader = 3
        self.first_round = True
        self.winner_team = None
        self.hand_layouts = {}

    def team_of(self, player): return player % 2
    def level_of_player(self, player): return self.level[self.team_of(player)]

    def apply_result(self, finish_order):
        p1, p2, p3, p4 = finish_order
        team1 = self.team_of(p1)
        if self.team_of(p2) == team1:   gain = 3
        elif self.team_of(p3) == team1: gain = 2
        else:                           gain = 1
        old = self.level[team1]
        already_at_ace = (old >= 14)
        self.level[team1] = min(14, old + gain)
        if already_at_ace:
            self.winner_team = team1
        self.round_leader = p4
        self.first_round = False
        return gain, team1


def deal():
    deck = build_deck()
    _shuffle(deck)
    hands = [[], [], [], []]
    for i, card in enumerate(deck):
        hands[i % 4].append(card)
    return hands


def get_layout(game, player, hand, level):
    if player not in game.hand_layouts:
        sh = sort_hand_display(hand, level)
        game.hand_layouts[player] = [[c] for c in sh]
    layout = game.hand_layouts[player]
    hand_set = set(hand)
    new_layout = []
    for g in layout:
        survivors = [c for c in g if c in hand_set]
        if not survivors:
            continue
        if len(survivors) == len(g):
            new_layout.append(survivors)
        else:
            for c in survivors:
                new_layout.append([c])
    in_layout = set()
    for g in new_layout:
        for c in g:
            in_layout.add(c)
    for c in hand:
        if c not in in_layout:
            new_layout.append([c])
    game.hand_layouts[player] = new_layout
    return new_layout


def run_round(game, hands, chooser, on_event=None):
    finished, finished_set = [], set()
    table_combo = None
    table_cards = None
    table_owner = None
    last_actions = {}
    passes_in_row = 0
    target_passes = 0
    turn = game.round_leader

    def next_active(p):
        p = (p + 1) % 4
        while p in finished_set:
            p = (p + 1) % 4
        return p

    while len(finished_set) < 3:
        must_play = (table_combo is None)
        result = chooser(turn, hands[turn], table_cards, table_combo,
                         table_owner, last_actions, must_play)
        if result is not None:
            cards, combo = result
            for c in cards:
                hands[turn].remove(c)
            table_combo = combo
            table_cards = list(cards)
            table_owner = turn
            last_actions[turn] = ('play', list(cards), combo)
            passes_in_row = 0
            if on_event: on_event('play', turn, cards, combo)
            if len(hands[turn]) == 0:
                finished.append(turn)
                finished_set.add(turn)
                if on_event: on_event('finish', turn, None, None)
                if len(finished_set) >= 3: break
            active_count = 4 - len(finished_set)
            owner_still_active = table_owner not in finished_set
            target_passes = active_count - (1 if owner_still_active else 0)
            turn = next_active(turn)
        else:
            last_actions[turn] = ('pass', None, None)
            if on_event: on_event('pass', turn, None, None)
            passes_in_row += 1
            turn = next_active(turn)
            if passes_in_row >= target_passes:
                leader = table_owner
                if leader in finished_set or leader is None:
                    leader = next_active(table_owner if table_owner is not None else turn)
                table_combo = None
                table_cards = None
                table_owner = None
                last_actions = {}
                passes_in_row = 0
                target_passes = 0
                turn = leader

    for p in range(4):
        if p not in finished:
            finished.append(p)
            break
    return finished


def greedy_bot_choice(hand, table_combo, must_play, level):
    hand_sorted = sort_hand(hand, level)
    by_rank = {}
    for c in hand_sorted:
        by_rank.setdefault(c[0], []).append(c)
    groups = sorted(by_rank.items(), key=lambda kv: keyval(kv[0], level))

    def same_rank_option(n):
        for r, cards in groups:
            if len(cards) >= n and r < 15:
                combo_cards = cards[:n]
                c = classify(combo_cards, level)
                if c and can_play(c, table_combo):
                    return combo_cards, c
        return None

    def run_option(run_len, group_size):
        ranks_present = sorted(r for r in by_rank
                               if 3 <= r <= 14 and len(by_rank[r]) >= group_size)
        rp = set(ranks_present)
        for start in ranks_present:
            run = list(range(start, start + run_len))
            if all(r in rp for r in run):
                combo_cards = []
                for r in run:
                    combo_cards.extend(by_rank[r][:group_size])
                c = classify(combo_cards, level)
                if c and can_play(c, table_combo):
                    return combo_cards, c
        return None

    if must_play:
        for n in (1, 2, 3):
            r = same_rank_option(n)
            if r: return r
        r = run_option(5, 1)
        if r: return r
        for n in (4, 5, 6, 7, 8, 9, 10):
            r = same_rank_option(n)
            if r: return r
        return [hand_sorted[0]], classify([hand_sorted[0]], level)
    else:
        typ, val, n = table_combo
        if typ in ('single', 'pair', 'triple'):
            r = same_rank_option(n)
            if r: return r
        elif typ == 'straight':
            r = run_option(n, 1)
            if r: return r
        elif typ == 'tractor':
            r = run_option(val[0], 2)
            if r: return r
        elif typ == 'airplane':
            r = run_option(val[0], 3)
            if r: return r
        for n2 in (4, 5, 6, 7, 8, 9, 10):
            r = same_rank_option(n2)
            if r and is_bomb(r[1]):
                return r
        return None


# ============== SELF-TEST (desktop only) ==============

if __name__ == "__main__" and not ON_CALC:
    random.seed(1234)

    def _unit_tests():
        assert classify([(5, 0)], 2)[0] == 'single'
        assert classify([(5, 0), (5, 1)], 2)[0] == 'pair'
        assert classify([(5, 0), (5, 1), (5, 2)], 2)[0] == 'triple'
        assert classify([(5, 0), (5, 1), (5, 2), (9, 0), (9, 1)], 2)[0] == 'fullhouse'
        assert classify([(3, 0), (4, 1), (5, 2), (6, 3), (7, 0)], 2)[0] == 'straight'
        assert classify([(3, 0), (3, 1), (4, 0), (4, 1), (5, 0), (5, 1)], 2)[0] == 'tractor'
        assert classify([(3, 0), (3, 1), (3, 2), (4, 0), (4, 1), (4, 2)], 2)[0] == 'airplane'
        assert classify([(5, 0), (5, 1), (5, 2), (5, 3)], 2)[0] == 'bomb'
        assert classify([(15, -1), (15, -1), (16, -1), (16, -1)], 2)[0] == 'jokerbomb'
        assert classify([(3, 0), (4, 0), (5, 0), (6, 0), (7, 0)], 2)[0] == 'straightflush'
        assert classify([(5, 0), (6, 1)], 2) is None
        assert keyval(2, 2) == 100 and keyval(14, 2) == 14 and keyval(15, 2) == 101
        b4 = classify([(5, 0), (5, 1), (5, 2), (5, 3)], 2)
        sf5 = classify([(3, 0), (4, 0), (5, 0), (6, 0), (7, 0)], 2)
        assert can_play(sf5, b4) is True
        assert bomb_tier(('bomb', (6, 10), 6)) > bomb_tier(sf5)
        assert bomb_tier(sf5) > bomb_tier(('bomb', (5, 10), 5))
        assert bomb_tier(('bomb', (9, 9), 9))  > bomb_tier(('bomb', (8, 9), 8))
        assert bomb_tier(('bomb', (10, 9), 10)) > bomb_tier(('bomb', (9, 9), 9))
        assert bomb_tier(('jokerbomb', 999, 4)) > bomb_tier(('bomb', (10, 9), 10))
        assert is_wildcard((5, 1), 5) is True
        assert is_wildcard((5, 0), 5) is False
        c = classify([(5, 1), (6, 0)], 5)
        assert c is not None and c[0] == 'pair'
        c = classify([(5, 1), (5, 0), (5, 2)], 5)
        assert c is not None and c[0] == 'triple'
        c = classify([(5, 1), (3, 0), (4, 0), (6, 0), (7, 0)], 5)
        assert c is not None and c[0] == 'straightflush'
        nine_cards = [(9, s) for s in range(4)] + [(9, s) for s in range(4)]
        c = classify(nine_cards + [(5, 1)], 5)
        assert c is not None and c[0] == 'bomb' and c[1][0] == 9
        c = classify(nine_cards + [(5, 1), (5, 1)], 5)
        assert c is not None and c[0] == 'bomb' and c[1][0] == 10
        assert is_wildcard((5, 1), 3) is False
        assert is_wildcard((3, 1), 3) is True
        print("Unit tests passed.")

    _unit_tests()

    print("Running offline round-flow self test...")
    for game_num in range(8):
        game = Game(tribute_enabled=False)
        rounds = 0
        while game.winner_team is None and rounds < 40:
            hands = deal()
            game.hand_layouts = {}
            level = game.level_of_player(game.round_leader)

            def chooser(player, hand, table_cards, table_combo, table_owner,
                        last_actions, must_play, _level=level):
                return greedy_bot_choice(hand, table_combo, must_play, _level)

            order = run_round(game, hands, chooser)
            assert sorted(order) == [0, 1, 2, 3]
            gain, team = game.apply_result(order)
            rounds += 1
        status = "WIN" if game.winner_team is not None else "cap reached"
        print("game %2d: %3d rounds, %s, levels=%s" % (game_num, rounds, status, game.level))
    print("Self test complete.")


# ============== CALCULATOR FRONT-END ==============

if ON_CALC:
    FG = C_BLACK
    BG = C_WHITE
    TEAM_COLOR = [C_BLUE, C_RED]

    try:
        YELLOW = C_RGB(255, 255, 0)
    except Exception:
        try:
            YELLOW = C_YELLOW
        except Exception:
            YELLOW = 0xFFE0   # RGB565 yellow

    # Lighter gray tint for selected cards.
    try:
        SELECTED_TINT = C_RGB(230, 230, 230)
    except Exception:
        SELECTED_TINT = 0xF79E   # very light gray RGB565

    RULES_PAGES = [
"""GUANDAN - RULES (1/7)

4 players, 2 fixed teams
(seats 0&2 vs seats 1&3).
2 decks (108 cards) are
dealt out completely, 27
cards per player.

Each team has a LEVEL,
starting at 2. The team's
level-rank card becomes a
super-high card, just
below the jokers, for
that round.
""",
"""RULES (2/7) - WILDCARD

The HEART card of the
level rank is a WILD
card. Example: level 5
=> 5H is wild.

It can stand in for any
card of rank 2..A, any
suit. It cannot stand
in for a joker.

When several readings
are possible, the game
picks the strongest.
""",
"""RULES (3/7) - COMBOS

Single, Pair, Triple,
Full House (3+2),
Straight (5+ in a row,
3..A, mixed suit),
Tractor (3+ consecutive
pairs),
Airplane (2+ consecutive
triples).
You must match the same
combo TYPE and LENGTH as
the card(s) on the table,
with a higher rank.
""",
"""RULES (4/7) - BOMBS

Bomb = 4-10 cards of one
rank. Straight Flush =
5+ same suit in a row.
Joker Bomb = all 4
jokers. Bombs beat ANY
non-bomb and any smaller
bomb.

Order (low to high):
4 < 5 < SF(5) < 6 < 7 <
8 < 9 < 10 < Joker Bomb.

9- and 10-bombs need
one or two wildcards.
""",
"""RULES (5/7) - PLAY

Play counterclockwise
(seat 1 -> 2 -> 3 -> 4 -> 1).
Each turn: play a legal
combo beating the table,
or pass. Once everyone
else has passed, the last
player to play leads a new
trick (table clears).
First 3 players to empty
their hand finish 1st-3rd;
the last player is 4th
automatically.
""",
"""RULES (6/7) - SCORING

1st+2nd same team: +3
levels. 1st+3rd: +2.
1st+4th: +1. Losers keep
their level and the 4th
place player leads next
round.
Reaching level ACE and
then winning a round wins
the match!
""",
"""RULES (7/7) - TRIBUTE

If tribute is ON: the
losing side's worst
player(s) give their
highest card to the
winner(s), who return a
low card (rank <=10) in
exchange. A losing side
holding BOTH jokers is
exempt from tribute.
""",
    ]

    def show_rules():
        page = 0
        n = len(RULES_PAGES)
        while True:
            dclear(BG)
            for i, line in enumerate(RULES_PAGES[page].split("\n")):
                dtext(4, 2 + i * 13, FG, line)
            dtext_opt(DWIDTH // 2, DHEIGHT - 14, FG, C_NONE,
                      DTEXT_CENTER, DTEXT_TOP,
                      "<LEFT %d/%d RIGHT> EXIT=back" % (page + 1, n), -1)
            dupdate()
            ev = getkey()
            if ev.key in (KEY_EXIT, KEY_F1): return
            elif ev.key in (KEY_RIGHT, KEY_DOWN): page = (page + 1) % n
            elif ev.key in (KEY_LEFT, KEY_UP): page = (page - 1) % n

    def show_controls():
        lines = [
            "CONTROLS",
            "",
            "LEFT/RIGHT: move cursor",
            "UP:         select card",
            "DOWN:       deselect card",
            "",
            "F2: group selected cards",
            "    (bomb -> left,",
            "     non-bomb -> right)",
            "F3: reset groupings",
            "F5: clear selection",
            "EXE: play selected cards",
            "F6: pass (when allowed)",
            "F1: show rules",
            "EXIT: quit the game",
        ]
        dclear(BG)
        for i, line in enumerate(lines):
            dtext(4, 2 + i * 13, FG, line)
        dtext_opt(DWIDTH // 2, DHEIGHT - 14, FG, C_NONE,
                  DTEXT_CENTER, DTEXT_TOP, "EXIT=back", -1)
        dupdate()
        while True:
            ev = getkey()
            if ev.key in (KEY_EXIT, KEY_OPTN):
                return

    def message_box(msg, y=None):
        if y is None:
            y = 100
        w = len(msg) * 7 + 16
        x = max(4, (DWIDTH - w) // 2)
        drect(x, y - 4, x + w, y + 14, C_WHITE)
        drect_border(x, y - 4, x + w, y + 14, C_NONE, 1, FG)
        dtext_opt(DWIDTH // 2, y, FG, C_NONE, DTEXT_CENTER, DTEXT_TOP, msg, -1)
        dupdate()

    def wait_any_key(msg=None, y=None):
        if msg:
            message_box(msg, y if y else 100)
        return getkey()

    CARD_W = 30
    CARD_H = 40
    CARD_ELEV = 14
    BASE_Y = 178
    GROUP_OFFSET = 12

    MINI_W = 18
    MINI_H = 26
    MINI_STEP_H = 14

    def card_color(card):
        r, s = card
        if r >= 15:
            return C_RED if r == 16 else FG
        return C_RED if SUIT_COLOR_IS_RED[s] else FG

    def draw_suit_icon(cx, cy, suit, color):
        if suit == 0:
            dpoly([cx, cy - 6, cx - 5, cy + 2, cx, cy + 1, cx + 5, cy + 2], color, color)
            drect(cx - 1, cy + 2, cx + 1, cy + 6, color)
        elif suit == 1:
            dcircle(cx - 2, cy - 2, 3, color, color)
            dcircle(cx + 2, cy - 2, 3, color, color)
            dpoly([cx - 5, cy - 1, cx + 5, cy - 1, cx, cy + 5], color, color)
        elif suit == 2:
            dpoly([cx, cy - 6, cx + 4, cy, cx, cy + 6, cx - 4, cy], color, color)
        elif suit == 3:
            dcircle(cx, cy - 3, 3, color, color)
            dcircle(cx - 3, cy + 1, 3, color, color)
            dcircle(cx + 3, cy + 1, 3, color, color)
            drect(cx - 1, cy + 3, cx + 1, cy + 6, color)

    def draw_mini_suit(cx, cy, suit, color):
        if suit == 0:
            dpoly([cx, cy - 4, cx - 4, cy + 1, cx, cy, cx + 4, cy + 1], color, color)
            drect(cx - 1, cy, cx + 1, cy + 4, color)
        elif suit == 1:
            dcircle(cx - 2, cy - 2, 2, color, color)
            dcircle(cx + 2, cy - 2, 2, color, color)
            dpoly([cx - 4, cy - 1, cx + 4, cy - 1, cx, cy + 3], color, color)
        elif suit == 2:
            dpoly([cx, cy - 4, cx + 3, cy, cx, cy + 4, cx - 3, cy], color, color)
        elif suit == 3:
            dcircle(cx, cy - 3, 2, color, color)
            dcircle(cx - 2, cy, 2, color, color)
            dcircle(cx + 2, cy, 2, color, color)
            drect(cx - 1, cy + 2, cx + 1, cy + 4, color)

    def draw_card(x, y, card, selected=False):
        r, s = card
        color = card_color(card)
        border = C_BLUE if selected else C_BLACK
        drect_border(x, y, x + CARD_W - 2, y + CARD_H, C_WHITE, 2, border)
        dtext(x + 3, y + 3, color, rank_name(r))
        if r < 15:
            draw_suit_icon(x + 9, y + CARD_H - 10, s, color)
        else:
            dtext(x + 3, y + CARD_H - 12, color, "*")

    def draw_card_loose(x, y, card, focused=False, selected=False):
        r, s = card
        color = card_color(card)
        fill = SELECTED_TINT if selected else C_WHITE
        border = C_GREEN if focused else C_BLACK
        drect_border(x, y, x + CARD_W - 2, y + CARD_H, fill, 2, border)
        dtext(x + 3, y + 3, color, rank_name(r))
        if r < 15:
            draw_suit_icon(x + 9, y + CARD_H - 10, s, color)
        else:
            dtext(x + 3, y + CARD_H - 12, color, "*")

    def draw_card_stacked(x, y, card, focused=False, selected=False):
        r, s = card
        color = card_color(card)
        if selected:
            fill = SELECTED_TINT
        elif focused:
            fill = YELLOW
        else:
            fill = C_WHITE
        drect_border(x, y, x + CARD_W - 2, y + CARD_H, fill, 2, FG)
        dtext(x + 3, y + 1, color, rank_name(r))
        if r < 15:
            draw_mini_suit(x + CARD_W - 8, y + 5, s, color)
        else:
            dtext(x + CARD_W - 12, y + 1, color, "*")

    def draw_mini_card(x, y, card):
        r, s = card
        color = card_color(card)
        drect_border(x, y, x + MINI_W, y + MINI_H, C_WHITE, 1, FG)
        dtext(x + 2, y + 2, color, rank_char(r))
        if s >= 0:
            draw_mini_suit(x + MINI_W // 2, y + MINI_H - 8, s, color)
        else:
            dtext(x + 4, y + 14, color, "*")

    def draw_action_h(cards, x, y):
        for i, c in enumerate(cards):
            draw_mini_card(x + i * MINI_STEP_H, y, c)

    def action_of(last_actions, p):
        a = last_actions.get(p)
        if a is None: return None
        if a[0] == 'pass': return 'PASS'
        return a[1]

    def draw_other_players(player, last_actions):
        teammate = (player + 2) % 4
        left_p = (player + 1) % 4
        right_p = (player - 1) % 4

        act = action_of(last_actions, teammate)
        dtext_opt(DWIDTH // 2, 14, TEAM_COLOR[teammate % 2], C_NONE,
                  DTEXT_CENTER, DTEXT_TOP,
                  "P%d (team)" % (teammate + 1), -1)
        if act == 'PASS':
            dtext_opt(DWIDTH // 2, 30, FG, C_NONE,
                      DTEXT_CENTER, DTEXT_TOP, "PASS", -1)
        elif act:
            total_w = MINI_W + (len(act) - 1) * MINI_STEP_H
            draw_action_h(act, DWIDTH // 2 - total_w // 2, 30)
        else:
            dtext_opt(DWIDTH // 2, 30, FG, C_NONE,
                      DTEXT_CENTER, DTEXT_TOP, "--", -1)

        act = action_of(last_actions, left_p)
        dtext(4, 66, TEAM_COLOR[left_p % 2], "P%d" % (left_p + 1))
        if act == 'PASS':
            dtext(4, 82, FG, "PASS")
        elif act:
            draw_action_h(act, 4, 82)
        else:
            dtext(4, 82, FG, "--")

        act = action_of(last_actions, right_p)
        dtext_opt(DWIDTH - 4, 66, TEAM_COLOR[right_p % 2], C_NONE,
                  DTEXT_RIGHT, DTEXT_TOP, "P%d" % (right_p + 1), -1)
        if act == 'PASS':
            dtext_opt(DWIDTH - 4, 82, FG, C_NONE,
                      DTEXT_RIGHT, DTEXT_TOP, "PASS", -1)
        elif act:
            total_w = MINI_W + (len(act) - 1) * MINI_STEP_H
            draw_action_h(act, DWIDTH - 4 - total_w, 82)
        else:
            dtext_opt(DWIDTH - 4, 82, FG, C_NONE,
                      DTEXT_RIGHT, DTEXT_TOP, "--", -1)

    def draw_center_table(table_cards, table_owner):
        y_cards = 82
        if not table_cards:
            dtext_opt(DWIDTH // 2, y_cards + 6, FG, C_NONE,
                      DTEXT_CENTER, DTEXT_TOP, "(empty)", -1)
            return
        total_w = MINI_W + (len(table_cards) - 1) * MINI_STEP_H
        x = DWIDTH // 2 - total_w // 2
        draw_action_h(table_cards, x, y_cards)
        if table_owner is not None:
            dtext_opt(DWIDTH // 2, y_cards + MINI_H + 2, FG, C_NONE,
                      DTEXT_CENTER, DTEXT_TOP,
                      "by P%d" % (table_owner + 1), -1)

    def compute_hand_positions(layout):
        """Compute X positions for each group. Gaps adjacent to a wide
        group (len > 1) get priority: they'll be at least CARD_W - 2 so
        the group never overlaps horizontally with its neighbours. Loose
        cards share whatever space is left."""
        n = len(layout)
        if n == 0:
            return []
        x0 = 4
        if n == 1:
            return [x0]
        full_gap = CARD_W - 2      # no overlap
        min_gap = 6                # extreme squeeze
        avail = DWIDTH - 8 - (CARD_W - 2)

        # Classify gaps: adjacent to a wide group -> fixed full_gap,
        # else flexible.
        gaps = []
        for i in range(n - 1):
            if len(layout[i]) > 1 or len(layout[i+1]) > 1:
                gaps.append(full_gap)
            else:
                gaps.append(-1)  # flexible placeholder

        fixed_total = sum(g for g in gaps if g > 0)
        n_flex = sum(1 for g in gaps if g < 0)
        remaining = avail - fixed_total
        if n_flex > 0:
            flex_gap = remaining // n_flex if remaining > 0 else min_gap
            if flex_gap > full_gap:
                flex_gap = full_gap
            if flex_gap < min_gap:
                flex_gap = min_gap
        else:
            flex_gap = full_gap
        gaps = [g if g > 0 else flex_gap for g in gaps]

        # If still doesn't fit, scale everything down proportionally.
        total = sum(gaps)
        if total > avail and total > 0:
            ratio = avail / total
            gaps = [max(4, int(g * ratio)) for g in gaps]

        positions = [x0]
        for g in gaps:
            positions.append(positions[-1] + g)
        return positions

    def hand_pass_screen(player, game=None, last_actions=None):
        dclear(BG)
        team = player % 2
        dtext_opt(DWIDTH // 2, 10, FG, C_NONE, DTEXT_CENTER, DTEXT_TOP,
                  "Pass the calculator to", -1)
        dtext_opt(DWIDTH // 2, 28, TEAM_COLOR[team], C_NONE, DTEXT_CENTER, DTEXT_TOP,
                  "P%d  (Team %s)" % (player + 1, "Blue" if team == 0 else "Red"), -1)
        if game is not None:
            dtext_opt(DWIDTH // 2, 48, TEAM_COLOR[0], C_NONE, DTEXT_CENTER, DTEXT_TOP,
                      "Blue Lv:%s" % rank_name(game.level[0]), -1)
            dtext_opt(DWIDTH // 2, 62, TEAM_COLOR[1], C_NONE, DTEXT_CENTER, DTEXT_TOP,
                      "Red Lv:%s" % rank_name(game.level[1]), -1)
        if last_actions:
            dtext(4, 84, FG, "Last actions:")
            y = 100
            for p in range(4):
                if p == player: continue
                dtext(4, y, TEAM_COLOR[p % 2], "P%d:" % (p + 1))
                act = action_of(last_actions, p)
                if act == 'PASS':
                    dtext(40, y, FG, "PASS")
                elif act:
                    draw_action_h(act, 40, y - 4)
                else:
                    dtext(40, y, FG, "--")
                y += 30
        dtext_opt(DWIDTH // 2, DHEIGHT - 18, FG, C_NONE, DTEXT_CENTER, DTEXT_TOP,
                  "EXE when ready", -1)
        dupdate()
        while True:
            ev = getkey()
            if ev.key == KEY_EXE: return

    def choose_and_play(player, hand, table_cards, table_combo, table_owner,
                        last_actions, must_play, level, game):
        layout = get_layout(game, player, hand, level)
        selected = [[False] * len(g) for g in layout]
        cursor = (0, 0)

        while True:
            if layout:
                gi, ci = cursor
                if gi >= len(layout): gi = len(layout) - 1
                if gi < 0: gi = 0
                if ci >= len(layout[gi]): ci = len(layout[gi]) - 1
                if ci < 0: ci = 0
                cursor = (gi, ci)

            dclear(BG)
            team = player % 2
            team_name = "Blue" if team == 0 else "Red"
            dtext_opt(DWIDTH // 2, 2, TEAM_COLOR[team], C_NONE,
                      DTEXT_CENTER, DTEXT_TOP,
                      "P%d (%s)" % (player + 1, team_name), -1)
            dtext_opt(4, 2, TEAM_COLOR[0], C_NONE, DTEXT_LEFT, DTEXT_TOP,
                      "B:%s" % rank_name(game.level[0]), -1)
            dtext_opt(DWIDTH - 4, 2, TEAM_COLOR[1], C_NONE, DTEXT_RIGHT, DTEXT_TOP,
                      "R:%s" % rank_name(game.level[1]), -1)

            draw_other_players(player, last_actions)
            draw_center_table(table_cards, table_owner)

            positions = compute_hand_positions(layout)
            n_groups = len(layout)

            for gi in range(n_groups):
                gx = positions[gi]
                group = layout[gi]
                n = len(group)
                for ci in range(n - 1, -1, -1):
                    cy = BASE_Y - ci * GROUP_OFFSET
                    is_focused = (gi == cursor[0] and ci == cursor[1])
                    is_selected = selected[gi][ci]
                    if n == 1:
                        cy = BASE_Y - (CARD_ELEV if is_selected else 0)
                        draw_card_loose(gx, cy, group[ci], is_focused, is_selected)
                    else:
                        draw_card_stacked(gx, cy, group[ci], is_focused, is_selected)

            dupdate()

            ev = getkey()
            if ev.key == KEY_LEFT:
                gi, ci = cursor
                if ci > 0:
                    ci -= 1
                elif gi > 0:
                    gi -= 1
                    ci = len(layout[gi]) - 1
                else:
                    gi = len(layout) - 1
                    ci = len(layout[gi]) - 1
                cursor = (gi, ci)
            elif ev.key == KEY_RIGHT:
                gi, ci = cursor
                if ci < len(layout[gi]) - 1:
                    ci += 1
                elif gi < len(layout) - 1:
                    gi += 1
                    ci = 0
                else:
                    gi = 0
                    ci = 0
                cursor = (gi, ci)
            elif ev.key == KEY_UP:
                gi, ci = cursor
                selected[gi][ci] = True
            elif ev.key == KEY_DOWN:
                gi, ci = cursor
                selected[gi][ci] = False
            elif ev.key == KEY_F5:
                selected = [[False] * len(g) for g in layout]
            elif ev.key == KEY_F1:
                show_rules()
            elif ev.key == KEY_OPTN:
                show_controls()
            elif ev.key == KEY_F2:
                sel_cards = []
                for gi2 in range(len(layout)):
                    for ci2 in range(len(layout[gi2])):
                        if selected[gi2][ci2]:
                            sel_cards.append(layout[gi2][ci2])
                if not sel_cards:
                    wait_any_key("Select cards first!", 100)
                    continue
                combo = classify(sel_cards, level)
                if combo is None:
                    wait_any_key("Not a legal combo!", 100)
                    continue
                sel_set = set(sel_cards)
                new_layout = []
                for g in layout:
                    survivors = [c for c in g if c not in sel_set]
                    if survivors:
                        new_layout.append(survivors)
                new_group = sorted(sel_cards, key=lambda c: (keyval(c[0], level), c[1]))
                if is_bomb(combo):
                    new_layout.insert(0, new_group)
                else:
                    new_layout.append(new_group)
                layout = new_layout
                selected = [[False] * len(g) for g in layout]
                cursor = (0, 0)
                game.hand_layouts[player] = layout
            elif ev.key == KEY_F3:
                sh = sort_hand_display(hand, level)
                layout = [[c] for c in sh]
                selected = [[False] * len(g) for g in layout]
                cursor = (0, 0)
                game.hand_layouts[player] = layout
            elif ev.key == KEY_F6:
                if not must_play:
                    game.hand_layouts[player] = layout
                    return None
                else:
                    wait_any_key("You must play!", 100)
            elif ev.key == KEY_EXIT:
                if confirm_quit():
                    raise SystemExit
            elif ev.key == KEY_EXE:
                chosen = []
                for gi2 in range(len(layout)):
                    for ci2 in range(len(layout[gi2])):
                        if selected[gi2][ci2]:
                            chosen.append(layout[gi2][ci2])
                combo = classify(chosen, level)
                if combo is None:
                    wait_any_key("Not a legal combo!", 100)
                    continue
                if not can_play(combo, table_combo):
                    wait_any_key("Doesn't beat the table!", 100)
                    continue
                game.hand_layouts[player] = layout
                return chosen, combo

    def confirm_quit():
        dclear(BG)
        dtext_opt(DWIDTH // 2, 80, FG, C_NONE, DTEXT_CENTER, DTEXT_TOP,
                  "Quit the whole game?", -1)
        dtext_opt(DWIDTH // 2, 110, FG, C_NONE, DTEXT_CENTER, DTEXT_TOP,
                  "EXE = yes, EXIT = no", -1)
        dupdate()
        while True:
            ev = getkey()
            if ev.key == KEY_EXE: return True
            if ev.key == KEY_EXIT: return False

    def do_tribute(game, hands, order_prev):
        p1, p2, p3, p4 = order_prev
        team1 = game.team_of(p1)
        double_down = (game.team_of(p2) == team1)

        givers_receivers = []
        if double_down:
            if not has_both_jokers(hands[p4]):
                givers_receivers.append((p4, p1))
            if not has_both_jokers(hands[p3]):
                givers_receivers.append((p3, p2))
        else:
            if not has_both_jokers(hands[p4]):
                givers_receivers.append((p4, p1))

        if not givers_receivers:
            dclear(BG)
            dtext_opt(DWIDTH // 2, 90, FG, C_NONE, DTEXT_CENTER, DTEXT_TOP,
                      "No tribute owed", -1)
            wait_any_key("Press any key", DHEIGHT - 24)
            return

        for giver, receiver in givers_receivers:
            level_g = game.level_of_player(giver)
            card = best_single(hands[giver], level_g)
            hand_pass_screen(giver, game)
            dclear(BG)
            dtext_opt(DWIDTH // 2, 40, FG, C_NONE, DTEXT_CENTER, DTEXT_TOP,
                      "P%d owes tribute" % (giver + 1), -1)
            dtext_opt(DWIDTH // 2, 65, FG, C_NONE, DTEXT_CENTER, DTEXT_TOP,
                      "Highest card:", -1)
            draw_card(DWIDTH // 2 - CARD_W // 2, 85, card, False)
            wait_any_key("EXE to hand over", DHEIGHT - 20)
            hands[giver].remove(card)
            hands[receiver].append(card)
            hand_pass_screen(receiver, game)
            level_r = game.level_of_player(receiver)
            eligible = [c for c in hands[receiver] if c[0] <= 10]
            if not eligible:
                eligible = sort_hand(hands[receiver], level_r)[:1]
            eligible = sorted(eligible, key=lambda c: (keyval(c[0], level_r), c[1]))
            cursor = 0
            while True:
                dclear(BG)
                dtext_opt(DWIDTH // 2, 6, FG, C_NONE, DTEXT_CENTER, DTEXT_TOP,
                          "P%d: return a card" % (receiver + 1), -1)
                for i, c in enumerate(eligible):
                    draw_card(10 + i * (CARD_W + 2), 90, c, i == cursor)
                dtext(4, DHEIGHT - 16, FG, "LEFT/RIGHT, EXE=confirm")
                dupdate()
                ev = getkey()
                if ev.key == KEY_LEFT:
                    cursor = (cursor - 1) % len(eligible)
                elif ev.key == KEY_RIGHT:
                    cursor = (cursor + 1) % len(eligible)
                elif ev.key == KEY_EXE:
                    ret = eligible[cursor]
                    hands[receiver].remove(ret)
                    hands[giver].append(ret)
                    break

    def show_round_result(order, gain, team):
        dclear(BG)
        placenames = ["1st", "2nd", "3rd", "4th"]
        dtext_opt(DWIDTH // 2, 6, FG, C_NONE, DTEXT_CENTER, DTEXT_TOP, "ROUND OVER", -1)
        for i, p in enumerate(order):
            col = TEAM_COLOR[p % 2]
            dtext(20, 30 + i * 18, col, "%s: P%d (%s)" %
                  (placenames[i], p + 1, "Blue" if p % 2 == 0 else "Red"))
        dtext_opt(DWIDTH // 2, 120, FG, C_NONE, DTEXT_CENTER, DTEXT_TOP,
                  "Team %s +%d levels" % ("Blue" if team == 0 else "Red", gain), -1)
        wait_any_key("Press any key", DHEIGHT - 20)

    def show_game_over(game):
        dclear(BG)
        team = game.winner_team
        dtext_opt(DWIDTH // 2, 70, TEAM_COLOR[team], C_NONE, DTEXT_CENTER, DTEXT_TOP,
                  "TEAM %s WINS!" % ("BLUE" if team == 0 else "RED"), -1)
        dtext_opt(DWIDTH // 2, 100, FG, C_NONE, DTEXT_CENTER, DTEXT_TOP,
                  "(players %s)" % ("1 & 3" if team == 0 else "2 & 4"), -1)
        dtext_opt(DWIDTH // 2, DHEIGHT - 20, FG, C_NONE, DTEXT_CENTER, DTEXT_TOP,
                  "EXIT to quit", -1)
        dupdate()
        while True:
            ev = getkey()
            if ev.key == KEY_EXIT: return

    def draw_title(choice_tribute):
        dclear(BG)
        dtext_opt(DWIDTH // 2, 10, FG, C_NONE, DTEXT_CENTER, DTEXT_TOP, "GUANDAN", -1)
        dtext_opt(DWIDTH // 2, 32, FG, C_NONE, DTEXT_CENTER, DTEXT_TOP,
                  "pass-and-play, 4 players", -1)
        dtext_opt(DWIDTH // 2, 70, FG, C_NONE, DTEXT_CENTER, DTEXT_TOP,
                  "Play WITH tribute rules?", -1)

        def opt_box(x, w, label, selected):
            color = C_BLUE if selected else FG
            drect_border(x, 95, x + w, 125, C_NONE, 2, color)
            dtext_opt(x + w // 2, 103, color, C_NONE, DTEXT_CENTER, DTEXT_TOP, label, -1)

        opt_box(30, 110, "NO", not choice_tribute)
        opt_box(DWIDTH - 140, 110, "YES", choice_tribute)
        dtext_opt(DWIDTH // 2, 140, FG, C_NONE, DTEXT_CENTER, DTEXT_TOP,
                  "LEFT/RIGHT choose, EXE=go", -1)
        dtext_opt(DWIDTH // 2, 160, FG, C_NONE, DTEXT_CENTER, DTEXT_TOP,
                  "F1 rules  OPTN controls", -1)
        dupdate()

    def ask_tribute():
        choice = False
        while True:
            draw_title(choice)
            ev = getkey()
            if ev.key == KEY_F1:
                show_rules()
            elif ev.key == KEY_OPTN:
                show_controls()
            elif ev.key in (KEY_LEFT, KEY_RIGHT):
                choice = not choice
            elif ev.key == KEY_EXE:
                return choice
            elif ev.key == KEY_EXIT:
                return False

    def main():
        tribute_enabled = ask_tribute()
        game = Game(tribute_enabled)
        prev_order = None

        while game.winner_team is None:
            hands = deal()
            game.hand_layouts = {}
            if tribute_enabled and not game.first_round and prev_order is not None:
                do_tribute(game, hands, prev_order)
            level = game.level_of_player(game.round_leader)

            def chooser(player, hand, table_cards, table_combo, table_owner,
                        last_actions, must_play, _level=level):
                hand_pass_screen(player, game, last_actions)
                return choose_and_play(player, hand, table_cards, table_combo,
                                       table_owner, last_actions, must_play,
                                       _level, game)

            order = run_round(game, hands, chooser)
            gain, team = game.apply_result(order)
            show_round_result(order, gain, team)
            prev_order = order

        show_game_over(game)

    try:
        main()
    except SystemExit:
        pass