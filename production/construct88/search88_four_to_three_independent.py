#!/usr/bin/env python3
from fractions import Fraction
from pathlib import Path
import json
import math
import os
import subprocess
import sys

from search88_local_replacements import two_tail
from search88_three_to_two_divisors import factor_number, divisors

ROOT = Path(__file__).resolve().parent
values = set(json.loads((ROOT / "logs/construct89_emath.json").read_text())["denominators"])


def unit_factors(q, x, common):
    merged = dict(factor_number(q))
    for prime, exponent in factor_number(x).items():
        merged[prime] = merged.get(prime, 0) + exponent
    for prime in list(merged):
        while common % prime == 0:
            common //= prime
            merged[prime] -= 1
    assert common == 1
    merged = {prime: exponent for prime, exponent in merged.items() if exponent}
    assert math.prod(prime ** exponent for prime, exponent in merged.items()) == q * x // math.gcd(p * x - q, q * x)
    return merged


def unit_two_tail(q, lo, hi, remaining, factors):
    g_checks = h_checks = 0
    for g in divisors(factors):
        quotient = q // g
        g_checks += 1
        for h in divisors(factors):
            if h > quotient:
                break
            if g % h or math.gcd(h, quotient) != 1:
                continue
            h_checks += 1
            t = quotient + h
            y = g * t
            if not lo <= y <= hi:
                continue
            z = q * t // h
            if z <= y or y in remaining or z in remaining:
                continue
            return (y, z), g_checks, h_checks
    return None, g_checks, h_checks


task_file = os.environ.get("TASK_FILE", "logs/search87_remaining_four_to_two_tasks.txt")
summary = json.loads((ROOT / os.environ.get("TASK_SUMMARY", "logs/search87_remaining_four_to_two_task_summary.json")).read_text())
quadruples = tested_x = tested_y = unit_cases = unit_g = unit_h = 0
for line in (ROOT / task_file).read_text().splitlines():
    fields = line.split()
    removed = tuple(map(int, fields[:-5] if ":" in fields[-1] else fields[:-4]))
    p, q = map(int, fields[len(removed):len(removed) + 2])
    target = Fraction(p, q)
    assert target == sum((Fraction(1, a) for a in removed), Fraction())
    target_terms = 89 - len(removed) + 3
    remaining = values - set(removed)
    quadruples += 1
    for x in range(q // p + 1, 3 * q // p + 1):
        if x in remaining:
            continue
        tested_x += 1
        original_p = p * x - q
        original_q = q * x
        common = math.gcd(original_p, original_q)
        rest = target - Fraction(1, x)
        p1, q1 = rest.numerator, rest.denominator
        lo = max(x + 1, q1 // p1 + 1)
        hi = (2 * q1 - 1) // p1
        if p1 == 1:
            unit_cases += 1
            solution, g_checks, h_checks = unit_two_tail(
                q1, lo, hi, remaining, unit_factors(q, x, common))
            unit_g += g_checks
            unit_h += h_checks
        else:
            cap = None
            if p1 > 4 * (q1 // p1):
                if p1 * lo - q1 > lo * lo:
                    continue
                left, right = lo, hi
                while left < right:
                    mid = (left + right + 1) // 2
                    if p1 * mid - q1 <= mid * mid:
                        left = mid
                    else:
                        right = mid - 1
                cap = left
            solution, tests, width = two_tail(rest, remaining | {x}, 1_000_000, previous=x, hi_limit=cap)
            if solution is None and tests < width:
                raise RuntimeError("independent two-tail width limit reached; cannot claim a negative")
            tested_y += tests
        if solution:
            y, z = solution
            found = sorted(remaining | {x, y, z})
            assert len(found) == target_terms and sum((Fraction(1, a) for a in found), Fraction()) == 5
            check = subprocess.run(["python3", str(ROOT / "verify.py"), "5", *map(str, found)],
                                   text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            assert check.returncode == 0, check.stdout
            (ROOT / f"logs/found{target_terms}.log").write_text(
                f"5 {target_terms} : {' '.join(map(str, found))}\n{check.stdout}")
            print(json.dumps({"status": "found_verified", "removed": removed,
                              "replacement": [x, y, z], "denominators": found,
                              "target_terms": target_terms,
                              "verification": check.stdout}, indent=2))
            raise SystemExit(0)
    if quadruples % 1000 == 0:
        print("progress", quadruples, tested_x, tested_y, unit_cases, unit_g, unit_h, file=sys.stderr)
assert quadruples == (summary["candidate_quintuples"] if "candidate_quintuples" in summary
                      else summary["candidate_quadruples"])
print(json.dumps({"status": "completed_prioritized_subset_without_representation",
                  "quadruples": quadruples, "tested_x": tested_x, "tested_y": tested_y,
                  "unit_cases": unit_cases, "unit_g": unit_g, "unit_h": unit_h,
                  "solutions": 0, **{f"global_{target_terms}_nonexistence_claimed": False}}, indent=2))
raise SystemExit(1)
