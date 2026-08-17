#!/usr/bin/env python3
"""Sample the CPU utilisation of a child process at a fixed cadence.

Tier-2b (thread-pool descheduling) measurement harness. Launches a command,
samples `ps -o cputime,rss` for its pid every `--interval` seconds, and writes
a CSV of (elapsed_s, cpu_s, util_pct, rss_kb). The child's stdout/stderr go to
the files given by --log / --err so the `bounds:` / `states:` timeline can be
aligned with the utilisation curve afterwards.

NOTE: macOS `ps -o %cpu` is a *lifetime average* (total CPU time / elapsed),
not an instantaneous rate, so it ramps monotonically and is useless for a
utilisation curve. This sampler therefore reads cumulative `cputime` and
differentiates it: `util_pct = 100 * dcpu / dwall`, i.e. 900 means nine cores
busy. `cputime` has 10 ms resolution, so at the default 100 ms cadence one
quantum is 10 percentage points of a single core (1 % of a 10-core box).

Usage:
  python3 tools/cpu_sampler.py --out cpu.csv --log run.log --err run.err \
      -- env FOO=1 ./sortnetopt -m search 10 /path/_search_10
"""
import argparse
import subprocess
import sys
import time


def parse_cputime(text: str) -> float:
    """`ps -o cputime` prints [DD-]HH:MM:SS.cc or MM:SS.cc (minutes may exceed 60)."""
    days = 0.0
    if "-" in text:
        d, text = text.split("-", 1)
        days = float(d)
    parts = text.split(":")
    total = 0.0
    for p in parts:
        total = total * 60.0 + float(p)
    return total + days * 86400.0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--log", required=True)
    ap.add_argument("--err", required=True)
    ap.add_argument("--interval", type=float, default=0.1)
    ap.add_argument("cmd", nargs=argparse.REMAINDER)
    args = ap.parse_args()

    cmd = args.cmd
    if cmd and cmd[0] == "--":
        cmd = cmd[1:]
    if not cmd:
        print("no command given", file=sys.stderr)
        return 2

    # Rows are written and flushed as they are taken, not buffered to the end:
    # a multi-hour n=11 run that is deliberately SIGKILLed must still leave a
    # usable utilisation trace.
    t0 = time.monotonic()
    count = 0
    with open(args.log, "wb") as log, open(args.err, "wb") as err, \
            open(args.out, "w") as f:
        f.write("elapsed_s,cpu_s,util_pct,rss_kb\n")
        f.flush()
        proc = subprocess.Popen(cmd, stdout=log, stderr=err)
        prev = None
        while proc.poll() is None:
            t = time.monotonic() - t0
            try:
                out = subprocess.run(
                    ["ps", "-o", "cputime=,rss=", "-p", str(proc.pid)],
                    capture_output=True, text=True, timeout=2,
                ).stdout.strip()
            except subprocess.TimeoutExpired:
                out = ""
            if out:
                parts = out.split()
                if len(parts) >= 2:
                    cpu, rss = parse_cputime(parts[0]), parts[1]
                    if prev is None or t <= prev[0]:
                        util = ""
                    else:
                        util = "%.1f" % (100.0 * (cpu - prev[1]) / (t - prev[0]))
                    f.write("%.3f,%.2f,%s,%s\n" % (t, cpu, util, rss))
                    f.flush()
                    prev = (t, cpu)
                    count += 1
            time.sleep(args.interval)
        rc = proc.wait()

    wall = time.monotonic() - t0
    print("exit=%d wall=%.3f samples=%d" % (rc, wall, count))
    return rc


if __name__ == "__main__":
    sys.exit(main())
