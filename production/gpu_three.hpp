#pragma once

#include <cstddef>
#include <cstdint>

struct GpuThreeTask {
    uint64_t p[8], q[8];
    uint64_t previous;
    uint64_t first_max = 0;
};

struct GpuThreeResult {
    int code;
    uint64_t a, b;
    uint64_t c[8];
};

bool gpu_three_search(const GpuThreeTask *tasks, size_t count,
                      GpuThreeResult *results, int device);
