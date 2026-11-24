#!/usr/bin/env python3
from fractions import Fraction
from hashlib import sha256
from itertools import combinations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "logs" / "construct89_emath.json"
source = json.loads(SOURCE.read_text())
values = set(source["denominators"])
assert len(values) == 89 and sum((Fraction(1, a) for a in values), Fraction()) == 5
valid88 = []
valid87 = []
pair_duplicates = 0
triple_duplicates = 0

for a, b in combinations(sorted(values), 2):
    target = Fraction(1, a) + Fraction(1, b)
    if target.numerator != 1:
        continue
    merged = target.denominator
    candidate = (values - {a, b}) | {merged}
    if merged in values - {a, b}:
        pair_duplicates += 1
        assert sum((Fraction(1, d) for d in candidate), Fraction()) != 5
    elif len(candidate) == 88 and sum((Fraction(1, d) for d in candidate), Fraction()) == 5:
        valid88.append({"removed": [a, b], "added": merged, "denominators": sorted(candidate)})

for a, b, c in combinations(sorted(values), 3):
    target = Fraction(1, a) + Fraction(1, b) + Fraction(1, c)
    if target.numerator != 1:
        continue
    merged = target.denominator
    candidate = (values - {a, b, c}) | {merged}
    if merged in values - {a, b, c}:
        triple_duplicates += 1
        assert sum((Fraction(1, d) for d in candidate), Fraction()) != 5
    elif len(candidate) == 87 and sum((Fraction(1, d) for d in candidate), Fraction()) == 5:
        valid87.append({"removed": [a, b, c], "added": merged, "denominators": sorted(candidate)})

report = {
    "valid": True,
    "scope": "Independent exhaustive pair-to-one and triple-to-one check; duplicate merged denominators are rejected by exact summation",
    "source": "logs/construct89_emath.json",
    "source_sha256": sha256(SOURCE.read_bytes()).hexdigest(),
    "checked_pairs": 3916,
    "checked_triples": 113564,
    "pair_duplicates_rejected": pair_duplicates,
    "triple_duplicates_rejected": triple_duplicates,
    "valid_88_merges": valid88,
    "valid_87_merges": valid87,
    "found88": bool(valid88),
    "found87": bool(valid87),
    "global_88_nonexistence_claimed": False,
}
print(json.dumps(report, indent=2))
