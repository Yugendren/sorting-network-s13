#!/usr/bin/env python3
"""
verify_shape_case_split.py -- independent machine check of the "five surviving
root tree-shape classes" claim for S(13).

WHAT THIS SCRIPT IS
-------------------
A read-only, deterministic, stdlib-only re-derivation of the counting argument
recorded in docs/research/xdomain-bound-theory.md Sec. 6.2 and repeated as the
headline of docs/research/synthesis-ranked-queue.md:

    "only 5 root tree-shape classes are consistent with a 44-comparator
     sorting network; all other shapes force >= 513 reachable outcomes"

It is NOT a search component and NOT a learning component.  It performs no
network construction, contains no witness network, and is never invoked from the
Track-A evolution harness.  The integer 44 appears here only because it is the
published lower bound whose supporting counting argument is the object under
audit; it is not a target, budget, feature or stopping condition of any search.

The script deliberately does NOT trust the numbers in the survey document.  It
re-derives the whole F(N) table, the shape enumeration and every downstream
arithmetic fact, then compares against the documented claims and reports every
disagreement.

USAGE
-----
    python3 tools/verify_shape_case_split.py             # audit the documented claim
    python3 tools/verify_shape_case_split.py --corrected # audit the corrected claim
    python3 tools/verify_shape_case_split.py --quiet     # verdicts only

Exit code 0 iff every check in the selected audit passes.

TRUST BOUNDARY
--------------
Three inputs are external and are *asserted*, not proved, here:

  (E1) The van Voorhis two-channel theorem  S(N) >= S(N-2) + P(2,N)  with
       P(2,N) >= ceil(log2 F(N)).   [Van Voorhis, Plenum 1972 - paywalled,
       not in hand; see docs/sota-survey.md]
  (E2) The recursion defining F(N) (Dobbelaere's gist, transcribed in
       docs/research/xdomain-bound-theory.md Sec. 1.4):
           F(N) = min over binary tree shapes T with N leaves of V(T), where
           V(leaf) = 0 and V(T) = 2 * (V(Tl) + V(Tr) + 2**(h(Tl) + h(Tr))).
       The script *validates* this transcription against every externally known
       data point it can reach (the published F table, the published lower-bound
       table for N=13..17, and non-violation of all known exact S(N)), but the
       semantics of V -- what the tree is a tree *of*, in terms of a network --
       cannot be checked without the primary source.
  (E3) The exact values S(1..12) (Harder arXiv:2012.04400 and predecessors).

Everything downstream of (E1)-(E3) is re-derived here from scratch.
"""

from __future__ import annotations

import argparse
import math
import sys
from functools import lru_cache
from collections import Counter, defaultdict

# --------------------------------------------------------------------------
# PART 0 -- external facts (E3) and the documented claims under audit
# --------------------------------------------------------------------------

N_TARGET = 13

# Exact minimum comparator counts, S(n), n = 1..12.  Sources: classical for
# n <= 8 (Knuth TAOCP 5.3.4), Codish-Cruz-Filho-Fonollosa-Schneider-Szeider 2014
# for n = 9,10, Harder arXiv:2012.04400 for n = 11, van Voorhis + known network
# for n = 12.
S_EXACT = {1: 0, 2: 1, 3: 3, 4: 5, 5: 9, 6: 12, 7: 16, 8: 19,
           9: 25, 10: 29, 11: 35, 12: 39}

# The F(N) table as recorded in docs/research/xdomain-bound-theory.md Sec. 0.
# Audited, not trusted.
DOCUMENTED_F = {3: 8, 4: 16, 5: 36, 6: 52, 7: 80, 8: 96, 9: 168, 10: 200,
                11: 256, 12: 288, 13: 392, 14: 424, 15: 480, 16: 512, 17: 784}

# Published lower bounds obtained by Dobbelaere from the two-channel theorem
# (SorterHunter, 2025-04-21).  Audited, not trusted.
DOCUMENTED_LOWER_BOUNDS = {13: 44, 14: 48, 15: 53, 16: 57, 17: 63}

# The claim under audit, verbatim from Sec. 6.2 of the survey: the root splits
# (left-size/left-height | right-size/right-height) said to achieve count <= 512.
DOCUMENTED_SURVIVING_ROOT_SPLITS = [
    ((5, 3), (8, 3)),
    ((6, 3), (7, 3)),
    ((7, 3), (6, 3)),
    ((8, 3), (5, 3)),
    ((4, 2), (9, 4)),
]
DOCUMENTED_CLASS_COUNT = 5

# Sec. 6.2 also records minf(13, d) by root height budget.
DOCUMENTED_MINF_13_BY_HEIGHT = {4: 392, 5: 496, 6: 856}

INF = float("inf")

# --------------------------------------------------------------------------
# check plumbing
# --------------------------------------------------------------------------

CHECKS: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str = "") -> bool:
    CHECKS.append((name, bool(ok), detail))
    return bool(ok)


def hdr(title: str) -> None:
    print()
    print("=" * 78)
    print(title)
    print("=" * 78)


# --------------------------------------------------------------------------
# PART 1 -- the F recursion, re-implemented from the definition in (E2)
# --------------------------------------------------------------------------
# Convention: g(s, h) = minimum V over binary tree shapes with exactly s leaves
# and height exactly h ("height" = number of edges on the longest root-leaf
# path; a single leaf has height 0).  Using *exact* height rather than a budget
# makes a shape class well defined and avoids the double counting that a
# "height <= h" convention invites.
#
# A binary tree with s leaves has height h with  ceil(log2 s) <= h <= s - 1.

MAX_H = N_TARGET + 4  # generous; values are strictly increasing well before this


@lru_cache(maxsize=None)
def g(s: int, h: int) -> float:
    """min V over shapes with exactly s leaves and height exactly h."""
    if s < 1 or h < 0:
        return INF
    if s == 1:
        return 0 if h == 0 else INF
    if h == 0:
        return INF
    best = INF
    for s1 in range(1, s):
        s2 = s - s1
        for h1 in range(0, h):
            for h2 in range(0, h):
                if max(h1, h2) != h - 1:
                    continue
                a = g(s1, h1)
                if a == INF:
                    continue
                b = g(s2, h2)
                if b == INF:
                    continue
                v = 2 * (a + b + 2 ** (h1 + h2))
                if v < best:
                    best = v
    return best


@lru_cache(maxsize=None)
def F(n: int) -> float:
    """F(n) = min over all shapes with n leaves of V."""
    return min(g(n, h) for h in range(0, MAX_H))


def minf(n: int, hmax: int) -> float:
    """min V over shapes with n leaves and height at most hmax (the survey's minf)."""
    return min(g(n, h) for h in range(0, hmax + 1))


# --------------------------------------------------------------------------
# PART 2 -- exhaustive shape enumeration (no DP, no pruning): the ground truth
# --------------------------------------------------------------------------
# Shapes are represented as nested tuples; () is a leaf.  We enumerate *all*
# ordered shapes with 13 leaves (Catalan(12) = 208012 of them) and compute V
# directly from the definition.  This is an independent cross-check of the DP:
# the DP's minima must coincide with the enumeration's minima.


@lru_cache(maxsize=None)
def all_shapes(n: int) -> tuple:
    """All ordered binary tree shapes with n leaves, as nested tuples."""
    if n == 1:
        return ((),)
    out = []
    for a in range(1, n):
        for left in all_shapes(a):
            for right in all_shapes(n - a):
                out.append((left, right))
    return tuple(out)


def V(t) -> int:
    """Outcome count of a shape, straight from the definition in (E2)."""
    if t == ():
        return 0
    l, r = t
    return 2 * (V(l) + V(r) + 2 ** (height(l) + height(r)))


def height(t) -> int:
    if t == ():
        return 0
    return 1 + max(height(t[0]), height(t[1]))


def nleaves(t) -> int:
    if t == ():
        return 1
    return nleaves(t[0]) + nleaves(t[1])


def node_sum(t) -> int:
    """Independent formula for V: sum over internal nodes u of
       2**(depth(u) + 1 + height(left(u)) + height(right(u))).
    Derived in docs/s13-shape-case-split.md; checked against V() below."""
    total = 0
    stack = [(t, 0)]
    while stack:
        u, d = stack.pop()
        if u == ():
            continue
        l, r = u
        total += 2 ** (d + 1 + height(l) + height(r))
        stack.append((l, d + 1))
        stack.append((r, d + 1))
    return total


def leaf_profile(t) -> tuple:
    """Sorted multiset of leaf depths."""
    out = []
    stack = [(t, 0)]
    while stack:
        u, d = stack.pop()
        if u == ():
            out.append(d)
        else:
            stack.append((u[0], d + 1))
            stack.append((u[1], d + 1))
    return tuple(sorted(out))


def root_split(t) -> tuple:
    """((leaves_l, height_l), (leaves_r, height_r)) in left-right order."""
    l, r = t
    return ((nleaves(l), height(l)), (nleaves(r), height(r)))


def mirror_canon(t):
    """Canonical form of a shape modulo recursive left/right reflection."""
    if t == ():
        return ()
    a = mirror_canon(t[0])
    b = mirror_canon(t[1])
    return (a, b) if a <= b else (b, a)


def render(t) -> str:
    if t == ():
        return "*"
    return "(%s %s)" % (render(t[0]), render(t[1]))


# --------------------------------------------------------------------------
# reporting
# --------------------------------------------------------------------------


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--corrected", action="store_true",
                    help="audit the corrected claim (this script's findings) "
                         "instead of the claim as documented in the survey")
    ap.add_argument("--quiet", action="store_true", help="suppress detail tables")
    args = ap.parse_args(argv)
    verbose = not args.quiet

    # ------------------------------------------------------------------
    hdr("PART 1  Cross-check of the underlying arithmetic facts")
    # ------------------------------------------------------------------

    # 1a. van Voorhis one-channel recurrence must not be violated by S_EXACT.
    ok = True
    for n in range(2, 13):
        lb = S_EXACT[n - 1] + math.ceil(math.log2(n))
        if S_EXACT[n] < lb:
            ok = False
    check("one-channel recurrence S(n) >= S(n-1)+ceil(log2 n) consistent with S(1..12)",
          ok)
    if verbose:
        print("  n :  S(n)  S(n-1)+ceil(log2 n)   S(n)-S(n-1)")
        for n in range(2, 13):
            print("  %2d :  %3d   %3d                  %2d"
                  % (n, S_EXACT[n], S_EXACT[n - 1] + math.ceil(math.log2(n)),
                     S_EXACT[n] - S_EXACT[n - 1]))

    # 1b. The "citation trap": the shifted form S(n+1) >= S(n)+ceil(log2 n)
    #     (Codish et al. 2014) is strictly weaker; confirm it never exceeds the
    #     standard form, i.e. it cannot be the source of any bound used here.
    shifted_ever_stronger = any(
        S_EXACT[n - 1] + math.ceil(math.log2(n - 1)) >
        S_EXACT[n - 1] + math.ceil(math.log2(n))
        for n in range(3, 13))
    check("shifted (Codish-form) one-channel recurrence is never stronger",
          not shifted_ever_stronger)

    # 1c. S(11) = 35 -- the input to the two-channel chain.  We cannot re-prove
    #     it here; we check it is consistent with its neighbours under both
    #     published recurrences.
    s11_ok = (S_EXACT[11] >= S_EXACT[10] + math.ceil(math.log2(11))
              and S_EXACT[12] >= S_EXACT[11] + math.ceil(math.log2(12)))
    check("S(11)=35 consistent with S(10)=29 and S(12)=39 under one-channel", s11_ok,
          "S(10)+4 = 33 <= 35;  35+4 = 39 = S(12)")

    # ------------------------------------------------------------------
    hdr("PART 2  Re-derivation of F(N) from the recursion (E2)")
    # ------------------------------------------------------------------

    print("  N     F(N)   log2 F(N)  ceil  S(N)-S(N-2)  slack   doc F(N)  agree")
    f_ok = True
    for n in range(3, 18):
        fn = int(F(n))
        lg = math.log2(fn)
        cl = math.ceil(lg)
        if n in S_EXACT and (n - 2) in S_EXACT:
            actual = S_EXACT[n] - S_EXACT[n - 2]
            slack = actual - cl
            act_s, sl_s = "%2d" % actual, "%2d" % slack
            if slack < 0:
                f_ok = False  # would refute (E1)+(E2) outright
        else:
            act_s, sl_s = " -", " -"
        doc = DOCUMENTED_F.get(n)
        agree = "yes" if doc == fn else "NO  (doc=%s)" % doc
        if doc != fn:
            f_ok = False
        print("  %2d  %6d   %8.4f   %2d   %s          %s     %6s   %s"
              % (n, fn, lg, cl, act_s, sl_s, doc, agree))
    check("re-derived F(N) reproduces the documented table for N=3..17", f_ok)

    # 2a. The bound must never exceed a known exact difference (falsification
    #     test for the transcription (E2) together with (E1)).
    viol = [n for n in range(3, 13)
            if math.ceil(math.log2(F(n))) > S_EXACT[n] - S_EXACT[n - 2]]
    check("ceil(log2 F(N)) never exceeds the true S(N)-S(N-2) for N=3..12",
          not viol, "violations: %s" % viol if viol else "no violations")

    # 2b. Reproduce the published lower-bound table for N=13..17 by chaining.
    lb = dict(S_EXACT)
    chain_ok = True
    if verbose:
        print()
        print("  chained two-channel lower bounds:")
    for n in range(13, 18):
        lb[n] = lb[n - 2] + math.ceil(math.log2(F(n)))
        got, want = lb[n], DOCUMENTED_LOWER_BOUNDS[n]
        if got != want:
            chain_ok = False
        if verbose:
            print("    S(%2d) >= S(%2d) + ceil(log2 F(%2d)) = %2d + %2d = %2d   "
                  "(published: %d) %s"
                  % (n, n - 2, n, lb[n - 2], math.ceil(math.log2(F(n))), got,
                     want, "ok" if got == want else "MISMATCH"))
    check("chain reproduces the published lower bounds for N=13..17", chain_ok)

    # 2c. The specific arithmetic of the 13 case.
    f13 = int(F(N_TARGET))
    check("F(13) = 392", f13 == 392, "got %d" % f13)
    check("log2 F(13) = 8.615 (3 dp)", round(math.log2(f13), 3) == 8.615,
          "%.6f" % math.log2(f13))
    check("ceil(log2 F(13)) = 9", math.ceil(math.log2(f13)) == 9)
    check("S(11) + ceil(log2 F(13)) = 44",
          S_EXACT[11] + math.ceil(math.log2(f13)) == 44)
    need = 2 ** 9 + 1
    check("the count needed for the next unit is 513",
          need == 513, "513/392 = %.4f  (a %.1f%% strengthening)"
          % (need / f13, 100 * (need / f13 - 1)))

    # 2d. minf(13, d) by height, as recorded in Sec. 6.2.  Note the survey writes
    #     "minf(13,d)" for what is in fact the *exact*-height minimum: under the
    #     "height at most d" reading, minf(13,5) would be 392, not 496.
    exact_ok = all(int(g(13, d)) == v
                   for d, v in DOCUMENTED_MINF_13_BY_HEIGHT.items())
    budget_ok = all(int(minf(13, d)) == v
                    for d, v in DOCUMENTED_MINF_13_BY_HEIGHT.items())
    check("documented 392/496/856 at d=4/5/6 are the EXACT-height minima", exact_ok)
    check("the same numbers are NOT the height-budget minima "
          "(so 'minf' in the survey means exact height)", not budget_ok,
          "budget reading would give minf(13,5)=%d" % int(minf(13, 5)))
    if verbose:
        print()
        print("  minimum outcome count for 13 leaves, by exact tree height:")
        for h in range(3, 13):
            v = g(13, h)
            print("    height %2d : %s" % (h, "infeasible" if v == INF else int(v)))

    # ------------------------------------------------------------------
    hdr("PART 3  Structural identities (independent re-derivations)")
    # ------------------------------------------------------------------

    shapes13 = all_shapes(N_TARGET)
    check("Catalan(12) = 208012 shapes with 13 leaves", len(shapes13) == 208012,
          "got %d" % len(shapes13))

    # 3a. exhaustive enumeration must agree with the DP, height stratum by stratum
    by_height_min: dict[int, int] = {}
    for t in shapes13:
        h = height(t)
        v = V(t)
        if h not in by_height_min or v < by_height_min[h]:
            by_height_min[h] = v
    dp_ok = all(by_height_min.get(h, INF) == g(13, h) for h in range(0, 13))
    check("exhaustive enumeration of all 208012 shapes reproduces the DP minima",
          dp_ok)

    # 3b. node-sum identity
    sample = shapes13[::997]  # deterministic stride sample, ~209 shapes
    check("node-sum identity V(T) = sum_u 2^(depth(u)+1+h_l(u)+h_r(u))",
          all(V(t) == node_sum(t) for t in sample),
          "checked on %d shapes" % len(sample))

    # 3c. closed form for the perfect tree: V = h * 2^(2h-1)
    def perfect(h):
        return () if h == 0 else (perfect(h - 1), perfect(h - 1))
    check("perfect tree of height h has V = h * 2^(2h-1)",
          all(V(perfect(h)) == h * 2 ** (2 * h - 1) for h in range(1, 6)),
          "h=1..5: %s" % [V(perfect(h)) for h in range(1, 6)])

    # 3d. validate the mirror canonicalisation against an external sequence:
    #     the number of 13-leaf binary trees up to reflection is the
    #     Wedderburn-Etherington number a(13) = 983 (OEIS A001190).
    we = [0, 1, 1, 1, 2, 3, 6, 11, 23, 46, 98, 207, 451, 983]
    we_ok = all(len({mirror_canon(t) for t in all_shapes(n)}) == we[n]
                for n in range(1, 11))
    we13 = len({mirror_canon(t) for t in shapes13})
    check("mirror canonicalisation reproduces Wedderburn-Etherington A001190",
          we_ok and we13 == 983, "13 leaves: %d unordered shapes (expect 983)" % we13)

    # 3e. count of minimum-height (h=4) shapes with 13 leaves, two ways
    h4 = [t for t in shapes13 if height(t) == 4]
    combinatorial = math.comb(8, 3) + 4   # collapse 3 of 8 cherries, or 1 of 4 quads
    check("number of 13-leaf shapes of minimum height 4 is C(8,3)+4 = 60",
          len(h4) == combinatorial == 60, "enumerated %d, formula %d"
          % (len(h4), combinatorial))

    # ------------------------------------------------------------------
    hdr("PART 4  Verdict table: root shape classes for N = 13")
    # ------------------------------------------------------------------
    ceiling = 2 ** 9   # a count of at most 512 is what ceil(log2 .) <= 9 permits
    print("  Admissible iff the forced outcome count is <= %d." % ceiling)
    print("  (count >= %d  =>  ceil(log2 count) >= 10  =>  S(13) >= S(11)+10 = 45)"
          % (ceiling + 1))
    print()
    print("  root split (leaves,height | leaves,height)   min count   verdict")
    print("  " + "-" * 68)

    ordered_survivors = []
    rows = []
    for s1 in range(1, N_TARGET):
        s2 = N_TARGET - s1
        for h1 in range(0, MAX_H):
            for h2 in range(0, MAX_H):
                a, b = g(s1, h1), g(s2, h2)
                if a == INF or b == INF:
                    continue
                v = int(2 * (a + b + 2 ** (h1 + h2)))
                rows.append(((s1, h1), (s2, h2), v))
                if v <= ceiling:
                    ordered_survivors.append(((s1, h1), (s2, h2), v))

    for L, R, v in sorted(ordered_survivors, key=lambda r: (r[2], r[0])):
        print("  (%2d,%d | %2d,%d)                                %6d   SURVIVES"
              % (L[0], L[1], R[0], R[1], v))
    # nearest misses, to show the margin
    misses = sorted((r for r in rows if r[2] > ceiling), key=lambda r: r[2])[:6]
    print()
    print("  nearest excluded root splits (why the rest die):")
    for L, R, v in misses:
        print("  (%2d,%d | %2d,%d)                                %6d   excluded "
              "(>= %d forces ceil(log2) >= 10)" % (L[0], L[1], R[0], R[1], v,
                                                   ceiling + 1))
    infeasible_pairs = sorted({(s, 13 - s) for s in range(1, 7)}
                              - {(min(L[0], R[0]), max(L[0], R[0]))
                                 for L, R, _ in ordered_survivors})
    print()
    print("  root splits by unordered size pair with NO admissible height "
          "assignment: %s" % (infeasible_pairs,))

    unordered_survivors = sorted({tuple(sorted([L, R])) + (v,)
                                  for L, R, v in ordered_survivors})
    all_ordered = {(L, R) for L, R, _ in rows}
    all_unordered = {tuple(sorted([L, R])) for L, R, _ in rows}
    print()
    print("  ordered root shape classes   : %d surviving of %d feasible"
          % (len(ordered_survivors), len(all_ordered)))
    print("  unordered root shape classes : %d surviving of %d feasible"
          % (len(unordered_survivors), len(all_unordered)))
    check("53 feasible unordered / 106 feasible ordered root classes",
          len(all_unordered) == 53 and len(all_ordered) == 106,
          "got %d / %d" % (len(all_unordered), len(all_ordered)))
    for L, R, v in unordered_survivors:
        print("      {(%d,%d),(%d,%d)}  count %d" % (L[0], L[1], R[0], R[1], v))

    doc_set = {tuple(sorted([L, R])) for L, R in DOCUMENTED_SURVIVING_ROOT_SPLITS}
    got_set = {(L, R) for L, R, _ in unordered_survivors}
    missing_from_doc = sorted(got_set - doc_set)
    spurious_in_doc = sorted(doc_set - got_set)
    print()
    print("  vs the documented list (compared as unordered classes):")
    print("      documented, not re-derived : %s" % (spurious_in_doc or "none"))
    print("      re-derived, not documented : %s" % (missing_from_doc or "none"))
    print("      documented list length %d, of which %d are mirror duplicates"
          % (len(DOCUMENTED_SURVIVING_ROOT_SPLITS),
             len(DOCUMENTED_SURVIVING_ROOT_SPLITS) - len(doc_set)))

    # ------------------------------------------------------------------
    hdr("PART 5  Complete-shape enumeration (the sharper case split)")
    # ------------------------------------------------------------------

    survivors = [t for t in shapes13 if V(t) <= ceiling]
    all_values = Counter(V(t) for t in shapes13)
    next_above = min(v for v in all_values if v > ceiling)

    surv_unordered = {mirror_canon(t) for t in survivors}
    print("  13-leaf plane shapes total                 : %d" % len(shapes13))
    print("  13-leaf shapes up to reflection total      : %d" % we13)
    print("  plane shapes with outcome count <= %d     : %d  (%.4f%%)"
          % (ceiling, len(survivors), 100 * len(survivors) / len(shapes13)))
    print("  ... up to reflection                       : %d  (%.3f%%)"
          % (len(surv_unordered), 100 * len(surv_unordered) / we13))
    print("  largest surviving count                    : %d"
          % max(V(t) for t in survivors))
    print("  smallest excluded count                    : %d" % next_above)
    print("  margin                                     : %.2f%%  (any restatement "
          "of the count that changes it by less than this leaves the case split "
          "unchanged)" % (100 * (next_above / ceiling - 1)))
    print()
    print("  survivors by tree height:")
    hh = Counter(height(t) for t in survivors)
    hall = Counter(height(t) for t in shapes13)
    for h in sorted(hall):
        print("    height %d : %5d surviving of %6d  (%s)"
              % (h, hh.get(h, 0), hall[h],
                 "ALL" if hh.get(h, 0) == hall[h] else
                 "%.2f%%" % (100 * hh.get(h, 0) / hall[h])))
    print()
    print("  survivors by leaf-depth profile:")
    prof = defaultdict(list)
    for t in survivors:
        prof[leaf_profile(t)].append(V(t))
    for p, vs in sorted(prof.items()):
        print("    %s  x%-3d values %s"
              % (str(p), len(vs), sorted(set(vs))))
    print()
    print("  survivors by unordered root class:")
    cls = defaultdict(list)
    for t in survivors:
        L, R = root_split(t)
        cls[tuple(sorted([L, R]))].append(V(t))
    class_table = []
    for k, vs in sorted(cls.items()):
        (l1, d1), (l2, d2) = k
        class_table.append((k, len(vs), min(vs), max(vs)))
        print("    {(%d leaves, h%d), (%d leaves, h%d)} : %2d ordered shapes "
              "(%d up to mirror), counts %d..%d, slack below ceiling %d..%d"
              % (l1, d1, l2, d2, len(vs),
                 len({mirror_canon(t) for t in survivors
                      if tuple(sorted(root_split(t))) == k}),
                 min(vs), max(vs), ceiling - max(vs), ceiling - min(vs)))
    if verbose:
        print()
        print("  THE COMPLETE CASE SPLIT: every surviving abstract shape, rendered")
        print("  (`*` = leaf; children written in canonical order; each line is one")
        print("   shape up to reflection, with its plane multiplicity):")
        seen = {}
        for t in survivors:
            seen.setdefault(mirror_canon(t), []).append(t)
        for i, (c, ts) in enumerate(
                sorted(seen.items(), key=lambda kv: (V(kv[0]), render(kv[0]))), 1):
            L, R = root_split(c)
            print("    S%d  count %3d  height %d  root {(%d,h%d),(%d,h%d)}  "
                  "plane multiplicity %2d" % (i, V(c), height(c), L[0], L[1],
                                              R[0], R[1], len(ts)))
            print("        %s" % render(c))
            print("        leaf depths %s" % (leaf_profile(c),))

    check("every minimum-height (h=4) 13-leaf shape survives",
          hh.get(4, 0) == hall[4] == 60)
    check("no shape of height >= 6 survives",
          all(height(t) <= 5 for t in survivors))
    check("exactly 24 of the %d height-5 shapes survive" % hall[5],
          hh.get(5, 0) == 24)
    check("total surviving complete shapes = 84 plane / 6 up to reflection",
          len(survivors) == 84 and len(surv_unordered) == 6,
          "the 84 plane shapes collapse to 6 abstract shapes")
    check("each surviving outcome value is realised by exactly one abstract shape "
          "per root class",
          all(len({mirror_canon(t) for t in survivors
                   if V(t) == v and tuple(sorted(root_split(t))) == k}) == 1
              for k in cls for v in set(cls[k])))
    check("shape-level exclusion margin is clean (512 -> %d)" % next_above,
          next_above == 528)

    # 5a. leaf-depth profiles: the cheapest engine-side filter.
    surviving_profiles = sorted(prof)
    print()
    print("  ENGINE FILTER -- the surviving leaf-depth profiles.  Under the")
    print("  interpretation that leaf i sits at depth delta(C,i) (the length of")
    print("  the max-path from channel i), only these %d multisets are admissible:"
          % len(surviving_profiles))
    for p in surviving_profiles:
        kraft = sum(2 ** (-d) for d in p)
        print("    %s   Kraft sum = %s   shapes: %s"
              % (Counter(p), "1" if abs(kraft - 1) < 1e-12 else "%.6f" % kraft,
                 sorted(set(prof[p]))))
    check("every surviving leaf-depth profile satisfies Kraft equality",
          all(abs(sum(2.0 ** (-d) for d in p) - 1) < 1e-12
              for p in surviving_profiles))
    check("exactly 4 leaf-depth profiles survive", len(surviving_profiles) == 4)

    # 5b. independent corroboration of the height restriction, from a DIFFERENT
    #     theorem: van Voorhis one-channel gives |C| >= S(12) + delta(C,i) for
    #     every channel i, so a 44-comparator 13-sorter has delta(C,i) <= 5 for
    #     all i, i.e. the max-path tree has height <= 5; and a 13-leaf binary
    #     tree has height >= ceil(log2 13) = 4.
    one_channel_hmax = 44 - S_EXACT[12]
    hmin = math.ceil(math.log2(N_TARGET))
    check("one-channel theorem independently forces tree height in {4,5}",
          one_channel_hmax == 5 and hmin == 4
          and set(hh) == {4, 5},
          "S(12)=39 gives delta <= 5; ceil(log2 13) = 4; "
          "shape enumeration independently yields heights %s" % sorted(hh))
    # how much does the shape count add over the one-channel restriction alone?
    profiles_h5 = {leaf_profile(t) for t in shapes13 if height(t) <= 5}
    print()
    print("  profiles allowed by the one-channel theorem alone (height <= 5): %d"
          % len(profiles_h5))
    print("  profiles allowed after the shape count                        : %d"
          % len(surviving_profiles))

    # 5c. sensitivity of the case split to the exact ceiling.  Recorded because
    #     one of these readings accidentally produces the number 5 and could be
    #     mistaken for confirmation of the documented claim.
    print()
    print("  sensitivity of the case split to the admissibility ceiling:")
    print("    ceiling   plane shapes   abstract shapes   root classes (unord.)")
    sens = {}
    for cap in (391, 392, 400, 416, 496, 511, 512, 527, 528):
        sv = [t for t in shapes13 if V(t) <= cap]
        ab = len({mirror_canon(t) for t in sv})
        rc = len({tuple(sorted(root_split(t))) for t in sv})
        sens[cap] = (len(sv), ab, rc)
        note = ""
        if cap == 512:
            note = "   <-- the derived ceiling, 2^9"
        if cap == 511:
            note = "   <-- strict reading; NOTE it yields 5 abstract shapes"
        print("    %7d   %12d   %15d   %21d%s" % (cap, len(sv), ab, rc, note))
    check("a strict-inequality reading of the ceiling would give 5 abstract "
          "shapes (numerical coincidence, not the documented claim)",
          sens[511][1] == 5,
          "the documented claim counts root splits, not shapes, so this is not "
          "its provenance; recorded to prevent accidental 'confirmation'")

    # ------------------------------------------------------------------
    hdr("PART 6  Verdict on the claim")
    # ------------------------------------------------------------------

    n_ordered = len(ordered_survivors)
    n_unordered = len(unordered_survivors)

    if args.corrected:
        print("  Auditing the CORRECTED claim.")
        check("corrected: exactly 3 unordered root shape classes survive",
              n_unordered == 3, "got %d" % n_unordered)
        check("corrected: exactly 6 ordered root shape classes survive",
              n_ordered == 6, "got %d" % n_ordered)
        check("corrected: exactly 84 plane / 6 abstract complete shapes survive",
              len(survivors) == 84 and len(surv_unordered) == 6)
    else:
        print("  Auditing the claim AS DOCUMENTED in "
              "docs/research/xdomain-bound-theory.md Sec. 6.2 and")
        print("  docs/research/synthesis-ranked-queue.md: "
              "\"only 5 root tree-shape classes\".")
        print()
        print("  re-derived ordered classes  : %d" % n_ordered)
        print("  re-derived unordered classes: %d" % n_unordered)
        print("  documented                  : %d" % DOCUMENTED_CLASS_COUNT)
        print()
        print("  Diagnosis: the documented list enumerates BOTH orientations of the")
        print("  height-4 splits -- (5,3|8,3) and (8,3|5,3), (6,3|7,3) and (7,3|6,3)")
        print("  -- but only ONE orientation of the height-5 split (4,2|9,4).  The")
        print("  recursion V = 2*(Vl + Vr + 2^(hl+hr)) is symmetric under exchanging")
        print("  the two subtrees, so (9,4|4,2) is admissible with the identical")
        print("  count 496 and was dropped.  5 is neither the ordered count (6) nor")
        print("  the unordered count (3); it is an enumeration slip, not a")
        print("  mathematical disagreement.")
        check("documented claim: exactly 5 root shape classes survive",
              n_ordered == DOCUMENTED_CLASS_COUNT
              or n_unordered == DOCUMENTED_CLASS_COUNT,
              "ordered=%d, unordered=%d, documented=%d"
              % (n_ordered, n_unordered, DOCUMENTED_CLASS_COUNT))

    # ------------------------------------------------------------------
    hdr("SUMMARY")
    # ------------------------------------------------------------------
    failed = [c for c in CHECKS if not c[1]]
    for name, ok, detail in CHECKS:
        print("  [%s] %s%s" % ("PASS" if ok else "FAIL", name,
                               ("   -- " + detail) if detail else ""))
    print()
    if failed:
        print("  %d of %d checks FAILED." % (len(failed), len(CHECKS)))
        print("  The counting mathematics is reproduced exactly; the failure(s)")
        print("  above are about the *stated class count*, not about F(13)=392 or")
        print("  the exclusion of the other shapes.  See docs/s13-shape-case-split.md.")
        return 1
    print("  All %d checks passed." % len(CHECKS))
    return 0


if __name__ == "__main__":
    sys.setrecursionlimit(10000)
    sys.exit(main())
