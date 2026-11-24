#!/usr/bin/env python3
from fractions import Fraction
from itertools import combinations
from pathlib import Path
import datetime
import hashlib
import json
import math
import subprocess
import time

from audit89_pair_triple_merges import merged_denominator
from search88_two_split_neighbors import valid_state

ROOT = Path(__file__).resolve().parent


def verify88(state, provenance):
    state = tuple(sorted(state))
    assert len(state) == 88 and valid_state(state)
    check = subprocess.run(['python3', 'verify.py', '5', *map(str, state)], cwd=ROOT,
                           text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True)
    assert 'valid: True' in check.stdout
    independent = subprocess.run(['python3', '-c',
        'from fractions import Fraction; import sys; '
        'v=list(map(int,sys.argv[1:])); assert len(v)==88==len(set(v)); '
        'print(sum((Fraction(1,a) for a in v),Fraction()))', *map(str, state)],
        cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True)
    assert independent.stdout.strip() == '5'
    record = {'terms': 88, 'denominators': state, 'provenance': provenance,
              'verify_py': check.stdout, 'independent_fraction_sum': independent.stdout.strip()}
    output = ROOT / 'logs/search88_base_pair_candidate88.json'
    if not output.exists():
        output.write_text(json.dumps(record, indent=2) + '\n')
    found = ROOT / 'logs/found88.log'
    if not found.exists():
        with found.open('x') as stream:
            stream.write('5 88 : ' + ' '.join(map(str, state)) + '\n')
    return record


def two_denominator_solutions(target, remaining):
    p, q = target.numerator, target.denominator
    lo, hi = q // p + 1, (2 * q - 1) // p
    for a in range(lo, hi + 1):
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
            assert Fraction(1, a) + Fraction(1, b) == target
            yield a, b


def main():
    started = time.monotonic()
    source_name = 'logs/construct89_emath.json'
    source = json.loads((ROOT / source_name).read_text())
    initial = tuple(sorted(source['denominators']))
    base = tuple(sorted(source['base']))
    values = set(initial)
    assert source['valid'] and len(base) == 83 and valid_state(initial)
    assert list(two_denominator_solutions(Fraction(5, 6), set())) == [(2, 3)]
    assert not (ROOT / 'logs/found87.log').exists() and not (ROOT / 'logs/found88.log').exists()
    new89 = {}
    pair_checks = solution_count = original_solutions = 0
    candidate_checks = 0
    max_first = 0
    for removed in combinations(base, 2):
        pair_checks += 1
        a, b = removed
        target = Fraction(a + b, a * b)
        remaining = values - set(removed)
        for solution in two_denominator_solutions(target, remaining):
            solution_count += 1
            candidate_checks += 1
            max_first = max(max_first, solution[0])
            candidate = tuple(sorted(remaining | set(solution)))
            assert len(candidate) == 89 and valid_state(candidate)
            if candidate == initial:
                original_solutions += 1
                continue
            new89.setdefault(candidate, {'removed_base_pair': removed, 'added_pair': solution})
    representations = []
    direct_pair_checks = direct_triple_checks = 0
    for state, provenance in sorted(new89.items()):
        current = set(state)
        for pair in combinations(state, 2):
            direct_pair_checks += 1
            merged = merged_denominator(pair)
            if merged is None or merged in current - set(pair):
                continue
            candidate = tuple(sorted((current - set(pair)) | {merged}))
            representations.append(verify88(candidate, {'new89_provenance': provenance,
                'pair_merge': {'removed': pair, 'added': merged}}))
        for triple in combinations(state, 3):
            direct_triple_checks += 1
            merged = merged_denominator(triple)
            if merged is None or merged in current - set(triple):
                continue
            candidate = tuple(sorted((current - set(triple)) | {merged}))
            representations.append(verify88(candidate, {'new89_provenance': provenance,
                'triple_merge': {'removed': triple, 'added': merged}}))
    report = {'valid': True,
              'scope': 'Every pair of the 83 base denominators is replaced by any two distinct unit denominators, using a complete finite two-denominator search; every new 89-term state is checked for direct pair-to-one and triple-to-one merges',
              'base_pairs': pair_checks, 'expected_base_pairs': math.comb(83, 2),
              'complete_two_denominator_search': True,
              'two_denominator_solutions': solution_count,
              'candidate_checks': candidate_checks,
              'solutions_returning_to_original': original_solutions,
              'max_first_new_denominator_observed': max_first,
              'unique_new_89_states': len(new89),
              'direct_pair_merge_checks': direct_pair_checks,
              'direct_triple_merge_checks': direct_triple_checks,
              'representations': representations,
              'found_88': bool(representations), 'found_87': False,
              'global_88_nonexistence_claimed': False,
              'new_89_examples': [{'denominators': state, 'provenance': new89[state]}
                                  for state in sorted(new89)[:10]],
              'source': source_name,
              'source_sha256': hashlib.sha256((ROOT / source_name).read_bytes()).hexdigest(),
              'program_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'seconds': time.monotonic() - started,
              'created_at': datetime.datetime.now(datetime.timezone.utc).isoformat()}
    assert pair_checks == math.comb(83, 2)
    output = ROOT / 'logs/search88_base_pair_swaps.json'
    assert not output.exists()
    output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2), flush=True)


if __name__ == '__main__':
    main()
