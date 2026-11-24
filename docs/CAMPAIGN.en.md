# Campaign Chronology, Time Accounting, and Current Progress

**[中文](CAMPAIGN.md) | English**

This chapter answers two different questions: **how long the exploration took** and **what has actually been proved**. All figures come from the included logs or the machine-readable [logs/campaign_summary.json](../logs/campaign_summary.json). No unsupported completion percentage or estimated completion date is offered.

## 1. Time conclusion

The available artifacts show:

- an early small-case log modified at **2026-11-09 05:27:14 UTC**;
- the safe31700 production snapshot dated **2026-11-24 07:58:00 UTC**;
- the latest included independent audit, safe31990, completed at **2026-11-24 09:18:13 UTC**.

The visible span of exploration, algorithm development, searching, corrections, and audits is therefore approximately **15.2 calendar days**, or “about 15 days” in round terms.

**This was not 15 days of continuously running one program at full capacity.** A file timestamp proves when an artifact existed or was updated, not the exact project start. The interval also included algorithm changes, withdrawn candidates, revalidation, resource migrations, pauses and resumes, scheduling changes, and independent audits. It cannot be converted into a precise net search duration.

## 2. Three meanings of “time”

### 2.1 Calendar span

Calendar span describes the distance between early and recent artifacts. It is useful for project history, not for estimating pure compute cost.

The roughly 15-day interval includes:

- symmetric-difference searches and independent small-value verification;
- two- and three-term tail algorithms and the hybrid CPU/GPU implementation;
- complete 85/86-term exclusions and partial 87-term coverage;
- collection and independent verification of the 89-term upper bound;
- withdrawn pruning, complete-fallback correction, and historical revalidation;
- local 88-term construction searches;
- repeated safe-coverage audits, independent full-content hashes, and uncovered-inventory export.

### 2.2 Time recorded for one coordinate or log

A `seconds` field records one coordinate under a particular implementation and scheduling environment. It may include device calls, host exact verification, fallback, and I/O. It is not pure GPU time and cannot simply be summed into project wall-clock time.

The same parent can take different times under different load, and concurrent tasks overlap. Naively adding all `seconds` values is therefore not a valid total runtime.

### 2.3 Production and audit window

The continuous file `safe_continuous_31000_31990.jsonl` supplies one complete reviewable window:

| Quantity | Start | End | Change |
|---|---:|---:|---:|
| Stage label | 31000 | 31990 | 100 record points |
| UTC time | 2026-11-24 04:52:57 | 2026-11-24 09:15:33 | About 4.38 hours |
| Accepted logs | 276835 | 277076 | +241 |
| Uncovered parents | 3118 | 3101 | -17 |

This window mixes production searching, owner acceptance, coverage computation, and independent review. It is not a pure-search throughput measurement. safe31700 lies within this window; the independent safe31990 audit finished at 09:18:13. **The 4.38-hour window must not be extrapolated into a completion estimate.**

## 3. Printed time for the small searches

The following are sums of the per-$`r`$ `seconds` values in `logs/small_cases.log`. They illustrate implementation scale, not total machine occupancy, verification, scheduling, or audit time.

| Target | Sum of printed seconds | Meaning |
|---|---:|---|
| $`n=3,k=11`$ | 0.000005742 | Harmonic and deletion-level exclusion |
| $`n=3,k=12`$ | 0.000287969 | Complete 12-term exclusion |
| $`n=3,k=13`$ | 0.000055153 | A 13-term representation found |
| $`n=4,k=31`$ | 0.002345255 | Complete 31-term exclusion |
| $`n=4,k=32`$ | 6.703523596 | Complete 32-term exclusion |
| $`n=4,k=33`$ | 2.399582102 | A 33-term representation found |
| $`n=5,k=83`$ | 0.000211193 | Complete 83-term exclusion |
| $`n=5,k=84`$ | 914.418441447 | Complete 84-term exclusion, about 15.24 minutes |

These figures use forced prefixes, symmetric differences, and exact pruning, not naive Cartesian-product enumeration. Other compiler options, tail algorithms, and audit methods can produce different timings. `make selftest` reruns the core cases, but these historical times are not performance promises.

## 4. Why long branches prevent simple estimates

Some coordinates are much more expensive than the small examples:

| Coordinate | Added-tail nodes $`y_{\rm nodes}`$ | Recorded seconds | Approximate hours | Result |
|---|---:|---:|---:|---|
| $`(4,77,79,85)`$ | 17387945695 | 168442 | 46.79 | Complete negative |
| $`(10,67,69,70)`$ | 21777794325 | 43997 | 12.22 | Complete negative |

The original logs are `logs/fixed87_depth3/r4_x77_y79_z85.log` and `logs/fixed86_depth3/r10_x67_y69_z70.log`. A single coordinate can require tens of hours, but that does not imply the same cost for others.

The recently closed parent $`(11,51,75)`$ illustrates variation within one parent:

| Child $`z`$ | $`x_{\rm nodes}`$ | $`y_{\rm nodes}`$ | Seconds | Result |
|---|---:|---:|---:|---|
| 76 | 495 | 2005983943 | 7978.24 | `no` |
| 77 | 165 | 842074549 | 3609.76 | `no` |
| 78 | 45 | 255763936 | 1037.30 | `no` |
| 79 | 9 | 42604355 | 164.145 | `no` |

All four use the accepted `cpu-gpu-three-v1` engine. Their times cannot simply be added as wall-clock time because tasks may run concurrently. Other parents also depend on denominator structure, tail bounds, factorization, candidate counts, and fallback paths.

## 5. Milestones

| UTC date | Milestone | Meaning |
|---|---|---|
| 2026-11-09 | Small exhaustive-search artifacts | Core evidence for $`S(3)=13`$ and $`S(4)=33`$ |
| 2026-11-10 | Complete pure-CPU 85-term coverage and small revalidation | Complete 85-term exclusion, supporting the lower bound |
| 2026-11-12 15:15 | Complete 86-term coverage and 118/118-child, 9/9-parent audit | Complete exclusion through 86 terms |
| 2026-11-16 | Hybrid production smoke representation | Invocation check only; not coverage |
| 2026-11-24 07:58 | safe31700 snapshot | 276997 accepted logs and 3109 uncovered parents |
| 2026-11-24 07:59 | safe31700 history and input-restoration checks | No violations or positives; four r4 coordinates pending |
| 2026-11-24 08:01 | safe31700 independent full-hash review | Partial coverage rebuilt without a coverage cache |
| 2026-11-24 08:04 | Export of all 3109 uncovered coordinates | Exact task boundary for subsequent work |
| 2026-11-24 09:18 | safe31990 independent full-hash review | 277076 accepted logs and 3101 uncovered parents |

The historical production environment recorded **8 GPU devices and 288 nonpaused compute slots**. These quantities describe one stage, not continuous full-load usage throughout the entire calendar span. No specific model is listed.

## 6. Progress at two checkpoints

The release retains safe31700 as the baseline for a complete uncovered-coordinate inventory and adds the later safe31990 independent audit. Coordinates from the two checkpoints must not be mixed into a fictitious single inventory.

| $`r`$ | safe31700 uncovered | safe31990 uncovered | Change |
|---|---:|---:|---:|
| 4 | 14 | 14 | 0 |
| 5 | 155 | 155 | 0 |
| 6 | 338 | 338 | 0 |
| 7 | 386 | 386 | 0 |
| 8 | 658 | 658 | 0 |
| 9 | 574 | 573 | -1 |
| 10 | 436 | 434 | -2 |
| 11 | 314 | 310 | -4 |
| 12 | 207 | 206 | -1 |
| 13 | 27 | 27 | 0 |
| 14–17 | 0 | 0 | 0 |
| **Total** | **3109** | **3101** | **-8** |

The safe31990 identifiers are:

- snapshot: `logs/production_safe31990_3101.json`;
- snapshot SHA-256: `795a331bcc41724b63766123b6eb8a90dae9d5571871cf3964e61a2c68845f16`;
- independent coverage: `logs/independent_safe31990_coverage.log`;
- independent coverage SHA-256: `5d7a7be463da590b31eeea2311b56ded0dd44d6451b943d6b3a8bbbabd8063eb`.

The safe31990 audit also records full content hashes, unique log paths, no coverage cache, and no positive representations. The complete **3101 uncovered coordinates** are now independently exported to [logs/uncovered_parents_safe31990.json](../logs/uncovered_parents_safe31990.json), with SHA-256 `26862c51260a3e627fab4760dbc05badebc97613aa424dd2b598a7678111ba07`; all ten scoped source sets have been checked. **It is a later independent coverage checkpoint, but this release does not splice its counts into the safe31700 coordinate list: each inventory belongs to its own checkpoint.** The latest complete historical-defect audit remains safe31700; these are different audit types.

## 7. What remains unresolved

### 87 terms

safe31990 still has 3101 uncovered parents, so it does not prove 87-term nonexistence. The following modular $`r=4`$ tails still lack terminal negative logs:
`$$ (4,73,84,85),\quad(4,76,81,84),\quad(4,76,82,83),\quad(4,76,83,84).$$`

Every parent must receive accepted exclusion evidence before the lower bound can advance from 87 to 88.

### 88 terms

The checked direct merges, three-to-two replacements, split/merge neighbors, base swaps, and designated exact construction families around the known 89-term representation produced no 88-term representation. **These are local exclusions, not a global 88-term proof.** Establishing $`S(5)=89`$ requires complete, separate exclusions of both 87 and 88 terms.

### 89 terms

An explicit 89-term representation has been independently verified by rational summation, so $`S(5)\le89`$. The construction comes from the public forum link preserved in the evidence. Its discovery time is not presented as this project's own search time, and it does not prove minimality.

## 8. Why no completion percentage or ETA is given

A reliable percentage or completion date cannot be inferred from the available records:

1. **Parents have unequal costs.** Some finish almost immediately; others require tens of hours, with substantial variation even within one parent.
2. **Parents are not candidate counts.** The number 3101 denotes uncovered tree nodes, not merely 3101 remaining candidate representations.
3. **Stage labels are not time.** An increment of 10 is an audit counter, not a fixed number of seconds or tasks.
4. **Scheduling and hardware changed.** Migrations, pauses and resumes, worker allocation, and priority changes affect throughput.
5. **The algorithm changed.** New pruning may accelerate later work, while invalid candidates require withdrawal and revalidation. Old node rates do not safely extrapolate.
6. **There is no complete resource-time ledger.** CPU hours, GPU hours, wall-clock time, and audit overhead cannot be separated exactly from the curated records.

Consequently, this release does not state a percentage complete or a number of days remaining. A future estimate would require the exact unclaimed-coordinate list, runtime distributions from comparable completed coordinates, actually available resources, and a fixed-algorithm benchmark.

## 9. Useful checks for readers

- Read the machine-readable chronology: [logs/campaign_summary.json](../logs/campaign_summary.json).
- Rerun the small upper and lower bounds with `make selftest`.
- Check both certified snapshots, coverage files, and hashes with `make audit`.
- Inspect the complete baseline inventory: [logs/uncovered_parents_safe31700.json](../logs/uncovered_parents_safe31700.json).
- Read the original long-coordinate and closure logs rather than relying only on aggregate timings.
- Check regular-file integrity with `sha256sum -c SHA256SUMS`.

The final mathematical statement remains
`$$S(1)=1,\quad S(2)=4,\quad S(3)=13,\quad S(4)=33,\qquad87\le S(5)\le89.$$`
The roughly 15-day calendar span documents the scale of exploration; it is not evidence that a determination of $`S(5)`$ is near.
