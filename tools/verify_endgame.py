#!/usr/bin/env python3
"""verify_endgame.py -- machine-checkable verification of the "end game"
(last-layer / saturation / suffix) theory as transferred to the OUTPUT-SET DP
used by `sortnetopt` (Harder, arXiv:2012.04400).

This file is the *authority* for docs/endgame-theory.md.  Every claim in that
document marked PROVEN is proved on paper there AND checked here by exhaustion
on every canonical output set reachable from the full cube for w <= WMAX.

Nothing here touches the engine, the pinned clone, checker/, evidence/,
config/ or ledger/.  It is a stand-alone reference model.

===========================================================================
MODEL  (engine-faithful; see docs/endgame-theory.md Sec. 2)
===========================================================================
An output set on w channels is a non-empty set X of w-bit vectors, encoded as
a frozenset of ints (bit c == channel c).

Comparator on the pair (lo, hi), lo < hi: MIN goes to `lo`, MAX goes to `hi`.
  This mirrors `OutputSet::apply_comparator([i, j])` (output_set.rs:568),
  which puts the max on channels[0] and the min on channels[1], called from
  search.rs:216-227 as `apply_comparator([i, j])` with `j < i` -- i.e. min on
  the LOWER-indexed channel.  Sorted order is therefore ASCENDING.

  A vector v is OUT OF ORDER on (lo,hi) iff v_lo = 1 and v_hi = 0.
  A vector v is IN ORDER (strictly) iff v_lo = 0 and v_hi = 1.

`apply_comparator` returns false -- i.e. the comparator is skipped -- iff
  (a) no vector is out of order      (the comparator is a no-op), or
  (b) no vector is strictly in order (the comparator is the transposition
      (lo hi) on X, a channel relabelling, hence G-equivalent to X).

TERMINAL CONDITION.  `OutputSet::is_sorted` (output_set.rs:157) accepts X iff
X has AT MOST ONE vector per Hamming weight.  `check_terminal_condition()`
verifies, exhaustively, that on sets reachable from the full cube this is
equivalent to "X is a chain under inclusion" and to "X is a channel
permutation of the sorted set" -- the untangling convention that licenses
`canonicalize(true)`.

bound(X) = least m such that some sequence of m comparators makes X sorted.
"""

from __future__ import annotations

import argparse
import itertools
import sys
import time
from collections import defaultdict
from typing import Dict, FrozenSet, Iterable, List, Optional, Sequence, Tuple

OutputSet = FrozenSet[int]
Pair = Tuple[int, int]
Key = Tuple[int, ...]


# ---------------------------------------------------------------------------
# basic operations (engine-faithful)
# ---------------------------------------------------------------------------

def all_values(w: int) -> OutputSet:
    return frozenset(range(1 << w))


def popcount(v: int) -> int:
    return bin(v).count("1")


def weight_classes(X: Iterable[int]) -> Dict[int, List[int]]:
    wc: Dict[int, List[int]] = defaultdict(list)
    for v in X:
        wc[popcount(v)].append(v)
    return wc


def is_sorted(X: Iterable[int]) -> bool:
    """`OutputSet::is_sorted`: at most one vector per Hamming weight."""
    seen = set()
    for v in X:
        p = popcount(v)
        if p in seen:
            return False
        seen.add(p)
    return True


def is_chain(X: Iterable[int]) -> bool:
    vs = sorted(X, key=popcount)
    return all(not (a & ~b) for a, b in zip(vs, vs[1:]))


def apply_comparator(X: OutputSet, lo: int, hi: int) -> OutputSet:
    """MIN -> lo, MAX -> hi.  Out of order is (v_lo=1, v_hi=0)."""
    blo, bhi = 1 << lo, 1 << hi
    out = set()
    for v in X:
        if (v & blo) and not (v & bhi):
            v = (v & ~blo) | bhi
        out.add(v)
    return frozenset(out)


def pair_flags(X: OutputSet, lo: int, hi: int) -> Tuple[bool, bool]:
    """(out_of_order_present, in_order_present) for the pair (lo, hi)."""
    blo, bhi = 1 << lo, 1 << hi
    ooo = ino = False
    for v in X:
        a, b = bool(v & blo), bool(v & bhi)
        if a and not b:
            ooo = True
        elif b and not a:
            ino = True
        if ooo and ino:
            break
    return ooo, ino


def is_settled(X: OutputSet, i: int, j: int) -> bool:
    ooo, ino = pair_flags(X, i, j)
    return not (ooo and ino)


def unsettled_pairs(X: OutputSet, w: int) -> List[Pair]:
    return [(i, j) for i in range(w) for j in range(i + 1, w)
            if not is_settled(X, i, j)]


def live_support(X: OutputSet, w: int) -> int:
    """L(X) as a channel bitmask: the channels on which two vectors of X of
    EQUAL Hamming weight disagree.

        L(X) = { p : exists u,v in X with |u| = |v| and u_p != v_p }

    Computed in one pass as  OR_l ( (OR of X_l) & ~(AND of X_l) ).
    See docs/endgame-theory.md Thm E4: every network sorting X must place a
    comparator on every channel of L(X)."""
    ors: Dict[int, int] = {}
    ands: Dict[int, int] = {}
    for v in X:
        p = popcount(v)
        if p in ors:
            ors[p] |= v
            ands[p] &= v
        else:
            ors[p] = v
            ands[p] = v
    live = 0
    for p in ors:
        live |= ors[p] & ~ands[p]
    return live & ((1 << w) - 1)


def live_count(X: OutputSet, w: int) -> int:
    return popcount(live_support(X, w))


def unsettled_dirty_count(X: OutputSet, w: int) -> int:
    d = set()
    for a, c in unsettled_pairs(X, w):
        d.add(a)
        d.add(c)
    return len(d)


def channel_is_extremal(X: OutputSet, w: int, c: int, polarity: bool) -> bool:
    """`OutputSet::channel_is_extremal`: polarity False tests the singleton
    e_c (channel c can still hold the maximum); polarity True tests its
    complement (channel c can still hold the minimum)."""
    allmask = (1 << w) - 1
    return ((1 << c) ^ (allmask if polarity else 0)) in X


# ---------------------------------------------------------------------------
# canonicalisation modulo G = S_w x C_2   (canonicalize(true))
# ---------------------------------------------------------------------------

class Canon:
    def __init__(self, w: int):
        self.w = w
        self.mask = (1 << w) - 1
        self.perms: List[Tuple[int, ...]] = list(itertools.permutations(range(w)))
        self.vmaps: List[List[int]] = []
        for p in self.perms:
            tbl = [0] * (1 << w)
            for v in range(1 << w):
                nv = 0
                for i in range(w):
                    if v & (1 << i):
                        nv |= 1 << p[i]
                tbl[v] = nv
            self.vmaps.append(tbl)
        # C_2: complement (equivalently, `OutputSet::invert`, bitmap reversal)
        self.cmap = [(~v) & self.mask for v in range(1 << w)]

    def canonical(self, X: OutputSet) -> Key:
        best: Optional[Key] = None
        for compl in (False, True):
            base = frozenset(self.cmap[v] for v in X) if compl else X
            for tbl in self.vmaps:
                cand = tuple(sorted(tbl[v] for v in base))
                if best is None or cand < best:
                    best = cand
        assert best is not None
        return best


_CANON: Dict[int, Canon] = {}


def canon_for(w: int) -> Canon:
    if w not in _CANON:
        _CANON[w] = Canon(w)
    return _CANON[w]


# ---------------------------------------------------------------------------
# the DP graph
# ---------------------------------------------------------------------------

def successors(X: OutputSet, w: int) -> Dict[Pair, OutputSet]:
    """Exactly the successors `search.rs:216-227` enumerates."""
    out: Dict[Pair, OutputSet] = {}
    for lo in range(w):
        for hi in range(lo + 1, w):
            ooo, ino = pair_flags(X, lo, hi)
            if not (ooo and ino):
                continue                      # apply_comparator returned false
            out[(lo, hi)] = apply_comparator(X, lo, hi)
    return out


class Graph:
    def __init__(self, w: int, cap: Optional[int] = None):
        self.w = w
        C = canon_for(w)
        self.rep: Dict[Key, OutputSet] = {}
        self.succ: Dict[Key, Dict[Pair, Key]] = {}
        root = C.canonical(all_values(w))
        self.rep[root] = frozenset(root)
        self.root = root
        stack = [root]
        while stack:
            k = stack.pop()
            X = self.rep[k]
            edges: Dict[Pair, Key] = {}
            for pair, Y in successors(X, w).items():
                ky = C.canonical(Y)
                edges[pair] = ky
                if ky not in self.rep:
                    self.rep[ky] = frozenset(ky)
                    stack.append(ky)
                    if cap is not None and len(self.rep) > cap:
                        raise RuntimeError(f"state cap {cap} exceeded at w={w}")
            self.succ[k] = edges
        self.states = list(self.rep.keys())
        self.bound = self._solve()

    def _solve(self) -> Dict[Key, Optional[int]]:
        b: Dict[Key, Optional[int]] = {
            k: (0 if is_sorted(self.rep[k]) else None) for k in self.states}
        changed = True
        while changed:
            changed = False
            for k in self.states:
                if b[k] == 0:
                    continue
                best = None
                for ky in self.succ[k].values():
                    v = b[ky]
                    if v is not None and (best is None or v < best):
                        best = v
                if best is not None:
                    cand = best + 1
                    if b[k] is None or cand < b[k]:
                        b[k] = cand
                        changed = True
        return b

    def optimal_pairs(self, k: Key) -> set:
        bk = self.bound[k]
        return {p for p, ky in self.succ[k].items() if self.bound[ky] == bk - 1}


_GRAPHS: Dict[int, Graph] = {}


def graph_for(w: int) -> Graph:
    if w not in _GRAPHS:
        _GRAPHS[w] = Graph(w)
    return _GRAPHS[w]


# ---------------------------------------------------------------------------
# CANDIDATE FILTERS
#
# Signature: F(X, w, budget, succ_pairs) -> admissible subset of succ_pairs.
#
# SOUNDNESS: for every reachable X with 1 <= bound(X) <= budget_cap, F must
# retain at least one pair p with bound(succ_p(X)) == bound(X) - 1.  A filter
# is applied only when bound(X) <= its declared activation budget; outside
# that it returns everything.
# ---------------------------------------------------------------------------

def f_all(X, w, b, sc):
    return set(sc)


def f_canonical_adjacent(X, w, b, sc):
    """NEGATIVE CONTROL / literal transfer of Codish Lemma 3-4.

    "every last-layer comparator is (i, i+1)".  X here is the CANONICAL
    representative, so this asks whether the canonical labelling already
    realises the adjacency normal form.  Expected to be UNSOUND -- see
    docs/endgame-theory.md Sec. 5.1."""
    return {p for p in sc if p[1] == p[0] + 1}


def f_span3(X, w, b, sc):
    """Weaker literal transfer: Codish Cor. 10 allows span <= 3 one layer up."""
    return {p for p in sc if p[1] - p[0] <= 3}


def f_bound1_unique(X, w, b, sc):
    """THEOREM E1 (proven).  If bound(X) = 1 then the sorting comparator is
    uniquely determined by the weight-class structure of X:

      - every weight class has size <= 2;
      - the classes of size 2 all differ in the SAME two channels {lo, hi},
        one vector out of order and one in order on (lo, hi);
      - the comparator is that pair.

    Returns the singleton (or empty, proving bound(X) >= 2)."""
    if b != 1:
        return set(sc)
    wc = weight_classes(X)
    pair = None
    for l, vs in wc.items():
        if len(vs) > 2:
            return set()
        if len(vs) == 2:
            d = vs[0] ^ vs[1]
            if popcount(d) != 2:
                return set()
            bits = [i for i in range(w) if d & (1 << i)]
            p = (bits[0], bits[1])
            if pair is None:
                pair = p
            elif pair != p:
                return set()
    if pair is None:
        return set()          # X already sorted; not reached (bound >= 1)
    return {pair} & set(sc)


def f_halving(X, w, b, sc):
    """THEOREM E2 (proven).  A comparator is at most 2-to-1 within each
    Hamming weight class, so bound(X) >= ceil(log2 max_l |X_l|).  Hence at
    budget b a successor is admissible only if max_l |c(X)_l| <= 2^(b-1)."""
    cap = 1 << (b - 1)
    out = set()
    for p, Y in ((p, apply_comparator(X, p[0], p[1])) for p in sc):
        if max(len(vs) for vs in weight_classes(Y).values()) <= cap:
            out.add(p)
    return out


def f_live_touch(X, w, b, sc):
    """THEOREM E4, touch form (proven).  Every channel of L(X) must carry a
    comparator.  A successor pair with BOTH endpoints outside L(X) can be
    excluded.  Machine-checked below; in practice this is the identity on the
    enumerated successor set, which is itself a (small) theorem."""
    live = live_support(X, w)
    return {p for p in sc if (live >> p[0]) & 1 or (live >> p[1]) & 1}


def f_live_budget(X, w, b, sc):
    """THEOREM E4, budget form (proven).  |L(X)| <= 2*bound(X).  As a filter:
    a successor Y is admissible only if |L(Y)| <= 2*(b-1)."""
    cap = 2 * (b - 1)
    return {p for p in sc
            if live_count(apply_comparator(X, p[0], p[1]), w) <= cap}


def f_e1_e2_e4(X, w, b, sc):
    """The deployable composite: E1 at budget 1, E2 and E4 at budget >= 2."""
    if b == 1:
        return f_bound1_unique(X, w, b, sc)
    return f_halving(X, w, b, sc) & f_live_budget(X, w, b, sc)


FILTERS = {
    "all": f_all,
    "canonical_adjacent": f_canonical_adjacent,
    "span3": f_span3,
    "bound1_unique": f_bound1_unique,
    "halving": f_halving,
    "live_touch": f_live_touch,
    "live_budget": f_live_budget,
    "composite": f_e1_e2_e4,
}

# Filters that are documented NEGATIVE CONTROLS: they are expected to be
# unsound and their failure is not a test failure.
NEGATIVE_CONTROLS = {"canonical_adjacent", "span3"}


# ---------------------------------------------------------------------------
# checks
# ---------------------------------------------------------------------------

def check_terminal_condition(w: int) -> Tuple[str, int]:
    g = graph_for(w)
    C = canon_for(w)
    sortedset = frozenset((1 << t) - 1 for t in range(w + 1))
    ksorted = C.canonical(sortedset)
    bad = 0
    for k in g.states:
        X = g.rep[k]
        a = is_sorted(X)
        b = is_chain(X)
        c = (k == ksorted)
        if not (a == b == c):
            bad += 1
    return (f"  w={w}: {len(g.states)} canonical states; "
            f"is_sorted <=> is_chain <=> canonical-sorted-set: "
            f"{'OK' if bad == 0 else f'{bad} MISMATCHES'}"), bad


def check_prop_settles(w: int) -> Tuple[str, int]:
    """Prop: applying the comparator on {lo,hi} settles {lo,hi}; and other
    pairs CAN become unsettled (so 'number of unsettled pairs' is not a
    monotone potential)."""
    g = graph_for(w)
    viol = 0
    unsettling = 0
    for k in g.states:
        X = g.rep[k]
        before = set(unsettled_pairs(X, w))
        for (lo, hi) in g.succ[k]:
            Y = apply_comparator(X, lo, hi)
            if not is_settled(Y, lo, hi):
                viol += 1
            if set(unsettled_pairs(Y, w)) - before:
                unsettling += 1
    return (f"  w={w}: acted-on pair always settled: "
            f"{'YES' if viol == 0 else f'NO ({viol})'}; "
            f"successors that UNSETTLE another pair: {unsettling}"), viol


def check_e4_channel_bound(w: int) -> Tuple[str, int]:
    """THEOREM E4 as a bound: |L(X)| <= 2 * bound(X) for every state.
    Also reports the unsettled-pair variant (CONJECTURE, not used)."""
    g = graph_for(w)
    viol = 0
    tight = 0
    viol_conj = 0
    for k in g.states:
        X = g.rep[k]
        b = g.bound[k]
        if b is None:
            continue
        n = live_count(X, w)
        if n > 2 * b:
            viol += 1
        if n == 2 * b:
            tight += 1
        if unsettled_dirty_count(X, w) > 2 * b:
            viol_conj += 1
    return (f"  w={w}: |L(X)| <= 2*bound(X): "
            f"{'OK' if viol == 0 else f'{viol} VIOLATIONS'} (tight on {tight}); "
            f"unsettled-pair variant (conjecture): "
            f"{'holds' if viol_conj == 0 else f'{viol_conj} VIOLATIONS'}"), viol


def check_e2_log_bound(w: int) -> Tuple[str, int]:
    """THEOREM E2, as a bound: bound(X) >= ceil(log2 max_l |X_l|)."""
    g = graph_for(w)
    viol = 0
    for k in g.states:
        X = g.rep[k]
        b = g.bound[k]
        if b is None:
            continue
        m = max(len(vs) for vs in weight_classes(X).values())
        need = (m - 1).bit_length()
        if b < need:
            viol += 1
    return (f"  w={w}: bound(X) >= ceil(log2 max_l |X_l|): "
            f"{'OK' if viol == 0 else f'{viol} VIOLATIONS'}"), viol


def check_monotone_edges(w: int) -> Tuple[str, int]:
    """PROPOSITION 5.1 (machine-checked): bound never INCREASES along a DP
    edge, i.e. bound(c(X)) <= bound(X) for every non-redundant comparator c.
    (It is >= bound(X)-1 by definition of the DP recursion.)  This is the
    hypothesis Theorem C of docs/endgame-theory.md needs."""
    g = graph_for(w)
    viol = 0
    dist: Dict[int, int] = defaultdict(int)
    for k in g.states:
        b = g.bound[k]
        if b is None:
            continue
        for ky in g.succ[k].values():
            by = g.bound[ky]
            if by is None:
                continue
            dist[by - b] += 1
            if by > b:
                viol += 1
    return (f"  w={w}: bound(c(X)) - bound(X) in "
            f"{dict(sorted(dist.items()))}: "
            f"{'OK (never increases)' if viol == 0 else f'{viol} INCREASES'}"), viol


def check_filter(w: int, name: str, budget_cap: int) -> Tuple[str, int]:
    g = graph_for(w)
    F = FILTERS[name]
    viol = 0
    kept = tot = 0
    audited = 0
    first_cex = None
    for k in g.states:
        b = g.bound[k]
        if b is None or b == 0 or b > budget_cap:
            continue
        audited += 1
        sc = set(g.succ[k])
        adm = F(g.rep[k], w, b, sc)
        assert adm <= sc, f"{name} returned pairs outside the successor set"
        tot += len(sc)
        kept += len(adm)
        if not (adm & g.optimal_pairs(k)):
            viol += 1
            if first_cex is None:
                first_cex = (k, b, sorted(g.optimal_pairs(k)), sorted(adm))
    pct = (100.0 * kept / tot) if tot else 0.0
    msg = (f"  w={w} {name:18s} budget<={budget_cap}: states {audited:6d}  "
           f"succ {tot:6d} -> kept {kept:6d} ({pct:5.1f}%)  "
           f"UNSOUND on {viol}")
    if first_cex and name in NEGATIVE_CONTROLS:
        msg += f"\n      first counterexample: X={first_cex[0]} bound={first_cex[1]} " \
               f"optimal={first_cex[2]} kept={first_cex[3]}"
    return msg, viol


def census(w: int) -> List[str]:
    g = graph_for(w)
    hist = defaultdict(int)
    sizes = defaultdict(list)
    for k in g.states:
        hist[g.bound[k]] += 1
        sizes[g.bound[k]].append(len(g.rep[k]))
    out = [f"  w={w}: {len(g.states)} canonical states reachable from the cube"]
    for b in sorted(hist, key=lambda x: (x is None, x)):
        s = sizes[b]
        out.append(f"    bound={str(b):>4}: {hist[b]:6d} states   "
                   f"|X| min/med/max = {min(s)}/{sorted(s)[len(s)//2]}/{max(s)}")
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-width", type=int, default=6)
    ap.add_argument("--min-width", type=int, default=3)
    ap.add_argument("--filters",
                    default="canonical_adjacent,span3,bound1_unique,halving,"
                            "live_touch,live_budget,composite")
    ap.add_argument("--budget", type=int, default=99)
    ap.add_argument("--census", action="store_true")
    args = ap.parse_args(argv)

    widths = range(args.min_width, args.max_width + 1)
    fails = 0
    t0 = time.time()

    print("== terminal condition (is_sorted <=> chain <=> perm of sorted) ==")
    for w in widths:
        m, bad = check_terminal_condition(w)
        print(m)
        fails += bad

    print("== Prop 3.2: a comparator settles exactly its own pair ==")
    for w in widths:
        m, bad = check_prop_settles(w)
        print(m)
        fails += bad

    print("== Prop 5.1: bound never increases along a DP edge ==")
    for w in widths:
        m, bad = check_monotone_edges(w)
        print(m)
        fails += bad

    print("== Theorem E2 as a bound: bound >= ceil(log2 max weight class) ==")
    for w in widths:
        m, bad = check_e2_log_bound(w)
        print(m)
        fails += bad

    print("== Theorem E4 as a bound: |dirty(X)| <= 2*bound(X) ==")
    for w in widths:
        m, bad = check_e4_channel_bound(w)
        print(m)
        fails += bad

    if args.census:
        print("== census by bound ==")
        for w in widths:
            print("\n".join(census(w)))

    print("== filter soundness audits (exhaustive over reachable states) ==")
    for name in [s.strip() for s in args.filters.split(",") if s.strip()]:
        for w in widths:
            m, bad = check_filter(w, name, args.budget)
            print(m)
            if name not in NEGATIVE_CONTROLS:
                fails += bad

    print(f"\nelapsed {time.time() - t0:.1f}s")
    print(f"TOTAL FAILURES: {fails}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
