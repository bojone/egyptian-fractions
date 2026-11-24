#!/usr/bin/env python3
from fractions import Fraction


def bounds(n, k):
    h = [Fraction()] * (2 * k + 2)
    for a in range(1, len(h)):
        h[a] = h[a - 1] + Fraction(1, a)
    assert h[k] >= n
    minimum_k = next(a for a in range(1, k + 1) if h[a] >= n)
    prefix = 0
    for a in range(1, k + 1):
        if h[k + 1] - Fraction(1, a) < n:
            prefix = a
        else:
            break
    delta = h[k] - n
    minimum_removed = Fraction()
    for r in range(1, k - prefix + 1):
        minimum_removed += Fraction(1, k - r + 1)
        allowed = delta + h[k + r] - h[k]
        if minimum_removed > allowed:
            return minimum_k, prefix, r, r - 1, delta
    return minimum_k, prefix, None, k - prefix, delta


for n, k in ((3, 12), (4, 31), (4, 32), (5, 83), (5, 84),
             (5, 85), (5, 86), (5, 87)):
    minimum_k, prefix, r_bound, rmax, delta = bounds(n, k)
    print(f"n={n} k={k} harmonic-min={minimum_k} prefix={prefix} "
          f"r-bound={r_bound} rmax={rmax} delta={float(delta):.12g}")

three = list(range(1, 11)) + [15, 230, 57960]
four = list(range(1, 29)) + [30, 34, 100, 11934, 14536368]
for n, values in ((3, three), (4, four)):
    assert len(values) == len(set(values))
    assert sum((Fraction(1, a) for a in values), Fraction()) == n
    print(f"n={n}: verified {len(values)} distinct unit fractions")
