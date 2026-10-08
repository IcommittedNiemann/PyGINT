# -*- coding: utf-8 -*-
"""
GUANDAN -- pass-and-play, Casio fx-CG50, PythonExtra + gint.
Version 3.4.
"""

import random

try:
    from gint import *
    ON_CALC = True
except ImportError:
    ON_CALC = False


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
    r = card[0]
    if r >= 15:
        return rank_name(r)
    return rank_name(r) + SUIT_NAMES[card[1]]


def _shuffle(seq):
    for i in range(len(seq) - 1, 0, -1):
        j = int(random.random() * (i + 1))
        if j > i: j = i
        seq[i], seq[j] = seq[j], seq[i]


def build_deck():
    deck = []
    uid = 0
    for _copy in range(2):
        for s in range(4):
            for r in range(2, 15):
                deck.append((r, s, uid))
                uid += 1
        deck.append((15, -1, uid)); uid += 1
        deck.append((16, -1, uid)); uid += 1
    return deck


def keyval(rank, level):
    if rank == 15: return 101
    if rank == 16: return 102
    if rank == level: return 100
    return rank


def is_wildcard(card, level):
    return card[0] == level and card[1] == 1


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


_classify_cache = {}
_NONE_SENTINEL = object()


def _classify_impl(cards, level):
    best = _classify_no_wild(cards, level)
    wilds = [c for c in cards if is_wildcard(c, level)]
    if not wilds:
        return best
    base = [c for c in cards if not is_wildcard(c, level)]
    n_wild = len(wilds)

    if n_wild == 1:
        for r in range(2, 15):
            for s in range(4):
                combo = _classify_no_wild(base + [(r, s, -1)], level)
                if combo is not None and (best is None
                                          or _combo_key(combo) > _combo_key(best)):
                    best = combo

    elif n_wild == 2:
        for r in range(2, 15):
            combo = _classify_no_wild(
                base + [(r, 0, -1), (r, 0, -2)], level)
            if combo is not None and (best is None
                                      or _combo_key(combo) > _combo_key(best)):
                best = combo
        for r1 in range(2, 15):
            for r2 in range(r1 + 1, 15):
                combo = _classify_no_wild(
                    base + [(r1, 0, -1), (r2, 0, -2)], level)
                if combo is not None and (best is None
                                          or _combo_key(combo) > _combo_key(best)):
                    best = combo
        if best is None or not is_bomb(best):
            suit_count = {}
            for c in base:
                suit_count[c[1]] = suit_count.get(c[1], 0) + 1
            for s, count in suit_count.items():
                if count >= 3:
                    for r1 in range(2, 15):
                        for r2 in range(r1, 15):
                            combo = _classify_no_wild(
                                base + [(r1, s, -1), (r2, s, -2)], level)
                            if combo is not None and (best is None
                                                      or _combo_key(combo) > _combo_key(best)):
                                best = combo
    return best


def classify(cards, level):
    key = (level, tuple(sorted((c[0], c[1]) for c in cards)))
    cached = _classify_cache.get(key, _NONE_SENTINEL)
    if cached is not _NONE_SENTINEL:
        return cached
    result = _classify_impl(cards, level)
    if len(_classify_cache) >= 200:
        _classify_cache.clear()
    _classify_cache[key] = result
    return result


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
        self.active_level = 2
        self.active_team = 0
        self.round_leader = int(random.random() * 4)
        if self.round_leader > 3:
            self.round_leader = 3
        self.first_round = True
        self.winner_team = None
        self.hand_layouts = {}
        self.seats = ['HUMAN', 'HUMAN', 'HUMAN', 'HUMAN']
        self.skip_prompt_shown = False
        self.skip_mode = False

    def team_of(self, player):
        return player % 2

    def level_of_player(self, player):
        return self.level[self.team_of(player)]

    def player_is_bot(self, player):
        return self.seats[player] != 'HUMAN'

    def apply_result(self, finish_order):
        p1, p2, p3, p4 = finish_order
        team1 = self.team_of(p1)
        if self.team_of(p2) == team1:   gain = 3
        elif self.team_of(p3) == team1: gain = 2
        else:                           gain = 1
        old = self.level[team1]
        already_at_ace = (old >= 14)
        self.level[team1] = min(14, old + gain)
        self.active_level = self.level[team1]
        self.active_team = team1
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


def _group_by_rank(hand, level):
    by_rank = {}
    for c in hand:
        by_rank.setdefault(c[0], []).append(c)
    for r in by_rank:
        by_rank[r].sort(key=lambda c: c[1])
    return sorted(by_rank.items(), key=lambda kv: keyval(kv[0], level))


def _same_type_follows(groups, table_combo, level):
    typ, val, n = table_combo
    by_rank = {r: cards for r, cards in groups}
    results = []
    if typ in ('single', 'pair', 'triple'):
        for r, cards in groups:
            if len(cards) >= n and r < 15:
                cc = cards[:n]
                combo = classify(cc, level)
                if combo and can_play(combo, table_combo):
                    results.append((cc, combo))
    elif typ == 'straight':
        for start in range(3, 15 - n + 1):
            run = list(range(start, start + n))
            if all(r in by_rank and len(by_rank[r]) >= 1 for r in run):
                cc = [by_rank[r][0] for r in run]
                combo = classify(cc, level)
                if combo and can_play(combo, table_combo):
                    results.append((cc, combo))
    elif typ == 'tractor':
        rl = val[0]
        for start in range(3, 15 - rl + 1):
            run = list(range(start, start + rl))
            if all(r in by_rank and len(by_rank[r]) >= 2 for r in run):
                cc = []
                for r in run:
                    cc.extend(by_rank[r][:2])
                combo = classify(cc, level)
                if combo and can_play(combo, table_combo):
                    results.append((cc, combo))
    elif typ == 'airplane':
        rl = val[0]
        for start in range(3, 15 - rl + 1):
            run = list(range(start, start + rl))
            if all(r in by_rank and len(by_rank[r]) >= 3 for r in run):
                cc = []
                for r in run:
                    cc.extend(by_rank[r][:3])
                combo = classify(cc, level)
                if combo and can_play(combo, table_combo):
                    results.append((cc, combo))
    elif typ == 'fullhouse':
        for r3, c3 in groups:
            if len(c3) >= 3 and r3 < 15:
                for r2, c2 in groups:
                    if r2 != r3 and len(c2) >= 2 and r2 < 15:
                        cc = c3[:3] + c2[:2]
                        combo = classify(cc, level)
                        if combo and can_play(combo, table_combo):
                            results.append((cc, combo))
    return results


def _bomb_plays(groups, level):
    results = []
    for r, cards in groups:
        if len(cards) >= 4 and r < 15:
            cc = list(cards)
            combo = classify(cc, level)
            if combo and combo[0] == 'bomb':
                results.append((cc, combo))
    js = [c for r, cs in groups if r == 15 for c in cs]
    jb = [c for r, cs in groups if r == 16 for c in cs]
    if len(js) >= 2 and len(jb) >= 2:
        cc = js[:2] + jb[:2]
        combo = classify(cc, level)
        if combo and combo[0] == 'jokerbomb':
            results.append((cc, combo))
    return results


def _play_cost(cards, level):
    total = 0
    for c in cards:
        r = c[0]
        if r == 16:      total += 50
        elif r == 15:    total += 40
        elif r == level: total += 30
        elif r == 14:    total += 20
        elif r >= 12:    total += 10
        elif r >= 10:    total += 5
        else:            total += 1
    return total


def bot_b_choice(hand, table_combo, must_play, level, last_actions,
                 table_owner, player, hand_sizes, game):
    groups = _group_by_rank(hand, level)
    by_rank = {r: cards for r, cards in groups}

    if must_play:
        for n in (1, 2, 3):
            for r, cards in groups:
                if len(cards) >= n and r < 15:
                    cc = cards[:n]
                    combo = classify(cc, level)
                    if combo:
                        return cc, combo
        for rl, gs in ((5, 1), (3, 2), (2, 3)):
            for start in range(3, 15 - rl + 1):
                run = list(range(start, start + rl))
                if all(r in by_rank and len(by_rank[r]) >= gs for r in run):
                    cc = []
                    for r in run:
                        cc.extend(by_rank[r][:gs])
                    combo = classify(cc, level)
                    if combo:
                        return cc, combo
        bombs = _bomb_plays(groups, level)
        if bombs:
            return bombs[0]
        hand_sorted = sort_hand(hand, level)
        return [hand_sorted[0]], classify([hand_sorted[0]], level)

    follows = _same_type_follows(groups, table_combo, level)
    if follows:
        follows.sort(key=lambda x: _play_cost(x[0], level))
        return follows[0]

    opponent_min = min((hand_sizes[p] for p in range(4)
                        if p != player and game.team_of(p) != game.team_of(player)),
                       default=99)
    if opponent_min <= 3 or len(hand) <= 5:
        bombs = _bomb_plays(groups, level)
        valid = [(cc, combo) for cc, combo in bombs if can_play(combo, table_combo)]
        if valid:
            valid.sort(key=lambda x: bomb_tier(x[1]))
            return valid[0]
    return None


def bot_c_choice(hand, table_combo, must_play, level, last_actions,
                 table_owner, player, hand_sizes, game):
    groups = _group_by_rank(hand, level)
    by_rank = {r: cards for r, cards in groups}
    partner = (player + 2) % 4

    if must_play:
        leads = []
        for n in (1, 2, 3):
            for r, cards in groups:
                if len(cards) >= n and r < 15:
                    cc = cards[:n]
                    combo = classify(cc, level)
                    if combo:
                        leads.append((cc, combo, _play_cost(cc, level) - n * 2))
        for rl, gs in ((5, 1), (3, 2), (2, 3)):
            for start in range(3, 15 - rl + 1):
                run = list(range(start, start + rl))
                if all(r in by_rank and len(by_rank[r]) >= gs for r in run):
                    cc = []
                    for r in run:
                        cc.extend(by_rank[r][:gs])
                    combo = classify(cc, level)
                    if combo:
                        leads.append((cc, combo,
                                      _play_cost(cc, level) - len(cc) * 2))
                    break
        if leads:
            leads.sort(key=lambda x: x[2])
            return leads[0][0], leads[0][1]
        hand_sorted = sort_hand(hand, level)
        return [hand_sorted[0]], classify([hand_sorted[0]], level)

    partner_owns = (table_owner == partner)
    follows = _same_type_follows(groups, table_combo, level)

    if partner_owns:
        if follows:
            follows.sort(key=lambda x: _play_cost(x[0], level))
            cc, combo = follows[0]
            if _play_cost(cc, level) <= 3:
                return cc, combo
        return None

    opponent_min = min((hand_sizes[p] for p in range(4)
                        if p != player and game.team_of(p) != game.team_of(player)),
                       default=99)

    if follows:
        follows.sort(key=lambda x: _play_cost(x[0], level))
        if opponent_min <= 2 and len(follows) > 1:
            follows.sort(key=lambda x: -_play_cost(x[0], level))
            return follows[0]
        return follows[0]

    should_bomb = (opponent_min <= 3) or (len(hand) <= 5)
    if should_bomb:
        bombs = _bomb_plays(groups, level)
        valid = [(cc, combo) for cc, combo in bombs if can_play(combo, table_combo)]
        if valid:
            valid.sort(key=lambda x: bomb_tier(x[1]))
            return valid[0]
    return None


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


if __name__ == "__main__" and not ON_CALC:
    random.seed(1234)

    def _unit_tests():
        T = lambda r, s, u=0: (r, s, u)
        assert classify([T(5, 0)], 2)[0] == 'single'
        assert classify([T(5, 0), T(5, 1)], 2)[0] == 'pair'
        assert classify([T(5, 0), T(5, 1), T(5, 2)], 2)[0] == 'triple'
        assert classify([T(5, 0), T(5, 1), T(5, 2), T(9, 0), T(9, 1)], 2)[0] == 'fullhouse'
        assert classify([T(3, 0), T(4, 1), T(5, 2), T(6, 3), T(7, 0)], 2)[0] == 'straight'
        assert classify([T(3, 0), T(3, 1), T(4, 0), T(4, 1), T(5, 0), T(5, 1)], 2)[0] == 'tractor'
        assert classify([T(3, 0), T(3, 1), T(3, 2), T(4, 0), T(4, 1), T(4, 2)], 2)[0] == 'airplane'
        assert classify([T(5, 0), T(5, 1), T(5, 2), T(5, 3)], 2)[0] == 'bomb'
        assert classify([T(15, -1), T(15, -1), T(16, -1), T(16, -1)], 2)[0] == 'jokerbomb'
        assert classify([T(3, 0), T(4, 0), T(5, 0), T(6, 0), T(7, 0)], 2)[0] == 'straightflush'
        assert classify([T(5, 0), T(6, 1)], 2) is None
        assert keyval(2, 2) == 100 and keyval(14, 2) == 14 and keyval(15, 2) == 101
        b4 = classify([T(5, 0), T(5, 1), T(5, 2), T(5, 3)], 2)
        sf5 = classify([T(3, 0), T(4, 0), T(5, 0), T(6, 0), T(7, 0)], 2)
        assert can_play(sf5, b4) is True
        assert bomb_tier(('bomb', (6, 10), 6)) > bomb_tier(sf5)
        assert bomb_tier(sf5) > bomb_tier(('bomb', (5, 10), 5))
        assert bomb_tier(('bomb', (9, 9), 9))  > bomb_tier(('bomb', (8, 9), 8))
        assert bomb_tier(('bomb', (10, 9), 10)) > bomb_tier(('bomb', (9, 9), 9))
        assert bomb_tier(('jokerbomb', 999, 4)) > bomb_tier(('bomb', (10, 9), 10))
        assert is_wildcard(T(5, 1), 5) is True
        assert is_wildcard(T(5, 0), 5) is False
        c = classify([T(5, 1), T(6, 0)], 5)
        assert c is not None and c[0] == 'pair'
        c = classify([T(5, 1), T(5, 0), T(5, 2)], 5)
        assert c is not None and c[0] == 'triple'
        c = classify([T(5, 1), T(3, 0), T(4, 0), T(6, 0), T(7, 0)], 5)
        assert c is not None and c[0] == 'straightflush'
        nine = [T(9, s, s) for s in range(4)] + [T(9, s, s + 4) for s in range(4)]
        c = classify(nine + [T(5, 1)], 5)
        assert c is not None and c[0] == 'bomb' and c[1][0] == 9
        c = classify(nine + [T(5, 1), T(5, 1)], 5)
        assert c is not None and c[0] == 'bomb' and c[1][0] == 10
        assert is_wildcard(T(5, 1), 3) is False
        assert is_wildcard(T(3, 1), 3) is True
        a = T(5, 1, 1)
        b = T(5, 1, 2)
        assert a != b
        s = {a, b}
        assert len(s) == 2
        print("Unit tests passed.")

    _unit_tests()
    print("Self test complete.")


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
            YELLOW = 0xFFE0

    RULES_PAGES = [
"""GUANDAN - RULES (1/7)

4 players, 2 fixed teams
(seats 0&2 vs seats 1&3).
2 decks (108 cards) are
dealt out completely, 27
cards per player.

Each team has its own
LEVEL, starting at 2.
But the ACTIVE level
card (super-high rank +
wildcard) is always the
level of the team that
won the previous round.
""",
"""RULES (2/7) - WILDCARD

The HEART card of the
ACTIVE level rank is a
WILD card.

Example: level 5 active
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
From P1's view: P2 on the
right, P3 (teammate) top,
P4 on the left.
Each turn: play a legal
combo beating the table,
or pass. Once everyone
else has passed, the last
player to play leads a new
trick (table clears).
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
            if ev.key in (KEY_EXIT, KEY_F1, KEY_F4): return
            elif ev.key in (KEY_RIGHT, KEY_DOWN): page = (page + 1) % n
            elif ev.key in (KEY_LEFT, KEY_UP): page = (page - 1) % n

    def show_controls():
        lines = [
            "CONTROLS",
            "",
            "LEFT/RIGHT: change column",
            "UP/DOWN:    change card",
            "F1:         select/deselect",
            "F2:         group selected",
            "F3:         reset groupings",
            "F4:         show rules",
            "F5:         clear selection",
            "F6:         pass (when allowed)",
            "EXE:        play selected",
            "OPTN:       this screen",
            "EXIT:       quit",
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

    def _wait_or_exit(ms):
        try:
            ev = getkey_opt(-1, ms)
        except Exception:
            try:
                delay(ms)
            except Exception:
                pass
            return False
        if ev is None:
            return False
        if ev.key == KEY_EXIT:
            return True
        return False

    def _busy_wait_no_input(ms):
        try:
            import time
            end = time.ticks_ms() + ms
            while time.ticks_diff(time.ticks_ms(), end) < 0:
                try:
                    getkey_opt(-1, 50)
                except Exception:
                    pass
            return
        except Exception:
            pass
        elapsed = 0
        step = 100
        while elapsed < ms:
            try:
                getkey_opt(-1, step)
            except Exception:
                try:
                    delay(step)
                except Exception:
                    pass
            elapsed += step

    CARD_W = 30
    CARD_H = 40
    BASE_Y = 178
    GROUP_OFFSET = 10

    MINI_W = 18
    MINI_H = 26
    MINI_STEP_H = 14

    def card_color(card):
        r = card[0]
        s = card[1]
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
            dpoly([cx, cy - 3, cx - 3, cy + 1, cx, cy, cx + 3, cy + 1], color, color)
            drect(cx - 1, cy, cx + 1, cy + 3, color)
        elif suit == 1:
            dcircle(cx - 2, cy - 2, 2, color, color)
            dcircle(cx + 2, cy - 2, 2, color, color)
            dpoly([cx - 3, cy - 1, cx + 3, cy - 1, cx, cy + 3], color, color)
        elif suit == 2:
            dpoly([cx, cy - 3, cx + 3, cy, cx, cy + 3, cx - 3, cy], color, color)
        elif suit == 3:
            dcircle(cx, cy - 2, 2, color, color)
            dcircle(cx - 2, cy, 2, color, color)
            dcircle(cx + 2, cy, 2, color, color)
            drect(cx - 1, cy + 2, cx + 1, cy + 4, color)

    def draw_card(x, y, card, selected=False):
        r = card[0]
        s = card[1]
        color = card_color(card)
        border = C_BLUE if selected else C_BLACK
        drect_border(x, y, x + CARD_W - 2, y + CARD_H, C_WHITE, 2, border)
        dtext(x + 3, y + 3, color, rank_name(r))
        if r < 15:
            draw_suit_icon(x + 9, y + CARD_H - 10, s, color)
        else:
            dtext(x + 3, y + CARD_H - 12, color, "*")

    def draw_card_stacked(x, y, card, focused=False, selected=False):
        r = card[0]
        s = card[1]
        color = card_color(card)
        fill = YELLOW if selected else C_WHITE
        border = C_GREEN if focused else FG
        drect_border(x, y, x + CARD_W - 2, y + CARD_H, fill, 2, border)
        dtext(x + 3, y + 1, color, rank_char(r))
        if s >= 0:
            draw_mini_suit(x + CARD_W - 10, y + 5, s, color)
        else:
            dtext(x + CARD_W - 12, y + 1, color, "*")

    def draw_mini_card(x, y, card):
        r = card[0]
        s = card[1]
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

    def _seat_label(p, hand_sizes, base):
        n = hand_sizes[p]
        if n == 0:
            return "%s (out)" % base
        if n <= 10:
            return "%s (%d)" % (base, n)
        return base

    def draw_other_players(player, last_actions, hand_sizes):
        teammate = (player + 2) % 4
        left_p = (player - 1) % 4
        right_p = (player + 1) % 4

        act = action_of(last_actions, teammate)
        dtext_opt(DWIDTH // 2, 14, TEAM_COLOR[teammate % 2], C_NONE,
                  DTEXT_CENTER, DTEXT_TOP,
                  _seat_label(teammate, hand_sizes,
                              "P%d (team)" % (teammate + 1)), -1)
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
        dtext(4, 66, TEAM_COLOR[left_p % 2],
              _seat_label(left_p, hand_sizes, "P%d" % (left_p + 1)))
        if act == 'PASS':
            dtext(4, 82, FG, "PASS")
        elif act:
            draw_action_h(act, 4, 82)
        else:
            dtext(4, 82, FG, "--")

        act = action_of(last_actions, right_p)
        dtext_opt(DWIDTH - 4, 66, TEAM_COLOR[right_p % 2], C_NONE,
                  DTEXT_RIGHT, DTEXT_TOP,
                  _seat_label(right_p, hand_sizes, "P%d" % (right_p + 1)), -1)
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

    def default_layout(hand, level):
        by_rank = {}
        for c in hand:
            by_rank.setdefault(c[0], []).append(c)
        groups = []
        jokers = by_rank.get(15, []) + by_rank.get(16, [])
        if jokers:
            groups.append(jokers)
        lvl_cards = by_rank.get(level, [])
        if lvl_cards:
            lvl_cards = sorted(lvl_cards, key=lambda c: c[1])
            groups.append(lvl_cards)
        for r in range(14, 1, -1):
            if r == level:
                continue
            if r in by_rank:
                cards = sorted(by_rank[r], key=lambda c: c[1])
                groups.append(cards)
        return groups

    def get_layout(game, player, hand, level):
        if player not in game.hand_layouts:
            game.hand_layouts[player] = default_layout(hand, level)
        layout = game.hand_layouts[player]
        hand_set = set(hand)
        new_layout = []
        for g in layout:
            survivors = [c for c in g if c in hand_set]
            if survivors:
                new_layout.append(survivors)
        in_layout = set()
        for g in new_layout:
            for c in g:
                in_layout.add(c)
        for c in hand:
            if c not in in_layout:
                new_layout.append([c])
        game.hand_layouts[player] = new_layout
        return new_layout

    def compute_column_positions(n_cols):
        if n_cols == 0:
            return []
        col_w = CARD_W - 2
        avail = DWIDTH - 4
        if n_cols * col_w <= avail:
            pitch = col_w
        else:
            pitch = max(16, avail // n_cols)
        total_w = (n_cols - 1) * pitch + col_w
        x0 = max(2, (DWIDTH - total_w) // 2)
        return [x0 + i * pitch for i in range(n_cols)]

    def show_bot_overlay(player, result, bot_name):
        team = player % 2
        dclear(BG)
        dtext_opt(DWIDTH // 2, 20, TEAM_COLOR[team], C_NONE,
                  DTEXT_CENTER, DTEXT_TOP,
                  "P%d  (%s)" % (player + 1, bot_name), -1)
        if result is None:
            dtext_opt(DWIDTH // 2, 60, FG, C_NONE,
                      DTEXT_CENTER, DTEXT_TOP, "PASSES", -1)
        else:
            cards, combo = result
            total_w = MINI_W + (len(cards) - 1) * MINI_STEP_H
            x = DWIDTH // 2 - total_w // 2
            draw_action_h(cards, x, 60)
        dtext_opt(DWIDTH // 2, 140, FG, C_NONE,
                  DTEXT_CENTER, DTEXT_TOP,
                  "EXE/any key: skip", -1)
        dtext_opt(DWIDTH // 2, 156, FG, C_NONE,
                  DTEXT_CENTER, DTEXT_TOP,
                  "EXIT: quit", -1)
        dupdate()
        ms = 800 if bot_name == 'BOT-C' else 400
        if _wait_or_exit(ms):
            if confirm_quit():
                raise SystemExit

    def ask_skip_to_end():
        dclear(BG)
        dtext_opt(DWIDTH // 2, 40, FG, C_NONE, DTEXT_CENTER, DTEXT_TOP,
                  "All humans are done!", -1)
        dtext_opt(DWIDTH // 2, 60, FG, C_NONE, DTEXT_CENTER, DTEXT_TOP,
                  "Let the bots finish:", -1)
        dtext_opt(DWIDTH // 2, 90, FG, C_NONE, DTEXT_CENTER, DTEXT_TOP,
                  "F1: Skip to end (fast)", -1)
        dtext_opt(DWIDTH // 2, 110, FG, C_NONE, DTEXT_CENTER, DTEXT_TOP,
                  "F2: Continue normally", -1)
        dupdate()
        while True:
            ev = getkey()
            if ev.key == KEY_F1:
                return True
            if ev.key == KEY_F2:
                return False

    def ask_seats():
        seats = ['HUMAN', 'BOT-B', 'BOT-C', 'HUMAN']
        options = ['HUMAN', 'BOT-B', 'BOT-C']
        cursor = 0
        error_msg = None
        while True:
            dclear(BG)
            dtext_opt(DWIDTH // 2, 10, FG, C_NONE, DTEXT_CENTER, DTEXT_TOP,
                      "Who plays each seat?", -1)
            for i in range(4):
                team = i % 2
                col = TEAM_COLOR[team]
                y = 45 + i * 22
                prefix = "> " if i == cursor else "  "
                dtext(4, y, C_BLUE if i == cursor else FG,
                      "%sP%d:" % (prefix, i + 1))
                dtext(50, y, col, "(%s)" % ("Blue" if team == 0 else "Red"))
                dtext(120, y, FG, seats[i])
            if error_msg:
                dtext_opt(DWIDTH // 2, DHEIGHT - 50, C_RED, C_NONE,
                          DTEXT_CENTER, DTEXT_TOP, error_msg, -1)
            dtext_opt(DWIDTH // 2, DHEIGHT - 30, FG, C_NONE,
                      DTEXT_CENTER, DTEXT_TOP,
                      "UP/DOWN: seat  LEFT/RIGHT: change", -1)
            dtext_opt(DWIDTH // 2, DHEIGHT - 16, FG, C_NONE,
                      DTEXT_CENTER, DTEXT_TOP,
                      "EXE: confirm", -1)
            dupdate()
            ev = getkey()
            error_msg = None
            if ev.key == KEY_UP:
                cursor = (cursor - 1) % 4
            elif ev.key == KEY_DOWN:
                cursor = (cursor + 1) % 4
            elif ev.key in (KEY_LEFT, KEY_RIGHT):
                idx = options.index(seats[cursor])
                idx = (idx + (1 if ev.key == KEY_RIGHT else -1)) % len(options)
                seats[cursor] = options[idx]
            elif ev.key == KEY_EXE:
                if seats.count('HUMAN') == 0:
                    error_msg = "Need at least 1 human!"
                    continue
                return seats
            elif ev.key == KEY_EXIT:
                return None

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
            dtext_opt(DWIDTH // 2, 76, TEAM_COLOR[game.active_team], C_NONE,
                      DTEXT_CENTER, DTEXT_TOP,
                      "Active: Lv:%s" % rank_name(game.active_level), -1)
        if last_actions:
            dtext(4, 92, FG, "Last actions:")
            y = 106
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
                y += 22
        dtext_opt(DWIDTH // 2, DHEIGHT - 18, FG, C_NONE, DTEXT_CENTER, DTEXT_TOP,
                  "EXE when ready", -1)
        dupdate()
        while True:
            ev = getkey()
            if ev.key == KEY_EXE: return

    def do_tribute(game, hands, order_prev):
        p1, p2, p3, p4 = order_prev
        team1 = game.team_of(p1)
        double_down = (game.team_of(p2) == team1)
        level = game.active_level

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
            giver_bot = game.player_is_bot(giver)
            receiver_bot = game.player_is_bot(receiver)
            card = best_single(hands[giver], level)
            if not giver_bot:
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

            if receiver_bot:
                eligible = [c for c in hands[receiver] if c[0] <= 10]
                if not eligible:
                    eligible = sort_hand(hands[receiver], level)[:1]
                eligible.sort(key=lambda c: (keyval(c[0], level), c[1]))
                ret = eligible[0]
                hands[receiver].remove(ret)
                hands[giver].append(ret)
            else:
                hand_pass_screen(receiver, game)
                eligible = [c for c in hands[receiver] if c[0] <= 10]
                if not eligible:
                    eligible = sort_hand(hands[receiver], level)[:1]
                eligible = sorted(eligible, key=lambda c: (keyval(c[0], level), c[1]))
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

    def choose_and_play(player, hand, table_cards, table_combo, table_owner,
                        last_actions, must_play, level, game, hand_sizes):
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
            dtext(4, 2, TEAM_COLOR[team], "P%d (%s)" % (player + 1, team_name))
            dtext_opt(DWIDTH - 4, 2, TEAM_COLOR[game.active_team], C_NONE,
                      DTEXT_RIGHT, DTEXT_TOP,
                      "Lv:%s" % rank_name(game.active_level), -1)

            draw_other_players(player, last_actions, hand_sizes)
            draw_center_table(table_cards, table_owner)

            positions = compute_column_positions(len(layout))
            for gi in range(len(layout)):
                gx = positions[gi]
                group = layout[gi]
                n = len(group)
                for ci in range(n - 1, -1, -1):
                    cy = BASE_Y - ci * GROUP_OFFSET
                    is_focused = (gi == cursor[0] and ci == cursor[1])
                    is_selected = selected[gi][ci]
                    draw_card_stacked(gx, cy, group[ci], is_focused, is_selected)

            dupdate()

            ev = getkey()
            if ev.key == KEY_LEFT:
                if layout:
                    gi = (cursor[0] - 1) % len(layout)
                    cursor = (gi, 0)
            elif ev.key == KEY_RIGHT:
                if layout:
                    gi = (cursor[0] + 1) % len(layout)
                    cursor = (gi, 0)
            elif ev.key == KEY_UP:
                if layout:
                    gi, ci = cursor
                    n = len(layout[gi])
                    ci = (ci + 1) % n
                    cursor = (gi, ci)
            elif ev.key == KEY_DOWN:
                if layout:
                    gi, ci = cursor
                    n = len(layout[gi])
                    ci = (ci - 1) % n
                    cursor = (gi, ci)
            elif ev.key == KEY_F1:
                if layout:
                    gi, ci = cursor
                    selected[gi][ci] = not selected[gi][ci]
            elif ev.key == KEY_F5:
                selected = [[False] * len(g) for g in layout]
            elif ev.key == KEY_F4:
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
                layout = default_layout(hand, level)
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
        dtext_opt(DWIDTH // 2, DHEIGHT - 20, FG, C_NONE, DTEXT_CENTER, DTEXT_TOP,
                  "Please wait 5 seconds...", -1)
        dupdate()
        _busy_wait_no_input(5000)
        drect(0, DHEIGHT - 24, DWIDTH, DHEIGHT - 4, BG)
        dtext_opt(DWIDTH // 2, DHEIGHT - 20, FG, C_NONE, DTEXT_CENTER, DTEXT_TOP,
                  "Press any key to continue", -1)
        dupdate()
        getkey()

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
        seats = ask_seats()
        if seats is None:
            return
        game.seats = seats
        prev_order = None

        while game.winner_team is None:
            hands = deal()
            game.hand_layouts = {}
            game.skip_prompt_shown = False
            game.skip_mode = False
            if tribute_enabled and not game.first_round and prev_order is not None:
                do_tribute(game, hands, prev_order)
            level = game.active_level

            def chooser(player, hand, table_cards, table_combo, table_owner,
                        last_actions, must_play, _level=level, _hands=hands):
                if game.seats[player] == 'HUMAN':
                    hand_pass_screen(player, game, last_actions)
                    hand_sizes = [len(h) for h in _hands]
                    return choose_and_play(player, hand, table_cards, table_combo,
                                           table_owner, last_actions, must_play,
                                           _level, game, hand_sizes)

                if not game.skip_prompt_shown:
                    humans_done = all(len(_hands[p]) == 0
                                      for p in range(4)
                                      if game.seats[p] == 'HUMAN')
                    if humans_done:
                        game.skip_prompt_shown = True
                        game.skip_mode = ask_skip_to_end()

                hand_sizes = [len(h) for h in _hands]
                if game.seats[player] == 'BOT-B':
                    result = bot_b_choice(hand, table_combo, must_play, _level,
                                          last_actions, table_owner, player,
                                          hand_sizes, game)
                else:
                    result = bot_c_choice(hand, table_combo, must_play, _level,
                                          last_actions, table_owner, player,
                                          hand_sizes, game)
                if not game.skip_mode:
                    show_bot_overlay(player, result, game.seats[player])
                return result

            order = run_round(game, hands, chooser)
            gain, team = game.apply_result(order)
            show_round_result(order, gain, team)
            prev_order = order

        show_game_over(game)

    try:
        main()
    except SystemExit:
        pass