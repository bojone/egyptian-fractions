#!/usr/bin/env python3
from fractions import Fraction
from itertools import combinations
from pathlib import Path
import argparse
import datetime
import hashlib
import json
import subprocess
import time

from search88_local_replacements import two_tail

ROOT = Path(__file__).resolve().parent


def three_tail(target, remaining, max_tests):
    p, q = target.numerator, target.denominator
    lo = q // p + 1
    hi = (3 * q - 1) // p
    tests = 0
    for a in range(lo, hi + 1):
        if a in remaining:
            continue
        rest = target - Fraction(1, a)
        if rest <= 0:
            continue
        pair, more, _ = two_tail(rest, remaining, max_tests, previous=a)
        tests += more
        if pair:
            return (a, *pair), tests
        if tests >= max_tests:
            break
    return None, tests


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--quad-limit", type=int, default=20000)
    parser.add_argument("--max-tests", type=int, default=100000)
    parser.add_argument("--output", default="logs/search88_four_to_three_status.json")
    args = parser.parse_args()
    values = set(json.loads((ROOT / "logs/construct89_emath.json").read_text())["denominators"])
    assert len(values) == 89 and sum((Fraction(1, a) for a in values), Fraction()) == 5
    started = time.monotonic()
    self_solution, _ = three_tail(Fraction(77, 60), set(), 10000)
    assert self_solution and sum((Fraction(1, a) for a in self_solution), Fraction()) == Fraction(77, 60)
    print("three_tail_selftest", self_solution, flush=True)
    quads = []
    for quad in combinations(sorted(values), 4):
        target = sum((Fraction(1, a) for a in quad), Fraction())
        p, q = target.numerator, target.denominator
        lo = q // p + 1
        hi = (3 * q - 1) // p
        if hi >= lo:
            quads.append((hi - lo + 1, quad))
    quads.sort()
    print("ranked_quads", len(quads), "limit", args.quad_limit, flush=True)
    print("narrowest", quads[:10], flush=True)
    candidate_tests = 0
    tested = 0
    for _, quad in quads[:args.quad_limit]:
        target = sum((Fraction(1, a) for a in quad), Fraction())
        remaining = values - set(quad)
        solution, tests = three_tail(target, remaining, args.max_tests)
        candidate_tests += tests
        tested += 1
        if solution:
            found = sorted(remaining | set(solution))
            if len(found) != 88 or sum((Fraction(1, a) for a in found), Fraction()) != 5:
                raise RuntimeError("invalid four-to-three certificate")
            check = subprocess.run(["python3", str(ROOT / "verify.py"), "5", *map(str, found)],
                                   text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            if check.returncode:
                raise RuntimeError(check.stdout)
            (ROOT / "logs/found88.log").write_text(
                f"5 88 : {' '.join(map(str, found))}\n{check.stdout}")
            report = {"status": "found_verified", "quad": quad, "replacement": solution,
                      "denominators": found, "verification": check.stdout,
                      "candidate_tests": candidate_tests}
            (ROOT / args.output).write_text(json.dumps(report, indent=2) + "\n")
            print(json.dumps(report, indent=2), flush=True)
            return 0
        if tested % 1000 == 0:
            print("tested_quads", tested, "candidate_tests", candidate_tests,
                  "seconds", time.monotonic() - started, flush=True)
    report = {
        "status": "completed_prioritized_subset_without_representation",
        "ranked_quads": len(quads), "tested_quads": tested,
        "candidate_tests": candidate_tests, "seconds": time.monotonic() - started,
        "quad_limit": args.quad_limit, "global_88_nonexistence_claimed": False,
        "source_sha256": hashlib.sha256((ROOT / "search88_four_to_three.py").read_bytes()).hexdigest(),
        "finished_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    (ROOT / args.output).write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2), flush=True)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
