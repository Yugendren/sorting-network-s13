"""gen0: reversal-symmetric greedy construction.

Lineage: seed program. Comparators are added in mirror pairs
((lo,hi) with (12-hi,12-lo)) per the Valsalam-Miikkulainen observation
that reversal-symmetric prefixes correlate with short completions; the
center pair coincides with its own mirror. Greedy choice by unsorted-
vector reduction, variant-seeded tie-breaking, greedy asymmetric tail
if symmetry stalls.
"""

import random

import numpy as np

CHANNELS = 13
N_VECTORS = 1 << CHANNELS
BUDGET = 90
SAMPLE = 20

_INPUTS = ((np.arange(N_VECTORS)[:, None] >> np.arange(CHANNELS)) & 1).astype(
    np.uint8
)
_SORTED = np.sort(_INPUTS, axis=1)
_ALL_PAIRS = [
    (lo, hi) for lo in range(CHANNELS) for hi in range(lo + 1, CHANNELS)
]


def _mirror(pair):
    lo, hi = pair
    return (CHANNELS - 1 - hi, CHANNELS - 1 - lo)


def _apply(state, pair):
    lo, hi = pair
    a, b = state[:, lo], state[:, hi]
    state[:, lo] = np.minimum(a, b)
    state[:, hi] = np.maximum(a, b)


def _unsorted_count(state):
    return int((state != _SORTED).any(axis=1).sum())


def build(params):
    rng = random.Random(params["variant"] * 104729 + 7)
    state = _INPUTS.copy()
    network = []
    current = _unsorted_count(state)
    stalls = 0
    while current > 0 and len(network) < BUDGET:
        candidates = rng.sample(_ALL_PAIRS, min(SAMPLE, len(_ALL_PAIRS)))
        best = None
        for pair in candidates:
            group = [pair] if _mirror(pair) == pair else [pair, _mirror(pair)]
            trial = state.copy()
            for p in group:
                _apply(trial, p)
            after = _unsorted_count(trial)
            if best is None or after < best[0]:
                best = (after, group, trial)
        after, group, trial = best
        if after >= current:
            stalls += 1
            if stalls >= 3:
                # Symmetric moves stopped helping: finish asymmetrically.
                pair = min(
                    _ALL_PAIRS,
                    key=lambda p: _try_single(state, p),
                )
                _apply(state, pair)
                network.append(pair)
                current = _unsorted_count(state)
                continue
        else:
            stalls = 0
        network.extend(group)
        state = trial
        current = after
    return network


def _try_single(state, pair):
    trial = state.copy()
    _apply(trial, pair)
    return _unsorted_count(trial)
