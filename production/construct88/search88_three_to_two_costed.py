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

from search88_three_to_two_divisors import combine_factors, divisors

ROOT = Path(__file__).resolve().parent


def scan_solution(p, q, remaining):
    lo = q // p + 1
    hi = (2 * q - 1) // p
    tested = 0
    for a in range(lo, hi + 1):
        tested += 1
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
            return (a, b), tested
    return None, tested


def divisor_solution(p, q, factors, remaining):
    tested = 0
    for divisor in divisors({prime: 2 * exponent for prime, exponent in factors.items()}):
        if divisor > q:
            break
        tested += 1
        if (divisor + q) % p:
            continue
        other = q * q // divisor
        if (other + q) % p:
            continue
        x = (divisor + q) // p
        y = (other + q) // p
        if x != y and x not in remaining and y not in remaining:
            return (x, y), tested
    return None, tested


def solve(p, q, factors, width, pair_count, remaining):
    if width <= pair_count:
        return scan_solution(p, q, remaining), "scan"
    return divisor_solution(p, q, factors, remaining), "divisor"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-cost", type=int, default=0)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    assert args.max_cost >= 0
    assert scan_solution(1, 2, set()) == ((3, 6), 1)
    assert divisor_solution(1, 2, {2: 1}, set()) == ((3, 6), 1)
    assert scan_solution(5, 6, set()) == ((2, 3), 1)
    source_name = "logs/construct89_emath.json"
    source = json.loads((ROOT / source_name).read_text())
    values = set(source["denominators"])
    assert source["valid"] and len(values) == 89
    assert sum((Fraction(1, a) for a in values), Fraction()) == 5
    assert not (ROOT / "logs/found87.log").exists() and not (ROOT / "logs/found88.log").exists()
    started = time.monotonic()
    rows = []
    candidates = []
    histogram = {}
    total_min_cost = 0
    nonempty = 0
    for triple in combinations(sorted(values), 3):
        factors = combine_factors(triple)
        lcm = math.prod(prime ** exponent for prime, exponent in factors.items())
        numerator = sum(lcm // value for value in triple)
        reduced = math.gcd(numerator, lcm)
        q = lcm // reduced
        p = numerator // reduced
        assert Fraction(p, q) == sum((Fraction(1, a) for a in triple), Fraction())
        q_factors = dict(factors)
        for prime in factors:
            while reduced % prime == 0:
                q_factors[prime] -= 1
                reduced //= prime
        assert reduced == 1 and all(exponent >= 0 for exponent in q_factors.values())
        q_factors = {prime: exponent for prime, exponent in q_factors.items() if exponent}
        lo = q // p + 1
        hi = (2 * q - 1) // p
        width = max(0, hi - lo + 1)
        divisor_count = math.prod(2 * exponent + 1 for exponent in q_factors.values())
        pair_count = (divisor_count + 1) // 2
        cost = min(width, pair_count)
        total_min_cost += cost
        histogram[cost.bit_length()] = histogram.get(cost.bit_length(), 0) + 1
        nonempty += width > 0
        row = (cost, width, pair_count, triple, p, q)
        rows.append(row)
        if 0 < cost <= args.max_cost:
            candidates.append((row, q_factors))
    rows.sort()
    candidates.sort(key=lambda item: item[0])
    report = {"valid": True, "profile_only": args.max_cost == 0,
              "source": source_name, "source_sha256": hashlib.sha256((ROOT / source_name).read_bytes()).hexdigest(),
              "all_triples": len(rows), "nonempty_first_denominator_ranges": nonempty,
              "cost_definition": "min(number of first denominators to scan, number of divisor pairs of q^2 with d<=q)",
              "total_min_cost_all_triples": total_min_cost,
              "cost_bit_length_histogram": histogram,
              "smallest": [{"cost": cost, "width": width, "divisor_pairs": pairs,
                            "triple": triple, "p": p, "q": q}
                           for cost, width, pairs, triple, p, q in rows[:40]],
              "max_cost_selected": args.max_cost,
              "selected_triples": len(candidates), "checked_triples": 0,
              "scan_triples": 0, "divisor_triples": 0, "tested_candidates": 0,
              "representations": [], "global_88_nonexistence_claimed": False,
              "seconds_profile_and_search": 0,
              "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat()}
    for (cost, width, pair_count, triple, p, q), factors in candidates:
        remaining = values - set(triple)
        (solution, tested), method = solve(p, q, factors, width, pair_count, remaining)
        report["checked_triples"] += 1
        report[method + "_triples"] += 1
        report["tested_candidates"] += tested
        assert tested <= cost
        if solution is None:
            continue
        found = sorted(remaining | set(solution))
        assert len(found) == 88
        assert sum((Fraction(1, a) for a in found), Fraction()) == 5
        check = subprocess.run(["python3", "verify.py", "5", *map(str, found)], cwd=ROOT,
                               text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True)
        assert "valid: True" in check.stdout
        report["representations"].append({"triple": triple, "replacement": solution,
                                         "denominators": found, "verify_py": check.stdout})
        with (ROOT / "logs/found88.log").open("x") as stream:
            stream.write("5 88 : " + " ".join(map(str, found)) + "\n")
        break
    report["profile_and_search_complete"] = True
    report["complete_all_triples"] = report["checked_triples"] == len(rows)
    report["seconds_profile_and_search"] = time.monotonic() - started
    report["program_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    output = ROOT / args.output
    assert not output.exists()
    output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0 if report["representations"] or args.max_cost == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
