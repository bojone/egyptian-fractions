# Algorithm and Proof Details

**[中文](TECHNICAL.md) | English**

This document explains why the searches are finite, how pruning preserves completeness, which negative logs enter coverage, and why safe31700 is not a determination of $`S(5)`$. Representations, complete exclusions, and uncovered branches are three different things.

## 1. Harmonic bounds and forced prefixes

Let
$$H_k=\sum_{j=1}^k\frac1j.$$
A sum of $`k`$ distinct unit fractions is at most $`H_k`$, so no representation exists when $`H_k<n`$. In particular, three distinct unit fractions sum to at most $`1+1/2+1/3=11/6<2`$, hence $`S(2)=4`$.

In particular,
$$H_{10}=2.928968\ldots<3<H_{11}=3.019877\ldots.$$
Thus the harmonic bound alone directly excludes only 10 terms; the 11- and 12-term cases still require exhaustive search. It would be incorrect to write $`H_{11}<3`$.

If
$$H_{k+1}-\frac1j<n,$$
then $`j`$ is forced: even taking every other denominator in $`\{1,\ldots,k+1\}\setminus\{j\}`$ is insufficient. `src/symdiff.cpp` computes this forced prefix length $`p`$ and does not enumerate those denominators again.

This condition is necessary, not sufficient. The remaining deleted set and added tail must still be solved exactly.

## 2. Symmetric difference makes the problem finite

Fix $`k`$ and compare a candidate with $`\{1,\ldots,k\}`$. Delete $`r`$ denominators and add $`r`$ denominators greater than $`k`$. Define
$$\delta=H_k-n\ge0,\qquad R=\text{deleted set},\qquad A=\text{added set}.$$
The necessary and sufficient balance is
$$\sum_{a\in R}\frac1a=\delta+\sum_{b\in A}\frac1b.$$

Forced-prefix denominators cannot be deleted, so $`r\le k-p`$. For fixed $`r`$, the minimum deleted sum and maximum added sum are
$$m_r=H_k-H_{k-r},\qquad M_r=H_{k+r}-H_k.$$
If $`m_r>\delta+M_r`$, that level is impossible. Since $`m_r`$ increases and $`M_r`$ decreases, the first such $`r`$ also rules out every later level.

| $`n,k`$ | Forced prefix $`p`$ | Maximum allowed $`r`$ |
|---|---:|---:|
| 3, 12 | 5 | 3 |
| 4, 31 | 17 | 5 |
| 4, 32 | 11 | 7 |
| 5, 83 | 71 | 3 |
| 5, 84 | 38 | 9 |
| 5, 85 | 26 | 13 |
| 5, 86 | 20 | 16 |
| 5, 87 | 16 | 19 |

`src/bounds.py` recomputes these bounds with `Fraction`, and `src/audit_release.py` checks them independently. Symmetric difference is not an approximation: enumerating every deleted set at every allowed level and then solving the added tail covers every representation with at most $`k`$ distinct terms.

## 3. Branch-and-bound on deleted sets

Let $`S`$ be the current deleted sum, `left` the number still to delete, and $`A_r=\delta+(H_{k+r}-H_k)`$. Two safe prunings are used:

- if $`S`$ plus the smallest possible remaining deleted sum exceeds $`A_r`$, there is no solution;
- if $`S`$ plus the largest possible remaining deleted sum is at most $`\delta`$, the required positive residual cannot be obtained.

The next deleted denominator is strictly increasing. A candidate is skipped if the new sum exceeds $`A_r`$. Only after reaching the prescribed deletion count does the code construct the added tail. Thus the bounds reject only impossible branches.

## 4. Exact search on added tails

### 4.1 Integer arithmetic and first-denominator bounds

Rational numbers are stored as GMP integer numerators and denominators, with reduction after each operation. `integer_bound` computes an integer upper bound for the first denominator when $`r`$ terms remain. Large-integer overflow is never silently truncated.

For a first denominator $`a`$, the implementation also checks
$$p\,a(a+1)\le q(ra+1),$$
which is equivalent to
$$\frac pa\le\frac ra-\frac1{a(a+1)}=\frac{ra+1}{a(a+1)}.$$
This necessary condition comes from the next term $`1/(a+1)`$ alone; it is not presented as a complete bound. Exact enumeration or a tail solver still follows.

### 4.2 One- and two-term tails

A one-term tail is accepted only when the numerator is 1 and the denominator exceeds the previous one.

A two-term tail requires $`p/q=1/a+1/b`$ with $`b>a`$. The ordinary path enumerates increasing $`a`$ and tests whether $`p/q-1/a`$ is a unit fraction with the required order. Another sufficient test uses divisibility and quadratic conditions on $`D=pa-q`$, all evaluated in integers.

### 4.3 Complete factorization fallback

With $`\gcd(p,q)=1`$, define
$$g=\gcd(a,q),\quad s=q/g,\quad c=a/g,\quad D=pa-q,\quad h=D/g.$$
From $`D\mid aq`$ and coprimality,
$$h\mid g,\qquad h<s,\qquad pc=s+h,\qquad b=gcs/h.$$
The complete fallback enumerates every divisor $`g`$ of $`q`$ and every positive divisor $`h`$ of $`g`$, then tests $`h<s`$, $`h\equiv-s\pmod p`$, and the final integer identity. It does not test only the least residue.

When $`p^2>2q`$, we have $`a<2q/p<p`$, so $`g<p`$ and $`h<p`$. The least nonnegative residue then covers every possibility, and the fast path remains complete. The old `full=True` fallback incorrectly used the least residue without this condition. The correction changes only the complete fallback; old logs are not retroactively accepted merely because the new code passes regression.

[logs/two_tail_complete_regression.log](../logs/two_tail_complete_regression.log) records 3162 positive cases, 78730 negative cases, 79209 identical fast-path cases, and zero failures. The independent pure-CPU exclusion at $`k=85`$ does not depend on this Python fallback.

### 4.4 CUDA two-term tail

`src/two_tail.py` factors $`p,q`$, builds congruence lookup tables from factor groups, and calls `src/two_tail`. The CUDA program enumerates the other factor group and returns candidate indices. The host reconstructs candidates and checks
$$a=(u+q)/p,\qquad b=(v+q)/p,\qquad b>a,$$
plus every integer divisibility requirement. Truncated buffers, abnormal exits, or incomplete factorization cause failure rather than a negative conclusion.

The GPU only screens candidates. Final acceptance uses exact integer verification, so it would be incorrect to claim that every branch was proved by the GPU.

## 5. Exact sufficient pruning for three-term tails

For target $`p/q`$ and first denominator $`a`$, put $`D=pa-q`$. Write the reduced remainder after subtracting $`1/a`$ as
$$\frac{D/\gamma}{aq/\gamma},\qquad \gamma\le a^2.$$
The first possible second denominator is
$$b_0=\max\left(a+1,\left\lfloor\frac{aq}{D}\right\rfloor+1\right).$$
If
$$D^2>4a^3q,\qquad Db_0-aq>a^2b_0^2,$$
then the two-term tail already fails at $`b_0`$. The first inequality supplies the monotone-prefix property and rules out all later $`b`$. Since $`\gamma\le a^2`$, these stronger conditions are sufficient for exclusion.

Failure of the conditions causes no pruning, and arithmetic overflow returns to the original exact search. Floating point estimates integer quotients only; exact integer comparisons correct endpoints. [logs/pruning_regression_summary.json](../logs/pruning_regression_summary.json) summarizes 20736 wide cases with no failure, 54039 first-denominator cases with 1150 prunes and 21475 positive first terms preserved, and 2404 small GPU tasks with no failure. These support the implementation; performance counts are not formal exclusion counts.

## 6. Hybrid CPU/GPU implementation

The `production/` reference implementation contains:

- `symdiff.cpp`, which includes `src/symdiff.cpp` rather than maintaining a second core implementation;
- `fixed.cpp` for fixed deleted prefixes;
- `fixed_server.cpp` for reading coordinate jobs and printing `JOB_END`;
- `gpu_hybrid.hpp` and `gpu_three_hybrid.hpp` for two- and three-term batch organization;
- `gpu_two_batch.cu`, `gpu_three_batch.cu`, and `gpu_exact_batch.cu` for device searches;
- host GMP verification of positive results and exact CPU fallback on device failure or overflow.

The historical production environment recorded 8 GPU devices and 288 nonpaused compute slots, but the CPU/GPU allocation varied by layer and time. No specific model is listed, and all historical layers $`r=7`$ through $`r=12`$ are not attributed to a single device.

`make production-smoke` was actually built and run in this release directory and returned a 13-term representation. A smoke pass establishes basic build and invocation correctness, not complete coverage.

## 7. Accepting negative evidence

A log is not a proof merely because it contains `result=no`. Production acceptance requires:

1. a unique coordinate and path, with content SHA-256 matching the owner record;
2. terminal `result=no` and no `result=yes` or `MULTISLOT `;
3. an engine among `gpu-exact-block-v3`, `cpu-gpu-two-v1`, `cpu-gpu-three-v1`, `depth3-block-v3`, or `depth4-block-v3`;
4. absence from the pending set and a valid owner report;
5. independent rational verification of any positive result;
6. no coverage contribution from timeouts, pauses, candidate engines, incomplete jobs, truncated buffers, or unaccepted concurrent logs.

Withdrawn labels include `cpu-gpu-pair-candidate-v1`, `cpu-gpu-triple-candidate-v1`, `cpu-gpu-quad-candidate-v1`, and `gpu-exact-wide`. Retired evidence enters a recovered owner mapping only after revalidation; retirement does not mean completion.

A cache may reuse only an identical validated record identity and content hash. Independent review disables coverage caching, rereads all then-accepted logs, and rebuilds coverage. A cache hit is not an independent recomputation.

## 8. Withdrawn bounds and historical fallback audits

Early pair/triple/quad candidate bounds omitted the candidate term $`1/a`$, causing invalid pruning. All negative logs with those labels and all derived coverage were removed from safe coverage. Old $`r=13`$ and $`r=14`$ closure totals were not inherited without proof. Safe coverage was then rebuilt using only accepted engines.

The historical fallback also relied on an invalid least-residue assumption. Static history audits look for mandatory fallback markers in old mixed-engine negative logs to assess that particular defect. They do not prove the absence of every other implementation defect, and they do not replace parent coverage. Mixed paths require a rerun or proof that the risky path never executed.

This history explains the conservative acceptance rule of safe labels, full content hashes, and independent coverage rather than selecting whichever log has more nodes or a longer runtime.

## 9. Parent coverage and global exclusion

For $`k=87`$, a depth-three parent is $`(r,x,y)`$, with children $`(r,x,y,z)`$ satisfying
$$z=y+1,\ldots,87-r+3.$$
It has $`87-r-y+3`$ required children. For example, $`(11,51,75)`$ requires negative results at $`z=76,77,78,79`$ before it can be removed from the uncovered set.

`coverage87_distinct_v1.py` checks root exclusions, secondary exclusions, and depth-three children. Scoped logs print each `uncovered_parent r x y`. A layer is closed only when all its parents are closed, and the entire $`k=87`$ case is excluded only when every relevant layer is closed.

safe31700 returns code 1 for valid partial coverage, not for program failure. It has 276997 accepted logs, 1672 unaccepted concurrent logs excluded from coverage, and 3109 uncovered parents. Stage labels are audit counters, not elapsed seconds, and cannot provide a direct completion estimate.

The latest original scoped coverage has SHA-256 `ba10beefff8e72e2516f9b1da6c724587ce5b4e10cd83063b87fa8542ee07814`; the recheck has `e4ecb17b7ce4931584126b9ee420c7066c4e4f7d3041da356955f890d2c062ef`. Different hashes do not automatically mean different coverage: concurrent counters may differ, while the uncovered-parent sets must be—and were—checked to be identical.

## 10. Scope of the 88-term construction searches

Completed local searches around the known 89-term representation include:

- direct pair-to-one and triple-to-one merges;
- every three-term subset replaced by two distinct unit fractions;
- designated one-split/one-merge, two-split, and restricted sequential-split neighbors;
- two-denominator swaps in the base set;
- selected exact pair90 families and other designated tail families.

No 88-term representation was found. These results concern only their respective local transformations or named families; they do **not** prove global 88-term nonexistence. A global 87-term exclusion would not settle 88 terms either. Proving $`S(5)=89`$ requires both global exclusions.

## 11. Source-to-verification map

- `src/symdiff.cpp`: full symmetric-difference enumeration, exact rational arithmetic, tail search, and command-line output.
- `src/selftest.py`: reruns the 11/12/13-term cases for 3, the 31/32/33-term cases for 4, and the 83-term case for 5.
- `src/bounds.py`: harmonic bounds and the explicit representations of 3 and 4.
- `src/verify.py`: exact verification of arbitrary denominator lists.
- `src/two_tail.py` and `src/two_tail.cu`: optional factorization CUDA path.
- `src/audit_release.py`: independent checks of representations, evidence fields, inventories, closure logs, and release metadata.
- `production/audit_safe_snapshot.py`: full independent review in the original complete-data environment.
- `production/certify_coverage_delta.py`: complete z-range, log hash, owner, pending, and before/after parent-set checks.
- `production/audit_two_tail_history.py`: static audit of the specific historical fallback defect.

The curated `make audit` invokes only the packaged independent auditor. Production scripts require the original complete owner reports, logs, and some historical process state; they must not be presented as successful full audits on the curated subset.

## 12. Unresolved work

At safe31700, layers r4–r13 still contain 14, 155, 338, 386, 658, 574, 436, 314, 207, and 27 uncovered parents. Every coordinate is listed in `logs/uncovered_parents_safe31700.json`. Only additional accepted negative logs or valid representations can improve the result.

Therefore the final statement remains
$$S(1)=1,\quad S(2)=4,\quad S(3)=13,\quad S(4)=33,\qquad87\le S(5)\le89.$$
Any stronger exact value for $`S(5)`$ requires a new mathematical proof or new complete coverage, not merely more unreviewed computation.
