#pragma once

#include "gpu_two.hpp"

#ifdef GPU_TWO_DEFAULT_POOL
#include <unistd.h>
#endif

extern "C" {
void __gmpz_import(mpz_ptr, size_t, int, size_t, int, size_t, const void *);
}

struct BatchSearch : Search {
    struct Pending {
        Rat target;
        unsigned long previous;
        std::vector<unsigned long> path;
    };

    std::vector<Pending> pending;
    size_t batch_limit = 8192;
    int device = 0;
    int call_depth = 0;

    BatchSearch() {
        if (const char *value = std::getenv("GPU_TWO_BATCH"))
            batch_limit = std::stoul(value);
        if (const char *value = std::getenv("GPU_TWO_DEVICE")) {
            device = std::stoi(value);
        } else {
#ifdef GPU_TWO_DEFAULT_POOL
            device = static_cast<int>(getpid()) % GPU_TWO_DEFAULT_POOL;
            if (setenv("GPU_TWO_DEVICE", std::to_string(device).c_str(), 0) != 0)
                throw std::runtime_error("cannot set GPU_TWO_DEVICE");
#endif
        }
        if (batch_limit == 0) throw std::runtime_error("GPU_TWO_BATCH must be positive");
    }

    static void export_big(const Big &value, uint64_t *limbs) {
        int size = value.v[0]._mp_size;
        if (size < 0 || size > 8) throw std::overflow_error("GPU two-tail input exceeds 512 bits");
        for (int i = 0; i < 8; ++i)
            limbs[i] = i < size ? value.v[0]._mp_d[i] : 0;
    }

    bool certificate(const Pending &item, const GpuTwoResult &result) {
        if (result.code != 1 || result.a <= item.previous) return false;
        Rat rest = unit_sub(item.target, result.a);
        Big b;
        __gmpz_import(b.v, 8, -1, sizeof(uint64_t), 0, 0, result.b);
        return __gmpz_cmp_ui(rest.p.v, 1) == 0 &&
               __gmpz_cmp(rest.q.v, b.v) == 0 &&
               __gmpz_cmp_ui(b.v, result.a) > 0;
    }

    bool flush() {
        if (pending.empty()) return false;
        std::vector<GpuTwoTask> tasks(pending.size());
        std::vector<GpuTwoResult> results(pending.size());
        bool converted = true;
        for (size_t i = 0; i < pending.size(); ++i) {
            try {
                export_big(pending[i].target.p, tasks[i].p);
                export_big(pending[i].target.q, tasks[i].q);
            } catch (const std::overflow_error &) {
                converted = false;
                break;
            }
            tasks[i].previous = pending[i].previous;
        }
        auto gpu_started = std::chrono::steady_clock::now();
        bool completed = converted && gpu_two_search(tasks.data(), tasks.size(), results.data(), device);
        if (std::getenv("GPU_TWO_TRACE"))
            std::cerr << "gpu_two_batch tasks=" << pending.size() << " completed=" << completed
                      << " seconds=" << std::chrono::duration<double>(
                          std::chrono::steady_clock::now() - gpu_started).count() << "\n";
        for (size_t i = 0; i < pending.size(); ++i) {
            if (completed && results[i].code == 0) continue;
            if (completed && certificate(pending[i], results[i])) {
                path = pending[i].path;
                penultimate_denominator = Big(results[i].a);
                __gmpz_import(final_denominator.v, 8, -1, sizeof(uint64_t), 0, 0, results[i].b);
                pending.clear();
                return true;
            }
            if (completed && results[i].code == 1) {
                Big b;
                __gmpz_import(b.v, 8, -1, sizeof(uint64_t), 0, 0, results[i].b);
                std::cerr << "invalid GPU two-tail certificate; using CPU: target="
                          << str(pending[i].target.p) << "/" << str(pending[i].target.q)
                          << " previous=" << pending[i].previous << " a=" << results[i].a
                          << " b=" << str(b) << "\n";
            }
            path = pending[i].path;
            if (Search::dfs(pending[i].target, 2, pending[i].previous)) {
                pending.clear();
                return true;
            }
        }
        pending.clear();
        return false;
    }

    bool dfs(const Rat &target, unsigned long r, unsigned long previous) override {
        if (r == 2) {
            ++nodes;
            pending.push_back({target, previous, path});
            if (pending.size() >= batch_limit || call_depth == 0) return flush();
            return false;
        }
        bool root = call_depth++ == 0;
        bool found = Search::dfs(target, r, previous);
        --call_depth;
        if (root && !found) found = flush();
        return found;
    }
};

#define SEARCH_CLASS BatchSearch
