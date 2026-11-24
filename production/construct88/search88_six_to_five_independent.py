#!/usr/bin/env python3
from fractions import Fraction
from pathlib import Path
import json
import math
import os
import subprocess

from search88_five_to_four_independent import (
    unit_factors, unit_two_tail, two_tail, values, factor_number)

ROOT = Path(__file__).resolve().parent


def main():
    assert unit_factors(8, 9, 3, 3) == {3: 2}
    assert unit_two_tail(6, 7, 11, set(), factor_number(6))[0] == (7, 42)
    task_file = os.environ["TASK_FILE"]
    expected = int(os.environ.get("EXPECTED_TASKS", "0"))
    sextuples = tested_x = tested_y = tested_z = tested_w = 0
    unit_cases = unit_g = unit_h = 0
    for line in (ROOT / task_file).read_text().splitlines():
        fields = line.split()
        removed = tuple(map(int, fields[:-5]))
        p, q = map(int, fields[len(removed):len(removed) + 2])
        target = Fraction(p, q)
        assert target == sum((Fraction(1, a) for a in removed), Fraction())
        remaining = values - set(removed)
        sextuples += 1
        for x in range(q // p + 1, 5 * q // p + 1):
            if x in remaining:
                continue
            tested_x += 1
            p1, q1 = p * x - q, q * x
            common = math.gcd(p1, q1)
            p1 //= common
            q1 //= common
            for y in range(max(x + 1, q1 // p1 + 1), 4 * q1 // p1 + 1):
                if y in remaining:
                    continue
                tested_y += 1
                p2, q2 = p1 * y - q1, q1 * y
                g2 = math.gcd(p2, q2)
                p2 //= g2
                q2 //= g2
                for z in range(max(y + 1, q2 // p2 + 1), 3 * q2 // p2 + 1):
                    tested_z += 1
                    if z in remaining:
                        continue
                    p3, q3 = p2 * z - q2, q2 * z
                    g3 = math.gcd(p3, q3)
                    p3 //= g3
                    q3 //= g3
                    solution = None
                    if p3 == 1 and g3 == z and q3 == q2:
                        unit_cases += 1
                        lo = max(z + 1, q2 + 1)
                        hi = 2 * q2 - 1
                        factors = unit_factors(p1, q1, y, g2)
                        solution, g_checks, h_checks = unit_two_tail(
                            q2, lo, hi, remaining, factors)
                        unit_g += g_checks
                        unit_h += h_checks
                    else:
                        cap = None
                        if p3 > 4 * (q3 // p3):
                            lo = max(z + 1, q3 // p3 + 1)
                            if p3 * lo - q3 > lo * lo:
                                continue
                            left, right = lo, (2 * q3 - 1) // p3
                            while left < right:
                                mid = (left + right + 1) // 2
                                if p3 * mid - q3 <= mid * mid:
                                    left = mid
                                else:
                                    right = mid - 1
                            cap = left
                        solution, tests, width = two_tail(
                            Fraction(p3, q3), remaining | {z}, 1_000_000_000,
                            previous=z, hi_limit=cap)
                        if solution is None and tests < width:
                            raise RuntimeError("independent two-tail width limit reached")
                        tested_w += tests
                    if solution:
                        w, v = solution
                        found = sorted(remaining | {x, y, z, w, v})
                        assert len(found) == 88 and sum((Fraction(1, a) for a in found), Fraction()) == 5
                        check = subprocess.run(["python3", str(ROOT / "verify.py"), "5", *map(str, found)],
                                               text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                        assert check.returncode == 0, check.stdout
                        (ROOT / "logs/found88.log").write_text(
                            f"5 88 : {' '.join(map(str, found))}\n{check.stdout}")
                        report = {"status": "found_verified", "removed": removed,
                                  "replacement": [x, y, z, w, v], "denominators": found,
                                  "verification": check.stdout}
                        (ROOT / "logs/found88_verification.json").write_text(json.dumps(report, indent=2) + "\n")
                        print(json.dumps(report, indent=2))
                        return 0
        if sextuples % 1000 == 0:
            print("progress", sextuples, tested_x, tested_y, tested_z, tested_w,
                  unit_cases, unit_g, unit_h, flush=True)
    if expected:
        assert sextuples == expected, (sextuples, expected)
    print(json.dumps({"status": "completed_selected_subset_without_representation",
                      "sextuples": sextuples, "tested_x": tested_x, "tested_y": tested_y,
                      "tested_z": tested_z, "tested_w": tested_w, "unit_cases": unit_cases,
                      "unit_g": unit_g, "unit_h": unit_h, "solutions": 0,
                      "global_88_nonexistence_claimed": False}, indent=2))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
