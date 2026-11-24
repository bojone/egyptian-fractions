# Evidence Index, Validation Levels, and Release Boundaries

**[中文](EVIDENCE.md) | English**

This release preserves curated, independently checkable evidence rather than duplicating a very large working directory. Each file below has a stated purpose and a stated limit. None of them is misrepresented as a determination of $`S(5)`$.

## 1. Result summary

The machine-readable starting point is [logs/current_result_summary.json](../logs/current_result_summary.json). It records:

- $`S(1)=1,S(2)=4,S(3)=13,S(4)=33`$;
- $`87\le S(5)\le89`$, with the exact value unresolved;
- 276997 accepted logs and 3109 uncovered parents at safe31700, with per-layer counts;
- paths and hashes for the snapshot, independent coverage, uncovered inventory, and 89-term construction;
- historical negative-log counts and four unfinished $`r=4`$ coordinates;
- no representation with 87 or 88 terms and no global exclusion claim.

`src/audit_release.py` independently checks the underlying fields rather than trusting this summary alone.

## 2. Representations and small-value evidence

| File | Contents | Independent check |
|---|---|---|
| [logs/construct89_emath.json](../logs/construct89_emath.json) | 89 denominators, construction definition, source link, verification fields | Reconstruct the set, check distinctness, and sum to 5 with `Fraction` |
| [logs/small_cases.log](../logs/small_cases.log) | Small searches for 3 and 4, plus 83/84-term records for 5 | Rerun core cases with `make selftest` |
| [logs/revalidated_small/](../logs/revalidated_small/) | Historical small-case revalidation output | Compare with a fresh local build |
| [src/bounds.py](../src/bounds.py) | Harmonic bounds and explicit representations of 3 and 4 | Direct exact rational computation |
| [src/verify.py](../src/verify.py) | General denominator-list verifier | `python3 src/verify.py N ...` |
| [logs/coverage85_cpu_only.log](../logs/coverage85_cpu_only.log) | Complete pure-CPU 85-term coverage | Check zero uncovered branches and no representation |
| [logs/r9_depth4_complete_coverage86.log](../logs/r9_depth4_complete_coverage86.log) | Final complete 86-term coverage | Check zero uncovered branches and no representation |
| [logs/r9_depth4_complete_audit.log](../logs/r9_depth4_complete_audit.log) | Final 86-term audit | Check 118/118 children, 9/9 parents, and no failures |

Complete exclusion of 12 terms for 3 and 31/32 terms for 4 gives $`S(3)\ge13`$ and $`S(4)\ge33`$; matching explicit representations establish equality. Complete exclusion of 83–86 terms for 5 gives $`S(5)\ge87`$, while smaller term counts are excluded harmonically.

These files do not contain complete 87- or 88-term coverage, so the same logic cannot be extended to minimality at 89.

## 3. Core safe31700 files

| File | Main contents |
|---|---|
| [logs/independent_safe31700_audit.json](../logs/independent_safe31700_audit.json) | Independent full-content-hash audit, owner summaries, no-cache coverage result |
| [logs/independent_safe31700_coverage.log](../logs/independent_safe31700_coverage.log) | Independently rebuilt layer and global coverage |
| [logs/production_safe31700_3109.json](../logs/production_safe31700_3109.json) | Production snapshot, layer counts, and audit links |
| [logs/goal87_safe31700.log](../logs/goal87_safe31700.log) | Production global coverage output |
| [logs/uncovered_parents_safe31700.json](../logs/uncovered_parents_safe31700.json) | All 3109 uncovered coordinates and ten scoped source hashes |
| [logs/uncovered_inventory_safe31700_driver.log](../logs/uncovered_inventory_safe31700_driver.log) | Inventory-generation result and its SHA-256 |

Important identifiers are:

- production snapshot SHA-256: `4b3deb581f3113b6792c21ab1f872d1a75042ce01251ff9e50013933c10eb161`;
- independent coverage SHA-256: `662f00c6942ba7138c468f50177eb1309c3f43937d6a83692b00ddc11f830038`;
- uncovered-inventory SHA-256: `babdf43f726ab5e057cc5295f27a616e3a6a7f4a4c9bc8653cf9f13b9aab37f7`.

The fields `full_content_hash_audit: true`, `coverage_cache_used: false`, and `independent_coverage_reused_after_completed_run: false` show that the audit recomputed content hashes and rebuilt coverage rather than reusing an earlier independent result.

Both `verified_safe_logs` and `unique_verified_log_paths` are 276997. Another 1672 concurrent logs were unaccepted at independent coverage and excluded. Return code 1 denotes partial coverage, not global nonexistence.

## 4. Ten scoped sources of the uncovered inventory

The inventory is not just a total. Every layer retains its original `uncovered_parent` coordinates, and the release auditor reconstructs and compares the sets:

| Layer | Count | Source file |
|---|---:|---|
| $`r=4`$ | 14 | `logs/remaining_r4_safe31700.log` |
| $`r=5`$ | 155 | `logs/remaining_r5_safe31700.log` |
| $`r=6`$ | 338 | `logs/r6_scoped_coverage_safe30060.log` |
| $`r=7`$ | 386 | `logs/r7_scoped_coverage_safe23500.log` |
| $`r=8`$ | 658 | `logs/r8_scoped_coverage_safe31680.log` |
| $`r=9`$ | 574 | `logs/r9_scoped_coverage_safe31310.log` |
| $`r=10`$ | 436 | `logs/r10_scoped_coverage_safe31530.log` |
| $`r=11`$ | 314 | `logs/r11_scoped_coverage_safe31700.log` |
| $`r=12`$ | 207 | `logs/r12_scoped_coverage_safe31640.log` |
| $`r=13`$ | 27 | `logs/remaining_r13_safe31700.log` |

Unchanged layers retain their most recent certified scoped logs; newly closed layers use newer logs. Their union contains 3109 distinct sorted coordinates. The inventory scope explicitly says **not a negative certificate**: these branches remain unexcluded.

safe31990 has a separate inventory of **3101 coordinates**: [logs/uncovered_parents_safe31990.json](../logs/uncovered_parents_safe31990.json), SHA-256 `26862c51260a3e627fab4760dbc05badebc97613aa424dd2b598a7678111ba07`. Layers r9, r10, r11, and r12 use the newer scoped logs at safe31940, safe31980, safe31970, and safe31990, respectively; unchanged layers retain the certified logs above. The two inventories are kept separate and are not mixed.

## 5. A complete recent closure example

[logs/r11_x51_y75_closure_safe31700.json](../logs/r11_x51_y75_closure_safe31700.json) certifies closure of $`(11,51,75)`$. Its required children are exactly $`z=76,77,78,79`$, with these original logs:

```text
logs/fixed87_depth3/r11_x51_y75_z76.log
logs/fixed87_depth3/r11_x51_y75_z77.log
logs/fixed87_depth3/r11_x51_y75_z78.log
logs/fixed87_depth3/r11_x51_y75_z79.log
```

For each log, the release audit checks the complete SHA-256, `result=no`, absence of `result=yes` and `MULTISLOT `, and an accepted engine label. It then verifies that the before-set has 315 parents, the after-set has 314, and their difference is exactly $`(11,51,75)`$.

Related files are:

- `logs/r11_scoped_coverage_safe31580.log`: before-set;
- `logs/r11_scoped_coverage_safe31700.log`: original after-set, SHA-256 `ba10beefff8e72e2516f9b1da6c724587ce5b4e10cd83063b87fa8542ee07814`;
- `logs/r11_scoped_coverage_safe31700_recheck.log`: independently rechecked set, SHA-256 `e4ecb17b7ce4931584126b9ee420c7066c4e4f7d3041da356955f890d2c062ef`;
- `logs/r11_closures_safe31700_recheck.json`: differential-program result;
- `logs/r11_new_closures_safe31700_summary.json`: closure summary and complete z-range.

The original and recheck files have different hashes but the same 314 uncovered coordinates. Concurrent counters can legitimately differ, so hash equality is not the right coverage comparison; set equality is required and was verified.

This example illustrates the evidence needed for one local closure. It does not prove any of the other 3109 branches.

## 6. Historical-audit summary

The original historical audit includes obsolete hardware identifiers and extensive binary metadata, so it is not copied verbatim. The curated release retains:

- [logs/history_safe31700_summary.json](../logs/history_safe31700_summary.json): counts, zero violations and positives, original audit SHA-256, fixed-input hash, and pending coordinates;
- [logs/two_tail_history_safe31700_validation.json](../logs/two_tail_history_safe31700_validation.json): input save/restore, archive ordering, counts, and r4 status.

The counts are:

| Target | Depth-three negative logs | Depth-four negative logs |
|---|---:|---:|
| 86 terms | 236879 | 206 |
| 87 terms | 397278 | 97 |

There are no violations or positive logs. The original historical-audit SHA-256 is `ce48b523f25d7c73d99d940666e58725b45a95c885945c071602d0bc91811362`, and the fixed-input SHA-256 is `cb42888b4e35c56dfa7a849645639c37e6ff9d20d21a5b488a36efa403953413`. The four modular $`r=4`$ coordinates still have no terminal negative result and must not be treated as excluded.

The historical audit addresses a particular old fallback defect. It does not replace coverage or retroactively certify every historical implementation. Original files were not modified; the release simply omits them and stores a mathematical summary.

## 7. Regression and smoke files

- [logs/two_tail_complete_regression.log](../logs/two_tail_complete_regression.log): positive/negative complete-fallback cases and fast-path agreement.
- [logs/two_tail_forced_fallback_summary.json](../logs/two_tail_forced_fallback_summary.json): positive and negative forced-GPU-failure/CPU-fallback summaries; original absolute paths are omitted and original log hashes retained.
- [logs/three_pair_ratio_host_test.log](../logs/three_pair_ratio_host_test.log) and [logs/three_pair_ratio_regression.log](../logs/three_pair_ratio_regression.log): original host regression output and 2404 GPU tasks with 655 positive cases.
- [logs/pruning_regression_summary.json](../logs/pruning_regression_summary.json): auxiliary three-tail pruning regression summary; performance profiles are not coverage.
- [logs/pigeonhole_product_fixed_regression.json](../logs/pigeonhole_product_fixed_regression.json): independent partition checks for the corrected product lower bound.
- [logs/product_max_server_smoke.json](../logs/product_max_server_smoke.json): basic hybrid smoke representation, explicitly marked `coverage_accepted: false`.

These files document implementation and regression scope, not global minimality by themselves.

## 8. What the release omits

The curated release does not include:

- all 276997 original negative logs or other historical logs;
- all owner reports, complete continuous production files, or caches;
- all historical binaries, specific hardware identifiers, or retired-process state;
- unaccepted candidates, timeouts, paused jobs, or performance-output collections.

Some archived JSON objects still contain relative references into the original complete-data environment. These references aid provenance; **they do not imply that every referenced file is included**. `src/audit_release.py` requires only the curated files listed here and does not pretend to inspect missing data.

Production programs such as `audit_safe_snapshot.py`, `coverage87_distinct_v1.py`, and `certify_coverage_delta.py` are intended for the original full-data environment. They require complete owner records, original logs, binaries, and some historical process information, and cannot perform a full recomputation on this curated subset. The relative `production/logs` link points only to the curated `logs/` directory, not to a complete production archive.

This boundary is deliberate: small cases can be rerun from scratch, curated evidence can be independently checked, and a full large-scale reproduction requires either the original complete evidence or new computation.

## 9. Checksums and recommended verification order

```bash
# 1. Check regular-file transfer integrity
sha256sum -c SHA256SUMS

# 2. Independently audit the curated evidence
make audit

# 3. Build and rerun the small searches
make selftest

# 4. Optionally build the hybrid implementation and run its smoke test
make production-smoke NVCC=/path/to/nvcc GPU_POOL=1
```

After editing documentation or source, regenerate the manifest with `make checksums`. Locally built binaries, temporary files, links, and `results/validation/` output are excluded. `make clean` never deletes the evidence.

## 10. Local 88-term construction evidence

The release now includes 17 local audit JSON files rather than only a prose summary. They cover designated base deletions, tail families, direct merges, three-to-two replacements, split/merge neighbors, base-pair swaps, and prioritized pair90 families. Every file explicitly sets `global_88_nonexistence_claimed: false`; none implies global nonexistence.

Two independent checks can be rerun directly:

```bash
python3 src/audit_merges89.py
python3 src/audit_base_pairs89.py
```

- [logs/merge89_independent_recheck.json](../logs/merge89_independent_recheck.json): all 3916 pairs and 113564 triples. The merged denominator is already present for 58 pairs and 214 triples, so exact summation no longer gives 5 and they must be rejected. No valid 88- or 87-term merge was found.
- [logs/base_pairs89_independent_recheck.json](../logs/base_pairs89_independent_recheck.json): all 3403 base pairs; every two-denominator solution returns to the original 89-term set, with no new 89-term state.
- [logs/audit89_pair_triple_merges.json](../logs/audit89_pair_triple_merges.json) and [logs/search88_base_pair_swaps_independent.json](../logs/search88_base_pair_swaps_independent.json): corresponding original local audits and independent reviews.

**A duplicate merged denominator is not a shortcut to a valid representation.** After merging, both distinctness and the exact sum must be checked. Deduplicating an already-present denominator changes the sum; a smaller term count alone is not a certificate.

`make audit-merges` reruns both independent programs and is included in `make check`. The other local families retain their original audit files; the packaged audit checks their validity flags, local scope, and empty representation sets, **without claiming to have rerun every historical construction search**. See [production/construct88/README.en.md](../production/construct88/README.en.md) for the experiment source and fresh-workspace protocol, and [logs/construct88_source_rechecks.json](../logs/construct88_source_rechecks.json) for the five source-rerun checks. The local evidence concerns only the named families and leaves the global statement at $`87\le S(5)\le89`$.

## 11. Precise statement of the result

The supported conclusion is
`$$S(1)=1,\quad S(2)=4,\quad S(3)=13,\quad S(4)=33,\qquad87\le S(5)\le89.$$`

safe31700 is partial 87-term coverage, not an 87-term exclusion; the local 88-term construction families are not global exclusions either. Proving $`S(5)=89`$ requires both global exclusions. Alternatively, a valid 87- or 88-term representation would improve the upper bound.
