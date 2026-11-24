#!/usr/bin/env python3
import math
import re
import subprocess

cases = solutions = 0
mismatches = []
for q in range(2, 61):
    for p in range(1, q):
        if math.gcd(p, q) != 1:
            continue
        lo = q // p + 1
        hi = (2 * q - 1) // p
        if hi < lo:
            continue
        expected = set()
        for a in range(lo, hi + 1):
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
            if b > a:
                expected.add((a, b))
        run = subprocess.run(["./search88_final_triple", str(p), str(q)],
                             text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        actual = {tuple(map(int, match)) for match in
                  re.findall(r"candidate=(\d+),(\d+)", run.stdout)}
        cases += 1
        solutions += len(expected)
        if run.returncode != 1 or actual != expected:
            mismatches.append((p, q, run.returncode, sorted(expected - actual),
                               sorted(actual - expected), run.stdout[-300:]))
print("cases", cases, "solutions", solutions, "mismatches", len(mismatches))
for item in mismatches[:10]:
    print(item)
assert not mismatches
