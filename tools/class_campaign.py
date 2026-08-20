#!/usr/bin/env python3
"""
tools/class_campaign.py -- job manifest, runner and signed result ledger for
class-restricted decomposition campaigns against S(13).

Pure stdlib Python 3. No third-party imports, no network access.

DECOMPOSITION IDENTITY (Objective 4 spec, sec.1) and its proof sketch
----------------------------------------------------------------------
For any depth `L` and any `n`, let `X_P` be the canonical output set obtained
by applying prefix `P` (a list of `L` comparators) to the full `n`-cube, and
let `s(X_P)` be the minimum number of comparators that sorts `X_P`. Then

    S(n) = min over all depth-L prefixes P of ( L + s(X_P) ).

(>=) An optimal n-sorter's first `L` comparators form some prefix `P`, and the
remaining comparators of that sorter sort `X_P` (whatever `X_P` turns out to
be); that tail therefore has length >= s(X_P), so the whole sorter has length
>= L + s(X_P) >= min over P of (L + s(X_P)).
(<=) For any prefix `P`, `P` followed by an optimal completion of `X_P` is an
n-sorter of length L + s(X_P); minimising over P gives an upper bound that
matches the lower bound above, hence equality.
Two prefixes with the same canonical `X_P` (same output set up to channel
permutation and complement) have the same `s`, so jobs are deduplicated by
canonical key: each equivalence class of prefixes is exactly one search job.

A **class-restricted** campaign takes the min over only those `P` that pass a
prefix filter (`class_filter.class_prefix_ok` for the C1/C2/C3 shape classes,
or `class_filter.generic_prefix_ok` for the root-split partition). The
root-split partition is exhaustive and disjoint over ALL n-leaf shapes *by
construction* (every shape has exactly one root-split key), so a
`--class-kind root_split --class ALL` campaign computes the identity above
unconditionally. The C1/C2/C3 shape classes are a *conjectured* case split
over the six admissible 13-leaf shapes -- see EPISTEMIC STATUS below.

COMPARATOR ORIENTATION -- the trap (ADDENDUM sec. B, verified independently
in this file's --selftest)
----------------------------------------------------------------------------
`tools/class_filter.py` uses the convention that a comparator `(u, v)` sends
the pairwise MIN to `u` and the pairwise MAX to `v`. The engine's
`OutputSet::apply_comparator([a, b])` (fed by both `-p/--prefix` and
`canon-key`) is the OPPOSITE: channel `a` (the first argument) receives the
pairwise MAXIMUM, channel `b` the MINIMUM. So a class_filter pair `(u, v)`
(u=min, v=max) must be emitted to the engine as `v-u` (canon-key) or the flat
pair `v u` (`-p`). This module does that translation in exactly one place,
`to_engine_pair`, and every engine invocation goes through it. Getting this
backwards silently computes the MIN branch tree instead of the MAX one and
every class verdict is wrong-but-plausible; `--selftest` re-derives the
popcount-384 / repeated-0xbb fact from a live `canon-key` call to catch a
regression here.

TAMPER-EVIDENT LEDGER, NOT A SIGNATURE
----------------------------------------------------------------------------
`ledger.jsonl` is a hash chain: record `i`'s `digest` is a SHA-256 over the
canonical JSON of every other field in record `i`, including `prev_digest`,
which is record `i-1`'s `digest` (or 64 zeros for `seq == 0`). This is
TAMPER-EVIDENT, not a public-key SIGNATURE: it detects accidental corruption
and post-hoc edits by anyone who does not recompute the whole chain from
scratch, and it makes results produced on different machines composable and
auditable (`verify` recomputes every digest and the chain). It does not
prove authorship. If a real signature is wanted later, sign the final
`digest` with an out-of-band key; nothing here needs to change for that.

The ledger file is **append-only**: `run` opens it with `"a"` and this module
contains no repair/compaction mode of any kind. (The `--selftest` tamper-
detection check simulates corruption with a direct rewrite of a throwaway
ledger to prove `verify` catches it; that is test harness code exercising
`verify`, not a capability the tool itself ever uses on a real campaign.)

SAFETY TRIPWIRE (spec sec.7) -- mandatory, reporting-only
----------------------------------------------------------------------------
`run` inspects every job's `composed_value` (`prefix_depth + lower_bound`)
the moment it is computed. If any composed value is <= SAFETY_TRIPWIRE_CEILING
(the only size-related constant in this file; see its definition below for
why and how it is used), `run`:
  * prints a loud, unmissable banner naming the job and its prefix;
  * writes `<campaign>/HALT.txt` with the full ledger record;
  * refuses to launch any further job in that campaign until a human removes
    HALT.txt;
  * exits with code 3, and any subsequent `run` invocation refuses to start
    at all while HALT.txt exists.
Such a candidate must go through **both frozen B1 verifiers** by the
documented procedure (`docs/b1-verification.md`), be reported immediately,
and this line of work stops pending review. This is a *reporting* tripwire
on completed results, never a search target: no part of the search, the
filter, or the job generation ever reads or branches on this number.

EPISTEMIC STATUS (spec sec.8) -- printed by `compose` for every C1/C2/C3
campaign
----------------------------------------------------------------------------
Class campaigns over C1/C2/C3 implement a **conjectured** case split. The
bridge statement (the source chapter's headline result, "E1'") is proved only
for *clean* sorters (no pass-through comparators on any max-path); the
proposed general repair was refuted by an adversarial counterexample
(`docs/kraft-repair-report.md`). Therefore:
  * a completed C1+C2+C3 exhaustion is a **conditional** result;
  * an unconditional conclusion requires either the missing general repair,
    or an all-shapes-coverage campaign
    (`--class-kind root_split --class ALL`, which is unconditional because
    the root-split partition is exhaustive and disjoint by construction, not
    by conjecture).

ENGINE INTERFACE, as actually built (ADDENDUM sec. E -- this overrides the
base spec's guesses about env var names)
----------------------------------------------------------------------------
  * Prefix search: `sortnetopt search N -p v1 u1 -p v2 u2 ...` (flat pairs,
    ENGINE convention: `v`=max receiver, `u`=min receiver). There is no
    `SORTNETOPT_PREFIX` env var.
  * Canonical key, batched: `sortnetopt canon-key N --prefix-file PATH`.
    Output: one `#`-prefixed header line, then one line per input prefix:
    `<prefix>\\t<channels>\\t<popcount>\\t<hex key>` (verbatim order). No
    thread pool, no stats thread, no 10s wall floor.
  * Bound seed: `SORTNETOPT_BOUND_SEED=<checkpoint.bin path>`, produced by a
    `SORTNETOPT_CHECKPOINT_DIR=... SORTNETOPT_CHECKPOINT_INTERVAL_SECS=0` run.
  * Checkpointing: `SORTNETOPT_CHECKPOINT_DIR`, `..._INTERVAL_SECS`,
    `..._RESUME`, `..._FINAL`, `..._KEEP_PREV`.
  * Instrumentation: `SORTNETOPT_INSTRUMENT_JSON=<path>` dumps
    `{schema, channels, result, counters, bound_iterations: [...]}`; each
    `bound_iterations` entry carries the process-relative `elapsed_ms`, which
    is the number this module records as `engine_elapsed_ms` (never the
    wall-clock time of a `search` invocation -- see TIMING HAZARD below).
  * The actual RESULT line this module parses is the unconditional
    `eprintln!("channels = {}, result = {}", ...)` from `instrument::report`
    (always on stderr, regardless of log level) -- NOT the `Just (9,25)`
    string from the base spec's example, which is `snocheck`'s own output
    format, not `sortnetopt search`'s.

ENGINE QUIRK found while building this tool (report this up: not documented
in either spec) -- RUST_LOG and checkpointing
----------------------------------------------------------------------------
With `SORTNETOPT_CHECKPOINT_DIR` set, this engine build silently exits 0 with
ZERO output in well under a second whenever `RUST_LOG` resolves to anything
other than the crate's own fallback level ("info", via env_logger's
`default_filter_or("info")`). Reproduced repeatedly: `RUST_LOG` unset works;
`RUST_LOG=info` works; `RUST_LOG=""`, `"off"`, `"error"`, `"warn"` all fail
silently with no error message on either stream. Plain `search` runs with no
checkpoint dir are unaffected by `RUST_LOG`. Root-causing this inside the
Rust checkpoint/thread-scope code was out of scope for this task. The
workaround applied everywhere in this module (`engine_env`) is to never set
`RUST_LOG` at all, and to make every stdout/stderr parser in this file
tolerant of the resulting `log::info!` noise lines instead (skip lines that
do not match the exact shape expected).

TIMING HAZARD (ADDENDUM sec. F)
----------------------------------------------------------------------------
`search` has a ~10 second process-wall floor (a stats/info thread on a fixed
10s tick that the enclosing `ThreadPool::scope` must join before the process
can exit, even once the actual search has closed its bound interval).
`wall_seconds` in the ledger is the real cost of a job and is recorded
regardless, but `engine_elapsed_ms` (parsed from `SORTNETOPT_INSTRUMENT_JSON`
when available, else from the `iteration ... elapsed_ms ...` table on
stderr) is the number to trust for search cost. `load_at_start`
(`os.getloadavg()[0]`) is recorded with every job because this machine has
been observed at load average 17-80 during this work; no timing comparison
in this campaign's own reports is valid without checking it.

Usage
-----
    class_campaign.py plan    --n N --class KEY --prefix-depth L --campaign DIR
                               [--class-kind shape|root_split] [--engine PATH]
                               [--seed-mode none|shared --seed-limit K]
                               [--env KEY=VALUE ...] [--force]
    class_campaign.py seed    --campaign DIR [--engine PATH]
    class_campaign.py run     --campaign DIR [--shard i/N] [--budget-seconds S]
                               [--max-jobs M] [--timeout-per-job S]
                               [--checkpoint-interval-secs S] [--dry-run]
                               [--certificates on|off] [--engine PATH]
    class_campaign.py status  --campaign DIR
    class_campaign.py compose --campaign DIR
    class_campaign.py verify  --campaign DIR [--engine PATH] [--no-certificates]
    class_campaign.py export  --campaign DIR --out FILE.tar
    class_campaign.py --selftest [--engine PATH]

`--engine` defaults to the `SORTNETOPT_BIN` environment variable.

PER-JOB CERTIFICATES (v2p, docs/certificate-format-v2.md sec.9)
----------------------------------------------------------------------------
With `--certificates on` (the default), `run` gives `search` an output
directory (`<job_dir>/search`) and, for every job that reaches `status ==
done`, runs `prune-all` then `gen-proof -p ... --prefix-root` on it to emit a
v2p prefix-rooted certificate (`<job_dir>/search/proof.bin`), then checks it
with `tools/cert_v2.py prefix-check` against the job's own `(n, prefix,
lower_bound)`. The outcome is recorded in the ledger record's `certificate`
field (see `LEDGER_RESULT_FIELDS`); a certificate failure does NOT discard
the search result (the job's `status` stays `done`), it prints a loud warning
and lets `verify` be the thing that turns it into a hard failure. `verify`
additionally rebuilds the depth-L frontier from the manifest and re-checks
every job's certificate against the file on disk (sec.9.6's three
composition obligations: exhaustiveness of the job set, certificate/job
agreement, and full coverage) before printing a composition verdict -- see
`cmd_verify` and `docs/certificate-format-v2.md` sec.9.6 for the exact
obligations and why a single certificate does not discharge any of them on
its own.
"""

import argparse
import ast
import contextlib
import hashlib
import io
import json
import os
import platform
import re
import resource
import shutil
import signal
import subprocess
import sys
import tarfile
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import class_filter  # noqa: E402  (local module, see sys.path.insert above)


# ===========================================================================
# Constants
# ===========================================================================

SCHEMA_MANIFEST = "class-campaign-manifest-v1"
SCHEMA_JOB = "class-campaign-job-v1"
SCHEMA_RESULT = "class-campaign-result-v1"
SCHEMA_SEED = "class-campaign-seed-v1"

ZERO_DIGEST = "0" * 64

# SAFETY TRIPWIRE (spec sec.7). This is the ONLY size-related constant in
# this file, and it is a REPORTING tripwire evaluated against completed
# results after the fact -- it is never read by the search, the filter, or
# job generation, and no comparator count is ever used as a target, bound,
# feature or stopping condition anywhere else in this module.
SAFETY_TRIPWIRE_CEILING = 45

# The tripwire is armed only from this width up. Below it, the composed value
# is just S(n) (25 at n=9, 29 at n=10) and sits under the ceiling for reasons
# that have nothing to do with a candidate network at the target width. Firing
# on those would be alarm fatigue, and an operator trained to clear HALT.txt
# reflexively is an operator who will clear the real one. Validation campaigns
# at n < 13 cannot produce a target-width candidate, so there is nothing there
# for the tripwire to detect.
TRIPWIRE_ARMED_FROM_N = 13

MANIFEST_HASHED_FIELDS = (
    "schema", "n", "class_key", "class_kind", "prefix_depth",
    "engine", "filter", "env_template", "seed_policy", "job_count",
)

LEDGER_RESULT_FIELDS = (
    "seq", "prev_digest", "campaign_id", "job_id", "prefix", "canon_key",
    "status", "result", "lower_bound", "bound_sequence", "composed_value",
    "wall_seconds", "engine_elapsed_ms", "max_rss_bytes", "load_at_start",
    "machine", "engine_binary_sha256", "seed_sha256", "counters",
    "certificate",
)
# `certificate` is added here (not to SCHEMA_RESULT, which is left
# unchanged) by the PREFIXCERT-V3 per-job-certificate work. Older ledger
# records simply lack the field; `verify_chain` recomputes their digests
# over exactly the fields they were written with (it hashes `dict(r)` minus
# `digest`, not this tuple), so pre-existing records are unaffected and are
# never retro-filled.

EPISTEMIC_STATUS_PARAGRAPH = (
    "EPISTEMIC STATUS: this is a C1/C2/C3 class campaign. The three-way\n"
    "shape case split is a CONJECTURED partition (the bridge statement is\n"
    "proved only for clean sorters; the proposed general repair was refuted,\n"
    "see docs/kraft-repair-report.md). A completed C1+C2+C3 exhaustion is a\n"
    "CONDITIONAL result. An unconditional conclusion needs either the\n"
    "missing general repair or a `--class-kind root_split --class ALL`\n"
    "campaign, which is unconditional by construction."
)

GENERIC_UNCONDITIONAL_NOTE = (
    "NOTE: this is a root-split campaign. The root-split partition is\n"
    "exhaustive and disjoint by construction (every shape has exactly one\n"
    "root-split key) -- a completed `--class ALL` composition is an\n"
    "UNCONDITIONAL result, not a conjectured one; a completed single-key\n"
    "composition is only a lower bound over that one key's shapes unless\n"
    "every key in the partition is also composed."
)


def _build_class_profiles():
    """CLASS_PROFILES: class name -> set of leaf-depth profile tuples, built
    exactly as ADDENDUM sec. A recommends (class_filter.py itself is
    read-only; this module builds the derived map locally)."""
    profiles = {}
    for name, cls in class_filter.CLASS_OF.items():
        profiles.setdefault(cls, set()).add(
            class_filter.PROFILES[class_filter.SHAPE_PROFILE[name]])
    return profiles


CLASS_PROFILES = _build_class_profiles()


# ===========================================================================
# Small utilities
# ===========================================================================


def die(msg, code=1):
    print("class_campaign.py: error: %s" % msg, file=sys.stderr)
    sys.exit(code)


def warn(msg):
    print("class_campaign.py: warning: %s" % msg, file=sys.stderr)


def canonical_json(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_hex(data):
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def machine_info():
    return {
        "os": platform.system(),
        "arch": platform.machine(),
        "cpu_count": os.cpu_count(),
    }


def max_rss_bytes_snapshot():
    """Best-effort, informational only (spec sec.4: 'measured; machine-
    dependent'). `RUSAGE_CHILDREN` is a cumulative high-water mark over ALL
    reaped children of this process, not just the most recent one -- exact
    per-job attribution would need a dedicated child-tracking mechanism this
    tool does not have. Units differ by platform: bytes on Darwin, KiB on
    Linux; normalised to bytes here."""
    ru = resource.getrusage(resource.RUSAGE_CHILDREN)
    if sys.platform == "darwin":
        return int(ru.ru_maxrss)
    return int(ru.ru_maxrss) * 1024


# ===========================================================================
# Comparator orientation (ADDENDUM sec. B)
# ===========================================================================


def to_engine_pair(pair):
    """class_filter convention (u, v): u=min output, v=max output. Engine
    convention `apply_comparator([a, b])`: a=max output, b=min output. So the
    engine argument order is `(v, u)`. See module docstring section B."""
    u, v = pair
    return (v, u)


def engine_token(pair):
    a, b = to_engine_pair(pair)
    return "%d-%d" % (a, b)


def engine_prefix_string(prefix):
    return ",".join(engine_token(pair) for pair in prefix)


def engine_flat_args(prefix):
    """[(u1,v1), (u2,v2), ...] -> ['a1','b1','a2','b2',...] for `-p a b`."""
    out = []
    for pair in prefix:
        a, b = to_engine_pair(tuple(pair))
        out.extend([str(a), str(b)])
    return out


# ===========================================================================
# Engine process plumbing
# ===========================================================================


def resolve_engine(cli_value):
    path = cli_value or os.environ.get("SORTNETOPT_BIN")
    if not path:
        die("no engine binary given: pass --engine PATH or set SORTNETOPT_BIN")
    if not os.path.isfile(path):
        die("engine binary not found: %s" % path)
    return os.path.abspath(path)


def engine_env(overrides=None):
    """Base environment for every engine invocation. Always strips RUST_LOG
    -- see the module docstring's 'ENGINE QUIRK' section for why: with a
    checkpoint dir set, any RUST_LOG value other than the crate's own
    'info' fallback makes the engine exit 0 with zero output almost
    instantly. Leaving RUST_LOG unset reproduces the working case in every
    observed trial."""
    env = dict(os.environ)
    env.pop("RUST_LOG", None)
    if overrides:
        env.update(overrides)
    return env


def cargo_profile_of(engine_path):
    parts = os.path.abspath(engine_path).split(os.sep)
    for p in ("release", "debug"):
        if p in parts:
            return p
    return "unknown"


def patch_stack_info(engine_path):
    """Best-effort INFERENCE, not a measurement: no authoritative build
    manifest exists for these read-only binaries (owned by other agents'
    build trees). This walks up from the binary looking for a sibling
    `diffs/` directory of `*.patch` files and records their names and
    hashes. If none is found, patch_stack is `[]` and that is recorded
    verbatim -- callers must not assume `[]` means 'unpatched'."""
    parts = os.path.abspath(engine_path).split(os.sep)
    for i in range(len(parts) - 1, 0, -1):
        candidate = os.sep.join(parts[:i] + ["diffs"])
        if os.path.isdir(candidate):
            stack = []
            for name in sorted(os.listdir(candidate)):
                if name.endswith(".patch"):
                    stack.append({
                        "name": name,
                        "sha256": sha256_file(os.path.join(candidate, name)),
                    })
            return stack
    return []


def run_canon_key_batch(engine, n, prefixes, workdir):
    """prefixes: list of class_filter-convention prefix tuples (each a tuple
    of (u, v) pairs; the empty tuple is the empty prefix). Returns a list of
    (canon_key_hex, width, popcount), one per input prefix, in input order
    (canon-key preserves line order and echoes back the input prefix string,
    which is cross-checked below as a cheap sanity check)."""
    os.makedirs(workdir, exist_ok=True)
    fd, path = tempfile.mkstemp(prefix="canon-key-in-", suffix=".txt", dir=workdir)
    try:
        with os.fdopen(fd, "w") as fh:
            for prefix in prefixes:
                fh.write(engine_prefix_string(prefix))
                fh.write("\n")
        cmd = [engine, "canon-key", str(n), "--prefix-file", path]
        proc = subprocess.run(cmd, env=engine_env(), capture_output=True,
                               text=True, check=False)
    finally:
        try:
            os.remove(path)
        except OSError:
            pass
    if proc.returncode != 0:
        die("canon-key batch failed (exit %d): %s"
            % (proc.returncode, proc.stderr[-2000:]))
    rows = []
    for line in proc.stdout.splitlines():
        if line.startswith("#"):
            continue
        fields = line.split("\t")
        if len(fields) != 4:
            continue  # stray log::info! noise line (e.g. "options: ..."), skip
        rows.append(fields)
    if len(rows) != len(prefixes):
        die("canon-key batch returned %d rows for %d input prefixes"
            % (len(rows), len(prefixes)))
    out = []
    for prefix, (echo, width_s, popcount_s, key_hex) in zip(prefixes, rows):
        expected = engine_prefix_string(prefix)
        if echo != expected:
            die("canon-key echo mismatch: sent %r, engine echoed %r "
                "(line-order desync?)" % (expected, echo))
        out.append((key_hex, int(width_s), int(popcount_s)))
    return out


_RESULT_RE = re.compile(r"^channels = (\d+), result = (\d+)$")
_TABLE_HEADER = "iteration  lower  upper  elapsed_ms  states  new_states"


def parse_search_stderr_fallback(stderr_text):
    """Fallback parser used only if SORTNETOPT_INSTRUMENT_JSON could not be
    read. Parses the unconditional `instrument::report` eprintln block:
    `channels = N, result = R` and the `iteration ... elapsed_ms ...` table.
    Both are printed on stderr regardless of RUST_LOG / logging config."""
    lower_bound = None
    bound_sequence = []
    engine_elapsed_ms = None
    in_table = False
    for raw in stderr_text.splitlines():
        line = raw.strip()
        m = _RESULT_RE.match(line)
        if m:
            lower_bound = int(m.group(2))
            continue
        if line == _TABLE_HEADER:
            in_table = True
            continue
        if in_table:
            parts = line.split()
            if len(parts) == 6 and all(re.match(r"^-?\d+$", p) for p in parts):
                bound_sequence.append([int(parts[1]), int(parts[2])])
                engine_elapsed_ms = int(parts[3])
                continue
            in_table = False
    return lower_bound, bound_sequence, engine_elapsed_ms, None


def parse_instrument_json(path):
    with open(path) as fh:
        data = json.load(fh)
    iterations = data.get("bound_iterations", [])
    bound_sequence = [list(it["bounds"]) for it in iterations]
    engine_elapsed_ms = iterations[-1]["elapsed_ms"] if iterations else None
    return data.get("result"), bound_sequence, engine_elapsed_ms, data.get("counters")


def _terminate_process_group(proc):
    try:
        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
    except (ProcessLookupError, PermissionError, OSError):
        try:
            proc.terminate()
        except Exception:
            pass


def _kill_process_group(proc):
    try:
        os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
    except (ProcessLookupError, PermissionError, OSError):
        try:
            proc.kill()
        except Exception:
            pass


def run_search_job(engine, n, prefix, ckpt_dir, instrument_path, timeout_seconds,
                    checkpoint_interval_secs, extra_env=None, search_dir=None):
    """Launch one `search` invocation. `prefix` is in class_filter (u, v)
    convention; translated to engine `-p a b` pairs via `to_engine_pair`.
    Honours `--timeout-per-job` with SIGTERM then SIGKILL against the whole
    process group (spec sec.3 'run'). `search_dir`, if given, is passed as
    `search`'s second positional argument (its output/state directory,
    PREFIXCERT-V3) and created if missing; default None reproduces the
    exact command line every caller used before that feature existed."""
    os.makedirs(ckpt_dir, exist_ok=True)
    cmd = [engine, "search", str(n)]
    if search_dir is not None:
        os.makedirs(search_dir, exist_ok=True)
        cmd.append(search_dir)
    flat = engine_flat_args(prefix)
    for i in range(0, len(flat), 2):
        cmd += ["-p", flat[i], flat[i + 1]]

    resume = os.path.isfile(os.path.join(ckpt_dir, "checkpoint.bin"))
    overrides = {
        "SORTNETOPT_CHECKPOINT_DIR": ckpt_dir,
        "SORTNETOPT_CHECKPOINT_INTERVAL_SECS": str(checkpoint_interval_secs),
        "SORTNETOPT_INSTRUMENT_JSON": instrument_path,
    }
    if resume:
        overrides["SORTNETOPT_CHECKPOINT_RESUME"] = "1"
    if extra_env:
        overrides.update(extra_env)
    env = engine_env(overrides)

    load_at_start = os.getloadavg()[0]
    t0 = time.time()
    kwargs = {}
    if hasattr(os, "setsid"):
        kwargs["preexec_fn"] = os.setsid
    proc = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, text=True, **kwargs)
    timed_out = False
    try:
        stdout, stderr = proc.communicate(timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        timed_out = True
        _terminate_process_group(proc)
        try:
            stdout, stderr = proc.communicate(timeout=15)
        except subprocess.TimeoutExpired:
            _kill_process_group(proc)
            stdout, stderr = proc.communicate()
    wall = time.time() - t0
    max_rss = max_rss_bytes_snapshot()

    return {
        "cmd": cmd, "returncode": proc.returncode, "stdout": stdout,
        "stderr": stderr, "wall_seconds": wall, "timed_out": timed_out,
        "load_at_start": load_at_start, "max_rss_bytes": max_rss,
        "resumed": resume,
    }


# ===========================================================================
# Filter resolution
# ===========================================================================


def parse_root_split_key(s):
    value = ast.literal_eval(s)
    a, b = value
    return tuple(sorted((tuple(a), tuple(b))))


def resolve_filter(n, class_kind, class_arg):
    """Returns (filter_fn_or_None, class_key_label, filter1_profiles).
    filter_fn(forest) -> bool; None means 'no filter' (the unconditional
    `root_split` / `ALL` case). filter1_profiles is a sorted list of
    leaf-depth-profile tuples usable as `class_filter.filter1`'s cheap
    pre-check, or None if not applicable."""
    if class_kind == "shape":
        if class_arg not in class_filter.CLASS_MEMBERS:
            die("--class must be one of %s for --class-kind shape"
                % sorted(class_filter.CLASS_MEMBERS))
        if n != 13:
            warn("--class-kind shape --class %s at n=%d: the C1/C2/C3 shape "
                 "classes are defined over the six admissible 13-leaf shapes "
                 "(docs/s13-shape-case-split.md); at n!=13 this filter is "
                 "not meaningful and will likely reject everything" % (class_arg, n))
        profiles = sorted(CLASS_PROFILES.get(class_arg, ()))
        return (lambda forest, _c=class_arg: class_filter.class_prefix_ok(forest, _c),
                class_arg, profiles)
    if class_kind == "root_split":
        if class_arg == "ALL":
            return None, "ALL", None
        key = parse_root_split_key(class_arg)
        classes = class_filter.root_split_classes(n)
        if key not in classes:
            die("root-split key %r is not one of the %d keys at n=%d"
                % (class_arg, len(classes), n))
        profiles = sorted({class_filter.depths(s) for s in classes[key]})
        return (lambda forest, _k=key: class_filter.generic_prefix_ok(forest, _k, n),
                repr(key), profiles)
    die("unknown --class-kind %r (must be shape|root_split)" % class_kind)


def filter1_ok(forest, profiles):
    if not profiles:
        return None
    return class_filter.filter1(forest, profiles)


# ===========================================================================
# Prefix enumeration (spec sec.3 'plan', step 1)
# ===========================================================================


def all_comparator_pairs(n):
    """All ordered (u, v), u != v, in class_filter (min, max) convention.
    n*(n-1) of them, matching the base spec's '156*156' count at n=13."""
    return [(u, v) for u in range(n) for v in range(n) if u != v]


def build_frontier(n, depth, filter_fn, report=None):
    """BFS over depth-`depth` prefixes, filtering after every extension
    (prefix-monotone pruning, spec sec.3 step 1: 'prune at depth 1 before
    extending'). filter_fn=None means no filtering. Returns a list of
    (prefix_tuple, forest) survivors at exactly `depth`. `report`, if given,
    is called as report(depth_reached, raw_count, survivor_count) after each
    extension -- this is the per-depth survival curve ADDENDUM sec. D asks
    `plan` to print."""
    pairs = all_comparator_pairs(n)
    frontier = [((), class_filter.MaxPathForest(n))]
    if depth == 0:
        if report:
            report(0, 1, 1)
        return frontier
    for d in range(1, depth + 1):
        raw_count = len(frontier) * len(pairs)
        next_frontier = []
        for prefix, forest in frontier:
            for pair in pairs:
                nf = forest.copy()
                nf.apply(pair[0], pair[1])
                if filter_fn is None or filter_fn(nf):
                    next_frontier.append((prefix + (pair,), nf))
        frontier = next_frontier
        if report:
            report(d, raw_count, len(frontier))
    return frontier


def build_jobs(n, frontier, filter_fn, filter1_profiles, engine, workdir):
    """Dedup `frontier` by engine-canonical key (spec sec.3 steps 2-3),
    keeping the lexicographically smallest prefix per canonical key as the
    representative. Returns (jobs, raw_survivor_count, deduped_count)."""
    frontier_sorted = sorted(frontier, key=lambda item: item[0])
    prefixes = [item[0] for item in frontier_sorted]
    forests = [item[1] for item in frontier_sorted]
    rows = run_canon_key_batch(engine, n, prefixes, workdir)

    seen = {}
    order = []
    for prefix, forest, (key_hex, width, popcount) in zip(prefixes, forests, rows):
        if width != n:
            die("canon-key returned width=%d for n=%d" % (width, n))
        if key_hex in seen:
            continue  # frontier_sorted is ascending, so the first occurrence
                      # per canon_key is already the lexicographically
                      # smallest representative.
        seen[key_hex] = {
            "prefix": prefix,
            "canon_key": key_hex,
            "canon_width": width,
            "canon_popcount": popcount,
            "filter_verdicts": {
                "filter1": filter1_ok(forest, filter1_profiles),
                "class": True if filter_fn is None else bool(filter_fn(forest)),
            },
        }
        order.append(key_hex)
    jobs = [seen[k] for k in order]
    return jobs, len(prefixes), len(jobs)


def job_record(manifest_sha256, job):
    canonical_prefix_key = canonical_json([list(pair) for pair in job["prefix"]])
    job_id = sha256_hex(manifest_sha256 + canonical_prefix_key)[:16]
    return {
        "schema": SCHEMA_JOB,
        "job_id": job_id,
        "prefix": [list(pair) for pair in job["prefix"]],
        "canon_key": job["canon_key"],
        "canon_width": job["canon_width"],
        "canon_popcount": job["canon_popcount"],
        "filter_verdicts": job["filter_verdicts"],
    }


# ===========================================================================
# Manifest
# ===========================================================================


def manifest_core(manifest):
    return {k: manifest[k] for k in MANIFEST_HASHED_FIELDS}


def build_manifest(n, class_kind, class_key_label, depth, engine_path,
                    env_template, seed_policy, job_count):
    core = {
        "schema": SCHEMA_MANIFEST,
        "n": n,
        "class_key": class_key_label,
        "class_kind": class_kind,
        "prefix_depth": depth,
        "engine": {
            "binary_sha256": sha256_file(engine_path),
            "patch_stack": patch_stack_info(engine_path),
            "cargo_profile": cargo_profile_of(engine_path),
        },
        "filter": {
            "module_path": "tools/class_filter.py",
            "module_sha256": sha256_file(class_filter.__file__),
        },
        "env_template": dict(env_template or {}),
        "seed_policy": seed_policy,
        "job_count": job_count,
    }
    manifest_sha256 = sha256_hex(canonical_json(core))
    manifest = dict(core)
    manifest["manifest_sha256"] = manifest_sha256
    return manifest


def load_manifest(campaign_dir):
    path = os.path.join(campaign_dir, "manifest.json")
    if not os.path.isfile(path):
        die("no manifest.json in %s (run `plan` first)" % campaign_dir)
    with open(path) as fh:
        return json.load(fh)


def load_jobs(campaign_dir):
    jobs = []
    path = os.path.join(campaign_dir, "jobs.jsonl")
    if not os.path.isfile(path):
        die("no jobs.jsonl in %s (run `plan` first)" % campaign_dir)
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if line:
                jobs.append(json.loads(line))
    return jobs


# ===========================================================================
# Ledger (spec sec.4)
# ===========================================================================


def read_ledger(campaign_dir):
    path = os.path.join(campaign_dir, "ledger.jsonl")
    records = []
    if os.path.isfile(path):
        with open(path) as fh:
            for line in fh:
                line = line.rstrip("\n")
                if line:
                    records.append(json.loads(line))
    return records


def last_digest(records):
    return records[-1]["digest"] if records else ZERO_DIGEST


def make_ledger_record(seq, prev_digest, **fields):
    record = {"schema": SCHEMA_RESULT, "seq": seq, "prev_digest": prev_digest}
    record.update(fields)
    missing = [f for f in LEDGER_RESULT_FIELDS if f not in record]
    if missing:
        die("internal error: ledger record missing fields %r" % missing)
    record["digest"] = sha256_hex(canonical_json(record))
    return record


def append_ledger(campaign_dir, record):
    """The ledger is APPEND-ONLY: always opened with 'a'. No function in
    this module ever opens ledger.jsonl with 'w' during normal operation
    (only the --selftest tamper-detection harness does, on a disposable
    throwaway ledger, to prove `verify` catches corruption)."""
    path = os.path.join(campaign_dir, "ledger.jsonl")
    with open(path, "a") as fh:
        fh.write(canonical_json(record))
        fh.write("\n")


def verify_chain(records):
    prev = ZERO_DIGEST
    for idx, r in enumerate(records):
        if r.get("seq") != idx:
            return False, "record %d has seq=%r (expected %d)" % (idx, r.get("seq"), idx)
        if r.get("prev_digest") != prev:
            return False, "record %d (job_id=%s) prev_digest mismatch" % (idx, r.get("job_id"))
        claimed = r.get("digest")
        recompute = dict(r)
        recompute.pop("digest", None)
        actual = sha256_hex(canonical_json(recompute))
        if actual != claimed:
            return False, ("record %d (job_id=%s) digest mismatch: file says %s, "
                            "recomputed %s" % (idx, r.get("job_id"), claimed, actual))
        prev = claimed
    return True, None


# ===========================================================================
# state.json (per-job resumability state, spec sec.3 'run')
# ===========================================================================


def job_dir(campaign_dir, job_id):
    return os.path.join(campaign_dir, "jobs", job_id)


def load_state(campaign_dir, job_id):
    path = os.path.join(job_dir(campaign_dir, job_id), "state.json")
    if not os.path.isfile(path):
        return {"status": "pending", "attempts": 0,
                "engine_checkpoint_dir": None, "last_stdout_offset": 0}
    with open(path) as fh:
        return json.load(fh)


def save_state(campaign_dir, job_id, state):
    d = job_dir(campaign_dir, job_id)
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, "state.json")
    tmp = path + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(state, fh, indent=2, sort_keys=True)
        fh.write("\n")
    os.replace(tmp, path)


def parse_shard_arg(spec):
    try:
        i_s, n_s = spec.split("/")
        i, n = int(i_s), int(n_s)
    except ValueError:
        die("--shard must look like 'i/N', got %r" % spec)
    if n <= 0 or not (0 <= i < n):
        die("--shard %s: need 0 <= i < N and N > 0" % spec)
    return i, n


def jobs_for_shard(jobs, shard):
    """Partition by index modulo N over the stable jobs.jsonl order: every
    job lands in exactly one shard, so shards 0..N-1 are pairwise disjoint
    and their union is the full job list (spec sec.6.4)."""
    if shard is None:
        return list(jobs)
    i, n = shard
    return [job for idx, job in enumerate(jobs) if idx % n == i]


def _trip_safety_tripwire(campaign_dir, job, record):
    banner = (
        "\n" + "!" * 78 + "\n"
        "!! SAFETY TRIPWIRE: composed_value <= %d for job %s\n"
        "!! prefix = %s\n"
        "!! This is a reporting tripwire on RESULTS ONLY -- no part of the\n"
        "!! search, filter or job generation ever used this number as a\n"
        "!! target, bound, feature or stopping condition.\n"
        "!! STOP. Route this candidate through BOTH frozen B1 verifiers via\n"
        "!! the documented procedure (docs/b1-verification.md) before any\n"
        "!! further work on this line of the campaign. Report immediately.\n"
        + "!" * 78 + "\n"
    ) % (SAFETY_TRIPWIRE_CEILING, job["job_id"], job["prefix"])
    print(banner, file=sys.stderr)
    with open(os.path.join(campaign_dir, "HALT.txt"), "w") as fh:
        fh.write(banner)
        fh.write("\n")
        fh.write(canonical_json(record))
        fh.write("\n")


# ===========================================================================
# Per-job certificates (PREFIXCERT-V3, docs/certificate-format-v2.md sec.9)
# ===========================================================================


def cert_v2_path():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "cert_v2.py")


def prefix_check_line(proc):
    """Extract the single OK line cert_v2.py prefix-check prints on stdout
    on success (last non-blank line, in case --quiet still leaves noise
    ahead of it), or the REJECT reason from stderr on failure."""
    if proc.returncode == 0:
        lines = [l for l in proc.stdout.splitlines() if l.strip()]
        return lines[-1] if lines else ""
    return (proc.stderr.strip() or proc.stdout.strip())


def build_certificate(engine, campaign_dir, jdir, n, prefix, lower_bound):
    """PREFIXCERT-V3: after a job's `search` has populated `<jdir>/search`,
    run `prune-all` then `gen-proof -p ... --prefix-root` on it to emit a
    v2p prefix-rooted certificate, then check it with `cert_v2.py
    prefix-check` against the job's own `(n, prefix, lower_bound)`.

    Never raises: every failure mode (prune-all/gen-proof non-zero exit, a
    missing proof.bin, a checker rejection, an unexpected exception) is
    captured in the returned dict's 'ok'/'verdict' fields instead, so a bad
    certificate cannot crash `run` -- the search result itself is real
    evidence and must not be discarded because certificate generation had a
    problem. `verify` is what turns a bad certificate into a hard failure.

    stdout/stderr of every subprocess invoked here is appended to
    `<jdir>/certgen.log`."""
    search_dir = os.path.join(jdir, "search")
    log_path = os.path.join(jdir, "certgen.log")
    proof_path = os.path.join(search_dir, "proof.bin")
    cv2 = cert_v2_path()
    checker_sha = sha256_file(cv2) if os.path.isfile(cv2) else None

    def log(cmd, proc):
        with open(log_path, "a") as fh:
            fh.write("$ %s\n" % " ".join(cmd))
            fh.write(proc.stdout or "")
            fh.write(proc.stderr or "")
            fh.write("\n")

    def fail(verdict):
        return {
            "path": os.path.relpath(proof_path, campaign_dir), "sha256": None,
            "bytes": None, "container": "v2p", "claimed_bound": None,
            "checker": "tools/cert_v2.py prefix-check",
            "checker_sha256": checker_sha, "ok": False, "verdict": verdict,
        }

    try:
        prune_cmd = [engine, "prune-all", search_dir]
        proc = subprocess.run(prune_cmd, env=engine_env(), capture_output=True,
                               text=True, check=False)
        log(prune_cmd, proc)
        if proc.returncode != 0:
            return fail("prune-all failed (exit %d): %s"
                         % (proc.returncode,
                            (proc.stderr.strip() or proc.stdout.strip())[-500:]))

        flat = engine_flat_args(prefix)
        gen_cmd = [engine, "gen-proof", search_dir]
        for i in range(0, len(flat), 2):
            gen_cmd += ["-p", flat[i], flat[i + 1]]
        gen_cmd.append("--prefix-root")
        proc = subprocess.run(gen_cmd, env=engine_env(), capture_output=True,
                               text=True, check=False)
        log(gen_cmd, proc)
        if proc.returncode != 0 or not os.path.isfile(proof_path):
            return fail("gen-proof failed (exit %d) or wrote no proof.bin: %s"
                         % (proc.returncode,
                            (proc.stderr.strip() or proc.stdout.strip())[-500:]))

        proof_sha = sha256_file(proof_path)
        proof_bytes = os.path.getsize(proof_path)

        check_cmd = [sys.executable, cv2, "prefix-check", proof_path,
                     "--expect-channels", str(n),
                     "--expect-prefix", engine_prefix_string(prefix),
                     "--expect-bound", str(lower_bound), "--quiet"]
        proc = subprocess.run(check_cmd, capture_output=True, text=True, check=False)
        log(check_cmd, proc)
        ok = proc.returncode == 0
        verdict = prefix_check_line(proc)
        claimed_bound = None
        if ok:
            m = re.search(r"bound=(-?\d+)", verdict)
            claimed_bound = int(m.group(1)) if m else None

        return {
            "path": os.path.relpath(proof_path, campaign_dir), "sha256": proof_sha,
            "bytes": proof_bytes, "container": "v2p", "claimed_bound": claimed_bound,
            "checker": "tools/cert_v2.py prefix-check", "checker_sha256": checker_sha,
            "ok": ok, "verdict": verdict,
        }
    except Exception as e:  # certificate generation must never crash `run`
        return fail("certificate generation raised %r" % (e,))


# ===========================================================================
# Commands
# ===========================================================================


def cmd_plan(args):
    n = args.n
    depth = args.prefix_depth
    engine_path = resolve_engine(args.engine)

    if os.path.exists(args.campaign) and not args.force:
        die("campaign dir %s already exists; pass --force (ledger.jsonl, if "
            "present, is never touched or overwritten)" % args.campaign)
    os.makedirs(args.campaign, exist_ok=True)
    os.makedirs(os.path.join(args.campaign, "seeds"), exist_ok=True)
    os.makedirs(os.path.join(args.campaign, "jobs"), exist_ok=True)

    filter_fn, class_key_label, filter1_profiles = resolve_filter(
        n, args.class_kind, args.class_)

    print("plan: n=%d class-kind=%s class=%s prefix-depth=%d"
          % (n, args.class_kind, class_key_label, depth))
    print("survival curve (ADDENDUM sec. D):")

    def report(depth_reached, raw_count, survivor_count):
        pct = 100.0 * survivor_count / raw_count if raw_count else 0.0
        print("  depth %2d: raw=%-8d survived=%-8d (%.1f%%)"
              % (depth_reached, raw_count, survivor_count, pct))

    frontier = build_frontier(n, depth, filter_fn, report=report)

    workdir = os.path.join(args.campaign, "_plan_work")
    jobs, raw_survivors, deduped_count = build_jobs(
        n, frontier, filter_fn, filter1_profiles, engine_path, workdir)
    shutil.rmtree(workdir, ignore_errors=True)

    ratio = (raw_survivors / deduped_count) if deduped_count else float("inf")
    print("dedup: %d surviving prefixes -> %d canonical jobs (collapse ratio %.2fx)"
          % (raw_survivors, deduped_count, ratio))

    env_template = dict(args.env or {})
    seed_policy = {
        "mode": args.seed_mode,
        "seed_limit": args.seed_limit if args.seed_mode == "shared" else None,
        "seed_n": n if args.seed_mode == "shared" else None,
    }

    manifest = build_manifest(n, args.class_kind, class_key_label, depth,
                               engine_path, env_template, seed_policy, len(jobs))
    manifest["dedup"] = {
        "raw_survivors": raw_survivors, "deduped_jobs": deduped_count,
        "ratio": ratio,
    }
    # NOTE: 'dedup' is an informational field beyond the spec's manifest
    # field list. It is added AFTER manifest_sha256 is computed over exactly
    # MANIFEST_HASHED_FIELDS, so it plays no part in the campaign identity
    # hash and `verify` ignores it (manifest_core() below).

    with open(os.path.join(args.campaign, "manifest.json"), "w") as fh:
        json.dump(manifest, fh, indent=2, sort_keys=True)
        fh.write("\n")

    with open(os.path.join(args.campaign, "jobs.jsonl"), "w") as fh:
        for job in jobs:
            fh.write(canonical_json(job_record(manifest["manifest_sha256"], job)))
            fh.write("\n")

    ledger_path = os.path.join(args.campaign, "ledger.jsonl")
    if not os.path.exists(ledger_path):
        open(ledger_path, "a").close()

    if args.class_kind == "shape":
        print()
        print(EPISTEMIC_STATUS_PARAGRAPH)
    elif args.class_kind == "root_split":
        print()
        print(GENERIC_UNCONDITIONAL_NOTE)

    print("\nwrote manifest.json (%d jobs) and jobs.jsonl to %s"
          % (len(jobs), args.campaign))
    return 0


def cmd_seed(args):
    manifest = load_manifest(args.campaign)
    seed_policy = manifest["seed_policy"]
    if seed_policy.get("mode") != "shared":
        print("seed_policy.mode = %r; nothing to seed" % seed_policy.get("mode"))
        return 0
    engine_path = resolve_engine(args.engine)
    seed_dir = os.path.join(args.campaign, "seeds")
    ckpt_dir = os.path.join(seed_dir, "checkpoint")
    os.makedirs(ckpt_dir, exist_ok=True)
    env = engine_env({
        "SORTNETOPT_CHECKPOINT_DIR": ckpt_dir,
        "SORTNETOPT_CHECKPOINT_INTERVAL_SECS": "0",
    })
    cmd = [engine_path, "search", str(seed_policy["seed_n"]),
           "--limit", str(seed_policy["seed_limit"])]
    print("seed: running %s" % " ".join(cmd))
    t0 = time.time()
    proc = subprocess.run(cmd, env=env, capture_output=True, text=True)
    wall = time.time() - t0
    ckpt_path = os.path.join(ckpt_dir, "checkpoint.bin")
    if proc.returncode != 0 or not os.path.isfile(ckpt_path):
        die("seed run failed (exit %d) or produced no checkpoint.bin:\n%s"
            % (proc.returncode, proc.stderr[-4000:]))
    seed_sha = sha256_file(ckpt_path)
    info = {
        "schema": SCHEMA_SEED,
        "seed_n": seed_policy["seed_n"],
        "seed_limit": seed_policy["seed_limit"],
        "checkpoint_path": os.path.relpath(ckpt_path, args.campaign),
        "checkpoint_sha256": seed_sha,
        "wall_seconds": round(wall, 3),
        "load_at_start": os.getloadavg()[0],
    }
    with open(os.path.join(seed_dir, "seed.json"), "w") as fh:
        json.dump(info, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print("seed: wrote %s (sha256=%s)" % (ckpt_path, seed_sha))
    return 0


def cmd_run(args):
    campaign_dir = args.campaign
    halt_path = os.path.join(campaign_dir, "HALT.txt")
    if os.path.isfile(halt_path):
        # Deliberately NOT die() (which would sys.exit() the whole process,
        # including a caller like --selftest that reuses cmd_run as a
        # function): callers must see this as an ordinary exit-code-3
        # return. The CLI entry point still turns this into process exit
        # code 3 via `sys.exit(main())`.
        print("class_campaign.py: HALT.txt present: a prior job produced "
              "composed_value <= %d and this campaign is frozen pending "
              "human review. Remove HALT.txt only after following "
              "docs/b1-verification.md." % SAFETY_TRIPWIRE_CEILING, file=sys.stderr)
        return 3

    manifest = load_manifest(campaign_dir)
    jobs = load_jobs(campaign_dir)
    shard = parse_shard_arg(args.shard) if args.shard else None
    shard_jobs = jobs_for_shard(jobs, shard)
    engine_path = resolve_engine(args.engine)
    engine_sha = sha256_file(engine_path)

    seed_sha = None
    seed_path = None
    if manifest.get("seed_policy", {}).get("mode") == "shared":
        seed_info_path = os.path.join(campaign_dir, "seeds", "seed.json")
        if os.path.isfile(seed_info_path):
            with open(seed_info_path) as fh:
                seed_info = json.load(fh)
            seed_sha = seed_info["checkpoint_sha256"]
            seed_path = os.path.join(campaign_dir, seed_info["checkpoint_path"])
        else:
            warn("seed_policy.mode=shared but seeds/seed.json is missing; "
                 "run `seed` first. Continuing without a seed.")

    records = read_ledger(campaign_dir)
    seq = len(records)
    prev_digest = last_digest(records)

    started = time.time()
    launched = 0
    for job in shard_jobs:
        if args.max_jobs is not None and launched >= args.max_jobs:
            print("run: --max-jobs %d reached, stopping" % args.max_jobs)
            break
        if args.budget_seconds is not None and (time.time() - started) >= args.budget_seconds:
            print("run: --budget-seconds %d exceeded, not launching further jobs"
                  % args.budget_seconds)
            break

        state = load_state(campaign_dir, job["job_id"])
        if state.get("status") == "done":
            continue

        if args.dry_run:
            print("dry-run: would launch job %s prefix=%s" % (job["job_id"], job["prefix"]))
            launched += 1
            continue

        jdir = job_dir(campaign_dir, job["job_id"])
        os.makedirs(jdir, exist_ok=True)
        ckpt_dir = os.path.join(jdir, "checkpoint")
        instrument_path = os.path.join(jdir, "instrument.json")

        state["status"] = "running"
        state["attempts"] = state.get("attempts", 0) + 1
        state["engine_checkpoint_dir"] = os.path.relpath(ckpt_dir, campaign_dir)
        save_state(campaign_dir, job["job_id"], state)

        env_overrides = dict(manifest.get("env_template", {}))
        if seed_path:
            env_overrides["SORTNETOPT_BOUND_SEED"] = seed_path

        search_dir = os.path.join(jdir, "search") if args.certificates == "on" else None
        result = run_search_job(
            engine_path, manifest["n"], job["prefix"], ckpt_dir, instrument_path,
            args.timeout_per_job, args.checkpoint_interval_secs,
            extra_env=env_overrides, search_dir=search_dir)

        with open(os.path.join(jdir, "stdout.log"), "a") as fh:
            fh.write(result["stdout"])
        with open(os.path.join(jdir, "stderr.log"), "a") as fh:
            fh.write(result["stderr"])
        state["last_stdout_offset"] = os.path.getsize(os.path.join(jdir, "stdout.log"))

        counters = None
        if os.path.isfile(instrument_path):
            try:
                lower_bound, bound_sequence, engine_elapsed_ms, counters = \
                    parse_instrument_json(instrument_path)
            except (ValueError, OSError, KeyError, IndexError):
                lower_bound, bound_sequence, engine_elapsed_ms, counters = \
                    parse_search_stderr_fallback(result["stderr"])
        else:
            lower_bound, bound_sequence, engine_elapsed_ms, counters = \
                parse_search_stderr_fallback(result["stderr"])

        if result["timed_out"]:
            status = "partial"
        elif result["returncode"] != 0 or lower_bound is None:
            status = "failed"
        else:
            status = "done"

        composed_value = (manifest["prefix_depth"] + lower_bound
                           if status == "done" and lower_bound is not None else None)

        if result["timed_out"]:
            result_str = "<timeout after %ss>" % args.timeout_per_job
        elif lower_bound is not None:
            result_str = "channels = %d, result = %d" % (manifest["n"], lower_bound)
        else:
            tail = (result["stderr"].strip() or result["stdout"].strip())
            result_str = tail[-500:] if tail else "<no output>"

        # PREFIXCERT-V3: certificate generation happens BEFORE the ledger
        # record is built, because 'certificate' is one of LEDGER_RESULT_FIELDS
        # and is therefore hashed into the record's own digest -- there is no
        # after-the-fact way to attach it once the record is on disk.
        certificate = None
        if args.certificates == "on" and status == "done":
            certificate = build_certificate(
                engine_path, campaign_dir, jdir, manifest["n"], job["prefix"],
                lower_bound)

        record = make_ledger_record(
            seq, prev_digest,
            campaign_id=manifest["manifest_sha256"],
            job_id=job["job_id"], prefix=job["prefix"], canon_key=job["canon_key"],
            status=status, result=result_str, lower_bound=lower_bound,
            bound_sequence=bound_sequence, composed_value=composed_value,
            wall_seconds=round(result["wall_seconds"], 3),
            max_rss_bytes=result["max_rss_bytes"], load_at_start=result["load_at_start"],
            machine=machine_info(), engine_binary_sha256=engine_sha,
            seed_sha256=seed_sha, counters=counters,
            engine_elapsed_ms=engine_elapsed_ms, certificate=certificate,
        )
        append_ledger(campaign_dir, record)
        seq += 1
        prev_digest = record["digest"]
        launched += 1

        state["status"] = status
        save_state(campaign_dir, job["job_id"], state)

        print("run: job %s -> status=%s lower_bound=%s composed=%s "
              "wall=%.1fs engine_ms=%s load=%.1f"
              % (job["job_id"], status, lower_bound, composed_value,
                 result["wall_seconds"], engine_elapsed_ms, result["load_at_start"]))

        # The job's search result stands regardless of certificate outcome
        # (status stays "done" above) -- a bad certificate here is reported,
        # not fatal; `verify` is what turns it into a hard failure.
        if certificate is not None and not certificate["ok"]:
            print("run: *** CERTIFICATE FAILED for job %s: %s ***"
                  % (job["job_id"], certificate["verdict"]), file=sys.stderr)

        # The tripwire is armed only at the target width. At small n the
        # composed value is S(n) itself (25 at n=9, 29 at n=10), which is below
        # the ceiling for arithmetic reasons that have nothing to do with a
        # candidate network -- firing there would be pure alarm fatigue and
        # would train an operator to clear HALT.txt reflexively, which is
        # exactly how a real event gets missed. A validation campaign at n<13
        # is not capable of producing a candidate at the target width, so the
        # tripwire has nothing to detect there.
        if status == "done" and composed_value is not None \
                and manifest["n"] >= TRIPWIRE_ARMED_FROM_N \
                and composed_value <= SAFETY_TRIPWIRE_CEILING:
            _trip_safety_tripwire(campaign_dir, job, record)
            return 3

    return 0


def cmd_status(args):
    manifest = load_manifest(args.campaign)
    jobs = load_jobs(args.campaign)
    counts = {"pending": 0, "running": 0, "partial": 0, "failed": 0, "done": 0}
    for job in jobs:
        st = load_state(args.campaign, job["job_id"]).get("status", "pending")
        counts[st] = counts.get(st, 0) + 1
    print("campaign: %s" % args.campaign)
    print("manifest_sha256: %s" % manifest["manifest_sha256"])
    print("n=%d class_kind=%s class_key=%s prefix_depth=%d job_count=%d"
          % (manifest["n"], manifest["class_kind"], manifest["class_key"],
             manifest["prefix_depth"], manifest["job_count"]))
    for k in ("done", "partial", "failed", "running", "pending"):
        print("  %-8s %d" % (k, counts.get(k, 0)))
    records = read_ledger(args.campaign)
    print("ledger records: %d" % len(records))
    if os.path.isfile(os.path.join(args.campaign, "HALT.txt")):
        print("*** HALT.txt present: campaign is frozen pending human review ***")
    return 0


def cmd_compose(args):
    manifest = load_manifest(args.campaign)
    jobs = load_jobs(args.campaign)
    records = read_ledger(args.campaign)
    ok, chain_error = verify_chain(records)

    by_job = {}
    for r in records:
        by_job[r["job_id"]] = r  # last record per job_id wins (retries re-append)

    done = []
    partial = []
    pending = []
    for j in jobs:
        r = by_job.get(j["job_id"])
        if r is None:
            pending.append(j)
        elif r["status"] == "done":
            done.append(r)
        else:
            partial.append(r)

    print("compose: %s" % args.campaign)
    if chain_error:
        print("LEDGER CHAIN INVALID: %s" % chain_error)

    completed_values = [r["composed_value"] for r in done if r["composed_value"] is not None]
    established = bool(jobs) and len(done) == len(jobs)
    if completed_values:
        minimum = min(completed_values)
        best = next(r for r in done if r["composed_value"] == minimum)
        print("min(L + lower_bound) over %d completed job(s) = %d (job %s, prefix %s) "
              "[SEARCH-BACKED -- see `verify` for the certificate-checked value]"
              % (len(completed_values), minimum, best["job_id"], best["prefix"]))
        if established:
            print("STATUS: ESTABLISHED -- all %d job(s) done; this is S(n) restricted "
                  "to this class/prefix depth" % len(jobs))
        else:
            print("STATUS: PROVISIONAL -- %d/%d jobs done, %d partial/failed, %d pending; "
                  "the minimum above is a LOWER BOUND ONLY OVER THE COMPLETED SUBSET"
                  % (len(done), len(jobs), len(partial), len(pending)))
    else:
        print("STATUS: no completed jobs yet")

    print("jobs: done=%d partial/failed=%d pending=%d total=%d"
          % (len(done), len(partial), len(pending), len(jobs)))

    # Certificate-backed composition (docs/certificate-format-v2.md sec.9.6).
    # This is a cheap report over the ledger's own recorded claimed_bound --
    # it does NOT re-run cert_v2.py or recompute the frontier; `verify` is
    # the command that actually re-checks certificates and the composition.
    cert_values = [(manifest["prefix_depth"] + r["certificate"]["claimed_bound"], r)
                   for r in done
                   if r.get("certificate") and r["certificate"].get("ok")
                   and r["certificate"].get("claimed_bound") is not None]
    if cert_values:
        cert_min, cert_best = min(cert_values, key=lambda t: t[0])
        cert_established = len(cert_values) == len(jobs)
        print("certificate-backed composition: min(L + certified bound) over %d "
              "certified job(s) = %d (job %s, prefix %s) [CERTIFICATE-BACKED%s -- "
              "not independently re-verified; run `verify` for that]"
              % (len(cert_values), cert_min, cert_best["job_id"], cert_best["prefix"],
                 "" if cert_established else ", PARTIAL: not every job is certified"))
    else:
        print("certificate-backed composition: no ok job certificates present -- "
              "the minimum above is SEARCH-BACKED ONLY, not certificate-backed")

    if manifest.get("class_kind") == "shape":
        print()
        print(EPISTEMIC_STATUS_PARAGRAPH)
    elif manifest.get("class_kind") == "root_split":
        print()
        print(GENERIC_UNCONDITIONAL_NOTE)

    return 0 if not chain_error else 1


def _job_triple(rec):
    """(job_id, canon_key, prefix-as-a-hashable-tuple), used to compare a
    job.jsonl entry against a job_record() rebuilt from the manifest's own
    parameters (frontier exhaustiveness, docs/certificate-format-v2.md
    sec.9.6 obligation 1)."""
    return (rec["job_id"], rec["canon_key"], tuple(tuple(p) for p in rec["prefix"]))


def _verify_frontier_exhaustiveness(args, manifest, jobs, engine_file):
    """Obligation 1 of sec.9.6: rebuild the depth-L frontier from the
    manifest's own (n, class_kind, class_key, prefix_depth) and check the
    recomputed job set is EXACTLY jobs.jsonl's job set. Returns True (OK),
    False (mismatch -- a real problem), or None (skipped, no engine)."""
    if engine_file is None:
        print("verify: SKIPPED frontier exhaustiveness (no engine given) -- "
              "the composition is NOT verified without it")
        return None

    filter_fn, _class_key_label, filter1_profiles = resolve_filter(
        manifest["n"], manifest["class_kind"], manifest["class_key"])
    frontier = build_frontier(manifest["n"], manifest["prefix_depth"], filter_fn)
    workdir = tempfile.mkdtemp(prefix="class-campaign-verify-")
    try:
        rebuilt_jobs, _raw, _deduped = build_jobs(
            manifest["n"], frontier, filter_fn, filter1_profiles, engine_file, workdir)
    finally:
        shutil.rmtree(workdir, ignore_errors=True)
    rebuilt_records = [job_record(manifest["manifest_sha256"], j) for j in rebuilt_jobs]

    rebuilt_triples = sorted(_job_triple(r) for r in rebuilt_records)
    actual_triples = sorted(_job_triple(j) for j in jobs)
    if rebuilt_triples == actual_triples:
        print("verify: frontier exhaustiveness OK (%d recomputed jobs == "
              "%d jobs.jsonl jobs)" % (len(rebuilt_triples), len(actual_triples)))
        return True

    missing = len(set(actual_triples) - set(rebuilt_triples))
    extra = len(set(rebuilt_triples) - set(actual_triples))
    print("verify: frontier exhaustiveness FAILED (recomputed %d jobs, "
          "jobs.jsonl has %d; missing=%d extra=%d)"
          % (len(rebuilt_triples), len(actual_triples), missing, extra))
    return False


def _verify_certificates_and_composition(args, manifest, jobs, records,
                                          ledger_ok, frontier_ok):
    """Obligations 2 and 3 of sec.9.6 (certificate/job agreement, coverage),
    plus the composition itself (min over certified bounds). `frontier_ok`
    is obligation 1's verdict: True/False/None (skipped, no engine) -- only
    True lets the composition be called VERIFIED, matching sec.9.6's "the
    composing script must check" list. Returns (hard_problems,
    composed_or_None) -- hard_problems is a list of strings to fold into the
    overall verify verdict; warnings are printed but not added to it."""
    by_job = {}
    for r in records:
        by_job[r["job_id"]] = r  # last record per job_id wins (retries re-append)

    any_certs = any((by_job.get(j["job_id"]) or {}).get("certificate") for j in jobs)
    if not any_certs:
        print("verify: no job certificates present -- this campaign predates "
              "per-job certificates; composition is NOT certificate-backed")
        return [], None

    cv2 = cert_v2_path()
    live_checker_sha = sha256_file(cv2) if os.path.isfile(cv2) else None
    print("verify: cert_v2.py on-disk sha256 = %s" % live_checker_sha)

    hard_problems = []
    cert_bounds = {}  # job_id -> certified bound (obligation 2/3 survivors)

    for j in jobs:
        jid = j["job_id"]
        r = by_job.get(jid)
        if r is None or r.get("status") != "done":
            hard_problems.append(
                "job %s: no 'done' ledger record -- coverage obligation "
                "(sec.9.6 #3) not met" % jid)
            print("verify: job %s: no 'done' ledger record" % jid)
            continue

        cert = r.get("certificate")
        if not cert or not cert.get("ok"):
            hard_problems.append(
                "job %s: no certificate or certificate not ok -- coverage "
                "obligation (sec.9.6 #3) not met" % jid)
            print("verify: job %s: no ok certificate on record (%s)"
                  % (jid, (cert or {}).get("verdict")))
            continue

        proof_path = os.path.join(args.campaign, cert["path"])
        if not os.path.isfile(proof_path):
            hard_problems.append(
                "job %s: certificate file missing on disk: %s" % (jid, proof_path))
            print("verify: job %s: certificate file missing on disk: %s"
                  % (jid, proof_path))
            continue

        live_sha = sha256_file(proof_path)
        if live_sha != cert.get("sha256"):
            hard_problems.append(
                "job %s: certificate file sha256 drift: ledger says %s, "
                "on-disk is %s" % (jid, cert.get("sha256"), live_sha))
            print("verify: job %s: CERTIFICATE FILE sha256 DRIFT: recorded=%s "
                  "on-disk=%s" % (jid, cert.get("sha256"), live_sha))
            continue

        check_cmd = [sys.executable, cv2, "prefix-check", proof_path,
                     "--expect-channels", str(manifest["n"]),
                     "--expect-prefix", engine_prefix_string([tuple(p) for p in j["prefix"]]),
                     "--quiet"]
        proc = subprocess.run(check_cmd, capture_output=True, text=True, check=False)
        if proc.returncode != 0:
            reason = prefix_check_line(proc)
            hard_problems.append(
                "job %s: cert_v2.py prefix-check re-run REJECTED: %s" % (jid, reason))
            print("verify: job %s: cert_v2.py prefix-check REJECTED on "
                  "re-verification: %s" % (jid, reason))
            continue

        line = prefix_check_line(proc)
        m = re.search(r"bound=(-?\d+)", line)
        if not m:
            hard_problems.append(
                "job %s: could not parse bound= out of cert_v2.py output: %r"
                % (jid, line))
            print("verify: job %s: could not parse a bound out of %r" % (jid, line))
            continue
        cert_bound = int(m.group(1))
        lower_bound = r.get("lower_bound")

        if lower_bound is not None and cert_bound > lower_bound:
            hard_problems.append(
                "job %s: certificate claims MORE than the search proved -- "
                "contradiction, investigate (cert_bound=%d > lower_bound=%d)"
                % (jid, cert_bound, lower_bound))
            print("verify: job %s: *** certificate claims MORE than the search "
                  "proved (cert_bound=%d > lower_bound=%d) -- contradiction, "
                  "investigate ***" % (jid, cert_bound, lower_bound))
            continue
        elif lower_bound is not None and cert_bound < lower_bound:
            print("verify: job %s: WARNING certified bound %d < search "
                  "lower_bound %d (pruned root replaced by a weaker subsumer); "
                  "sound, but composition uses the certified bound"
                  % (jid, cert_bound, lower_bound))
        else:
            print("verify: job %s: certificate OK, bound=%d" % (jid, cert_bound))

        recorded_checker_sha = cert.get("checker_sha256")
        if live_checker_sha and recorded_checker_sha and live_checker_sha != recorded_checker_sha:
            print("verify: job %s: WARNING cert_v2.py sha256 drift since this "
                  "certificate was generated (recorded=%s on-disk=%s)"
                  % (jid, recorded_checker_sha, live_checker_sha))

        cert_composed = manifest["prefix_depth"] + cert_bound
        if cert_composed != r.get("composed_value"):
            print("verify: job %s: composed-value disagreement: ledger says %s "
                  "(search-backed), certificate-backed value is %d"
                  % (jid, r.get("composed_value"), cert_composed))

        cert_bounds[jid] = cert_bound

    composed = None
    if cert_bounds:
        composed = min(manifest["prefix_depth"] + b for b in cert_bounds.values())
        best_jid = next(jid for jid, b in cert_bounds.items()
                         if manifest["prefix_depth"] + b == composed)
        best_job = next(j for j in jobs if j["job_id"] == best_jid)
        print("verify: composition = min over %d job(s) of (L + certified bound) = %d"
              % (len(cert_bounds), composed))
        print("verify: composition attained by job %s prefix %s"
              % (best_jid, best_job["prefix"]))

    coverage_ok = len(cert_bounds) == len(jobs) and not hard_problems
    if coverage_ok and ledger_ok and frontier_ok is True:
        print("verify: COMPOSITION VERIFIED -- every job certified, frontier "
              "exhaustive, ledger chain intact")
    else:
        reasons = []
        if frontier_ok is None:
            reasons.append("frontier exhaustiveness not checked (no engine given)")
        elif frontier_ok is False:
            reasons.append("frontier exhaustiveness FAILED")
        if hard_problems:
            reasons.append("%d job certificate problem(s)" % len(hard_problems))
        if not ledger_ok:
            reasons.append("ledger chain broken")
        print("verify: COMPOSITION NOT VERIFIED -- %s" % ("; ".join(reasons) or "unknown"))

    return hard_problems, composed


def cmd_verify(args):
    problems = []
    manifest_path = os.path.join(args.campaign, "manifest.json")
    if not os.path.isfile(manifest_path):
        die("no manifest.json in %s" % args.campaign)
    with open(manifest_path) as fh:
        manifest = json.load(fh)
    jobs = load_jobs(args.campaign)

    recomputed = sha256_hex(canonical_json(manifest_core(manifest)))
    if recomputed != manifest.get("manifest_sha256"):
        problems.append("manifest_sha256 mismatch: file says %s, recomputed %s"
                         % (manifest.get("manifest_sha256"), recomputed))
    else:
        print("verify: manifest_sha256 OK")

    module_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "class_filter.py")
    live_sha = sha256_file(module_path)
    recorded_sha = manifest.get("filter", {}).get("module_sha256")
    if live_sha != recorded_sha:
        problems.append("class_filter.py sha256 drift: manifest says %s, on-disk is %s"
                         % (recorded_sha, live_sha))
    else:
        print("verify: class_filter.py sha256 OK (no drift)")

    engine_file = None
    if args.engine or os.environ.get("SORTNETOPT_BIN"):
        engine_file = resolve_engine(args.engine)
        live_engine_sha = sha256_file(engine_file)
        recorded_engine_sha = manifest.get("engine", {}).get("binary_sha256")
        if live_engine_sha != recorded_engine_sha:
            problems.append("engine binary sha256 drift: manifest says %s, %s is %s"
                             % (recorded_engine_sha, engine_file, live_engine_sha))
        else:
            print("verify: engine binary sha256 OK (no drift)")
    else:
        print("verify: no --engine/SORTNETOPT_BIN given, skipping engine binary drift check")

    records = read_ledger(args.campaign)
    ledger_ok, err = verify_chain(records)
    if not ledger_ok:
        problems.append("ledger: %s" % err)
    else:
        print("verify: ledger chain OK (%d records)" % len(records))

    # --- obligation 1 (sec.9.6): frontier exhaustiveness -------------------
    frontier_ok = _verify_frontier_exhaustiveness(args, manifest, jobs, engine_file)
    if frontier_ok is False:
        problems.append("frontier exhaustiveness FAILED: recomputed job set "
                         "!= jobs.jsonl (see composition NOT unconditional)")

    # --- obligations 2/3 (sec.9.6) + composition ----------------------------
    if args.no_certificates:
        print("verify: --no-certificates given, skipping certificate and "
              "composition checks")
    else:
        cert_problems, _composed = _verify_certificates_and_composition(
            args, manifest, jobs, records, ledger_ok, frontier_ok)
        problems.extend(cert_problems)

    if problems:
        print("verify: FAILED")
        for p in problems:
            print("  - %s" % p)
        return 1
    print("verify: OK")
    return 0


def cmd_export(args):
    with tarfile.open(args.out, "w") as tf:
        tf.add(args.campaign, arcname=os.path.basename(os.path.normpath(args.campaign)))
    print("export: wrote %s" % args.out)
    return 0


# ===========================================================================
# --selftest (spec sec.6 + ADDENDUM sec. B)
# ===========================================================================

_CHECKS = []


def _check(name, ok, detail=""):
    """ok=True/False is PASS/FAIL as before; ok=None is SKIP (used when a
    dependency -- e.g. cert_v2.py prefix-check -- isn't available yet) and
    is reported but does not count toward the pass/fail summary."""
    normalized = None if ok is None else bool(ok)
    _CHECKS.append((name, normalized, detail))
    return normalized


def _hdr(title):
    print()
    print("=" * 78)
    print(title)
    print("=" * 78)


def _selftest_orientation(engine, tmp_root):
    _hdr("CHECK 0 -- comparator orientation trap (ADDENDUM sec. B)")
    workdir = os.path.join(tmp_root, "orientation")
    pair = (0, 1)  # class_filter convention: u=0 (min output), v=1 (max output)
    token = engine_token(pair)
    ok_token = _check("0a  to_engine_pair((0,1)) == (1,0) and engine_token == '1-0'",
                       to_engine_pair(pair) == (1, 0) and token == "1-0",
                       "to_engine_pair=%r token=%r" % (to_engine_pair(pair), token))
    rows = run_canon_key_batch(engine, 9, [(pair,)], workdir)
    key_hex, width, popcount = rows[0]
    expected_key = "bb" * ((1 << width) // 8)
    ok_probe = _check(
        "0b  live canon-key(9, prefix='0-1' engine-side) reproduces popcount=384 "
        "and key=repeated 0xbb (ADDENDUM sec. B's independent verification)",
        popcount == 384 and key_hex == expected_key and width == 9,
        "width=%d popcount=%d key[:16]=%s" % (width, popcount, key_hex[:16]))
    return ok_token and ok_probe


def _selftest_exhaustiveness(engine, tmp_root):
    _hdr("CHECK 1 -- root_split ALL vs per-key union, n=9 depth=1 (spec sec.6.1)")
    n, depth = 9, 1
    workdir = os.path.join(tmp_root, "exhaust")
    filter_all, _, _ = resolve_filter(n, "root_split", "ALL")
    frontier_all = build_frontier(n, depth, filter_all)
    jobs_all, raw_all, deduped_all = build_jobs(n, frontier_all, filter_all, None, engine, workdir)
    distinct = len({j["canon_key"] for j in jobs_all})
    _check("1a  all canon keys distinct after dedup", distinct == len(jobs_all),
           "distinct=%d jobs=%d (raw survivors=%d)" % (distinct, len(jobs_all), raw_all))

    all_prefixes = {p for p, _ in frontier_all}
    union_prefixes = set()
    keys = class_filter.root_split_classes(n)
    for key in keys:
        filter_key, _, _ = resolve_filter(n, "root_split", repr(key))
        frontier_key = build_frontier(n, depth, filter_key)
        union_prefixes |= {p for p, _ in frontier_key}
    _check("1b  union of per-root-split-key survivors == unfiltered survivor set "
           "(exhaustiveness, %d keys)" % len(keys),
           union_prefixes == all_prefixes,
           "missing=%d extra=%d" % (len(all_prefixes - union_prefixes),
                                     len(union_prefixes - all_prefixes)))


def _selftest_ledger_tamper(tmp_root):
    _hdr("CHECK 2 -- ledger tamper-evidence (spec sec.6.2)")
    campaign_dir = os.path.join(tmp_root, "tamper")
    os.makedirs(campaign_dir, exist_ok=True)
    seq, prev = 0, ZERO_DIGEST
    for i in range(3):
        record = make_ledger_record(
            seq, prev, campaign_id="selftest", job_id="job%d" % i, prefix=[[0, 1]],
            canon_key="00" * 8, status="done", result="dummy", lower_bound=i,
            bound_sequence=[[0, i]], composed_value=i, wall_seconds=0.0,
            max_rss_bytes=0, load_at_start=0.0, machine=machine_info(),
            engine_binary_sha256="0" * 64, seed_sha256=None, counters=None,
            engine_elapsed_ms=0, certificate=None)
        append_ledger(campaign_dir, record)
        seq += 1
        prev = record["digest"]

    ok1, err1 = verify_chain(read_ledger(campaign_dir))
    _check("2a  fresh 3-record ledger verifies clean", ok1, err1 or "")

    # Simulate corruption by directly rewriting the file -- this is test
    # harness code proving `verify` detects tampering, NOT something the
    # tool itself ever does to a real ledger (see module docstring).
    ledger_path = os.path.join(campaign_dir, "ledger.jsonl")
    with open(ledger_path) as fh:
        lines = fh.readlines()
    victim = 1
    tampered = lines[victim].replace('"job1"', '"job1x"')
    if tampered == lines[victim]:
        die("selftest internal error: tamper substitution did not change record %d" % victim)
    lines[victim] = tampered
    with open(ledger_path, "w") as fh:
        fh.writelines(lines)

    ok2, err2 = verify_chain(read_ledger(campaign_dir))
    names_record = (err2 is not None) and ("record %d" % victim) in err2
    _check("2b  a single mutated field in a middle record makes verify_chain fail "
           "and name that record", (not ok2) and names_record, err2 or "")


def _selftest_shard_disjointness(engine, tmp_root):
    _hdr("CHECK 4 -- shard disjointness (spec sec.6.4)")
    n, depth = 9, 2
    workdir = os.path.join(tmp_root, "shard")
    filter_all, _, _ = resolve_filter(n, "root_split", "ALL")
    frontier = build_frontier(n, depth, filter_all)
    raw_jobs, _, _ = build_jobs(n, frontier, filter_all, None, engine, workdir)
    fake_manifest_sha = sha256_hex("selftest-shard-disjointness")
    jobs = [job_record(fake_manifest_sha, j) for j in raw_jobs]
    shards = [jobs_for_shard(jobs, (i, 3)) for i in range(3)]
    union_ids = set()
    overlap = False
    for s in shards:
        ids = {j["job_id"] for j in s}
        if union_ids & ids:
            overlap = True
        union_ids |= ids
    all_ids = {j["job_id"] for j in jobs}
    _check("4a  shard 0/3, 1/3, 2/3 are pairwise disjoint (%d jobs total)" % len(jobs),
           not overlap)
    _check("4b  shard 0/3 U 1/3 U 2/3 == full job set", union_ids == all_ids,
           "missing=%d" % len(all_ids - union_ids))


def _selftest_resumability(engine, tmp_root):
    _hdr("CHECK 3 -- resumability via --max-jobs 1 (spec sec.6.3)")
    campaign_dir = os.path.join(tmp_root, "resume")
    os.makedirs(os.path.join(campaign_dir, "seeds"), exist_ok=True)
    os.makedirs(os.path.join(campaign_dir, "jobs"), exist_ok=True)
    open(os.path.join(campaign_dir, "ledger.jsonl"), "a").close()

    n = 6
    workdir = os.path.join(tmp_root, "resume_work")

    # Get two genuinely different short (depth-2) canonical prefixes first
    # (n=6 depth=2 ALL was measured to collapse 900 raw prefixes to 3
    # canonical jobs -- see the campaign report). Then pad each with its own
    # trailing comparator repeated: `apply_comparator` is a no-op once a
    # channel pair is already in order (`docs/sortnetopt-internals.md`
    # sec.1.3 step 5, "returns false for redundant comparators"), so padding
    # cannot change X_P -- it only inflates the recorded prefix_depth.
    short_frontier = build_frontier(n, 2, None)
    short_jobs, _, _ = build_jobs(n, short_frontier, None, None, engine, workdir)
    if len(short_jobs) < 2:
        _check("3-setup  found >=2 canonically distinct depth-2 prefixes at n=%d" % n,
               False, "got %d" % len(short_jobs))
        return

    # depth is deliberately >> SAFETY_TRIPWIRE_CEILING so composed_value =
    # depth + lower_bound(X_P) cannot possibly trip the safety tripwire here
    # -- this check is testing resumability, not the tripwire (CHECK 5).
    depth = SAFETY_TRIPWIRE_CEILING + 5
    raw_prefixes = []
    for j in short_jobs[:2]:
        base = j["prefix"]
        pad_pair = base[-1]
        raw_prefixes.append(base + (pad_pair,) * (depth - len(base)))

    rows = run_canon_key_batch(engine, n, raw_prefixes, workdir)
    if rows[0][0] == rows[1][0]:
        _check("3-setup  the two probe prefixes are canonically distinct", False,
               "both collapsed to canon_key %s" % rows[0][0])
        return
    _check("3-setup  the two probe prefixes are canonically distinct after padding "
           "to depth=%d" % depth, True)

    manifest = build_manifest(n, "root_split", "ALL", depth, engine,
                               {}, {"mode": "none", "seed_limit": None, "seed_n": None}, 2)
    with open(os.path.join(campaign_dir, "manifest.json"), "w") as fh:
        json.dump(manifest, fh, indent=2, sort_keys=True)
        fh.write("\n")

    jobs = []
    for prefix, (key_hex, width, popcount) in zip(raw_prefixes, rows):
        raw = {"prefix": prefix, "canon_key": key_hex, "canon_width": width,
               "canon_popcount": popcount, "filter_verdicts": {"filter1": None, "class": True}}
        jobs.append(job_record(manifest["manifest_sha256"], raw))
    with open(os.path.join(campaign_dir, "jobs.jsonl"), "w") as fh:
        for j in jobs:
            fh.write(canonical_json(j))
            fh.write("\n")

    # certificates=off: this check is testing resumability, not certificate
    # generation (that has its own selftest, CHECK 6) -- keeping certificates
    # off here matches this check's pre-existing behaviour and runtime.
    common = dict(campaign=campaign_dir, engine=engine, shard=None,
                  budget_seconds=None, timeout_per_job=120,
                  checkpoint_interval_secs=0, dry_run=False, certificates="off")
    cmd_run(argparse.Namespace(max_jobs=1, **common))

    st0 = load_state(campaign_dir, jobs[0]["job_id"])
    st1 = load_state(campaign_dir, jobs[1]["job_id"])
    _check("3a  after --max-jobs 1: job 1 is done, job 2 is still not done",
           st0.get("status") == "done" and st1.get("status") != "done",
           "job0=%s job1=%s" % (st0.get("status"), st1.get("status")))
    records1 = read_ledger(campaign_dir)
    _check("3b  ledger has exactly 1 record after the interrupted run",
           len(records1) == 1, "got %d" % len(records1))

    cmd_run(argparse.Namespace(max_jobs=None, **common))

    st0b = load_state(campaign_dir, jobs[0]["job_id"])
    st1b = load_state(campaign_dir, jobs[1]["job_id"])
    _check("3c  job 1 was skipped (attempts still 1, not re-run) and job 2 executed "
           "on rerun", st0b.get("attempts") == 1 and st1b.get("status") == "done",
           "job0.attempts=%s job1.status=%s" % (st0b.get("attempts"), st1b.get("status")))

    records2 = read_ledger(campaign_dir)
    ok_chain, err_chain = verify_chain(records2)
    _check("3d  ledger has exactly 2 records with a valid hash chain after rerun",
           len(records2) == 2 and ok_chain,
           err_chain or ("count=%d" % len(records2)))


def _cert_v2_supports_prefix_check(cv2):
    """Best-effort probe: does this cert_v2.py build have a working
    'prefix-check' subcommand? Used only to decide whether CHECK 6 can run
    or must SKIP -- the checker is owned by another agent and may not have
    landed yet."""
    if not os.path.isfile(cv2):
        return False
    proc = subprocess.run([sys.executable, cv2, "prefix-check", "--help"],
                           capture_output=True, text=True, check=False)
    return proc.returncode == 0


def _selftest_certificate_tamper(engine, tmp_root):
    _hdr("CHECK 6 -- per-job certificate tamper-evidence "
         "(docs/certificate-format-v2.md sec.9)")
    cv2 = cert_v2_path()
    if not _cert_v2_supports_prefix_check(cv2):
        _check("6-setup  tools/cert_v2.py has a working 'prefix-check' subcommand",
               None, "SKIP: cert_v2.py prefix-check is not available yet "
                     "(owned by another agent) -- not passing vacuously, "
                     "marking SKIP")
        return

    campaign_dir = os.path.join(tmp_root, "cert-tamper")
    os.makedirs(os.path.join(campaign_dir, "seeds"), exist_ok=True)
    os.makedirs(os.path.join(campaign_dir, "jobs"), exist_ok=True)
    open(os.path.join(campaign_dir, "ledger.jsonl"), "a").close()

    n, depth = 6, 1
    workdir = os.path.join(tmp_root, "cert_tamper_work")
    filter_all, _, _ = resolve_filter(n, "root_split", "ALL")
    frontier = build_frontier(n, depth, filter_all)
    raw_jobs, _, _ = build_jobs(n, frontier, filter_all, None, engine, workdir)
    if not raw_jobs:
        _check("6-setup  found >=1 canonical depth-1 prefix at n=%d" % n, False, "got 0")
        return

    manifest = build_manifest(n, "root_split", "ALL", depth, engine, {},
                               {"mode": "none", "seed_limit": None, "seed_n": None}, 1)
    with open(os.path.join(campaign_dir, "manifest.json"), "w") as fh:
        json.dump(manifest, fh, indent=2, sort_keys=True)
        fh.write("\n")

    job = job_record(manifest["manifest_sha256"], raw_jobs[0])
    with open(os.path.join(campaign_dir, "jobs.jsonl"), "w") as fh:
        fh.write(canonical_json(job))
        fh.write("\n")

    common = dict(campaign=campaign_dir, engine=engine, shard=None,
                  budget_seconds=None, timeout_per_job=120,
                  checkpoint_interval_secs=0, dry_run=False, certificates="on")
    cmd_run(argparse.Namespace(max_jobs=None, **common))

    records = read_ledger(campaign_dir)
    cert_ok = bool(records) and records[0].get("status") == "done" \
        and records[0].get("certificate") is not None \
        and records[0]["certificate"].get("ok") is True
    _check("6a  run produced 1 ledger record with status=done and an ok certificate",
           cert_ok, canonical_json(records[0].get("certificate")) if records else "no records")
    if not cert_ok:
        return

    proof_rel = records[0]["certificate"]["path"]
    proof_path = os.path.join(campaign_dir, proof_rel)
    with open(proof_path, "rb") as fh:
        original = bytearray(fh.read())

    # Flip a byte inside the payload region, just ahead of the trailer --
    # this corrupts step-table/payload content covered by the file's own
    # `payload_sha256` (docs/certificate-format-v2.md sec.3.5), independent
    # of anything class_campaign.py itself records.
    tampered = bytearray(original)
    flip_off = len(tampered) - 41
    tampered[flip_off] ^= 0xFF
    with open(proof_path, "wb") as fh:
        fh.write(bytes(tampered))

    # --- 6b: the sha256-drift check alone must catch this -----------------
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = cmd_verify(argparse.Namespace(campaign=campaign_dir, engine=engine,
                                            no_certificates=False))
    out = buf.getvalue()
    drift_line = next((l for l in out.splitlines() if "sha256 DRIFT" in l), "")
    _check("6b  verify FAILS once the certificate file is byte-flipped "
           "(sha256 drift, ledger sha256 untouched)",
           rc != 0 and "verify: FAILED" in out, "rc=%r" % rc)
    _check("6c  verify's own output names the sha256 drift specifically",
           bool(drift_line), drift_line or "(no drift line found)")

    # --- 6d: now hide the drift from OUR check by forging the ledger's own
    # recorded sha256 to match the tampered file, and recomputing that one
    # record's digest so the ledger CHAIN itself still verifies clean. This
    # isolates the second, independent detection layer: cert_v2.py's own
    # internal file digest (sec.3.5's payload_sha256), which the tampered
    # bytes still violate regardless of what class_campaign.py's ledger
    # claims about the file.
    ledger_path = os.path.join(campaign_dir, "ledger.jsonl")
    with open(ledger_path) as fh:
        rec = json.loads(fh.readline())
    rec["certificate"]["sha256"] = sha256_file(proof_path)
    recompute = dict(rec)
    recompute.pop("digest", None)
    rec["digest"] = sha256_hex(canonical_json(recompute))
    with open(ledger_path, "w") as fh:
        fh.write(canonical_json(rec))
        fh.write("\n")

    ok_chain, err_chain = verify_chain(read_ledger(campaign_dir))
    _check("6-setup  forged ledger sha256 still yields a valid hash chain "
           "(isolating the file-integrity check from the chain check)",
           ok_chain, err_chain or "")

    buf2 = io.StringIO()
    with contextlib.redirect_stdout(buf2):
        rc2 = cmd_verify(argparse.Namespace(campaign=campaign_dir, engine=engine,
                                             no_certificates=False))
    out2 = buf2.getvalue()
    reject_line = next((l for l in out2.splitlines() if "REJECTED" in l), "")
    _check("6d  verify STILL FAILS with the ledger sha256 forged to match the "
           "tampered file (caught by cert_v2.py's own re-verification, not "
           "our sha256 drift check)",
           rc2 != 0 and "verify: FAILED" in out2, "rc=%r" % rc2)
    _check("6e  the rejection reason is cert_v2.py's own integrity check "
           "(payload sha256 mismatch), not a sha256-drift message",
           "payload sha256 mismatch" in out2 and "sha256 DRIFT" not in out2,
           reject_line or "(no REJECTED line found)")


def run_selftest(args):
    engine = resolve_engine(args.engine)
    tmp_root = tempfile.mkdtemp(prefix="class-campaign-selftest-")
    _CHECKS[:] = []
    try:
        _selftest_orientation(engine, tmp_root)
        _selftest_exhaustiveness(engine, tmp_root)
        _selftest_ledger_tamper(tmp_root)
        _selftest_shard_disjointness(engine, tmp_root)
        _selftest_resumability(engine, tmp_root)
        _selftest_certificate_tamper(engine, tmp_root)
    finally:
        shutil.rmtree(tmp_root, ignore_errors=True)

    _hdr("SUMMARY")
    failed = [c for c in _CHECKS if c[1] is False]
    skipped = [c for c in _CHECKS if c[1] is None]
    for name, ok, detail in _CHECKS:
        status = "SKIP" if ok is None else ("PASS" if ok else "FAIL")
        print("  [%s] %s%s" % (status, name, ("   -- " + detail) if detail else ""))
    if failed:
        print("\n  %d of %d checks FAILED (%d skipped)."
              % (len(failed), len(_CHECKS), len(skipped)))
        return 1
    if skipped:
        print("\n  All %d non-skipped checks passed (%d SKIPPED, %d total)."
              % (len(_CHECKS) - len(skipped), len(skipped), len(_CHECKS)))
    else:
        print("\n  All %d checks passed." % len(_CHECKS))
    return 0


# ===========================================================================
# CLI
# ===========================================================================


def _env_kv(value):
    if "=" not in value:
        raise argparse.ArgumentTypeError("--env expects KEY=VALUE, got %r" % value)
    k, v = value.split("=", 1)
    return k, v


def build_arg_parser():
    ap = argparse.ArgumentParser(
        prog="class_campaign.py",
        description="Job manifest, runner and signed result ledger for "
                     "class-restricted S(13) decomposition campaigns.")
    ap.add_argument("--selftest", action="store_true", help="run all self-checks and exit")
    ap.add_argument("--engine", default=None,
                     help="path to the sortnetopt binary (default: $SORTNETOPT_BIN); "
                          "used by --selftest")
    sub = ap.add_subparsers(dest="command")

    p = sub.add_parser("plan")
    p.add_argument("--n", type=int, required=True)
    p.add_argument("--class", dest="class_", required=True,
                    help="'ALL' or a root-split key literal for --class-kind "
                         "root_split; 'C1'/'C2'/'C3' for --class-kind shape")
    p.add_argument("--prefix-depth", type=int, required=True)
    p.add_argument("--campaign", required=True)
    p.add_argument("--class-kind", choices=["shape", "root_split"], default="root_split")
    p.add_argument("--engine", default=None)
    p.add_argument("--seed-mode", choices=["none", "shared"], default="none")
    p.add_argument("--seed-limit", type=int, default=None)
    p.add_argument("--env", action="append", type=_env_kv, default=[], dest="env_kv")
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=lambda a: cmd_plan(_finalize_plan_args(a)))

    p = sub.add_parser("seed")
    p.add_argument("--campaign", required=True)
    p.add_argument("--engine", default=None)
    p.set_defaults(func=cmd_seed)

    p = sub.add_parser("run")
    p.add_argument("--campaign", required=True)
    p.add_argument("--shard", default=None, help="i/N")
    p.add_argument("--budget-seconds", type=float, default=None)
    p.add_argument("--max-jobs", type=int, default=None)
    p.add_argument("--timeout-per-job", type=float, default=None)
    p.add_argument("--checkpoint-interval-secs", type=int, default=60,
                    help="periodic engine checkpoint interval; 0 = final "
                         "write only on clean exit (default: 60)")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--engine", default=None)
    p.add_argument("--certificates", choices=["on", "off"], default="on",
                    help="emit and check a per-job v2p prefix certificate "
                         "for every job that reaches status=done "
                         "(docs/certificate-format-v2.md sec.9; default: on)")
    p.set_defaults(func=cmd_run)

    p = sub.add_parser("status")
    p.add_argument("--campaign", required=True)
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("compose")
    p.add_argument("--campaign", required=True)
    p.set_defaults(func=cmd_compose)

    p = sub.add_parser("verify")
    p.add_argument("--campaign", required=True)
    p.add_argument("--engine", default=None)
    p.add_argument("--no-certificates", action="store_true",
                    help="skip per-job certificate re-checking and the "
                         "composition verdict (for a legacy campaign that "
                         "predates certificates)")
    p.set_defaults(func=cmd_verify)

    p = sub.add_parser("export")
    p.add_argument("--campaign", required=True)
    p.add_argument("--out", required=True)
    p.set_defaults(func=cmd_export)

    return ap


def _finalize_plan_args(args):
    args.env = dict(args.env_kv)
    return args


def main(argv=None):
    ap = build_arg_parser()
    args = ap.parse_args(argv)
    if args.selftest:
        return run_selftest(args)
    if not getattr(args, "command", None):
        ap.print_help()
        return 1
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
