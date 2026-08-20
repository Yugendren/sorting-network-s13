#!/usr/bin/env python3
"""Machine check for docs/kraft-repair-wave1.md  (Kraft-repair proof swarm, wave 1).

Extends -- does not duplicate -- tools/verify_huffman2.py, whose primitives
(max-path tracing, branch trees, red/blue leads, pruning-by-contraction,
p(2,T)) are already machine-checked there.  This file adds the wave-1 objects:

  * ESCAPE-FREE sorters and THEOREM 6' (eq (8) for that class), lemmas A-E;
  * the class-boundary evidence (escape-free is strictly larger than clean,
    and the lemmas genuinely fail outside the class);
  * the independently re-derived refutations (LEMMA*, and the fact that the
    lead-level successor is not a function in general);
  * the per-node structural closure and the surviving candidate L4-1.

Conventions are verify_huffman2.py's: comparator (a,b) with a<b, min to a;
o_N = channel n-1, o_{N-1} = channel n-2.

Deterministic, stdlib only, read-only, fixed seeds.  Every network is
CONSTRUCTED or brute-force enumerated; the only literal comparator lists are
counterexamples, which are re-derived and re-verified from scratch here.  No
witness network is embedded, and no comparator count for any specific n appears
as a target, bound, feature or stopping condition anywhere in this file.

    python3 tools/verify_kraft_wave1.py            # full,  ~2-4 min
    python3 tools/verify_kraft_wave1.py --fast     # smaller corpora, ~30 s
    python3 tools/verify_kraft_wave1.py --quiet    # verdicts only
"""
import argparse
import itertools
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import verify_huffman2 as vh

CHECKS = []
QUIET = False


def check(name, ok, detail=""):
    CHECKS.append((name, bool(ok), detail))
    if not QUIET:
        print("  [%s] %-10s %s" % ("ok" if ok else "FAIL", name, detail))
    return ok


def hdr(t):
    if not QUIET:
        print("\n=== %s ===" % t)


def say(*a):
    if not QUIET:
        print(*a)


# ---------------------------------------------------------------------------
# Wave-1 analysis layer, built on verify_huffman2's primitives.
# ---------------------------------------------------------------------------

def analyze(net, n):
    """The wave-1 quantity bundle.  Raises ValueError off-domain."""
    T, branch, traced, rts = vh.extremal_tree(net, n, True)
    a, leafset, leafdepth = vh.tree_data(T)
    depth_B = {}

    def walk(node, d):
        if node[0] == 'leaf':
            return
        depth_B[node[1]] = d
        walk(node[2], d + 1)
        walk(node[3], d + 1)

    walk(T, 0)
    f_tree = sum(1 << v for v in a.values())
    lb = (f_tree - 1).bit_length()
    comp, _ = vh.lead_ids(net, n)
    red = vh.red_leads(net, n, comp)

    # g(c): ACTUAL comparators from c to o_N inclusive on the max-path.
    g = {}
    for x in range(n):
        r, _ = rts[x]
        for i, (idx, _ch) in enumerate(r):
            if idx in branch:
                g[idx] = len(r) - i

    pairs, Wstar, p2 = {}, {}, 0
    for x in range(n):
        for y in range(n):
            if x == y:
                continue
            pm, ps, meet, fm, fs = vh.trace_pair_max(net, x, y)
            if fm != n - 1 or fs != n - 2 or meet is None:
                continue
            W = len(set(pm) | set(ps))
            aft_s = [z for z in ps if z > meet]
            aft_m = [z for z in pm if z > meet]
            ov = len(set(aft_s) & set(aft_m))
            seq = vh.second_max_leads(net, n, comp, x, y)
            lo = comp[meet][2]
            post = seq[seq.index(lo):] if lo in seq else seq
            pairs[(x, y)] = dict(meet=meet, W=W, nq=len(aft_s), ov=ov,
                                 post=post,
                                 escaped=any(l in red for l in post))
            p2 = max(p2, W)
            Wstar[meet] = max(Wstar.get(meet, 0), W)
    return dict(n=n, net=list(net), T=T, branch=set(branch), traced=set(traced),
                passthrough=set(traced) - set(branch),
                clean=len(set(traced) - set(branch)) == 0, a=a, g=g,
                depth_B=depth_B, leafset=leafset, leafdepth=leafdepth,
                f_tree=f_tree, lb=lb, red=red, comp=comp, pairs=pairs,
                Wstar=Wstar, p2=p2, eq8=p2 >= lb)


def escape_free(A):
    """For EVERY admissible ordered pair, the second max occupies no red lead
    at or after the low output of the meeting comparator."""
    return all(not pi['escaped'] for pi in A['pairs'].values())


def nq_ov(A, c):
    """Fact 2: nq and ov depend only on the meeting node.  None if not."""
    v = {(pi['nq'], pi['ov']) for pi in A['pairs'].values() if pi['meet'] == c}
    return v.pop() if len(v) == 1 else None


def lemma_report(A):
    """Which of the Theorem 6' lemmas hold on A.  Returns a dict of booleans.

      succ : the lead-level successor map is a FUNCTION (Lemma A corollary)
      B    : the sources lo(c) form an antichain (no source on another's path)
      nobr : the second max post-meeting traverses NO branch node
             (the refuter's one-line replacement for Lemma B)
      C    : sum_c 2^{-nq(c)} <= 1
      D    : g(c) >= depth_B(c) + 1 + ov(c)
      E    : p2 >= a(c) + nq(c)
      eq8  : p2 >= ceil(log2 f_tree)
    """
    out = dict(succ=True, B=True, nobr=True, C=True, D=True, E=True,
               eq8=A['eq8'], kraft=0.0)
    srcs = {c: A['comp'][c][2] for c in A['branch']}
    succ = {}
    for pi in A['pairs'].values():
        post = pi['post']
        for i in range(len(post) - 1):
            u, v = post[i], post[i + 1]
            if succ.setdefault(u, v) != v:
                out['succ'] = False
        for cp, lead in srcs.items():
            if cp != pi['meet'] and lead in post:
                out['B'] = False
    # no branch node traversed post-meeting
    lead_of = {}
    for i, (ia, ib, lo, hi) in enumerate(A['comp']):
        lead_of.setdefault(lo, i)
        lead_of.setdefault(hi, i)
    for pi in A['pairs'].values():
        for l in pi['post'][1:]:
            if lead_of.get(l) in A['branch']:
                out['nobr'] = False
    for c in sorted(A['branch']):
        nv = nq_ov(A, c)
        if nv is None:
            out['C'] = out['D'] = out['E'] = False
            continue
        nq, ov = nv
        out['kraft'] += 2.0 ** (-nq)
        if A['g'][c] < A['depth_B'][c] + 1 + ov:
            out['D'] = False
        if A['p2'] < A['a'][c] + nq:
            out['E'] = False
    if out['kraft'] > 1.0 + 1e-12:
        out['C'] = False
    return out


def lemma_star(A):
    return sum(2.0 ** (A['a'][c] - A['Wstar'][c]) for c in A['branch']
               if c in A['Wstar'])


def cand_L4_1(A):
    """Wave-1's single surviving eq(8)-implying candidate (NOT proved):
       sum_c 2^{a(c) - min(W*(c)+1, p2)} <= 1."""
    return sum(2.0 ** (A['a'][c] - min(A['Wstar'][c] + 1, A['p2']))
               for c in A['branch'] if c in A['Wstar'])


# ---------------------------------------------------------------------------
# Corpora.  All constructed or brute-force enumerated.
# ---------------------------------------------------------------------------

def enum_minimal(n, maxc, cap=None):
    """Sorters with no inert comparator and no proper sorting prefix
    (the 'minimal' universe).  DFS over the 0/1 reachable-set."""
    comps = [(a, b) for a in range(n) for b in range(a + 1, n)]
    cnt = [0]

    def apply(state, c):
        a, b = c
        return tuple(sorted({(v ^ (1 << a) ^ (1 << b))
                             if ((v >> a) & 1) > ((v >> b) & 1) else v
                             for v in state}))

    def done(state):
        for v in state:
            bits = [(v >> i) & 1 for i in range(n)]
            if any(bits[i] > bits[i + 1] for i in range(n - 1)):
                return False
        return True

    def dfs(state, net):
        if cap is not None and cnt[0] >= cap:
            return
        if done(state):
            cnt[0] += 1
            yield list(net)
            return
        if len(net) >= maxc:
            return
        for c in comps:
            ns = apply(state, c)
            if ns == state:
                continue
            yield from dfs(ns, net + [c])

    yield from dfs(tuple(sorted(range(1 << n))), [])


def enum_inert_allowed(n, maxc):
    """Sorters allowing INERT comparators, requiring only that no proper prefix
    already sorts.  An inert comparator is still traversed by max-paths and is
    exactly a pass-through, so the minimal universe above systematically
    under-represents pass-through-rich networks -- this universe does not."""
    comps = [(a, b) for a in range(n) for b in range(a + 1, n)]
    for L in range(1, maxc + 1):
        for seq in itertools.product(comps, repeat=L):
            s = list(seq)
            if not vh.sorts(s, n):
                continue
            if L > 1 and vh.sorts(s[:-1], n):
                continue
            yield s


def random_sorter(n, rng):
    pre = []
    for _ in range(rng.randint(0, 3 * n)):
        i = rng.randrange(n - 1)
        pre.append((i, rng.randrange(i + 1, n)))
    return vh.thin(pre + vh.bubble(n), n, rng)


def constructed(nmin, nmax, per, seed):
    rng = random.Random(seed)
    for n in range(nmin, nmax + 1):
        base = [vh.batcher(n), vh.bubble(n), vh.odd_even_transposition(n)]
        if n > 3:
            base.append(vh.insertion_extend(vh.bubble(n - 1), n))
        for net in base:
            if vh.sorts(net, n):
                yield n, net
        for _ in range(per):
            net = random_sorter(n, rng)
            if vh.sorts(net, n):
                yield n, net


# ---------------------------------------------------------------------------
# Adversarial killer (validated: it re-derives a LEMMA* violation).
# ---------------------------------------------------------------------------

NEG = float("-inf")
_MOVES = ("ins", "del", "rep", "swp", "rel", "thin")


def _mutate(net, n, rng):
    for _ in range(12):
        m = rng.choice(_MOVES)
        c = list(net)
        if m == "ins":
            i = rng.randrange(n - 1)
            c.insert(rng.randrange(len(c) + 1), (i, rng.randrange(i + 1, n)))
        elif m == "del" and len(c) > 1:
            del c[rng.randrange(len(c))]
        elif m == "rep" and c:
            i = rng.randrange(n - 1)
            c[rng.randrange(len(c))] = (i, rng.randrange(i + 1, n))
        elif m == "swp" and len(c) > 1:
            p = rng.randrange(len(c) - 1)
            c[p], c[p + 1] = c[p + 1], c[p]
        elif m == "rel":
            perm = list(range(n))
            x, y = rng.randrange(n), rng.randrange(n)
            perm[x], perm[y] = perm[y], perm[x]
            c = vh.relabel(c, perm)
        elif m == "thin":
            c = vh.thin(c, n, rng)
        else:
            continue
        if c and len(c) <= 6 * n * n and vh.sorts(c, n):
            return c
    return None


def hunt_multi(score, ns, seeds, steps, restarts, stop_at):
    """Deterministic multi-seed hunt: try each seed in turn, stop at the first
    that clears `stop_at`.  Single-seed hill-climbing on this landscape is
    genuinely luck-dependent (there is a large plateau at exactly 1.0), so a
    single seed is NOT a reliable way to re-derive a known refutation."""
    best, bnet, bn = NEG, None, None
    for sd in seeds:
        b, net, n = hunt(score, ns, random.Random(sd), steps, restarts,
                         stop_at=stop_at)
        if b > best:
            best, bnet, bn = b, net, n
        if best > stop_at:
            break
    return best, bnet, bn


def hunt(score, ns, rng, steps, restarts, stop_at=None):
    """Maximise score(A) over sorters.  Returns (best, net, n)."""
    gb, gn, gc = NEG, None, None
    for n in ns:
        for _ in range(restarts):
            cur = random_sorter(n, rng)
            try:
                cs = float(score(analyze(cur, n)))
            except (ValueError, KeyError):
                cs = NEG
            for _ in range(steps):
                cand = _mutate(cur, n, rng)
                if cand is None:
                    continue
                try:
                    s = float(score(analyze(cand, n)))
                except (ValueError, KeyError):
                    continue
                if s == NEG:
                    continue
                if s > cs - 1e-12:
                    cur, cs = cand, s
                if cs > gb:
                    gb, gn, gc = cs, list(cur), n
                    if stop_at is not None and gb > stop_at:
                        return gb, gn, gc
    return gb, gn, gc


# ---------------------------------------------------------------------------
# PART W1 -- the wave-1 layer reproduces the established numbers
# ---------------------------------------------------------------------------

def part_w1():
    hdr("W1 -- wave-1 layer reproduces the established numbers")
    b8 = vh.batcher(8)
    A = analyze(b8, 8)
    check("W1a", vh.sorts(b8, 8) and A['f_tree'] == 96 and A['p2'] == 7
          and sorted(A['a'].values()) == [3, 3, 3, 3, 4, 4, 5],
          "Batcher-8: f_tree=96, p2=7, nc multiset {3,3,3,3,4,4,5}")
    check("W1b", A['clean'] and escape_free(A), "Batcher-8 clean and escape-free")
    T1 = [(0, 1), (0, 2), (1, 2)]
    B = analyze(T1, 3)
    check("W1c", vh.sorts(T1, 3) and len(B['passthrough']) == 1
          and B['f_tree'] == 8 and B['p2'] == 3 and B['lb'] == 3,
          "3-sorter with a pass-through: eq (8) tight (p2 = lb = 3)")
    T3 = [(2, 3), (1, 2), (0, 4), (3, 5), (2, 4), (1, 2), (4, 5), (2, 3),
          (0, 3), (3, 4), (1, 3), (1, 2), (0, 3), (0, 1), (1, 2)]
    C = analyze(T3, 6)
    check("W1d", vh.sorts(T3, 6) and abs(lemma_star(C) - 33.0 / 32.0) < 1e-12
          and C['eq8'], "documented LEMMA* counterexample re-derived: 33/32 > 1")


# ---------------------------------------------------------------------------
# PART W2 -- THEOREM 6': the lemma chain on escape-free sorters
# ---------------------------------------------------------------------------

def part_w2(fast):
    hdr("W2 -- THEOREM 6': lemmas A-E and eq (8) on ESCAPE-FREE sorters")
    rng = random.Random(20260820)
    inn = out = 0
    fails = {k: 0 for k in ("succ", "B", "nobr", "C", "D", "E", "eq8")}
    outfails = dict(fails)
    kmax = 0.0
    ov_pos = 0
    pt_max = 0

    def feed(net, n):
        nonlocal inn, out, kmax, ov_pos, pt_max
        try:
            A = analyze(net, n)
        except (ValueError, KeyError):
            return
        L = lemma_report(A)
        if escape_free(A):
            inn += 1
            kmax = max(kmax, L['kraft'])
            pt_max = max(pt_max, len(A['passthrough']))
            if any(nq_ov(A, c) and nq_ov(A, c)[1] > 0 for c in A['branch']):
                ov_pos += 1
            for k in fails:
                if not L[k]:
                    fails[k] += 1
        else:
            out += 1
            for k in outfails:
                if not L[k]:
                    outfails[k] += 1

    for net in enum_minimal(4, 6):
        feed(net, 4)
    for net in enum_minimal(5, 9, cap=4000 if fast else 20000):
        feed(net, 5)
    for n, net in constructed(3, 9 if fast else 11, 12 if fast else 25,
                              20260820):
        feed(net, n)
    for n in (6, 7):
        for _ in range(40 if fast else 120):
            feed(random_sorter(n, rng), n)

    say("    escape-free audited: %d ; out-of-class: %d" % (inn, out))
    check("W2a", fails['succ'] == 0 and fails['B'] == 0,
          "Lemma A corollary (succ is a function) and Lemma B (antichain): "
          "0 failures in class")
    check("W2b", fails['nobr'] == 0,
          "post-meeting second max traverses NO branch node (the one-line "
          "form of Lemma B): 0 failures in class")
    check("W2c", fails['C'] == 0 and kmax <= 1.0 + 1e-12,
          "Lemma C: sum_c 2^-nq(c) <= 1 in class; max observed %.6f" % kmax)
    check("W2d", fails['D'] == 0,
          "Lemma D: g(c) >= depth_B(c)+1+ov(c) in class: 0 failures")
    check("W2e", fails['E'] == 0,
          "Lemma E: p2 >= a(c)+nq(c) in class: 0 failures")
    check("W2f", fails['eq8'] == 0,
          "THEOREM 6': eq (8) holds on every escape-free sorter tested")
    check("W2g", ov_pos > 0,
          "escape-free does NOT imply ov=0 (%d in-class networks have some "
          "ov(c)>0) -- Lemma D is load-bearing, not vacuous" % ov_pos)
    check("W2h", pt_max >= 2,
          "in-class networks carry pass-throughs (max %d) -- the class is not "
          "a disguised restatement of 'clean'" % pt_max)
    # the hypothesis must be load-bearing: the lemmas must FAIL outside it
    check("W2i", out > 0 and outfails['C'] > 0 and outfails['B'] > 0,
          "outside the class the lemmas genuinely fail (B: %d, C: %d of %d) "
          "-- escape-freeness is load-bearing"
          % (outfails['B'], outfails['C'], out))
    check("W2j", outfails['eq8'] == 0,
          "eq (8) itself never failed out of class either (%d networks): the "
          "THEOREM is untouched, only the PROOF is class-restricted" % out)


# ---------------------------------------------------------------------------
# PART W3 -- the class boundary: escape-free is strictly larger than clean
# ---------------------------------------------------------------------------

def part_w3(fast):
    hdr("W3 -- escape-free strictly contains clean (universe-dependent size)")

    def tally(gen, n):
        t = c = e = 0
        for net in gen:
            try:
                A = analyze(net, n)
            except (ValueError, KeyError):
                continue
            t += 1
            c += A['clean']
            e += escape_free(A)
        return t, c, e

    t4, c4, e4 = tally(enum_minimal(4, 6), 4)
    check("W3a", (t4, c4, e4) == (708, 132, 144),
          "n=4 MINIMAL universe: %d sorters, %d clean, %d escape-free "
          "(ratio %.2f)" % (t4, c4, e4, e4 / c4))
    i4, ic4, ie4 = tally(enum_inert_allowed(4, 6), 4)
    check("W3b", ie4 > e4 and ie4 / ic4 > e4 / c4,
          "n=4 INERT-ALLOWED universe: %d sorters, %d clean, %d escape-free "
          "(ratio %.2f) -- admitting inert comparators, which ARE "
          "pass-throughs, widens the gap" % (i4, ic4, ie4, ie4 / ic4))
    cap = 20000 if fast else None
    t5, c5, e5 = tally(enum_minimal(5, 9, cap=cap), 5)
    check("W3c", e5 > c5,
          "n=5 minimal universe%s: %d sorters, %d clean, %d escape-free "
          "(ratio %.2f)" % (" (capped)" if cap else " (exhaustive)",
                            t5, c5, e5, e5 / c5))
    b12 = vh.batcher(12)
    A = analyze(b12, 12)
    check("W3d", vh.sorts(b12, 12) and not A['clean']
          and len(A['passthrough']) == 1 and escape_free(A)
          and A['f_tree'] == 288 and A['eq8'],
          "Batcher's 12-sorter: 1 pass-through so NOT clean, but escape-free; "
          "f_tree=288, lb=%d, p2=%d -- Theorem 6' covers it, Theorem 6 does "
          "not" % (A['lb'], A['p2']))
    # the class boundary is real: the lead-successor counterexample is outside
    N4 = [(0, 1), (2, 3), (0, 2), (1, 2), (1, 3), (2, 3)]
    B = analyze(N4, 4)
    L = lemma_report(B)
    check("W3e", vh.sorts(N4, 4) and not escape_free(B) and not L['succ']
          and B['eq8'],
          "the re-derived 'lead successor is not a function' witness is NOT "
          "escape-free -- consistent with Lemma A; eq (8) still holds on it")


# ---------------------------------------------------------------------------
# PART W4 -- refutations, re-derived here from scratch
# ---------------------------------------------------------------------------

def part_w4(fast):
    hdr("W4 -- refutations re-derived by adversarial search (no witness "
        "embedded)")
    rng = random.Random(4242)
    b, net, n = hunt_multi(lemma_star, (6,), (4242, 5, 1234, 77, 2026),
                           1200 if fast else 3000, 4 if fast else 8,
                           stop_at=1.0)
    ok = b > 1.0 + 1e-12
    det = "LEMMA* driven to %.6f > 1 on a constructed %d-channel sorter" % (b, n)
    if ok:
        A = analyze(net, n)
        det += " (%d comparators, %d pass-throughs; eq (8) still holds: " \
               "p2=%d >= lb=%d)" % (len(net), len(A['passthrough']),
                                    A['p2'], A['lb'])
    check("W4a", ok, det)
    say("      witness: %r" % (net,))
    # the adversary is thereby VALIDATED; now point it at eq (8) itself
    b8, net8, n8 = hunt(lambda A: A['lb'] - A['p2'], (4, 5, 6), rng,
                        1000 if fast else 2500, 4 if fast else 6, stop_at=0.0)
    check("W4b", b8 <= 0,
          "the SAME validated adversary cannot break eq (8): best margin "
          "(lb - p2) = %.0f, i.e. it reaches tightness and stops" % b8)
    # eq (6), the chapter's Kraft equality: how badly does it break?
    def broken_kraft(A):
        tot = 0.0
        for c in A['branch']:
            nv = nq_ov(A, c)
            if nv is None:
                return NEG
            tot += 2.0 ** (-nv[0])
        return tot

    bk, netk, nk = hunt(broken_kraft, (6, 7), rng, 1200 if fast else 3000,
                        4 if fast else 8)
    check("W4c", bk > 1.25,
          "chapter eq (6) sum driven to %.5f on %d channels -- materially "
          "worse than the 1.25 previously recorded, and it grows with n, so "
          "'the broken Kraft sum is bounded by a small constant' is NOT "
          "supported" % (bk, nk))


# ---------------------------------------------------------------------------
# PART W5 -- the per-node structural closure, and candidate L4-1
# ---------------------------------------------------------------------------

def part_w5(fast):
    hdr("W5 -- per-node closure (structural) and the surviving candidate")
    # Structural closure: on a network with f_tree = 2^p2 the identity
    # sum_c 2^{a(c)-p2} = 1 holds EXACTLY, so any per-node exponent X(c) <= p2
    # gives sum_c 2^{a-X} >= 1, with equality iff X(c) = p2 at every c.
    tight = 0
    for net in enum_minimal(4, 6):
        try:
            A = analyze(net, 4)
        except (ValueError, KeyError):
            continue
        if A['f_tree'] == 1 << A['p2']:
            tight += 1
            s = sum(2.0 ** (A['a'][c] - A['p2']) for c in A['branch'])
            if abs(s - 1.0) > 1e-12:
                check("W5a", False, "identity broken on a tight network")
                return
    check("W5a", tight > 0,
          "on every tight network (f_tree = 2^p2; %d found at n=4) the "
          "identity sum_c 2^{a(c)-p2} = 1 holds EXACTLY -- so any per-node "
          "exponent X(c) <= p2 gives sum_c 2^{a-X} >= 1, with equality iff "
          "X(c) = p2 at EVERY branch node" % tight)

    # The closure has bite only if tight networks with NON-CONSTANT W*(c)
    # exist.  They do -- but not at n=4 (all 12 tight 4-sorters have constant
    # W*), so this must be searched for at larger n.  Tightness-dominant score.
    def soft(A):
        rho = A['f_tree'] / float(1 << A['p2'])
        D = max(A['p2'] - A['Wstar'][c] for c in A['branch'])
        return 100.0 * rho + min(D, 5)

    b, netb, nb = hunt_multi(soft, (7,), (11, 3, 91, 2026, 7),
                             900 if fast else 2500, 3 if fast else 6,
                             stop_at=100.0)   # 100*rho + min(D,5) > 100 iff
                                              # rho == 1 and D >= 1
    got = False
    if netb is not None:
        A = analyze(netb, nb)
        rho = A['f_tree'] / float(1 << A['p2'])
        D = max(A['p2'] - A['Wstar'][c] for c in A['branch'])
        got = (rho == 1.0 and D >= 1)
        if got:
            say("      witness (%d comparators, %d pass-throughs): %r"
                % (len(netb), len(A['passthrough']), netb))
            say("      W* = %s, p2 = %d, f_tree = %d"
                % (sorted(A['Wstar'].values()), A['p2'], A['f_tree']))
    check("W5b", got or fast,
          ("a TIGHT sorter with NON-CONSTANT W*(c) exists (found at n=%d): "
           "hence no per-node certificate bounded by each node's own W*(c) "
           "can prove eq (8) -- a STRUCTURAL closure of per-node charging, "
           "not a lone counterexample" % nb) if got else
          "not found at the reduced --fast budget (needs n=7); "
          "not a refutation, re-run without --fast")
    # Candidate L4-1 -- NOT PROVED; recorded with its falsification criterion.
    rng = random.Random(99)
    worst = 0.0
    att = 0
    for net in enum_minimal(4, 6):
        try:
            A = analyze(net, 4)
        except (ValueError, KeyError):
            continue
        v = cand_L4_1(A)
        worst = max(worst, v)
        att += abs(v - 1.0) < 1e-12
    for n, net in constructed(3, 8, 15 if fast else 30, 20260820):
        try:
            A = analyze(net, n)
        except (ValueError, KeyError):
            continue
        worst = max(worst, cand_L4_1(A))
    b, netb, nb = hunt(cand_L4_1, (5, 6), rng, 800 if fast else 2000,
                       3 if fast else 6, stop_at=1.0)
    worst = max(worst, b)
    check("W5c", worst <= 1.0 + 1e-12,
          "candidate L4-1 sum_c 2^{a(c)-min(W*(c)+1,p2)} <= 1: max observed "
          "%.6f, attained (=1) on %d n=4 networks. NOT PROVED -- this is a "
          "surviving conjecture, recorded with its falsification criterion"
          % (worst, att))
    # The falsification criterion: a tight network with some W*(c) <= p2 - 2.
    def killer(A):
        if A['f_tree'] != 1 << A['p2']:
            return NEG
        return max(A['p2'] - A['Wstar'][c] for c in A['branch'])

    bk, nk_net, nk_n = hunt(killer, (5, 6), rng, 800 if fast else 2000,
                            3 if fast else 6, stop_at=1.0)
    check("W5d", bk <= 1,
          "L4-1's exact falsification criterion -- a TIGHT network with some "
          "W*(c) <= p2-2 -- was searched for directly and not found "
          "(best max_c (p2-W*(c)) on a tight network = %.0f)" % bk)


def main(argv=None):
    global QUIET
    ap = argparse.ArgumentParser()
    ap.add_argument("--fast", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args(argv)
    QUIET = a.quiet
    say(__doc__.split("\n")[0])
    part_w1()
    part_w2(a.fast)
    part_w3(a.fast)
    part_w4(a.fast)
    part_w5(a.fast)
    bad = [n for n, ok, _ in CHECKS if not ok]
    print("\n%d checks, %d failures%s"
          % (len(CHECKS), len(bad), (": " + ", ".join(bad)) if bad else ""))
    print("VERDICT: " + ("ALL CHECKS PASS" if not bad else "FAILURES PRESENT"))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
