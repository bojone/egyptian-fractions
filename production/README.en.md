# Production Reference Implementation and Usage Boundaries

**[中文](README.md) | English**

This directory contains core reference source for the hybrid CPU/GPU searcher and full-coverage audits. It is intended for understanding the algorithm, rebuilding searchers, and working in a complete-data environment. It is not a one-command full recomputation of the curated release.

## Build and run the smoke test

Run these commands from the repository root. A CUDA compiler, GMP, and a C++17 host environment are required:

```bash
make production NVCC=/path/to/nvcc GPU_POOL=1
make production-smoke NVCC=/path/to/nvcc GPU_POOL=1
```

`GPU_POOL` defaults to 8 and controls the device-allocation pool; change it to the available device count. `GPU_ARCH` defaults to `native`. `make production` only builds `production/fixed_server` and never starts a full search. `make production-smoke` submits a fixed-deletion task and returns:

```text
r=3 fixed=11,12,13, ... result=yes
JOB_END smoke code=0
3 13 : 1 2 3 4 5 6 7 8 9 10 15 230 57960
```

These are 13 distinct denominators with exact sum 3. The smoke result proves basic build and invocation correctness, not completion of any large branch. The historical production environment recorded 8 GPU devices and 288 nonpaused compute slots. No specific model is listed, and identical runtimes are not promised.

## Source responsibilities

- `symdiff.cpp`: includes `../src/symdiff.cpp`, sharing one GMP symmetric-difference core.
- `fixed.cpp`: enumerates remaining deletions and added tails after a fixed deleted prefix.
- `fixed_server.cpp`: reads a job identifier and $`r,x,y,z`$ from standard input, calls the fixed search, and prints `JOB_END`.
- `gpu_hybrid.hpp`: two-term batching, host certificates, and CPU fallback.
- `gpu_three_hybrid.hpp`: three-term batching, task partitioning, host certificates, and CPU fallback.
- `gpu_two_batch.cu`, `gpu_three_batch.cu`, and `gpu_exact_batch.cu`: device tail searches.
- `gpu_big_arithmetic.hpp` and `factor64.hpp`: device big-integer and factor helpers.
- `gpu_two.hpp` and `gpu_three.hpp`: host/device data types and interfaces.

Default production macros include `GPU_THREE`, `DIVISOR_TWO_TAIL`, `CPU_QUADRATIC_BIG`, `THREE_PAIR_LIFT`, and `TWO_TAIL_BINARY_SEARCH=16`. `CPU_ONLY_ROOT_MAX_R=4` keeps shallow roots on the CPU, `GPU_TWO_RANGE_LIMIT=100000` controls the device-path range, and `GPU_TWO_DEFAULT_POOL=$(GPU_POOL)` controls device allocation. `GPU_TWO_DEVICE` can select a device for a single task.

A compiler may warn that device `long double` is treated as `double`. These values are estimates only; exact integer comparisons correct every endpoint, and a floating estimate cannot by itself produce a negative result. Device positives are verified with host GMP.

## Standalone two-term CUDA path

The root `Makefile` also offers a smaller independent path:

```bash
make gpu NVCC=/path/to/nvcc
python3 -m pip install -r requirements.txt
cd src
python3 two_tail.py p q previous device
```

`two_tail.py` performs factorization and congruence lookup, while `two_tail.cu` enumerates combinations. `previous` is the previous denominator and `device` is the device index. This path requires a GPU and SymPy; neither is needed for the curated evidence audit.

## Full-coverage scripts require complete data

The following programs come from the original production environment:

- `audit_safe_snapshot.py`: independently reads all accepted content hashes and rebuilds coverage;
- `coverage87_distinct_v1.py`: root, secondary, and depth-three parent coverage;
- `certify_coverage_delta.py`: checks complete z-ranges, logs, owners, pending sets, and before/after parent sets for new closures;
- `audit_two_tail_history.py`: audits the particular old complete-fallback defect;
- `audit_history_checkpoint.py`: periodically archives the history audit and restores fixed inputs.

They **cannot complete a full audit on this curated release alone**. Most original logs, owner reports, binaries, continuous files, caches, and historical process state are deliberately omitted. The relative `production/logs` link points only to `../logs`; it does not supply the missing production archive.

For example, an independent snapshot audit requires a continuous production file, a valid snapshot, owner mapping, every cited owner report, fixed-search binaries, and every referenced negative log. Differential closure certification also needs the preceding scoped coverage. A missing input can make a command fail; that failure must not be interpreted as a mathematical exclusion.

## Negative acceptance and positive verification

A production negative log needs terminal `result=no`, a unique coordinate, a complete content hash, and an accepted engine label. Pending jobs, timeouts, candidate labels, truncated output, and unaccepted concurrent logs do not count. Retiring a process or restoring a session is not itself a proof of completion.

Every GPU positive result requires an independent check of distinct denominators and exact rational sum. Overflow or numerical uncertainty triggers exact CPU fallback. Neither positive nor negative output is accepted solely because it has a familiar textual form.

## Recommended checks within this release

```bash
make audit
make selftest
make production-smoke NVCC=/path/to/nvcc GPU_POOL=1
sha256sum -c SHA256SUMS
```

`make audit` invokes only `src/audit_release.py`; it does not accidentally invoke the full-production programs above. `make selftest` performs actual small GMP searches and needs no GPU.

To continue complete 87- or 88-term searches, prepare the original complete data and a separate empty output directory, then configure devices and owner management as in the original environment. Do not overwrite the curated evidence or interpret a local closure as global nonexistence. See [../docs/TECHNICAL.en.md](../docs/TECHNICAL.en.md) and [../docs/EVIDENCE.en.md](../docs/EVIDENCE.en.md).
