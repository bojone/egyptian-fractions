#!/usr/bin/env python3
from pathlib import Path
from itertools import product
import json
import os
import subprocess
import sys
import tempfile
from math import gcd, prod

import sympy

root = Path(__file__).resolve().parent
p = int(sys.argv[1])
q = int(sys.argv[2])
previous = int(sys.argv[3]) if len(sys.argv) > 3 else 0
device = int(sys.argv[4]) if len(sys.argv) > 4 else 0
if p <= 0 or q <= 0 or previous < 0:
    raise SystemExit("p and q must be positive and previous must be nonnegative")
if gcd(p, q) != 1:
    raise SystemExit("p and q must be coprime")

q_factors = sorted(sympy.factorint(q).items())
p_factors = sorted(sympy.factorint(p).items())
if prod(prime ** exponent for prime, exponent in q_factors) != q:
    raise SystemExit("incomplete factorization of q; exact fallback required")
if prod(prime ** exponent for prime, exponent in p_factors) != p:
    raise SystemExit("incomplete factorization of p; exact fallback required")
if not p_factors:
    raise SystemExit("this factorization method requires p>1")
group_a = q_factors[:4]
group_b = q_factors[4:]
fitting_moduli = [prime ** exponent for prime, exponent in p_factors
                  if prime ** exponent < 2**64]
if not fitting_moduli:
    raise SystemExit("no prime-power factor of p fits uint64; exact fallback required")
lookup_modulus = max(fitting_moduli)
if any(2 * exponent >= 16 for _, exponent in group_b):
    raise SystemExit("factor exponent exceeds the GPU configuration; exact fallback required")
target = (-q) % lookup_modulus
residue_map = {}
for exponents in product(*[range(2 * exponent + 1) for _, exponent in group_a]):
    ua = 1
    for (prime, _), exponent in zip(group_a, exponents):
        ua *= prime ** exponent
    needed_b = target * pow(ua, -1, lookup_modulus) % lookup_modulus
    residue_map.setdefault(needed_b, []).append(ua)
keys = sorted(residue_map)
total = prod(2 * exponent + 1 for _, exponent in group_b)
if total >= 2**64:
    raise SystemExit("candidate count exceeds uint64")

print(f"p factors: {p_factors}")
print(f"q factors: {q_factors}")
print(f"group A combinations: {sum(map(len, residue_map.values()))}; lookup residues: {len(keys)}")
print(f"enumerating {total} group-B combinations on GPU {device}", flush=True)
env = dict(os.environ)
env["LD_LIBRARY_PATH"] = str(root / "compat")
temporary_root = root / "tmp"
temporary_root.mkdir(exist_ok=True)
with tempfile.TemporaryDirectory(prefix="two-tail-", dir=temporary_root) as directory:
    workspace = Path(directory)
    config = workspace / "config.txt"
    with config.open("w") as stream:
        stream.write(f"{len(group_b)} {lookup_modulus} {total} {len(keys)}\n")
        stream.write(' '.join(str(2 * exponent) for _, exponent in group_b) + "\n")
        for prime, _ in group_b:
            stream.write(' '.join(str(pow(prime, e, lookup_modulus)) for e in range(16)) + "\n")
        stream.write(' '.join(map(str, keys)) + "\n")

    indices_path = workspace / "indices.txt"
    process = subprocess.run(
        [str(root / os.environ.get("TWO_TAIL_BINARY", "two_tail")), str(device),
         str(config), str(indices_path)],
        env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    print(process.stdout, end="")
    if process.returncode != 0:
        raise SystemExit("GPU candidate enumeration failed")
    lines = indices_path.read_text().splitlines()
    count = int(lines[0])
    if count < 0 or count > 65536 or len(lines) != count + 1:
        raise SystemExit("invalid or truncated candidate buffer; exact fallback required")
    indices = [int(line) for line in lines[1:]]
    if any(index < 0 or index >= total for index in indices):
        raise SystemExit("candidate index outside the enumerated range")
    q_squared = q * q
    for index in indices:
        ub = 1
        for prime, exponent in group_b:
            e = index % (2 * exponent + 1)
            index //= 2 * exponent + 1
            ub *= prime ** e
        for ua in residue_map.get(ub % lookup_modulus, []):
            u = ua * ub
            if u % lookup_modulus != target or u >= q:
                continue
            v = q_squared // u
            if (u + q) % p or (v + q) % p:
                continue
            a = (u + q) // p
            b = (v + q) // p
            if a <= previous or b <= a:
                continue
            if a * p != u + q or b * p != v + q:
                continue
            result = {"a": a, "b": b, "u": u, "v": v, "group_B_candidates": total}
            print(json.dumps(result, indent=2))
            raise SystemExit(0)
    print(f"NO exact two-term representation; checked {total} group-B combinations and {count} matches")
