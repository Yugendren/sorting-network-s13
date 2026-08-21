#!/usr/bin/env python3
"""verify_ambient.py -- machine checks for the Ambient-Freedom / Lemma L claims.

Operates on `Search::dump_states` output directories (`sortnetopt search <n>
-l <L> <dir>`), which contain `index.txt` plus files

    group_<width>_<lower_bound>.bin

Each such file is a concatenation of fixed-size packed canonical output-set
keys; the record size at width w is exactly `packed_len_for_channels(w)` =
2**w // 8 bytes (see `src/output_set.rs`).  The file name therefore carries
both the width and the stored lower bound, so a dump is a complete
`(width, packed key) -> lower bound` table.

Nothing here needs the engine: a dump is self-describing.

Subcommands
-----------
census    DUMP...            width x lower-bound census, one column per dump
compare   A B                key-set + bound comparison, per width
lemma-l   HI LO              the exact Lemma L test (HI at ambient n, LO at n-1)
chain     DUMP...            the free-chain claim: one state per width above
                             the population front, at bound C(w) + level
selfcheck DUMP               internal consistency (record sizes divide, no
                             duplicate keys, no key in two bound groups)

Exit status is 0 iff every requested check passed.
"""

import argparse
import collections
import os
import re
import sys

GROUP_RE = re.compile(r"^group_(\d+)_(\d+)\.bin$")


def packed_len(width: int) -> int:
    """Bytes per packed key at `width`; mirrors packed_len_for_channels."""
    return ((1 << width) + 7) // 8


def free_chain_bound(n: int) -> int:
    """C(n) = 3 + sum_{k=4..n} ceil(log2 k) -- the van Voorhis/Huffman floor."""
    total = 3
    for k in range(4, n + 1):
        total += (k - 1).bit_length()  # ceil(log2 k) for k >= 1
    return total


def load_dump(path):
    """-> dict width -> dict key(bytes) -> bound(int), plus a problem list."""
    problems = []
    table = collections.defaultdict(dict)
    if not os.path.isdir(path):
        raise SystemExit("not a directory: %s" % path)
    for name in sorted(os.listdir(path)):
        m = GROUP_RE.match(name)
        if not m:
            if name != "index.txt":
                problems.append("unexpected file %s" % name)
            continue
        width, bound = int(m.group(1)), int(m.group(2))
        rec = packed_len(width)
        blob = open(os.path.join(path, name), "rb").read()
        if len(blob) % rec:
            problems.append(
                "%s: %d bytes is not a multiple of the width-%d record size %d"
                % (name, len(blob), width, rec)
            )
        w = table[width]
        for off in range(0, len(blob) - rec + 1, rec):
            key = blob[off : off + rec]
            if key in w:
                problems.append(
                    "%s: key already present at bound %d (duplicate or "
                    "cross-group collision)" % (name, w[key])
                )
            w[key] = bound
    return dict(table), problems


def total(table):
    return sum(len(v) for v in table.values())


# --------------------------------------------------------------------------
def cmd_census(args):
    dumps = [(p, load_dump(p)[0]) for p in args.dumps]
    widths = sorted({w for _, t in dumps for w in t})
    names = [os.path.basename(p.rstrip("/")) for p, _ in dumps]
    print("width | " + " | ".join("%12s" % n for n in names))
    for w in widths:
        row = ["%12d" % len(t.get(w, {})) for _, t in dumps]
        print("%5d | " % w + " | ".join(row))
    print("total | " + " | ".join("%12d" % total(t) for _, t in dumps))
    return True


def cmd_selfcheck(args):
    table, problems = load_dump(args.dump)
    for p in problems:
        print("PROBLEM: %s" % p)
    print("widths %s, %d states" % (sorted(table), total(table)))
    return not problems


def _compare_width(a, b, w, verbose):
    ka, kb = set(a.get(w, {})), set(b.get(w, {}))
    inter = ka & kb
    only_a, only_b = ka - kb, kb - ka
    jac = len(inter) / len(ka | kb) if (ka or kb) else 1.0
    same = sum(1 for k in inter if a[w][k] == b[w][k])
    diffs = collections.Counter(b[w][k] - a[w][k] for k in inter if a[w][k] != b[w][k])
    return dict(
        width=w,
        na=len(ka),
        nb=len(kb),
        inter=len(inter),
        only_a=len(only_a),
        only_b=len(only_b),
        jaccard=jac,
        bound_same=same,
        bound_diffs=diffs,
        only_a_keys=only_a if verbose else None,
        only_b_keys=only_b if verbose else None,
        a_tab=a.get(w, {}),
        b_tab=b.get(w, {}),
    )


def _print_compare(rows, label_a, label_b, max_width=None):
    print(
        "%5s %10s %10s %10s %8s %8s %9s %10s %8s"
        % ("width", "|A|", "|B|", "|A&B|", "|A\\B|", "|B\\A|", "jaccard",
           "bnd_equal", "bnd_ne")
    )
    tot = collections.Counter()
    for r in rows:
        if max_width is not None and r["width"] > max_width:
            continue
        ne = r["inter"] - r["bound_same"]
        print(
            "%5d %10d %10d %10d %8d %8d %9.6f %10d %8d"
            % (r["width"], r["na"], r["nb"], r["inter"], r["only_a"],
               r["only_b"], r["jaccard"], r["bound_same"], ne)
        )
        for k in ("na", "nb", "inter", "only_a", "only_b", "bound_same"):
            tot[k] += r[k]
        tot["ne"] += ne
    union = tot["na"] + tot["nb"] - tot["inter"]
    print(
        "%5s %10d %10d %10d %8d %8d %9.6f %10d %8d"
        % ("TOT", tot["na"], tot["nb"], tot["inter"], tot["only_a"],
           tot["only_b"], (tot["inter"] / union if union else 1.0),
           tot["bound_same"], tot["ne"])
    )
    print("\nA = %s\nB = %s" % (label_a, label_b))
    return tot


def cmd_compare(args):
    a, pa = load_dump(args.a)
    b, pb = load_dump(args.b)
    for p in pa + pb:
        print("PROBLEM: %s" % p)
    widths = sorted(set(a) | set(b))
    rows = [_compare_width(a, b, w, args.verbose) for w in widths]
    tot = _print_compare(rows, args.a, args.b, args.max_width)

    agg = collections.Counter()
    for r in rows:
        if args.max_width is not None and r["width"] > args.max_width:
            continue
        agg.update(r["bound_diffs"])
    if agg:
        print("\nbound differences on shared keys (B - A): %s"
              % dict(sorted(agg.items())))

    # Characterise the non-shared keys: where do they sit in (width, bound,
    # popcount)?  A genuine ambient leak should be structured; search-order
    # noise should not be.
    for tag, side, tab_key in (("A\\B", "only_a", "a_tab"), ("B\\A", "only_b", "b_tab")):
        keys = []
        for r in rows:
            if args.max_width is not None and r["width"] > args.max_width:
                continue
            ks = r["only_a_keys"] if side == "only_a" else r["only_b_keys"]
            if ks:
                keys += [(r["width"], r[tab_key][k], bin(int.from_bytes(k, "little")).count("1")) for k in ks]
        if keys:
            byw = collections.Counter(w for w, _, _ in keys)
            byb = collections.Counter((w, bd) for w, bd, _ in keys)
            print("\n%s: %d keys; by width %s" % (tag, len(keys), dict(sorted(byw.items()))))
            print("   top (width,bound) cells: %s"
                  % sorted(byb.items(), key=lambda kv: -kv[1])[:10])
    return tot["only_a"] == 0 and tot["only_b"] == 0


def cmd_lemma_l(args):
    """The exact Lemma L test.

    HI is a dump at ambient n and level l; LO a dump at ambient n-1, level l.
    Lemma L asserts

        Reach(n, l) restricted to widths <= n-1  ==  Reach(n-1, l)
        and Reach(n, l) has exactly one state of width n.
    """
    hi, ph = load_dump(args.hi)
    lo, pl = load_dump(args.lo)
    for p in ph + pl:
        print("PROBLEM: %s" % p)
    n = args.n if args.n else max(hi)
    print("ambient(HI) taken as n = %d ; LO is the n-1 = %d run\n" % (n, n - 1))

    widths = sorted(set(hi) | set(lo))
    rows = [_compare_width(hi, lo, w, args.verbose) for w in widths if w <= n - 1]
    tot = _print_compare(rows, args.hi + " (restricted to width <= %d)" % (n - 1), args.lo)

    ok_restriction = tot["only_a"] == 0 and tot["only_b"] == 0
    ok_bounds = tot["ne"] == 0

    topw = {w: len(hi.get(w, {})) for w in hi if w >= n}
    print("\nHI states at width >= n = %d : %s" % (n, topw))
    ok_top = topw.get(n, 0) == 1 and all(v == 0 for w, v in topw.items() if w > n)

    # and its bound should be exactly C(n) + level
    if topw.get(n, 0) == 1:
        bnd = hi[n][next(iter(hi[n]))]
        lvl = bnd - free_chain_bound(n)
        print("   the single width-%d state carries lower bound %d = C(%d) + %d"
              % (n, bnd, n, lvl))

    print("\nLemma L clause 1 (restriction equals Reach(n-1,l)) : %s"
          % ("PASS" if ok_restriction else "FAIL"))
    print("Lemma L clause 1' (bounds agree on the restriction)  : %s"
          % ("PASS" if ok_bounds else "FAIL (%d disagreements)" % tot["ne"]))
    print("Lemma L clause 2 (exactly one new width-n state)     : %s"
          % ("PASS" if ok_top else "FAIL"))
    return ok_restriction and ok_top


def _width_arrays(path, w, np):
    """Sorted (keys, bounds) arrays for one width. One width at a time so a
    50 M-state dump never has to be resident all at once."""
    rec = packed_len(w)
    keys, bnds = [], []
    for name in sorted(os.listdir(path)):
        m = GROUP_RE.match(name)
        if not m or int(m.group(1)) != w:
            continue
        b = int(m.group(2))
        a = np.fromfile(os.path.join(path, name), dtype=("S%d" % rec))
        if a.size:
            keys.append(a)
            bnds.append(np.full(a.size, b, dtype=np.uint8))
    if not keys:
        return np.empty(0, dtype=("S%d" % rec)), np.empty(0, dtype=np.uint8)
    k = np.concatenate(keys)
    b = np.concatenate(bnds)
    order = np.argsort(k, kind="stable")
    return k[order], b[order]


def cmd_compare_big(args):
    """Same comparison as `compare`, but width-by-width via numpy so it runs
    on level-5-sized dumps (5e7 states) inside a few GB."""
    import numpy as np

    a_w = {int(GROUP_RE.match(f).group(1))
           for f in os.listdir(args.a) if GROUP_RE.match(f)}
    b_w = {int(GROUP_RE.match(f).group(1))
           for f in os.listdir(args.b) if GROUP_RE.match(f)}
    widths = sorted(a_w | b_w)
    maxw = args.max_width if args.max_width is not None else max(widths)

    print("%5s %12s %12s %12s %9s %9s %10s %12s %8s"
          % ("width", "|A|", "|B|", "|A&B|", "|A\\B|", "|B\\A|", "jaccard",
             "bnd_equal", "bnd_ne"))
    tot = collections.Counter()
    diff_hist = collections.Counter()
    only_cells = {"A\\B": collections.Counter(), "B\\A": collections.Counter()}
    for w in widths:
        ka, ba = _width_arrays(args.a, w, np)
        kb, bb = _width_arrays(args.b, w, np)
        inter, ia, ib = np.intersect1d(ka, kb, assume_unique=True,
                                       return_indices=True)
        n_int = inter.size
        eq = int(np.count_nonzero(ba[ia] == bb[ib])) if n_int else 0
        if n_int:
            d = bb[ib].astype(np.int16) - ba[ia].astype(np.int16)
            for v, c in zip(*np.unique(d[d != 0], return_counts=True)):
                diff_hist[int(v)] += int(c)
        oa = ka.size - n_int
        ob = kb.size - n_int
        union = ka.size + kb.size - n_int
        if w <= maxw:
            print("%5d %12d %12d %12d %9d %9d %10.6f %12d %8d"
                  % (w, ka.size, kb.size, n_int, oa, ob,
                     (n_int / union if union else 1.0), eq, n_int - eq))
            for k in ("na", "nb", "inter", "eq"):
                pass
            tot["na"] += ka.size; tot["nb"] += kb.size
            tot["inter"] += n_int; tot["eq"] += eq
            tot["oa"] += oa; tot["ob"] += ob
        # where do the non-shared keys sit?
        if oa:
            mask = np.isin(ka, inter, assume_unique=True, invert=True)
            for v, c in zip(*np.unique(ba[mask], return_counts=True)):
                only_cells["A\\B"][(w, int(v))] += int(c)
        if ob:
            mask = np.isin(kb, inter, assume_unique=True, invert=True)
            for v, c in zip(*np.unique(bb[mask], return_counts=True)):
                only_cells["B\\A"][(w, int(v))] += int(c)
        del ka, ba, kb, bb, inter
    union = tot["na"] + tot["nb"] - tot["inter"]
    print("%5s %12d %12d %12d %9d %9d %10.6f %12d %8d"
          % ("TOT", tot["na"], tot["nb"], tot["inter"], tot["oa"], tot["ob"],
             (tot["inter"] / union if union else 1.0), tot["eq"],
             tot["inter"] - tot["eq"]))
    print("\nA = %s\nB = %s" % (args.a, args.b))
    if diff_hist:
        top = sorted(diff_hist.items())
        print("\nbound differences on shared keys (B-A): %s"
              % dict(top[:12]) + (" ..." if len(top) > 12 else ""))
    for tag, cells in only_cells.items():
        if cells:
            byw = collections.Counter()
            for (w, _), c in cells.items():
                byw[w] += c
            print("\n%s: %d keys; by width %s" % (tag, sum(cells.values()),
                                                  dict(sorted(byw.items()))))
            print("   top (width,bound) cells: %s"
                  % sorted(cells.items(), key=lambda kv: -kv[1])[:8])
    return tot["oa"] == 0 and tot["ob"] == 0


def cmd_chain(args):
    """Free-chain claim: above the population front every width holds exactly
    one state -- the full cube -- at lower bound C(width) + level."""
    ok = True
    for path in args.dumps:
        table, _ = load_dump(path)
        n = max(table)
        root_bound = max(table[n].values())
        level = root_bound - free_chain_bound(n)
        print("%s : n=%d, root bound %d = C(%d)+%d"
              % (os.path.basename(path.rstrip("/")), n, root_bound, n, level))
        for w in sorted(table, reverse=True):
            cnt = len(table[w])
            bounds = sorted(set(table[w].values()))
            if cnt == 1:
                b = bounds[0]
                exp = free_chain_bound(w) + level
                mark = "OK " if b == exp else "!! "
                if b != exp:
                    ok = False
                print("   %swidth %2d: 1 state, bound %d (C(%d)+%d = %d)"
                      % (mark, w, b, w, level, exp))
            else:
                print("    width %2d: %d states, bounds %d..%d  <- population front"
                      % (w, cnt, bounds[0], bounds[-1]))
                break
        print()
    return ok


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("census"); p.add_argument("dumps", nargs="+"); p.set_defaults(fn=cmd_census)
    p = sub.add_parser("selfcheck"); p.add_argument("dump"); p.set_defaults(fn=cmd_selfcheck)
    p = sub.add_parser("compare")
    p.add_argument("a"); p.add_argument("b")
    p.add_argument("--max-width", type=int, default=None)
    p.add_argument("--verbose", action="store_true", default=True)
    p.set_defaults(fn=cmd_compare)
    p = sub.add_parser("lemma-l")
    p.add_argument("hi"); p.add_argument("lo")
    p.add_argument("--n", type=int, default=None)
    p.add_argument("--verbose", action="store_true", default=True)
    p.set_defaults(fn=cmd_lemma_l)
    p = sub.add_parser("compare-big")
    p.add_argument("a"); p.add_argument("b")
    p.add_argument("--max-width", type=int, default=None)
    p.set_defaults(fn=cmd_compare_big)
    p = sub.add_parser("chain"); p.add_argument("dumps", nargs="+"); p.set_defaults(fn=cmd_chain)

    args = ap.parse_args()
    sys.exit(0 if args.fn(args) else 1)


if __name__ == "__main__":
    main()
