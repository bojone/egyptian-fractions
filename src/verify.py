#!/usr/bin/env python3
import argparse
from fractions import Fraction

parser = argparse.ArgumentParser(description="Verify a distinct unit-fraction representation exactly")
parser.add_argument("n", type=int)
parser.add_argument("denominators", type=int, nargs="+")
args = parser.parse_args()

if args.n <= 0 or any(a <= 0 for a in args.denominators):
    parser.error("n and all denominators must be positive integers")
if len(set(args.denominators)) != len(args.denominators):
    parser.error("denominators are not distinct")

total = sum((Fraction(1, a) for a in args.denominators), Fraction())
print(f"terms: {len(args.denominators)}")
print(f"sum: {total}")
print(f"valid: {total == args.n}")
raise SystemExit(total != args.n)
