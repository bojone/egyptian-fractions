#!/usr/bin/env python3
from fractions import Fraction
from pathlib import Path
import json
import math
import os
import subprocess

from search88_local_replacements import two_tail
from search88_three_to_two_divisors import factor_number, divisors

ROOT = Path(__file__).resolve().parent
values = set(json.loads((ROOT / "logs/construct89_emath.json").read_text())["denominators"])


def unit_factors(p, q, x, common):
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


def main():
    assert unit_factors(8, 9, 3, 3) == {3: 2}
    assert unit_two_tail(6, 7, 11, set(), factor_number(6))[0] == (7, 42)
    task_file = os.environ["TASK_FILE"]
    expected = int(os.environ.get("EXPECTED_TASKS", "0"))
    quadruples = tested_x = tested_y = tested_z = 0
    unit_cases = unit_g = unit_h = 0
    for line in (ROOT / task_file).read_text().splitlines():
        fields = line.split()
        removed = tuple(map(int, fields[:-5]))
        p, q = map(int, fields[len(removed):len(removed) + 2])
        target = Fraction(p, q)
        assert target == sum((Fraction(1, a) for a in removed), Fraction())
        remaining = values - set(removed)
        quadruples += 1
        for x in range(q // p + 1, 4 * q // p + 1):
            if x in remaining:
                continue
            tested_x += 1
            p1, q1 = p * x - q, q * x
            common = math.gcd(p1, q1)
            p1 //= common
            q1 //= common
            for y in range(max(x + 1, q1 // p1 + 1), 3 * q1 // p1 + 1):
                if y in remaining:
                    continue
                tested_y += 1
                original_p = p1 * y - q1
                original_q = q1 * y
                g2 = math.gcd(original_p, original_q)
                rest = Fraction(original_p, original_q)
                p2, q2 = rest.numerator, rest.denominator
                solution = None
                if p2 == 1 and g2 == y:
                    assert q2 == q1
                    unit_cases += 1
                    lo = max(y + 1, q1 + 1)
                    hi = 2 * q1 - 1
                    solution, g_checks, h_checks = unit_two_tail(
                        q1, lo, hi, remaining, unit_factors(p, q, x, common))
                    unit_g += g_checks
                    unit_h += h_checks
                else:
                    cap = None
                    if p2 > 4 * (q2 // p2):
                        lo = max(y + 1, q2 // p2 + 1)
                        if p2 * lo - q2 > lo * lo:
                            continue
                        left, right = lo, (2 * q2 - 1) // p2
                        while left < right:
                            mid = (left + right + 1) // 2
                            if p2 * mid - q2 <= mid * mid:
                                left = mid
                            else:
                                right = mid - 1
                        cap = left
                    solution, tests, width = two_tail(rest, remaining | {y}, 1_000_000_000,
                                                     previous=y, hi_limit=cap)
                    if solution is None and tests < width:
                        raise RuntimeError("independent two-tail width limit reached")
                    tested_z += tests
                if solution:
                    z, w = solution
                    found = sorted(remaining | {x, y, z, w})
                    assert len(found) == 88 and sum((Fraction(1, a) for a in found), Fraction()) == 5
                    check = subprocess.run(["python3", str(ROOT / "verify.py"), "5", *map(str, found)],
                                           text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                    assert check.returncode == 0, check.stdout
                    (ROOT / "logs/found88.log").write_text(
                        f"5 88 : {' '.join(map(str, found))}\n{check.stdout}")
                    report = {"status": "found_verified", "removed": removed,
                              "replacement": [x, y, z, w], "denominators": found,
                              "verification": check.stdout}
                    (ROOT / "logs/found88_verification.json").write_text(json.dumps(report, indent=2) + "\n")
                    print(json.dumps(report, indent=2))
                    return 0
        if quadruples % 1000 == 0:
            print("progress", quadruples, tested_x, tested_y, tested_z, unit_cases, unit_g, unit_h, flush=True)
    if expected:
        assert quadruples == expected, (quadruples, expected)
    print(json.dumps({"status": "completed_selected_subset_without_representation",
                      "quadruples": quadruples, "tested_x": tested_x, "tested_y": tested_y,
                      "tested_z": tested_z, "unit_cases": unit_cases, "unit_g": unit_g,
                      "unit_h": unit_h, "solutions": 0,
                      "global_88_nonexistence_claimed": False}, indent=2))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
