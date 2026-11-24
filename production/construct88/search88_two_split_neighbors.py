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
from search88_split_merge_neighbors import LARGE
from search88_three_to_two_divisors import factor_number, divisors

ROOT = Path(__file__).resolve().parent


def valid_state(state):
    return len(state) == len(set(state)) and sum((Fraction(1, a) for a in state), Fraction()) == 5


def verify_representation(state, provenance):
    state = tuple(sorted(state))
    assert valid_state(state)
    check = subprocess.run(['python3', 'verify.py', '5', *map(str, state)], cwd=ROOT,
                           text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True)
    assert 'valid: True' in check.stdout
    independent = subprocess.run(['python3', '-c',
        'from fractions import Fraction; import sys; '
        'v=list(map(int,sys.argv[1:])); assert len(v)==len(set(v)); '
        'print(sum((Fraction(1,a) for a in v),Fraction()))', *map(str, state)],
        cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True)
    assert independent.stdout.strip() == '5'
    record = {'terms': len(state), 'denominators': state, 'provenance': provenance,
              'verify_py': check.stdout, 'independent_fraction_sum': independent.stdout.strip()}
    terms = len(state)
    assert terms in (87, 88)
    candidate_path = ROOT / f'logs/search88_two_split_candidate{terms}.json'
    if not candidate_path.exists():
        candidate_path.write_text(json.dumps(record, indent=2) + '\n')
    with (ROOT / f'logs/found{terms}.log').open('x') as stream:
        stream.write(f'5 {terms} : ' + ' '.join(map(str, state)) + '\n')
    return record


def main():
    started = time.monotonic()
    source_name = 'logs/construct89_emath.json'
    source = json.loads((ROOT / source_name).read_text())
    initial = tuple(sorted(source['denominators']))
    original = frozenset(initial)
    assert source['valid'] and len(initial) == 89 and valid_state(initial)
    assert not (ROOT / 'logs/found87.log').exists() and not (ROOT / 'logs/found88.log').exists()
    options = {}
    for a in initial:
        current = []
        remaining = original - {a}
        for b in divisors(factor_number(a * a)):
            if a in LARGE and b > 64:
                continue
            u = a + b
            v = a * u // b
            if u == v or v.bit_length() > 512 or u in remaining or v in remaining:
                continue
            assert Fraction(1, a) == Fraction(1, u) + Fraction(1, v)
            current.append((u, v))
        options[a] = sorted(set(current))
    assert sum(map(len, options.values())) == 359
    first_states = {tuple(sorted((original - {a}) | set(pair)))
                    for a, pairs in options.items() for pair in pairs}
    assert len(first_states) == 238
    universe = original | {d for pairs in options.values() for pair in pairs for d in pair}
    first_edges = set()
    first_outputs = set()
    for a, b in combinations(sorted(universe), 2):
        merged = merged_denominator((a, b))
        if merged is not None:
            first_edges.add((a, b, merged))
            first_outputs.add(merged)
    merge_universe = universe | first_outputs
    edges = set()
    for a, b in combinations(sorted(merge_universe), 2):
        merged = merged_denominator((a, b))
        if merged is not None:
            edges.add((a, b, merged))
    assert first_edges <= edges
    partners = {}
    for a, b, merged in sorted(edges):
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
                if merged in state - {a, b}:
                    continue
                yield pair, merged

    seen91 = set()
    new89 = {}
    representations = []
    operation_pairs = 0
    first_merge_applications = 0
    second_merge_applications = 0
    pair_checks = 0
    triple_checks = 0
    for i, a in enumerate(initial):
        for b in initial[i + 1:]:
            if not options[a] or not options[b]:
                continue
            remaining = original - {a, b}
            for first in options[a]:
                for second in options[b]:
                    operation_pairs += 1
                    added = first + second
                    if len(set(added)) != 4:
                        continue
                    state91 = tuple(sorted(remaining | set(added)))
                    assert len(state91) == 91 and valid_state(state91)
                    if state91 in seen91:
                        continue
                    seen91.add(state91)
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
                            if state89 == initial or state89 in new89:
                                continue
                            provenance = {'split_original_denominators': [a, b],
                                          'splits': [first, second],
                                          'first_merge': {'removed': pair1, 'added': merged1},
                                          'second_merge': {'removed': pair2, 'added': merged2}}
                            new89[state89] = provenance
                    if len(seen91) % 5000 == 0:
                        print('two_split_states', len(seen91), 'new89', len(new89),
                              'seconds', time.monotonic() - started, flush=True)
    for state89, provenance in sorted(new89.items()):
        current = set(state89)
        for pair in combinations(state89, 2):
            pair_checks += 1
            merged = merged_denominator(pair)
            if merged is None or merged in current - set(pair):
                continue
            candidate = tuple(sorted((current - set(pair)) | {merged}))
            assert len(candidate) == 88
            representations.append(verify_representation(candidate,
                {'new89_provenance': provenance, 'third_pair_merge': {'removed': pair, 'added': merged}}))
        for triple in combinations(state89, 3):
            triple_checks += 1
            merged = merged_denominator(triple)
            if merged is None or merged in current - set(triple):
                continue
            candidate = tuple(sorted((current - set(triple)) | {merged}))
            assert len(candidate) == 88
            representations.append(verify_representation(candidate,
                {'new89_provenance': provenance, 'triple_merge': {'removed': triple, 'added': merged}}))
    report = {'valid': True,
              'scope': 'Two splits of distinct original denominators in the previously stated split domain, followed by two arbitrary pair merges; every resulting new 89-term state is checked for direct pair-to-one and triple-to-one merges',
              'split_domain': 'Same 359 split operations as logs/search88_split_merge_neighbors.json; splits of newly created denominators are not included',
              'sequential_split_new_denominators_included': False,
              'split_candidates': sum(map(len, options.values())),
              'unique_first_split_states': len(first_states),
              'split_operation_pairs': operation_pairs,
              'unique_two_split_states': len(seen91),
              'merge_universe_size': len(merge_universe),
              'precomputed_merge_edges': len(edges),
              'first_merge_applications': first_merge_applications,
              'second_merge_applications': second_merge_applications,
              'unique_new_89_states': len(new89),
              'direct_pair_merge_checks': pair_checks,
              'direct_triple_merge_checks': triple_checks,
              'representations': representations,
              'found_88': any(item['terms'] == 88 for item in representations),
              'found_87': any(item['terms'] == 87 for item in representations),
              'global_88_nonexistence_claimed': False,
              'new_89_examples': [{'denominators': state, 'provenance': new89[state]}
                                  for state in sorted(new89)[:10]],
              'source': source_name,
              'source_sha256': hashlib.sha256((ROOT / source_name).read_bytes()).hexdigest(),
              'program_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'seconds': time.monotonic() - started,
              'created_at': datetime.datetime.now(datetime.timezone.utc).isoformat()}
    output = ROOT / 'logs/search88_two_split_neighbors.json'
    assert not output.exists()
    output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2), flush=True)


if __name__ == '__main__':
    main()
