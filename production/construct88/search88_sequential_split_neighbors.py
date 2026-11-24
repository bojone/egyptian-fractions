#!/usr/bin/env python3
from fractions import Fraction
from itertools import combinations
from pathlib import Path
import datetime
import hashlib
import json
import subprocess
import time

from audit89_pair_triple_merges import merged_denominator
from search88_split_merge_neighbors import LARGE
from search88_three_to_two_divisors import factor_number, divisors
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
    output = ROOT / 'logs/search88_sequential_candidate88.json'
    if not output.exists():
        output.write_text(json.dumps(record, indent=2) + '\n')
    found = ROOT / 'logs/found88.log'
    if not found.exists():
        with found.open('x') as stream:
            stream.write('5 88 : ' + ' '.join(map(str, state)) + '\n')
    return record


def main():
    started = time.monotonic()
    source_name = 'logs/construct89_emath.json'
    source = json.loads((ROOT / source_name).read_text())
    initial = tuple(sorted(source['denominators']))
    original = frozenset(initial)
    assert source['valid'] and len(initial) == 89 and valid_state(initial)
    assert not (ROOT / 'logs/found87.log').exists() and not (ROOT / 'logs/found88.log').exists()
    first_states = {}
    split_count = 0
    for a in initial:
        remaining = original - {a}
        for b in divisors(factor_number(a * a)):
            if a in LARGE and b > 64:
                continue
            u, v = a + b, a * (a + b) // b
            if u == v or v.bit_length() > 512 or u in remaining or v in remaining:
                continue
            assert Fraction(1, a) == Fraction(1, u) + Fraction(1, v)
            split_count += 1
            state = tuple(sorted(remaining | {u, v}))
            first_states.setdefault(state, (a, (u, v)))
    assert split_count == 359 and len(first_states) == 238
    sequential_states = set()
    sequential_operations = 0
    universe = set(original)
    for state90, (original_a, first_pair) in sorted(first_states.items()):
        current = set(state90)
        for a in first_pair:
            remaining = current - {a}
            for b in range(1, 65):
                if (a * a) % b:
                    continue
                u, v = a + b, a * (a + b) // b
                if u == v or v.bit_length() > 512 or u in remaining or v in remaining:
                    continue
                sequential_operations += 1
                state91 = tuple(sorted(remaining | {u, v}))
                assert len(state91) == 91 and valid_state(state91)
                sequential_states.add(state91)
                universe.update((u, v))
    first_outputs = set()
    for a, b in combinations(sorted(universe), 2):
        merged = merged_denominator((a, b))
        if merged is not None:
            first_outputs.add(merged)
    merge_universe = universe | first_outputs
    partners = {}
    edge_count = 0
    for a, b in combinations(sorted(merge_universe), 2):
        merged = merged_denominator((a, b))
        if merged is None:
            continue
        edge_count += 1
        partners.setdefault(a, []).append((b, merged))
        partners.setdefault(b, []).append((a, merged))

    def merges(state):
        seen = set()
        for a in sorted(state):
            for b, merged in partners.get(a, []):
                pair = tuple(sorted((a, b)))
                key = (pair, merged)
                if key in seen or b not in state:
                    continue
                seen.add(key)
                if merged not in state - {a, b}:
                    yield pair, merged

    new89 = {}
    first_merge_applications = second_merge_applications = 0
    for state91 in sorted(sequential_states):
        current91 = set(state91)
        for pair1, merged1 in merges(current91):
            state90 = tuple(sorted((current91 - set(pair1)) | {merged1}))
            assert len(state90) == 90 and valid_state(state90)
            first_merge_applications += 1
            current90 = set(state90)
            for pair2, merged2 in merges(current90):
                state89 = tuple(sorted((current90 - set(pair2)) | {merged2}))
                assert len(state89) == 89 and valid_state(state89)
                second_merge_applications += 1
                if state89 != initial:
                    new89.setdefault(state89, {'two_split_state': state91,
                        'first_merge': {'removed': pair1, 'added': merged1},
                        'second_merge': {'removed': pair2, 'added': merged2}})
    representations = []
    pair_checks = triple_checks = 0
    for state89, provenance in sorted(new89.items()):
        current = set(state89)
        for pair in combinations(state89, 2):
            pair_checks += 1
            merged = merged_denominator(pair)
            if merged is None or merged in current - set(pair):
                continue
            candidate = tuple(sorted((current - set(pair)) | {merged}))
            representations.append(verify88(candidate, {'new89_provenance': provenance,
                'third_pair_merge': {'removed': pair, 'added': merged}}))
        for triple in combinations(state89, 3):
            triple_checks += 1
            merged = merged_denominator(triple)
            if merged is None or merged in current - set(triple):
                continue
            candidate = tuple(sorted((current - set(triple)) | {merged}))
            representations.append(verify88(candidate, {'new89_provenance': provenance,
                'triple_merge': {'removed': triple, 'added': merged}}))
    report = {'valid': True,
              'scope': 'One original split followed by one split of a newly created denominator with b<=64, then two arbitrary pair merges; new 89-term states are checked for direct pair-to-one and triple-to-one merges',
              'second_split_b_limit': 64,
              'new_denominator_bit_limit': 512,
              'two_distinct_original_splits_included': False,
              'initial_split_candidates': split_count,
              'unique_first_split_states': len(first_states),
              'sequential_split_operations': sequential_operations,
              'unique_sequential_two_split_states': len(sequential_states),
              'merge_universe_size': len(merge_universe),
              'precomputed_merge_edges': edge_count,
              'first_merge_applications': first_merge_applications,
              'second_merge_applications': second_merge_applications,
              'unique_new_89_states': len(new89),
              'direct_pair_merge_checks': pair_checks,
              'direct_triple_merge_checks': triple_checks,
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
    output = ROOT / 'logs/search88_sequential_split_neighbors.json'
    assert not output.exists()
    output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2), flush=True)


if __name__ == '__main__':
    main()
