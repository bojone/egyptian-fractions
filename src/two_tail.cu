#include <cuda_runtime.h>
#include <cinttypes>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <vector>

constexpr int MAX_EXPONENT = 16;
constexpr int MAX_SOLUTIONS = 65536;

__device__ bool contains(const uint64_t *keys, int count, uint64_t value) {
    int lo = 0, hi = count - 1;
    while (lo <= hi) {
        int mid = (lo + hi) >> 1;
        uint64_t key = keys[mid];
        if (key == value) return true;
        if (key < value) lo = mid + 1;
        else hi = mid - 1;
    }
    return false;
}

__global__ void enumerate_candidates(
        const uint64_t *powers, const int *max_exponent, int factor_count,
        unsigned long long total, uint64_t modulus,
        const uint64_t *keys, int key_count,
        unsigned long long *solutions, unsigned long long *solution_count) {
    unsigned long long stride = (unsigned long long)gridDim.x * blockDim.x;
    for (unsigned long long index = blockIdx.x * blockDim.x + threadIdx.x;
         index < total; index += stride) {
        unsigned long long work = index;
        uint64_t u = 1;
        for (int j = 0; j < factor_count; ++j) {
            int e = work % (max_exponent[j] + 1);
            work /= max_exponent[j] + 1;
            u = (uint64_t)((unsigned __int128)u * powers[j * MAX_EXPONENT + e] % modulus);
        }
        if (!contains(keys, key_count, u)) continue;
        unsigned long long slot = atomicAdd(solution_count, 1ULL);
        if (slot < MAX_SOLUTIONS) solutions[slot] = index;
    }
}

bool cuda_ok(cudaError_t error) {
    if (error == cudaSuccess) return true;
    std::fprintf(stderr, "CUDA error: %s\n", cudaGetErrorString(error));
    return false;
}

#define CUDA_CHECK(call) do { if (!cuda_ok(call)) return 2; } while (0)

int main(int argc, char **argv) {
    if (argc != 4) {
        std::fprintf(stderr, "usage: two_tail DEVICE INPUT OUTPUT\n");
        return 2;
    }
    int device = std::atoi(argv[1]);
    FILE *input = std::fopen(argv[2], "r");
    if (!input) return 2;
    int n, key_count;
    uint64_t modulus, total;
    if (std::fscanf(input, "%d %" SCNu64 " %" SCNu64 " %d",
                    &n, &modulus, &total, &key_count) != 4) return 2;
    if (n < 0 || n > 1024 || key_count <= 0 || modulus < 2) return 2;
    std::vector<int> exponents(n);
    std::vector<uint64_t> powers(n * MAX_EXPONENT), keys(key_count);
    for (int &e : exponents) if (std::fscanf(input, "%d", &e) != 1 || e < 0 || e >= 16) return 2;
    for (uint64_t &x : powers) if (std::fscanf(input, "%" SCNu64, &x) != 1) return 2;
    for (uint64_t &x : keys) if (std::fscanf(input, "%" SCNu64, &x) != 1) return 2;
    if (std::fclose(input) != 0) return 2;
    uint64_t *dp, *dk;
    unsigned long long *solutions, *count;
    int *de;
    CUDA_CHECK(cudaSetDevice(device));
    CUDA_CHECK(cudaMalloc(&dp, powers.size() * sizeof(uint64_t)));
    CUDA_CHECK(cudaMalloc(&dk, keys.size() * sizeof(uint64_t)));
    CUDA_CHECK(cudaMalloc(&de, n * sizeof(int)));
    CUDA_CHECK(cudaMalloc(&count, sizeof(*count)));
    CUDA_CHECK(cudaMalloc(&solutions, MAX_SOLUTIONS * sizeof(unsigned long long)));
    CUDA_CHECK(cudaMemcpy(dp, powers.data(), powers.size() * sizeof(uint64_t), cudaMemcpyHostToDevice));
    CUDA_CHECK(cudaMemcpy(dk, keys.data(), keys.size() * sizeof(uint64_t), cudaMemcpyHostToDevice));
    CUDA_CHECK(cudaMemcpy(de, exponents.data(), n * sizeof(int), cudaMemcpyHostToDevice));
    CUDA_CHECK(cudaMemset(count, 0, sizeof(*count)));
    enumerate_candidates<<<1024, 256>>>(dp, de, n, total, modulus, dk, key_count,
                                       solutions, count);
    CUDA_CHECK(cudaGetLastError());
    CUDA_CHECK(cudaDeviceSynchronize());
    unsigned long long host_count;
    std::vector<unsigned long long> host_solutions(MAX_SOLUTIONS);
    CUDA_CHECK(cudaMemcpy(&host_count, count, sizeof(host_count), cudaMemcpyDeviceToHost));
    CUDA_CHECK(cudaMemcpy(host_solutions.data(), solutions,
                          MAX_SOLUTIONS * sizeof(unsigned long long), cudaMemcpyDeviceToHost));
    FILE *output = std::fopen(argv[3], "w");
    if (!output) return 2;
    if (std::fprintf(output, "%llu\n", host_count) < 0) return 2;
    for (unsigned long long i = 0; i < host_count && i < MAX_SOLUTIONS; ++i)
        if (std::fprintf(output, "%llu\n", host_solutions[i]) < 0) return 2;
    if (std::fclose(output) != 0) return 2;
    CUDA_CHECK(cudaFree(dp));
    CUDA_CHECK(cudaFree(dk));
    CUDA_CHECK(cudaFree(de));
    CUDA_CHECK(cudaFree(count));
    CUDA_CHECK(cudaFree(solutions));
    return 0;
}
