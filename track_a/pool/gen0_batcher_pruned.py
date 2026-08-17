"""gen0: Batcher odd-even mergesort for 16 channels, pruned to 13.

Lineage: seed program. Comparators touching channels >= 13 are dropped;
the remainder still sorts 13 inputs because the dropped channels can be
treated as +infinity padding at the top.
"""

CHANNELS = 13
PADDED = 16


def _batcher(n):
    net = []
    p = 1
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


def build(params):
    full = _batcher(PADDED)
    return [(a, b) for a, b in full if a < CHANNELS and b < CHANNELS]
