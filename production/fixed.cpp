#define main symdiff_original_main
#include "symdiff.cpp"
#undef main

#ifndef FIXED_MAIN
#define FIXED_MAIN main
#endif

int FIXED_MAIN(int argc, char **argv) {
    if (argc < 5) {
        std::cerr << "usage: fixed N K R X1 [X2 ...]\n";
        return 2;
    }
    unsigned long n = std::stoul(argv[1]);
    unsigned long k = std::stoul(argv[2]);
    unsigned long r = std::stoul(argv[3]);
    std::vector<unsigned long> fixed;
    for (int i = 4; i < argc; ++i) fixed.push_back(std::stoul(argv[i]));
    if (fixed.size() > r || r > k) return 2;

    std::vector<Rat> h(2 * k + 2);
    for (unsigned long i = 1; i <= 2 * k + 1; ++i) h[i] = unit_add(h[i - 1], i);
    unsigned long prefix = 0;
    for (unsigned long j = 1; j <= k; ++j) {
        Rat largest_without = unit_sub(h[k + 1], j);
        Big rhs = mul_ui(largest_without.q, n);
        if (__gmpz_cmp(largest_without.p.v, rhs.v) < 0) prefix = j;
        else break;
    }
    Rat delta;
    Big t = mul_ui(h[k].q, n);
    __gmpz_sub(delta.p.v, h[k].p.v, t.v);
    delta.q = h[k].q;
    normalize(delta);

    Symdiff search(h, k, prefix);
    search.r = r;
    search.delta = delta;
    search.allowed = rat_add(delta, rat_sub(h[k + r], h[k]));
    search.min_removed.assign(k + 1, Rat());
    for (unsigned long j = 1; j <= r; ++j) search.min_removed[j] = rat_sub(h[k], h[k - j]);
    if (compare(search.min_removed[r], search.allowed) > 0) {
        std::cerr << "result=no\n";
        return 1;
    }

    Rat sum;
    unsigned long previous = prefix;
    for (unsigned long x : fixed) {
        if (x <= previous || x > k) {
            std::cerr << "fixed denominators must be increasing and lie in the removable range\n";
            return 2;
        }
        sum = unit_add(sum, x);
        previous = x;
    }
    if (compare(sum, search.allowed) > 0) {
        std::cerr << "result=no\n";
        return 1;
    }
    search.removed = fixed;
    auto started = std::chrono::steady_clock::now();
    bool found = search.enumerate_removed(sum, r - fixed.size(), previous);
    double seconds = std::chrono::duration<double>(std::chrono::steady_clock::now() - started).count();
    std::cerr << "r=" << r << " fixed=";
    for (unsigned long x : fixed) std::cerr << x << ',';
    std::cerr << " xnodes=" << search.xnodes << " ynodes=" << search.ynodes
#ifdef FOUR_PRIME_COVER
              << " four_candidates=" << four_cover_stats.candidates
              << " four_ordinary=" << four_cover_stats.ordinary
              << " four_cover=" << four_cover_stats.cover
              << " four_factor_fallback=" << four_cover_stats.factor_fallback
#endif
#ifdef DENOMINATOR_PRIME_POWER_COVER
              << " denominator_candidates=" << denominator_cover_stats.candidates
              << " denominator_prime_power_cover=" << denominator_cover_stats.prime_power_cover
#endif
#ifdef PRIME_TAIL_PAIR
              << " prime_pair_cases=" << prime_pair_stats.cases
              << " prime_pair_candidates=" << prime_pair_stats.candidates
              << " prime_pair_fallbacks=" << prime_pair_stats.fallbacks
#endif
#ifdef LARGE_PRIME_COVER
              << " large_prime_candidates=" << large_prime_cover_stats.candidates
              << " large_prime_divisors=" << large_prime_cover_stats.prime_divisors
              << " large_prime_cover=" << large_prime_cover_stats.cover
#endif
#ifdef FACTOR_CACHE_STATS
              << " factor_cache_children=" << factor_cache_stats.children
              << " factor_native_cases=" << factor_cache_stats.native_cases
              << " factor_native_tested=" << factor_cache_stats.native_tested
              << " factor_native_positive=" << factor_cache_stats.native_positive
#endif
              << " seconds=" << seconds << " result=" << (found ? "yes" : "no") << '\n';
    if (!found) return 1;

    std::cout << n << " " << k << " :";
    for (unsigned long a = 1; a <= k; ++a) {
        if (!std::binary_search(search.removed.begin(), search.removed.end(), a)) std::cout << " " << a;
    }
    for (const Big &a : search.added) std::cout << " " << str(a);
    std::cout << '\n';
    return 0;
}
