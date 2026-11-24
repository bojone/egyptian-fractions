#!/usr/bin/env python3
from fractions import Fraction
import argparse
import math
import random
import time

from search88_five_to_four_independent import two_tail
from search88_three_to_two_divisors import factor_number, divisors


def factor_two_tail(target, remaining=frozenset(), previous=0, hi_limit=None, factors=None):
    p, q = target.numerator, target.denominator
    assert p > 0 and math.gcd(p, q) == 1
    lo = max(previous + 1, q // p + 1)
    hi = (2 * q - 1) // p
    if hi_limit is not None:
        hi = min(hi, hi_limit)
    if hi < lo:
        return None, 0, 0
    square = q * q
    checked = 0
    if factors is None:
        factors = factor_number(q)
    assert math.prod(prime ** exponent for prime, exponent in factors.items()) == q
    for divisor in divisors({prime: 2 * exponent
                             for prime, exponent in factors.items()}):
        if divisor >= q:
            break
        checked += 1
        if (divisor + q) % p:
            continue
        other = square // divisor
        if (other + q) % p:
            continue
        first = (divisor + q) // p
        second = (other + q) // p
        if not lo <= first <= hi or second <= first:
            continue
        if first in remaining or second in remaining:
            continue
        assert Fraction(1, first) + Fraction(1, second) == target
        return (first, second), checked, hi - lo + 1
    return None, checked, hi - lo + 1


def selftest():
    answer, _, _ = factor_two_tail(Fraction(1, 6), previous=6)
    assert answer == (7, 42)
    answer, _, _ = factor_two_tail(Fraction(13, 12))
    assert answer and Fraction(1, answer[0]) + Fraction(1, answer[1]) == Fraction(13, 12)
    rng = random.Random(6505)
    cases = 0
    positive = 0
    old_tests = 0
    divisor_pairs = 0
    for p in range(1, 11):
        for q in range(max(2, p), 61):
            if math.gcd(p, q) != 1:
                continue
            target = Fraction(p, q)
            previous = rng.randrange(0, 15)
            old, tests, width = two_tail(target, set(), 1_000_000, previous=previous)
            new, pairs, new_width = factor_two_tail(target, previous=previous)
            assert tests <= width and new_width == width
            assert (old is None) == (new is None), (target, previous, old, new)
            if new:
                assert sum((Fraction(1, a) for a in new), Fraction()) == target
                assert new[0] > previous and new[1] > new[0]
                positive += 1
            cases += 1
            old_tests += tests
            divisor_pairs += pairs
    for _ in range(100):
        p = rng.randrange(1, 200)
        q = rng.randrange(p + 1, 5000)
        if math.gcd(p, q) != 1:
            continue
        target = Fraction(p, q)
        previous = rng.randrange(0, 100)
        forbidden = set(range(previous + 1, previous + 20, 3))
        old, tests, width = two_tail(target, forbidden, 1_000_000, previous=previous)
        new, pairs, _ = factor_two_tail(target, forbidden, previous=previous)
        assert tests <= width
        assert (old is None) == (new is None), (target, previous, old, new)
        if new:
            assert new[0] not in forbidden and new[1] not in forbidden
            assert sum((Fraction(1, a) for a in new), Fraction()) == target
            positive += 1
        cases += 1
        old_tests += tests
        divisor_pairs += pairs
    return {"cases": cases, "positive": positive, "old_tests": old_tests,
            "divisor_pairs": divisor_pairs}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample", type=int, default=0)
    args = parser.parse_args()
    started = time.monotonic()
    result = selftest()
    print({"selftest": result, "seconds": time.monotonic() - started}, flush=True)
    if not args.sample:
        return
    from search88_five_to_four_independent import values
    from pathlib import Path

    added_factor_cache = {}

    def added_factors(value):
        if value not in added_factor_cache:
            if value > 1000000:
                added_factor_cache[value] = factor_number(value)
            else:
                remaining = value
                result = {}
                prime = 2
                while prime * prime <= remaining:
                    while remaining % prime == 0:
                        result[prime] = result.get(prime, 0) + 1
                        remaining //= prime
                    prime += 1 if prime == 2 else 2
                if remaining > 1:
                    result[remaining] = result.get(remaining, 0) + 1
                added_factor_cache[value] = result
        return added_factor_cache[value]

    def propagate(p, q, x, common, factors):
        merged = dict(factors)
        for prime, exponent in added_factors(x).items():
            merged[prime] = merged.get(prime, 0) + exponent
        for prime in list(merged):
            while common % prime == 0:
                common //= prime
                merged[prime] -= 1
        assert common == 1
        merged = {prime: exponent for prime, exponent in merged.items() if exponent}
        assert math.prod(prime ** exponent for prime, exponent in merged.items()) == q * x // math.gcd(p * x - q, q * x)
        return merged

    compared = 0
    third_terms = 0
    old_tests = 0
    divisor_pairs = 0
    positive = 0
    factor_seconds = 0.0
    old_seconds = 0.0
    for line in Path("logs/search88_six_to_five_factor_tasks.txt").read_text().splitlines()[:args.sample]:
        fields = line.split()
        removed = tuple(map(int, fields[:-5]))
        p, q = map(int, fields[len(removed):len(removed) + 2])
        target = Fraction(p, q)
        remaining = values - set(removed)
        q_factors = {int(item.split(":")[0]): int(item.split(":")[1])
                     for item in fields[-1].split(",")}
        assert math.prod(prime ** exponent for prime, exponent in q_factors.items()) == q
        for x in range(q // p + 1, 5 * q // p + 1):
            if x in remaining:
                continue
            p1, q1 = p * x - q, q * x
            g1 = math.gcd(p1, q1)
            first_factors = propagate(p, q, x, g1, q_factors)
            p1 //= g1
            q1 //= g1
            for y in range(max(x + 1, q1 // p1 + 1), 4 * q1 // p1 + 1):
                if y in remaining:
                    continue
                p2, q2 = p1 * y - q1, q1 * y
                g2 = math.gcd(p2, q2)
                second_factors = propagate(p1, q1, y, g2, first_factors)
                p2 //= g2
                q2 //= g2
                for z in range(max(y + 1, q2 // p2 + 1), 3 * q2 // p2 + 1):
                    third_terms += 1
                    if z in remaining:
                        continue
                    p3, q3 = p2 * z - q2, q2 * z
                    g3 = math.gcd(p3, q3)
                    third_factors = propagate(p2, q2, z, g3, second_factors)
                    target3 = Fraction(p3 // g3, q3 // g3)
                    cap = None
                    if target3.numerator > 4 * (target3.denominator // target3.numerator):
                        lo = max(z + 1, target3.denominator // target3.numerator + 1)
                        if target3.numerator * lo - target3.denominator > lo * lo:
                            continue
                        left, right = lo, (2 * target3.denominator - 1) // target3.numerator
                        while left < right:
                            mid = (left + right + 1) // 2
                            if target3.numerator * mid - target3.denominator <= mid * mid:
                                left = mid
                            else:
                                right = mid - 1
                        cap = left
                    before = time.monotonic()
                    old, tests, width = two_tail(target3, remaining | {z}, 1_000_000_000,
                                                 previous=z, hi_limit=cap)
                    old_seconds += time.monotonic() - before
                    assert tests <= width
                    before = time.monotonic()
                    new, pairs, _ = factor_two_tail(target3, remaining | {z},
                                                   previous=z, hi_limit=cap,
                                                   factors=third_factors)
                    factor_seconds += time.monotonic() - before
                    assert (old is None) == (new is None), (target3, z, old, new)
                    old_tests += tests
                    divisor_pairs += pairs
                    positive += new is not None
                    compared += 1
        print({"sample_sextuples": args.sample, "tail_cases": compared,
               "third_terms": third_terms, "old_tests": old_tests,
               "divisor_pairs": divisor_pairs, "positive": positive,
               "old_seconds": old_seconds, "factor_seconds": factor_seconds}, flush=True)


if __name__ == "__main__":
    main()
