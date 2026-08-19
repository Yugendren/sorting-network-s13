#!/usr/bin/env python3
"""
class_filter.py -- branch-tree max-path tracer and the S(13) class prefix
filters (Filter 0 / Filter 1 / Filter 2), plus a generic root-split partition
usable at any leaf count.

Pure stdlib Python 3.  No third-party imports, no network access, no
comparator-count constants.  Where a size ceiling is conceptually needed the
module uses only V_CEILING = 512 (the shape-count admissibility ceiling of
docs/s13-shape-case-split.md Sec.1) -- never a comparator count.  This file
performs no search and embeds no witness sorting network: every test network
below is CONSTRUCTED by a named algorithm (Batcher odd-even mergesort, or an
explicit merge-schedule builder that realizes a target branch-tree shape from
scratch).

EPISTEMIC STATUS
-----------------
The three-way class split (C1/C2/C3, six abstract shapes S1..S6) implemented
here is a CONJECTURED case split, not a proved one.  Per
docs/van-voorhis-theory-report.md, the bridge statement that a network's
two-channel prunability is bounded by a function of its own MAX branch tree
(the chapter's eq (8), matching this document's "E1'") is confirmed as the
Plenum-1972 source's own headline result -- it is stated and used exactly as
the case split assumed, not merely a corollary the case split needed to
invent.  BUT the chapter's own *proof* of that headline result is not valid
as written: two structural lemmas it depends on (the union-of-paths count and
the MAX2 Kraft equality) are refuted by an explicit constructed 3-sorter, and
by a large fraction of larger constructed sorters.  A partial repair exists
(docs/kraft-repair-report.md): the headline result is now PROVED for *clean*
sorters (no pass-through comparators on any max-path), but the proposed
general-case repair (a per-node charging lemma) was itself refuted by an
adversarial counterexample, and no replacement general argument is in hand.
Consequently: every class-exhaustion result obtainable with the filters in
this module is CONDITIONAL on the case split (equivalently, on the un-repaired
general form of the bridge statement).  An unconditional lower-bound
improvement from this programme needs either the missing general repair or
full coverage of all admissible shapes by other means.  Nothing in this file
asserts, searches for, or depends on any specific comparator-count target;
it is pure shape/branch-tree structure.

FILTER-2 SOUNDNESS ARGUMENT (the load-bearing fact)
----------------------------------------------------
Appending comparators to a network prefix can only ever MERGE two ROOTS of
the current max-path forest into a new root; it can never alter the interior
of a tree that has already formed inside the forest (an already-merged
subtree's leaves and internal structure are frozen from that point on).
Therefore, at any prefix, the current forest is exactly an ANTICHAIN CUT of
whatever the eventual, completed branch tree turns out to be: each tree
currently in the forest is isomorphic to the subtree of the final tree that
hangs from the corresponding cut node.  Hence a prefix can be completed to a
network whose MAX branch tree is (abstractly) some target shape S only if the
forest's signature -- the sorted tuple of its trees' canonical abstract shapes
-- is one of S's "cut signatures" (the signatures reachable by cutting S at
any antichain of its nodes, including the trivial all-leaves cut and the
trivial single-root cut).  This is a NECESSARY condition on completability,
hence a sound prune; and it is prefix-monotone, because the contrapositive of
the argument above holds at every prefix depth: if the current signature is
not a cut signature of S, no future comparator sequence can repair that,
since every future forest signature is obtained from the current one by
further (monotone) merges of the current roots.

BRANCH-TREE VS LITERAL DEPTH -- WHY LITERAL DEPTH IS UNSOUND HERE
--------------------------------------------------------------------
A comparator that a max-path traverses does not always create a merge: if the
one-hot value that is "highest so far" enters a comparator (a,b) on lead b
(the max lead) while nothing tracked currently occupies lead a, the value
simply passes through -- the comparator is traversed but contributes no
depth to the *branch* tree, because no two max-paths met there.  Per
docs/van-voorhis-theory-report.md Sec.3.2/3.5/6.2, the quantity that governs
the two-channel bound (Theorem 1's f, i.e. this module's V) is a function of
the BRANCH tree (only genuine merges count as depth), not of literal
comparator counts along a path.  Literal depth is always >= branch depth, and
the two differ on a majority of constructed test networks.  Filter 0 is sound
using the LITERAL count because it descends from the one-channel theorem,
where the literal count is exactly the quantity that theorem bounds.  Filters
1 and 2 MUST use branch depths / the branch tree: using literal depths there
would reject completable prefixes (unsound as a prune).  This module
therefore maintains two entirely separate quantities per prefix --
literal_deltas() (per docs' delta(C,i)) and branch_depths() (the tree the
case split actually needs) -- and never conflates them.

MIN DUAL
--------
Per docs/van-voorhis-theory-report.md Sec.6.3/4.1, every filter here has a
MIN-side mirror: trace the smallest value from each channel to the minimum
output instead of the largest value to the maximum output.  MinPathForest
implements this mirror.  It is sound under exactly the same (conjectured)
hypotheses as the MAX-side filters and is exposed here, but this module does
NOT wire it into the default class filter; callers opt in explicitly (e.g.
via build_forest(net, n, dual=True)).

USAGE
-----
    python3 tools/class_filter.py --selftest          # all checks, exit 0/1
    python3 tools/class_filter.py --selftest --fast   # smaller random samples
    python3 tools/class_filter.py --shapes             # print S1..S6 table
    python3 tools/class_filter.py --trace "0-1,2-3" --n 13
"""

import argparse
import sys
import time
import random
from fractions import Fraction
from functools import lru_cache
from collections import defaultdict

V_CEILING = 512
INF = float("inf")

# ===========================================================================
# PART 1 -- abstract shape arithmetic
#
# An abstract (canonical, up-to-reflection) shape is a nested tuple: () is a
# leaf; (l, r) is an internal node with l <= r under Python tuple ordering
# (this is what makes it canonical: children are always presented in a fixed,
# reflection-independent order).
# ===========================================================================


def parse_sexpr(s):
    """Parse an s-expression of the form used in docs/s13-shape-case-split.md
    Sec.5 ('*' = leaf) into a nested tuple, () = leaf."""
    tokens = s.replace("(", " ( ").replace(")", " ) ").split()
    pos = [0]

    def parse():
        tok = tokens[pos[0]]
        if tok == "*":
            pos[0] += 1
            return ()
        if tok == "(":
            pos[0] += 1
            left = parse()
            right = parse()
            if tokens[pos[0]] != ")":
                raise ValueError("expected ')' at token %d, got %r"
                                  % (pos[0], tokens[pos[0]]))
            pos[0] += 1
            return (left, right)
        raise ValueError("unexpected token %r" % tok)

    result = parse()
    if pos[0] != len(tokens):
        raise ValueError("trailing tokens: %r" % (tokens[pos[0]:],))
    return result


def canon_shape(t):
    """Canonicalise a (possibly non-canonical) nested-tuple shape: leaf -> (),
    internal -> sorted pair of canonicalised children."""
    if t == ():
        return ()
    l, r = t
    cl, cr = canon_shape(l), canon_shape(r)
    return tuple(sorted((cl, cr)))


@lru_cache(maxsize=None)
def leaves(shape):
    """Number of leaves of a canonical shape."""
    if shape == ():
        return 1
    return leaves(shape[0]) + leaves(shape[1])


@lru_cache(maxsize=None)
def height(shape):
    """Height in edges; a single leaf has height 0."""
    if shape == ():
        return 0
    return 1 + max(height(shape[0]), height(shape[1]))


def depths(shape):
    """Sorted tuple (multiset) of leaf depths."""
    out = []

    def walk(s, d):
        if s == ():
            out.append(d)
        else:
            walk(s[0], d + 1)
            walk(s[1], d + 1)

    walk(shape, 0)
    return tuple(sorted(out))


@lru_cache(maxsize=None)
def V(shape):
    """V(leaf) = 0; V(T) = 2*(V(Tl) + V(Tr) + 2**(h(Tl)+h(Tr))).
    docs/s13-shape-case-split.md Sec.1 / Theorem 1 of the Plenum chapter."""
    if shape == ():
        return 0
    l, r = shape
    return 2 * (V(l) + V(r) + 2 ** (height(l) + height(r)))


@lru_cache(maxsize=None)
def g(s, h):
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
def F(n):
    """F(n) = min over all n-leaf shapes of V."""
    return min(g(n, h) for h in range(0, n))


@lru_cache(maxsize=None)
def abstract_shapes(n):
    """All abstract (canonical, up-to-reflection) binary tree shapes with n
    leaves, generated directly (no plane-shape enumeration + dedupe), by the
    standard Wedderburn-Etherington recursion: split n = s1+s2, combine every
    abstract shape of size s1 with every abstract shape of size s2; when
    s1==s2 only unordered pairs (including the pair with itself) are taken so
    each abstract shape is produced exactly once."""
    if n == 1:
        return ((),)
    result = set()
    for s1 in range(1, n // 2 + 1):
        s2 = n - s1
        left = abstract_shapes(s1)
        right = abstract_shapes(s2)
        if s1 == s2:
            for i, a in enumerate(left):
                for b in left[i:]:
                    result.add(tuple(sorted((a, b))))
        else:
            for a in left:
                for b in right:
                    result.add(tuple(sorted((a, b))))
    return tuple(sorted(result))


def root_split_key(shape):
    """The unordered {(leaves,height), (leaves,height)} root-split key of a
    (non-leaf) canonical shape."""
    l, r = shape
    a = (leaves(l), height(l))
    b = (leaves(r), height(r))
    return tuple(sorted((a, b)))


@lru_cache(maxsize=None)
def root_split_classes(n):
    """A COMPLETE partition (exhaustive and disjoint by construction, since
    every shape has exactly one root-split key) of all n-leaf abstract shapes
    by root_split_key.  Returns {key: tuple of shapes}."""
    classes = defaultdict(list)
    for s in abstract_shapes(n):
        classes[root_split_key(s)].append(s)
    return {k: tuple(v) for k, v in classes.items()}


# ===========================================================================
# PART 2 -- the six admissible S(13) shapes, the three classes, four profiles
# docs/s13-shape-case-split.md Sec.5
# ===========================================================================

_S_EXPR = {
    "S1": "(((* *) ((* *) (* *))) ((* (* *)) ((* *) (* *))))",
    "S2": "(((* *) (* (* *))) (((* *) (* *)) ((* *) (* *))))",
    "S3": "((* ((* *) (* *))) (((* *) (* *)) ((* *) (* *))))",
    "S4": "(((* (* *)) (* (* *))) ((* (* *)) ((* *) (* *))))",
    "S5": "(((* *) (* *)) (((* *) (* *)) ((* *) (* (* *)))))",
    "S6": "(((* *) (* *)) ((* ((* *) (* *))) ((* *) (* *))))",
}

SHAPES = {name: canon_shape(parse_sexpr(expr)) for name, expr in _S_EXPR.items()}

CLASS_MEMBERS = {"C1": ("S2", "S3"), "C2": ("S1", "S4"), "C3": ("S5", "S6")}
CLASS_OF = {name: cls for cls, names in CLASS_MEMBERS.items() for name in names}
SHAPES_BY_CLASS = {cls: frozenset(SHAPES[name] for name in names)
                   for cls, names in CLASS_MEMBERS.items()}

PROFILES = {
    "P1": tuple(sorted((3, 3, 3) + (4,) * 10)),
    "P2": tuple(sorted((2,) + (4,) * 12)),
    "P3": tuple(sorted((3, 3, 3, 3) + (4,) * 7 + (5, 5))),
    "P4": tuple(sorted((3,) * 5 + (4,) * 4 + (5,) * 4)),
}
SHAPE_PROFILE = {"S1": "P1", "S2": "P1", "S3": "P2",
                  "S4": "P1", "S5": "P3", "S6": "P4"}


# ===========================================================================
# PART 3 -- the branch-tree max-path / min-path tracer
# docs/s13-shape-case-split.md Sec.2 (see also this module's docstring for the
# soundness argument the tracer's incremental algorithm depends on)
# ===========================================================================


class _PathForest(object):
    """Incremental tracer for the MAX branch tree (dual=False) or MIN branch
    tree (dual=True).  Node-table entries are ('leaf', channel) or
    ('internal', left, right); `node[c]` is the current occupant of channel c
    or None."""

    def __init__(self, n, dual=False):
        self.n = n
        self.dual = dual
        self.node = [("leaf", c) for c in range(n)]
        self._pos = list(range(n))
        self._literal_delta = [0] * n
        self.branch_log = []  # per apply() call: True iff it created a branch node

    def apply(self, a, b):
        if a == b:
            raise ValueError("comparator channels must differ: %r" % ((a, b),))

        # --- literal one-hot trace (Filter 0's quantity; a different number
        #     from the branch-tree depth) ---------------------------------
        dst = a if self.dual else b
        pos = self._pos
        ld = self._literal_delta
        for i in range(self.n):
            if pos[i] == a or pos[i] == b:
                ld[i] += 1
                pos[i] = dst

        # --- merge-forest (branch tree) update ------------------------------
        # MAX: source=a, target=b (max moves a->b).
        # MIN (mirror): source=b, target=a (min moves b->a).
        src, tgt = (b, a) if self.dual else (a, b)
        n_src, n_tgt = self.node[src], self.node[tgt]
        if n_src is None:
            self.branch_log.append(False)
            return
        if n_tgt is None:
            self.node[tgt] = n_src
            self.node[src] = None
            self.branch_log.append(False)
            return
        self.node[tgt] = ("internal", n_src, n_tgt)
        self.node[src] = None
        self.branch_log.append(True)

    def apply_network(self, net):
        for a, b in net:
            self.apply(a, b)

    def roots(self):
        return [x for x in self.node if x is not None]

    def forest_signature(self):
        return tuple(sorted(canon(r) for r in self.roots()))

    def branch_depths(self):
        out = {}

        def walk(node, d):
            if node[0] == "leaf":
                out[node[1]] = d
            else:
                walk(node[1], d + 1)
                walk(node[2], d + 1)

        for r in self.roots():
            walk(r, 0)
        return out

    def literal_deltas(self):
        return {i: self._literal_delta[i] for i in range(self.n)}

    def is_complete(self):
        return len(self.roots()) == 1

    def tree(self):
        if not self.is_complete():
            raise ValueError("forest is not complete (%d roots)" % len(self.roots()))
        return self.roots()[0]

    def copy(self):
        other = type(self)(self.n)
        other.node = list(self.node)
        other._pos = list(self._pos)
        other._literal_delta = list(self._literal_delta)
        other.branch_log = list(self.branch_log)
        return other


class MaxPathForest(_PathForest):
    def __init__(self, n):
        super(MaxPathForest, self).__init__(n, dual=False)


class MinPathForest(_PathForest):
    def __init__(self, n):
        super(MinPathForest, self).__init__(n, dual=True)


def build_forest(net, n, dual=False):
    forest = MinPathForest(n) if dual else MaxPathForest(n)
    forest.apply_network(net)
    return forest


def canon(node):
    """canon() for a live node-table entry (as opposed to canon_shape() for an
    already-abstract shape tuple): leaf -> (); internal -> canonical pair."""
    if node[0] == "leaf":
        return ()
    _, l, r = node
    return tuple(sorted((canon(l), canon(r))))


# ===========================================================================
# PART 4 -- the prefix filters
# ===========================================================================


def filter0(forest, limit=5):
    """Filter 0: class-independent, LITERAL count.  max_i literal_delta[i]
    <= limit.  Sound from the one-channel theorem alone."""
    ld = forest.literal_deltas()
    if not ld:
        return True
    return max(ld.values()) <= limit


def filter1(forest, profiles):
    """Filter 1 (prefix form): a profile P (sorted n-tuple) is still reachable
    iff, sorting both lb and P ascending, lb[k] <= P[k] for every k, where
    lb_i = branch_depth_i + (1 if >=2 roots remain, else 0)."""
    n = forest.n
    m = len(forest.roots())
    bd = forest.branch_depths()
    bump = 1 if m >= 2 else 0
    lb = sorted(bd.get(i, 0) + bump for i in range(n))
    for p in profiles:
        ps = sorted(p)
        if len(ps) != n:
            continue
        if all(lb[k] <= ps[k] for k in range(n)):
            return True
    return False


@lru_cache(maxsize=None)
def cutsigs(shape):
    """The set of cut signatures of an abstract shape (memoised on the shape
    itself).  See the module docstring, "FILTER-2 SOUNDNESS ARGUMENT".

        cutsigs(leaf) = { ((),) }
        cutsigs(u)    = { (canon(u),) } | { merge(x,y) : x in cutsigs(l),
                                             y in cutsigs(r) }
        merge(x,y) = tuple(sorted(x + y))
    """
    if shape == ():
        return frozenset({((),)})
    l, r = shape
    result = {(shape,)}
    for x in cutsigs(l):
        for y in cutsigs(r):
            result.add(tuple(sorted(x + y)))
    return frozenset(result)


def _cutsigs_for_shapes(shapes):
    sigs = set()
    for s in shapes:
        sigs |= cutsigs(s)
    return frozenset(sigs)


CUTSIGS = {cls: _cutsigs_for_shapes(SHAPES_BY_CLASS[cls]) for cls in CLASS_MEMBERS}


def class_prefix_ok(forest, class_name):
    """Filter 2 (EXACT prefix form): O(1) set lookup after computing the
    forest's signature.  Sound (necessary, never rejects a completable
    prefix) and prefix-monotone."""
    return forest.forest_signature() in CUTSIGS[class_name]


def class_complete_ok(forest, class_name):
    return forest.is_complete() and canon(forest.tree()) in SHAPES_BY_CLASS[class_name]


_GENERIC_CUTSIGS_CACHE = {}


def generic_cutsigs(n, key):
    """Cached per (n, key): union of cutsigs over every n-leaf abstract shape
    whose root_split_key equals key."""
    cache_key = (n, key)
    cached = _GENERIC_CUTSIGS_CACHE.get(cache_key)
    if cached is not None:
        return cached
    shapes = root_split_classes(n).get(key, ())
    result = _cutsigs_for_shapes(shapes)
    _GENERIC_CUTSIGS_CACHE[cache_key] = result
    return result


def generic_prefix_ok(forest, key, n):
    """The generic (root-split-key) analogue of class_prefix_ok, for arbitrary
    n; used for the n=9/n=10 partition-exhaustiveness validation.  This
    partition is exhaustive and disjoint BY CONSTRUCTION and does not depend
    on any conjecture."""
    return forest.forest_signature() in generic_cutsigs(n, key)


# ===========================================================================
# PART 5 -- constructors: Batcher odd-even mergesort, and a shape-realizing
# merge scheduler.  No witness network is embedded: both are general
# algorithms parameterised by n (Batcher) or by a target abstract shape /
# random tree (the scheduler).
# ===========================================================================


def batcher(n):
    """Batcher's odd-even mergesort, comparator (a,b): min->a, max->b."""
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


def run_network(net, vals):
    v = list(vals)
    for a, b in net:
        if v[a] > v[b]:
            v[a], v[b] = v[b], v[a]
    return v


def sorts(net, n):
    for x in range(1 << n):
        v = run_network(net, [(x >> i) & 1 for i in range(n)])
        if any(v[i] > v[i + 1] for i in range(n - 1)):
            return False
    return True


def schedule_tree(t):
    """Realize a binary tree t as a comparator sequence: leaves that are ()
    get auto-numbered channels (0,1,2,... in the order encountered); leaves
    that are already ints use that channel directly.  At each internal node,
    once both children's channels are established, emit one comparator
    (min(wa,wb), max(wa,wb)) -- i.e. "pick two current roots that are
    siblings in the target and emit a comparator between their channels" --
    and the merged tree's channel becomes the larger of the two.  The
    resulting sequence need not sort; it is used only to realize a target
    branch-tree shape for testing the filters against it."""
    net = []
    counter = [0]

    def rec(node):
        if isinstance(node, tuple):
            if node == ():
                c = counter[0]
                counter[0] += 1
                return c
            wa, wb = rec(node[0]), rec(node[1])
            a, b = (wa, wb) if wa < wb else (wb, wa)
            net.append((a, b))
            return b
        return node  # already a channel index

    rec(t)
    return net


def random_shape_tree(channel_list, rng):
    """A structurally arbitrary binary tree over the given (already shuffled)
    list of channel labels: recursively split at a random point."""
    if len(channel_list) == 1:
        return channel_list[0]
    k = rng.randint(1, len(channel_list) - 1)
    left = random_shape_tree(channel_list[:k], rng)
    right = random_shape_tree(channel_list[k:], rng)
    return (left, right)


def strip_labels(t):
    """Replace int leaves with () so the tree can be canon_shape()'d."""
    if isinstance(t, tuple):
        return (strip_labels(t[0]), strip_labels(t[1]))
    return ()


# ===========================================================================
# PART 6 -- self-tests
# ===========================================================================

CHECKS = []


def check(name, ok, detail=""):
    CHECKS.append((name, bool(ok), detail))
    return bool(ok)


def hdr(title):
    print()
    print("=" * 78)
    print(title)
    print("=" * 78)


_WE = [0, 1, 1, 1, 2, 3, 6, 11, 23, 46, 98, 207, 451, 983]

_EXPECTED_G = {
    (1, 0): 0,
    (2, 1): 2,
    (3, 2): 8,
    (4, 2): 16, (4, 3): 24,
    (5, 3): 36, (5, 4): 64,
    (6, 3): 52, (6, 4): 84, (6, 5): 160,
    (7, 3): 80, (7, 4): 108, (7, 5): 196, (7, 6): 384,
    (8, 3): 96, (8, 4): 140, (8, 5): 236, (8, 6): 452,
    (9, 4): 168, (9, 5): 284, (9, 6): 524,
    (10, 4): 200, (10, 5): 328, (10, 6): 604,
    (11, 4): 256, (11, 5): 376, (11, 6): 680,
    (12, 4): 288, (12, 5): 440, (12, 6): 760,
    (13, 4): 392, (13, 5): 496, (13, 6): 856,
}


def _selftest_1():
    hdr("CHECK 1  -- shape arithmetic reproduces the audited document")

    def perfect(h):
        return () if h == 0 else (perfect(h - 1), perfect(h - 1))

    ok = all(V(perfect(h)) == h * 2 ** (2 * h - 1) for h in range(1, 6))
    check("1a  V(perfect tree of height h) == h*2**(2h-1), h=1..5", ok,
          "got %s" % [V(perfect(h)) for h in range(1, 6)])

    bad = []
    for s in range(1, 14):
        for h in range(0, 7):
            expect = _EXPECTED_G.get((s, h), INF)
            if g(s, h) != expect:
                bad.append((s, h, g(s, h), expect))
    check("1b  DP g(s,h) matches docs/s13-shape-case-split.md Sec.5.1 exactly, s<=13",
          not bad, repr(bad[:5]))
    check("1c  g(13,4)=392, g(13,5)=496, g(13,6)=856",
          g(13, 4) == 392 and g(13, 5) == 496 and g(13, 6) == 856,
          "got %r/%r/%r" % (g(13, 4), g(13, 5), g(13, 6)))

    we_ok = all(len(abstract_shapes(n)) == _WE[n] for n in range(1, 14))
    check("1d  abstract_shapes(n) reproduces Wedderburn-Etherington A001190, n=1..13",
          we_ok, "got %s" % [len(abstract_shapes(n)) for n in range(1, 14)])

    shapes13 = abstract_shapes(13)
    survivors = [s for s in shapes13 if V(s) <= V_CEILING]
    check("1e  exactly 6 of the 983 abstract 13-leaf shapes have V<=V_CEILING",
          len(survivors) == 6, "got %d" % len(survivors))
    check("1f  the 6 survivors are exactly S1..S6 (as canonical forms)",
          set(survivors) == set(SHAPES.values()),
          "missing=%r extra=%r" % (set(SHAPES.values()) - set(survivors),
                                    set(survivors) - set(SHAPES.values())))

    expected_vh = {"S1": (392, 4), "S2": (392, 4), "S3": (400, 4),
                    "S4": (416, 4), "S5": (496, 5), "S6": (512, 5)}
    bad = [name for name, (v, h) in expected_vh.items()
           if (V(SHAPES[name]), height(SHAPES[name])) != (v, h)]
    check("1g  S1..S6 have the stated V and height", not bad, repr(bad))

    expected_rs = {"S1": ((6, 3), (7, 3)), "S2": ((5, 3), (8, 3)),
                    "S3": ((5, 3), (8, 3)), "S4": ((6, 3), (7, 3)),
                    "S5": ((4, 2), (9, 4)), "S6": ((4, 2), (9, 4))}
    bad = [name for name, k in expected_rs.items()
           if root_split_key(SHAPES[name]) != k]
    check("1h  S1..S6 have the stated root splits", not bad, repr(bad))

    excluded = [V(s) for s in shapes13 if V(s) > V_CEILING]
    check("1i  smallest excluded V is 528", min(excluded) == 528,
          "got %d" % min(excluded))

    prof_ok = all(depths(SHAPES[name]) == PROFILES[pkey]
                  for name, pkey in SHAPE_PROFILE.items())
    check("1j  P1..P4 are exactly the leaf-depth multisets of S1,S2,S4 / S3 / S5 / S6",
          prof_ok)
    kraft_ok = all(sum(Fraction(1, 2 ** d) for d in p) == 1 for p in PROFILES.values())
    check("1k  each of P1..P4 satisfies Kraft equality", kraft_ok)


def _selftest_2():
    hdr("CHECK 2  -- the van Voorhis 3-sorter counterexample")
    n = 3
    T = [(0, 1), (0, 2), (1, 2)]
    check("2a  T sorts (exhaustive 0/1 test)", sorts(T, n))

    forest = MaxPathForest(n)
    forest.apply_network(T)
    check("2b  branch tree has 3 leaves, 2 internal nodes",
          forest.is_complete() and leaves(canon(forest.tree())) == 3
          and forest.branch_log.count(True) == 2,
          "roots=%d leaves=%r branches=%d"
          % (len(forest.roots()),
             leaves(canon(forest.tree())) if forest.is_complete() else None,
             forest.branch_log.count(True)))
    check("2c  comparator (0,2) (index 1) is a pass-through, not a branch node",
          forest.branch_log == [True, False, True],
          "branch_log=%r" % forest.branch_log)

    ld = forest.literal_deltas()
    bd = forest.branch_depths()
    check("2d  literal_deltas() == {0:2, 1:2, 2:2}", ld == {0: 2, 1: 2, 2: 2},
          "got %r" % ld)
    check("2e  branch_depths() == {0:2, 1:2, 2:1}", bd == {0: 2, 1: 2, 2: 1},
          "got %r" % bd)
    check("2f  literal_deltas() and branch_depths() differ", ld != bd)
    check("2g  V(canon(branch tree)) == 8", V(canon(forest.tree())) == 8,
          "got %d" % V(canon(forest.tree())))


def _selftest_3():
    hdr("CHECK 3  -- Batcher anchors")
    b8 = batcher(8)
    b12 = batcher(12)
    check("3a  Batcher-8 sorts (exhaustive)", sorts(b8, 8))
    check("3b  Batcher-12 sorts (exhaustive over 4096 vectors)", sorts(b12, 12))

    max8 = MaxPathForest(8)
    max8.apply_network(b8)
    min8 = MinPathForest(8)
    min8.apply_network(b8)
    max12 = MaxPathForest(12)
    max12.apply_network(b12)

    v_max8 = V(canon(max8.tree()))
    v_min8 = V(canon(min8.tree()))
    v_max12 = V(canon(max12.tree()))
    check("3c  V(MAX branch tree of Batcher-8) == 96 == F(8)",
          v_max8 == 96 == F(8), "got %d, F(8)=%d" % (v_max8, F(8)))
    check("3d  V(MIN branch tree of Batcher-8) == 96",
          v_min8 == 96, "got %d" % v_min8)
    check("3e  V(MAX branch tree of Batcher-12) == 288 == F(12)",
          v_max12 == 288 == F(12), "got %d, F(12)=%d" % (v_max12, F(12)))


def _selftest_4():
    hdr("CHECK 4  -- realizability + end-to-end filter check for S1..S6")
    n = 13
    all_pass = True
    for name in ("S1", "S2", "S3", "S4", "S5", "S6"):
        shape = SHAPES[name]
        cls = CLASS_OF[name]
        other_classes = [c for c in CLASS_MEMBERS if c != cls]
        net = schedule_tree(shape)  # need NOT sort; realizes the MAX branch shape only
        forest = MaxPathForest(n)
        profile = [PROFILES[SHAPE_PROFILE[name]]]

        prefix_ok = True
        f1_ok = True
        for a, b in net:
            forest.apply(a, b)
            if not class_prefix_ok(forest, cls):
                prefix_ok = False
            if not filter1(forest, profile):
                f1_ok = False

        complete_own = class_complete_ok(forest, cls)
        complete_others = all(not class_complete_ok(forest, c) for c in other_classes)

        ok = prefix_ok and f1_ok and complete_own and complete_others
        all_pass = all_pass and ok
        check("4-%s  class_prefix_ok(%s) True at every prefix; Filter1 passes "
              "at every prefix; complete_ok True for %s and False for %s "
              "(sequence realizes the shape, need not sort)"
              % (name, cls, cls, other_classes),
              ok, "prefix_ok=%s f1_ok=%s complete_own=%s complete_others=%s"
              % (prefix_ok, f1_ok, complete_own, complete_others))
    check("4z  all six shapes pass end-to-end", all_pass)


def _selftest_5(fast):
    hdr("CHECK 5  -- prefix monotonicity, randomised")
    n = 13
    rng = random.Random(20260817)
    trials = 300 if fast else 2000
    max_len = 40
    mono_violations = []
    depth_violations = []
    for _ in range(trials):
        length = rng.randint(0, max_len)
        net = [tuple(rng.sample(range(n), 2)) for _ in range(length)]
        forest = MaxPathForest(n)
        state = {c: True for c in CLASS_MEMBERS}
        prev_bd = {i: 0 for i in range(n)}
        for a, b in net:
            forest.apply(a, b)
            bd = forest.branch_depths()
            for i in range(n):
                if bd.get(i, 0) < prev_bd.get(i, 0):
                    depth_violations.append((net, i))
            prev_bd = bd
            for c in CLASS_MEMBERS:
                ok_now = class_prefix_ok(forest, c)
                if not state[c] and ok_now:
                    mono_violations.append((c, net))
                state[c] = state[c] and ok_now
    check("5a  class_prefix_ok never flips False->True along a prefix (%d trials)"
          % trials, not mono_violations, repr(mono_violations[:2]))
    check("5b  branch depths are non-decreasing along every prefix (%d trials)"
          % trials, not depth_violations, repr(depth_violations[:2]))


def _selftest_6(fast):
    hdr("CHECK 6  -- soundness (no false rejects), randomised complete schedules")
    n = 13
    rng = random.Random(20260818)
    trials = 500 if fast else 5000
    violations = []
    tested_with_class = 0
    for _ in range(trials):
        channels = list(range(n))
        rng.shuffle(channels)
        tree = random_shape_tree(channels, rng)
        net = schedule_tree(tree)
        shape = canon_shape(strip_labels(tree))
        name = next((nm for nm, s in SHAPES.items() if s == shape), None)
        if name is None:
            continue
        cls = CLASS_OF[name]
        tested_with_class += 1
        forest = MaxPathForest(n)
        for a, b in net:
            forest.apply(a, b)
            if not class_prefix_ok(forest, cls):
                violations.append((cls, net))
                break
    check("6a  every prefix of every admissible-class random complete schedule "
          "passes class_prefix_ok (%d/%d schedules had an admissible shape)"
          % (tested_with_class, trials),
          not violations, repr(violations[:2]))


def _selftest_7(fast):
    hdr("CHECK 7  -- partition exhaustiveness at n=9 and n=10")
    rng = random.Random(20260819)
    trials_each = 250 if fast else 2500
    violations = []
    key_misses = []
    for n in (9, 10):
        classes = root_split_classes(n)
        for _ in range(trials_each):
            channels = list(range(n))
            rng.shuffle(channels)
            tree = random_shape_tree(channels, rng)
            net = schedule_tree(tree)
            shape = canon_shape(strip_labels(tree))
            key = root_split_key(shape)
            if key not in classes or shape not in classes[key]:
                key_misses.append((n, key))
                continue
            forest = MaxPathForest(n)
            for a, b in net:
                forest.apply(a, b)
                if not generic_prefix_ok(forest, key, n):
                    violations.append((n, key, net))
                    break
    check("7a  every random complete schedule at n=9,10 falls into exactly one "
          "root_split_classes key (%d trials each)" % trials_each,
          not key_misses, repr(key_misses[:2]))
    check("7b  generic_prefix_ok holds at every prefix for that key",
          not violations, repr(violations[:2]))


def _selftest_8():
    hdr("CHECK 8  -- cut-signature table sizes (printed, not asserted)")
    for cls in ("C1", "C2", "C3"):
        print("  |CUTSIGS[%s]| = %d" % (cls, len(CUTSIGS[cls])))
    for n in (9, 10):
        classes = root_split_classes(n)
        print("  n=%d: %d root-split keys, %d abstract shapes total"
              % (n, len(classes), len(abstract_shapes(n))))
        for key in sorted(classes):
            size = len(generic_cutsigs(n, key))
            print("    key=%-40s  shapes=%-3d  |cutsigs|=%d"
                  % (str(key), len(classes[key]), size))
    check("8z  cut-signature table sizes printed", True)


def selftest(fast=False):
    t0 = time.time()
    CHECKS[:] = []
    _selftest_1()
    _selftest_2()
    _selftest_3()
    _selftest_4()
    _selftest_5(fast)
    _selftest_6(fast)
    _selftest_7(fast)
    _selftest_8()

    hdr("SUMMARY")
    failed = [c for c in CHECKS if not c[1]]
    for name, ok, detail in CHECKS:
        print("  [%s] %s%s" % ("PASS" if ok else "FAIL", name,
                                ("   -- " + detail) if detail else ""))
    elapsed = time.time() - t0
    print()
    print("  runtime: %.2f s" % elapsed)
    if failed:
        print("  %d of %d checks FAILED." % (len(failed), len(CHECKS)))
        return 1
    print("  All %d checks passed." % len(CHECKS))
    return 0


# ===========================================================================
# PART 7 -- CLI
# ===========================================================================


def print_shapes():
    print("%-4s %6s %6s %-10s %-6s %s" % ("id", "V", "height", "root", "class", "profile"))
    for name in ("S1", "S2", "S3", "S4", "S5", "S6"):
        s = SHAPES[name]
        l, r = s
        rs = "%d|%d" % (leaves(l), leaves(r))
        print("%-4s %6d %6d %-10s %-6s %s"
              % (name, V(s), height(s), rs, CLASS_OF[name], SHAPE_PROFILE[name]))


def parse_prefix_string(s):
    s = s.strip()
    if not s:
        return []
    out = []
    for tok in s.split(","):
        a, b = tok.split("-")
        out.append((int(a), int(b)))
    return out


def print_trace(spec_str, n):
    net = parse_prefix_string(spec_str)
    forest = MaxPathForest(n)
    forest.apply_network(net)
    print("forest signature :", forest.forest_signature())
    print("branch depths    :", forest.branch_depths())
    print("literal deltas   :", forest.literal_deltas())
    print("is_complete      :", forest.is_complete())
    if n == 13:
        for cls in ("C1", "C2", "C3"):
            print("class_prefix_ok(%s) = %s" % (cls, class_prefix_ok(forest, cls)))
    else:
        print("(per-class prefix verdicts only defined for n=13)")


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="branch-tree max-path tracer and S(13) class prefix filters")
    ap.add_argument("--selftest", action="store_true", help="run all checks")
    ap.add_argument("--fast", action="store_true", help="smaller random samples")
    ap.add_argument("--shapes", action="store_true", help="print S1..S6 table")
    ap.add_argument("--trace", type=str, default=None,
                     help="comma-separated a-b comparator prefix, e.g. 0-1,2-3")
    ap.add_argument("--n", type=int, default=13, help="channel count for --trace")
    args = ap.parse_args(argv)

    if args.selftest:
        return selftest(fast=args.fast)
    if args.shapes:
        print_shapes()
        return 0
    if args.trace is not None:
        print_trace(args.trace, args.n)
        return 0
    ap.print_help()
    return 1


if __name__ == "__main__":
    sys.setrecursionlimit(10000)
    sys.exit(main())
