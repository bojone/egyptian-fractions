#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

extern "C" {
typedef unsigned long mp_limb_t;
typedef struct { int _mp_alloc; int _mp_size; mp_limb_t *_mp_d; } __mpz_struct;
typedef __mpz_struct mpz_t[1];
typedef __mpz_struct *mpz_ptr;
typedef const __mpz_struct *mpz_srcptr;
void __gmpz_init(mpz_ptr);
void __gmpz_init_set_ui(mpz_ptr, unsigned long);
void __gmpz_init_set(mpz_ptr, mpz_srcptr);
void __gmpz_clear(mpz_ptr);
void __gmpz_set(mpz_ptr, mpz_srcptr);
void __gmpz_set_ui(mpz_ptr, unsigned long);
void __gmpz_swap(mpz_ptr, mpz_ptr);
void __gmpz_mul(mpz_ptr, mpz_srcptr, mpz_srcptr);
void __gmpz_mul_ui(mpz_ptr, mpz_srcptr, unsigned long);
void __gmpz_sub(mpz_ptr, mpz_srcptr, mpz_srcptr);
void __gmpz_add(mpz_ptr, mpz_srcptr, mpz_srcptr);
void __gmpz_gcd(mpz_ptr, mpz_srcptr, mpz_srcptr);
void __gmpz_tdiv_q(mpz_ptr, mpz_srcptr, mpz_srcptr);
int __gmpz_cmp(mpz_srcptr, mpz_srcptr);
int __gmpz_cmp_ui(mpz_srcptr, unsigned long);
unsigned long __gmpz_get_ui(mpz_srcptr);
double __gmpz_get_d(mpz_srcptr);
char *__gmpz_get_str(char *, int, mpz_srcptr);
int __gmpz_set_str(mpz_ptr, const char *, int);
}

struct Big {
    mpz_t v;
    Big() { __gmpz_init(v); }
    Big(unsigned long x) { __gmpz_init_set_ui(v, x); }
    Big(const Big &x) { __gmpz_init_set(v, x.v); }
    Big(Big &&x) { __gmpz_init(v); __gmpz_swap(v, x.v); }
    ~Big() { __gmpz_clear(v); }
    Big &operator=(const Big &x) { if (this != &x) __gmpz_set(v, x.v); return *this; }
    Big &operator=(Big &&x) { __gmpz_swap(v, x.v); return *this; }
};

Big mul_ui(const Big &x, unsigned long a) {
    Big z;
    __gmpz_mul_ui(z.v, x.v, a);
    return z;
}

Big sub(const Big &x, const Big &y) {
    Big z;
    __gmpz_sub(z.v, x.v, y.v);
    return z;
}

Big div_exact(const Big &x, const Big &y) {
    Big z;
    __gmpz_tdiv_q(z.v, x.v, y.v);
    return z;
}

struct Rat {
    Big p, q{1};
};

extern "C" {
unsigned long __gmpz_tdiv_ui(mpz_srcptr, unsigned long);
unsigned long __gmpz_tdiv_q_ui(mpz_ptr, mpz_srcptr, unsigned long);
}

unsigned long gcd_ui(unsigned long a, unsigned long b) {
    while (b) {
        unsigned long t = a % b;
        a = b;
        b = t;
    }
    return a;
}

void unit_op_into(const Rat &x, unsigned long a, bool subtract, Rat &z, Big &qprime,
                  unsigned long *gcd_output = nullptr) {
    unsigned long g = gcd_ui(a, __gmpz_tdiv_ui(x.q.v, a));
    if (gcd_output) *gcd_output = g;
    __gmpz_tdiv_q_ui(qprime.v, x.q.v, g);
    __gmpz_mul_ui(z.p.v, x.p.v, a / g);
    if (subtract) __gmpz_sub(z.p.v, z.p.v, qprime.v);
    else __gmpz_add(z.p.v, z.p.v, qprime.v);
    __gmpz_mul_ui(z.q.v, qprime.v, a);
    unsigned long h = gcd_ui(g, __gmpz_tdiv_ui(z.p.v, g));
    if (h > 1) {
        __gmpz_tdiv_q_ui(z.p.v, z.p.v, h);
        __gmpz_tdiv_q_ui(z.q.v, z.q.v, h);
    }
}

Rat unit_op(const Rat &x, unsigned long a, bool subtract) {
    Rat z;
    Big qprime;
    unit_op_into(x, a, subtract, z, qprime);
    return z;
}

Rat unit_add(const Rat &x, unsigned long a) {
    return unit_op(x, a, false);
}

Rat unit_sub(const Rat &x, unsigned long a) {
    return unit_op(x, a, true);
}

long double as_double(const Rat &x) {
    return (long double)__gmpz_get_d(x.p.v) / (long double)__gmpz_get_d(x.q.v);
}

std::string str(const Big &x);

unsigned long integer_bound(const Rat &x, unsigned long r) {
#ifdef REUSE_GMP_SCRATCH
    static thread_local Big t, z;
    __gmpz_mul_ui(t.v, x.q.v, r);
    __gmpz_tdiv_q(z.v, t.v, x.p.v);
#else
    Big t = mul_ui(x.q, r);
    Big z = div_exact(t, x.p);
#endif
    static const Big max_ulong(~0UL);
    if (__gmpz_cmp(z.v, max_ulong.v) > 0) {
        std::cerr << "bound debug r=" << r << " z=" << str(z) << " max=" << str(max_ulong)
                  << " p=" << str(x.p) << " q=" << str(x.q) << '\n';
        throw std::overflow_error("denominator bound exceeds unsigned long");
    }
    return __gmpz_get_ui(z.v);
}

std::string str(const Big &x) {
    char *s = __gmpz_get_str(nullptr, 10, x.v);
    std::string z(s);
    std::free(s);
    return z;
}

#if defined(CPU_THREE_PAIR_EXACT_GAMMA) || defined(CPU_THREE_PAIR_GCD_SQUARE)
#include "cpu_three_pair.hpp"
#endif

#if defined(FOUR_PRIME_COVER) || defined(PRIME_TAIL_PAIR) || defined(LARGE_PRIME_COVER)
#include "four_cover.hpp"
#endif

#ifdef PRIME_TAIL_PAIR
#include "prime_pair.hpp"
#endif

#ifdef LARGE_PRIME_COVER
#include "large_prime_cover.hpp"
#endif

#ifdef DENOMINATOR_PRIME_POWER_COVER
#include "denominator_cover.hpp"
#endif

#ifdef CPU_QUADRATIC_BIG
bool quadratic_big_impossible(const Rat &target, unsigned long previous,
                              const Big *gamma_bound = nullptr) {
    Big p_squared;
    __gmpz_mul(p_squared.v, target.p.v, target.p.v);
    Big four_q = mul_ui(target.q, 4);
    if (__gmpz_cmp(p_squared.v, four_q.v) <= 0) return false;
    Big a = div_exact(target.q, target.p);
    Big one(1);
    __gmpz_add(a.v, a.v, one.v);
    Big previous_plus_one(previous);
    __gmpz_add(previous_plus_one.v, previous_plus_one.v, one.v);
    if (__gmpz_cmp(a.v, previous_plus_one.v) < 0) a = std::move(previous_plus_one);
    Big difference;
    __gmpz_mul(difference.v, target.p.v, a.v);
    __gmpz_sub(difference.v, difference.v, target.q.v);
    if (gamma_bound && __gmpz_cmp_ui(gamma_bound->v, 0) > 0)
        return __gmpz_cmp(difference.v, gamma_bound->v) > 0;
    Big square;
    __gmpz_mul(square.v, a.v, a.v);
    return __gmpz_cmp(difference.v, square.v) > 0;
}
#endif

int solve_two_big(const Rat &target, unsigned long previous, Big &a, Big &b) {
#ifdef CPU_QUADRATIC_BIG
    if (quadratic_big_impossible(target, previous)) return 0;
#endif
    const char *gpu_device = std::getenv("GPU_TWO_DEVICE");
    std::string command = "python3 two_tail_divisors.py " + str(target.p) + " " + str(target.q) +
                          " " + std::to_string(previous) + " " + (gpu_device ? gpu_device : "0");
    FILE *pipe = popen(command.c_str(), "r");
    if (!pipe) return 2;
    std::string output;
    char buffer[4096];
    while (fgets(buffer, sizeof(buffer), pipe)) output += buffer;
    int status = pclose(pipe);
    if (status != 0) return 2;
    size_t apos = output.find("\"a\":");
    size_t bpos = output.find("\"b\":");
    if (apos == std::string::npos || bpos == std::string::npos) {
        if (output.find("NO exact") != std::string::npos) return 0;
        return 2;
    }
    std::string sa = output.substr(apos + 4, output.find(',', apos) - apos - 4);
    std::string sb = output.substr(bpos + 4, output.find(',', bpos) - bpos - 4);
    if (__gmpz_set_str(a.v, sa.c_str(), 10) != 0 || __gmpz_set_str(b.v, sb.c_str(), 10) != 0) return 2;
    return 1;
}

struct Search {
    uint64_t nodes = 0;
    std::chrono::steady_clock::time_point started = std::chrono::steady_clock::now();
    std::vector<unsigned long> path;
    Big penultimate_denominator;
    Big final_denominator;
#ifdef CPU_TWO_TAIL_GCD_SQUARE
    Big two_tail_gamma_bound;
#endif
#ifdef FIRST_ADDED_DENOMINATOR
    unsigned long first_added = [] {
        const char *value = std::getenv("FIRST_ADDED");
        return value ? std::stoul(value) : 0UL;
    }();
    unsigned long first_added_min = [] {
        const char *value = std::getenv("FIRST_ADDED_MIN");
        return value ? std::stoul(value) : 0UL;
    }();
    unsigned long first_added_max = [] {
        const char *value = std::getenv("FIRST_ADDED_MAX");
        return value ? std::stoul(value) : 0UL;
    }();
#endif
#ifdef PRIME_POWER_INVARIANT
    unsigned long required_prime_power = 0;

    void require_largest_prime_power(const Rat &target, unsigned long k) {
        for (unsigned long p = 2; p <= k; ++p) {
            bool prime = true;
            for (unsigned long d = 2; d * d <= p; ++d) {
                if (p % d == 0) {
                    prime = false;
                    break;
                }
            }
            if (!prime || __gmpz_tdiv_ui(target.q.v, p) != 0) continue;
            unsigned long power = p;
            while (power <= ~0UL / p &&
                   __gmpz_tdiv_ui(target.q.v, power * p) == 0)
                power *= p;
            if (power > required_prime_power) required_prime_power = power;
        }
    }
#endif

    bool possible_max(unsigned long a, unsigned long r, const Rat &target) const {
        if (a == ~0UL) return true;
#ifdef REUSE_GMP_SCRATCH
        static thread_local Big lhs, rhs;
        __gmpz_mul_ui(lhs.v, target.p.v, a);
        __gmpz_mul_ui(lhs.v, lhs.v, a + 1);
        __gmpz_mul_ui(rhs.v, target.q.v, r);
#else
        Big lhs = mul_ui(mul_ui(target.p, a), a + 1);
        Big rhs = mul_ui(target.q, r);
#endif
        __gmpz_mul_ui(rhs.v, rhs.v, a);
        __gmpz_add(rhs.v, rhs.v, target.q.v);
        return __gmpz_cmp(lhs.v, rhs.v) <= 0;
    }

    virtual bool dfs(const Rat &target, unsigned long r, unsigned long previous) {
#ifdef DUMP_THREE_TASKS
        if (r == 3) {
            static unsigned long dumped = 0;
#ifdef DUMP_THREE_STRIDE
            const unsigned long stride = DUMP_THREE_STRIDE;
#else
            const unsigned long stride = 1;
#endif
            unsigned long first = previous + 1;
            if (first <= integer_bound(target, 3) && possible_max(first, 3, target)) {
                unsigned long sample = dumped++;
                if (sample % stride == 0 && sample / stride < DUMP_THREE_TASKS)
                    std::cout << str(target.p) << ' ' << str(target.q) << ' ' << previous << '\n';
            }
            return false;
        }
#endif
        ++nodes;
        if ((nodes & ((1u << 24) - 1)) == 0) {
            std::cerr << "nodes=" << nodes << " depth=" << path.size()
                      << " seconds=" << std::chrono::duration<double>(std::chrono::steady_clock::now() - started).count() << '\n';
        }
        if (r == 1) {
            if (__gmpz_cmp_ui(target.p.v, 1) == 0 && __gmpz_cmp_ui(target.q.v, previous) > 0) {
                final_denominator = target.q;
                return true;
            }
            return false;
        }
        Rat rest;
        Big qprime;
        if (r == 2) {
#ifdef DUMP_DENSE_TWO_TASKS
            Big dense_p_squared, dense_four_q;
            __gmpz_mul(dense_p_squared.v, target.p.v, target.p.v);
            dense_four_q = mul_ui(target.q, 4);
            if (__gmpz_cmp(dense_p_squared.v, dense_four_q.v) <= 0) {
                static unsigned long dumped_dense = 0;
                std::cout << str(target.p) << ' ' << str(target.q) << ' ' << previous << std::endl;
                if (++dumped_dense >= DUMP_DENSE_TWO_TASKS) std::exit(0);
            }
            return false;
#endif
#ifdef DUMP_TWO_TASKS
            static unsigned long dumped_two = 0;
#ifdef DUMP_TWO_STRIDE
            const unsigned long stride = DUMP_TWO_STRIDE;
#else
            const unsigned long stride = 1;
#endif
            unsigned long sample = dumped_two++;
            if (sample % stride == 0 && sample / stride < DUMP_TWO_TASKS)
                std::cout << str(target.p) << ' ' << str(target.q) << ' ' << previous << '\n';
            return false;
#endif
            Big twice_bound = mul_ui(target.q, 2);
            Big max_p = mul_ui(target.p, ~0UL);
            if (__gmpz_cmp(twice_bound.v, max_p.v) > 0) {
#ifdef CPU_TWO_TAIL_GCD_SQUARE
                if (quadratic_big_impossible(target, previous, &two_tail_gamma_bound)) return false;
#endif
                int code = solve_two_big(target, previous, penultimate_denominator, final_denominator);
                if (code == 1) return true;
                if (code == 0) return false;
                throw std::runtime_error("two-tail solver failed");
            }
            unsigned long lo = std::max(previous + 1, integer_bound(target, 1) + 1);
            unsigned long hi = integer_bound(target, 2);
            Big twice_q = mul_ui(target.q, 2);
            Big product = mul_ui(target.p, hi);
            if (__gmpz_cmp(twice_q.v, product.v) == 0) {
                if (hi == 0) return false;
                --hi;
            }
#ifdef PRIME_TAIL_PAIR
            if (lo <= hi) {
                int code = prime_pair_solve(target, previous, lo, hi, path, final_denominator);
                if (code >= 0) return code == 1;
            }
#endif
#ifdef TWO_TAIL_THRESHOLD
            if (hi >= lo && hi - lo > TWO_TAIL_THRESHOLD && __gmpz_cmp_ui(target.p.v, 1) > 0) {
                int code = solve_two_big(target, previous, penultimate_denominator, final_denominator);
                if (std::getenv("GPU_TWO_TRACE"))
                    std::cerr << "factor_two code=" << code << " previous=" << previous
                              << " lo=" << lo << " hi=" << hi << "\n";
                if (code == 1) return true;
                if (code == 0) return false;
            }
#endif
            Big p_squared, four_q;
            __gmpz_mul(p_squared.v, target.p.v, target.p.v);
            four_q = mul_ui(target.q, 4);
            bool monotone = __gmpz_cmp(p_squared.v, four_q.v) > 0;
#ifdef TWO_TAIL_BINARY_SEARCH
            if (monotone && hi >= lo && hi - lo >= TWO_TAIL_BINARY_SEARCH) {
                auto possible = [&](unsigned long a) {
                    Big difference = mul_ui(target.p, a);
                    __gmpz_sub(difference.v, difference.v, target.q.v);
                    Big square(a);
                    __gmpz_mul(square.v, square.v, square.v);
                    return __gmpz_cmp(difference.v, square.v) <= 0;
                };
                if (!possible(lo)) return false;
                unsigned long first = lo, last = hi;
                while (first < last) {
                    unsigned long mid = first + (last - first + 1) / 2;
                    if (possible(mid)) first = mid;
                    else last = mid - 1;
                }
                hi = first;
            }
#endif
            for (unsigned long a = lo; a <= hi; ++a) {
                Big difference = mul_ui(target.p, a);
                __gmpz_sub(difference.v, difference.v, target.q.v);
                Big square(a);
                __gmpz_mul(square.v, square.v, square.v);
                if (__gmpz_cmp(difference.v, square.v) > 0) {
                    if (monotone) break;
                    if (a == ~0UL) break;
                    continue;
                }
#ifdef DIVISOR_TWO_TAIL
                static const Big max_ulong(~0UL);
                unsigned long g = __gmpz_cmp(difference.v, max_ulong.v) <= 0
                    ? gcd_ui(a, __gmpz_get_ui(difference.v))
                    : gcd_ui(a, __gmpz_tdiv_ui(target.q.v, a));
                if (g <= 4294967295UL) {
                    if (__gmpz_cmp_ui(difference.v, 0) > 0 &&
                        __gmpz_cmp_ui(difference.v, g * g) <= 0) {
                        unsigned long h = __gmpz_get_ui(difference.v) / g;
                        if (g % h == 0) {
                            if (h == 0 || a % h != 0) throw std::runtime_error("invalid two-tail divisor reduction");
                            __gmpz_tdiv_q_ui(qprime.v, target.q.v, g);
                            Big denominator = mul_ui(qprime, a / h);
                            if (__gmpz_cmp_ui(denominator.v, a) > 0) {
                                path.emplace_back(a);
                                final_denominator = std::move(denominator);
                                return true;
                            }
                        }
                    }
                    if (a == ~0UL) break;
                    continue;
                }
#endif
                unit_op_into(target, a, true, rest, qprime);
                if (__gmpz_cmp_ui(rest.p.v, 1) == 0 && __gmpz_cmp_ui(rest.q.v, a) > 0) {
                    path.emplace_back(a);
                    final_denominator = rest.q;
                    return true;
                }
                if (a == ~0UL) break;
            }
            return false;
        }
#ifdef PRIME_POWER_INVARIANT
        if (required_prime_power > 1 && previous <= ~0UL - required_prime_power) {
            unsigned long multiple = (previous / required_prime_power + 1) * required_prime_power;
            if (multiple <= (~0UL - previous - 1) / (r - 1)) {
                Big left = mul_ui(mul_ui(target.p, multiple), previous + 1);
                Big right = mul_ui(target.q, (r - 1) * multiple + previous + 1);
                if (__gmpz_cmp(left.v, right.v) > 0) return false;
            }
        }
#endif
        unsigned long upper = integer_bound(target, r);
        unsigned long first = previous + 1;
        if (first > upper || !possible_max(first, r, target)) return false;
        unsigned long last = upper;
        while (first < last) {
            unsigned long mid = first + (last - first + 1) / 2;
            if (possible_max(mid, r, target)) first = mid;
            else last = mid - 1;
        }
        unsigned long first_candidate = previous + 1;
#ifdef FIRST_ADDED_DENOMINATOR
        if (r == 4 && path.empty()) {
            if (first_added_min) first_candidate = std::max(first_candidate, first_added_min);
            if (first_added_max) first = std::min(first, first_added_max);
            if (first_added) {
                if (first_added < previous + 1 || first_added > first) return false;
                first_candidate = first = first_added;
            }
            if (first_candidate > first) return false;
        }
#endif
#ifdef PRIME_FIRST_ROOT_R
        unsigned long preferred_prime = 0;
        if (r == PRIME_FIRST_ROOT_R && previous == 87) {
            for (unsigned long prime : {2UL, 3UL, 5UL, 7UL, 11UL, 13UL, 17UL, 19UL,
                                       23UL, 29UL, 31UL, 37UL, 41UL, 43UL, 47UL, 53UL,
                                       59UL, 61UL, 67UL, 71UL, 73UL, 79UL, 83UL}) {
                if (__gmpz_tdiv_ui(target.q.v, prime) == 0) preferred_prime = prime;
            }
        }
        for (unsigned pass = 0; pass < 2; ++pass) {
            if (pass == 0 && preferred_prime == 0) continue;
#endif
        for (unsigned long a = first_candidate; a <= first; ++a) {
#ifdef PRIME_FIRST_ROOT_R
            if (preferred_prime && ((a % preferred_prime == 0) != (pass == 0))) continue;
#endif
#ifdef FIRST_ADDED_DENOMINATOR
            if (r == 4 && path.empty() && first_added && a != first_added) continue;
#endif
#ifdef FOUR_PRIME_COVER
            if (r == 4 && four_cover_impossible(target, a)) continue;
#endif
#ifdef CPU_THREE_PAIR_GCD_SQUARE
            if (r == 3 && cpu_three_pair_gcd_square_impossible(target, a)) continue;
#endif
#ifdef CPU_THREE_PAIR_EXACT_GAMMA
            if (r == 3 && cpu_three_pair_impossible(target, a)) continue;
#endif
#ifdef CPU_TWO_TAIL_GCD_SQUARE
            unsigned long parent_gcd;
            unit_op_into(target, a, true, rest, qprime, &parent_gcd);
#else
            unit_op_into(target, a, true, rest, qprime);
#endif
            if (__gmpz_cmp_ui(rest.p.v, 0) <= 0) continue;
#ifdef LARGE_PRIME_COVER
            if (r >= 4 && large_prime_cover_impossible(target, a, r - 1, rest)) continue;
#endif
#ifdef DENOMINATOR_PRIME_POWER_COVER
            if (r > 3 && denominator_prime_power_impossible(rest, r - 1, a)) continue;
#endif
#ifdef CPU_TWO_TAIL_GCD_SQUARE
            Big saved_gamma = std::move(two_tail_gamma_bound);
            two_tail_gamma_bound = mul_ui(Big(parent_gcd), parent_gcd);
#endif
            path.emplace_back(a);
            bool found;
#ifdef PRIME_POWER_INVARIANT
            unsigned long saved_power = required_prime_power;
            if (saved_power > 1 && a % saved_power == 0) required_prime_power = 0;
            found = dfs(rest, r - 1, a);
            required_prime_power = saved_power;
#else
            found = dfs(rest, r - 1, a);
#endif
#ifdef CPU_TWO_TAIL_GCD_SQUARE
            two_tail_gamma_bound = std::move(saved_gamma);
#endif
            if (found) return true;
            path.pop_back();
            if (a == ~0UL) break;
        }
#ifdef PRIME_FIRST_ROOT_R
        }
#endif
        return false;
    }
};

void normalize(Rat &x) {
    Big g;
    __gmpz_gcd(g.v, x.p.v, x.q.v);
    if (__gmpz_cmp_ui(g.v, 1) > 0) {
        x.p = div_exact(x.p, g);
        x.q = div_exact(x.q, g);
    }
}

Rat rat_add(const Rat &x, const Rat &y) {
    Rat z;
    Big a, b;
    __gmpz_mul(a.v, x.p.v, y.q.v);
    __gmpz_mul(b.v, y.p.v, x.q.v);
    __gmpz_add(z.p.v, a.v, b.v);
    __gmpz_mul(z.q.v, x.q.v, y.q.v);
    normalize(z);
    return z;
}

Rat rat_sub(const Rat &x, const Rat &y) {
    Rat z;
    Big a, b;
    __gmpz_mul(a.v, x.p.v, y.q.v);
    __gmpz_mul(b.v, y.p.v, x.q.v);
    __gmpz_sub(z.p.v, a.v, b.v);
    __gmpz_mul(z.q.v, x.q.v, y.q.v);
    normalize(z);
    return z;
}

int compare(const Rat &x, const Rat &y) {
    Big a, b;
    __gmpz_mul(a.v, x.p.v, y.q.v);
    __gmpz_mul(b.v, y.p.v, x.q.v);
    return __gmpz_cmp(a.v, b.v);
}

#if defined(GPU_THREE) && defined(GPU_FOUR)
#include "gpu_four_hybrid.hpp"
#elif defined(GPU_THREE)
#include "gpu_three_hybrid.hpp"
#elif defined(GPU_TWO)
#include "gpu_hybrid.hpp"
#endif
#ifdef FACTOR_CACHED_SEARCH
#include "factor_cached_three.hpp"
#endif
#ifndef SEARCH_CLASS
#define SEARCH_CLASS Search
#endif

struct Symdiff {
    Symdiff(const std::vector<Rat> &h, unsigned long k, unsigned long prefix)
        : h(h), k(k), prefix(prefix), r(0) {}

    const std::vector<Rat> &h;
    unsigned long k, prefix, r;
    Rat delta, allowed;
    std::vector<Rat> min_removed;
    std::vector<unsigned long> removed;
    std::vector<Big> added;
    uint64_t xnodes = 0, ynodes = 0;

    bool enumerate_removed(const Rat &sum, unsigned long left, unsigned long previous) {
        ++xnodes;
        if (left == 0) {
            Rat target = rat_sub(sum, delta);
            if (__gmpz_cmp_ui(target.p.v, 0) <= 0) return false;
#if defined(DENOMINATOR_PRIME_POWER_COVER) && defined(DENOMINATOR_ROOT_COVER)
            if (denominator_prime_power_impossible(target, r, k)) return false;
#endif
            SEARCH_CLASS search;
#ifdef PRIME_POWER_INVARIANT
            search.require_largest_prime_power(target, k);
#endif
            bool found = search.dfs(target, r, k);
            ynodes += search.nodes;
            if (found) {
                added.clear();
                for (unsigned long a : search.path) added.emplace_back(a);
                if (__gmpz_cmp_ui(search.penultimate_denominator.v, 0) > 0) added.push_back(search.penultimate_denominator);
                added.push_back(search.final_denominator);
                return true;
            }
            return false;
        }
        Rat low_side = rat_add(min_removed[left], sum);
        if (compare(low_side, allowed) > 0) return false;
        Rat largest = rat_sub(h[previous + left], h[previous]);
        Rat high_side = rat_add(largest, sum);
        if (compare(high_side, delta) <= 0) return false;
        for (unsigned long x = previous + 1; x + left - 1 <= k; ++x) {
            Rat next = unit_add(sum, x);
            if (compare(next, allowed) > 0) continue;
            removed.push_back(x);
            if (enumerate_removed(next, left - 1, x)) return true;
            removed.pop_back();
        }
        return false;
    }

    bool run(unsigned long rmin, unsigned long rmax, unsigned long xmin, unsigned long xmax) {
        Rat zero;
        for (r = rmin; r <= rmax && r <= k - prefix; ++r) {
            Rat max_added = rat_sub(h[k + r], h[k]);
            allowed = rat_add(delta, max_added);
            min_removed.assign(k + 1, Rat());
            for (unsigned long j = 1; j <= r; ++j) min_removed[j] = rat_sub(h[k], h[k - j]);
            if (compare(min_removed[r], allowed) > 0) {
                std::cerr << "r-bound=" << r << '\n';
                return false;
            }
            removed.clear();
            xnodes = ynodes = 0;
            auto started = std::chrono::steady_clock::now();
            bool found = false;
            if (xmin == 0) {
                found = enumerate_removed(zero, r, prefix);
            } else {
                unsigned long last = std::min(xmax, k - r + 1);
                for (unsigned long x = std::max(xmin, prefix + 1); x <= last; ++x) {
                    Rat next = unit_add(zero, x);
                    if (compare(next, allowed) > 0) continue;
                    removed.push_back(x);
                    ++xnodes;
                    if (enumerate_removed(next, r - 1, x)) {
                        found = true;
                        break;
                    }
                    removed.pop_back();
                }
            }
            double seconds = std::chrono::duration<double>(std::chrono::steady_clock::now() - started).count();
            std::cerr << "r=" << r << " xnodes=" << xnodes << " ynodes=" << ynodes
                      << " seconds=" << seconds << " result=" << (found ? "yes" : "no") << '\n';
            if (found) return true;
        }
        return false;
    }
};

int main(int argc, char **argv) {
    if (argc < 3 || argc > 7) {
        std::cerr << "usage: symdiff N K [RMIN [RMAX [XMIN XMAX]]]\n";
        return 2;
    }
    unsigned long n = std::stoul(argv[1]);
    unsigned long k = std::stoul(argv[2]);
    unsigned long rmin = argc >= 4 ? std::stoul(argv[3]) : 1;
    unsigned long rmax = argc >= 5 ? std::stoul(argv[4]) : k;
    unsigned long xmin = argc >= 6 ? std::stoul(argv[5]) : 0;
    unsigned long xmax = argc >= 7 ? std::stoul(argv[6]) : k;
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
    if (__gmpz_cmp_ui(delta.p.v, 0) < 0) {
        std::cerr << "H_k < N; use a larger K\n";
        return 2;
    }
    std::cerr << "n=" << n << " k=" << k << " prefix=" << prefix
              << " delta=" << as_double(delta) << '\n';
    if (__gmpz_cmp_ui(delta.p.v, 0) == 0) {
        std::cout << n << " " << k << " :";
        for (unsigned long a = 1; a <= k; ++a) std::cout << " " << a;
        std::cout << '\n';
        return 0;
    }
    Symdiff search(h, k, prefix);
    search.delta = delta;
    if (!search.run(rmin, rmax, xmin, xmax)) return 1;
    std::cout << n << " " << k << " :";
    for (unsigned long a = 1; a <= k; ++a) {
        if (!std::binary_search(search.removed.begin(), search.removed.end(), a)) std::cout << " " << a;
    }
    for (const Big &a : search.added) std::cout << " " << str(a);
    std::cout << '\n';
    std::cerr << "removed:";
    for (unsigned long a : search.removed) std::cerr << " " << a;
    std::cerr << "\nadded:";
    for (const Big &a : search.added) std::cerr << " " << str(a);
    std::cerr << '\n';
    return 0;
}
