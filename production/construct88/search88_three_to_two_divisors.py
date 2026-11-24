#!/usr/bin/env python3
from fractions import Fraction
from itertools import combinations
from functools import lru_cache
from pathlib import Path
import argparse
import datetime
import hashlib
import json
import math
import subprocess
import time

ROOT = Path(__file__).resolve().parent


@lru_cache(maxsize=None)
def factor_number(value):
    result = subprocess.run(["factor", str(value)], text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True)
    fields = result.stdout.split()
    assert fields[0] == f"{value}:"
    primes = list(map(int, fields[1:]))
    assert math.prod(primes) == value
    factors = {}
    for prime in primes:
        factors[prime] = factors.get(prime, 0) + 1
    return factors


def combine_factors(values):
    result = {}
    for value in values:
        for prime, exponent in factor_number(value).items():
            result[prime] = max(result.get(prime, 0), exponent)
    return result


def divisors(factors):
    result = [1]
    for prime, exponent in factors.items():
        powers = [prime ** i for i in range(exponent + 1)]
        result = [value * power for value in result for power in powers]
    result.sort()
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--divisor-limit", type=int, default=4096)
    parser.add_argument("--profile-only", action="store_true")
    parser.add_argument("--output", default="logs/search88_three_to_two_divisors_status.json")
    args = parser.parse_args()
    values = set(json.loads((ROOT / "logs/construct89_emath.json").read_text())["denominators"])
    assert len(values) == 89 and sum((Fraction(1, a) for a in values), Fraction()) == 5
    started = time.monotonic()
    candidates = []
    for triple in combinations(sorted(values), 3):
        factors = combine_factors(triple)
        lcm = math.prod(prime ** exponent for prime, exponent in factors.items())
        numerator = sum(lcm // value for value in triple)
        reduced = math.gcd(numerator, lcm)
        q = lcm // reduced
        p = numerator // reduced
        q_factors = dict(factors)
        for prime in factors:
            while reduced % prime == 0:
                q_factors[prime] -= 1
                reduced //= prime
        assert reduced == 1 and all(exponent >= 0 for exponent in q_factors.values())
        q_factors = {prime: exponent for prime, exponent in q_factors.items() if exponent}
        width = (2 * q - 1) // p - q // p
        if width <= 1_000_000:
            continue
        count = math.prod(2 * exponent + 1 for exponent in q_factors.values())
        if args.profile_only or count <= args.divisor_limit:
            candidates.append((count, width, triple, p, q, q_factors))
    candidates.sort()
    if args.profile_only:
        report = {"status": "profile_only_no_search", "candidate_count": len(candidates),
                  "smallest": [{"divisor_count": count, "width": width, "triple": triple}
                               for count, width, triple, _, _, _ in candidates[:100]],
                  "old_width_fully_covered": 1_000_000}
        (ROOT / args.output).write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps(report, indent=2), flush=True)
        return 0
    print("targeted_triples", len(candidates), "divisor_limit", args.divisor_limit, flush=True)
    checked = pairs = 0
    for count, width, triple, p, q, q_factors in candidates:
        remaining = values - set(triple)
        square = q * q
        for divisor in divisors({prime: 2 * exponent for prime, exponent in q_factors.items()}):
            if divisor > q:
                break
            pairs += 1
            if (divisor + q) % p:
                continue
            other = square // divisor
            if (other + q) % p:
                continue
            x = (divisor + q) // p
            y = (other + q) // p
            if x in remaining or y in remaining or x == y:
                continue
            found = sorted(remaining | {x, y})
            assert len(found) == 88
            assert sum((Fraction(1, a) for a in found), Fraction()) == 5
            check = subprocess.run(["python3", str(ROOT / "verify.py"), "5", *map(str, found)],
                                   text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            assert check.returncode == 0, check.stdout
            report = {"status": "found_verified", "triple": triple,
                      "replacement": [x, y], "denominators": found,
                      "verification": check.stdout}
            (ROOT / "logs/found88.log").write_text(
                f"5 88 : {' '.join(map(str, found))}\n{check.stdout}")
            (ROOT / args.output).write_text(json.dumps(report, indent=2) + "\n")
            print(json.dumps(report, indent=2), flush=True)
            return 0
        checked += 1
        if checked % 100 == 0:
            print("checked", checked, "divisor_pairs", pairs,
                  "seconds", time.monotonic() - started, flush=True)
    report = {
        "status": "completed_prioritized_divisor_subset_without_representation",
        "old_width_fully_covered": 1_000_000,
        "new_width_strictly_greater_than": 1_000_000,
        "divisor_limit": args.divisor_limit,
        "targeted_triples": len(candidates),
        "checked_triples": checked,
        "checked_divisor_pairs": pairs,
        "global_88_nonexistence_claimed": False,
        "seconds": time.monotonic() - started,
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "finished_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    (ROOT / args.output).write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2), flush=True)
    return 1


if __name__ == "__main__":
    main()
