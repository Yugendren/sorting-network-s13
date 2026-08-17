"""gen0: greedy randomized construction.

Lineage: seed program. At each step, sample candidate comparators and
append the one that most reduces the number of unsorted binary vectors;
random tie-breaking driven by the variant seed. Stops when sorted or at
the budget.
"""

import random

import numpy as np

CHANNELS = 13
N_VECTORS = 1 << CHANNELS
BUDGET = 90
SAMPLE = 24

_INPUTS = ((np.arange(N_VECTORS)[:, None] >> np.arange(CHANNELS)) & 1).astype(
    np.uint8
)
_SORTED = np.sort(_INPUTS, axis=1)
_ALL_PAIRS = [
    (lo, hi) for lo in range(CHANNELS) for hi in range(lo + 1, CHANNELS)
]


def _unsorted_count(state):
    return int((state != _SORTED).any(axis=1).sum())


def build(params):
    rng = random.Random(params["variant"] * 7919 + 13)
    state = _INPUTS.copy()
    network = []
    current = _unsorted_count(state)
    while current > 0 and len(network) < BUDGET:
        candidates = rng.sample(_ALL_PAIRS, min(SAMPLE, len(_ALL_PAIRS)))
        best_pair, best_after, best_state = None, current + 1, None
        for lo, hi in candidates:
            trial = state.copy()
            a, b = trial[:, lo], trial[:, hi]
            trial[:, lo] = np.minimum(a, b)
            trial[:, hi] = np.maximum(a, b)
            after = _unsorted_count(trial)
            if after < best_after:
                best_pair, best_after, best_state = (lo, hi), after, trial
        if best_pair is None or best_after >= current:
            # No sampled comparator helps; take a random productive-looking
            # one anyway to escape the plateau.
            lo, hi = rng.choice(_ALL_PAIRS)
            a, b = state[:, lo], state[:, hi]
            state[:, lo] = np.minimum(a, b)
            state[:, hi] = np.maximum(a, b)
            network.append((lo, hi))
            current = _unsorted_count(state)
        else:
            network.append(best_pair)
            state = best_state
            current = best_after
    return network
