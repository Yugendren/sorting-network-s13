"""gen0: odd-even transposition (brick) sort, optionally truncated.

Lineage: seed program. Baseline valid sorter at 78 comparators; variants
truncate trailing rounds to explore the validity boundary.
"""

CHANNELS = 13


def build(params):
    variant = params["variant"]
    rounds = CHANNELS - (variant % 4)  # 13, 12, 11, 10 rounds
    network = []
    for r in range(rounds):
        start = r % 2
        for lo in range(start, CHANNELS - 1, 2):
            network.append((lo, lo + 1))
    return network
