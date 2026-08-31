#!/usr/bin/env python3
"""
verify_kraft_dispute.py -- INDEPENDENT adversarial re-derivation of the disputed
steps in

    D. C. Van Voorhis, "Toward a Lower Bound for Sorting Networks",
    in Miller & Thatcher (eds.), *Complexity of Computer Computations*,
    Plenum Press 1972, pp. 119-129.

This file was written from scratch against the chapter text (book pp. 121-125).
It deliberately does NOT import, copy or consult tools/verify_huffman2.py,
.build/v3-theory/vv_core.py or .build/v3-theory/stress.py.

Conventions (0-indexed, matching the chapter's picture):
  * channels 0 .. n-1;  channel n-1 is the TOP wire, so o_N = channel n-1.
  * a comparator is a pair (a,b) with a < b; it emits its LARGER input on the
    HIGHER lead b ("comparators ... all emit their larger input on their higher
    output lead", p. 119).
  * a network is a time-ordered list of comparators.

Objects built here, each traceable to a sentence of the chapter:

  p_i        (p.120) path of the largest value entered at lead i, to o_N.
  MAX(T)     (p.121) union of the p_i.
  branch node(p.121) a comparator of MAX(T) both of whose leads can carry the
             largest value; the chapter asserts there are exactly N-1 of them
             and calls them c_1..c_{N-1}.
  pass-through: a comparator ON MAX(T) that is not a branch node.  The chapter
             does not name these; their existence is the first fault line.
  nc(c_j)    (p.122) #comparators from i_{j1} to c_j  +  #from i_{j2} to c_j
             +  #from c_j to o_N, with c_j counted exactly once, where
             i_{j1}, i_{j2} are the leads of the LONGEST max-paths through
             L(c_j) and R(c_j).
             Two readings are computed:
               LITERAL  -- count comparators of T (pass-throughs included).
               TREE     -- count branch nodes only (i.e. edges of the binary
                           tree of Fig. 5).
  q_j        (p.122) the path of the SECOND largest value from the lower output
             lead of c_j to o_{N-1}.  Traced with the largest value present in
             the network, so that if the two re-meet the second largest
             correctly takes the low lead.
  p(2,T)     (p.121) the greatest number of comparators that can be pruned by
             giving two input leads the two highest values = max over unordered
             pairs of the size of the UNION of the two traced paths.

Disputed statements, restated exactly:
  (5)  p(2,T)  =  max_j [ nc(c_j) + nc(q_j) ]
  (6)  sum_j 2^{-nc(q_j)}  =  1
  (7)  sum_j 2^{-[p(2,T) - nc(c_j)]}  <=  1
  (8)  p(2,T)  >=  ceil(log2 f(MAX(T)))
  (9)  f(MAX(T)) = sum_j 2^{+nc(c_j)}
  (12) P(2,N) >= ceil(log2 F(N)),  F(N) = min over binary trees B of f(B)
  (13) f(B) = 2[ f(L(B)) + f(R(B)) + 2^{lp(L(B))+lp(R(B))} ],  f(leaf)=lp(leaf)=0

Run:  python3 tools/verify_kraft_dispute.py            (full)
      python3 tools/verify_kraft_dispute.py --fast     (small stress sample)
"""

from __future__ import annotations

import argparse
import itertools
import math
import random
import sys
from fractions import Fraction

# --------------------------------------------------------------------------
# 0.  basic network machinery
# --------------------------------------------------------------------------


def is_sorter(net, n):
    """0/1 principle: check every 0/1 vector is sorted (ascending, low->high)."""
    for mask in range(1 << n):
        v = [(mask >> i) & 1 for i in range(n)]
        for (a, b) in net:
            if v[a] > v[b]:
                v[a], v[b] = v[b], v[a]
        if any(v[i] > v[i + 1] for i in range(n - 1)):
            return False
    return True


def apply_net(net, v):
    v = list(v)
    for (a, b) in net:
        if v[a] > v[b]:
            v[a], v[b] = v[b], v[a]
    return v


def max_path(net, n, start):
    """Comparator indices traversed by the largest value entered at lead `start`.

    Returns (list_of_indices, final_channel).  The largest value always leaves a
    comparator on the high lead, so this is the chapter's p_j (p.120).
    """
    ch = start
    idx = []
    for t, (a, b) in enumerate(net):
        if ch == a:
            ch = b
            idx.append(t)
        elif ch == b:
            idx.append(t)
    return idx, ch


def two_value_paths(net, n, hi_lead, lo_lead):
    """Trace the two largest values simultaneously.

    `hi_lead` carries the largest input value, `lo_lead` the second largest.
    Returns (idx_hi, idx_lo, meet_index, final_hi, final_lo) where idx_* are the
    comparator indices each token traverses and meet_index is the index of the
    FIRST comparator at which the two tokens are compared (None if never).

    This is exactly Green's pruning with k=2 (p.121): the set of comparators
    removed is the UNION set(idx_hi) | set(idx_lo).
    """
    ph, pl = hi_lead, lo_lead
    ih, il = [], []
    meet = None
    for t, (a, b) in enumerate(net):
        hin = ph in (a, b)
        lin = pl in (a, b)
        if hin and lin:
            if meet is None:
                meet = t
            ph, pl = b, a
            ih.append(t)
            il.append(t)
        elif hin:
            ph = b
            ih.append(t)
        elif lin:
            pl = b
            il.append(t)
    return ih, il, meet, ph, pl


def p2(net, n):
    """p(2,T): greatest number of comparators pruned over all pairs of leads."""
    best = -1
    arg = None
    for i, j in itertools.combinations(range(n), 2):
        ih, il, meet, fh, fl = two_value_paths(net, n, i, j)
        assert fh == n - 1, "largest did not reach o_N"
        assert fl == n - 2, "second largest did not reach o_{N-1}"
        u = len(set(ih) | set(il))
        if u > best:
            best, arg = u, (i, j)
    return best, arg


def p1(net, n):
    """p(1,T): greatest number of comparators pruned with one high value."""
    return max(len(max_path(net, n, i)[0]) for i in range(n))


# --------------------------------------------------------------------------
# 1.  MAX(T), branch nodes, the binary tree of Fig. 5
# --------------------------------------------------------------------------


class MaxTree:
    """The MAX subnetwork of T, decomposed into branch nodes + pass-throughs."""

    def __init__(self, net, n):
        self.net = net
        self.n = n
        self.paths = {i: max_path(net, n, i)[0] for i in range(n)}
        for i in range(n):
            assert max_path(net, n, i)[1] == n - 1

        self.max_sub = set()
        for i in range(n):
            self.max_sub |= set(self.paths[i])

        # sweep once, maintaining for each channel the group of input leads
        # whose max-path currently sits on it.
        cur = {c: frozenset([c]) for c in range(n)}
        self.branch = []            # comparator indices, in time order = c_1..c_{N-1}
        self.passthrough = set()    # comparator indices on MAX(T) that are not branch
        self.left = {}              # branch idx -> frozenset of leads arriving low
        self.right = {}             # branch idx -> frozenset of leads arriving high
        for t, (a, b) in enumerate(net):
            ga, gb = cur.get(a), cur.get(b)
            if ga and gb:
                self.branch.append(t)
                self.left[t] = ga
                self.right[t] = gb
                cur[b] = ga | gb
                cur[a] = None
            elif ga:
                self.passthrough.add(t)
                cur[b] = ga
                cur[a] = None
            elif gb:
                self.passthrough.add(t)
                cur[b] = gb
                cur[a] = None
        self.root = self.branch[-1] if self.branch else None
        assert cur[n - 1] == frozenset(range(n)), "MAX(T) is not a tree rooted at o_N"
        assert self.passthrough | set(self.branch) == self.max_sub

        # sanity: the chapter's N-1 claim, for branch nodes
        self.n_branch = len(self.branch)

        self.subtree = {t: self.left[t] | self.right[t] for t in self.branch}

    # ---- nc(c_j), both readings -----------------------------------------

    def _count_before(self, lead, t, only_branch):
        """#comparators on p_lead strictly before comparator index t."""
        seq = self.paths[lead]
        k = seq.index(t)
        pre = seq[:k]
        if only_branch:
            bs = set(self.branch)
            return sum(1 for x in pre if x in bs)
        return len(pre)

    def _count_from(self, t, only_branch):
        """#comparators from c_j to o_N inclusive of c_j, along the max path."""
        lead = next(iter(self.subtree[t]))
        seq = self.paths[lead]
        k = seq.index(t)
        post = seq[k:]
        if only_branch:
            bs = set(self.branch)
            return sum(1 for x in post if x in bs)
        return len(post)

    def nc(self, t, reading):
        """nc(c_t).  reading in {'literal','tree'}."""
        ob = (reading == "tree")
        a = max(self._count_before(l, t, ob) for l in self.left[t])
        b = max(self._count_before(l, t, ob) for l in self.right[t])
        d = self._count_from(t, ob)
        return a + b + d

    def nc_all(self, reading):
        return {t: self.nc(t, reading) for t in self.branch}

    def realizing_pair(self, t, reading):
        """(i_{j1}, i_{j2}) -- the leads of the two longest paths through L,R."""
        ob = (reading == "tree")
        l = max(self.left[t], key=lambda x: self._count_before(x, t, ob))
        r = max(self.right[t], key=lambda x: self._count_before(x, t, ob))
        return l, r

    def f(self, reading):
        return sum(2 ** v for v in self.nc_all(reading).values())

    # ---- q_j and the MAX2 subnetwork -------------------------------------

    def q(self, t):
        """Comparator indices on q_j, the second largest value's path from the
        LOW output lead of c_j to o_{N-1}.  Traced with the largest value still
        in the network, so a re-meeting is handled correctly."""
        a, b = self.net[t]
        ph, pl = b, a            # after c_j: max on high lead, 2nd max on low
        idx = []
        for s in range(t + 1, len(self.net)):
            x, y = self.net[s]
            hin = ph in (x, y)
            lin = pl in (x, y)
            if hin and lin:
                ph, pl = y, x
                idx.append(s)
            elif hin:
                ph = y
            elif lin:
                pl = y
                idx.append(s)
        assert pl == self.n - 2, "q_j did not reach o_{N-1}"
        assert ph == self.n - 1
        return idx

    def q_all(self):
        return {t: self.q(t) for t in self.branch}

    def max_path_after(self, t):
        """Comparator indices strictly after c_j on the max path c_j -> o_N."""
        lead = next(iter(self.subtree[t]))
        seq = self.paths[lead]
        k = seq.index(t)
        return seq[k + 1:]


# --------------------------------------------------------------------------
# 2.  F(N) by exact minimisation over binary trees  (eq (11)+(13))
# --------------------------------------------------------------------------


def F_table(nmax):
    """best[nleaves][height] = min f(B); returns F(N) list, F(1)=0."""
    HMAX = nmax + 1
    NEG = None
    best = [[None] * (HMAX + 1) for _ in range(nmax + 1)]
    best[1][0] = 0
    for n in range(2, nmax + 1):
        for k in range(1, n):
            m = n - k
            for h1 in range(0, HMAX + 1):
                if best[k][h1] is None:
                    continue
                for h2 in range(0, HMAX + 1):
                    if best[m][h2] is None:
                        continue
                    h = 1 + max(h1, h2)
                    if h > HMAX:
                        continue
                    val = 2 * (best[k][h1] + best[m][h2] + 2 ** (h1 + h2))
                    if best[n][h] is None or val < best[n][h]:
                        best[n][h] = val
    F = [None] * (nmax + 1)
    for n in range(1, nmax + 1):
        cand = [v for v in best[n] if v is not None]
        F[n] = min(cand)
    return F, best


# --------------------------------------------------------------------------
# 3.  network zoo -- everything CONSTRUCTED, nothing hard-coded from a table
# --------------------------------------------------------------------------


def bubble(n):
    net = []
    for i in range(n - 1):
        for j in range(n - 1 - i):
            net.append((j, j + 1))
    return net


def insertion(n):
    net = []
    for i in range(1, n):
        for j in range(i, 0, -1):
            net.append((j - 1, j))
    return net


def oe_transposition(n):
    net = []
    for r in range(n):
        for j in range(r % 2, n - 1, 2):
            net.append((j, j + 1))
    return net


def batcher_oem(n):
    """Batcher odd-even mergesort (Knuth 5.2.2 Alg. M), 0-indexed, min->low."""
    net = []
    m = 1
    while m < n:
        m *= 2
    p = 1
    while p < m:
        k = p
        while k >= 1:
            j = k % p
            while j <= m - 1 - k:
                for i in range(0, min(k, m - j - k)):
                    if (i + j) // (2 * p) == (i + j + k) // (2 * p):
                        a, b = i + j, i + j + k
                        if a < n and b < n:
                            net.append((a, b))
                j += 2 * k
            k //= 2
        p *= 2
    return net


def random_sorter(rng, n, extra):
    """random comparator prefix, then a bubble network, then greedy thinning."""
    net = [tuple(sorted(rng.sample(range(n), 2))) for _ in range(extra)]
    net += bubble(n)
    assert is_sorter(net, n)
    order = list(range(len(net)))
    rng.shuffle(order)
    removed = set()
    for i in order:
        cand = [c for k, c in enumerate(net) if k not in removed and k != i]
        if is_sorter(cand, n):
            removed.add(i)
    out = [c for k, c in enumerate(net) if k not in removed]
    assert is_sorter(out, n)
    return out


def relabel(net, perm):
    out = []
    for (a, b) in net:
        x, y = perm[a], perm[b]
        out.append((x, y) if x < y else (y, x))
    return out


# --------------------------------------------------------------------------
# 4.  the audit of one network
# --------------------------------------------------------------------------


def audit(net, n, Ftab):
    mt = MaxTree(net, n)
    P2, pair = p2(net, n)
    ncL = mt.nc_all("literal")
    ncT = mt.nc_all("tree")
    qs = mt.q_all()
    kraft = sum(Fraction(1, 2 ** len(qs[t])) for t in mt.branch)

    # eq (5) as written
    eq5 = max(ncL[t] + len(qs[t]) for t in mt.branch)
    eq5_tree = max(ncT[t] + len(qs[t]) for t in mt.branch)

    # overlap: q_j vs the max path after c_j -- "the pruned paths re-meet"
    overlap = {t: len(set(qs[t]) & set(mt.max_path_after(t))) for t in mt.branch}

    fL = mt.f("literal")
    fT = mt.f("tree")

    # ---- the "MAX and MAX2 are comparator-disjoint" defence -------------
    # The most natural steelman: if no comparator lies on both MAX(T) and some
    # q_j, then (a) eq (5) has nothing to double-count and (b) each q_j follows
    # high leads throughout, so the MAX2 leaves are prefix-free and (6) holds
    # as an inequality.  The defence stands or falls on this disjointness.
    max2 = set()
    for t in mt.branch:
        max2 |= set(qs[t])
    disjoint_all = not (max2 & mt.max_sub)          # against all of MAX(T)
    disjoint_branch = not (max2 & set(mt.branch))   # against branch nodes only

    # ---- the candidate REPAIR ------------------------------------------
    # u_j := the true number of comparators pruned by the best pair of leads
    #        whose max-paths meet at c_j.  Always <= p(2,T) by definition of
    #        p(2,T), with no re-meeting hazard because it is a union.
    # Conjecture (K):  sum_j 2^{-(u_j - nc_tree(c_j))}  <=  1.
    # (K) + [u_j <= p(2,T)] gives eq (8) in the branch-tree reading directly,
    # replacing the chapter's (5)+(6).
    u = {}
    for t in mt.branch:
        best = -1
        for i in mt.left[t]:
            for k in mt.right[t]:
                ih, il, meet, _, _ = two_value_paths(net, n, i, k)
                assert meet == t, "LCA mismatch"
                best = max(best, len(set(ih) | set(il)))
        u[t] = best
    repair_kraft = sum(Fraction(1, 2 ** (u[t] - ncT[t])) for t in mt.branch)
    repair_kraft_lit = sum(Fraction(1, 2 ** (u[t] - ncL[t]))
                           if u[t] >= ncL[t] else Fraction(2 ** (ncL[t] - u[t]))
                           for t in mt.branch)

    def clog2(x):
        return math.ceil(math.log2(x)) if x > 0 else 0

    return dict(
        n=n,
        size=len(net),
        n_branch=mt.n_branch,
        n_passthrough=len(mt.passthrough),
        p2=P2,
        p2_pair=pair,
        p1=p1(net, n),
        nc_literal=ncL,
        nc_tree=ncT,
        q_len={t: len(qs[t]) for t in mt.branch},
        kraft=kraft,
        eq5=eq5,
        eq5_tree=eq5_tree,
        overlap=overlap,
        f_literal=fL,
        f_tree=fT,
        eq8_literal_ok=(P2 >= clog2(fL)),
        eq8_tree_ok=(P2 >= clog2(fT)),
        eq6_equality_ok=(kraft == 1),
        eq6_inequality_ok=(kraft <= 1),
        eq5_ok=(eq5 == P2),
        eq5_le_ok=(eq5 <= P2),
        eq7_ok=(sum(Fraction(2 ** ncL[t], 2 ** P2) for t in mt.branch) <= 1),
        eq7_tree_ok=(sum(Fraction(2 ** ncT[t], 2 ** P2) for t in mt.branch) <= 1),
        conclusion_ok=(P2 >= clog2(Ftab[n])),
        u=u,
        disjoint_all=disjoint_all,
        disjoint_branch=disjoint_branch,
        repair_kraft=repair_kraft,
        repair_ok=(repair_kraft <= 1),
        repair_kraft_lit=repair_kraft_lit,
        repair_lit_ok=(repair_kraft_lit <= 1),
        u_le_p2=all(v <= P2 for v in u.values()),
        m_nonneg=all(u[t] >= ncT[t] for t in mt.branch),
        branch_count_ok=(mt.n_branch == n - 1),
        maxsub_size_ok=(len(mt.max_sub) == n - 1),
        mt=mt,
    )


# --------------------------------------------------------------------------
# 5.  reporting
# --------------------------------------------------------------------------

FAILS = []


def check(name, cond, detail=""):
    status = "PASS" if cond else "FAIL"
    if not cond:
        FAILS.append(name)
    print(f"  [{status}] {name}" + (f"   {detail}" if detail else ""))
    return cond


def hr(t):
    print()
    print("=" * 78)
    print(t)
    print("=" * 78)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fast", action="store_true")
    ap.add_argument("--seed", type=int, default=20260818)
    args = ap.parse_args()

    Ftab, _ = F_table(16)

    # ---------------------------------------------------------------- A
    hr("A.  F(N) from Theorem 1 / eq (11)+(13), against Table 1 (book p.128)")
    published = [None, 0, 2, 8, 16, 36, 52, 80, 96, 168, 200, 256, 288,
                 392, 424, 480, 512]
    mine = [Ftab[n] for n in range(0, 17)]
    print("   N :  1  2  3   4   5   6   7   8    9   10   11   12   13   14   15   16")
    print("  mine:", " ".join(f"{Ftab[n]:4d}" for n in range(1, 17)))
    print("  pub :", " ".join(f"{published[n]:4d}" for n in range(1, 17)))
    check("A1  F(N) reproduces Table 1 for N=1..16",
          all(Ftab[n] == published[n] for n in range(1, 17)))
    check("A2  F(13) = 392 and ceil(log2 F(13)) = 9",
          Ftab[13] == 392 and math.ceil(math.log2(392)) == 9,
          f"ceil(log2 392) = {math.ceil(math.log2(392))}")

    # ---------------------------------------------------------------- B
    hr("B.  The chapter's own worked example: Batcher's 8-sorter (Figs. 3,4,5)")
    b8 = batcher_oem(8)
    check("B0  the constructed 8-sorter sorts and has 19 comparators",
          is_sorter(b8, 8) and len(b8) == 19, f"|T| = {len(b8)}")
    r8 = audit(b8, 8, Ftab)
    mt = r8["mt"]
    print(f"  MAX(T): {len(mt.max_sub)} comparators, "
          f"{r8['n_branch']} branch nodes, {r8['n_passthrough']} pass-throughs")
    ncs = sorted(r8["nc_literal"].values())
    print(f"  nc(c_j) literal (sorted) = {ncs}")
    print(f"  nc(c_j) tree    (sorted) = {sorted(r8['nc_tree'].values())}")
    print(f"  f(MAX(T)) literal = {r8['f_literal']},  tree = {r8['f_tree']}")
    check("B1  Fig. 5's nc multiset {3,3,3,3,4,4,5} is reproduced",
          ncs == [3, 3, 3, 3, 4, 4, 5], f"got {ncs}")
    check("B2  f(MAX(T)) = 96 = F(8) for Batcher's 8-sorter",
          r8["f_tree"] == 96 == Ftab[8])
    qlens = [r8["q_len"][t] for t in mt.branch]
    print(f"  nc(q_j) in time order c_1..c_7 = {qlens}")
    print(f"  eq (6) sum_j 2^-nc(q_j)        = {r8['kraft']} "
          f"= {float(r8['kraft'])}")
    check("B3  eq (6) is NOT an equality on the chapter's own example",
          r8["kraft"] != 1, f"sum = {r8['kraft']}")
    check("B4  but the Kraft INEQUALITY (what (7) actually needs) does hold here",
          r8["kraft"] <= 1)
    check("B5  eq (5) holds on the chapter's own example",
          r8["eq5"] == r8["p2"], f"eq(5) = {r8['eq5']}, true p(2,T) = {r8['p2']}")
    check("B6  eq (8) holds on the chapter's own example (both readings)",
          r8["eq8_literal_ok"] and r8["eq8_tree_ok"])

    # ---------------------------------------------------------------- C
    hr("C.  The disputed counterexample: the 3-sorter T1 = [(0,1),(0,2),(1,2)]")
    T1 = [(0, 1), (0, 2), (1, 2)]
    check("C0  T1 sorts and |T1| = 3 = S(3)", is_sorter(T1, 3) and len(T1) == 3)
    r1 = audit(T1, 3, Ftab)
    mt1 = r1["mt"]
    print(f"  max-paths: " + ", ".join(
        f"p_{i} = {mt1.paths[i]}" for i in range(3)))
    print(f"  MAX(T) = {sorted(mt1.max_sub)}  ({len(mt1.max_sub)} comparators)")
    print(f"  branch nodes c_1..c_{{N-1}} = {mt1.branch}   "
          f"pass-throughs = {sorted(mt1.passthrough)}")
    check("C1  MAX(T1) contains N = 3 comparators, not N-1 = 2",
          len(mt1.max_sub) == 3, "comparator (0,2) is a pass-through")
    check("C2  ...but the number of BRANCH nodes is still N-1 = 2",
          mt1.n_branch == 2)
    for t in mt1.branch:
        l, rr = mt1.realizing_pair(t, "literal")
        print(f"  c@{t} = {T1[t]}: L={sorted(mt1.left[t])} R={sorted(mt1.right[t])}"
              f"  nc_lit={r1['nc_literal'][t]}  nc_tree={r1['nc_tree'][t]}"
              f"  q_j={mt1.q(t)} (len {r1['q_len'][t]})"
              f"  overlap with max path after c_j = {r1['overlap'][t]}")
    print(f"  true p(2,T1) = {r1['p2']} (realised by leads {r1['p2_pair']}); "
          f"|T1| = 3 so p(2,T)=3 is forced")
    print(f"  eq (5) RHS  max_j[nc(c_j)+nc(q_j)]  literal = {r1['eq5']}, "
          f"tree = {r1['eq5_tree']}")
    print(f"  eq (6) sum_j 2^-nc(q_j) = {r1['kraft']} = {float(r1['kraft'])}")
    print(f"  f literal = {r1['f_literal']} -> eq(8) demands p(2,T) >= "
          f"{math.ceil(math.log2(r1['f_literal']))}")
    print(f"  f tree    = {r1['f_tree']} -> eq(8) demands p(2,T) >= "
          f"{math.ceil(math.log2(r1['f_tree']))}")
    check("C3  eq (5) is FALSE for T1 (it over-states p(2,T))",
          r1["eq5"] != r1["p2"] and r1["eq5"] > r1["p2"],
          f"claims {r1['eq5']}, truth {r1['p2']}")
    check("C4  the cause is re-meeting: q_1 shares a comparator with the "
          "max path after c_1", max(r1["overlap"].values()) >= 1)
    check("C5  eq (6) is FALSE for T1 and exceeds 1 (the fatal direction)",
          r1["kraft"] > 1, f"sum = {r1['kraft']}")
    check("C6  eq (7) FAILS for T1 under the literal reading",
          not r1["eq7_ok"])
    check("C7  eq (8) FAILS for T1 under the literal reading of nc / eq (9)",
          not r1["eq8_literal_ok"],
          f"demands {math.ceil(math.log2(r1['f_literal']))}, truth {r1['p2']}")
    check("C8  eq (8) HOLDS for T1 under the branch-tree reading of nc",
          r1["eq8_tree_ok"])
    check("C9  the CONCLUSION P(2,3) >= ceil(log2 F(3)) = 3 still holds for T1",
          r1["conclusion_ok"])
    print(f"  MAX(T1) = {sorted(mt1.max_sub)}; MAX2(T1) = "
          f"{sorted(set().union(*[set(mt1.q(t)) for t in mt1.branch]))}")
    check("C10 the 'MAX and MAX2 are comparator-disjoint' defence FAILS on T1",
          (not r1["disjoint_all"]) and (not r1["disjoint_branch"]),
          "q_1 runs through the pass-through (0,2) AND through the root (1,2)")
    check("C11 by contrast it DOES hold on Batcher's 8-sorter, which is why "
          "Fig. 4 does not expose it", r8["disjoint_all"])

    # a second, equally optimal 3-sorter where nothing goes wrong
    hr("C'. Control: the other optimal 3-sorter T2 = [(0,1),(1,2),(0,1)]")
    T2 = [(0, 1), (1, 2), (0, 1)]
    check("C'0 T2 sorts and |T2| = 3", is_sorter(T2, 3) and len(T2) == 3)
    r2 = audit(T2, 3, Ftab)
    print(f"  MAX(T2) = {sorted(r2['mt'].max_sub)}, pass-throughs = "
          f"{sorted(r2['mt'].passthrough)}")
    print(f"  nc literal = {r2['nc_literal']}, q lens = {r2['q_len']}, "
          f"Kraft = {r2['kraft']}, eq5 = {r2['eq5']}, p2 = {r2['p2']}")
    check("C'1 every disputed statement holds for T2",
          r2["eq5_ok"] and r2["eq6_equality_ok"] and r2["eq8_literal_ok"],
          "so the fault is a property of the network, not of N=3")

    # ---------------------------------------------------------------- D
    hr("D.  Is the failure rare?  Structured + randomised sweep")
    rng = random.Random(args.seed)
    zoo = []
    for n in range(3, 9 if args.fast else 11):
        zoo.append((f"bubble-{n}", bubble(n), n))
        zoo.append((f"insertion-{n}", insertion(n), n))
        zoo.append((f"oetrans-{n}", oe_transposition(n), n))
        zoo.append((f"batcher-{n}", batcher_oem(n), n))
    nrand = 10 if args.fast else 40
    nmaxr = 7 if args.fast else 8
    for n in range(3, nmaxr + 1):
        for k in range(nrand):
            zoo.append((f"rand-{n}-{k}", random_sorter(rng, n, rng.randint(0, 3 * n)), n))
    # channel relabellings of the structured ones (still sorters only if the
    # relabelling is applied to a network that stays a sorter -- filter)
    extra = []
    for name, net, n in list(zoo):
        if n <= 7:
            for k in range(2 if args.fast else 4):
                perm = list(range(n))
                rng.shuffle(perm)
                cand = relabel(net, perm)
                if is_sorter(cand, n):
                    extra.append((name + f"-relab{k}", cand, n))
    zoo += extra

    stats = dict(total=0, eq5_bad=0, eq5_le_bad=0, kraft_gt1=0, kraft_ne1=0,
                 eq8_lit_bad=0, eq8_tree_bad=0, concl_bad=0, passthrough=0,
                 remeet=0, eq7_bad=0, eq7_tree_bad=0, repair_bad=0,
                 repair_lit_bad=0, u_bad=0, m_bad=0)
    worst = []
    repair_bad_ex = []
    for name, net, n in zoo:
        assert is_sorter(net, n), name
        r = audit(net, n, Ftab)
        stats["total"] += 1
        stats["eq5_bad"] += (not r["eq5_ok"])
        stats["eq5_le_bad"] += (not r["eq5_le_ok"])
        stats["kraft_gt1"] += (r["kraft"] > 1)
        stats["kraft_ne1"] += (r["kraft"] != 1)
        stats["eq7_bad"] += (not r["eq7_ok"])
        stats["eq7_tree_bad"] += (not r["eq7_tree_ok"])
        stats["eq8_lit_bad"] += (not r["eq8_literal_ok"])
        stats["eq8_tree_bad"] += (not r["eq8_tree_ok"])
        stats["concl_bad"] += (not r["conclusion_ok"])
        stats["passthrough"] += (r["n_passthrough"] > 0)
        stats["remeet"] += (max(r["overlap"].values()) > 0)
        slack = r["p2"] - (math.ceil(math.log2(r["f_tree"])) if r["f_tree"] else 0)
        stats.setdefault("tight", 0)
        stats.setdefault("tight_and_broken", 0)
        if slack == 0:
            stats["tight"] += 1
            if r["kraft"] > 1:
                stats["tight_and_broken"] += 1
        stats.setdefault("clean", 0)
        stats.setdefault("clean_bad", 0)
        if r["n_passthrough"] == 0:
            stats["clean"] += 1
            if (not r["eq5_le_ok"]) or r["kraft"] > 1 or (not r["disjoint_all"]):
                stats["clean_bad"] += 1
        stats.setdefault("disj_all_bad", 0)
        stats.setdefault("disj_branch_bad", 0)
        stats["disj_all_bad"] += (not r["disjoint_all"])
        stats["disj_branch_bad"] += (not r["disjoint_branch"])
        stats["repair_bad"] += (not r["repair_ok"])
        stats["repair_lit_bad"] += (not r["repair_lit_ok"])
        stats["u_bad"] += (not r["u_le_p2"])
        stats["m_bad"] += (not r["m_nonneg"])
        if not r["conclusion_ok"] or not r["eq8_tree_ok"]:
            worst.append((name, n, r["p2"], r["f_tree"], Ftab[n]))
        if not r["repair_ok"] and len(repair_bad_ex) < 5:
            repair_bad_ex.append((name, n, net, r["repair_kraft"]))
    tot = stats["total"]

    def pct(k):
        return f"{100.0*k/tot:5.1f}%"

    print(f"  networks audited: {tot} (all verified sorters by the 0/1 principle)")
    print(f"  MAX(T) has >=1 pass-through comparator ....... {stats['passthrough']:4d}  {pct(stats['passthrough'])}")
    print(f"  some q_j re-meets the max path after c_j ..... {stats['remeet']:4d}  {pct(stats['remeet'])}")
    print(f"  eq (5) not an equality ....................... {stats['eq5_bad']:4d}  {pct(stats['eq5_bad'])}")
    print(f"  eq (5) RHS strictly EXCEEDS p(2,T) (fatal) ... {stats['eq5_le_bad']:4d}  {pct(stats['eq5_le_bad'])}")
    print(f"  eq (6) not an equality ....................... {stats['kraft_ne1']:4d}  {pct(stats['kraft_ne1'])}")
    print(f"  eq (6) sum > 1 (fatal direction) ............. {stats['kraft_gt1']:4d}  {pct(stats['kraft_gt1'])}")
    print(f"  eq (7) fails, literal nc ..................... {stats['eq7_bad']:4d}  {pct(stats['eq7_bad'])}")
    print(f"  eq (7) fails, tree nc ........................ {stats['eq7_tree_bad']:4d}  {pct(stats['eq7_tree_bad'])}")
    print(f"  eq (8) fails, literal nc ..................... {stats['eq8_lit_bad']:4d}  {pct(stats['eq8_lit_bad'])}")
    print(f"  eq (8) fails, TREE nc ........................ {stats['eq8_tree_bad']:4d}  {pct(stats['eq8_tree_bad'])}")
    print(f"  CONCLUSION p(2,T) >= ceil(log2 F(n)) fails ... {stats['concl_bad']:4d}  {pct(stats['concl_bad'])}")
    print(f"  p(2,T) = ceil(log2 f_tree) exactly, i.e. NO slack .... {stats['tight']:4d}  {pct(stats['tight'])}")
    print(f"  ... of those, eq (6) also fails with sum > 1 ...... {stats['tight_and_broken']:4d}"
          f"  {pct(stats['tight_and_broken'])} of all")
    print(f"  MAX2(T) shares a comparator with MAX(T) ...... {stats['disj_all_bad']:4d}  {pct(stats['disj_all_bad'])}")
    print(f"  MAX2(T) shares a BRANCH NODE with MAX(T) ..... {stats['disj_branch_bad']:4d}  {pct(stats['disj_branch_bad'])}")
    print(f"  networks whose MAX(T) is pass-through-FREE ... {stats['clean']:4d}  {pct(stats['clean'])}")
    print(f"    ... of which any of eq(5)/eq(6)/disjointness fails: "
          f"{stats['clean_bad']:4d}")
    check("D-2 pass-through-free sorters are unaffected: on every "
          "pass-through-free sorter, eq (5), eq (6) and MAX/MAX2 disjointness "
          "all hold. (NOTE: this does NOT show pass-throughs are the sole "
          "obstruction -- that stronger claim was RETRACTED; the obstruction "
          "is escapes, see docs/kraft-repair-wave1.md)", stats["clean_bad"] == 0,
          f"{stats['clean']} pass-through-free networks, 0 failures")
    check("D-1 the 'MAX and MAX2 are comparator-disjoint' defence is REFUTED",
          stats["disj_all_bad"] > 0 and stats["disj_branch_bad"] > 0,
          "this is the strongest steelman and it is false")
    check("D0  the broken lemma fails on networks where the bound is TIGHT, "
          "not only where it has slack", stats["tight_and_broken"] > 0,
          "so this is not a harmless technicality")
    check("D1  eq (5) and eq (6) both fail on a positive fraction of sorters",
          stats["eq5_le_bad"] > 0 and stats["kraft_gt1"] > 0)
    check("D2  eq (8) with the branch-tree reading survives the sweep",
          stats["eq8_tree_bad"] == 0)
    check("D3  the conclusion p(2,T) >= ceil(log2 F(n)) survives the sweep",
          stats["concl_bad"] == 0, f"counterexamples: {worst}")

    hr("D'. The candidate REPAIR of the Kraft step")
    print("  Replace the chapter's (5)+(6) by:")
    print("    u_j := #comparators actually pruned by the best pair of leads")
    print("           whose max-paths merge at c_j   (a UNION, so re-meeting is")
    print("           accounted for);  trivially u_j <= p(2,T).")
    print("    (K)   sum_j 2^{-(u_j - nc_tree(c_j))} <= 1.")
    print("  (K) + u_j <= p(2,T) would give eq (8) in the branch-tree reading")
    print("  with no appeal to MAX2 being a binary tree.  (K) rescues the")
    print("  disputed 3-sorter -- but (K) is ITSELF FALSE (check D'3 below).")
    print(f"  u_j <= p(2,T) violated ....................... {stats['u_bad']:4d}")
    print(f"  m_j = u_j - nc_tree(c_j) < 0 ................. {stats['m_bad']:4d}")
    print(f"  (K) violated ................................. {stats['repair_bad']:4d}"
          f"  {pct(stats['repair_bad'])}")
    print(f"  (K) with nc_LITERAL instead of nc_tree ....... {stats['repair_lit_bad']:4d}"
          f"  {pct(stats['repair_lit_bad'])}  (expected to fail: literal (8) is false)")
    check("D'1 u_j <= p(2,T) always (definitional sanity)", stats["u_bad"] == 0)
    check("D'2 m_j >= 0 always", stats["m_bad"] == 0)
    r1k = r1["repair_kraft"]
    print(f"  on the disputed 3-sorter T1: u = {r1['u']}, nc_tree = {r1['nc_tree']},"
          f"  (K) sum = {r1k}   (exactly 1 -- (K) rescues T1)")

    # ...but (K) is itself false.  Found by hill-climbing (see
    # .build/v3-theory-audit/adversarial.py); pinned here as a fixed test.
    T3 = [(2, 3), (1, 2), (0, 4), (3, 5), (2, 4), (1, 2), (4, 5), (2, 3),
          (0, 3), (3, 4), (1, 3), (1, 2), (0, 3), (0, 1), (1, 2)]
    check("D'4 T3 is a genuine 6-sorter", is_sorter(T3, 6) and len(T3) == 15)
    r3 = audit(T3, 6, Ftab)
    print()
    print("  A 6-sorter T3 that REFUTES the candidate repair (K):")
    print(f"    T3 = {T3}")
    print(f"    branch nodes {r3['mt'].branch}, pass-throughs "
          f"{sorted(r3['mt'].passthrough)}")
    print(f"    nc_tree {r3['nc_tree']}")
    print(f"    u_j     {r3['u']}      p(2,T3) = {r3['p2']}")
    print(f"    m_j     {{{', '.join(f'{t}: {r3['u'][t]-r3['nc_tree'][t]}' for t in r3['mt'].branch)}}}")
    print(f"    (K) sum = {r3['repair_kraft']} = {float(r3['repair_kraft'])}  > 1")
    print(f"    yet eq (8) tree reading still holds: "
          f"ceil(log2 {r3['f_tree']}) = {math.ceil(math.log2(r3['f_tree']))} "
          f"<= {r3['p2']}")
    check("D'3 candidate repair (K) is REFUTED (so the natural union-based "
          "repair of the Kraft step also fails)",
          not r3["repair_ok"], f"(K) sum = {r3['repair_kraft']}")
    check("D'5 ...but eq (8) tree reading and the conclusion survive on T3",
          r3["eq8_tree_ok"] and r3["conclusion_ok"])
    print(f"  (K) violations in the random sweep: {stats['repair_bad']} / {tot}")

    # ---------------------------------------------------------------- E
    hr("E.  Exhaustive attack on the conclusion for n = 3,4 "
       "(all sorters up to size cap)")
    for n, cap in ((3, 4), (4, 6)) if not args.fast else ((3, 4), (4, 5)):
        best_p2 = None
        found = 0
        for net in _all_sorters(n, cap):
            found += 1
            v, _ = p2(net, n)
            if best_p2 is None or v < best_p2:
                best_p2 = v
        need = math.ceil(math.log2(Ftab[n]))
        check(f"E{n}  n={n}: min p(2,T) over all {found} sorters with <= {cap} "
              f"comparators is {best_p2} >= ceil(log2 F({n})) = {need}",
              best_p2 >= need)

    # ---------------------------------------------------------------- F
    hr("F.  Where the load actually is: does the Kraft step carry the 44?")
    print("  Without the Kraft step, the argument yields only")
    print("      p(2,T) >= max_j nc(c_j) = lp(MAX(T)) + (2nd longest arm at root)")
    print("  For the 13-leaf trees minimising f this is:")
    for n in (11, 13):
        need = math.ceil(math.log2(Ftab[n]))
        print(f"    n={n}: ceil(log2 F({n})) = {need}   "
              f"(F({n}) = {Ftab[n]})")
    print("  S(13) >= S(11) + P(2,13) = 35 + 9 = 44, the value TABULATED by")
    print("  Dobbelaere (2025) but never peer-reviewed; the 9 is ceil(log2 F(13))")
    print("  and comes from (12), i.e. from (7), i.e. from (6) -- the equation")
    print("  this script refutes. The best PUBLISHED lower bound remains 43.")

    hr("VERDICT SUMMARY")
    if FAILS:
        print("  UNEXPECTED FAILURES: " + ", ".join(FAILS))
    else:
        print("  All checks returned their expected value.")
    print()
    print("  eq (5)  : REFUTED as an equality and as an upper bound on p(2,T).")
    print("  eq (6)  : REFUTED as an equality; ALSO refuted as an inequality")
    print("            (sum > 1) on optimal sorters -- the fatal direction.")
    print("  eq (7)  : not established, since it is derived from (5)+(6).")
    print("  eq (8)  : FALSE under the literal reading of eq (9);")
    print("            no counterexample found under the branch-tree reading,")
    print("            but the chapter's proof of it is the broken one, and the")
    print("            natural union-based repair (K) is itself false.")
    print("  eq (12) : no counterexample found; unproved by this chapter.")
    print()
    print("  VERDICT: (A) HOLE CONFIRMED.  eq (5) and eq (6) are false under")
    print("  every reading of the chapter's definitions; eq (7) is derived from")
    print("  them and from nothing else; therefore eq (8), (10) and (12) --")
    print("  and hence P(2,13) >= 9 and S(13) >= 44 -- are not proved by this")
    print("  chapter.  They are also not refuted.")
    return 1 if FAILS else 0


def _all_sorters(n, cap):
    """Enumerate EVERY sorting network on n channels with exactly k <= cap
    comparators, k running from the smallest k that admits one.  No pruning, no
    canonical forms: brute force, so nothing can be lost."""
    comps = [(a, b) for a in range(n) for b in range(a + 1, n)]
    out = []
    for k in range(1, cap + 1):
        for net in itertools.product(comps, repeat=k):
            if is_sorter(list(net), n):
                out.append(list(net))
    return out


if __name__ == "__main__":
    sys.exit(main())
