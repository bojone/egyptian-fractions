# Distinct Unit Fractions: Exact Searches, Proofs, and Curated Evidence

**[中文](README.md) | English**

**This entire project was completed autonomously by Kimi K3.1 Pro [thinkg: max] + Kimi-Code.**

For a positive integer $`n`$, consider
`$$n=\sum_{i=1}^{k}\frac1{a_i},\qquad a_i\in\mathbb Z_{>0},$$`
where all $`a_i`$ are pairwise distinct. The minimum possible $`k`$ is denoted by $`S(n)`$. The term $`1/1`$ is allowed. This repository provides executable source code, independent rational verifiers, exhaustive small-value searches, curated coverage evidence, and a precise account of what remains unresolved.

## Read the boundaries first

| Term | Proven value or bound | Evidence |
|---|---:|---|
| $`S(1)`$ | $`1`$ | Immediate |
| $`S(2)`$ | $`4`$ | Three terms sum to at most $`11/6<2`$ |
| $`S(3)`$ | $`13`$ | Exhaustive exclusion of 12 terms; explicit 13-term representation |
| $`S(4)`$ | $`33`$ | Exhaustive exclusion of 31 and 32 terms; explicit 33-term representation |
| $`S(5)`$ | $`87\le S(5)\le89`$ | Complete exclusion through 86 terms; verified 89-term representation |

**The exact value of $`S(5)`$ is still unknown.** The 87-term and 88-term cases must be settled separately. A representation improves the upper bound; a complete exclusion improves the lower bound. Excluding both is necessary to prove $`S(5)=89`$. A closed parent branch, a rejected heuristic family, or the end of a compute job is not a global minimality proof.

The frozen coverage checkpoint in this release is **safe31700**. It contains 276997 accepted negative logs and 3109 uncovered parents, so it does **not** prove that no 87-term representation exists. Start with [logs/current_result_summary.json](logs/current_result_summary.json). The subsequent **safe31990** independent audit reaches 277076 accepted logs and 3101 uncovered parents. For the calendar span, per-coordinate runtimes, latest layer counts, and why no completion estimate is justified, see [Campaign chronology and time accounting](docs/CAMPAIGN.en.md).

## Quick start

### Audit the curated evidence without a GPU

Only Python 3 and its standard library are required:

```bash
make audit
```

A successful run ends with:

```text
PASS: no specific hardware models or personal machine paths in the curated release
RELEASE_AUDIT_OK
```

The audit:

- recomputes the exact rational sums of the 13-term, 33-term, and 89-term representations;
- recomputes harmonic and symmetric-difference bounds;
- checks the complete 85/86-term coverage records and the final 86-term audit;
- checks safe31700 fields, snapshot digests, the count of 276997 accepted logs, and the 3109 uncovered parents;
- reconstructs every uncovered coordinate and compares all ten scoped source sets and their SHA-256 values;
- checks the historical-audit summary, input-restoration record, and four unfinished $`r=4`$ coordinates;
- inspects the four original negative logs for the latest $`r=11`$ closure and compares the parent sets before and after closure;
- rejects specific hardware models and personal machine paths in the curated files.

**This does not reread all 276997 original logs or rescan the 85/86/87-term search spaces.** It independently checks the curated evidence. Minimality still relies on the original algorithm, full historical evidence, and coverage derivation. See [docs/EVIDENCE.en.md](docs/EVIDENCE.en.md).

### Build with GMP and rerun the small cases

A C++17 compiler and GMP are required. The default linker setting is `GMP_LIBS=-l:libgmp.so.10`. For a different library layout, override it with `make selftest GMP_LIBS='-L/path/to/gmp/lib -lgmp'`; the local linker setting is not a cross-platform guarantee:

```bash
make selftest
```

This builds `src/symdiff_exact` and actually performs the following searches:

```text
PASS: no 11-term representation of 3 (complete r=1..2)
PASS: no 12-term representation of 3 (complete r=1..3)
PASS: independently verified a 13-term representation of 3
PASS: no 31-term representation of 4 (complete r=1..5)
PASS: no 32-term representation of 4 (complete r=1..7)
PASS: independently verified a 33-term representation of 4
PASS: no 83-term representation of 5 (complete r=1..3)
SELFTEST_OK
```

Thus the default test is not just a compilation check. It reruns the core upper- and lower-bound cases for $`S(3)`$ and $`S(4)`$, plus the complete deletion range for $`k=83,n=5`$. Every returned representation is checked again with exact rational arithmetic. Output is written to `results/validation/selftest.log`, which is ignored by version control.

Useful separate targets are:

```bash
make cpu           # Build only the GMP searcher
make audit         # Audit only the curated evidence
make audit-merges  # Independently recheck pair/triple merges and base-pair swaps
make check         # Evidence and local-merge audits + small searches
```

### Optional CUDA builds

Build the two-term-tail CUDA code and run the hybrid smoke test without starting a full search:

```bash
make gpu NVCC=/path/to/nvcc
make production-smoke NVCC=/path/to/nvcc GPU_POOL=1
```

The second command builds the hybrid CPU/GPU reference implementation and checks a 13-term representation of 3. `GPU_POOL` defaults to 8 and can be overridden for the available device count; `GPU_ARCH` defaults to `native`. The historical production environment used 8 GPU devices and 288 nonpaused compute slots. These quantities are records, not performance promises. **No specific CPU or GPU model is listed in this release.**

`make production` only compiles the hybrid implementation. `make production-smoke` additionally runs the smoke check. A compiler may warn that device `long double` is treated as `double`; those values are estimates only, while integer comparisons correct every endpoint.

### Integrity checks

```bash
make checksums
sha256sum -c SHA256SUMS
```

`SHA256SUMS` covers regular release files. Locally built binaries, temporary directories, and the relative `production/logs` link are excluded. `make clean` removes only locally built search binaries, never the evidence.

## Explicit representations

For the small values:
`$$1=\frac11,\qquad 2=\frac11+\frac12+\frac13+\frac16,$$`
`$$3=\sum_{j=1}^{10}\frac1j+\frac1{15}+\frac1{230}+\frac1{57960},$$`
`$$4=\sum_{j=1}^{28}\frac1j+\frac1{30}+\frac1{34}+\frac1{100}+\frac1{11934}+\frac1{14536368}.$$`

Let $`D`$ be
`$$\{1,\ldots,60\}\cup\{m\in[61,80]:m\text{ is composite}\}\cup\{81,84,88,90,92,96,98,99,100\},$$`
with 96 removed, so $`|D|=83`$. An 89-term representation is
`$$5=\sum_{d\in D}\frac1d+\frac1{82}+\frac1{162}+\frac1{76368}+\frac1{1821627808}+\frac1{323912070702990}+\frac1{1848221296482496}.$$`

The audit reconstructs this set and verifies 89 distinct denominators and an exact sum of 5. The source link and verification fields are preserved in [logs/construct89_emath.json](logs/construct89_emath.json). This proves an upper bound, not minimality.

To verify any other representation:

```bash
python3 src/verify.py N denominator1 denominator2 ...
```

## Outline of the minimality method

Write $`H_k=\sum_{j=1}^k1/j`$. Any sum of $`k`$ distinct unit fractions is at most $`H_k`$. More strongly, if
`$$H_{k+1}-\frac1j<n,$$`
then denominator $`j`$ is forced: without it, even every other available denominator is insufficient.

Fix $`k`$ and compare a candidate with $`\{1,\ldots,k\}`$. Put $`\delta=H_k-n\ge0`$. Delete $`r`$ denominators and add $`r`$ denominators greater than $`k`$. The deleted set $`R`$ and added set $`A`$ must satisfy
`$$\sum_{a\in R}\frac1a=\delta+\sum_{b\in A}\frac1b.$$`

The smallest possible deleted sum is $`H_k-H_{k-r}`$, and the largest possible added sum is $`H_{k+r}-H_k`$. Hence
`$$H_k-H_{k-r}>\delta+H_{k+r}-H_k$$`
rules out that $`r`$. This yields finite ranges: at most $`r=3`$ for 12 terms of 3; $`r=5,7`$ for 31 and 32 terms of 4; and $`r=3,9,13,16,19`$ for 83–87 terms of 5.

The GMP implementation enumerates deleted sets and performs increasing branch-and-bound on added denominators. Two-term tails use divisibility, while three-term tails use exact sufficient pruning. Floating point is only an estimate; integer comparisons correct endpoints. A positive GPU result requires an independent rational certificate, and overflow or numerical uncertainty falls back to exact search. See [docs/TECHNICAL.en.md](docs/TECHNICAL.en.md).

## Current $`k=87`$ layers

The frozen uncovered-parent counts are below. Here $`r`$ is the symmetric-difference deletion level. Levels $`r=1,2,3`$ and $`r\ge18`$ are complete; zero counts at levels 14–17 do not imply closure elsewhere.

| $`r`$ | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14–17 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Uncovered parents | 14 | 155 | 338 | 386 | 658 | 574 | 436 | 314 | 207 | 27 | 0 |

The total is 3109. Every coordinate is listed in [logs/uncovered_parents_safe31700.json](logs/uncovered_parents_safe31700.json), with SHA-256 `babdf43f726ab5e057cc5295f27a616e3a6a7f4a4c9bc8653cf9f13b9aab37f7`. These are **unfinished branches**, neither counterexamples nor proven exclusions. The subsequent **3101 coordinates** are separately listed in [logs/uncovered_parents_safe31990.json](logs/uncovered_parents_safe31990.json), SHA-256 `26862c51260a3e627fab4760dbc05badebc97613aa424dd2b598a7678111ba07`; each inventory belongs to its own checkpoint.

Four modular $`r=4`$ tail coordinates still have no terminal negative log:
`$$ (4,73,84,85),\quad(4,76,81,84),\quad(4,76,82,83),\quad(4,76,83,84).$$`

## Evidence levels and release scope

1. **Directly reproducible small proofs.** `make selftest` enumerates the core cases from scratch.
2. **Exact representation certificates.** Every upper-bound representation can be checked by exact rational summation.
3. **Complete historical 85/86-term coverage.** `logs/coverage85_cpu_only.log` and `logs/r9_depth4_complete_coverage86.log` report zero uncovered branches; the latter also has a 118/118-child and 9/9-parent final audit.
4. **safe31700 partial coverage.** The independent audit recomputed all then-accepted content hashes and rebuilt coverage. The release includes the audit, snapshot, layer lists, and selected closure evidence.
5. **Historical defect audits.** Pair/triple/quad candidates that omitted the candidate term $`1/a`$ and all derived coverage were withdrawn. An old complete-fallback residue-enumeration defect was corrected and audited separately. Neither audit replaces coverage.

This curated release omits raw work logs, retired-process state, historical binaries, and large caches. Some original files also identify specific hardware, so only mathematical summaries and original SHA-256 values are retained. **The packaged audit does not execute missing original logs and does not turn safe31700 partial coverage into global exclusion.**

## Layout

```text
egyptian-fractions/
├── README.md                 # Chinese overview
├── README.en.md              # English overview
├── LICENSE                   # MIT
├── CITATION.cff
├── Makefile                  # Build, audit, self-test, checksums
├── requirements.txt          # Needed only by the optional CUDA wrapper
├── SHA256SUMS                # Integrity manifest for regular files
├── src/                      # GMP search, CUDA tail, verification, self-test
├── production/               # Hybrid search and full-coverage reference code
├── docs/                     # Chinese and English algorithm and evidence guides
├── logs/                     # Curated representations, coverage, audits, uncovered list
│   ├── fixed87_depth3/       # Four original negative logs for the latest closure
│   └── revalidated_small/    # Historical small-case revalidation logs
└── results/validation/       # Local validation output (not versioned)
```

## Further reading and reproduction

- [docs/TECHNICAL.en.md](docs/TECHNICAL.en.md): algorithm, exact pruning, complete fallback, coverage definitions, and withdrawn candidates.
- [docs/EVIDENCE.en.md](docs/EVIDENCE.en.md): evidence files, hashes, counts, validation levels, and omissions.
- [production/README.en.md](production/README.en.md): hybrid implementation and the limits of full-production audits.
- Chinese versions are `README.md`, `docs/TECHNICAL.md`, `docs/EVIDENCE.md`, and `production/README.md`.

A full large-scale rerun requires the original complete dataset and substantial computation. `make check` is not a full reproduction. Generate fresh evidence in a new empty output directory rather than overwriting the archived files. Performance experiments, timeouts, candidate pruning, and unaccepted logs must not enter a proof.

## License

Distributed under the [MIT License](LICENSE). Citation metadata is in [CITATION.cff](CITATION.cff). Historical snapshots are omitted from this curated release, while the states, lists, representations, and closure logs used by the current audit are retained.
