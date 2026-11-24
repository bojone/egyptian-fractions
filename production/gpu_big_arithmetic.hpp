#pragma once

HD int high_bit(const Big &a) {
    for (int i = LIMBS - 1; i >= 0; --i) {
        if (a.v[i]) return i * 64 + 63 - __builtin_clzll(a.v[i]);
    }
    return -1;
}

HD int divide_big(const Big &numerator, const Big &denominator,
                  Big &quotient, Big &remainder) {
    if (is_zero(denominator)) return 2;
    quotient = zero();
    remainder = zero();
    for (int bit = high_bit(numerator); bit >= 0; --bit) {
        bool carry = remainder.v[LIMBS - 1] >> 63;
        for (int i = LIMBS - 1; i > 0; --i)
            remainder.v[i] = (remainder.v[i] << 1) | (remainder.v[i - 1] >> 63);
        remainder.v[0] = (remainder.v[0] << 1) |
                         ((numerator.v[bit / 64] >> (bit % 64)) & 1);
        if (carry || cmp(remainder, denominator) >= 0) {
            remainder = sub(remainder, denominator);
            quotient.v[bit / 64] |= 1ULL << (bit % 64);
        }
    }
    return 0;
}

HD int negative_residue_big(const Big &s, const Big &p, Big &c, Big &e) {
    Big quotient, remainder;
    int code = divide_big(s, p, quotient, remainder);
    if (code) return code;
    c = quotient;
    if (is_zero(remainder)) {
        e = zero();
        return 0;
    }
    bool overflow = false;
    c = add(c, from64(1), overflow);
    if (overflow) return 2;
    e = sub(p, remainder);
    return 0;
}
