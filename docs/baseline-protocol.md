# Frozen baseline protocol

The run is serial: only B0, then B1, then B2, then B3, then B4. A later gate
must fail closed unless its predecessor has committed PASS evidence.

## B0

Pass if the current target is not stale, all required source and protocol
records are pinned, exactly 20 nonzero seeds and all caps are frozen, authority
hashes match, required local artifacts match their hashes, and a clean Git
commit can produce an immutable evidence run.

## B1

Pass only if two independent verifiers agree across the maintained 45 witness,
trusted small positives, independently confirmed negatives, malformed files,
random differential cases, reflection metamorphisms, deterministic replay,
mutations, and a frozen exhaustive small subset.

## B2

Use the external pinned SENSO source with the audited portability patch and the
paper parameters in `config/frozen/b2-senso.json`. Run all 20 frozen seeds
serially within `config/frozen/budgets.json`; preserve every result. Also run
the frozen random and greedy baselines. Every returned candidate is checked by
both B1 verifiers. Pass requires at least one valid 45-comparator result. A
result below 45 triggers the contract's exceptional stop procedure.

## B3

Run the official n=9 search-and-verify workflow at the frozen commit, then
hash and replay the published n=11 certificate. Do not regenerate n=11.
Corrupt a copy of a small input or certificate and require safe rejection.

## B4

Aggregate all evidence without rerunning a search, name the strongest
reproduced construction, distinguish every truth label, issue exactly one
terminal verdict, commit, and stop.
