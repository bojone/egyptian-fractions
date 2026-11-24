#pragma once

#include "gpu_hybrid.hpp"
#include "gpu_three.hpp"

struct BatchThreeSearch : BatchSearch {
    std::vector<Pending> three_pending;
    bool cpu_root = false;

    bool certificate(const Pending &item, const GpuThreeResult &result) {
        if (result.code != 1 || result.a <= item.previous || result.b <= result.a) return false;
        Rat rest = unit_sub(item.target, result.a);
        rest = unit_sub(rest, result.b);
        Big c;
        __gmpz_import(c.v, 8, -1, sizeof(uint64_t), 0, 0, result.c);
        return __gmpz_cmp_ui(rest.p.v, 1) == 0 &&
               __gmpz_cmp(rest.q.v, c.v) == 0 &&
               __gmpz_cmp_ui(c.v, result.b) > 0;
    }

    bool flush_three() {
        if (three_pending.empty()) return false;
        std::vector<GpuThreeTask> tasks(three_pending.size());
        bool converted = true;
        for (size_t i = 0; i < three_pending.size(); ++i) {
            try {
                export_big(three_pending[i].target.p, tasks[i].p);
                export_big(three_pending[i].target.q, tasks[i].q);
            } catch (const std::overflow_error &) {
                converted = false;
                break;
            }
            tasks[i].previous = three_pending[i].previous;
        }
        unsigned long split_blocks = 1;
        if (const char *value = std::getenv("GPU_THREE_SPLIT_BLOCKS")) {
            split_blocks = std::stoul(value);
            if (split_blocks == 0 || split_blocks > 4096)
                throw std::invalid_argument("GPU_THREE_SPLIT_BLOCKS must be in [1,4096]");
        }
        std::vector<std::vector<size_t>> partitions(three_pending.size());
        if (converted && split_blocks > 1) {
            std::vector<GpuThreeTask> expanded;
            for (size_t i = 0; i < three_pending.size() && converted; ++i) {
                try {
                    unsigned long previous = three_pending[i].previous;
                    unsigned long last = integer_bound(three_pending[i].target, 3);
                    if (previous == ~0UL || previous >= last) {
                        partitions[i].push_back(expanded.size());
                        expanded.push_back(tasks[i]);
                        continue;
                    }
                    unsigned long first = previous + 1;
                    unsigned long count = std::min(split_blocks, last - first + 1);
                    unsigned long small = (last - first + 1) / count;
                    unsigned long extra = (last - first + 1) % count;
                    unsigned long lo = first;
                    for (unsigned long part = 0; part < count; ++part) {
                        unsigned long hi = lo + small + (part < extra) - 1;
                        GpuThreeTask task = tasks[i];
                        task.previous = lo - 1;
                        task.first_max = hi;
                        partitions[i].push_back(expanded.size());
                        expanded.push_back(task);
                        if (hi == ~0UL) break;
                        lo = hi + 1;
                    }
                } catch (const std::overflow_error &) {
                    converted = false;
                }
            }
            if (converted) tasks = std::move(expanded);
        }
        if (converted && split_blocks == 1) {
            for (size_t i = 0; i < tasks.size(); ++i) partitions[i].push_back(i);
        }
        std::vector<GpuThreeResult> results(tasks.size());
        auto gpu_started = std::chrono::steady_clock::now();
        bool completed = converted && gpu_three_search(tasks.data(), tasks.size(), results.data(), device);
        if (std::getenv("GPU_TWO_TRACE"))
            std::cerr << "gpu_three_batch tasks=" << three_pending.size() << " blocks=" << tasks.size()
                      << " completed=" << completed
                      << " seconds=" << std::chrono::duration<double>(
                          std::chrono::steady_clock::now() - gpu_started).count() << "\n";
        for (size_t i = 0; i < three_pending.size(); ++i) {
            bool negative = completed;
            bool invalid_certificate = false;
            for (size_t j : partitions[i]) {
                if (!completed || results[j].code == 0) continue;
                negative = false;
                if (results[j].code == 1 && certificate(three_pending[i], results[j])) {
                    path = three_pending[i].path;
                    path.push_back(results[j].a);
                    penultimate_denominator = Big(results[j].b);
                    __gmpz_import(final_denominator.v, 8, -1, sizeof(uint64_t), 0, 0, results[j].c);
                    three_pending.clear();
                    return true;
                }
                if (results[j].code == 1) invalid_certificate = true;
            }
            if (negative) continue;
            if (invalid_certificate)
                std::cerr << "invalid GPU three-tail certificate; using CPU\n";
            Search cpu;
            cpu.path = three_pending[i].path;
            bool found = cpu.dfs(three_pending[i].target, 3, three_pending[i].previous);
            nodes += cpu.nodes;
            if (found) {
                path = std::move(cpu.path);
                penultimate_denominator = std::move(cpu.penultimate_denominator);
                final_denominator = std::move(cpu.final_denominator);
                three_pending.clear();
                return true;
            }
        }
        three_pending.clear();
        return false;
    }

    bool dfs(const Rat &target, unsigned long r, unsigned long previous) override {
        if (cpu_root) return Search::dfs(target, r, previous);
#ifdef CPU_ONLY_ROOT_MAX_R
        if (call_depth == 0 && r <= CPU_ONLY_ROOT_MAX_R) {
            cpu_root = true;
            bool found = Search::dfs(target, r, previous);
            cpu_root = false;
            return found;
        }
#endif
        if (r == 3) {
            ++nodes;
#if defined(PRIME_POWER_PIGEONHOLE) && defined(PRIME_PIGEONHOLE_DUMMY)
            if (previous != ~0UL && prime_pigeonhole_impossible(target, previous + 1, 3))
                return false;
#endif
            three_pending.push_back({target, previous, path});
            if (three_pending.size() >= batch_limit || call_depth == 0) return flush_three();
            return false;
        }
        bool root = call_depth == 0;
        bool found = BatchSearch::dfs(target, r, previous);
        if (root && !found) found = flush_three();
        return found;
    }
};

#undef SEARCH_CLASS
#define SEARCH_CLASS BatchThreeSearch
