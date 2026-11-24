#pragma once

#include <cstddef>
#include <cstdint>

struct GpuTwoTask {
    uint64_t p[8], q[8];
    uint64_t previous;
};

struct GpuTwoResult {
    int code;
    uint64_t a;
    uint64_t b[8];
};

bool gpu_two_search(const GpuTwoTask *tasks, size_t count,
                    GpuTwoResult *results, int device);
