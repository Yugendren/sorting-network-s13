#!/usr/bin/env python3
"""verify_novel_facts.py -- machine checks for docs/novel-facts.md.

Pure Python 3 standard library. Deterministic. No randomness, no network, no
environment sensitivity, no threads. Runs in well under a minute.

SCOPE NOTE (mirrors audit-paper-v2.md 10.8).  This program performs no search
for a sorting network, constructs no network, and contains no witness.  The
integer 44 appears here only as the tabulated value under audit -- the entry
whose *proof status* this project examines -- and never as a target, bound,
feature or stopping condition of any search or learning procedure.  It is
introduced once, as TABULATED_13, and is used only to instantiate hypotheses of
the form "suppose a 13-sorter of that size existed; what must it look like".

Sections
  A  Known values, the one-value chain, the two-value chain, and the PROVED vs
     PUBLISHED lower-bound tables for N = 13..32 (Dobbelaere and Wikipedia).
  B  Unconditional structure of a hypothetical minimum-size 13-sorter at the
     tabulated size: deletion-slack table, Kraft profiles, forced substructure.
  C  Branch-tree shapes: f(B) = V(T), the admissible set, and the
     UNCONDITIONAL case split on the escape-free class.
  D  Chain Collapse arithmetic: the n = 13 level ladder from the n = 11 runs,
     and an audit of the published per-level multipliers.
  E  The matched-configuration A/B ladder, read from the measurement logs, and
     the level-7 estimate recomputed in the configuration that was measured.
     Skipped (not failed) if the scratch logs are absent.

Usage
  python3 tools/verify_novel_facts.py            # full report, exit 0 iff all pass
  python3 tools/verify_novel_facts.py --quiet    # verdict lines only
  python3 tools/verify_novel_facts.py --section C
"""

from __future__ import annotations

import argparse
import math
import sys
from fractions import Fraction

# --------------------------------------------------------------------------
# Constants.  Every one of these is either an established value from the
# literature or a measurement recorded elsewhere in this repository; the
# provenance is given inline and repeated in docs/novel-facts.md.
# --------------------------------------------------------------------------

# S(n) for n <= 12.  [FK73] through n=8; [CCFS16] n=9,10; [Ha20] n=11,12.
# S(11) = 35 is additionally certified by this project (audit-paper-v2.md 7).
S = {0: 0, 1: 0, 2: 1, 3: 3, 4: 5, 5: 9, 6: 12, 7: 16, 8: 19,
     9: 25, 10: 29, 11: 35, 12: 39}

# The tabulated (not published, not proved) lower-bound value for n = 13.
# See the scope note in this file's docstring.
TABULATED_13 = 44

# Lower bounds as listed by Dobbelaere's table, column "Min. size bounds /
# OEIS A003075", fetched 2026-08-23 from
# https://bertdobbelaere.github.io/sorting_networks.html
# Changelog there: "2025-04-21 Tighter lower bounds for size, on suggestion of
# Jelmer Firet and based on principles in [VVoorh72]."  No derivation is given
# on the page and no publication behind it could be located.
DOBBELAERE_LB = {
    13: 44, 14: 48, 15: 53, 16: 57, 17: 63, 18: 68, 19: 73, 20: 78,
    21: 84, 22: 89, 23: 95, 24: 100, 25: 106, 26: 111, 27: 117, 28: 123,
    29: 129, 30: 135, 31: 141, 32: 147,
}

# Lower bounds as listed by the Wikipedia "Sorting network" article, row
# "Size, lower bound (if different)", fetched 2026-08-23.  Footnote there:
# "Obtained by Van Voorhis lemma and the value S(11) = 35".
WIKIPEDIA_LB = {13: 43, 14: 47, 15: 51, 16: 55, 17: 60, 18: 65, 19: 70, 20: 75}

# OEIS A003075 (entry version #70, last edited Nov 05 2025) lists terms for
# n = 1..12 only and carries no lower bound for any n >= 13, and no b-file.
OEIS_A003075_LAST_TERM = 12

# Measured level censuses at ambient 11 (states inserted).
# Levels 1-4: deterministic runs, .build/v3-ambient/logs/det_n11_L3{0,1,2,3}.log
# Level 5:    multithreaded run,  .build/v3-ambient/logs/mt_n11_L34.log
# Level 6:    the certified run,  evidence/v3/n11-certified/report.md
REACH_N11 = {1: 39, 2: 449, 3: 24201, 4: 207997, 5: 50594721, 6: 95221143}
REACH_N11_DETERMINISTIC_UPTO = 4

# Measured level censuses at ambient 13 (deterministic, levels 1-4).
# .build/v3-ambient/dumps/det_n13_L3{8,9},det_n13_L4{0,1}
REACH_N13_MEASURED = {1: 41, 2: 451, 3: 24203, 4: 207999}

_FAILURES: list[str] = []
_CHECKS = 0


def check(cond: bool, label: str, detail: str = "") -> bool:
    global _CHECKS
    _CHECKS += 1
    tag = "[PASS]" if cond else "[FAIL]"
    line = f"{tag} {label}"
    if detail:
        line += f"  --  {detail}"
    print(line)
    if not cond:
        _FAILURES.append(label)
    return cond


def note(text: str) -> None:
    print(f"       {text}")


def head(text: str) -> None:
    print()
    print(text)
    print("-" * len(text))


def clog2(x: int) -> int:
    """ceil(log2 x) for positive integers, computed exactly (no floats)."""
    if x <= 0:
        raise ValueError(x)
    return (x - 1).bit_length()


def C_free(n: int) -> int:
    """C(n) = 3 + sum_{k=4..n} ceil(log2 k) = sum_{k=1..n} ceil(log2 k)."""
    return sum(clog2(k) for k in range(1, n + 1))


# ==========================================================================
# Section C support: plane binary shapes, V, f(B), admissibility.
# ==========================================================================

def all_shapes(nleaves: int):
    """All plane binary shapes with `nleaves` leaves, as nested tuples.

    A leaf is the string 'L'; an internal node is (left, right).
    Subtrees are shared between trees, so memory stays small.
    """
    memo: dict[int, list] = {1: ["L"]}
    for s in range(2, nleaves + 1):
        out = []
        for s1 in range(1, s):
            for a in memo[s1]:
                for b in memo[s - s1]:
                    out.append((a, b))
        memo[s] = out
    return memo[nleaves]


# Memoisation is keyed by the shape VALUE, never by id(): shapes built by two
# different all_shapes() calls are distinct objects, and an id()-keyed cache
# silently returns another tree's answer once the first is garbage collected.
# (This bit us; the check that caught it is C1/C2.)

def height(t, _memo=None) -> int:
    if t == "L":
        return 0
    if _memo is None:
        _memo = _H
    v = _memo.get(t)
    if v is None:
        v = 1 + max(height(t[0]), height(t[1]))
        _memo[t] = v
    return v


def leaves(t) -> int:
    if t == "L":
        return 1
    v = _LV.get(t)
    if v is None:
        v = leaves(t[0]) + leaves(t[1])
        _LV[t] = v
    return v


def V(t) -> int:
    """van Voorhis's outcome count: V(leaf)=0, V(T)=2(V(l)+V(r)+2^(h_l+h_r))."""
    if t == "L":
        return 0
    v = _VV.get(t)
    if v is None:
        l, r = t
        v = 2 * (V(l) + V(r) + 2 ** (height(l) + height(r)))
        _VV[t] = v
    return v


_H: dict = {}
_LV: dict = {}
_VV: dict = {}


def node_a_values(t) -> list[int]:
    """a(c) = lp(L(c)) + lp(R(c)) + depth_B(c) + 1 over all internal nodes c."""
    out: list[int] = []
    stack = [(t, 0)]
    while stack:
        node, d = stack.pop()
        if node == "L":
            continue
        l, r = node
        out.append(height(l) + height(r) + d + 1)
        stack.append((l, d + 1))
        stack.append((r, d + 1))
    return out


def f_of_B(t) -> int:
    """f(B) = sum over internal nodes c of 2^{a(c)}  (audit-paper-v2.md 2)."""
    return sum(1 << a for a in node_a_values(t))


def canon_abstract(t) -> str:
    """Canonical string form up to reflection at any subset of nodes.

    Strings give a total order for free, so children can be sorted; nested
    tuples cannot be compared against the leaf sentinel.
    """
    if t == "L":
        return "*"
    v = _CA.get(t)
    if v is None:
        a = canon_abstract(t[0])
        b = canon_abstract(t[1])
        lo, hi = (a, b) if a <= b else (b, a)
        v = "(" + lo + " " + hi + ")"
        _CA[t] = v
    return v


_CA: dict = {}


def leaf_depths(t) -> tuple[int, ...]:
    out: list[int] = []
    stack = [(t, 0)]
    while stack:
        node, d = stack.pop()
        if node == "L":
            out.append(d)
        else:
            stack.append((node[0], d + 1))
            stack.append((node[1], d + 1))
    return tuple(sorted(out))


def min_V_dp(maxs: int):
    """g[s][h] = min V over shapes with exactly s leaves and exactly height h."""
    INF = None
    g = [[INF] * (maxs + 1) for _ in range(maxs + 1)]
    g[1][0] = 0
    for s in range(2, maxs + 1):
        for s1 in range(1, s):
            s2 = s - s1
            for h1 in range(0, maxs + 1):
                if g[s1][h1] is None:
                    continue
                for h2 in range(0, maxs + 1):
                    if g[s2][h2] is None:
                        continue
                    h = max(h1, h2) + 1
                    if h > maxs:
                        continue
                    v = 2 * (g[s1][h1] + g[s2][h2] + 2 ** (h1 + h2))
                    if g[s][h] is None or v < g[s][h]:
                        g[s][h] = v
    return g


def F_table(maxn: int) -> dict[int, int]:
    g = min_V_dp(maxn)
    out = {}
    for s in range(1, maxn + 1):
        vals = [x for x in g[s] if x is not None]
        out[s] = min(vals)
    return out


# ==========================================================================
# Section B support: Kraft-tight leaf-depth profiles.
# ==========================================================================

def kraft_profiles(nleaves: int, maxdepth: int, mindepth: int = 1):
    """All multisets of leaf depths in [mindepth, maxdepth] of size `nleaves`
    with sum 2^-d == 1.  Returned as tuples of (depth, count) with count > 0.

    By Kraft's converse these are exactly the leaf-depth multisets realisable
    by a full binary tree with `nleaves` leaves and height <= maxdepth.
    """
    res = []

    def rec(d: int, remaining: int, val: Fraction, cur: list[tuple[int, int]]):
        if d > maxdepth:
            if remaining == 0 and val == 1:
                res.append(tuple(x for x in cur if x[1]))
            return
        for c in range(remaining + 1):
            nv = val + Fraction(c, 1 << d)
            if nv > 1:
                break
            rec(d + 1, remaining - c, nv, cur + [(d, c)])

    rec(mindepth, nleaves, Fraction(0), [])
    return res


def fmt_profile(p) -> str:
    return " ".join(f"{d}^{c}" for d, c in p)


# ==========================================================================
# Section A -- the lower-bound tables.
# ==========================================================================

def section_A() -> None:
    head("SECTION A -- one-value chain, two-value chain, PROVED vs PUBLISHED")

    F = F_table(32)

    doc_F = [8, 16, 36, 52, 80, 96, 168, 200, 256, 288, 392, 424, 480, 512, 784]
    check([F[n] for n in range(3, 18)] == doc_F,
          "A1  F(N) for N=3..17 reproduces van Voorhis Table 1 / the repo table",
          f"F(13)={F[13]}, F(17)={F[17]}")

    # Independent cross-check of F by brute-force enumeration at N = 13.
    shapes13 = all_shapes(13)
    check(len(shapes13) == 208012,
          "A2  the number of plane shapes with 13 leaves is Catalan(12)",
          f"{len(shapes13)}")
    bf = min(V(t) for t in shapes13)
    check(bf == F[13],
          "A3  brute-force min over 13-leaf shapes agrees with the height DP",
          f"brute={bf} dp={F[13]}")

    # Consistency of the two-value inequality against every known exact value.
    slacks = []
    ok = True
    for n in range(3, 13):
        s = S[n] - S[n - 2] - clog2(F[n])
        slacks.append(s)
        if s < 0:
            ok = False
    check(ok, "A4  eq (8) consistent with every known exact S(n), n=3..12",
          f"slacks {slacks}")

    # The two chains, run out to the end of Dobbelaere's table.
    one = dict(S)
    both = dict(S)
    for n in range(13, 33):
        one[n] = one[n - 1] + clog2(n)
        both[n] = max(both[n - 1] + clog2(n), both[n - 2] + clog2(F[n]))

    print()
    print("     N |   F(N) | lg2F | PROVED (one-value) | eq(8) chain |"
          " Dobbelaere | Wikipedia | deficit")
    for n in range(13, 33):
        w = WIKIPEDIA_LB.get(n)
        print(f"    {n:2d} | {F[n]:6d} | {clog2(F[n]):4d} | {one[n]:18d} |"
              f" {both[n]:11d} | {DOBBELAERE_LB[n]:10d} |"
              f" {('-' if w is None else str(w)):>9} | {both[n] - one[n]:7d}")

    check(all(both[n] == DOBBELAERE_LB[n] for n in DOBBELAERE_LB),
          "A5  the eq(8)-conditional chain reproduces Dobbelaere's table "
          "at EVERY n = 13..32",
          "20 of 20 entries, exactly; no derivation is published for any of them")

    check(all(one[n] == WIKIPEDIA_LB[n] for n in WIKIPEDIA_LB),
          "A6  the one-value chain reproduces Wikipedia's table at every "
          "n = 13..20",
          "8 of 8 entries, exactly")

    check(one[13] == 43,
          "A6b the one-value chain gives the proved floor at n=13", f"{one[13]}")

    check(all(one[n] < DOBBELAERE_LB[n] for n in DOBBELAERE_LB),
          "A7  every Dobbelaere entry n=13..32 strictly exceeds the proved floor",
          "so every one of the 20 depends on eq (8)")

    check(all(WIKIPEDIA_LB[n] < DOBBELAERE_LB[n] for n in WIKIPEDIA_LB),
          "A7b the two public tables DISAGREE at every n = 13..20",
          "deficits " + ",".join(str(DOBBELAERE_LB[n] - WIKIPEDIA_LB[n])
                                 for n in sorted(WIKIPEDIA_LB)))
    note("    Wikipedia lists the one-value chain and footnotes it as such.")
    note("    Dobbelaere lists the two-value chain, attributed to a 2025-04-21")
    note("    suggestion and to the Plenum chapter, with no derivation given.")
    note("    OEIS A003075 lists no lower bound at all for any n >= 13.")
    note("    The audit adjudicates: Wikipedia's column is the defensible one.")
    note(f"    The deficit grows from {DOBBELAERE_LB[13]-one[13]} at n=13 to "
         f"{DOBBELAERE_LB[32]-one[32]} at n=32.")

    # Which known values does the published chain rest on?
    check(one[13] == S[12] + clog2(13) and S[12] == S[11] + clog2(12),
          "A8  the one-value floor at 13 reduces through S(12) to S(11)=35",
          f"43 = 39 + 4, 39 = 35 + 4")
    check(both[13] == S[11] + clog2(F[13]),
          "A9  the tabulated value at 13 reduces directly to S(11)=35",
          f"{S[11]} + {clog2(F[13])} = {both[13]}")

    note("Both chains bottom out at S(11) = 35 and at no other computed value:")
    note("S(12)=39 is one-value from S(11); every entry 13..20 is a chain above")
    note("S(11) or S(12).  S(11)=35 is the deepest computational input to the")
    note("whole table, and until this project it had exactly one machine proof.")

    # Sensitivity: what would change if S(11) were not 35?
    note("")
    note("Sensitivity: lowering S(11) by 1 lowers every entry N>=12 by at least 1")
    Sx = dict(S)
    Sx[11] -= 1
    Sx[12] = Sx[11] + clog2(12)
    bx = dict(Sx)
    for n in range(13, 33):
        bx[n] = max(bx[n - 1] + clog2(n), bx[n - 2] + clog2(F[n]))
    note("   S(11)=34 => table 13..20 = "
         + ",".join(str(bx[n]) for n in range(13, 21)))


# ==========================================================================
# Section B -- unconditional structure at the tabulated size.
# ==========================================================================

def section_B() -> None:
    head("SECTION B -- unconditional structure of a hypothetical 13-sorter "
         f"of the tabulated size ({TABULATED_13})")

    note("Inputs, all classical and all already used by audit-paper-v2.md:")
    note("  (F1) deleting a channel at either polarity from an N-sorter C")
    note("       removes exactly the comparators on that channel's extremal")
    note("       path and leaves an (N-1)-sorter; hence")
    note("       |C| >= S(N-1) + delta(C,i) for every channel i and polarity.")
    note("  (F2) the branch tree B of the max computation has N leaves and")
    note("       N-1 internal nodes; delta(C,i) = depth_B(i) + pt(C,i) where")
    note("       pt counts pass-throughs on i's max-path (Proposition 3).")
    note("  (F3) Kraft equality on a full binary tree: sum_i 2^-depth_B(i) = 1.")
    note("  (F4) the dual statements for the min computation.")
    note("None of this uses eq (8).")

    B = TABULATED_13

    # B1 -- the per-channel depth ceiling.
    ceiling = B - S[12]
    check(ceiling == 5,
          "B1  every extremal path has at most B - S(12) comparators",
          f"{B} - {S[12]} = {ceiling}")
    note(f"    Hence for every channel i and either polarity: "
         f"depth_B(i) + pt(C,i) <= {ceiling}.")
    note("    A leaf at branch-depth 5 therefore has a pass-through-FREE path.")

    # B2 -- the height bracket.
    lo = clog2(13)
    check(lo == 4 and ceiling == 5,
          "B2  both branch trees have height in {4,5}",
          f"ceil(log2 13) = {lo} <= h <= {ceiling}")

    # B3 -- the Kraft profiles.
    profs = kraft_profiles(13, ceiling)
    check(len(profs) == 13,
          "B3  admissible branch-tree leaf-depth profiles, unconditionally",
          f"{len(profs)} Kraft-tight profiles with all depths <= {ceiling}")
    for p in profs:
        note("    " + fmt_profile(p))
    profs4 = kraft_profiles(13, 4)
    check(len(profs4) == 2,
          "B4  if a branch tree has height 4 only two profiles are possible",
          ", ".join(fmt_profile(p) for p in profs4))

    # B5 -- the iterated-deletion slack table.
    print()
    print("     k | S(k) | sum_{m=k+1..13} ceil(log2 m) | slack = B - S(k) - sum")
    tot = 0
    slack = {}
    for k in range(12, 2, -1):
        tot += clog2(k + 1)
        slack[k] = B - S[k] - tot
        print(f"    {k:2d} | {S[k]:4d} | {tot:27d} | {slack[k]:21d}")
    check(min(slack.values()) >= 0,
          "B5  the iterated-deletion chain is consistent at every k",
          "no negative slack, as it must be since B exceeds the one-value floor")
    check(slack[12] == 1 and slack[11] == 1,
          "B6  the chain is tightest at k = 12 and k = 11, with slack exactly 1",
          f"slack(12)={slack[12]}, slack(11)={slack[11]}")

    # B7 -- forced optimal minor.
    note("")
    note("B7 (forced substructure).  Suppose some channel i has an extremal")
    note(f"    path of the maximum length {ceiling}.  Deleting it leaves a")
    note(f"    12-sorter with {B} - {ceiling} = {B - ceiling} = S(12)")
    note("    comparators, i.e. a SIZE-OPTIMAL 12-sorter.  In that minor every")
    note(f"    extremal path has length at most S(12) - S(11) = "
         f"{S[12] - S[11]}, so both of ITS branch trees have height exactly")
    note(f"    ceil(log2 12) = {clog2(12)} and all 12 leaves at depth <= "
         f"{S[12]-S[11]}.")
    p12 = kraft_profiles(12, S[12] - S[11])
    check(len(p12) == 2,
          "B7  the forced optimal 12-sorter minor has only two depth profiles",
          ", ".join(fmt_profile(p) for p in p12))

    # B8 -- the extremes-pair deletion bound.
    note("")
    note("B8 (extremes pair).  Feeding +inf to channel i and -inf to channel")
    note("    j != i determines every comparator on i's max-path and on j's")
    note("    min-path, so all of them may be deleted by rewiring, leaving an")
    note("    11-sorter.  Hence for all i != j")
    note("        |maxpath(i) UNION minpath(j)| <= B - S(11) = "
         f"{B - S[11]}.")
    note("    This is the max/min analogue of the max/second-max quantity")
    note("    p(2,T) of the chapter under audit; it is a different deletion")
    note("    and, as far as we can find, has not been studied.")
    check(B - S[11] == 9,
          "B8  the extremes-pair budget at the tabulated size", f"{B - S[11]}")
    note("    Corollary (dichotomy).  If the deepest max-path and the deepest")
    note("    min-path are comparator-disjoint then h(B_max) + h(B_min) <= "
         f"{B - S[11]}, so they cannot both be 5: at least one of the two")
    note("    branch trees has minimum height 4.  Paths may share comparators,")
    note("    so the dichotomy is conditional on disjointness -- we state it")
    note("    with that hypothesis and do not hide it.")


# ==========================================================================
# Section C -- the escape-free case split, unconditionally.
# ==========================================================================

def section_C() -> None:
    head("SECTION C -- f(B) = V(T), and the case split made unconditional "
         "on the escape-free class")

    shapes13 = all_shapes(13)

    # C1 -- the bridge: the paper's f(B) is the shape literature's V(T).
    bad = 0
    for t in shapes13:
        if f_of_B(t) != V(t):
            bad += 1
            if bad < 4:
                note(f"    mismatch: f={f_of_B(t)} V={V(t)}")
    check(bad == 0,
          "C1  f(B) = sum_c 2^{a(c)} equals V(T) on all 208,012 plane shapes",
          "the audit's decorated-tree object IS the shape literature's count")
    small = 0
    for n in range(1, 12):
        for t in all_shapes(n):
            if f_of_B(t) != V(t):
                small += 1
    check(small == 0,
          "C2  the same identity holds for every shape with <= 11 leaves",
          "checked exhaustively")

    # C3 -- the admissible set.
    ceiling = 1 << (TABULATED_13 - S[11])
    check(ceiling == 512,
          "C3  the admissibility ceiling implied by Theorem 6 at n = 13",
          f"2^(B - S(11)) = 2^{TABULATED_13 - S[11]} = {ceiling}")
    note("    Theorem 6 (audit-paper-v2.md 5.2), PROVED for every escape-free")
    note("    N-sorter and with no appeal to eq (8):")
    note("        |T| >= S(N-2) + ceil(log2 f(B)).")
    note("    At N = 13 with |T| at the tabulated size this forces")
    note(f"        ceil(log2 f(B)) <= {TABULATED_13 - S[11]}, i.e. "
         f"f(B) <= {ceiling}.")
    note("    That is EXACTLY the admissibility condition of the shape case")
    note("    split, which until now was conditional on the unverified")
    note("    per-network form of the two-channel theorem (assumption E1').")
    note("    Theorem 6 IS E1', proved, on the escape-free class.")

    adm = [t for t in shapes13 if V(t) <= ceiling]
    check(len(adm) == 84,
          "C4  admissible plane shapes with 13 leaves", f"{len(adm)}")
    absset = {canon_abstract(t) for t in adm}
    check(len(absset) == 6,
          "C5  admissible shapes up to reflection", f"{len(absset)}")
    hs = sorted({height(t) for t in adm})
    check(hs == [4, 5],
          "C6  admissible heights are exactly {4,5}", f"{hs}")
    excluded_min = min(V(t) for t in shapes13 if V(t) > ceiling)
    check(excluded_min == 528,
          "C7  the smallest excluded count is 528 (3.1% robustness margin)",
          f"{excluded_min}")

    # Root splits and classes.
    splits = {}
    for t in adm:
        l, r = t
        key = tuple(sorted([(leaves(l), height(l)), (leaves(r), height(r))]))
        splits.setdefault(key, []).append(t)
    check(len(splits) == 3,
          "C8  exactly three unordered root classes survive", f"{len(splits)}")
    print()
    print("     class root split                       | plane | abstract |"
          " V range   | max_c a(c)")
    names = {}
    for key in sorted(splits, key=lambda k: min(V(t) for t in splits[k])):
        ts = splits[key]
        lab = f"({key[0][0]} leaves,h{key[0][1]} | {key[1][0]} leaves,h{key[1][1]})"
        names[key] = lab
        vs = sorted({V(t) for t in ts})
        maxa = max(max(node_a_values(t)) for t in ts)
        print(f"     {lab:36s} | {len(ts):5d} | "
              f"{len({canon_abstract(t) for t in ts}):8d} | "
              f"{vs[0]:3d}-{vs[-1]:3d}   | {maxa:2d}")

    # C9 -- leaf-depth profiles of admissible shapes vs the unconditional set.
    admprofs = {leaf_depths(t) for t in adm}
    check(len(admprofs) == 4,
          "C9  admissible shapes realise only 4 leaf-depth profiles",
          f"{len(admprofs)} of the {len(kraft_profiles(13,5))} "
          "permitted unconditionally (Section B3)")
    for p in sorted(admprofs):
        cnt: dict[int, int] = {}
        for d in p:
            cnt[d] = cnt.get(d, 0) + 1
        note("    " + " ".join(f"{d}^{c}" for d, c in sorted(cnt.items())))

    # C10 -- tightness and rigidity.
    tight = [t for t in adm if V(t) == ceiling]
    check(len(tight) > 0,
          "C10 some admissible shapes are TIGHT (f(B) = 2^{p(2,T)})",
          f"{len(tight)} plane shapes with f(B) = {ceiling}; on these "
          "Theorem 7's rigidity applies with margin 0")
    note("    On a tight escape-free sorter Theorem 7 forces, at EVERY branch")
    note("    node c: eps(c) = 0, gamma(c) = ov(c), W*(c) = p(2,T).  eps(c)=0")
    note("    says the deepest leaf of each side reaches c in exactly its")
    note("    branch-tree depth -- no pass-through anywhere on those paths.")

    # C11 -- the max_c a(c) budget.
    note("")
    note("C11 (node budget).  For an escape-free sorter at the tabulated size,")
    note(f"    p(2,T) <= B - S(11) = {TABULATED_13 - S[11]}, and by Lemma 5")
    note("    p(2,T) = max_c [a(c) + eps(c) + gamma(c) + r(c)].  Hence at every")
    note(f"    branch node  eps(c) + gamma(c) + r(c) <= "
         f"{TABULATED_13 - S[11]} - a(c).")
    worst = {}
    for key in splits:
        worst[names[key]] = max(max(node_a_values(t)) for t in splits[key])
    for k in sorted(worst):
        note(f"    {k}: max_c a(c) = {worst[k]}  =>  slack "
             f"{TABULATED_13 - S[11] - worst[k]} at the worst node")
    check(all(v <= TABULATED_13 - S[11] for v in worst.values()),
          "C11 no admissible shape has a node exceeding the p(2,T) budget",
          "as it must be, since f(B) <= 2^{p(2,T)} bounds every summand")

    # C12 -- the dual.
    note("")
    note("C12 (dual).  The reverse-and-flip dual of a sorter is a sorter whose")
    note("    max branch tree is the original's MIN branch tree.  So if T and")
    note("    its dual are both escape-free, BOTH branch trees are admissible")
    note("    -- two independent shape constraints, unconditionally.")


# ==========================================================================
# Section D -- Chain Collapse arithmetic.
# ==========================================================================

def section_D() -> None:
    head("SECTION D -- the n = 13 level census from the n = 11 runs")

    D = {n: S[n] - C_free(n) for n in range(3, 13)}
    check([D[n] for n in range(3, 13)] == [0, 0, 1, 1, 2, 2, 4, 4, 6, 6],
          "D1  D(n) = S(n) - C(n) for n = 3..12",
          ",".join(str(D[n]) for n in range(3, 13)))
    check(C_free(13) == 37, "D2  C(13) = 37", f"{C_free(13)}")

    nmin = {}
    for l in range(1, 8):
        cands = [n for n in range(3, 13) if D[n] >= l]
        nmin[l] = cands[0] if cands else 13
    check([nmin[l] for l in range(1, 8)] == [5, 7, 9, 9, 11, 11, 13],
          "D3  n_min(l) for l = 1..7",
          ",".join(str(nmin[l]) for l in range(1, 8)))

    print()
    print("     level | n_min | |Reach(11,l)| measured | +(13-n_min) |"
          " |Reach(13,l)| | measured at 13 | agree")
    okall = True
    for l in range(1, 7):
        r11 = REACH_N11[l]
        pred = r11 + (13 - 11)          # n_min(l) = 11 for l = 5,6; <= 11 else
        meas = REACH_N13_MEASURED.get(l)
        agree = "-" if meas is None else ("yes" if meas == pred else "NO")
        if meas is not None and meas != pred:
            okall = False
        print(f"     {l:5d} | {nmin[l]:5d} | {r11:23d} | {2:11d} |"
              f" {pred:12d} | {str(meas):14s} | {agree}")
    check(okall,
          "D4  Theorem 12 predicts the measured n=13 census exactly at l=1..4",
          "the +2 is the free-chain pair {cube_12, cube_13}")

    note("")
    note(f"    Levels 1-{REACH_N11_DETERMINISTIC_UPTO} are single-threaded")
    note("    deterministic runs; the equality is exact.  Levels 5 and 6 are")
    note("    multithreaded, where the stored census is run-dependent at the")
    note("    1-2% level, so the level-5 and level-6 entries are EMPIRICAL")
    note("    measurements, not exact invariants.  The '+2' is PROVEN at every")
    note("    level by Theorem 12; only the base measurement carries noise.")
    note("")
    note(f"    |Reach(13,6)| = {REACH_N11[6]} + 2 = {REACH_N11[6] + 2}")
    note("    This number has never been computed at n = 13 by any means.")

    # ---- multiplier audit -------------------------------------------------
    # The published multipliers 12.49 / 46.11 / 8.36 / 245.89 are attributed
    # by audit-paper-v2.md 8.2 to "the n = 12 ladder".  They are not: they are
    # the n = 13 column of the pre-determinism census table in
    # transforms-assessment.md 2.3, whose level 1-4 entries that same project
    # later showed to be thread-scheduling noise (ambient-reduction.md 4.1-4.2).
    NOISY_N13 = {1: 43, 2: 537, 3: 24761, 4: 207097, 5: 50922864}
    NOISY_N12 = {1: 42, 2: 541, 3: 25706, 4: 208070, 5: 50788878}
    PAPER_MULT = [12.49, 46.11, 8.36, 245.89]

    def mults(d, upto):
        return [d[l + 1] / d[l] for l in range(1, upto)]

    m13 = mults(NOISY_N13, 5)
    m12 = mults(NOISY_N12, 5)
    check(all(abs(a - b) < 0.01 for a, b in zip(m13, PAPER_MULT)),
          "D5  the quoted multipliers come from the n=13 column, not n=12",
          "n=13 " + "/".join(f"{x:.2f}" for x in m13)
          + "   n=12 " + "/".join(f"{x:.2f}" for x in m12))
    note("    audit-paper-v2.md 8.2 attributes them to 'the n = 12 ladder'.")
    note("    That attribution is wrong; the n=12 ladder gives "
         + "/".join(f"{x:.2f}" for x in m12) + ".")

    # Recompute from the deterministic censuses, which are noise-free.
    DET13 = {1: 41, 2: 451, 3: 24203, 4: 207999}
    det = mults(DET13, 4)
    note("")
    note("    Recomputed from the DETERMINISTIC ambient-13 censuses "
         "(41/451/24,203/207,999):")
    note("      1->2 " + f"{det[0]:.2f}x   2->3 {det[1]:.2f}x   "
         f"3->4 {det[2]:.2f}x")
    note("    against the noisy figures 12.49 / 46.11 / 8.36.  The level-1")
    note("    multiplier moves by 12% and the level-2 by 16%; the geometric")
    note("    mean of the four-factor product is what the level-7 bracket")
    note("    rests on, so this is not cosmetic.")

    prod_noisy = 1.0
    for x in m13:
        prod_noisy *= x
    det_full = det + [NOISY_N13[5] / DET13[4]]
    prod_det = 1.0
    for x in det_full:
        prod_det *= x
    note("")
    note(f"    geometric mean, as published : {prod_noisy ** 0.25:.3f}x")
    note(f"    geometric mean, deterministic: {prod_det ** 0.25:.3f}x")
    check(abs(prod_noisy ** 0.25 - 33.0) < 0.2,
          "D6  the published geometric mean 33.0x is reproduced",
          f"{prod_noisy ** 0.25:.3f}")

    print()
    print("     level transition | ambient-11 raw ratio")
    for l in range(1, 6):
        m = REACH_N11[l + 1] / REACH_N11[l]
        print(f"     {l} -> {l+1:13d} | {m:10.2f}x")
    note("")
    note("    The 5->6 figure MIXES CONFIGURATIONS: levels 1-5 were measured")
    note("    with on-line subsumption OFF, the level-6 figure with eviction-")
    note("    mode subsumption at pinned widths 8,9.  Under eviction the")
    note("    engine's reported count is an INSERTION counter while the")
    note("    stored census is inserts minus evictions, so the two numbers")
    note("    are not even the same quantity.  Do NOT read 1.88x as a")
    note("    multiplier: Section E measures the matched value and it is")
    note("    20.20x.  The raw ratio is wrong by a factor of 10.7.")


# ==========================================================================

def _parse_run_log(path) -> dict:
    """Pull the three counters we need out of an engine stdout log."""
    out: dict[str, int] = {}
    with open(path, "r", errors="replace") as fh:
        for line in fh:
            p = line.split()
            if len(p) >= 3 and p[0] == "counter" and p[1] in (
                    "set_inserts", "idx_evictions"):
                out[p[1]] = int(p[2])
            elif len(p) >= 3 and p[0] == "statemap" and p[1] == "total_entries":
                out["total_entries"] = int(p[2])
            elif "result =" in line:
                out["result"] = int(line.split("result =")[1].split()[0])
    return out


def section_E() -> None:
    """Matched-configuration A/B ladder, read from the measurement logs."""
    import os
    head("SECTION E -- matched-configuration A/B ladder at ambient 11")

    root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",
                        ".build", "v3-novelty", "ladder")
    root = os.path.normpath(root)
    if not os.path.isdir(root):
        print(f"[SKIP] E   measurement logs absent ({root})")
        note("This section reads the scratch logs produced by the A/B runs;")
        note("it is skipped on a checkout that does not carry them.  The")
        note("numbers are tabulated in docs/novel-facts.md 1.2.")
        return

    note("Config A = plain (SORTNETOPT_POOL_THREADS=4 only).")
    note("Config B = certified-matched (SUBSUME=evict, DIMS=96, WIDTHS=8,9).")
    note("Same binary, same thread count, sequential runs.")
    print()
    print("     level | limit | A inserts | B inserts | B/A   | B entries |"
          " evictions")

    rows = []
    for L in range(30, 36):
        pa = os.path.join(root, f"configA_n11_L{L}.log")
        pb = os.path.join(root, f"configB_n11_L{L}.log")
        if not (os.path.exists(pa) and os.path.exists(pb)):
            continue
        a = _parse_run_log(pa)
        b = _parse_run_log(pb)
        if "set_inserts" not in a or "set_inserts" not in b:
            continue
        ratio = b["set_inserts"] / a["set_inserts"]
        rows.append((L - 29, L, a, b, ratio))
        print(f"     {L-29:5d} | {L:5d} | {a['set_inserts']:9d} |"
              f" {b['set_inserts']:9d} | {ratio:5.3f} |"
              f" {b.get('total_entries', -1):9d} |"
              f" {b.get('idx_evictions', -1):9d}")

    check(len(rows) >= 4,
          "E1  the A/B ladder covers at least levels 1-4",
          f"{len(rows)} matched level(s) found")

    if rows:
        okres = all(r[2].get("result") == r[1] and r[3].get("result") == r[1]
                    for r in rows)
        check(okres,
              "E2  every run returned result = its own limit (level reached)",
              "so each row is a completed level, not a truncated run")

        okevict = all(
            r[3].get("total_entries", 0) + r[3].get("idx_evictions", 0)
            == r[3]["set_inserts"] for r in rows)
        check(okevict,
              "E3  under eviction, entries + evictions = inserts exactly",
              "confirms the two quantities differ and by how much")
        note("    This is the reason the certified run's '95,221,143 states'")
        note("    is ambiguous: with no surviving log, we cannot tell whether")
        note("    it is the insert counter or the stored census.")

        deep = [r for r in rows if r[0] >= 3]
        if deep:
            check(all(r[4] < 1.0 for r in deep),
                  "E4  subsumption reduces the insert count from level 3 on",
                  ", ".join(f"l{r[0]}:{r[4]:.3f}" for r in deep))
            check(all(deep[i][4] >= deep[i + 1][4]
                      for i in range(len(deep) - 1)),
                  "E5  the configuration correction deepens monotonically",
                  "so the level-6 correction is at least as strong as level "
                  f"{deep[-1][0]}'s {deep[-1][4]:.3f}")
            note("")
            note("    The correction is NOT a small constant.  It is ~1.0 at")
            note("    levels 1-2, 1.5x at level 4, and 10.7x at level 5.  Any")
            note("    extrapolation of the shallow-level trend is wrong; this")
            note("    is precisely why the measurement was worth making.")

    # The matched multiplier -- the number audit-paper-v2.md 8.2 asks for.
    if len(rows) >= 5:
        b5 = rows[4][3]["set_inserts"]
        a5 = rows[4][2]["set_inserts"]
        matched = REACH_N11[6] / b5
        raw = REACH_N11[6] / a5
        note("")
        note("    *** THE MATCHED MEASUREMENT ***")
        note(f"    level-5 census, config B (matched to the certified run): "
             f"{b5:,}")
        note(f"    level-6 census, config B (the certified run)          : "
             f"{REACH_N11[6]:,}")
        note(f"    MATCHED level-5 -> level-6 multiplier = {matched:.2f}x")
        note(f"    (the unmatched reading was {raw:.2f}x, wrong by "
             f"{matched/raw:.1f}x)")
        check(matched > 8.36,
              "E6  the matched multiplier exceeds the 'optimistic floor' 8.36x",
              f"{matched:.2f}x -- the paper's worry that it was below the floor "
              "does not survive the matched measurement")

        # Per-configuration growth rates over the whole ladder.
        def geo(seq):
            p = 1.0
            for i in range(len(seq) - 1):
                p *= seq[i + 1] / seq[i]
            return p ** (1.0 / (len(seq) - 1))

        aseq = [r[2]["set_inserts"] for r in rows]
        bseq = [r[3]["set_inserts"] for r in rows] + [REACH_N11[6]]
        note("")
        note(f"    config A ladder {aseq}")
        note(f"      per-level multipliers "
             + "/".join(f"{aseq[i+1]/aseq[i]:.2f}"
                        for i in range(len(aseq) - 1))
             + f"   geometric mean {geo(aseq):.2f}x")
        note(f"    config B ladder {bseq}")
        note(f"      per-level multipliers "
             + "/".join(f"{bseq[i+1]/bseq[i]:.2f}"
                        for i in range(len(bseq) - 1))
             + f"   geometric mean {geo(bseq):.2f}x")
        check(abs(geo(aseq) - 33.0) < 1.0,
              "E7  config A reproduces the published growth rate of 33x",
              f"{geo(aseq):.2f}x -- so the published bracket is a config-A "
              "bracket")
        check(geo(bseq) < geo(aseq) * 0.75,
              "E8  the memory-frugal configuration grows markedly slower",
              f"{geo(bseq):.2f}x vs {geo(aseq):.2f}x")

        # Level-7, in the configuration a level-7 run would actually use.
        bm = [bseq[i + 1] / bseq[i] for i in range(len(bseq) - 1)]
        lo, hi, gm = min(bm), max(bm), geo(bseq)
        anchor = REACH_N11[6]
        note("")
        note("    Level-7 estimate IN CONFIG B, the configuration the")
        note("    certified run used and a level-7 run would use:")
        print()
        print(f"       floor  ({lo:5.2f}x) : {anchor*lo:9.2e} states")
        print(f"       geo    ({gm:5.2f}x) : {anchor*gm:9.2e} states")
        print(f"       ceiling({hi:5.2f}x) : {anchor*hi:9.2e} states")
        note("")
        note("    Standing published bracket: 5.55e10 - 3.08e12 states, and")
        note("    'Go/no-go: NO' on a disk wall short by 7.4x at the floor.")
        note(f"    The new floor is {5.55e10/(anchor*lo):.0f}x below the old "
             f"floor and the new ceiling is {3.08e12/(anchor*hi):.0f}x below")
        note("    the old ceiling.  The standing bracket was computed in a")
        note("    configuration nobody would run level 7 in.")
        note("")
        note("    EMPIRICAL and extrapolated.  The 6->7 multiplier is not")
        note("    measured and cannot be: level 7 exists at no ambient below")
        note("    13.  And config B's own reduction factor GREW with level")
        note("    (1.0, 1.0, 1.25, 1.54, 10.69); whether it keeps growing at")
        note("    6->7 is unknown, and it moves the answer either way.")


SECTIONS = {"A": section_A, "B": section_B, "C": section_C, "D": section_D,
            "E": section_E}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--section", choices=sorted(SECTIONS), default=None)
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    if args.quiet:
        class _Null:
            def write(self, *a):
                return 0

            def flush(self):
                pass
        real = sys.stdout

        def check_only(cond, label, detail=""):
            global _CHECKS
            _CHECKS += 1
            print(("[PASS] " if cond else "[FAIL] ") + label, file=real)
            if not cond:
                _FAILURES.append(label)
            return cond

        globals()["check"] = check_only
        sys.stdout = _Null()

    names = [args.section] if args.section else sorted(SECTIONS)
    for n in names:
        SECTIONS[n]()

    if args.quiet:
        sys.stdout = real

    print()
    print("=" * 72)
    if _FAILURES:
        print(f"FAILED {len(_FAILURES)} of {_CHECKS} checks:")
        for f in _FAILURES:
            print(f"  - {f}")
        return 1
    print(f"ALL {_CHECKS} CHECKS PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
