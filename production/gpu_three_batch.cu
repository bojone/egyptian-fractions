#include "gpu_three.hpp"
#include "gpu_two_batch.cu"

__global__ void three_kernel(const GpuThreeTask *tasks, GpuThreeResult *results) {
    unsigned task_id = blockIdx.x;
    unsigned lane = threadIdx.x;
    Rat target{};
    for (int i = 0; i < LIMBS; ++i) {
        target.p.v[i] = tasks[task_id].p[i];
        target.q.v[i] = tasks[task_id].q[i];
    }
    uint64_t previous = tasks[task_id].previous;
    __shared__ int winner;
    __shared__ int numeric_error;
    __shared__ uint64_t winning_a;
    __shared__ Result winning_result;
#ifdef GPU_SHARED_THREE_BOUND
    __shared__ uint64_t shared_last;
#endif
    if (lane == 0) {
        winner = -1;
        numeric_error = 0;
        for (int i = LIMBS; i < 8; ++i) {
            if (tasks[task_id].p[i] || tasks[task_id].q[i]) numeric_error = 1;
        }
#ifdef GPU_FORCE_CPU_FALLBACK
        numeric_error = 1;
#endif
#ifdef GPU_SHARED_THREE_BOUND
        bool bound_overflow = false;
        shared_last = integer_bound(target, 3, bound_overflow);
        if (bound_overflow) numeric_error = 1;
#endif
    }
    __syncthreads();
    bool overflow = false;
#ifdef GPU_SHARED_THREE_BOUND
    uint64_t last = shared_last;
    if (numeric_error) overflow = true;
#else
    uint64_t last = integer_bound(target, 3, overflow);
    if (overflow) numeric_error = 1;
#endif
    if (tasks[task_id].first_max && tasks[task_id].first_max < last)
        last = tasks[task_id].first_max;
    uint64_t first = previous;
#ifdef THREE_ROOT_RECIPROCAL_LOWER_BOUND
    uint64_t reciprocal_floor = integer_bound(target, 1, overflow);
    if (overflow) numeric_error = 1;
    if (reciprocal_floor > previous) {
        if (reciprocal_floor == ~0ULL) numeric_error = 1;
        else first = reciprocal_floor + 1;
    }
#endif
    if (!overflow && !numeric_error && previous != ~0ULL) {
        for (uint64_t a = first + lane; a <= last; a += 256) {
            if (atomicAdd(&winner, 0) >= 0 || a <= previous) break;
            if (!possible_max(a, 3, target)) break;
#ifdef THREE_PAIR_LIFT
            bool lifted_overflow = false;
#ifdef THREE_REUSE_TWO_LOWER_BOUND
            uint64_t two_lower = 0;
            if (three_pair_impossible(target, a, lifted_overflow, &two_lower)) {
#else
            if (three_pair_impossible(target, a, lifted_overflow)) {
#endif
                if (a > ~0ULL - 256) break;
                continue;
            }
            if (lifted_overflow) {
                numeric_error = 1;
                break;
            }
#endif
            Rat rest;
            int code = unit_op(target, a, rest);
            if (code == 0 && !rest.negative && !is_zero(rest.p)) {
                Result result{};
#ifdef THREE_REUSE_TWO_LOWER_BOUND
                code = search_y(rest, 2, a, result, 0, &winner, two_lower);
#else
                code = search_y(rest, 2, a, result, 0, &winner);
#endif
                if (code == 1 && atomicCAS(&winner, -1, (int)lane) == -1) {
                    winning_a = a;
                    winning_result = result;
                }
            }
            if (code == 2) {
                numeric_error = 1;
                break;
            }
            if (a > ~0ULL - 256) break;
        }
    }
    __syncthreads();
    if (lane == 0) {
        if (winner >= 0) {
            results[task_id].code = 1;
            results[task_id].a = winning_a;
            results[task_id].b = winning_result.y[0];
            for (int i = 0; i < 8; ++i)
                results[task_id].c[i] = i < LIMBS ? winning_result.final_denominator.v[i] : 0;
        } else {
            results[task_id].code = numeric_error ? 2 : 0;
            results[task_id].a = results[task_id].b = 0;
            for (int i = 0; i < 8; ++i) results[task_id].c[i] = 0;
        }
    }
}

bool gpu_three_search(const GpuThreeTask *tasks, size_t count,
                      GpuThreeResult *results, int device) {
    if (count == 0) return true;
    static GpuThreeTask *device_tasks = nullptr;
    static GpuThreeResult *device_results = nullptr;
    static size_t capacity = 0;
    static int current_device = -1;
    if (cudaSetDevice(device) != cudaSuccess) return false;
    if (current_device >= 0 && current_device != device) {
        cudaSetDevice(current_device);
        cudaFree(device_tasks);
        cudaFree(device_results);
        device_tasks = nullptr;
        device_results = nullptr;
        capacity = 0;
        current_device = -1;
        if (cudaSetDevice(device) != cudaSuccess) return false;
    }
    if (count > capacity) {
        cudaFree(device_tasks);
        cudaFree(device_results);
        device_tasks = nullptr;
        device_results = nullptr;
        bool allocated = cudaMalloc(&device_tasks, count * sizeof(*tasks)) == cudaSuccess;
        if (allocated) allocated = cudaMalloc(&device_results, count * sizeof(*results)) == cudaSuccess;
        if (!allocated) {
            cudaFree(device_tasks);
            cudaFree(device_results);
            device_tasks = nullptr;
            device_results = nullptr;
            capacity = 0;
            current_device = -1;
            return false;
        }
        capacity = count;
        current_device = device;
    }
    bool ok = cudaMemcpy(device_tasks, tasks, count * sizeof(*tasks),
                         cudaMemcpyHostToDevice) == cudaSuccess;
    if (ok) {
        three_kernel<<<(unsigned)count, 256>>>(device_tasks, device_results);
        ok = cudaGetLastError() == cudaSuccess;
    }
    if (ok) ok = cudaDeviceSynchronize() == cudaSuccess;
    if (ok) ok = cudaMemcpy(results, device_results, count * sizeof(*results),
                            cudaMemcpyDeviceToHost) == cudaSuccess;
    return ok;
}
