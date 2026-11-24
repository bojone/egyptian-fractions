PYTHON ?= python3
CXX ?= g++
NVCC ?= nvcc
GPU_ARCH ?= native
GPU_POOL ?= 8
CXXFLAGS ?= -O3 -std=c++17
GMP_LIBS ?= -l:libgmp.so.10

.PHONY: all cpu gpu audit audit-merges selftest check checksums production production-smoke clean

all: cpu gpu

cpu: src/symdiff_exact

gpu: src/two_tail

src/symdiff_exact: src/symdiff.cpp
	$(CXX) $(CXXFLAGS) $< $(GMP_LIBS) -o $@

src/two_tail: src/two_tail.cu
	$(NVCC) -O3 -std=c++17 -arch=$(GPU_ARCH) -x cu $< -o $@

audit:
	$(PYTHON) src/audit_release.py

audit-merges:
	$(PYTHON) src/audit_merges89.py
	$(PYTHON) src/audit_base_pairs89.py

selftest: cpu
	$(PYTHON) src/selftest.py

check: audit audit-merges selftest

checksums:
	$(PYTHON) src/make_checksums.py

production: production/fixed_server

production/fixed_server: production/fixed_server.cpp production/fixed.cpp production/symdiff.cpp production/gpu_three_batch.cu production/gpu_two_batch.cu production/gpu_exact_batch.cu production/gpu_three_hybrid.hpp production/gpu_hybrid.hpp production/gpu_three.hpp production/gpu_two.hpp production/gpu_big_arithmetic.hpp production/factor64.hpp
	$(NVCC) -O3 -std=c++17 -Iproduction -rdc=true -DGPU_THREE -DDIVISOR_TWO_TAIL -DGPU_TWO_DEFAULT_POOL=$(GPU_POOL) -DCPU_ONLY_ROOT_MAX_R=4 -DGPU_TWO_RANGE_LIMIT=100000 -DCPU_QUADRATIC_BIG -DTHREE_PAIR_LIFT -DTWO_TAIL_BINARY_SEARCH=16 -arch=$(GPU_ARCH) -x cu production/fixed_server.cpp production/gpu_three_batch.cu $(GMP_LIBS) -o $@

production-smoke: production
	printf 'smoke 3 11 12 13\n' | production/fixed_server 3 13

clean:
	rm -f src/symdiff_exact src/two_tail production/fixed_server
