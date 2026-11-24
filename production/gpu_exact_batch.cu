#include <cuda_runtime.h>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>

#define HD __host__ __device__
#ifndef STAGE
#define STAGE 99
#endif
#ifndef FIXED_DEPTH
#define FIXED_DEPTH 3
#endif
#ifndef GPU_LIMBS
#define GPU_LIMBS 8
#endif
constexpr int LIMBS = GPU_LIMBS;
constexpr int WIDE = 2 * LIMBS;

struct Big { uint64_t v[LIMBS]; };
struct Wide { uint64_t v[WIDE]; };
struct Rat { Big p, q; bool negative; };
struct Constants {
    int n, k, r;
    Big m, delta, allowed;
    Big min_removed[16];
};
struct Result {
    int code;
    unsigned long long x[16], y[16];
    Big final_denominator;
};

HD Big zero() { Big a{}; return a; }
HD Big from64(uint64_t x) { Big a{}; a.v[0] = x; return a; }
HD bool is_zero(const Big &a) {
    uint64_t z = 0;
    for (int i = 0; i < LIMBS; ++i) z |= a.v[i];
    return z == 0;
}
HD int used_limbs(const Big &a) {
    int i = LIMBS - 1;
    while (i > 0 && a.v[i] == 0) --i;
    return i;
}
HD int cmp(const Big &a, const Big &b) {
#ifdef GPU_DYNAMIC_BIG
    int first = used_limbs(a) > used_limbs(b) ? used_limbs(a) : used_limbs(b);
#else
    int first = LIMBS - 1;
#endif
    for (int i = first; i >= 0; --i) {
        if (a.v[i] < b.v[i]) return -1;
        if (a.v[i] > b.v[i]) return 1;
    }
    return 0;
}
HD Big add(const Big &a, const Big &b, bool &overflow) {
    Big z{};
    unsigned __int128 carry = 0;
    for (int i = 0; i < LIMBS; ++i) {
        unsigned __int128 t = (unsigned __int128)a.v[i] + b.v[i] + carry;
        z.v[i] = (uint64_t)t;
        carry = t >> 64;
    }
    if (carry) overflow = true;
    return z;
}
HD Big sub(const Big &a, const Big &b) {
    Big z{};
    uint64_t borrow = 0;
    for (int i = 0; i < LIMBS; ++i) {
        uint64_t next_borrow = a.v[i] < b.v[i] || (borrow && a.v[i] == b.v[i]);
        z.v[i] = a.v[i] - b.v[i] - borrow;
        borrow = next_borrow;
    }
    return z;
}
HD Big mul_small(const Big &a, uint64_t b, bool &overflow) {
    Big z{};
    unsigned __int128 carry = 0;
#ifdef GPU_DYNAMIC_BIG
    int last = used_limbs(a);
#else
    int last = LIMBS - 1;
#endif
    for (int i = 0; i < LIMBS && (i <= last || carry); ++i) {
        unsigned __int128 t = (unsigned __int128)a.v[i] * b + carry;
        z.v[i] = (uint64_t)t;
        carry = t >> 64;
    }
    if (carry) overflow = true;
    return z;
}
HD uint64_t div_small(Big &a, uint64_t b) {
    unsigned __int128 remainder = 0;
#ifdef GPU_DYNAMIC_BIG
    int first = used_limbs(a);
#else
    int first = LIMBS - 1;
#endif
    for (int i = first; i >= 0; --i) {
        unsigned __int128 cur = (remainder << 64) | a.v[i];
        a.v[i] = (uint64_t)(cur / b);
        remainder = cur % b;
    }
    return (uint64_t)remainder;
}
HD uint64_t mod_small(const Big &a, uint64_t b) {
    unsigned __int128 remainder = 0;
#ifdef GPU_DYNAMIC_BIG
    int first = used_limbs(a);
#else
    int first = LIMBS - 1;
#endif
    for (int i = first; i >= 0; --i)
        remainder = ((remainder << 64) | a.v[i]) % b;
    return (uint64_t)remainder;
}
HD Wide mul_wide(const Big &a, const Big &b) {
    Wide z{};
    int b_size = 0;
    for (int j = 0; j < LIMBS; ++j) if (b.v[j]) b_size = j + 1;
    for (int i = 0; i < LIMBS; ++i) {
        if (!a.v[i]) continue;
        unsigned __int128 carry = 0;
        for (int j = 0; j < b_size; ++j) {
            unsigned __int128 t = (unsigned __int128)a.v[i] * b.v[j] + z.v[i + j] + carry;
            z.v[i + j] = (uint64_t)t;
            carry = t >> 64;
        }
        z.v[i + b_size] = (uint64_t)carry;
    }
    return z;
}
HD int cmp_wide(const Wide &a, const Wide &b) {
    for (int i = WIDE - 1; i >= 0; --i) {
        if (a.v[i] < b.v[i]) return -1;
        if (a.v[i] > b.v[i]) return 1;
    }
    return 0;
}
HD Wide wide_from_big(const Big &a) {
    Wide z{};
    for (int i = 0; i < LIMBS; ++i) z.v[i] = a.v[i];
    return z;
}
#ifdef GPU_GCD_BINARY
HD int gcd_ctz(uint64_t x) {
#ifdef __CUDA_ARCH__
    return __ffsll(x);
#else
    return __builtin_ctzll(x);
#endif
}
#endif
HD uint64_t gcd_ui(uint64_t a, uint64_t b) {
#ifdef GPU_GCD_BINARY
    if (!a) return b;
    if (!b) return a;
    int shift = gcd_ctz(a | b) - 1;
    a >>= gcd_ctz(a) - 1;
    do {
        b >>= gcd_ctz(b) - 1;
        if (a > b) {
            uint64_t t = a;
            a = b;
            b = t;
        }
        b -= a;
    } while (b);
    return a << shift;
#else
#ifdef GPU_GCD32
    if (a <= 0xffffffffULL && b <= 0xffffffffULL) {
        uint32_t u = (uint32_t)a, v = (uint32_t)b;
        while (v) { uint32_t t = u % v; u = v; v = t; }
        return u;
    }
#endif
    while (b) { uint64_t t = a % b; a = b; b = t; }
    return a;
#endif
}
HD double as_double(const Big &a) {
    int i = LIMBS - 1;
    while (i > 0 && a.v[i] == 0) --i;
    long double value = 0;
    for (int j = i; j >= 0 && j >= i - 2; --j) value = value * 18446744073709551616.0L + a.v[j];
    return (double)value;
}
HD double as_double(const Rat &a) { return as_double(a.p) / as_double(a.q); }

HD bool possible_max(uint64_t a, unsigned r, const Rat &target) {
    bool overflow = false;
    Big lhs = mul_small(target.p, a, overflow);
    lhs = mul_small(lhs, a + 1, overflow);
    Big rhs = mul_small(target.q, r, overflow);
    rhs = mul_small(rhs, a, overflow);
    rhs = add(rhs, target.q, overflow);
    return overflow || cmp(lhs, rhs) <= 0;
}

HD unsigned long long integer_bound(const Rat &x, unsigned r, bool &overflow) {
    long double estimate = (long double)r / as_double(x);
    if (!std::isfinite(estimate) || estimate < 0 || estimate >= 9007199254740991.0L) {
        overflow = true;
        return 0;
    }
    unsigned long long result = (unsigned long long)estimate;
    Big t = mul_small(x.q, r, overflow);
    if (overflow) return 0;
    while (cmp(mul_small(x.p, result, overflow), t) > 0) {
        if (overflow) return 0;
        if (result == 0) break;
        --result;
    }
    while (cmp(mul_small(x.p, result + 1, overflow), t) <= 0) {
        if (overflow) return 0;
        ++result;
    }
    return result;
}

HD int unit_denominator(const Rat &target, uint64_t previous, Big &denominator) {
    if (target.negative || is_zero(target.p)) return 0;
    if (is_zero(target.q)) return 0;
    if (cmp(target.p, from64(1)) == 0) {
        if (cmp(target.q, from64(previous)) > 0) {
            denominator = target.q;
            return 1;
        }
        return 0;
    }
    bool overflow = false;
    unsigned long long a = integer_bound(target, 1, overflow);
    if (overflow) return 2;
    if (a <= previous) return 0;
    if (cmp(mul_small(target.p, a, overflow), target.q) == 0) {
        denominator = from64(a);
        return 1;
    }
    return overflow ? 2 : 0;
}

HD int unit_op(const Rat &x, uint64_t a, Rat &z) {
    bool overflow = false;
    uint64_t g = gcd_ui(a, mod_small(x.q, a));
    Big qprime = x.q;
    div_small(qprime, g);
    Big left = mul_small(x.p, a / g, overflow);
    if (x.negative) {
        z.p = add(qprime, left, overflow);
        z.negative = true;
    } else if (cmp(left, qprime) >= 0) {
        z.p = sub(left, qprime);
        z.negative = false;
    } else {
        z.p = sub(qprime, left);
        z.negative = true;
    }
    z.q = mul_small(qprime, a, overflow);
    uint64_t h = gcd_ui(g, mod_small(z.p, g));
    if (h > 1) { div_small(z.p, h); div_small(z.q, h); }
    return overflow ? 2 : 0;
}

HD void normalize_small(Rat &x) {
    auto reduce = [&x](unsigned p) {
        while (mod_small(x.p, p) == 0 && mod_small(x.q, p) == 0) {
            div_small(x.p, p);
            div_small(x.q, p);
        }
    };
    reduce(2); reduce(3); reduce(5); reduce(7); reduce(11);
    reduce(13); reduce(17); reduce(19); reduce(23); reduce(29);
    reduce(31); reduce(37); reduce(41); reduce(43); reduce(47);
    reduce(53); reduce(59); reduce(61); reduce(67); reduce(71);
    reduce(73); reduce(79); reduce(83); reduce(89); reduce(97);
    reduce(101); reduce(103);
}

HD int unit_pair_divisor(const Rat &target, uint64_t a, const Big &difference,
                         uint64_t g, Big &denominator) {
    if (g > 4294967295ULL) return -1;
    uint64_t square = g * g;
    if (is_zero(difference) || cmp(difference, from64(square)) > 0) return 0;
    uint64_t h = difference.v[0] / g;
    if (g % h != 0) return 0;
    if (h == 0 || a % h != 0) return 2;
    Big qprime = target.q;
    div_small(qprime, g);
    bool overflow = false;
    denominator = mul_small(qprime, a / h, overflow);
    if (overflow) return 2;
    return cmp(denominator, from64(a)) > 0 ? 1 : 0;
}

HD bool three_pair_impossible(const Rat &target, uint64_t a, bool &error,
                             uint64_t *two_lower = nullptr) {
    if (a == ~0ULL) return false;
    Big product = mul_small(target.p, a, error);
    if (error || cmp(product, target.q) <= 0) return false;
    Big difference = sub(product, target.q);
    Big a_times_q = mul_small(target.q, a, error);
    if (error) return false;
    Rat reciprocal{difference, a_times_q, false};
    uint64_t b = integer_bound(reciprocal, 1, error) + 1;
    if (b < a + 1) b = a + 1;
    if (two_lower && !error) *two_lower = b;
    Big left = mul_small(difference, b, error);
    Big b_squared = mul_small(from64(b), b, error);
#ifdef THREE_PAIR_GAMMA_G_SQUARED
    if (error) return false;
#ifdef THREE_PAIR_GAMMA_G_SQUARED_ADAPTIVE
    if (cmp(left, a_times_q) <= 0) return false;
    Big a_squared = mul_small(from64(a), a, error);
    Wide coarse_remainder = wide_from_big(sub(left, a_times_q));
    if (cmp_wide(coarse_remainder, mul_wide(a_squared, b_squared)) > 0) {
        Big coarse_right = mul_small(a_times_q, a, error);
        coarse_right = mul_small(coarse_right, a, error);
        coarse_right = mul_small(coarse_right, 4, error);
        if (!error && cmp_wide(mul_wide(difference, difference), wide_from_big(coarse_right)) > 0)
            return true;
        error = false;
    }
#endif
    bool small_difference = true;
    for (int i = 1; i < LIMBS; ++i) small_difference &= difference.v[i] == 0;
#ifdef THREE_PAIR_GCD_DIFFERENCE
    auto active_mod = [](const Big &value, uint64_t modulus) {
        unsigned __int128 remainder = 0;
        for (int i = used_limbs(value); i >= 0; --i)
            remainder = ((remainder << 64) | value.v[i]) % modulus;
        return (uint64_t)remainder;
    };
    uint64_t g = small_difference
        ? gcd_ui(a, difference.v[0])
        : gcd_ui(a, active_mod(difference, a));
#else
    uint64_t g = small_difference
        ? gcd_ui(a, difference.v[0])
        : gcd_ui(a, mod_small(target.q, a));
#endif
    Big gamma = mul_small(from64(g), g, error);
    if (error || cmp(left, a_times_q) <= 0) return false;
    Wide remainder = wide_from_big(sub(left, a_times_q));
    if (cmp_wide(remainder, mul_wide(gamma, b_squared)) <= 0) return false;
    Big four_gamma_aq = mul_small(a_times_q, g, error);
    four_gamma_aq = mul_small(four_gamma_aq, g, error);
    four_gamma_aq = mul_small(four_gamma_aq, 4, error);
    if (!error) return cmp_wide(mul_wide(difference, difference), wide_from_big(four_gamma_aq)) > 0;
#ifdef THREE_PAIR_GAMMA_WIDE_FALLBACK
    error = false;
    Wide wide_right = mul_wide(a_times_q, gamma);
    unsigned __int128 carry = 0;
    for (int i = 0; i < WIDE; ++i) {
        unsigned __int128 next = (unsigned __int128)wide_right.v[i] * 4 + carry;
        wide_right.v[i] = (uint64_t)next;
        carry = next >> 64;
    }
    if (carry) return false;
    return cmp_wide(mul_wide(difference, difference), wide_right) > 0;
#else
    return false;
#endif
#elif defined(THREE_PAIR_GAMMA_EXACT_G2)
    if (error) return false;
    bool small_difference = true;
    for (int i = 1; i < LIMBS; ++i) small_difference &= difference.v[i] == 0;
    uint64_t g = small_difference
        ? gcd_ui(a, difference.v[0])
        : gcd_ui(a, mod_small(target.q, a));
    if (g > 4294967295ULL) return false;
    uint64_t square = g * g;
    uint64_t gamma = gcd_ui(square, mod_small(difference, square));
    if (cmp(left, a_times_q) <= 0) return false;
    Wide remainder = wide_from_big(sub(left, a_times_q));
    if (cmp_wide(remainder, mul_wide(from64(gamma), b_squared)) <= 0) return false;
    Big four_gamma_aq = mul_small(a_times_q, gamma, error);
    four_gamma_aq = mul_small(four_gamma_aq, 4, error);
    if (error) return false;
    return cmp_wide(mul_wide(difference, difference), wide_from_big(four_gamma_aq)) > 0;
#elif defined(THREE_PAIR_EXACT_GAMMA)
    if (error) return false;
    uint64_t gamma;
#ifdef THREE_PAIR_GAMMA_A_SQUARED
    if (a <= 4294967295ULL) {
        uint64_t square = a * a;
        gamma = gcd_ui(square, mod_small(difference, square));
    } else {
#endif
    bool small_difference = true;
    for (int i = 1; i < LIMBS; ++i) small_difference &= difference.v[i] == 0;
    uint64_t g = small_difference
        ? gcd_ui(a, difference.v[0])
        : gcd_ui(a, mod_small(target.q, a));
    Big quotient = difference;
    if (div_small(quotient, g) != 0) {
        error = true;
        return false;
    }
    uint64_t h = gcd_ui(g, mod_small(quotient, g));
    if (h == 0 || g > ~0ULL / h) {
        error = true;
        return false;
    }
    gamma = g * h;
#ifdef THREE_PAIR_GAMMA_A_SQUARED
    }
#endif
    if (cmp(left, a_times_q) <= 0) return false;
    Wide remainder = wide_from_big(sub(left, a_times_q));
    if (cmp_wide(remainder, mul_wide(from64(gamma), b_squared)) <= 0) return false;
    Big four_gamma_aq = mul_small(a_times_q, gamma, error);
    four_gamma_aq = mul_small(four_gamma_aq, 4, error);
    if (error) return false;
    return cmp_wide(mul_wide(difference, difference), wide_from_big(four_gamma_aq)) > 0;
#else
    Big a_squared = mul_small(from64(a), a, error);
    if (error || cmp(left, a_times_q) <= 0) return false;
    Wide remainder = wide_from_big(sub(left, a_times_q));
    if (cmp_wide(remainder, mul_wide(a_squared, b_squared)) <= 0) return false;
    Big four_a_cubed_q = mul_small(a_times_q, a, error);
    four_a_cubed_q = mul_small(four_a_cubed_q, a, error);
    four_a_cubed_q = mul_small(four_a_cubed_q, 4, error);
    if (error) return false;
    return cmp_wide(mul_wide(difference, difference), wide_from_big(four_a_cubed_q)) > 0;
#endif
}

HD int search_y(const Rat &target, unsigned r, uint64_t previous, Result &result, int depth,
                int *stop = nullptr, uint64_t two_lower = 0) {
    if (r == 1) {
        Big denominator;
        int code = unit_denominator(target, previous, denominator);
        if (code == 1) result.final_denominator = denominator;
        return code;
    }
    if (r == 2) {
        bool overflow = false;
#ifdef THREE_REUSE_TWO_LOWER_BOUND
        unsigned long long lo = two_lower ? two_lower : integer_bound(target, 1, overflow) + 1;
        if (two_lower && two_lower < previous + 1) return 2;
#else
        unsigned long long lo = integer_bound(target, 1, overflow) + 1;
#endif
        if (previous + 1 > lo) lo = previous + 1;
        unsigned long long hi = integer_bound(target, 2, overflow);
        if (overflow) return 2;
        if (cmp(mul_small(target.q, 2, overflow), mul_small(target.p, hi, overflow)) == 0) {
            if (hi == 0) return 0;
            --hi;
        }
        Wide p_squared = mul_wide(target.p, target.p);
        Wide four_q = wide_from_big(mul_small(target.q, 4, overflow));
        bool monotone = cmp_wide(p_squared, four_q) > 0;
#ifdef TWO_TAIL_BINARY_SEARCH
        if (monotone && hi >= lo && hi - lo >= TWO_TAIL_BINARY_SEARCH && !overflow) {
            auto possible = [&](unsigned long long a, bool &error) {
                bool local_overflow = false;
                Big difference = sub(mul_small(target.p, a, local_overflow), target.q);
                Big square = mul_small(from64(a), a, local_overflow);
                error = local_overflow;
                return cmp(difference, square) <= 0;
            };
            bool numeric_error = false;
            if (!possible(lo, numeric_error)) return numeric_error ? 2 : 0;
            unsigned long long first = lo, last = hi;
            while (first < last) {
                unsigned long long mid = first + (last - first + 1) / 2;
                if (possible(mid, numeric_error)) first = mid;
                else last = mid - 1;
                if (numeric_error) return 2;
            }
            hi = first;
        }
#endif
#if defined(GPU_TWO_RANGE_LIMIT) && defined(QUADRATIC_RANGE_LIMIT)
        if (stop && hi >= lo && hi - lo > GPU_TWO_RANGE_LIMIT && !overflow) {
            if (monotone) {
                auto possible = [&](unsigned long long a, bool &error) {
                    bool local_overflow = false;
                    Big difference = sub(mul_small(target.p, a, local_overflow), target.q);
                    Big square = mul_small(from64(a), a, local_overflow);
                    error = local_overflow;
                    return cmp(difference, square) <= 0;
                };
                bool numeric_error = false;
                bool first_possible = possible(lo, numeric_error);
                if (numeric_error) return 2;
                if (!first_possible) return 0;
                unsigned long long first = lo, last = hi;
                while (first < last) {
                    unsigned long long mid = first + (last - first + 1) / 2;
                    if (possible(mid, numeric_error)) first = mid;
                    else last = mid - 1;
                    if (numeric_error) return 2;
                }
                hi = first;
            }
            if (hi >= lo && hi - lo > GPU_TWO_RANGE_LIMIT) return 2;
        }
#elif defined(GPU_TWO_RANGE_LIMIT)
        if (stop && hi >= lo && hi - lo > GPU_TWO_RANGE_LIMIT) return 2;
#endif
        for (unsigned long long a = lo; a <= hi; ++a) {
#ifdef __CUDA_ARCH__
            if (stop && (a & 63) == 0 && atomicAdd(stop, 0) >= 0) return 0;
#endif
            Big difference = sub(mul_small(target.p, a, overflow), target.q);
            Big square = mul_small(from64(a), a, overflow);
            if (!overflow && cmp(difference, square) > 0) {
                if (monotone) break;
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
            Big gcd_square = mul_small(from64(g), g, overflow);
            if (!overflow && cmp(difference, gcd_square) > 0) continue;
#ifdef DIVISOR_TWO_TAIL
            if (overflow) return 2;
            Big pair_denominator;
            int pair_code = unit_pair_divisor(target, a, difference, g, pair_denominator);
            if (pair_code == 2) return 2;
            if (pair_code == 1) {
                result.y[depth] = a;
                result.final_denominator = pair_denominator;
                return 1;
            }
            if (pair_code == 0) {
                if (a == ~0ULL) break;
                continue;
            }
#endif
            Rat rest;
            int code = unit_op(target, a, rest);
            if (code) return code;
            if (rest.negative || is_zero(rest.p)) continue;
            Big denominator;
            code = unit_denominator(rest, a, denominator);
            if (code == 2) return 2;
            if (code == 1) {
                result.y[depth] = a;
                result.final_denominator = denominator;
                return 1;
            }
            if (a == ~0ULL) break;
        }
        return overflow ? 2 : 0;
    }
    bool overflow = false;
    unsigned long long last = integer_bound(target, r, overflow);
    if (overflow) return 2;
    for (unsigned long long a = previous + 1; a <= last; ++a) {
        if (!possible_max(a, r, target)) break;
#ifdef THREE_PAIR_LIFT
        if (r == 3 && three_pair_impossible(target, a, overflow)) continue;
        if (overflow) return 2;
#endif
        Rat rest;
        int code = unit_op(target, a, rest);
        if (code) return code;
        if (rest.negative || is_zero(rest.p)) continue;
        result.y[depth] = a;
        code = search_y(rest, r - 1, a, result, depth + 1, stop);
        if (code) return code;
        if (a == ~0ULL) break;
    }
    return 0;
}

#ifndef GPU_TWO_ONLY
HD int search_split(const Rat &target, unsigned r, uint64_t previous,
                    Result &result, int depth, unsigned lane) {
    bool overflow = false;
    unsigned long long last = integer_bound(target, r, overflow);
    if (overflow) return 2;
    for (unsigned long long a = previous + 1 + lane; a <= last; a += 32) {
        if (!possible_max(a, r, target)) break;
        Rat rest;
        int code = unit_op(target, a, rest);
        if (code) return code;
        if (rest.negative || is_zero(rest.p)) continue;
        result.y[depth] = a;
        code = search_y(rest, r - 1, a, result, depth + 1);
        if (code) return code;
        if (a > ~0ULL - 32) break;
    }
    return 0;
}

HD int search_root(const Rat &target, unsigned r, uint64_t previous,
                   Result &result, unsigned lane) {
    if (r <= 4) return search_split(target, r, previous, result, 0, lane);
    return search_y(target, r, previous, result, 0);
}

__device__ int search_root_block(const Rat &target, unsigned r, uint64_t previous,
                                 Result &result, int &status, unsigned lane) {
    if (lane == 0) status = 0;
    __syncthreads();
    bool overflow = false;
    unsigned long long last = integer_bound(target, r, overflow);
    if (overflow) return 2;
    for (unsigned long long first = previous + 1; first <= last; ++first) {
        if (!possible_max(first, r, target)) break;
        Rat rest;
        int root_code = unit_op(target, first, rest);
        if (root_code) return root_code;
        if (rest.negative || is_zero(rest.p)) continue;
        overflow = false;
        unsigned long long second_last = integer_bound(rest, r - 1, overflow);
        if (overflow) {
            if (lane == 0) status = 2;
            __syncthreads();
            return 2;
        }
        if (r <= 5) {
            for (unsigned long long second = first + 1 + lane; second <= second_last; second += 32) {
                if (!possible_max(second, r - 1, rest)) break;
                Rat next;
                int code = unit_op(rest, second, next);
                if (!code && !next.negative && !is_zero(next.p)) {
                    result.y[0] = first;
                    result.y[1] = second;
                    code = search_y(next, r - 2, second, result, 2);
                }
                if (code) {
                    if (code == 1) result.code = 1;
                    atomicMax(&status, code);
                    break;
                }
                if (second > ~0ULL - 32) break;
            }
            __syncthreads();
        } else {
            for (unsigned long long second = first + 1; second <= second_last; ++second) {
                if (!possible_max(second, r - 1, rest)) break;
                Rat next;
                int second_code = unit_op(rest, second, next);
                if (second_code) return second_code;
                if (next.negative || is_zero(next.p)) continue;
                overflow = false;
                unsigned long long third_last = integer_bound(next, r - 2, overflow);
                if (overflow) {
                    if (lane == 0) status = 2;
                    __syncthreads();
                    return 2;
                }
                for (unsigned long long third = second + 1 + lane; third <= third_last; third += 32) {
                    if (!possible_max(third, r - 2, next)) break;
                    Rat after;
                    int code = unit_op(next, third, after);
                    if (!code && !after.negative && !is_zero(after.p)) {
                        result.y[0] = first;
                        result.y[1] = second;
                        result.y[2] = third;
                        code = search_y(after, r - 3, third, result, 3);
                    }
                    if (code) {
                        if (code == 1) result.code = 1;
                        atomicMax(&status, code);
                        break;
                    }
                    if (third > ~0ULL - 32) break;
                }
                __syncthreads();
                if (status) return status;
                if (second == ~0ULL) break;
            }
        }
        if (status) return status;
        if (first == ~0ULL) break;
    }
    return 0;
}

#ifndef CACHE_SIZE
#define CACHE_SIZE 262144
#endif

HD unsigned allocate_target(unsigned &count) {
#ifdef __CUDA_ARCH__
    return atomicAdd(&count, 1);
#else
    return count++;
#endif
}

HD int enumerate_x(const Constants &c, const Big &sum, unsigned left,
                   uint64_t previous, Result &result, int depth,
                   Rat *cache, unsigned long long (*cache_x)[16], unsigned &count) {
    if (left == 0) {
        if (cmp(sum, c.delta) <= 0) return 0;
        unsigned index = allocate_target(count);
        if (index >= CACHE_SIZE) return 3;
        Rat target{sub(sum, c.delta), c.m, false};
        normalize_small(target);
        cache[index] = target;
        for (int i = 0; i < c.r; ++i) cache_x[index][i] = result.x[i];
        return 0;
    }
    bool overflow = false;
    Big low = add(sum, c.min_removed[left], overflow);
    if (cmp(low, c.allowed) > 0) return overflow ? 2 : 0;
    Big high = sum;
    for (unsigned j = 0; j < left; ++j) {
        Big term = c.m;
        div_small(term, previous + j + 1);
        high = add(high, term, overflow);
    }
    if (cmp(high, c.delta) <= 0) return overflow ? 2 : 0;
    for (uint64_t x = previous + 1; x + left - 1 <= (uint64_t)c.k; ++x) {
        Big term = c.m;
        div_small(term, x);
        Big next = add(sum, term, overflow);
        if (cmp(next, c.allowed) > 0) continue;
        result.x[depth] = x;
        int code = enumerate_x(c, next, left - 1, x, result, depth + 1, cache, cache_x, count);
        if (code) return code;
    }
    return overflow ? 2 : 0;
}

HD int enumerate_x_split(const Constants &c, const Big &sum, unsigned left,
                         uint64_t previous, Result &result, int depth,
                         Rat *cache, unsigned long long (*cache_x)[16],
                         unsigned &count, unsigned lane) {
    if (left == 0) {
        if (depth == FIXED_DEPTH && lane != 0) return 0;
        return enumerate_x(c, sum, 0, previous, result, depth, cache, cache_x, count);
    }
    bool overflow = false;
    Big low = add(sum, c.min_removed[left], overflow);
    if (cmp(low, c.allowed) > 0) return overflow ? 2 : 0;
    Big high = sum;
    for (unsigned j = 0; j < left; ++j) {
        Big term = c.m;
        div_small(term, previous + j + 1);
        high = add(high, term, overflow);
    }
    if (cmp(high, c.delta) <= 0) return overflow ? 2 : 0;
    for (uint64_t x = previous + 1 + lane; x + left - 1 <= (uint64_t)c.k; x += 32) {
        Big term = c.m;
        div_small(term, x);
        Big next = add(sum, term, overflow);
        if (cmp(next, c.allowed) > 0) continue;
        result.x[depth] = x;
        int code = enumerate_x(c, next, left - 1, x, result, depth + 1, cache, cache_x, count);
        if (code) return code;
        if (x > ~0ULL - 32) break;
    }
    return overflow ? 2 : 0;
}

struct Task { unsigned long long x[FIXED_DEPTH]; };

__global__ void exact_kernel(const Constants *c, const Task *tasks, Result *output,
                             Rat *cache, unsigned long long (*cache_x)[16], int count) {
    int task_id = blockIdx.x;
    unsigned lane = threadIdx.x;
    if (task_id >= count) return;
    __shared__ unsigned target_count;
    __shared__ int x_error;
    __shared__ int y_status;
    cache += task_id * CACHE_SIZE;
    cache_x += task_id * CACHE_SIZE;
    Task task = tasks[task_id];
    Result &result = output[task_id * 32 + lane];
    result.code = 0;
    Big sum{};
    for (int i = 0; i < FIXED_DEPTH; ++i) {
        unsigned long long a = task.x[i];
        result.x[i] = a;
        Big term = c->m;
        div_small(term, a);
        bool overflow = false;
        sum = add(sum, term, overflow);
        if (overflow) { result.code = 2; return; }
    }
    if (lane == 0) {
        target_count = 0;
        x_error = 0;
    }
    __syncthreads();
    int code = enumerate_x_split(*c, sum, c->r - FIXED_DEPTH,
                                 task.x[FIXED_DEPTH - 1], result, FIXED_DEPTH,
                                 cache, cache_x, target_count, lane);
    if (code) atomicMax(&x_error, code);
    __syncthreads();
    if (x_error) { result.code = x_error; return; }
    for (unsigned i = 0; i < target_count; ++i) {
        for (int j = 0; j < c->r; ++j) result.x[j] = cache_x[i][j];
        code = c->r > 3 ? search_root_block(cache[i], c->r, c->k, result, y_status, lane)
                        : search_root(cache[i], c->r, c->k, result, lane);
        if (code != 0) {
            if (result.code != 1) result.code = (code == 1 && c->r > 3) ? 0 : code;
            break;
        }
    }
}

Constants make_constants(int n, int k, int r) {
    Constants c{};
    c.n = n; c.k = k; c.r = r;
    c.m = from64(1);
    for (int i = 2; i <= k + r; ++i) {
        uint64_t g = gcd_ui(mod_small(c.m, i), i);
        div_small(c.m, g);
        bool overflow = false;
        c.m = mul_small(c.m, i, overflow);
        if (overflow) { std::fprintf(stderr, "constant overflow\n"); std::exit(2); }
    }
    bool overflow = false;
    for (int i = 1; i <= k; ++i) {
        Big term = c.m; div_small(term, i);
        c.delta = add(c.delta, term, overflow);
    }
    c.delta = sub(c.delta, mul_small(c.m, n, overflow));
    for (int i = 1; i <= k + r; ++i) {
        Big term = c.m; div_small(term, i);
        c.allowed = add(c.allowed, term, overflow);
    }
    c.allowed = sub(c.allowed, mul_small(c.m, n, overflow));
    for (int j = 1; j <= r; ++j) {
        Big term = c.m; div_small(term, k - j + 1);
        c.min_removed[j] = add(c.min_removed[j - 1], term, overflow);
    }
    return c;
}

void print_big(Big a) {
    if (is_zero(a)) { std::printf("0"); return; }
    unsigned parts[64];
    int count = 0;
    while (!is_zero(a)) {
        parts[count++] = div_small(a, 1000000000);
    }
    std::printf("%u", parts[count - 1]);
    for (int i = count - 2; i >= 0; --i) std::printf("%09u", parts[i]);
}

int main(int argc, char **argv) {
    if (argc != 7) {
        std::fprintf(stderr, "usage: gpu_exact_batch DEVICE N K R INPUT.bin OUTPUT.bin\n");
        return 2;
    }
    int device = std::atoi(argv[1]);
    int n = std::atoi(argv[2]), k = std::atoi(argv[3]), r = std::atoi(argv[4]);
    cudaSetDevice(device);
    FILE *input = std::fopen(argv[5], "rb");
    if (!input) return 2;
    uint32_t count;
    if (std::fread(&count, sizeof(count), 1, input) != 1) return 2;
    Task *tasks = (Task *)std::malloc(count * sizeof(Task));
    Result *results = (Result *)std::malloc(count * 32 * sizeof(Result));
    if (std::fread(tasks, sizeof(Task), count, input) != count) return 2;
    std::fclose(input);
    Constants c = make_constants(n, k, r);
    Constants *device_c;
    Task *device_tasks;
    Result *device_results;
    Rat *cache;
    unsigned long long (*cache_x)[16];
    cudaError_t error = cudaMalloc(&device_c, sizeof(c));
    if (error == cudaSuccess) error = cudaMalloc(&device_tasks, count * sizeof(Task));
    if (error == cudaSuccess) error = cudaMalloc(&device_results, count * 32 * sizeof(Result));
    if (error == cudaSuccess) error = cudaMalloc(&cache, (size_t)count * CACHE_SIZE * sizeof(Rat));
    if (error == cudaSuccess) error = cudaMalloc(&cache_x, (size_t)count * CACHE_SIZE * sizeof(*cache_x));
    if (error != cudaSuccess) {
        std::fprintf(stderr, "CUDA allocation error: %s\n", cudaGetErrorString(error));
        return 2;
    }
    cudaMemcpy(device_c, &c, sizeof(c), cudaMemcpyHostToDevice);
    cudaMemcpy(device_tasks, tasks, count * sizeof(Task), cudaMemcpyHostToDevice);
    cudaDeviceSetLimit(cudaLimitStackSize, 262144);
    exact_kernel<<<count, 32>>>(device_c, device_tasks, device_results, cache, cache_x, count);
    error = cudaDeviceSynchronize();
    if (error != cudaSuccess) {
        std::fprintf(stderr, "CUDA error: %s\n", cudaGetErrorString(error));
        return 2;
    }
    cudaMemcpy(results, device_results, count * 32 * sizeof(Result), cudaMemcpyDeviceToHost);
    int found = 0, overflow = 0, cache_full = 0, numeric_overflow = 0;
    for (uint32_t i = 0; i < count; ++i) {
        int task_code = 0;
        bool has_cache_full = false, has_numeric_overflow = false;
        for (int lane = 0; lane < 32; ++lane) {
            int code = results[i * 32 + lane].code;
            if (code == 1) { task_code = 1; break; }
            if (code == 3) has_cache_full = true;
            if (code == 2) has_numeric_overflow = true;
            if (code >= 2) task_code = 2;
            if (code >= 2) results[i * 32 + lane].code = 2;
        }
        if (task_code == 1) ++found;
        if (task_code == 2) ++overflow;
        if (task_code == 2 && has_cache_full && !has_numeric_overflow) ++cache_full;
        if (task_code == 2 && has_numeric_overflow) ++numeric_overflow;
    }
    FILE *output = std::fopen(argv[6], "wb");
    if (!output) return 2;
    std::fwrite(results, sizeof(Result), count * 32, output);
    std::fclose(output);
    std::fprintf(stderr, "device=%d tasks=%u no=%u found=%d overflow=%d cache=%d numeric=%d\n",
                 device, count, count - found - overflow, found, overflow, cache_full, numeric_overflow);
    cudaFree(device_c); cudaFree(device_tasks); cudaFree(device_results);
    cudaFree(cache); cudaFree(cache_x);
    std::free(tasks); std::free(results);
    return 0;
}
#endif
