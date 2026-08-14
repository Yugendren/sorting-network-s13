#!/usr/bin/env python3
"""Transparent uniform-random comparator baseline for B2."""

from __future__ import annotations

import argparse
import json
import random
import sys


def initial_wires(channels: int) -> tuple[int, ...]:
    patterns = 1 << channels
    wires = [0] * channels
    for pattern in range(patterns):
        bit = 1 << pattern
        for channel in range(channels):
            if (pattern >> channel) & 1:
                wires[channel] |= bit
    return tuple(wires)


def is_sorted(wires: list[int]) -> bool:
    return all((wires[index] & ~wires[index + 1]) == 0 for index in range(len(wires) - 1))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--channels", type=int, required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--trials", type=int, required=True)
    parser.add_argument("--max-comparators", type=int, required=True)
    args = parser.parse_args()
    if args.channels < 1 or args.trials < 1 or args.max_comparators < 0:
        parser.error("channels/trials must be positive and max-comparators nonnegative")

    rng = random.Random(args.seed)
    choices = [(lower, upper) for lower in range(args.channels) for upper in range(lower + 1, args.channels)]
    base_wires = initial_wires(args.channels)
    best: list[tuple[int, int]] | None = None
    trial_sizes: list[int | None] = []
    evaluations = 0
    for _ in range(args.trials):
        wires = list(base_wires)
        comparators: list[tuple[int, int]] = []
        if is_sorted(wires):
            best = []
            trial_sizes.append(0)
            continue
        for _ in range(args.max_comparators):
            lower, upper = choices[rng.randrange(len(choices))]
            comparators.append((lower, upper))
            low_values, high_values = wires[lower], wires[upper]
            wires[lower] = low_values & high_values
            wires[upper] = low_values | high_values
            evaluations += 1
            if is_sorted(wires):
                trial_sizes.append(len(comparators))
                if best is None or len(comparators) < len(best):
                    best = list(comparators)
                break
        else:
            trial_sizes.append(None)

    report = {
        "schema_version": "s13-random-baseline/v1",
        "algorithm": "uniform random comparator pairs with replacement; stop each trial at first sorting network",
        "channels": args.channels,
        "seed": args.seed,
        "trials": args.trials,
        "max_comparators": args.max_comparators,
        "evaluations": evaluations,
        "successful_trials": sum(size is not None for size in trial_sizes),
        "trial_sizes": trial_sizes,
        "best_size": len(best) if best is not None else None,
        "best_comparators": best,
    }
    sys.stdout.write(json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
