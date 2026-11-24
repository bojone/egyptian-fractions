# Local 88-Term Construction Experiments

**[中文](README.md) | English**

This directory contains local construction searches around the known 89-term representation. **They do not establish global 88-term nonexistence and do not change the bound $`87\le S(5)\le89`$.**

## Source files and purposes

- `audit89_pair_triple_merges.py`: all 3916 pairs and 113564 triples for direct merging, with duplicate denominators counted and rejected separately.
- `search88_base_pair_swaps.py`: replace every pair among the 83 base denominators by two distinct unit denominators, covering 3403 pairs.
- `search88_split_merge_neighbors.py`: one split followed by one merge, with 359 split candidates and 238 states.
- `search88_two_split_neighbors.py`: split two distinct original denominators and perform two merges, covering 60487 split-operation pairs.
- `search88_sequential_split_neighbors.py`: split an original denominator and then a newly created denominator, performing 7984 sequential splits.
- `search88_three_to_two_divisors.py`: factorization path and candidate-width analysis for three-to-two replacement.
- `search88_three_to_two_costed.py`: cost-ordered three-to-two candidates.
- `search88_local_replacements.py`: general two-term-tail solver and prioritized local replacement.
- `search88_four_to_three.py`, `search88_four_to_three_independent.py`, `search88_five_to_four_independent.py`, `search88_six_to_five_independent.py`, `search88_six_to_five_independent_resume.py`, and `search88_six_to_five_factor_tail.py`: additional restricted transformations.
- `search88_pair_driver.py`, `search88_variant_driver.py`, and `search88_walk.py`: scheduling, variant drivers, and random-walk references.
- `search88_final_triple_regression.py`: regression checks for the dedicated three-tail executable.
- `scheduler_snapshot.py`: process-snapshot helper for the original scheduler.
- `verify.py`: copy of the original independent representation verifier.

These files preserve the actual algorithms and report fields used in the experiments, rather than only a final “nothing found” statement.

## Runtime requirements and limitations

The pure-Python algorithms primarily use the standard library and the system `factor` command. Some specialized tail programs also require original production binaries, owner management, or scheduler processes, which are not all included. In particular, `search88_final_triple_regression.py` requires the original `search88_final_triple` executable. A missing binary must never be interpreted as a mathematical exclusion.

The relative `production/construct88/logs` link points to `../logs` for access to the formal evidence. Some scripts deliberately stop if their output already exists, so running directly in this directory would overwrite-risk archived evidence. **Always run experiments in a fresh empty workspace.**

## Reproduce in a fresh workspace

Run from the repository root to create an isolated workspace without changing the archived logs:

```bash
tmp=$(mktemp -d)
cp production/construct88/*.py "$tmp/"
mkdir -p "$tmp/logs"
cp logs/construct89_emath.json "$tmp/logs/"
cd "$tmp"

python3 audit89_pair_triple_merges.py
python3 search88_base_pair_swaps.py
python3 search88_split_merge_neighbors.py
python3 search88_two_split_neighbors.py
python3 search88_sequential_split_neighbors.py
```

Each script writes its report into the new workspace's `logs/`. Every candidate requires independent rational verification. A repeated denominator also needs an exact-sum check; a smaller term count alone is not a valid certificate.

`search88_three_to_two_costed.py`, `search88_local_replacements.py`, and the other variants can be copied into a fresh workspace in the same way. Scripts that require dedicated binaries or a scheduler need that original environment first and are not expected to complete a full search on this curated subset alone.

## Verification records

[logs/construct88_source_rechecks.json](../../logs/construct88_source_rechecks.json) summarizes fresh-workspace source reruns and checks:

- pair/triple counts and the 58 and 214 duplicate denominators;
- all 3403 base-pair replacements returning only the original set;
- 359/238 one-split candidates and states;
- 60487 two-split operation pairs and 25885 states;
- 7984 sequential splits and 7913 states;
- local-only scope and no new representation in every report.

Two additional standard-library checkers are `src/audit_merges89.py` and `src/audit_base_pairs89.py`, available through `make audit-merges`. Original local audit JSON files are `logs/search88_*.json`, `logs/audit89_pair_triple_merges.json`, and `logs/construct88_tail60_complete_audit.json`.

## Evidence boundary

These experiments exclude only named transformations or designated construction families. They do not prove global 88-term nonexistence and do not replace a complete 87-term exclusion. For broader exact searches, use `production/fixed_server` with the original complete tasks, owners, and coverage system.
