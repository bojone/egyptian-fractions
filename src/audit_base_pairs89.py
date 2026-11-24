#!/usr/bin/env python3
from fractions import Fraction
from hashlib import sha256
from itertools import combinations
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "logs" / "construct89_emath.json"
source = json.loads(SOURCE.read_text())
initial = tuple(sorted(source["denominators"]))
base = tuple(sorted(source["base"]))
values = set(initial)
assert len(initial) == 89 and len(base) == 83
assert sum((Fraction(1, a) for a in initial), Fraction()) == 5


def solutions(target, remaining):
    p, q = target.numerator, target.denominator
    for a in range(q // p + 1, (2 * q - 1) // p + 1):
        if a in remaining:
            continue
        difference = p * a - q
        if difference <= 0 or difference > a * a:
            continue
        g = math.gcd(a, q)
        if difference > g * g or difference % g:
            continue
        h = difference // g
        if not h or g % h or a % h:
            continue
        b = (q // g) * (a // h)
        if b > a and b not in remaining:
            assert Fraction(1, a) + Fraction(1, b) == target
            yield a, b


assert list(solutions(Fraction(5, 6), set())) == [(2, 3)]
pair_checks = solution_count = original_solutions = 0
new_states = set()
for removed in combinations(base, 2):
    pair_checks += 1
    target = Fraction(removed[0] + removed[1], removed[0] * removed[1])
    remaining = values - set(removed)
    for solution in solutions(target, remaining):
        solution_count += 1
        candidate = tuple(sorted(remaining | set(solution)))
        assert len(candidate) == 89
        assert sum((Fraction(1, a) for a in candidate), Fraction()) == 5
        if candidate == initial:
            original_solutions += 1
        else:
            new_states.add(candidate)
assert pair_checks == math.comb(83, 2) == 3403
report = {
    "valid": True,
    "scope": "Independent exhaustive replacement of every pair of the 83 base denominators by two distinct unit denominators",
    "source": "logs/construct89_emath.json",
    "source_sha256": sha256(SOURCE.read_bytes()).hexdigest(),
    "checked_base_pairs": pair_checks,
    "two_denominator_solutions": solution_count,
    "solutions_returning_to_original": original_solutions,
    "unique_new_89_states": len(new_states),
    "representations_88": [],
    "found88": False,
    "global_88_nonexistence_claimed": False,
}
print(json.dumps(report, indent=2))
