#!/usr/bin/env python3
from fractions import Fraction
from itertools import islice
from pathlib import Path
import hashlib
import json
import math
import os
import re
import subprocess

from search88_five_to_four_independent import (
    unit_factors, unit_two_tail, two_tail, values, factor_number)

ROOT = Path(__file__).resolve().parent


def propagate(factors, x, common):
    merged = dict(factors)
    for prime, exponent in factor_number(x).items():
        merged[prime] = merged.get(prime, 0) + exponent
    for prime in list(merged):
        while common % prime == 0:
            common //= prime
            merged[prime] -= 1
    assert common == 1
    result = {prime: exponent for prime, exponent in merged.items() if exponent}
    return result


def native_two_tail(p, q, lo, hi, forbidden, factors):
    binary = ROOT / "search88_six_to_five_hybrid"
    expected_hash = os.environ["EXPECTED_NATIVE_SHA256"]
    assert hashlib.sha256(binary.read_bytes()).hexdigest() == expected_hash
    assert q <= (1 << 127) - 1 and hi - lo + 1 <= (1 << 64) - 1
    assert math.prod(prime ** exponent for prime, exponent in factors.items()) == q
    factor_text = ",".join(f"{prime}:{exponent}" for prime, exponent in sorted(factors.items()))
    command = [str(binary), str(p), str(q), str(lo), str(hi), factor_text,
               ",".join(map(str, sorted(forbidden)))]
    checked = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if checked.returncode not in (0, 1):
        raise RuntimeError(checked.stdout)
    method = re.search(r"method=(linear|factor|empty)", checked.stdout)
    assert method, checked.stdout
    width = hi - lo + 1
    if checked.returncode == 1:
        assert "result=no" in checked.stdout
        if method.group(1) == "linear":
            actual = int(re.search(r"linear_checks=(\d+)", checked.stdout).group(1))
            assert actual == width, checked.stdout
        elif method.group(1) == "factor":
            actual = int(re.search(r"factor_pairs=(\d+)", checked.stdout).group(1))
            expected = (math.prod(2 * exponent + 1 for exponent in factors.values()) - 1) // 2
            assert actual == expected, (checked.stdout, expected)
        return None, width, method.group(1)
    pair = tuple(map(int, re.search(r"candidate=(\d+),(\d+)", checked.stdout).groups()))
    assert lo <= pair[0] <= hi and pair[1] > pair[0]
    assert pair[0] not in forbidden and pair[1] not in forbidden
    assert Fraction(1, pair[0]) + Fraction(1, pair[1]) == Fraction(p, q)
    return pair, pair[0] - lo + 1, method.group(1)


def main():
    assert unit_factors(8, 9, 3, 3) == {3: 2}
    assert unit_two_tail(6, 7, 11, set(), factor_number(6))[0] == (7, 42)
    task_file = os.environ["TASK_FILE"]
    expected = int(os.environ["EXPECTED_TASKS"])
    skip = int(os.environ["SKIP_TASKS"])
    assert 0 < skip < expected
    prefix_log = os.environ["PREFIX_LOG"]
    prefix_lines = (ROOT / prefix_log).read_text().splitlines()
    checkpoint = [line for line in prefix_lines if line.startswith(f"progress {skip} ")]
    assert len(checkpoint) == 1, checkpoint
    prefix_fields = checkpoint[0].split()
    raw_counts = list(map(int, prefix_fields[1:]))
    if len(prefix_fields) == 9:
        prefix_counts = raw_counts
    elif len(prefix_fields) == 13:
        prefix_counts = raw_counts[:4] + [raw_counts[3] + raw_counts[4]] + raw_counts[5:8]
    else:
        raise AssertionError(prefix_fields)
    assert prefix_counts[0] == skip and len(prefix_counts) == 8
    assert not any("result=yes" in line for line in prefix_lines)
    file_skip = int(os.environ.get("TASK_FILE_SKIP", str(skip)))
    assert file_skip >= 0
    sextuples = skip
    tested_x = tested_y = tested_z = tested_w = covered_w = 0
    unit_cases = unit_g = unit_h = native_cases = 0
    native_counts = {"linear": 0, "factor": 0, "empty": 0}
    with (ROOT / task_file).open() as source:
        for line in islice(source, file_skip, None):
            fields = line.split()
            removed = tuple(map(int, fields[:-5]))
            p, q = map(int, fields[len(removed):len(removed) + 2])
            target = Fraction(p, q)
            assert target == sum((Fraction(1, a) for a in removed), Fraction())
            remaining = values - set(removed)
            q_factors = {int(item.split(":")[0]): int(item.split(":")[1])
                         for item in fields[-1].split(",")}
            assert math.prod(prime ** exponent for prime, exponent in q_factors.items()) == q
            sextuples += 1
            for x in range(q // p + 1, 5 * q // p + 1):
                if x in remaining:
                    continue
                tested_x += 1
                p1, q1 = p * x - q, q * x
                common = math.gcd(p1, q1)
                first_factors = propagate(q_factors, x, common)
                p1 //= common
                q1 //= common
                for y in range(max(x + 1, q1 // p1 + 1), 4 * q1 // p1 + 1):
                    if y in remaining:
                        continue
                    tested_y += 1
                    p2, q2 = p1 * y - q1, q1 * y
                    g2 = math.gcd(p2, q2)
                    second_factors = propagate(first_factors, y, g2)
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
                            lo = max(z + 1, q3 // p3 + 1)
                            hi = (2 * q3 - 1) // p3
                            if cap is not None:
                                hi = min(hi, cap)
                            width = max(0, hi - lo + 1)
                            if width > 1000000000:
                                third_factors = propagate(second_factors, z, g3)
                                solution, eliminated, method = native_two_tail(
                                    p3, q3, lo, hi, remaining | {z}, third_factors)
                                covered_w += eliminated
                                native_cases += 1
                                native_counts[method] += 1
                            else:
                                solution, tests, width = two_tail(
                                    Fraction(p3, q3), remaining | {z}, 1000000000,
                                    previous=z, hi_limit=cap)
                                if solution is None and tests < width:
                                    raise RuntimeError("independent two-tail width limit reached")
                                tested_w += tests
                        if solution:
                            w, v = solution
                            found = sorted(remaining | {x, y, z, w, v})
                            assert len(found) == 88
                            assert sum((Fraction(1, a) for a in found), Fraction()) == 5
                            check = subprocess.run(["python3", str(ROOT / "verify.py"), "5", *map(str, found)],
                                                   text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                            assert check.returncode == 0, check.stdout
                            (ROOT / "logs/found88.log").write_text(
                                f"5 88 : {' '.join(map(str, found))}\n{check.stdout}")
                            report = {"status": "found_verified", "removed": removed,
                                      "replacement": [x, y, z, w, v], "denominators": found,
                                      "verification": check.stdout}
                            (ROOT / "logs/found88_verification.json").write_text(json.dumps(report, indent=2) + "\n")
                            print(json.dumps(report, indent=2), flush=True)
                            return 0
            if sextuples % 1000 == 0:
                print("progress", sextuples, tested_x, tested_y, tested_z, tested_w,
                      covered_w, unit_cases, unit_g, unit_h, native_cases,
                      native_counts["linear"], native_counts["factor"], flush=True)
    assert sextuples == expected, (sextuples, expected)
    binary = ROOT / "search88_six_to_five_hybrid"
    print(json.dumps({"status": "completed_resumed_subset_without_representation",
                      "skipped_sextuples": skip, "sextuples": sextuples,
                      "tested_x": tested_x, "tested_y": tested_y, "tested_z": tested_z,
                      "tested_w": tested_w, "native_eliminated": covered_w,
                      "covered_w": tested_w + covered_w,
                      "unit_cases": unit_cases, "unit_g": unit_g, "unit_h": unit_h,
                      "native_cases": native_cases, "native_counts": native_counts,
                      "solutions": 0, "global_88_nonexistence_claimed": False,
                      "prefix_log": prefix_log, "prefix_counts": prefix_counts,
                      "native_binary_sha256": hashlib.sha256(binary.read_bytes()).hexdigest(),
                      "native_source_sha256": hashlib.sha256((ROOT / "search88_six_to_five_hybrid.cpp").read_bytes()).hexdigest()}, indent=2))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
