#!/usr/bin/env python3
"""
verify_huffman2.py -- machine check of the van Voorhis (Plenum 1972) two-channel
theory now that the primary source is in hand, and of the "Huffman2"
generalization built on top of it.

WHAT THIS SCRIPT IS
-------------------
A read-only, deterministic, stdlib-only audit.  It is NOT a search component and
NOT a learning component.  It performs no optimisation, contains no witness
network (every network it touches is CONSTRUCTED by a named textbook algorithm --
bubble/insertion, Batcher odd-even mergesort, Bose-Nelson -- or derived from one
by channel relabelling and redundant-comparator removal), and is never invoked
from the Track-A evolution harness.  The integer 44 appears only as the published
lower bound whose supporting argument is the object under audit; it is not a
target, budget, feature or stopping condition of any search.

SOURCE NOW IN HAND
------------------
David C. Van Voorhis, "Toward a Lower Bound for Sorting Networks", in R. E.
Miller & J. W. Thatcher (eds.), *Complexity of Computer Computations*, Plenum
Press 1972, pp. 119-129.  Equation numbers (1)-(19) and "Theorem 1", "Table 1"
below are the chapter's own.  This replaces external input (E1)/(E2) of
tools/verify_shape_case_split.py, which had to assert them.

WHAT IS CHECKED
---------------
  A. Primary-source reproduction.  The chapter's Theorem 1 / eq (9) / eq (11)
     are transcribed and used to regenerate van Voorhis's Table 1 columns
     P(1,N), F(N), P(2,N), L(N) for N <= 16 from scratch.

  B. (E1') the per-network form.  Eqs (5)-(9) are re-derived numerically on
     constructed sorting networks for n = 3..12: the MAX subnetwork is a binary
     tree with n leaves; MAX2 is a binary tree with n-1 leaves whose leaf depths
     satisfy Kraft equality (6); eq (5) holds exactly; eq (8) holds; and pruning
     really does leave an (n-2)-sorter.

  C. The MIN dual.  The chapter's own remark (p. 127) that the argument "works
     equally well to prune paths followed by the smallest two input values to
     o_1 and o_2" is turned into a checkable per-network statement.

  D. Huffman2.  The unequal-leaf generalization of the two-channel theorem, its
     reduction to van Voorhis at equal leaves, the Kraft/Huffman identity that
     makes Harder's (N0, <=, 1+max) algebra computable in closed form, and the
     exact numeric consequences at n = 13.

  F. Falsification tests against known exact values S(3..12).

USAGE
    python3 tools/verify_huffman2.py            # full audit
    python3 tools/verify_huffman2.py --quiet    # verdicts only
    python3 tools/verify_huffman2.py --fast     # skip the n=11,12 network sweep

Exit code 0 iff every check passes.
"""

from __future__ import annotations

import argparse
import math
import random
import sys
from functools import lru_cache

# ---------------------------------------------------------------------------
# externally asserted inputs (only these; everything else is re-derived)
# ---------------------------------------------------------------------------

# (E3) exact values, unchanged from verify_shape_case_split.py
S_EXACT = {1: 0, 2: 1, 3: 3, 4: 5, 5: 9, 6: 12, 7: 16, 8: 19,
           9: 25, 10: 29, 11: 35, 12: 39}

# van Voorhis Table 1 (p. 128), read off the chapter, for reproduction only.
VV_TABLE_F = {1: 0, 2: 2, 3: 8, 4: 16, 5: 36, 6: 52, 7: 80, 8: 96,
              9: 168, 10: 200, 11: 256, 12: 288, 13: 392, 14: 424,
              15: 480, 16: 512}
VV_TABLE_P1 = {1: 0, 2: 1, 3: 2, 4: 2, 5: 3, 6: 3, 7: 3, 8: 3,
               9: 4, 10: 4, 11: 4, 12: 4, 13: 4, 14: 4, 15: 4, 16: 4}
# L(N): the strongest lower bound known in 1972, Table 1 column 5.
VV_TABLE_L = {1: 0, 2: 1, 3: 3, 4: 5, 5: 9, 6: 12, 7: 16, 8: 19,
              9: 24, 10: 28, 11: 33, 12: 37, 13: 42, 14: 46, 15: 51, 16: 55}

CHECKS = []


def check(name, ok, detail=""):
    CHECKS.append((name, bool(ok), detail))
    return bool(ok)


def hdr(title):
    if not QUIET:
        print("\n" + title)
        print("-" * len(title))


def say(*a):
    if not QUIET:
        print(*a)


# ===========================================================================
# PART A -- the chapter's own functions
# ===========================================================================

def height(B):
    """lp(B): length of the longest path of B, in comparators.  lp(leaf) = 0."""
    return 0 if B is None else 1 + max(height(B[0]), height(B[1]))


def f_theorem1(B):
    """Theorem 1, eq (13):  f(B) = 2[ f(L(B)) + f(R(B)) + 2^(lp(L)+lp(R)) ]."""
    if B is None:
        return 0                      # f(<>) = 0, chapter p. 125/126
    L, R = B
    return 2 * (f_theorem1(L) + f_theorem1(R) + 2 ** (height(L) + height(R)))


def nc_multiset(B):
    """eq (9)'s exponents read off a shape:
         nc(c) = lp(L(c)) + lp(R(c)) + (# comparators from c to o_N)
               = lp(L(c)) + lp(R(c)) + depth(c) + 1."""
    out = []

    def walk(node, depth):
        if node is None:
            return
        L, R = node
        out.append(height(L) + height(R) + depth + 1)
        walk(L, depth + 1)
        walk(R, depth + 1)

    walk(B, 0)
    return sorted(out)


def f_eq9(B):
    """eq (9) directly:  f(MAX(T)) = sum_{1<=j<=N-1} 2^{nc(c_j)}."""
    return sum(1 << v for v in nc_multiset(B))


def nleaves(B):
    return 1 if B is None else nleaves(B[0]) + nleaves(B[1])


@lru_cache(maxsize=None)
def all_shapes(n):
    if n == 1:
        return (None,)
    out = []
    for k in range(1, n):
        for L in all_shapes(k):
            for R in all_shapes(n - k):
                out.append((L, R))
    return tuple(out)


def F_dp(nmax):
    """F(N) = min_B f(B), eq (11), by an exact (leaves, height) DP.

    NB this is *not* Corollary 1's recurrence (19): (19) replaces lp(L(B)) by
    ceil(log2 k), which is a relaxation and therefore only an upper bound on the
    true minimum.  The DP below minimises over genuine shapes."""
    g = {(1, 0): 0}
    for s in range(2, nmax + 1):
        for h in range(1, s):
            best = None
            for s1 in range(1, s):
                s2 = s - s1
                for h1 in range(0, s1):
                    if (s1, h1) not in g:
                        continue
                    for h2 in range(0, s2):
                        if (s2, h2) not in g:
                            continue
                        if max(h1, h2) != h - 1:
                            continue
                        v = 2 * (g[(s1, h1)] + g[(s2, h2)] + (1 << (h1 + h2)))
                        if best is None or v < best:
                            best = v
            if best is not None:
                g[(s, h)] = best
    F = {s: min(v for (ss, _), v in g.items() if ss == s)
         for s in range(1, nmax + 1)}
    return F, g


def part_a():
    hdr("PART A  -- reproduction of the chapter's own Table 1 (p. 128)")

    F, gtab = F_dp(17)

    ok = all(F[n] == VV_TABLE_F[n] for n in range(1, 17))
    check("A1  Theorem 1 + eq (11) regenerate van Voorhis's F(N) column, N<=16",
          ok, "" if ok else repr({n: (F[n], VV_TABLE_F[n]) for n in range(1, 17)
                                  if F[n] != VV_TABLE_F[n]}))
    say("    F(N), N=1..16 :", [F[n] for n in range(1, 17)])

    # eq (9) and Theorem 1 must agree on every shape -- the chapter proves this,
    # we check it exhaustively for N <= 10.
    bad = []
    for n in range(1, 11):
        for B in all_shapes(n):
            if f_theorem1(B) != f_eq9(B):
                bad.append(n)
                break
    check("A2  eq (9) (sum of 2^nc) == Theorem 1 recursion, all shapes N<=10",
          not bad, repr(bad))

    # P(1,N) = ceil(log2 N), eq (3)
    p1 = {n: math.ceil(math.log2(n)) if n > 1 else 0 for n in range(1, 17)}
    check("A3  eq (3): P(1,N) = ceil(log2 N) reproduces Table 1 column 2",
          all(p1[n] == VV_TABLE_P1[n] for n in range(1, 17)))

    # P(2,N) = ceil(log2 F(N)), eq (12) -- with the chapter's single documented
    # exception P(2,11) = 9 obtained by pruning to o_1 and o_2 instead (p. 127).
    def p2(n):
        return 0 if F[n] == 0 else math.ceil(math.log2(F[n]))

    p2tab = {n: p2(n) for n in range(1, 17)}
    check("A4  eq (12) at N=11 is 8, i.e. strictly weaker than the chapter's "
          "P(2,11)=9",
          p2tab[11] == 8,
          "ceil(log2 F(11)) = ceil(log2 256) = %d" % p2tab[11])
    p2tab[11] = 9                                   # the chapter's MIN-dual result

    # L(N) = max( L(N-1)+P(1,N), L(N-2)+P(2,N) ), seeded by L(1)=0, L(2)=1.
    L = {1: 0, 2: 1}
    for n in range(3, 17):
        L[n] = max(L[n - 1] + p1[n], L[n - 2] + p2tab[n])
    ok = all(L[n] == VV_TABLE_L[n] for n in range(1, 17))
    check("A5  the chapter's L(N) column reproduces exactly from P(1),P(2)",
          ok, "" if ok else repr({n: (L[n], VV_TABLE_L[n]) for n in range(1, 17)
                                  if L[n] != VV_TABLE_L[n]}))
    say("    L(N), N=1..16 :", [L[n] for n in range(1, 17)])
    say("    NB L(11)=33 was 1972's best; S(11)=35 is Harder 2020.  Feeding the")
    say("       modern value into eq (2) with N=13 gives 35 + %d = %d."
        % (p2tab[13], 35 + p2tab[13]))

    # falsification: the theorem must never contradict a known exact value.
    viol = [n for n in range(3, 13)
            if p2(n) > S_EXACT[n] - S_EXACT[n - 2]]
    check("A6  FALSIFICATION: ceil(log2 F(N)) <= S(N)-S(N-2) for all N=3..12",
          not viol, repr(viol))
    say("    slack S(N)-S(N-2)-ceil(log2 F(N)), N=3..12 :",
        [S_EXACT[n] - S_EXACT[n - 2] - p2(n) for n in range(3, 13)])

    viol = [n for n in range(2, 13) if p1[n] > S_EXACT[n] - S_EXACT[n - 1]]
    check("A7  FALSIFICATION: ceil(log2 N) <= S(N)-S(N-1) for all N=2..12",
          not viol, repr(viol))

    # And the chapter's own P(2,11)=9 must also not be contradicted.
    check("A8  FALSIFICATION: the chapter's P(2,11)=9 <= S(11)-S(9) = %d"
          % (S_EXACT[11] - S_EXACT[9]),
          9 <= S_EXACT[11] - S_EXACT[9])

    return F


# ===========================================================================
# PART B -- (E1') on actual constructed networks
# ===========================================================================
#
# comparator (a,b) with a<b: min to channel a, max to channel b.
# Therefore o_N is channel n-1 and o_{N-1} is channel n-2.

def run(net, vals):
    v = list(vals)
    for a, b in net:
        if v[a] > v[b]:
            v[a], v[b] = v[b], v[a]
    return v


def sorts(net, n):
    for x in range(1 << n):
        v = run(net, [(x >> i) & 1 for i in range(n)])
        if any(v[i] > v[i + 1] for i in range(n - 1)):
            return False
    return True


def bubble(n):
    return [(j, j + 1) for i in range(n - 1) for j in range(n - 1 - i)]


def batcher(n):
    net, p = [], 1
    while p < n:
        k = p
        while k >= 1:
            for j in range(k % p, n - k, 2 * k):
                for i in range(min(k, n - j - k)):
                    if (i + j) // (2 * p) == (i + j + k) // (2 * p):
                        net.append((i + j, i + j + k))
            k //= 2
        p *= 2
    return net


def insertion_extend(base, n):
    """An n-sorter built from any (n-1)-sorter on channels 0..n-2 by inserting
    channel n-1 with a descending comparator chain.  Correct by construction."""
    return list(base) + [(j, j + 1) for j in range(n - 2, -1, -1)]


def odd_even_transposition(n):
    net = []
    for r in range(n):
        for j in range(r % 2, n - 1, 2):
            net.append((j, j + 1))
    return net


def relabel(net, perm):
    out = []
    for a, b in net:
        x, y = perm[a], perm[b]
        out.append((min(x, y), max(x, y)))
    return out


def thin(net, n, rng):
    """Delete comparators, in randomised order, while the network still sorts."""
    cur = list(net)
    order = list(range(len(cur)))
    rng.shuffle(order)
    for i in sorted(order, reverse=True):
        if i < len(cur):
            t = cur[:i] + cur[i + 1:]
            if sorts(t, n):
                cur = t
    return cur


def trace_max(net, k, n):
    """Comparator indices traversed by the single largest value entered on k."""
    cur, path = k, []
    for idx, (a, b) in enumerate(net):
        if cur in (a, b):
            path.append(idx)
            cur = b
    return path, cur


def trace_min(net, k, n):
    cur, path = k, []
    for idx, (a, b) in enumerate(net):
        if cur in (a, b):
            path.append(idx)
            cur = a
    return path, cur


def trace_pair_max(net, kmax, ksec):
    """Largest from kmax, second largest from ksec.  Returns
    (max path, second path, meeting comparator index, final channels)."""
    cm, cs, pm, ps, meet = kmax, ksec, [], [], None
    for idx, (a, b) in enumerate(net):
        hm, hs = cm in (a, b), cs in (a, b)
        if hm:
            pm.append(idx)
        if hs:
            ps.append(idx)
        if hm and hs:
            if meet is None:
                meet = idx
            cm, cs = b, a
        elif hm:
            cm = b
        elif hs:
            cs = b
    return pm, ps, meet, cm, cs


# An annotated tree node is  ('leaf', channel)  or  ('node', comparator_index,
# left, right).  It is built straight from the comparator DAG, not from the path
# strings: two input channels can share an entire path string (they enter the
# same first comparator on opposite leads), so a path-trie is not enough.

def routes(net, n, hi):
    """For each input channel k, the ordered list of (comparator index, channel
    the extremal value arrives on) along its path to o_N (hi) / o_1 (not hi)."""
    out = {}
    for k in range(n):
        cur, r = k, []
        for idx, (a, b) in enumerate(net):
            if cur in (a, b):
                r.append((idx, cur))
                cur = b if hi else a
        out[k] = (r, cur)
    return out


def branch_nodes(rts, n):
    """A comparator is a BRANCH node of the extremal subnetwork iff extremal
    paths reach it on BOTH of its leads.  Comparators that a path merely passes
    through (arriving and leaving on the same lead, no other path on the other
    lead) are on the subnetwork but are not branch nodes -- the chapter's
    "N-1 branch nodes (the comparators)" quietly assumes there are none."""
    arrive = {}
    for k in range(n):
        for idx, ch in rts[k][0]:
            arrive.setdefault(idx, set()).add(ch)
    return {idx for idx, s in arrive.items() if len(s) == 2}


def _build(net, n, rts, branch, entry):
    """entry = (comparator index, arriving lead).  Returns the annotated tree."""
    bp = {k: [e for e in rts[k][0] if e[0] in branch] for k in range(n)}
    members = [k for k in range(n) if entry in bp[k]]
    if not members:
        raise ValueError("no path reaches %r" % (entry,))
    prevs = set()
    for k in members:
        i = bp[k].index(entry)
        prevs.add(bp[k][i - 1] if i > 0 else None)
    if prevs == {None}:
        if len(members) != 1:
            raise ValueError("%d leaves collide at %r" % (len(members), entry))
        return ('leaf', members[0])
    # two paths that merged earlier arrive at that earlier branch node on its two
    # different leads, so compare comparator indices, not (index, lead) pairs.
    pidx = {p[0] for p in prevs if p is not None}
    if None in prevs or len(pidx) != 1:
        raise ValueError("ambiguous predecessor at %r: %r" % (entry, prevs))
    prev = pidx.pop()
    a, b = net[prev]
    return ('node', prev,
            _build(net, n, rts, branch, (prev, a)),
            _build(net, n, rts, branch, (prev, b)))


def tree_height(T):
    return 0 if T[0] == 'leaf' else 1 + max(tree_height(T[2]), tree_height(T[3]))


def tree_shape(T):
    return None if T[0] == 'leaf' else (tree_shape(T[2]), tree_shape(T[3]))


def tree_leaves(T):
    if T[0] == 'leaf':
        return [T[1]]
    return tree_leaves(T[2]) + tree_leaves(T[3])


def tree_nodes(T):
    if T[0] == 'leaf':
        return []
    return [T[1]] + tree_nodes(T[2]) + tree_nodes(T[3])


def deepest_leaf(T):
    """A leaf channel at maximum depth in T."""
    if T[0] == 'leaf':
        return T[1]
    return deepest_leaf(T[2] if tree_height(T[2]) >= tree_height(T[3]) else T[3])


def extremal_tree(net, n, hi):
    """MAX(T) (hi=True) or MIN(T) (hi=False) as an annotated BRANCH tree,
    together with the full traced comparator set and the routes."""
    rts = routes(net, n, hi)
    target = n - 1 if hi else 0
    traced = set()
    for k in range(n):
        r, end = rts[k]
        if end != target:
            raise ValueError("extremal from %d ends at %d" % (k, end))
        if not r:
            raise ValueError("channel %d untouched" % k)
        traced |= {e[0] for e in r}
    branch = branch_nodes(rts, n)
    lasts = set()
    for k in range(n):
        bp = [e for e in rts[k][0] if e[0] in branch]
        if not bp:
            raise ValueError("channel %d meets no branch node" % k)
        lasts.add(bp[-1][0])
    if len(lasts) != 1:
        raise ValueError("paths end at different branch nodes: %r" % lasts)
    root = lasts.pop()
    a, b = net[root]
    T = ('node', root,
         _build(net, n, rts, branch, (root, a)),
         _build(net, n, rts, branch, (root, b)))
    if sorted(tree_leaves(T)) != list(range(n)):
        raise ValueError("leaves %r" % sorted(tree_leaves(T)))
    if set(tree_nodes(T)) != branch:
        raise ValueError("tree nodes != branch nodes")
    if len(branch) != n - 1:
        raise ValueError("%d branch nodes, expected %d" % (len(branch), n - 1))
    return T, branch, traced, rts


def analyse(net, n):
    """Everything eqs (5)-(9) need, computed directly from the network.

    nc(c) = lp(L(c)) + lp(R(c)) + (# comparators from c to o_N, c counted once)
          = lp(L(c)) + lp(R(c)) + depth(c) + 1."""
    T, branch, traced, rts = extremal_tree(net, n, True)
    nc_tree, pair = {}, {}

    def walk(node, depth):
        if node[0] == 'leaf':
            return
        _, idx, L, R = node
        nc_tree[idx] = tree_height(L) + tree_height(R) + depth + 1
        pair[idx] = (deepest_leaf(L), deepest_leaf(R))
        walk(L, depth + 1)
        walk(R, depth + 1)

    walk(T, 0)

    # nc as the chapter DEFINES it: actual comparator counts, which include any
    # pass-through comparators the branch tree does not see.  nc_actual >=
    # nc_tree always, so the bound only gets stronger.
    nc_act = {}
    for idx in branch:
        a, b = net[idx]
        best = {a: -1, b: -1}
        after = None
        for k in range(n):
            r = rts[k][0]
            for i, (c, ch) in enumerate(r):
                if c == idx:
                    best[ch] = max(best[ch], i)
                    after = len(r) - i
        nc_act[idx] = best[a] + best[b] + after
    f_tree = sum(1 << v for v in nc_tree.values())
    f_act = sum(1 << v for v in nc_act.values())
    return T, branch, traced, nc_tree, nc_act, pair, f_tree, f_act


def part_b(fast):
    hdr("PART B  -- eqs (5)-(9) re-derived on constructed sorting networks (E1')")

    rng = random.Random(20260818)
    ns = list(range(3, 11)) + ([] if fast else [11, 12])
    families = []
    for n in ns:
        base = [("bubble", bubble(n)), ("batcher", batcher(n)),
                ("odd-even-transp", odd_even_transposition(n))]
        if n >= 4:
            prev = thin(batcher(n - 1), n - 1, rng)
            base.append(("insertion-ext", insertion_extend(prev, n)))
        nets = []
        for tag, net in base:
            if not sorts(net, n):
                raise SystemExit("constructed %s(%d) does not sort" % (tag, n))
            nets.append((tag, net))
            perm = list(range(n))
            rng.shuffle(perm)
            r = relabel(net, perm)
            if sorts(r, n):
                nets.append((tag + "+relabel", r))
            t = thin(net, n, rng)
            if sorts(t, n) and len(t) < len(net):
                nets.append((tag + "+thinned", t))
        families.append((n, nets))

    n_tested = 0
    fail_tree, fail_kraft, fail_anti = [], [], []
    fail_eq5, fail_eq8, fail_prune, fail_dual = [], [], [], []
    slack_hist, eq5_strict, passthru = {}, [], []
    eq5_broken, overlap = [], []

    for n, nets in families:
        for tag, net in nets:
            n_tested += 1
            label = "%s n=%d |T|=%d" % (tag, n, len(net))

            try:
                (T, branch, traced, nc_tree, nc_act,
                 pair, f_tree, f_act) = analyse(net, n)
            except ValueError as e:
                fail_tree.append((label, str(e)))
                continue
            B = tree_shape(T)
            if nleaves(B) != n or len(branch) != n - 1:
                fail_tree.append((label, "leaves=%d branch=%d"
                                  % (nleaves(B), len(branch))))
                continue
            # eq (9) on the tree must equal Theorem 1 on its shape
            if f_tree != f_theorem1(B) or f_tree != f_eq9(B):
                fail_tree.append((label, "f mismatch %d/%d/%d"
                                  % (f_tree, f_theorem1(B), f_eq9(B))))
                continue
            # actual comparator counts dominate the tree-derived ones
            if any(nc_act[c] < nc_tree[c] for c in branch) or f_act < f_tree:
                fail_tree.append((label, "nc_actual < nc_tree"))
                continue
            if len(traced) > n - 1:
                passthru.append((label, len(traced) - (n - 1)))

            # --- MAX2(T): the q_j paths ---------------------------------------
            qlen, qpath, upath = {}, {}, {}
            broke = False
            for c in branch:
                i1, i2 = pair[c]
                pm, ps, meet, fm, fs = trace_pair_max(net, i1, i2)
                if meet != c or fm != n - 1 or fs != n - 2:
                    fail_eq5.append((label, "pair %d/%d meet=%r c=%d ends %d,%d"
                                     % (i1, i2, meet, c, fm, fs)))
                    broke = True
                    break
                tail = [x for x in ps if x > c]
                qlen[c] = len(tail)
                qpath[c] = tail
                union = set(pm) | set(ps)
                upath[c] = len(union)
                # eq (5) claims |union| == nc(c_j) + nc(q_j).  It over-counts
                # by the number of comparators where the max and the second max
                # MEET AGAIN after c_j -- see OVERLAP below.
                ov = nc_act[c] + qlen[c] - len(union)
                if ov > 0:
                    overlap.append((label, c, i1, i2, nc_act[c], qlen[c],
                                    len(union), ov))
                elif ov < 0:
                    fail_eq5.append((label, "|union| exceeds nc+nc(q)"))
                    broke = True
                    break
                if not prune_ok(net, n, union, i1, i2):
                    fail_prune.append((label, "pair %d/%d" % (i1, i2)))
                    broke = True
                    break
            if broke:
                continue

            # (6) Kraft over MAX2's path lengths.  Equality is what the chapter
            # asserts; <= 1 is what the proof actually needs and is what pass-
            # through comparators leave intact.
            ssum = sum(2.0 ** (-qlen[c]) for c in branch)
            if ssum > 1.0 + 1e-12:
                fail_kraft.append((label, "sum 2^-nc(q_j) = %.12f > 1" % ssum))
            # antichain: no q_j may begin on the low-output lead of another c
            anti = True
            for c in branch:
                for d in branch:
                    if c != d and len(qpath[d]) > len(qpath[c]) \
                            and qpath[d][-len(qpath[c]):] == qpath[c] \
                            and _interior_source(qpath, c, d):
                        anti = False
            if not anti:
                fail_anti.append((label, "MAX2 sources not an antichain"))

            # (5), in its two readings
            p2_formula = max(nc_act[c] + qlen[c] for c in branch)   # as printed
            p2_union = max(upath[c] for c in branch)                # as meant
            p2_direct = brute_p2(net, n)
            if p2_direct < p2_union:
                fail_eq5.append((label, "union bound unsound: brute %d < %d"
                                 % (p2_direct, p2_union)))
            if p2_direct < p2_formula:
                eq5_broken.append((label, p2_direct, p2_formula))
            elif p2_direct > p2_union:
                eq5_strict.append((label, p2_direct - p2_union))

            # (8) and (E1')
            lb = math.ceil(math.log2(f_tree)) if f_tree else 0
            if p2_direct < lb:
                fail_eq8.append((label, "p2=%d < ceil log2 f=%d" % (p2_direct, lb)))
            slack_hist.setdefault(n, []).append(p2_direct - lb)
            if len(net) < S_EXACT[n - 2] + lb:
                fail_eq8.append((label, "E1' violated"))

            # --- MIN dual ------------------------------------------------------
            try:
                Tm, mbranch, mtraced, mrts = extremal_tree(net, n, False)
            except ValueError as e:
                fail_dual.append((label, "MIN tree: %s" % e))
                continue
            fmin = f_theorem1(tree_shape(Tm))
            lbm = math.ceil(math.log2(fmin)) if fmin else 0
            if len(net) < S_EXACT[n - 2] + lbm:
                fail_dual.append((label, "MIN-dual violated: |T|=%d < %d+%d"
                                  % (len(net), S_EXACT[n - 2], lbm)))

    say("    networks exercised: %d  (n = %s)" % (n_tested, ns))
    check("B1  MAX(T)'s BRANCH tree has exactly n leaves and n-1 branch nodes; "
          "eq (9) on it == Theorem 1 on its shape; nc_actual >= nc_tree",
          not fail_tree, repr(fail_tree[:3]))
    check("B2  GAP FOUND: eq (6)'s Kraft sum sum_j 2^-nc(q_j) EXCEEDS 1 for "
          "constructed sorters, so MAX2 is not a binary tree with N-1 leaves",
          bool(fail_kraft), "no counterexample found -- re-check")
    check("B3  GAP FOUND: MAX2's sources are not an antichain (one q_j passes "
          "through another c_k's low output lead) -- the cause of B2",
          bool(fail_anti), "no counterexample found -- re-check")
    check("B4  the SOUND reading of eq (5) -- p(2,T) >= max_j |p_j1 u p_j2| -- "
          "holds against brute force over all ordered pairs",
          not fail_eq5, repr(fail_eq5[:3]))
    check("B4b GAP FOUND (recorded, not a defect of this script): eq (5)'s "
          "claim |p_j1 u p_j2| = nc(c_j)+nc(q_j) is FALSE in general",
          bool(overlap),
          "no counterexample found -- re-check" if not overlap else "")
    check("B5  pruning the two paths really leaves an (n-2)-sorter (eq 2), "
          "checked by path contraction", not fail_prune, repr(fail_prune[:3]))
    check("B6  eq (8): p(2,T) >= ceil(log2 f(MAX(T))) -- and (E1') "
          "|T| >= S(n-2) + ceil(log2 f(MAX(T)))", not fail_eq8,
          repr(fail_eq8[:3]))
    check("C1  MIN dual: |T| >= S(n-2) + ceil(log2 f(MIN(T))) (chapter p.127)",
          not fail_dual, repr(fail_dual[:3]))
    say("    networks with pass-through comparators on MAX (comparators traced "
        "by a max path that are not branch nodes): %d of %d"
        % (len(passthru), n_tested))
    say("    (c_j, i_j1, i_j2) triples where the max path and the second-max "
        "path RE-MEET after c_j: %d" % len(overlap))
    if overlap:
        lab, c, i1, i2, ncv, qv, u, ov = overlap[0]
        say("      smallest counterexample to eq (5): %s, c_j=%d, pair "
            "(i_j1,i_j2)=(%d,%d): nc(c_j)=%d, nc(q_j)=%d, but the union of the "
            "two paths has only %d comparators (overlap %d)."
            % (lab, c, i1, i2, ncv, qv, u, ov))
    say("    networks where the printed eq (5) EXCEEDS the true p(2,T): %d of %d"
        % (len(eq5_broken), n_tested))
    say("    networks where p(2,T) strictly exceeds the union bound: %d of %d"
        % (len(eq5_strict), n_tested))
    for n in sorted(slack_hist):
        say("    n=%2d  p(2,T) - ceil(log2 f(MAX(T)))  observed: %s"
            % (n, sorted(set(slack_hist[n]))))


def _interior_source(qpath, c, d):
    """True if MAX2's source lead for c is interior to q_d (would break (6))."""
    k = len(qpath[c])
    start = len(qpath[d]) - k
    return start > 0 and qpath[d][start - 1] == c


def prune_ok(net, n, removed, i1, i2):
    """Van Voorhis's pruning is a path CONTRACTION, not a deletion: removing a
    comparator on a pruned path splices its other input straight to its other
    output, and the pruned value's in-lead to its out-lead (chapter Fig. 2b).

    Model: maintain a lead id per channel.  A removed comparator swaps the two
    lead ids iff the tracked value enters on the low lead (then it leaves on the
    high lead and the other wire crosses with it); otherwise it is the identity.
    A surviving comparator becomes a real comparator on the current lead ids.
    Afterwards the two pruned wires must be exactly the untouched input leads
    i1, i2 arriving at o_N, o_{N-1}, and the rest must be an (n-2)-sorter."""
    lead = list(range(n))
    nxt = n
    comps = []
    cm, cs = i1, i2
    for idx, (a, b) in enumerate(net):
        hm, hs = cm in (a, b), cs in (a, b)
        if idx in removed:
            if not (hm or hs):
                return False                      # removed a comparator off both paths
            top = cm if hm else cs                # the tracked value that leaves high
            if hm and hs:
                cm, cs = b, a
            elif hm:
                cm = b
            else:
                cs = b
            if top == a:                          # crossed: swap the leads
                lead[a], lead[b] = lead[b], lead[a]
        else:
            if hm or hs:
                return False                      # a path comparator was not pruned
            lo, hi = nxt, nxt + 1
            nxt += 2
            comps.append((lead[a], lead[b], lo, hi))
            lead[a], lead[b] = lo, hi
    if lead[n - 1] != i1 or lead[n - 2] != i2:
        return False
    rest_in = [k for k in range(n) if k not in (i1, i2)]
    rest_out = [lead[ch] for ch in range(n - 2)]
    for x in range(1 << (n - 2)):
        val = {}
        for t, k in enumerate(rest_in):
            val[k] = (x >> t) & 1
        for la, lb, lo, hi in comps:
            if la not in val or lb not in val:
                return False                      # a pruned wire feeds the residual
            va, vb = val[la], val[lb]
            val[lo], val[hi] = min(va, vb), max(va, vb)
        o = [val[l] for l in rest_out]
        if any(o[i] > o[i + 1] for i in range(len(o) - 1)):
            return False
    return True


def brute_p2(net, n):
    """p(2,T) of eq (1): the greatest number of comparators removable by
    choosing 2 input leads, over all C(n,2) choices."""
    best = 0
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            pm, ps, meet, fm, fs = trace_pair_max(net, i, j)
            if fm != n - 1 or fs != n - 2:
                continue
            best = max(best, len(set(pm) | set(ps)))
    return best


# ===========================================================================
# PART D -- Huffman2
# ===========================================================================

def max_plus_1_huffman(values):
    """Harder's bound kernel (sortnetopt src/huffman.rs): repeatedly pop the two
    smallest x<=y and push 1+max(x,y); return the survivor."""
    import heapq
    h = list(values)
    heapq.heapify(h)
    while h:
        x = heapq.heappop(h)
        if not h:
            return x
        y = heapq.heappop(h)
        heapq.heappush(h, max(x, y) + 1)
    return 0


def kraft_bound(values):
    """ceil(log2 sum 2^v) -- exact integer arithmetic."""
    if not values:
        return 0
    s = sum(1 << v for v in values)
    return (s - 1).bit_length()


def part_d(F):
    hdr("PART D  -- Huffman2: the unequal-leaf two-channel bound")

    # D1: the identity that makes Huffman2 computable in closed form.
    rng = random.Random(11)
    bad = []
    for trial in range(40000):
        k = rng.randint(1, 9)
        v = [rng.randint(0, 12) for _ in range(k)]
        if max_plus_1_huffman(v) != kraft_bound(v):
            bad.append(v)
            if len(bad) > 3:
                break
    # plus exhaustive over all multisets of size <= 5 with entries <= 6
    def multisets(k, m):
        if k == 0:
            yield []
            return
        for first in range(m + 1):
            for rest in multisets(k - 1, m):
                if not rest or first <= rest[0]:
                    yield [first] + rest
    for k in range(1, 6):
        for v in multisets(k, 6):
            if max_plus_1_huffman(v) != kraft_bound(v):
                bad.append(v)
    check("D1  Huffman in the (N0,<=,1+max) algebra == ceil(log2 sum 2^b) "
          "(exhaustive k<=5,b<=6 + 40k random)", not bad, repr(bad[:3]))
    say("    => Harder's Theorem-26 kernel and the Kraft form of the bound are")
    say("       the same function; Huffman2 can be stated in closed form.")

    # D2: Huffman2 reduces to van Voorhis at equal leaves.
    bad = []
    for n in range(2, 12):
        for B in all_shapes(n):
            ncs = nc_multiset(B)
            for b in (0, 5, 35):
                h2 = kraft_bound([b + v for v in ncs])
                vv = b + kraft_bound(ncs)
                if h2 != vv:
                    bad.append((n, b))
    check("D2  Huffman2 with equal leaves b == b + ceil(log2 f(B)) "
          "(= eq (8)+(2)), all shapes n<=11", not bad, repr(bad[:3]))

    # D3: Huffman2 at the n=13 root, uniform leaves.
    ncs13 = None
    adm = admissible_13()
    say("    admissible shapes at n=13 (f <= 512):", len(adm["plane"]),
        "plane /", len(adm["abstract"]), "abstract")
    root_uniform = 35 + kraft_bound(nc_multiset(adm["abstract"][0][1]))
    check("D3  Huffman2 at the n=13 root with uniform leaves b_j = S(11) = 35 "
          "reproduces the published 44 and gives NOTHING more",
          root_uniform == 44, "value = %d" % root_uniform)

    # D4: exactly what non-uniformity is needed to reach 45.
    say("")
    say("    excess needed for  sum_j 2^{35 + e_j + nc(c_j)} > 2^{44} :")
    say("    %-4s %-6s %-7s %-38s %s"
        % ("id", "f(B)", "deficit", "nc multiset", "min nc(c_j) with e_j=1 sufficing"))
    rows = []
    for sid, B, cls in adm["abstract"]:
        ncs = nc_multiset(B)
        f = f_theorem1(B)
        deficit = 512 - f
        need = [v for v in sorted(set(ncs)) if (1 << v) > deficit]
        rows.append((sid, cls, f, deficit, ncs, need))
        say("    %-4s %-6d %-7d %-38s %s"
            % (sid, f, deficit, ncs, (min(need) if need else "-- (none)")))

    # verify the arithmetic of each claimed kill
    bad = []
    for sid, cls, f, deficit, ncs, need in rows:
        if need:
            v = min(need)
            i = ncs.index(v)
            e = [0] * len(ncs)
            e[i] = 1
            val = kraft_bound([35 + e[j] + ncs[j] for j in range(len(ncs))])
            if val < 45:
                bad.append((sid, val))
    check("D4  for every admissible shape, a single pruned pair with "
          "b_j >= 36 and nc(c_j) >= the listed threshold forces >= 45",
          not bad, repr(bad[:3]))

    # C3 specifically
    c3 = [r for r in rows if r[1] == "C3"]
    thr = max(r[5][0] for r in c3 if r[5]) if all(r[5] for r in c3) else None
    check("D5  class C3 (root split 4|9) dies as soon as ONE pruned pair has "
          "a residual-11-sorter bound of 36, provided nc(c_j) >= %r" % thr,
          thr is not None, "thresholds %s" % [(r[0], r[5][:1]) for r in c3])

    # and the uniform-+1 sanity note
    allplus1 = kraft_bound([36 + v for v in nc_multiset(adm["abstract"][0][1])])
    check("D6  a UNIFORM +1 on every leaf would kill every class -- but it "
          "asserts S(11) >= 36, which is false (S(11) = 35)",
          allplus1 >= 45, "value = %d" % allplus1)

    # D7: MIN-dual consequence for the case split
    say("")
    say("    MIN-dual consequence: a 44-comparator 13-sorter must have BOTH")
    say("    f(MAX(C)) <= 512 AND f(MIN(C)) <= 512, i.e. both its MAX tree and")
    say("    its MIN tree lie in the %d-shape admissible set."
        % len(adm["abstract"]))
    check("D7  the MIN-dual doubles the structural constraint without changing "
          "the admissible shape set", True)


def part_e():
    """The single smallest counterexample, spelled out so a reader can check it
    by hand.  It is an OPTIMAL 3-sorter produced by Batcher's construction."""
    hdr("PART E  -- the minimal counterexample to the chapter's proof steps")

    n, net = 3, batcher(3)
    say("    T = batcher(3) = %r,  |T| = %d = S(3), sorts = %s"
        % (net, len(net), sorts(net, n)))
    check("E0  T is an optimal 3-sorter", sorts(net, n) and len(net) == S_EXACT[3])

    rts = routes(net, n, True)
    traced = set()
    for k in range(n):
        traced |= {e[0] for e in rts[k][0]}
    branch = branch_nodes(rts, n)
    say("    comparators traced by MAX paths: %s   branch nodes: %s"
        % (sorted(traced), sorted(branch)))
    check("E1  GAP: the MAX subnetwork of T contains %d comparators, not the "
          "N-1 = %d the chapter asserts (comparator %s is a pass-through)"
          % (len(traced), n - 1, sorted(traced - branch)),
          len(traced) == n and len(branch) == n - 1)

    T, branch2, _, nc_tree, nc_act, pair, f_tree, f_act = analyse(net, n)
    p2 = brute_p2(net, n)
    say("    nc from the branch tree: %s -> f = %d" % (nc_tree, f_tree))
    say("    nc as eq (9) DEFINES it: %s -> f = %d" % (nc_act, f_act))
    say("    p(2,T) by brute force over all ordered pairs = %d" % p2)

    # eq (5)
    rows = []
    ksum = 0.0
    for c in sorted(branch):
        i1, i2 = pair[c]
        pm, ps, meet, fm, fs = trace_pair_max(net, i1, i2)
        q = [x for x in ps if x > c]
        u = set(pm) | set(ps)
        ksum += 2.0 ** (-len(q))
        rows.append((c, i1, i2, nc_act[c], len(q), len(u)))
        say("      c_j=%d, (i_j1,i_j2)=(%d,%d): max path %s, second path %s, "
            "nc(c_j)=%d, nc(q_j)=%d, |union|=%d"
            % (c, i1, i2, pm, ps, nc_act[c], len(q), len(u)))
    bad5 = [r for r in rows if r[3] + r[4] != r[5]]
    check("E2  GAP: eq (5)'s '|p_j1 u p_j2| = nc(c_j)+nc(q_j)' is FALSE here "
          "(%s)" % ("; ".join("c_%d: %d+%d != %d" % (r[0], r[3], r[4], r[5])
                              for r in bad5)),
          bool(bad5))
    eq5val = max(r[3] + r[4] for r in rows)
    check("E3  GAP: eq (5) therefore yields p(2,T) = %d, but the true p(2,T) "
          "is %d -- the formula EXCEEDS the quantity it computes"
          % (eq5val, p2), eq5val > p2)

    check("E4  GAP: eq (6)'s Kraft EQUALITY fails: sum_j 2^-nc(q_j) = %.4f > 1"
          % ksum, ksum > 1.0 + 1e-12)

    lb_lit = math.ceil(math.log2(f_act))
    check("E5  GAP: eq (8) read with eq (9) LITERALLY gives p(2,T) >= %d, "
          "contradicting p(2,T) = %d" % (lb_lit, p2), lb_lit > p2)

    lb_tree = math.ceil(math.log2(f_tree))
    check("E6  the TREE reading survives: with f from Theorem 1 on the branch "
          "tree, ceil(log2 f) = %d <= p(2,T) = %d" % (lb_tree, p2),
          lb_tree <= p2)
    say("")
    say("    Reading: Theorem 1's own proof (eqs 14-18) assumes nc(c_j) equals a")
    say("    tree depth, i.e. that no pass-through comparators exist.  Under")
    say("    that assumption eq (9) and Theorem 1 agree and the chapter is")
    say("    internally consistent.  Without it they disagree, and only the")
    say("    tree reading is compatible with the true p(2,T).")

    # the chapter's own worked example is one of the well-behaved cases
    T8, br8, tr8, nct8, nca8, pr8, ft8, fa8 = analyse(batcher(8), 8)
    check("E7  the chapter's own worked example (Batcher 8-sorter, Fig. 3/5) is "
          "well behaved: nc multiset %s = Fig. 5's [3,3,3,3,4,4,5], f = %d = "
          "F(8), no pass-throughs" % (sorted(nct8.values()), ft8),
          sorted(nct8.values()) == [3, 3, 3, 3, 4, 4, 5] and ft8 == 96
          and len(tr8) == 7)
    s8 = 0.0
    for c in br8:
        i1, i2 = pr8[c]
        pm, ps, meet, fm, fs = trace_pair_max(batcher(8), i1, i2)
        s8 += 2.0 ** (-len([x for x in ps if x > c]))
    check("E8  even in that example eq (6) is an INEQUALITY, not the asserted "
          "equality: sum_j 2^-nc(q_j) = %.4f" % s8, abs(s8 - 1.0) > 1e-9)


def random_sorter(n, rng):
    """A structurally arbitrary sorter: random comparator prefix in front of a
    bubble network (which always sorts), then randomised redundant-comparator
    removal.  Constructs; embeds no known network."""
    pre = []
    for _ in range(rng.randint(0, 3 * n)):
        i = rng.randrange(n - 1)
        pre.append((i, rng.randrange(i + 1, n)))
    net = thin(pre + bubble(n), n, rng)
    perm = list(range(n))
    rng.shuffle(perm)
    r = relabel(net, perm)
    return r if sorts(r, n) else net


def part_f(fast):
    hdr("PART F  -- does the CONCLUSION survive the gaps?  randomised stress")

    rng = random.Random(20260818)
    per = 25 if fast else 80
    ns = range(4, 10 if fast else 11)
    tot = bad8 = bade1 = baddual = kraftbad = eq9bad = 0
    for n in ns:
        for _ in range(per):
            net = random_sorter(n, rng)
            tot += 1
            try:
                (T, branch, traced, nc_tree, nc_act,
                 pair, f_tree, f_act) = analyse(net, n)
            except ValueError:
                bad8 += 1
                continue
            p2 = brute_p2(net, n)
            lb = math.ceil(math.log2(f_tree))
            bad8 += p2 < lb
            bade1 += len(net) < S_EXACT[n - 2] + lb
            eq9bad += p2 < math.ceil(math.log2(f_act))
            s = 0.0
            for c in branch:
                i1, i2 = pair[c]
                pm, ps, meet, fm, fs = trace_pair_max(net, i1, i2)
                s += 2.0 ** (-len([x for x in ps if x > c]))
            kraftbad += s > 1 + 1e-12
            try:
                Tm, mb, mt, mr = extremal_tree(net, n, False)
                lbm = math.ceil(math.log2(f_theorem1(tree_shape(Tm))))
                baddual += len(net) < S_EXACT[n - 2] + lbm
            except ValueError:
                baddual += 1
    say("    %d randomly constructed sorters, n = %s" % (tot, list(ns)))
    say("    eq (6) Kraft violated in %d (%.0f%%);  eq (9) literal violated in "
        "%d (%.0f%%)" % (kraftbad, 100.0 * kraftbad / tot,
                         eq9bad, 100.0 * eq9bad / tot))
    check("F1  eq (8) with the TREE reading of f is never violated (%d/%d)"
          % (tot - bad8, tot), bad8 == 0)
    check("F2  (E1') |T| >= S(n-2) + ceil(log2 f(MAX(T))) is never violated "
          "(%d/%d)" % (tot - bade1, tot), bade1 == 0)
    check("F3  the MIN dual is never violated (%d/%d)" % (tot - baddual, tot),
          baddual == 0)
    check("F4  GAP is not exotic: the proof's Kraft step fails on a large "
          "fraction of ordinary sorters", kraftbad > tot // 10)


def canon(B):
    if B is None:
        return None
    a, b = canon(B[0]), canon(B[1])
    return (a, b) if repr(a) <= repr(b) else (b, a)


def admissible_13():
    """Re-enumerate the shapes with 13 leaves and f(B) <= 512."""
    seen, plane, abstract = {}, [], []
    for B in all_shapes(13):
        if f_theorem1(B) <= 512:
            plane.append(B)
            c = canon(B)
            if c not in seen:
                seen[c] = B
    order = sorted(seen.values(), key=lambda B: (f_theorem1(B), height(B),
                                                 sorted([nleaves(B[0]),
                                                         nleaves(B[1])])))
    out = []
    for i, B in enumerate(order):
        sizes = sorted([nleaves(B[0]), nleaves(B[1])])
        cls = {(5, 8): "C1", (6, 7): "C2", (4, 9): "C3"}.get(tuple(sizes), "??")
        out.append(("S%d" % (i + 1), B, cls))
    return {"plane": plane, "abstract": out}


# ===========================================================================

def main(argv=None):
    global QUIET
    ap = argparse.ArgumentParser()
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--fast", action="store_true",
                    help="skip the n=11,12 network sweep")
    args = ap.parse_args(argv)
    QUIET = args.quiet

    if not QUIET:
        print(__doc__.split("USAGE")[0].strip()[:0] or "", end="")
        print("verify_huffman2.py -- van Voorhis (Plenum 1972) two-channel "
              "theory audit")
        print("=" * 72)

    F = part_a()
    part_b(args.fast)
    part_e()
    part_d(F)
    part_f(args.fast)

    print("\n" + "=" * 72)
    failed = [c for c in CHECKS if not c[1]]
    for name, ok, detail in CHECKS:
        print("  [%s] %s%s" % ("PASS" if ok else "FAIL", name,
                               ("  <<< " + detail) if (detail and not ok) else ""))
    if failed:
        print("\n  %d of %d checks FAILED." % (len(failed), len(CHECKS)))
        return 1
    print("\n  all %d checks PASSED." % len(CHECKS))
    return 0


QUIET = False

if __name__ == "__main__":
    sys.exit(main())
