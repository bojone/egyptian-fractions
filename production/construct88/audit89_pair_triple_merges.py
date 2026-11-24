#!/usr/bin/env python3
from fractions import Fraction
from itertools import combinations
from pathlib import Path
import datetime
import hashlib
import json
import math
import subprocess

ROOT = Path(__file__).resolve().parent


def merged_denominator(values):
    lcm = math.lcm(*values)
    numerator = sum(lcm // value for value in values)
    if math.gcd(numerator, lcm) != numerator:
        return None
    return lcm // numerator


def main():
    assert merged_denominator((3, 6)) == 2
    assert merged_denominator((2, 3, 6)) == 1
    assert merged_denominator((2, 3, 7)) is None
    source_name = "logs/construct89_emath.json"
    source = json.loads((ROOT / source_name).read_text())
    values = tuple(sorted(source["denominators"]))
    assert source["valid"] and len(values) == len(set(values)) == 89
    assert sum((Fraction(1, a) for a in values), Fraction()) == 5
    assert not (ROOT / "logs/found87.log").exists()
    assert not (ROOT / "logs/found88.log").exists()
    checked = {2: 0, 3: 0}
    non_distinct = {2: 0, 3: 0}
    representations = []
    for size in (2, 3):
        for subset in combinations(values, size):
            checked[size] += 1
            merged = merged_denominator(subset)
            if merged is None:
                continue
            remaining = set(values) - set(subset)
            if merged in remaining:
                non_distinct[size] += 1
                continue
            candidate = tuple(sorted(remaining | {merged}))
            expected_terms = 90 - size
            assert len(candidate) == expected_terms
            assert sum((Fraction(1, a) for a in candidate), Fraction()) == 5
            check = subprocess.run(["python3", "verify.py", "5", *map(str, candidate)],
                                   cwd=ROOT, text=True, stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT, check=True)
            assert "valid: True" in check.stdout
            representations.append({"removed": subset, "added": merged,
                                    "terms": expected_terms, "denominators": candidate,
                                    "verify_py": check.stdout})
            found = ROOT / f"logs/found{expected_terms}.log"
            with found.open("x") as stream:
                stream.write(f"5 {expected_terms} : " + " ".join(map(str, candidate)) + "\n")
    assert checked == {2: math.comb(89, 2), 3: math.comb(89, 3)}
    report = {"valid": True,
              "scope": "Complete pair-to-one and triple-to-one merges inside the known 89-term representation only",
              "local_only": True, "global_88_nonexistence_claimed": False,
              "source": source_name,
              "source_sha256": hashlib.sha256((ROOT / source_name).read_bytes()).hexdigest(),
              "checked_pairs": checked[2], "checked_triples": checked[3],
              "unit_sum_pairs_with_duplicate_merged_denominator": non_distinct[2],
              "unit_sum_triples_with_duplicate_merged_denominator": non_distinct[3],
              "representations": representations,
              "found_88": any(item["terms"] == 88 for item in representations),
              "found_87": any(item["terms"] == 87 for item in representations),
              "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat()}
    output = ROOT / "logs/audit89_pair_triple_merges.json"
    assert not output.exists()
    output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
