#!/usr/bin/env python3
from fractions import Fraction
from itertools import combinations
from pathlib import Path
import datetime
import hashlib
import json
import subprocess
import time

from audit89_pair_triple_merges import merged_denominator
from search88_three_to_two_divisors import factor_number, divisors

ROOT = Path(__file__).resolve().parent
LARGE = {82, 162, 76368, 1821627808, 323912070702990, 1848221296482496}


def main():
    started = time.monotonic()
    source_name = "logs/construct89_emath.json"
    source = json.loads((ROOT / source_name).read_text())
    initial = tuple(sorted(source["denominators"]))
    assert source["valid"] and len(initial) == len(set(initial)) == 89
    assert sum((Fraction(1, a) for a in initial), Fraction()) == 5
    assert not (ROOT / "logs/found87.log").exists() and not (ROOT / "logs/found88.log").exists()
    split_count = 0
    split_states = set()
    for a in initial:
        for b in divisors(factor_number(a * a)):
            if a in LARGE and b > 64:
                continue
            u = a + b
            v = a * u // b
            if u == v or v.bit_length() > 512:
                continue
            assert Fraction(1, a) == Fraction(1, u) + Fraction(1, v)
            remaining = set(initial) - {a}
            if u in remaining or v in remaining:
                continue
            split_count += 1
            split_states.add(tuple(sorted(remaining | {u, v})))
    assert all(sum((Fraction(1, a) for a in state), Fraction()) == 5 for state in split_states)
    neighbors = {}
    merge_applications = 0
    for state in sorted(split_states):
        for pair in combinations(state, 2):
            merged = merged_denominator(pair)
            if merged is None:
                continue
            remaining = set(state) - set(pair)
            if merged in remaining:
                continue
            merge_applications += 1
            candidate = tuple(sorted(remaining | {merged}))
            if candidate == initial or candidate in neighbors:
                continue
            assert len(candidate) == 89
            assert sum((Fraction(1, a) for a in candidate), Fraction()) == 5
            neighbors[candidate] = {"split_state": state, "merged_pair": pair, "added": merged}
    representations = []
    pair_checks = triple_checks = 0
    for index, (state, provenance) in enumerate(sorted(neighbors.items())):
        for size in (2, 3):
            for subset in combinations(state, size):
                merged = merged_denominator(subset)
                if merged is None:
                    continue
                remaining = set(state) - set(subset)
                if merged in remaining:
                    continue
                candidate = tuple(sorted(remaining | {merged}))
                expected_terms = 90 - size
                assert len(candidate) == expected_terms
                assert sum((Fraction(1, a) for a in candidate), Fraction()) == 5
                check = subprocess.run(["python3", "verify.py", "5", *map(str, candidate)], cwd=ROOT,
                                       text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True)
                assert "valid: True" in check.stdout
                representations.append({"neighbor": state, "provenance": provenance,
                                        "removed": subset, "added": merged, "terms": expected_terms,
                                        "denominators": candidate, "verify_py": check.stdout})
                with (ROOT / f"logs/found{expected_terms}.log").open("x") as stream:
                    stream.write(f"5 {expected_terms} : " + " ".join(map(str, candidate)) + "\n")
            if size == 2:
                pair_checks += 3916
            else:
                triple_checks += 113564
        if (index + 1) % 25 == 0:
            print("checked_neighbors", index + 1, "of", len(neighbors), flush=True)
    report = {"valid": True,
              "scope": "Every one-split/one-merge neighbor in the stated split domain, then all direct pair-to-one and triple-to-one merges",
              "split_domain": "All divisor splits for denominators not in LARGE; LARGE splits use divisors at most 64 and require new denominators below 2^512",
              "large_tail": sorted(LARGE), "split_candidates": split_count,
              "unique_split_states": len(split_states), "merge_applications": merge_applications,
              "unique_new_89_states": len(neighbors),
              "direct_pair_merge_checks": pair_checks, "direct_triple_merge_checks": triple_checks,
              "representations": representations,
              "found_88": any(item["terms"] == 88 for item in representations),
              "found_87": any(item["terms"] == 87 for item in representations),
              "global_88_nonexistence_claimed": False,
              "neighbor_examples": [{"denominators": state, **provenance}
                                    for state, provenance in list(sorted(neighbors.items()))[:10]],
              "source": source_name, "source_sha256": hashlib.sha256((ROOT / source_name).read_bytes()).hexdigest(),
              "program_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "seconds": time.monotonic() - started,
              "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat()}
    output = ROOT / "logs/search88_split_merge_neighbors.json"
    assert not output.exists()
    output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
