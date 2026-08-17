# Addendum: n=13 --limit 43 probe (killed at cap breach; data salvaged)

Date: 2026-08-18, ~00:51-01:00. Run by the orchestrating session on the
M4 per the limits report's recommendation #5.

## Defect disclosure

The probe's inline watchdog was defective: it monitored the child's RSS
but targeted `kill -9` at the `/usr/bin/time` wrapper PID rather than
the search PID, so neither the 8 GB RSS cap nor the 30-minute cap could
actually stop the search. The (still-running) limits campaign agent
detected this, attempted to enforce the probe's own stated caps, was
correctly denied by the permission system, and instead attached a
non-destructive monitor (`watchdog.csv`) and escalated. The session
then killed both PIDs manually at ~9m10s, at ~5.8 GB RSS with system
swap filling — before machine exhaustion. Lesson recorded: reuse
`probe12.py`'s tested cap machinery (`--max-rss-gb`, `--max-secs`)
instead of ad-hoc inline watchdogs.

## Salvaged data point (interpretable per the n=12 analogue)

- Bound trajectory: free chain to 40 at 0.14 s; 41 at 0.91 s;
  **42 completed at 4:51** (matches the standalone --limit 42 probe:
  298 s);
  then the 42->43 iteration ran ~4.3 more minutes before the kill:
- At kill (~9m10s): **~89.7M live states, ~5.8 GB RSS** (peaked 6.8 GB
  earlier per watchdog.csv), still growing ~150k states/10 s; swap
  1.1+ GB used of 2 GB.
- Conclusion: the 42->43 iteration at n=13 exceeds 90M states and
  ~6-7 GB within its first half; consistent with the n=12 --limit 39
  analogue (135M states / 5.57 GB at 30-min cap) shifted four levels.
  The first n=13 level where a 16 GiB machine memory-binds is 42->43;
  completing it needs either the 47 GB server or the online index
  (with its measured wall cost) — or, per the programme, decomposition
  so no monolithic 42->43 iteration is ever needed.

Artifacts: `.build/v3-limits/probe13-43/run.log`, `watchdog.csv`,
`NOTE-what-actually-happened.txt`.

## Correction (agent post-mortem, 01:1x)

The monitor trace shows the search was killed BY THE OS at 9m10s under
memory pressure (RSS falling while states rose = compressor reclaiming;
peak 6.45 GiB; free pages bottomed at 3,639), essentially simultaneous
with the session's manual kill. Any later `KILLED: 30min cap` /
`probe-done` lines appended to run.log by the orphaned launcher shell
are FALSE — see the NOTE file. Two amendments adopted:
- **Practical RSS ceiling on the 16 GiB M4 is ~6 GB, not 8 GB** (5.57
  GiB survived; 6.45 GiB was killed).
- Future probes must trip on free-page count, not RSS alone — the
  compressor makes RSS understate pressure exactly when it matters.
Silver lining: the probe independently reproduced the bound-42
measurement (4:51.0 vs 4:58.4, ~2%), strengthening the n=12<->n=13
correspondence.
