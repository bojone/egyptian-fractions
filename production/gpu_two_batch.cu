#include "gpu_two.hpp"

#define GPU_TWO_ONLY
#define Big GpuBig
#define Rat GpuRat
#define gcd_ui gpu_gcd_ui
#define main gpu_exact_program_main
#include "gpu_exact_batch.cu"
#undef main

#ifdef PROFILE_WIDE_TWO
__device__ unsigned long long profile_wide_two_count = 0;
#endif

__global__ void two_kernel(const GpuTwoTask *tasks, GpuTwoResult *results) {
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
    __shared__ Big winning_b;
    if (lane == 0) {
        winner = -1;
        numeric_error = 0;
        for (int i = LIMBS; i < 8; ++i) {
            if (tasks[task_id].p[i] || tasks[task_id].q[i]) numeric_error = 1;
        }
    }
    __syncthreads();
    bool overflow = false;
    uint64_t lower = integer_bound(target, 1, overflow);
    uint64_t hi = integer_bound(target, 2, overflow);
#ifdef PROFILE_WIDE_TWO
    if (lane == 0 && !overflow && hi > lower && hi - lower >= PROFILE_WIDE_TWO) {
        if (atomicAdd(&profile_wide_two_count, 1ULL) < 64) {
            printf("WIDE task=%u previous=%llu p=", task_id, (unsigned long long)previous);
            for (int i = 0; i < LIMBS; ++i) printf("%llu ", (unsigned long long)target.p.v[i]);
            printf("q=");
            for (int i = 0; i < LIMBS; ++i) printf("%llu ", (unsigned long long)target.q.v[i]);
            printf("lo=%llu hi=%llu\n", (unsigned long long)lower, (unsigned long long)hi);
        }
    }
#endif
    if (!overflow && cmp(mul_small(target.q, 2, overflow),
                         mul_small(target.p, hi, overflow)) == 0) {
        if (hi == 0) overflow = true;
        else --hi;
    }
    if (overflow) {
        numeric_error = 1;
    } else {
        bool empty = previous == ~0ULL || lower == ~0ULL;
        uint64_t lo = empty ? 1 : previous + 1;
        if (!empty && lower + 1 > lo) lo = lower + 1;
        Wide p_squared = mul_wide(target.p, target.p);
        Wide four_q = wide_from_big(mul_small(target.q, 4, overflow));
        if (overflow) numeric_error = 1;
        bool monotone = cmp_wide(p_squared, four_q) > 0;
#ifdef TWO_TAIL_BINARY_SEARCH
        if (!overflow && !empty && monotone && lo <= hi && hi - lo >= TWO_TAIL_BINARY_SEARCH) {
            auto possible = [&](unsigned long long a, bool &error) {
                bool local_overflow = false;
                Big difference = sub(mul_small(target.p, a, local_overflow), target.q);
                Big square = mul_small(from64(a), a, local_overflow);
                error = local_overflow;
                return cmp(difference, square) <= 0;
            };
            bool numeric_error_local = false;
            if (!possible(lo, numeric_error_local)) {
                if (numeric_error_local) numeric_error = 1;
                else hi = lo - 1;
            } else {
                unsigned long long first = lo, last = hi;
                while (first < last) {
                    unsigned long long mid = first + (last - first + 1) / 2;
                    if (possible(mid, numeric_error_local)) first = mid;
                    else last = mid - 1;
                    if (numeric_error_local) break;
                }
                if (numeric_error_local) numeric_error = 1;
                else hi = first;
            }
        }
#endif
        if (!overflow && !numeric_error && !empty && lo <= hi) {
            for (uint64_t a = lo + lane; a <= hi; a += 256) {
                if (atomicAdd(&winner, 0) >= 0 || a < lo) break;
                bool candidate_overflow = false;
                Big difference = sub(mul_small(target.p, a, candidate_overflow), target.q);
                Big square = mul_small(from64(a), a, candidate_overflow);
                if (candidate_overflow) {
                    numeric_error = 1;
                    break;
                }
                if (cmp(difference, square) > 0) {
                    if (monotone) break;
                    if (a > ~0ULL - 256) break;
                    continue;
                }
#ifdef TAIL_GCD_BIG_MODULUS
                uint64_t g = gcd_ui(a, mod_small(target.q, a));
#else
                bool small_difference = true;
                for (int i = 1; i < LIMBS; ++i) small_difference &= difference.v[i] == 0;
                uint64_t g = small_difference
                    ? gcd_ui(a, difference.v[0])
                    : gcd_ui(a, mod_small(target.q, a));
#endif
                Big gcd_square = mul_small(from64(g), g, candidate_overflow);
                if (candidate_overflow) {
                    numeric_error = 1;
                    break;
                }
                if (cmp(difference, gcd_square) > 0) {
                    if (a > ~0ULL - 256) break;
                    continue;
                }
#ifdef DIVISOR_TWO_TAIL
                Big pair_denominator;
                int pair_code = unit_pair_divisor(target, a, difference, g, pair_denominator);
                if (pair_code == 1 && atomicCAS(&winner, -1, (int)lane) == -1) {
                    winning_a = a;
                    winning_b = pair_denominator;
                }
                if (pair_code == 2) {
                    numeric_error = 1;
                    break;
                }
                if (pair_code >= 0) {
                    if (a > ~0ULL - 256) break;
                    continue;
                }
#endif
                Rat rest;
                int code = unit_op(target, a, rest);
                if (code == 0 && !rest.negative && !is_zero(rest.p)) {
                    Big denominator;
                    code = unit_denominator(rest, a, denominator);
                    if (code == 1 && atomicCAS(&winner, -1, (int)lane) == -1) {
                        winning_a = a;
                        winning_b = denominator;
                    }
                }
                if (code == 2) {
                    numeric_error = 1;
                    break;
                }
                if (a > ~0ULL - 256) break;
            }
        }
    }
    __syncthreads();
    if (lane == 0) {
        if (winner >= 0) {
            results[task_id].code = 1;
            results[task_id].a = winning_a;
            for (int i = 0; i < 8; ++i)
                results[task_id].b[i] = i < LIMBS ? winning_b.v[i] : 0;
        } else {
            results[task_id].code = numeric_error ? 2 : 0;
            results[task_id].a = 0;
            for (int i = 0; i < 8; ++i) results[task_id].b[i] = 0;
        }
    }
}

bool gpu_two_search(const GpuTwoTask *tasks, size_t count,
                    GpuTwoResult *results, int device) {
    if (count == 0) return true;
    static GpuTwoTask *device_tasks = nullptr;
    static GpuTwoResult *device_results = nullptr;
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
        two_kernel<<<(unsigned)count, 256>>>(device_tasks, device_results);
        ok = cudaGetLastError() == cudaSuccess;
    }
    if (ok) ok = cudaDeviceSynchronize() == cudaSuccess;
    if (ok) ok = cudaMemcpy(results, device_results, count * sizeof(*results),
                            cudaMemcpyDeviceToHost) == cudaSuccess;
    return ok;
}
