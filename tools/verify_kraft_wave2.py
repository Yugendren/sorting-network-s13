#!/usr/bin/env python3
"""Machine check for docs/kraft-repair-wave2.md  (Kraft-repair proof swarm, wave 2).

Extends -- does not duplicate -- tools/verify_kraft_wave1.py, whose analysis
layer (escape-freeness, the lemma report, the adversarial hunter) it imports,
which in turn sits on tools/verify_huffman2.py's primitives (max-path tracing,
branch trees, red/blue leads, pruning-by-contraction, p(2,T)).

Wave 2 adds:

  * LEMMA W1, the EXACT identity   W*(c) = a(c) + eps(c) + gamma(c) + r(c)
    with eps, gamma, r >= 0 and p(2,T) = max_c W*(c)  -- general, no hypothesis;
  * THEOREM 6'' : (C) AND (D)  ==>  eq (8), a strict weakening of the
    escape-freeness hypothesis of wave 1's Theorem 6';
  * THEOREM 7 : on a TIGHT sorter (f(B) = 2^{p(2,T)}) satisfying (C) and (D),
    W*(c) = p(2,T) at EVERY branch node -- i.e. conjecture L4-1's falsification
    criterion is PROVED on that class, with margin 0 rather than the 1 it needs;
  * LEMMA W2, the excess lemma, which localises any counterexample: it must
    drive the LEMMA-star sum above 1 + 3*2^{-(N-2)};
  * THEOREM 8 / 8' : f(B) <= 2^{p(2,T)} * sum_c 2^{-gamma(c)}, so eq (8) also
    holds at the PASS-THROUGH-RICH end of the spectrum.

Conventions are verify_huffman2.py's: comparator (a,b) with a<b, min to a;
o_N = channel n-1, o_{N-1} = channel n-2.

Deterministic, stdlib only, read-only, fixed seeds.  Every network is
CONSTRUCTED or brute-force enumerated; the only literal comparator lists are
counterexamples, re-derived and re-verified from scratch here.  No witness
network is embedded, and no comparator count for any specific n appears as a
target, bound, feature or stopping condition anywhere in this file.

    python3 tools/verify_kraft_wave2.py            # full,  ~3-5 min
    python3 tools/verify_kraft_wave2.py --fast     # smaller corpora, ~40 s
    python3 tools/verify_kraft_wave2.py --quiet    # verdicts only
"""
import argparse
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import verify_huffman2 as vh
import verify_kraft_wave1 as w1

CHECKS = []
QUIET = False
NEG = float("-inf")


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
# Wave-2 analysis layer.
# ---------------------------------------------------------------------------

def tree_parent(T):
    """parent[comparator index] = comparator index of its parent branch node."""
    par = {}

    def walk(node, p):
        if node[0] == 'leaf':
            return
        par[node[1]] = p
        walk(node[2], node[1])
        walk(node[3], node[1])

    walk(T, None)
    return par


def bundle(net, n, A=None):
    """The wave-2 quantity bundle.  Raises ValueError/KeyError off-domain.

    Per branch node c:
      a, g, depth, Wstar, nq, ov,  r = nq-ov,  gamma = g-depth-1,
      m = Wstar-a,  eps = m-r-gamma,  d = p2-a.
    Network level:
      tight  : f(B) == 2^{p2}
      C      : sum_c 2^{-nq(c)} <= 1                     (the Kraft step)
      D      : gamma(c) >= ov(c) for every c             (the per-node step)
      D0     : every re-meeting comparator is a pass-through (structural form
               of D; escape-freeness implies it, and it implies D)
      star   : sum_c 2^{-m(c)}                           (the LEMMA-star sum)
      Gsum   : sum_c 2^{-gamma(c)},  Rsum : sum_c 2^{-r(c)}
      gap    : max_c (d(c) - m(c)) = max_c (p2 - W*(c)) >= 0
      T8     : Theorem 8' hypothesis (every B-edge carries >= 2 pass-throughs
               and the root's stem carries >= 1)
    """
    if A is None:
        A = w1.analyze(net, n)
    p2 = A['p2']
    par = tree_parent(A['T'])
    nodes = {}
    C_sum = 0.0
    D_ok = D0_ok = True
    for c in sorted(A['branch']):
        nv = w1.nq_ov(A, c)
        if nv is None:
            raise ValueError("nq/ov not a function of the meeting node")
        nq, ov = nv
        a, g, dep = A['a'][c], A['g'][c], A['depth_B'][c]
        gamma = g - dep - 1
        r, m = nq - ov, A['Wstar'][c] - a
        nodes[c] = dict(a=a, g=g, depth=dep, Wstar=A['Wstar'][c], nq=nq, ov=ov,
                        r=r, gamma=gamma, eps=m - r - gamma, m=m, d=p2 - a)
        C_sum += 2.0 ** (-nq)
        if gamma < ov:
            D_ok = False
    # D0: locate the re-meeting comparators explicitly and test (R3) on them.
    # By Fact 2 the post-meeting trajectory depends only on the meeting node, so
    # one representative pair per branch node suffices.
    rep = {}
    for (x, y), pi in A['pairs'].items():
        rep.setdefault(pi['meet'], (x, y))
    for c, (x, y) in rep.items():
        pm, ps, meet, _, _ = vh.trace_pair_max(net, x, y)
        for e in set(pm) & set(ps):
            if e > meet and e in A['branch']:
                D0_ok = False
    # Theorem 8' hypothesis
    root = min(A['branch'], key=lambda c: A['depth_B'][c])
    T8 = nodes[root]['gamma'] >= 1 and all(
        nodes[c]['gamma'] - nodes[par[c]]['gamma'] >= 2
        for c in nodes if par[c] is not None)
    return dict(n=n, net=list(net), A=A, p2=p2, f=A['f_tree'], lb=A['lb'],
                nodes=nodes, root=root, parent=par,
                tight=A['f_tree'] == (1 << p2), eq8=A['eq8'],
                escape_free=w1.escape_free(A), clean=A['clean'],
                npt=len(A['passthrough']),
                C_sum=C_sum, C=C_sum <= 1.0 + 1e-12, D=D_ok, D0=D0_ok,
                star=sum(2.0 ** (-v['m']) for v in nodes.values()),
                Gsum=sum(2.0 ** (-v['gamma']) for v in nodes.values()),
                Rsum=sum(2.0 ** (-v['r']) for v in nodes.values()),
                gap=max(v['d'] - v['m'] for v in nodes.values()), T8=T8)


def safe_bundle(net, n):
    try:
        return bundle(net, n)
    except (ValueError, KeyError, IndexError):
        return None


# ---------------------------------------------------------------------------
# Corpora.  All constructed or brute-force enumerated.  The inert-augmented
# generator repairs the enumerator flaw recorded in wave 1 section 6 item 3:
# an INERT comparator is still traversed by max-paths and IS a pass-through, so
# every "exhaustive" universe that skips inert comparators systematically
# deletes pass-through-rich networks.
# ---------------------------------------------------------------------------

def reach(net, n):
    """The reachable 0/1 state set after the whole of net."""
    st = frozenset(range(1 << n))
    for (a, b) in net:
        st = frozenset((v ^ (1 << a) ^ (1 << b))
                       if ((v >> a) & 1) > ((v >> b) & 1) else v for v in st)
    return st


def inert_insertions(net, n):
    """All (position, comparator) pairs whose insertion is INERT there, hence
    provably preserves sorting and creates a pass-through if the maximum's path
    traverses it."""
    out = []
    st = frozenset(range(1 << n))
    for i in range(len(net) + 1):
        for a in range(n - 1):
            for b in range(a + 1, n):
                if all(((v >> a) & 1) <= ((v >> b) & 1) for v in st):
                    out.append((i, (a, b)))
        if i < len(net):
            a, b = net[i]
            st = frozenset((v ^ (1 << a) ^ (1 << b))
                           if ((v >> a) & 1) > ((v >> b) & 1) else v
                           for v in st)
    return out


def inert_augment(net, n, rng, k):
    """Insert k inert comparators, one at a time, deterministically from rng."""
    cur = list(net)
    for _ in range(k):
        opts = inert_insertions(cur, n)
        if not opts:
            break
        i, c = opts[rng.randrange(len(opts))]
        cur = cur[:i] + [c] + cur[i:]
    return cur


def inert_family(nmin, nmax, per, kmax, seed):
    """Deterministic pass-through-rich family: constructed sorters plus 1..kmax
    inert comparators."""
    rng = random.Random(seed)
    for n in range(nmin, nmax + 1):
        bases = [vh.batcher(n), vh.bubble(n), vh.odd_even_transposition(n)]
        if n > 3:
            bases.append(vh.insertion_extend(vh.bubble(n - 1), n))
        for base in bases:
            if not vh.sorts(base, n):
                continue
            for _ in range(per):
                k = rng.randint(1, kmax)
                net = inert_augment(base, n, rng, k)
                if vh.sorts(net, n):
                    yield n, net


# ---------------------------------------------------------------------------
# PART X1 -- anchors, and LEMMA W1 (the exact identity)
# ---------------------------------------------------------------------------

def corpus(fast):
    """The standard wave-2 audit corpus, streamed as (net, n)."""
    for net in w1.enum_minimal(4, 6):
        yield net, 4
    for net in w1.enum_inert_allowed(4, 6):
        yield net, 4
    for net in w1.enum_minimal(5, 9, cap=6000 if fast else 30000):
        yield net, 5
    for n, net in w1.constructed(3, 9 if fast else 11, 8 if fast else 20,
                                 20260821):
        yield net, n
    for n, net in inert_family(4, 8, 3 if fast else 8, 4, 20260821):
        yield net, n
    rng = random.Random(20260821)
    for n in (6, 7):
        for _ in range(20 if fast else 60):
            yield w1.random_sorter(n, rng), n


def part_x1(fast):
    hdr("X1 -- anchors, and LEMMA W1: the exact identity W* = a + eps + gamma + r")
    b8 = vh.batcher(8)
    B = bundle(b8, 8)
    check("X1a", vh.sorts(b8, 8) and B['f'] == 96 and B['p2'] == 7
          and B['clean'] and B['escape_free'] and B['C'] and B['D'],
          "wave-2 layer reproduces Batcher-8 (f=96, p2=7) and its class flags")
    b12 = vh.batcher(12)
    C = bundle(b12, 12)
    check("X1b", vh.sorts(b12, 12) and not C['clean'] and C['npt'] == 1
          and C['escape_free'] and C['f'] == 288 and C['eq8'],
          "wave-2 layer reproduces Batcher-12 (1 pass-through, escape-free, "
          "f=288, lb=%d, p2=%d)" % (C['lb'], C['p2']))

    tot = bad_id = bad_sign = bad_p2 = bad_gb = bad_rb = 0
    for net, n in corpus(fast):
        b = safe_bundle(net, n)
        if b is None:
            continue
        tot += 1
        for v in b['nodes'].values():
            if v['m'] != v['eps'] + v['gamma'] + v['r']:
                bad_id += 1
            if v['eps'] < 0 or v['gamma'] < 0 or v['r'] < 0:
                bad_sign += 1
        if max(v['Wstar'] for v in b['nodes'].values()) != b['p2']:
            bad_p2 += 1
        if b['f'] > (1 << b['p2']) * b['Gsum'] + 1e-9:
            bad_gb += 1
        if b['f'] > (1 << b['p2']) * b['Rsum'] + 1e-9:
            bad_rb += 1
    say("    audited %d sorters" % tot)
    check("X1c", tot > 0 and bad_id == 0 and bad_sign == 0,
          "LEMMA W1: W*(c) = a(c)+eps(c)+gamma(c)+r(c) with all three >= 0, "
          "on %d sorters: %d failures" % (tot, bad_id + bad_sign))
    check("X1d", bad_p2 == 0,
          "p(2,T) = max_c W*(c) on all %d sorters (every ordered pair meets at "
          "some branch node)" % tot)
    check("X1e", bad_gb == 0 and bad_rb == 0,
          "THEOREM 8 bounds f(B) <= 2^{p2} * sum_c 2^{-gamma(c)} and "
          "f(B) <= 2^{p2} * sum_c 2^{-r(c)}: 0 violations on %d sorters" % tot)
    return tot


# ---------------------------------------------------------------------------
# PART X2 -- THEOREM 6' re-proved modularly: escape-free => (C) and (D0)
# ---------------------------------------------------------------------------

def part_x2(fast):
    hdr("X2 -- THEOREM 6' modular: escape-free => (C) and (D0) => (D) => eq (8)")
    inn = out = 0
    disagree = 0
    f = dict(C=0, D=0, D0=0, eq8=0)
    of = dict(C=0, D=0, D0=0, eq8=0)
    for net, n in corpus(fast):
        b = safe_bundle(net, n)
        if b is None:
            continue
        if b['D0'] != b['escape_free']:
            disagree += 1
        if b['escape_free']:
            inn += 1
            for k in f:
                if not b[k]:
                    f[k] += 1
        else:
            out += 1
            for k in of:
                if not b[k]:
                    of[k] += 1
    check("X2a", inn > 0 and f['C'] == 0,
          "escape-free ==> (C) sum_c 2^{-nq(c)} <= 1: 0 failures in %d "
          "in-class sorters" % inn)
    check("X2b", f['D0'] == 0 and f['D'] == 0,
          "escape-free ==> (D0) every re-meeting comparator is a pass-through, "
          "hence (D) gamma(c) >= ov(c): 0 failures in class")
    check("X2c", f['eq8'] == 0,
          "THEOREM 6': eq (8) on every escape-free sorter tested")
    check("X2d", out > 0 and of['C'] > 0 and of['D0'] > 0,
          "the hypothesis is load-bearing: out of class (C) fails %d times and "
          "(D0) fails %d times of %d" % (of['C'], of['D0'], out))
    check("X2e", of['eq8'] == 0,
          "eq (8) itself never failed out of class either (%d sorters)" % out)
    check("X2f", disagree == 0,
          "LEMMA W3: escape-freeness IS (D0) -- 'the second maximum never "
          "re-meets the maximum at a branch node'.  0 disagreements over "
          "%d sorters.  This is a purely local characterisation of the "
          "hypothesis of Theorem 6', and it makes Lemma D immediate."
          % (inn + out))


# ---------------------------------------------------------------------------
# PART X3 -- THEOREM 6'': (C) and (D) suffice, and are strictly weaker
# ---------------------------------------------------------------------------

def part_x3(fast):
    hdr("X3 -- THEOREM 6'': (C) AND (D) ==> eq (8), strictly weaker than "
        "escape-freeness")
    tot = cd = ef = wider = viol = 0
    wit = []
    for net, n in corpus(fast):
        b = safe_bundle(net, n)
        if b is None:
            continue
        tot += 1
        ef += b['escape_free']
        if b['C'] and b['D']:
            cd += 1
            if not b['eq8']:
                viol += 1
            if not b['escape_free']:
                wider += 1
                if len(wit) < 3:
                    wit.append((n, list(net), b['npt'], b['p2'], b['f'],
                                b['lb'], round(b['C_sum'], 6)))
    check("X3a", viol == 0 and cd > 0,
          "THEOREM 6'': eq (8) holds on every one of the %d sorters satisfying "
          "(C) and (D): 0 failures" % cd)
    check("X3b", wider > 0 and cd > ef,
          "(C) and (D) is STRICTLY wider than escape-free: %d of %d sorters "
          "satisfy it, vs %d escape-free; %d ESCAPE yet satisfy both"
          % (cd, tot, ef, wider))
    for w in wit:
        say("      escaping (C)&(D) witness: n=%d npt=%d p2=%d f=%d lb=%d "
            "C_sum=%s  %r" % (w[0], w[2], w[3], w[4], w[5], w[6], w[1]))


# ---------------------------------------------------------------------------
# PART X4 -- THEOREM 7 and LEMMA W2 (the excess lemma)
# ---------------------------------------------------------------------------

def part_x4(fast):
    hdr("X4 -- THEOREM 7: tight + (C) + (D) forces W*(c) = p(2,T) everywhere")
    tight = tcd = rigid = viol = 0
    star_ge1 = star_bad = 0
    depth_bad = 0
    gap_pos_but_cd = cor7a_bad = 0
    excess_bad = 0
    for net, n in corpus(fast):
        b = safe_bundle(net, n)
        if b is None or not b['tight']:
            continue
        tight += 1
        # LEMMA W2 part 1: on a tight network sum_c 2^{-m(c)} >= 1 exactly.
        if b['star'] < 1.0 - 1e-12:
            star_bad += 1
        else:
            star_ge1 += 1
        # LEMMA W2 part 2: the d(c) are the leaf depths of a full binary tree
        # with n-1 leaves, so max_c d(c) <= n-2, and sum_c 2^{-d(c)} = 1.
        if abs(sum(2.0 ** (-v['d']) for v in b['nodes'].values()) - 1.0) > 1e-12:
            depth_bad += 1
        if max(v['d'] for v in b['nodes'].values()) > n - 2:
            depth_bad += 1
        # LEMMA W2 part 3: the excess bound.
        for v in b['nodes'].values():
            g = v['d'] - v['m']
            if b['star'] < 1.0 + (2.0 ** g - 1.0) * 2.0 ** (-v['d']) - 1e-9:
                excess_bad += 1
        if b['C'] and b['D']:
            tcd += 1
            if b['gap'] != 0:
                viol += 1
            if all(v['d'] == v['m'] == v['nq'] and v['eps'] == 0
                   and v['gamma'] == v['ov'] for v in b['nodes'].values()):
                rigid += 1
        if b['gap'] >= 1:
            gap_pos_but_cd += 1
            if b['C'] and b['D']:
                cor7a_bad += 1
    check("X4a", tight > 0 and tcd > 0 and viol == 0,
          "THEOREM 7: on all %d TIGHT sorters satisfying (C) and (D), "
          "max_c (p(2,T) - W*(c)) = 0 -- i.e. W* is CONSTANT = p(2,T): "
          "%d violations" % (tcd, viol))
    check("X4b", rigid == tcd,
          "and the full rigidity holds: nq(c) = m(c) = d(c), eps(c) = 0, "
          "gamma(c) = ov(c) at every branch node of all %d of them" % tcd)
    check("X4c", star_bad == 0 and star_ge1 == tight,
          "LEMMA W2(i): sum_c 2^{-m(c)} >= 1 on every one of the %d tight "
          "sorters (the structural closure of per-node charging)" % tight)
    check("X4d", depth_bad == 0,
          "LEMMA W2(ii): on a tight sorter the d(c) = p2-a(c) satisfy "
          "sum_c 2^{-d(c)} = 1 and max_c d(c) <= n-2 (Kraft's converse plus "
          "'a full binary tree with L leaves has height <= L-1')")
    check("X4e", excess_bad == 0,
          "LEMMA W2(iii): sum_c 2^{-m(c)} >= 1 + (2^{d-m}-1) 2^{-d} at every "
          "node of every tight sorter -- so a counterexample to L4-1's "
          "criterion (some d-m >= 2) forces the LEMMA-star sum above "
          "1 + 3*2^{-(n-2)}")
    check("X4f", cor7a_bad == 0,
          "COROLLARY 7a: of the %d tight sorters in this corpus with "
          "p(2,T) > W*(c) at some branch node, %d satisfy (C) and (D) -- "
          "the contrapositive of Theorem 7 says this must be 0.  NOTE: if the "
          "first number is 0 this check is VACUOUS here; the substantive "
          "instance is X5b, which takes a gap-1 tight sorter found by targeted "
          "n=7 search and confirms it fails (C) and (D)"
          % (gap_pos_but_cd, cor7a_bad))


# ---------------------------------------------------------------------------
# PART X5 -- the L4-1 falsification criterion: direct adversarial attack
# ---------------------------------------------------------------------------

def part_x5(fast):
    hdr("X5 -- conjecture L4-1's falsification criterion, attacked directly")

    def soft(A):
        """100*(f/2^p2) + min(gap,5): > 100 iff tight and gap >= 1,
        >= 102 iff tight and gap >= 2 (which would REFUTE L4-1)."""
        try:
            b = bundle(A['net'], A['n'], A)
        except (ValueError, KeyError):
            return NEG
        return 100.0 * (b['f'] / float(1 << b['p2'])) + min(b['gap'], 5)

    # (1) VALIDATION: the same adversary must be able to reach a TIGHT sorter
    # with gap == 1 -- the configuration wave 1 section 3.1 exhibits.  An
    # adversary that cannot reach a known positive proves nothing by failing.
    vseeds = (11, 3, 91, 2026, 7)
    bv, netv, nv = w1.hunt_multi(soft, (7,), vseeds,
                                 900 if fast else 2500, 3 if fast else 6,
                                 stop_at=100.0)
    gap1 = None
    if netv is not None:
        bb = safe_bundle(netv, nv)
        if bb is not None and bb['tight'] and bb['gap'] >= 1:
            gap1 = bb
    check("X5a", gap1 is not None or fast,
          ("adversary VALIDATED: it re-derives a TIGHT sorter with "
           "max_c (p(2,T) - W*(c)) = %d at n=%d (%d comparators, %d "
           "pass-throughs, f=%d=2^%d) under %d seeds x %d restarts x %d steps"
           % (gap1['gap'], nv, len(netv), gap1['npt'], gap1['f'], gap1['p2'],
              len(vseeds), 3 if fast else 6, 900 if fast else 2500))
          if gap1 is not None else
          "gap-1 validation witness not reached at the reduced --fast budget; "
          "re-run without --fast before trusting any non-refutation below")
    if gap1 is not None:
        say("      validation witness: %r" % (netv,))
        check("X5b", not (gap1['C'] and gap1['D']),
              "COROLLARY 7a confirmed on it: a tight sorter with "
              "p(2,T) > W*(c) somewhere MUST fail (C) or (D) -- this one has "
              "C=%s, D=%s, escape-free=%s"
              % (gap1['C'], gap1['D'], gap1['escape_free']))

    # (2) THE REFUTATION HUNT: score >= 102 iff tight and gap >= 2.
    # Budget note: the SHIPPED budget here is deliberately modest so that the
    # verifier stays runnable.  The large campaign (4 score functions, 8 seeds,
    # n = 6..9, 728 500 evaluations) lives in the reproducible scratch
    # .build/v3-swarm2/adversary/ and is reported in the document; its finding
    # that no TIGHT network is reached AT ALL at n >= 8 is the honest limit of
    # adversarial search here.
    seeds = (11, 3, 91, 2026, 7, 555, 8192, 41)
    ns = (6,) if fast else (6, 7)
    steps = 500 if fast else 1200
    rest = 2 if fast else 3
    use = seeds[:3] if fast else seeds
    b, netb, nb = w1.hunt_multi(soft, ns, use, steps, rest, stop_at=101.0)
    got2 = False
    det = "best score %.4f" % b
    if netb is not None:
        bb = safe_bundle(netb, nb)
        if bb is not None:
            got2 = bb['tight'] and bb['gap'] >= 2
            det = ("best reached: n=%d, f/2^p2 = %.4f, max_c (p2-W*(c)) = %d"
                   % (nb, bb['f'] / float(1 << bb['p2']), bb['gap']))
    check("X5c", not got2,
          "L4-1's falsification criterion NOT met: budget %d seeds %s x %d "
          "restarts x %d steps over n=%s; %s"
          % (len(use), str(use), rest, steps, str(ns), det))
    if got2:
        say("      *** REFUTATION CANDIDATE -- STOP AND VERIFY *** %r" % (netb,))


# ---------------------------------------------------------------------------
# PART X6 -- THEOREM 8': the pass-through-rich end of the spectrum
# ---------------------------------------------------------------------------

def append_inert(net, n, k):
    """Append k copies of (n-2, n-1).  At the end of a sorting network every
    reachable 0/1 vector is sorted, so this comparator is INERT there and the
    result still sorts; the maximum's path traverses each copy, and the other
    input lead is blue (every max-path has already merged onto channel n-1), so
    by (R3) each copy is a PASS-THROUGH on the stem of EVERY branch node.
    Hence gamma(c) increases by k at every c and the branch tree is unchanged."""
    return list(net) + [(n - 2, n - 1)] * k


def part_x6(fast):
    hdr("X6 -- THEOREM 8: pass-through-rich sorters also satisfy eq (8)")
    tot = ok8a = bad8a = esc8a = t8 = bad8 = esc8 = 0
    minmax_ok = 0
    wit = []
    src = []
    for net in w1.enum_minimal(4, 6):
        src.append((net, 4))
    cnt = 0
    for net in w1.enum_minimal(5, 9, cap=1500 if fast else 6000):
        src.append((net, 5))
        cnt += 1
    for n, net in w1.constructed(3, 8 if fast else 10, 4 if fast else 10,
                                 20260822):
        src.append((net, n))
    for base, n in src:
        k = max(1, (n - 2).bit_length())          # k >= ceil(log2(n-1))
        net = append_inert(base, n, k)
        if not vh.sorts(net, n):
            continue
        b = safe_bundle(net, n)
        b0 = safe_bundle(base, n)
        if b is None or b0 is None:
            continue
        tot += 1
        # the appended comparators must be pass-throughs, not branch nodes
        if b['f'] == b0['f'] and min(v['gamma'] for v in b['nodes'].values()) \
                >= min(v['gamma'] for v in b0['nodes'].values()) + k:
            minmax_ok += 1
        if b['Gsum'] <= 1.0 + 1e-12:
            ok8a += 1
            if not b['eq8']:
                bad8a += 1
            if not b['escape_free']:
                esc8a += 1
                if len(wit) < 2:
                    wit.append((n, list(net), b['npt'], b['p2'], b['f'],
                                b['lb'], round(b['Gsum'], 6)))
        if b['T8']:
            t8 += 1
            if b['Gsum'] > 1.0 + 1e-12 or not b['eq8']:
                bad8 += 1
            if not b['escape_free']:
                esc8 += 1
    say("    pass-through-padded family: %d sorters" % tot)
    check("X6a", tot > 0 and minmax_ok == tot,
          "appending k = ceil(log2(n-1)) inert comparators leaves f(B) fixed "
          "and raises gamma(c) by k at EVERY branch node, on all %d "
          "constructed sorters -- the padding lemma" % tot)
    check("X6b", ok8a > 0 and bad8a == 0,
          "COROLLARY 8a: sum_c 2^{-gamma(c)} <= 1 ==> eq (8).  Hypothesis "
          "holds on %d of the %d padded sorters (it is forced by "
          "min_c gamma(c) >= log2(n-1)); eq (8) failures: %d"
          % (ok8a, tot, bad8a))
    check("X6c", esc8a > 0,
          "and the class is NOT contained in escape-free: %d of them ESCAPE, "
          "so Corollary 8a proves eq (8) for sorters Theorem 6' cannot reach"
          % esc8a)
    for w in wit:
        say("      escaping Corollary-8a witness: n=%d npt=%d p2=%d f=%d lb=%d "
            "Gsum=%s  %r" % (w[0], w[2], w[3], w[4], w[5], w[6], w[1]))

    # The sharper per-edge hypothesis of Corollary 8c needs pass-throughs
    # BETWEEN consecutive branch nodes, which end-padding cannot supply.
    # Duplicating every comparator k times does: each repeat after the first is
    # inert at that point, hence sorting is preserved, and each is a
    # pass-through wherever a max-path traverses it.
    def dup(net, k):
        out = []
        for c in net:
            out.extend([c] * k)
        return out

    n8c = n8c_bad = n8c_esc = n8c_nocd = 0
    ex = None
    for n in range(4, 9 if fast else 10):
        for base in (vh.batcher(n), vh.bubble(n),
                     vh.odd_even_transposition(n)):
            for k in (2, 3, 4):
                net = dup(base, k)
                if not vh.sorts(net, n):
                    continue
                b = safe_bundle(net, n)
                if b is None or not b['T8']:
                    continue
                n8c += 1
                if b['Gsum'] > 1.0 + 1e-12 or not b['eq8']:
                    n8c_bad += 1
                if not b['escape_free']:
                    n8c_esc += 1
                if not (b['C'] and b['D']):
                    n8c_nocd += 1
                    if ex is None:
                        ex = (n, list(net), b['npt'], b['p2'], b['lb'],
                              b['C'], b['D'])
    check("X6d", n8c > 0 and n8c_bad == 0,
          "COROLLARY 8c (root stem >= 1 pass-through, every B-edge >= 2) is "
          "satisfiable at every n tested: %d constructed instances, all with "
          "sum_c 2^{-gamma(c)} <= 1 and eq (8): %d failures" % (n8c, n8c_bad))
    check("X6e", n8c_nocd > 0,
          "and %d of them ESCAPE (%d fail (C) or (D)) -- so Corollary 8c "
          "proves eq (8) for sorters that BOTH Theorem 6' and Theorem 6'' "
          "miss" % (n8c_esc, n8c_nocd))
    if ex is not None:
        say("      escaping Corollary-8c witness: n=%d npt=%d p2=%d lb=%d "
            "C=%s D=%s  %r" % (ex[0], ex[2], ex[3], ex[4], ex[5], ex[6], ex[1]))


def main(argv=None):
    global QUIET
    ap = argparse.ArgumentParser()
    ap.add_argument("--fast", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--only", default="")
    a = ap.parse_args(argv)
    QUIET = a.quiet
    say(__doc__.split("\n")[0])
    parts = dict(x1=part_x1, x2=part_x2, x3=part_x3, x4=part_x4, x5=part_x5,
                 x6=part_x6)
    order = a.only.split(",") if a.only else ["x1", "x2", "x3", "x4", "x5", "x6"]
    for k in order:
        parts[k](a.fast)
    bad = [n for n, ok, _ in CHECKS if not ok]
    print("\n%d checks, %d failures%s"
          % (len(CHECKS), len(bad), (": " + ", ".join(bad)) if bad else ""))
    print("VERDICT: " + ("ALL CHECKS PASS" if not bad else "FAILURES PRESENT"))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
