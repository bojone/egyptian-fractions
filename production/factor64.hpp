#pragma once

#include <algorithm>
#include <cstdint>
#include <map>
#include <numeric>
#include <stdexcept>
#include <vector>

inline uint64_t factor64_mul_mod(uint64_t a, uint64_t b, uint64_t modulus) {
    return (unsigned __int128)a * b % modulus;
}

inline uint64_t factor64_add_mod(uint64_t a, uint64_t b, uint64_t modulus) {
    return ((unsigned __int128)a + b) % modulus;
}

inline uint64_t factor64_pow_mod(uint64_t a, uint64_t exponent, uint64_t modulus) {
    uint64_t result = 1;
    while (exponent) {
        if (exponent & 1) result = factor64_mul_mod(result, a, modulus);
        a = factor64_mul_mod(a, a, modulus);
        exponent >>= 1;
    }
    return result;
}

inline bool factor64_is_prime(uint64_t n) {
    if (n < 2) return false;
    for (uint64_t prime : {2ULL, 3ULL, 5ULL, 7ULL, 11ULL, 13ULL, 17ULL,
                          19ULL, 23ULL, 29ULL, 31ULL, 37ULL}) {
        if (n % prime == 0) return n == prime;
    }
    uint64_t d = n - 1;
    unsigned shift = 0;
    while ((d & 1) == 0) {
        d >>= 1;
        ++shift;
    }
    for (uint64_t base : {2ULL, 325ULL, 9375ULL, 28178ULL, 450775ULL,
                         9780504ULL, 1795265022ULL}) {
        if (base % n == 0) continue;
        uint64_t x = factor64_pow_mod(base % n, d, n);
        if (x == 1 || x == n - 1) continue;
        bool composite = true;
        for (unsigned i = 1; i < shift; ++i) {
            x = factor64_mul_mod(x, x, n);
            if (x == n - 1) {
                composite = false;
                break;
            }
        }
        if (composite) return false;
    }
    return true;
}

inline uint64_t factor64_brent(uint64_t n) {
    if (n % 2 == 0) return 2;
    if (n % 3 == 0) return 3;
    for (uint64_t seed = 1; seed <= 128; ++seed) {
        uint64_t x = seed % n;
        uint64_t y = x;
        uint64_t c = factor64_add_mod(seed, 1, n);
        for (unsigned iteration = 0; iteration < 2000000; ++iteration) {
            x = factor64_add_mod(factor64_mul_mod(x, x, n), c, n);
            y = factor64_add_mod(factor64_mul_mod(y, y, n), c, n);
            y = factor64_add_mod(factor64_mul_mod(y, y, n), c, n);
            uint64_t difference = x > y ? x - y : y - x;
            uint64_t divisor = std::gcd(difference, n);
            if (divisor > 1) {
                if (divisor < n) return divisor;
                break;
            }
        }
    }
    throw std::runtime_error("bounded 64-bit factorization failed");
}

inline void factor64_recursive(uint64_t n, std::map<uint64_t, unsigned> &factors) {
    if (n == 1) return;
    if (factor64_is_prime(n)) {
        ++factors[n];
        return;
    }
    uint64_t divisor;
    try {
        divisor = factor64_brent(n);
    } catch (const std::exception &error) {
        throw std::runtime_error("factorization of " + std::to_string(n) + ": " + error.what());
    }
    factor64_recursive(divisor, factors);
    factor64_recursive(n / divisor, factors);
}

inline std::map<uint64_t, unsigned> factor64_deterministic(uint64_t n) {
    if (n == 0) throw std::invalid_argument("cannot factor zero");
    std::map<uint64_t, unsigned> factors;
    factor64_recursive(n, factors);
    return factors;
}
