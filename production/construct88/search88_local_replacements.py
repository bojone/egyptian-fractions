#!/usr/bin/env python3
from fractions import Fraction
from itertools import combinations
from pathlib import Path
import argparse
import datetime
import hashlib
import json
import math
import subprocess
import time

ROOT = Path(__file__).resolve().parent


def two_tail(target, remaining, max_tests=1_000_000, previous=0, hi_limit=None):
    p, q = target.numerator, target.denominator
    lo = max(previous + 1, q // p + 1)
    hi = (2 * q - 1) // p
    if hi_limit is not None:
        hi = min(hi, hi_limit)
    if hi < lo:
        return None, 0, 0
    width = hi - lo + 1
    tests = 0
    for a in range(lo, hi + 1):
        if tests >= max_tests:
            return None, tests, width
        tests += 1
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
            return (a, b), tests, width
    return None, tests, width


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--triple-limit", type=int, default=20000)
    parser.add_argument("--max-tests", type=int, default=1_000_000)
    parser.add_argument("--output", default="logs/search88_local_replacements_status.json")
    args = parser.parse_args()
    source = json.loads((ROOT / "logs/construct89_emath.json").read_text())
    values = set(source["denominators"])
    assert len(values) == 89 and sum((Fraction(1, a) for a in values), Fraction()) == 5
    started = time.monotonic()
    self_solution, _, _ = two_tail(Fraction(13, 12), set(), 1000)
    assert self_solution and sum((Fraction(1, a) for a in self_solution), Fraction()) == Fraction(13, 12)
    print("two_tail_selftest", self_solution, flush=True)
    pair_checks = 0
    for a, b in combinations(sorted(values), 2):
        pair_checks += 1
        numerator = a + b
        denominator = a * b
        if denominator % numerator == 0:
            c = denominator // numerator
            candidate = (values - {a, b}) | {c}
            if len(candidate) == 88:
                found = sorted(candidate)
                check = subprocess.run(["python3", str(ROOT / "verify.py"), "5", *map(str, found)],
                                       text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                if check.returncode == 0:
                    (ROOT / "logs/found88.log").write_text(
                        f"5 88 : {' '.join(map(str, found))}\n{check.stdout}")
                    print(check.stdout, flush=True)
                    return 0
    triples = []
    for triple in combinations(sorted(values), 3):
        target = sum((Fraction(1, a) for a in triple), Fraction())
        p, q = target.numerator, target.denominator
        lo = q // p + 1
        hi = (2 * q - 1) // p
        if hi < lo:
            continue
        triples.append((hi - lo + 1, triple, target))
    triples.sort(key=lambda item: (item[0], item[1]))
    print("pair_checks", pair_checks, "ranked_triples", len(triples),
          "limit", args.triple_limit, flush=True)
    print("narrowest", [(width, triple) for width, triple, _ in triples[:10]], flush=True)
    tested_triples = 0
    candidate_tests = 0
    for width, triple, target in triples[:args.triple_limit]:
        remaining = values - set(triple)
        solution, tests, _ = two_tail(target, remaining, args.max_tests)
        tested_triples += 1
        candidate_tests += tests
        if solution:
            found = sorted(remaining | set(solution))
            if len(found) != 88 or sum((Fraction(1, a) for a in found), Fraction()) != 5:
                raise RuntimeError("invalid three-to-two certificate")
            check = subprocess.run(["python3", str(ROOT / "verify.py"), "5", *map(str, found)],
                                   text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            if check.returncode:
                raise RuntimeError(check.stdout)
            (ROOT / "logs/found88.log").write_text(
                f"5 88 : {' '.join(map(str, found))}\n{check.stdout}")
            report = {"status": "found_verified", "triple": triple, "replacement": solution,
                      "denominators": found, "verification": check.stdout,
                      "candidate_tests": candidate_tests}
            (ROOT / args.output).write_text(json.dumps(report, indent=2) + "\n")
            print(json.dumps(report, indent=2), flush=True)
            return 0
        if tested_triples % 1000 == 0:
            print("tested_triples", tested_triples, "candidate_tests", candidate_tests,
                  "seconds", time.monotonic() - started, flush=True)
    report = {
        "status": "completed_prioritized_subset_without_representation",
        "pair_checks": pair_checks, "ranked_triples": len(triples),
        "tested_triples": tested_triples, "candidate_tests": candidate_tests,
        "seconds": time.monotonic() - started,
        "triple_limit": args.triple_limit,
        "global_88_nonexistence_claimed": False,
        "source_sha256": hashlib.sha256((ROOT / "search88_local_replacements.py").read_bytes()).hexdigest(),
        "finished_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    (ROOT / args.output).write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2), flush=True)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
