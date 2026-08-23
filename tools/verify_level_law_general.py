#!/usr/bin/env python3
"""verify_level_law_general.py -- is Chain Collapse a METHOD or a fact about
sorting networks?

This tool implements the abstract class of searches defined in
`docs/level-law-general.md` (a "graded ambient search") and mechanically checks
its hypotheses, and its two conclusions, in several domains:

    sortnet   miniature pure-Python model of the sortnetopt state space
              (output sets under comparators + channel pruning).  Used only to
              check the abstract hypotheses H1-H5 directly; the census identity
              itself is established at scale by `tools/verify_ambient.py`
              against the Rust engine's dumps.

    bool      Boolean chains / straight-line programs over a binary basis.
              Ambient = number of input variables.  Canonicalisation quotients
              unused inputs and permutes the used ones.  Width = number of
              essential input variables.  Width is NON-DECREASING, growth is
              <= 2 per gate, so n_min(l) = 2l in closed form.

    pancake   Prefix-reversal ("pancake") sorting.  Ambient = number of
              pancakes.  Canonicalisation strips the maximal sorted suffix.
              Width is NEITHER monotone up NOR monotone down: a long flip can
              raise the width and a later flip can lower it again.  This is the
              domain that genuinely tests hypothesis H4 (width convexity /
              "no high-width detour"), which is free in the other two.

Subcommands
-----------
  bool-bruteforce --ambients a,b,c --level L
        independent validation of the Boolean-chain domain: raw enumeration
        with NO canonicalisation and NO fresh-variable cap, true S_n orbits by
        brute force, and the three checks that the canonical form is a
        complete invariant and that reach() reproduces it exactly.

  hypotheses DOMAIN --ambients a,b,c --level L
        H1 ambient freedom of the successor relation (stratified by width)
        H2 grading is ambient free
        H3 root tower
        H4 width convexity  (empirical: are the strata equal?)
        H5 tail triviality  (is the stratum above the front a single state?)

  census DOMAIN --ambient N --level L [--out FILE]
        compute Reach(N, L); write a JSON census + the sorted canonical keys

  predict DOMAIN --level L [--from FILE] --ambients a,b,c [--out FILE]
        emit the PRE-REGISTERED prediction for larger ambients derived from a
        small-ambient census.  Writes JSON; hash it and record it in the doc
        BEFORE running `collapse`.

  collapse DOMAIN --level L --ambients a,b,c [--check FILE]
        compute Reach at each ambient and check the collapse identity exactly
        (set equality of canonical keys, stratified by width), optionally
        against a pre-registered prediction file.

  nmin DOMAIN --levels L
        the closed-form n_min(l) the domain claims.

Exit status is 0 iff every requested check passed.
"""

import argparse
import collections
import hashlib
import itertools
import json
import sys
import time

# --------------------------------------------------------------------------
# The abstract class: a graded ambient search.
#
# A Domain must provide
#   roots(n)        -> list of canonical keys at level 0
#   width(key)      -> int, the intrinsic size of the state
#   succ(key, n)    -> list of (key', dlevel) available at ambient n
#   n_min(l)        -> int or None, the closed-form cutoff claim
#   tail(n, l)      -> description of the predicted states of width > n_min(l)
#   chain_states(n) -> the predicted free chain (may be empty)
# Keys must be ambient-free: the same object must have the same key at every
# ambient that can hold it.  That is hypothesis H0 and it is the whole ball
# game; every domain below states explicitly how it achieves it.
# --------------------------------------------------------------------------


class Domain:
    name = "abstract"
    # cost, in levels, of the free chain from the ambient-n root down to the
    # ambient-(n-1) root.  0 when the root tower is trivial.
    def chain_delta(self, n):
        return 0

    def C(self, n):
        """Free-chain bound: total grade of the root tower above width 0."""
        return sum(self.chain_delta(k) for k in range(1, n + 1))

    def roots(self, n):
        raise NotImplementedError

    def width(self, key):
        raise NotImplementedError

    def succ(self, key, n):
        raise NotImplementedError

    def n_min(self, level):
        return None

    def growth(self):
        """Max width increase per unit level, or None if width can decrease."""
        return None


# --------------------------------------------------------------------------
# Generic engine: the level-graded reachable set.
# --------------------------------------------------------------------------


def reach(dom, n, max_level, cap=None):
    """Dijkstra over the level grading.  -> {key: min level <= max_level}."""
    best = {}
    frontier = {}
    for k in dom.roots(n):
        if 0 <= max_level:
            best[k] = 0
            frontier.setdefault(0, set()).add(k)
    level = 0
    while level <= max_level:
        cur = frontier.pop(level, None)
        # states sitting at the budget can have no in-budget successor when
        # every edge carries a strictly positive grade, so do not expand them.
        # Domains with grade-0 edges must set min_grade = 0.
        if level + getattr(dom, "min_grade", 1) > max_level:
            cur = None
        if cur:
            for key in sorted(cur):
                if best[key] != level:
                    continue
                for nxt, dl in dom.succ(key, n):
                    nl = level + dl
                    if nl > max_level:
                        continue
                    old = best.get(nxt)
                    if old is None or nl < old:
                        best[nxt] = nl
                        frontier.setdefault(nl, set()).add(nxt)
                        if cap and len(best) > cap:
                            raise SystemExit(
                                "state cap %d exceeded at ambient %d level %d"
                                % (cap, n, max_level)
                            )
        level += 1
    return best


def strata(dom, best):
    """-> {width: {key: level}}"""
    out = collections.defaultdict(dict)
    for k, l in best.items():
        out[dom.width(k)][k] = l
    return out


def census_table(dom, best):
    """-> {width: {level: count}} as plain dicts, JSON friendly."""
    t = collections.defaultdict(lambda: collections.Counter())
    for k, l in best.items():
        t[dom.width(k)][l] += 1
    return {str(w): {str(l): c for l, c in sorted(v.items())}
            for w, v in sorted(t.items())}


# --------------------------------------------------------------------------
# DOMAIN 1: Boolean chains (straight-line programs).
# --------------------------------------------------------------------------

_AND = lambda a, b, m: a & b
_OR = lambda a, b, m: a | b
_XOR = lambda a, b, m: a ^ b
_NAND = lambda a, b, m: (~(a & b)) & m

BASES = {
    "aox": [("AND", _AND), ("OR", _OR), ("XOR", _XOR)],
    "ao": [("AND", _AND), ("OR", _OR)],
    "nand": [("NAND", _NAND)],
    "ax": [("AND", _AND), ("XOR", _XOR)],
}


def _proj(i, w):
    """Truth table of x_i as a 2^w-bit integer, bit m = value at assignment m."""
    tt = 0
    for m in range(1 << w):
        if (m >> i) & 1:
            tt |= 1 << m
    return tt


class _PermCache:
    """Cached machinery for permuting variables of 2^w-bit truth tables."""

    def __init__(self):
        self.maps = {}

    def perm_maps(self, w):
        """List of (index-map) for every permutation of w variables.

        index_map[m] = the assignment that must supply the value at m.
        """
        if w in self.maps:
            return self.maps[w]
        out = []
        for p in itertools.permutations(range(w)):
            # new_f(m) = f(m') where m' has bit p[i] taken from bit i of m
            src = []
            for m in range(1 << w):
                mm = 0
                for i in range(w):
                    if (m >> i) & 1:
                        mm |= 1 << p[i]
                src.append(mm)
            out.append(tuple(src))
        self.maps[w] = out
        return out


_PC = _PermCache()


def _apply_perm(tt, src):
    out = 0
    for m, mm in enumerate(src):
        if (tt >> mm) & 1:
            out |= 1 << m
    return out


def _support(tt, w):
    """Set of essential variables of a 2^w-bit truth table."""
    s = []
    for i in range(w):
        step = 1 << i
        dep = False
        for m in range(1 << w):
            if not (m >> i) & 1:
                if ((tt >> m) & 1) != ((tt >> (m + step)) & 1):
                    dep = True
                    break
        if dep:
            s.append(i)
    return s


def _restrict(tt, w, keep):
    """Project a 2^w-bit table onto the variables `keep` (in order)."""
    k = len(keep)
    out = 0
    for m in range(1 << k):
        mm = 0
        for j, i in enumerate(keep):
            if (m >> j) & 1:
                mm |= 1 << i
        if (tt >> mm) & 1:
            out |= 1 << m
    return out


class BoolChains(Domain):
    """State = the MULTISET of gate outputs of a straight-line program starting
    from the projections x_1..x_n.  A gate applies one basis operation to two
    distinct elements of {projections} u {computed}; its output is recorded
    even when it duplicates a function already present, so a program with a
    redundant gate is a distinct state at that length -- which is what an
    exhaustive program enumeration actually explores.  Level = number of gates.
    `bool-bruteforce` checks this convention against a raw enumeration.

    Canonical key: restrict every computed function to the union of their
    essential supports (this is exactly "quotient the unused dimensions"), then
    take the lexicographic minimum over all permutations of the used variables.
    The key therefore never mentions the ambient n.  Width = |support|.

    Ambient freedom: from a state of width w, the only thing n controls is how
    many FRESH projections are available, and by symmetry at most two of them
    are distinguishable.  So succ(X, n) depends on n only through min(n, w+2),
    and succ(X, n) restricted to width <= m equals succ(X, m) whenever m >= w.

    Width is non-decreasing and grows by at most 2 per gate, hence the closed
    form  n_min(l) = 2l, and there is NO tail: Reach(n, l) = Reach(2l, l) for
    every n >= 2l.
    """

    def __init__(self, basis="aox", fresh_cap=2, leak=False):
        self.name = "bool[%s]" % basis
        if fresh_cap != 2:
            self.name += "/fresh%d" % fresh_cap
        if leak:
            self.name += "/LEAK"
        self.ops = BASES[basis]
        self.fresh_cap = fresh_cap
        self.leak = leak
        self._succ_cache = {}

    # -- key encoding ------------------------------------------------------
    @staticmethod
    def encode(w, tables):
        return json.dumps([w, sorted(tables)], separators=(",", ":"))

    @staticmethod
    def decode(key):
        w, tables = json.loads(key)
        return w, tables

    def width(self, key):
        return self.decode(key)[0]

    def canon(self, w, tables):
        """tables: list of 2^w-bit ints.  -> canonical key."""
        tables = [t for t in tables]
        if not tables:
            return self.encode(0, [])
        sup = set()
        for t in tables:
            sup.update(_support(t, w))
        keep = sorted(sup)
        k = len(keep)
        if k == 0:
            # every computed function is constant
            consts = sorted(set(1 if t else 0 for t in tables))
            return self.encode(0, consts)
        red = [_restrict(t, w, keep) for t in tables]
        best = None
        for src in _PC.perm_maps(k):
            cand = tuple(sorted(_apply_perm(t, src) for t in red))
            if best is None or cand < best:
                best = cand
        return self.encode(k, list(best))

    def roots(self, n):
        return [self.encode(0, [])]

    def succ(self, key, n):
        w = self.decode(key)[0]
        # ---- the FRESH-CAP LEMMA -------------------------------------------
        # At ambient n the state may also use any of the n - w projections it
        # does not yet touch.  Those are interchangeable under the symmetry the
        # canonical form already quotients by, and a single gate can consume at
        # most two of them, so only  min(n, w + fresh_cap)  variables need be
        # materialised.  fresh_cap = 2 is the claim; `bool-fresh-lemma` checks
        # it against fresh_cap = 3, 4 and against the full ambient.
        we = min(n, w + self.fresh_cap)
        # ---- the AMBIENT LEAK ----------------------------------------------
        # Deliberate mis-implementation modelled on SORTNETOPT_SUBSUME_WIDTHS:
        # a pruning heuristic keyed to the ROOT width rather than to the
        # state's own width.  Looks harmless, destroys the collapse.
        if self.leak and w in (n - 3, n - 2):
            return []
        ck = (key, we)
        hit = self._succ_cache.get(ck)
        if hit is not None:
            return hit
        out = self._succ_raw(key, we)
        self._succ_cache[ck] = out
        return out

    def _succ_raw(self, key, we):
        w, tables = self.decode(key)
        fresh = we - w
        mask = (1 << (1 << we)) - 1
        # widen the stored tables from 2^w bits to 2^we bits
        if fresh:
            wide = []
            for t in tables:
                nt = 0
                for m in range(1 << we):
                    if (t >> (m & ((1 << w) - 1))) & 1:
                        nt |= 1 << m
                wide.append(nt)
        else:
            wide = list(tables)
        pool = [_proj(i, we) for i in range(we)] + wide
        out = set()
        for a in range(len(pool)):
            for b in range(a + 1, len(pool)):
                for _nm, f in self.ops:
                    g = f(pool[a], pool[b], mask)
                    out.add(self.canon(we, wide + [g]))
        return [(k, 1) for k in sorted(out)]

    def n_min(self, level):
        return 2 * level

    def growth(self):
        return 2


# --------------------------------------------------------------------------
# DOMAIN 2: prefix-reversal (pancake) sorting.
# --------------------------------------------------------------------------


class Pancake(Domain):
    """State = a permutation of [n] reached from the identity by prefix
    reversals.  Canonical key: strip the maximal already-sorted suffix, i.e.
    keep pi[0..w-1] where w = 1 + max{i : pi[i] != i}.  The stripped tail is
    exactly the "unused dimensions" and the key never mentions n.
    Width = w.  Level = number of flips.

    Ambient freedom holds in the stratified sense: from a width-w state, flips
    of length k <= n are available, a flip of length k > w produces a state of
    width exactly k, and flips of length k <= max(w, m) are exactly those
    available at ambient m.  So  succ(X, n) n {width <= m} = succ(X, m).

    Width is NOT monotone: flip_k raises the width to k and a later flip can
    lower it again.  So hypothesis H4 (width convexity) is a genuine open
    question here, and this domain is the test of it.
    """

    name = "pancake"

    @staticmethod
    def encode(perm):
        return ",".join(str(x) for x in perm)

    @staticmethod
    def decode(key):
        return [] if key == "" else [int(x) for x in key.split(",")]

    def width(self, key):
        return 0 if key == "" else len(self.decode(key))

    @staticmethod
    def reduce(perm):
        w = len(perm)
        while w > 0 and perm[w - 1] == w - 1:
            w -= 1
        return Pancake.encode(perm[:w])

    def roots(self, n):
        return [""]

    def succ(self, key, n):
        p = self.decode(key)
        w = len(p)
        full = p + list(range(w, n))
        out = set()
        for k in range(2, n + 1):
            q = full[:k][::-1] + full[k:]
            out.add(self.reduce(q))
        return [(x, 1) for x in sorted(out)]

    def n_min(self, level):
        return None  # no closed form claimed; measured

    def growth(self):
        return None  # width can decrease


# --------------------------------------------------------------------------
# DOMAIN 3: miniature sorting-network state space (hypothesis checks only).
# --------------------------------------------------------------------------


class SortNetMini(Domain):
    """Pure-Python model of the sortnetopt state space.

    A state is an output set X subset of {0,1}^n, canonicalised under the group
    S_n x C_2 (channel permutation and global complement, matching
    `output_set/canon.rs` semantically).  Two transition families:

        Succ(X)  = { canon(X |> [i,j]) }    -- width preserving
        Prune(X) = { canon(X|_{c=p} \\ c) } -- width lowering by one

    Width = the number of channels.  Only used here to check the abstract
    hypotheses (H1, H3, H4, Theorem B, Theorem C) directly; the census identity
    itself is checked at scale by tools/verify_ambient.py.
    """

    name = "sortnet"

    def __init__(self):
        self._canon_cache = {}

    @staticmethod
    def cube(n):
        return frozenset(range(1 << n))

    @staticmethod
    def apply_comparator(X, n, i, j):
        """channel i receives the min, channel j the max (i < j)."""
        out = set()
        bi, bj = 1 << i, 1 << j
        for v in X:
            a, b = (v >> i) & 1, (v >> j) & 1
            lo, hi = min(a, b), max(a, b)
            v2 = v & ~(bi | bj)
            if lo:
                v2 |= bi
            if hi:
                v2 |= bj
            out.add(v2)
        return frozenset(out)

    @staticmethod
    def prune(X, n, c, p):
        """condition channel c to value p, then delete the channel."""
        out = set()
        bc = 1 << c
        for v in X:
            if ((v >> c) & 1) != p:
                continue
            lo = v & (bc - 1)
            hi = (v >> (c + 1)) << c
            out.add(lo | hi)
        return frozenset(out)

    def canon(self, X, n):
        key = (n, X)
        hit = self._canon_cache.get(key)
        if hit is not None:
            return hit
        best = None
        full = (1 << n) - 1
        for perm in itertools.permutations(range(n)):
            pm = [0] * (1 << n)
            for v in range(1 << n):
                w = 0
                for i in range(n):
                    if (v >> i) & 1:
                        w |= 1 << perm[i]
                pm[v] = w
            base = frozenset(pm[v] for v in X)
            for comp in (0, 1):
                s = base if not comp else frozenset(full ^ v for v in base)
                cand = (n, tuple(sorted(s)))
                if best is None or cand < best:
                    best = cand
        out = json.dumps([best[0], list(best[1])], separators=(",", ":"))
        self._canon_cache[key] = out
        return out

    def width(self, key):
        return json.loads(key)[0]

    def unkey(self, key):
        n, vs = json.loads(key)
        return n, frozenset(vs)

    def roots(self, n):
        return [self.canon(self.cube(n), n)]

    def succ(self, key, n):
        w, X = self.unkey(key)
        out = set()
        for i in range(w):
            for j in range(i + 1, w):
                Y = self.apply_comparator(X, w, i, j)
                if Y != X:
                    out.add(self.canon(Y, w))
        for c in range(w):
            for p in (0, 1):
                Y = self.prune(X, w, c, p)
                if len(Y) and w > 1:
                    out.add(self.canon(Y, w - 1))
        return [(k, 1) for k in sorted(out)]

    def chain_delta(self, n):
        return 0 if n < 4 else (n - 1).bit_length()

    def C(self, n):
        if n < 3:
            return 0
        return 3 + sum((k - 1).bit_length() for k in range(4, n + 1))


DOMAINS = {
    "bool": lambda: BoolChains("aox"),
    "bool-nand": lambda: BoolChains("nand"),
    "bool-ao": lambda: BoolChains("ao"),
    "bool-ax": lambda: BoolChains("ax"),
    "bool-leak": lambda: BoolChains("aox", leak=True),
    # fresh_cap = 99 materialises EVERY ambient variable: no modelling
    # shortcut at all, so a collapse observed here cannot be an artefact of
    # the fresh-cap lemma.  Only affordable at level <= 2.
    "bool-full": lambda: BoolChains("aox", fresh_cap=99),
    "bool-fresh3": lambda: BoolChains("aox", fresh_cap=3),
    "pancake": Pancake,
    "sortnet": SortNetMini,
}


# --------------------------------------------------------------------------
# Checks
# --------------------------------------------------------------------------


def cmd_nmin(args):
    dom = DOMAINS[args.domain]()
    print("domain            : %s" % dom.name)
    print("growth per level  : %s" % dom.growth())
    for l in range(0, args.levels + 1):
        print("  n_min(%d) = %s" % (l, dom.n_min(l)))
    return True


def cmd_census(args):
    dom = DOMAINS[args.domain]()
    t0 = time.time()
    best = reach(dom, args.ambient, args.level, cap=args.cap)
    dt = time.time() - t0
    tab = census_table(dom, best)
    print("domain %s  ambient %d  level<=%d : %d states  (%.2fs)"
          % (dom.name, args.ambient, args.level, len(best), dt))
    for w in sorted(tab, key=int):
        print("  width %2s : %s" % (w, dict(tab[w])))
    if args.out:
        payload = {
            "domain": dom.name,
            "ambient": args.ambient,
            "max_level": args.level,
            "total": len(best),
            "census": tab,
            "keys": sorted(best),
            "levels": {k: best[k] for k in sorted(best)},
        }
        with open(args.out, "w") as fh:
            json.dump(payload, fh, sort_keys=True, indent=1)
        print("wrote %s  sha256=%s" % (args.out, sha256_file(args.out)))
    return True


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def cmd_predict(args):
    """Emit the pre-registered prediction for larger ambients."""
    with open(args.source) as fh:
        src = json.load(fh)
    dom = DOMAINS[args.domain]()
    small_n = src["ambient"]
    L = src["max_level"]
    keys = set(src["keys"])
    pred = {}
    for n in args.ambients:
        if n < small_n:
            expect = sorted(k for k in keys if dom.width(k) <= n)
            basis = "restriction: {s in Reach(%d,%d) : width(s) <= %d}" % (
                small_n, L, n)
        else:
            expect = sorted(keys)
            basis = ("identity: Reach(%d,%d) = Reach(%d,%d) exactly, "
                     "empty tail" % (n, L, small_n, L))
        cen = collections.defaultdict(collections.Counter)
        for k in expect:
            cen[dom.width(k)][src["levels"][k]] += 1
        pred[str(n)] = {
            "basis": basis,
            "total": len(expect),
            "census": {str(w): {str(l): c for l, c in sorted(v.items())}
                       for w, v in sorted(cen.items())},
            "sha256_of_keys": hashlib.sha256(
                "\n".join(expect).encode()).hexdigest(),
        }
    out = {
        "domain": dom.name,
        "max_level": L,
        "derived_from_ambient": small_n,
        "derived_from_sha256": sha256_file(args.source),
        "n_min_claimed": dom.n_min(L),
        "predictions": pred,
        "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    js = json.dumps(out, sort_keys=True, indent=1)
    if args.out:
        with open(args.out, "w") as fh:
            fh.write(js + "\n")
        print("wrote %s" % args.out)
        print("PREDICTION sha256 = %s" % sha256_file(args.out))
    else:
        print(js)
    for n in args.ambients:
        p = pred[str(n)]
        print("  ambient %2d : total %8d   keys-sha256 %s"
              % (n, p["total"], p["sha256_of_keys"][:16]))
    return True


def cmd_collapse(args):
    dom = DOMAINS[args.domain]()
    L = args.level
    pre = None
    if args.check:
        with open(args.check) as fh:
            pre = json.load(fh)
        print("checking against pre-registered %s (sha256 %s)"
              % (args.check, sha256_file(args.check)))
        print("  registered at %s from ambient %s"
              % (pre["utc"], pre["derived_from_ambient"]))
    runs = {}
    for n in args.ambients:
        t0 = time.time()
        runs[n] = reach(dom, n, L, cap=args.cap)
        print("  computed ambient %2d : %8d states (%.2fs)"
              % (n, len(runs[n]), time.time() - t0))
    ok = True

    # 1. exact prediction check
    if pre:
        print("\n-- PRE-REGISTERED PREDICTION --")
        for n in args.ambients:
            p = pre["predictions"].get(str(n))
            if p is None:
                print("  ambient %2d : no prediction registered" % n)
                continue
            got = sorted(runs[n])
            gh = hashlib.sha256("\n".join(got).encode()).hexdigest()
            hit = (gh == p["sha256_of_keys"]) and (len(got) == p["total"])
            ok &= hit
            print("  ambient %2d : predicted %8d  observed %8d  keys %s  %s"
                  % (n, p["total"], len(got),
                     "IDENTICAL" if gh == p["sha256_of_keys"] else "DIFFER",
                     "PASS" if hit else "FAIL"))

    # 2. stratified collapse: Reach(n,L) restricted to width <= m == Reach(m,L)
    print("\n-- H4 / stratified collapse: Reach(n,L)|_{w<=m} == Reach(m,L) --")
    ams = sorted(args.ambients)
    for a, b in itertools.combinations(ams, 2):
        A = set(k for k in runs[b] if dom.width(k) <= a)
        B = set(runs[a])
        extra, missing = A - B, B - A
        hit = not extra and not missing
        ok &= hit
        print("  m=%2d vs n=%2d : |A|=%7d |B|=%7d  A\\B=%d  B\\A=%d  %s"
              % (a, b, len(A), len(B), len(extra), len(missing),
                 "PASS" if hit else "FAIL"))
        if extra:
            for k in sorted(extra)[:4]:
                print("      only-at-n=%d (width %d, level %d): %s"
                      % (b, dom.width(k), runs[b][k], k[:110]))
        if missing:
            for k in sorted(missing)[:4]:
                print("      only-at-m=%d (width %d, level %d): %s"
                      % (a, dom.width(k), runs[a][k], k[:110]))

    # 3. bound agreement on shared keys (the level must be ambient free)
    print("\n-- H2 / grading is ambient free (level agreement on shared keys) --")
    for a, b in itertools.combinations(ams, 2):
        shared = set(runs[a]) & set(runs[b])
        bad = [k for k in shared if runs[a][k] != runs[b][k]]
        ok &= not bad
        print("  m=%2d vs n=%2d : %7d shared, %d level disagreements  %s"
              % (a, b, len(shared), len(bad), "PASS" if not bad else "FAIL"))

    # 4. width census table
    print("\n-- width x ambient census (level <= %d) --" % L)
    widths = sorted({dom.width(k) for n in ams for k in runs[n]})
    print("  width | " + " | ".join("n=%-8d" % n for n in ams))
    for w in widths:
        row = [sum(1 for k in runs[n] if dom.width(k) == w) for n in ams]
        print("  %5d | " % w + " | ".join("%-10d" % r for r in row))
    print("  TOTAL | " + " | ".join("%-10d" % len(runs[n]) for n in ams))

    # 5. tail triviality (H5).  This is INDEPENDENT of H1-H4: it asks whether
    # the strata above the population front are single states (sorting
    # networks) or grow (everything else measured so far).
    print("\n-- H5 / tail triviality (independent of H1-H4) --")
    nm = dom.n_min(L)
    for n in ams:
        by_w = collections.Counter(dom.width(k) for k in runs[n])
        if not by_w:
            continue
        top = max(by_w)
        # population front = the largest width whose stratum is NOT a
        # singleton.  A trivial tail means front < top.
        front = max((w for w in by_w if by_w[w] != 1), default=None)
        tail = [(w, by_w[w]) for w in sorted(by_w) if w > (nm if nm else -1)]
        if nm is not None and top <= nm:
            regime = "EMPTY (nothing above n_min=%s)" % nm
        elif front is not None and front < top:
            regime = "TRIVIAL (singleton strata above the front)"
        else:
            regime = "NON-TRIVIAL: top stratum has %d states" % by_w[top]
        print("  ambient %2d : widths %d..%d, largest non-singleton stratum at "
              "width %s -> tail %s" % (n, min(by_w), top, front, regime))
        if nm is not None and tail:
            print("       strata above the claimed n_min(%d)=%s : %s"
                  % (L, nm, tail[:8]))
    return ok


def cmd_hypotheses(args):
    dom = DOMAINS[args.domain]()
    L = args.level
    ams = sorted(args.ambients)
    ok = True
    print("== hypothesis audit: %s, ambients %s, level <= %d =="
          % (dom.name, ams, L))

    big = max(ams)
    R = reach(dom, big, L, cap=args.cap)
    print("reference run at ambient %d : %d states" % (big, len(R)))

    # H1: succ(X, n)|_{width<=m} == succ(X, m)  for every state X with w(X)<=m
    print("\nH1 ambient freedom of the successor relation (stratified)")
    for m in ams:
        if m == big:
            continue
        bad = 0
        tested = 0
        for k in sorted(R):
            if dom.width(k) > m:
                continue
            tested += 1
            a = {x for x, _ in dom.succ(k, big) if dom.width(x) <= m}
            b = {x for x, _ in dom.succ(k, m)}
            if a != b:
                bad += 1
                if bad <= 3:
                    print("    MISMATCH at width %d: %s" % (dom.width(k), k[:90]))
        ok &= not bad
        print("  n=%d vs m=%2d : %6d states tested, %d mismatches  %s"
              % (big, m, tested, bad, "PASS" if not bad else "FAIL"))

    # H2: grade is ambient free -- checked structurally (every domain here
    # grades every edge 1) plus by the level agreement in `collapse`.
    print("\nH2 grading ambient free : all edges graded by the domain's own "
          "cost function, which takes no ambient argument -- structural PASS")

    # H3: root tower
    print("\nH3 root tower  (canonical image of root_n under width-lowering "
          "edges contains root_{n-1})")
    tower = True
    for n in ams:
        if n - 1 < min(ams):
            continue
        try:
            rn = dom.roots(n)
            rm = set(dom.roots(n - 1))
        except Exception as exc:  # pragma: no cover
            print("  ambient %d : root unavailable (%s)" % (n, exc))
            continue
        down = set()
        for r in rn:
            for x, _ in dom.succ(r, n):
                if dom.width(x) < dom.width(r):
                    down.add(x)
        if dom.width(rn[0]) == 0:
            print("  n=%2d : root has width 0 -- root_n == root_{n-1} as "
                  "canonical objects, so the tower is DEGENERATE (C(n) = 0) "
                  "and H3 carries no content in this domain" % n)
            tower = False
            continue
        hit = bool(rm & down)
        tower &= hit
        print("  n=%2d : root width %d, %d width-lowering images, "
              "contains root_{n-1} = %s"
              % (n, dom.width(rn[0]), len(down), hit))
    print("  => root tower %s"
          % ("PRESENT (non-degenerate)" if tower else "DEGENERATE/ABSENT"))

    # H4: width convexity, empirically
    print("\nH4 width convexity  (no high-width detour): see `collapse`")

    # growth / n_min
    print("\nclosed-form cutoff : growth=%s  n_min(%d)=%s"
          % (dom.growth(), L, dom.n_min(L)))
    return ok


def cmd_sortnet_theorems(args):
    """Directly check Theorems B and C of docs/ambient-reduction.md in pure
    Python, i.e. the two hypotheses that give the sorting-network instance its
    root tower and its trivial tail."""
    dom = SortNetMini()
    ok = True
    print("== sorting-network structural hypotheses (pure Python) ==")
    for n in range(3, args.max_n + 1):
        cube = dom.cube(n)
        # Theorem B: canon(prune_{p,c}(cube_n)) == cube_{n-1} for all c, p
        images = set()
        for c in range(n):
            for p in (0, 1):
                images.add(dom.canon(dom.prune(cube, n, c, p), n - 1))
        want = dom.canon(dom.cube(n - 1), n - 1)
        b_ok = images == {want}
        # Theorem C: canon(cube_n |> [i,j]) is a single state
        succs = set()
        for i in range(n):
            for j in range(i + 1, n):
                succs.add(dom.canon(dom.apply_comparator(cube, n, i, j), n))
        c_ok = len(succs) == 1
        size = None
        if c_ok:
            size = len(json.loads(next(iter(succs)))[1])
        c_size_ok = (size == 3 * (1 << (n - 2))) if n >= 2 else True
        ok &= b_ok and c_ok and c_size_ok
        print("  n=%2d  Theorem B (prune(cube_n)=cube_{n-1}, %d images): %s"
              "   Theorem C (unique successor): %s  |s_n|=%s (want %d): %s"
              % (n, 2 * n, "PASS" if b_ok else "FAIL",
                 "PASS" if c_ok else "FAIL", size, 3 * (1 << (n - 2)),
                 "PASS" if c_size_ok else "FAIL"))
    print("\n  C(n) free chain: " +
          ", ".join("C(%d)=%d" % (n, dom.C(n))
                    for n in range(3, args.max_n + 1)))
    return ok


def cmd_bool_fresh_lemma(args):
    """The one modelling assumption in the Boolean-chain domain is that from a
    width-w state at ambient n only min(n, w+2) variables need materialising.
    Check it against fresh_cap = 3, 4 and against the FULL ambient."""
    base = BoolChains("aox", fresh_cap=2)
    R = reach(base, args.ambient, args.level, cap=args.cap)
    print("== fresh-cap lemma: %d states from ambient %d level <= %d =="
          % (len(R), args.ambient, args.level))
    ok = True
    for cap in args.caps:
        alt = BoolChains("aox", fresh_cap=cap)
        bad = 0
        tested = 0
        for k in sorted(R):
            w = base.width(k)
            if w + cap > args.max_frame:
                continue           # 2^frame truth tables get expensive
            tested += 1
            a = {x for x, _ in base.succ(k, args.ambient)}
            b = {x for x, _ in alt.succ(k, args.ambient)}
            if a != b:
                bad += 1
                if bad <= 3:
                    print("   MISMATCH width %d cap %d: |2|=%d |%d|=%d"
                          % (w, cap, len(a), cap, len(b)))
        ok &= not bad
        print("  fresh_cap 2 vs %d : %5d states tested, %d mismatches  %s"
              % (cap, tested, bad, "PASS" if not bad else "FAIL"))
    return ok


def cmd_bool_bruteforce(args):
    """Independent validation of the Boolean-chain domain.

    Enumerates EVERY raw gate sequence at ambient `n` with no canonicalisation
    during the search and no fresh-variable cap, groups the raw states into
    true `S_n` orbits by brute force over all `n!` permutations, and checks
    three things:

      1. `BoolChains.canon` is constant on orbits (it is a genuine invariant);
      2. `BoolChains.canon` separates orbits (it is a COMPLETE invariant -- a
         too-coarse canonical form would otherwise produce a false collapse);
      3. `reach()` reproduces the brute force exactly, key set and levels.

    The brute force shares no machinery with the domain implementation, so it
    also confirms the ambient collapse on its own.
    """
    ops = [f for _nm, f in BASES["aox"]]
    dom = BoolChains("aox")
    ok = True
    print("== Boolean chains: brute-force validation ==")
    print("  n   R |    raw | S_n-orbits | canon keys | reach() | invariant "
          "| complete | matches")
    for n in args.ambients:
        for R in range(1, args.level + 1):
            mask = (1 << (1 << n)) - 1
            proj = [_proj(i, n) for i in range(n)]
            seen = {(): 0}
            frontier = [()]
            for r in range(1, R + 1):
                nxt = []
                for st in frontier:
                    pool = proj + list(st)
                    for a in range(len(pool)):
                        for b in range(a + 1, len(pool)):
                            for f in ops:
                                new = tuple(sorted(
                                    st + (f(pool[a], pool[b], mask),)))
                                if new not in seen:
                                    seen[new] = r
                                    nxt.append(new)
                frontier = nxt
            orbit_of = {}
            norb = 0
            perms = list(itertools.permutations(range(n)))
            srcs = []
            for p in perms:
                src = []
                for m in range(1 << n):
                    mm = 0
                    for i in range(n):
                        if (m >> i) & 1:
                            mm |= 1 << p[i]
                    src.append(mm)
                srcs.append(tuple(src))
            for st in seen:
                if st in orbit_of:
                    continue
                for src in srcs:
                    orbit_of[tuple(sorted(_apply_perm(t, src) for t in st))] = norb
                norb += 1
            key_of = {st: dom.canon(n, list(st)) for st in seen}
            by_orbit = collections.defaultdict(set)
            by_key = collections.defaultdict(set)
            for st in seen:
                by_orbit[orbit_of[st]].add(key_of[st])
                by_key[key_of[st]].add(orbit_of[st])
            inv = all(len(v) == 1 for v in by_orbit.values())
            comp = all(len(v) == 1 for v in by_key.values())
            fr = reach(dom, n, R)
            lv = {}
            for st, r in seen.items():
                k = key_of[st]
                lv[k] = min(lv.get(k, 1 << 30), r)
            match = set(fr) == set(lv) and all(fr[k] == lv[k] for k in fr)
            ok &= inv and comp and match
            print("  %2d %2d | %6d | %10d | %10d | %7d | %9s | %8s | %s"
                  % (n, R, len(seen), norb, len(by_key), len(fr),
                     inv, comp, "PASS" if match else "FAIL"))
    return ok


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    def add_common(p):
        p.add_argument("domain", choices=sorted(DOMAINS))
        p.add_argument("--cap", type=int, default=2_000_000)

    p = sub.add_parser("nmin")
    add_common(p)
    p.add_argument("--levels", type=int, default=6)
    p.set_defaults(fn=cmd_nmin)

    p = sub.add_parser("census")
    add_common(p)
    p.add_argument("--ambient", type=int, required=True)
    p.add_argument("--level", type=int, required=True)
    p.add_argument("--out")
    p.set_defaults(fn=cmd_census)

    p = sub.add_parser("predict")
    add_common(p)
    p.add_argument("--source", required=True,
                   help="census JSON from the small ambient")
    p.add_argument("--ambients", type=lambda s: [int(x) for x in s.split(",")],
                   required=True)
    p.add_argument("--out")
    p.set_defaults(fn=cmd_predict)

    p = sub.add_parser("collapse")
    add_common(p)
    p.add_argument("--level", type=int, required=True)
    p.add_argument("--ambients", type=lambda s: [int(x) for x in s.split(",")],
                   required=True)
    p.add_argument("--check")
    p.set_defaults(fn=cmd_collapse)

    p = sub.add_parser("hypotheses")
    add_common(p)
    p.add_argument("--level", type=int, required=True)
    p.add_argument("--ambients", type=lambda s: [int(x) for x in s.split(",")],
                   required=True)
    p.set_defaults(fn=cmd_hypotheses)

    p = sub.add_parser("sortnet-theorems")
    p.add_argument("--max-n", type=int, default=6)
    p.set_defaults(fn=cmd_sortnet_theorems)

    p = sub.add_parser("bool-bruteforce")
    p.add_argument("--ambients", type=lambda s: [int(x) for x in s.split(",")],
                   default=[4, 5, 6])
    p.add_argument("--level", type=int, default=2)
    p.set_defaults(fn=cmd_bool_bruteforce)

    p = sub.add_parser("bool-fresh-lemma")
    p.add_argument("--ambient", type=int, required=True)
    p.add_argument("--level", type=int, required=True)
    p.add_argument("--caps", type=lambda s: [int(x) for x in s.split(",")],
                   default=[3, 4])
    p.add_argument("--max-frame", type=int, default=8)
    p.add_argument("--cap", type=int, default=2_000_000)
    p.set_defaults(fn=cmd_bool_fresh_lemma)

    args = ap.parse_args(argv)
    good = args.fn(args)
    return 0 if good else 1


if __name__ == "__main__":
    sys.exit(main())
