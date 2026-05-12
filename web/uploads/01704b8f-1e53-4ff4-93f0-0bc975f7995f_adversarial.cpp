#include <string>
#include <vector>
#include <numeric>
#include <stdexcept>

// -----------------------------------------------------------------------
// 1. COMBINATORIAL STATE MACHINE
//    Seven independent boolean flags produce 128 distinct states.
//    Only specific flag combinations reach the deeper return paths.
//    An LLM must enumerate the exact combinations — not just "try true/false".
// -----------------------------------------------------------------------
int stateMachine(bool a, bool b, bool c, bool d, bool e, bool f, bool g) {
    int state = 0;
    if (a) state |= 1;
    if (b) state |= 2;
    if (c) state |= 4;
    if (d) state |= 8;
    if (e) state |= 16;
    if (f) state |= 32;
    if (g) state |= 64;

    if (state == 0)   return -1;          // all false
    if (state == 127) return -2;          // all true
    if (state % 17 == 0) return -3;       // state ∈ {17,34,51,68,85,102}
    if (state % 13 == 0 && state % 7 != 0) return -4;
    if ((state & 0b0101010) == 0b0101010) return -5; // b,d,f all set
    if ((state & 0b1010101) == 0b1010101) return -6; // a,c,e,g all set
    if (__builtin_popcount(state) == 3)  return -7;  // exactly 3 flags set
    if (__builtin_popcount(state) == 4)  return -8;  // exactly 4 flags set
    return state;
}

// -----------------------------------------------------------------------
// 2. NUMERIC PRECISION CLIFF
//    Branches depend on exact arithmetic relationships.
//    Off-by-one inputs silently miss entire code paths.
// -----------------------------------------------------------------------
std::string classifyTriangle(int a, int b, int c) {
    if (a <= 0 || b <= 0 || c <= 0)
        return "invalid";

    long long sa = a, sb = b, sc = c;

    if (sa + sb <= sc || sa + sc <= sb || sb + sc <= sa)
        return "degenerate";

    long long a2 = sa*sa, b2 = sb*sb, c2 = sc*sc;

    // Sort so that c is the longest side
    if (a2 > c2) { std::swap(sa, sc); std::swap(a2, c2); }
    if (b2 > c2) { std::swap(sb, sc); std::swap(b2, c2); }

    if (sa == sb && sb == sc)
        return "equilateral";
    if (sa == sb || sb == sc || sa == sc)
        return "isosceles";
    if (a2 + b2 == c2)
        return "right-scalene";
    if (a2 + b2 > c2)
        return "acute-scalene";

    return "obtuse-scalene";
}

// -----------------------------------------------------------------------
// 3. RECURSIVE MUTUAL RECURSION WITH PARITY GUARD
//    Two functions call each other. The parity and magnitude of the input
//    determine which branch fires. An LLM must reason across call frames.
// -----------------------------------------------------------------------
static int helperB(int n, int depth);  // forward declaration

static int helperA(int n, int depth) {
    if (depth > 10) return 0;
    if (n == 0)     return 1;
    if (n < 0)      return -1;
    if (n % 2 == 0) return helperB(n / 2, depth + 1);
    return helperA(n - 1, depth + 1) + helperB(n - 1, depth + 1);
}

static int helperB(int n, int depth) {
    if (depth > 10) return 0;
    if (n == 0)     return 2;
    if (n < 0)      return -2;
    if (n % 3 == 0) return helperA(n / 3, depth + 1);
    return helperB(n - 1, depth + 1) * 2;
}

int mutualRecursion(int n) {
    if (n > 1000 || n < -1000) return -999;
    return helperA(n, 0);
}

// -----------------------------------------------------------------------
// 4. EXCEPTION-GUARDED PIPELINE
//    Multiple exception types are thrown under different precise conditions.
//    The LLM must trigger each throw site AND the no-throw path.
// -----------------------------------------------------------------------
static double safeDivide(double num, double den) {
    if (den == 0.0)
        throw std::domain_error("division by zero");
    return num / den;
}

static int parsePositive(const std::string& s) {
    if (s.empty())
        throw std::invalid_argument("empty string");
    for (char ch : s)
        if (ch < '0' || ch > '9')
            throw std::invalid_argument("non-digit character");
    int val = std::stoi(s);
    if (val <= 0)
        throw std::range_error("must be positive");
    return val;
}

double exceptionPipeline(const std::string& numStr,
                         const std::string& denStr) {
    try {
        int n = parsePositive(numStr);
        int d = parsePositive(denStr);
        return safeDivide(static_cast<double>(n),
                          static_cast<double>(d));
    } catch (const std::domain_error&) {
        return -1.0;
    } catch (const std::invalid_argument&) {
        return -2.0;
    } catch (const std::range_error&) {
        return -3.0;
    }
}

// -----------------------------------------------------------------------
// 5. ACCUMULATOR WITH HIDDEN SENTINEL INTERACTION
//    The result depends on the ORDER and VALUES of the vector elements.
//    Sentinels (0, negative, INT_MAX) alter internal state mid-loop,
//    and later elements behave differently depending on what came before.
// -----------------------------------------------------------------------
int accumulateWithSentinels(const std::vector<int>& values) {
    if (values.empty()) return 0;

    int result   = 0;
    bool locked  = false;
    bool inverted = false;
    int  skipNext = 0;

    for (size_t i = 0; i < values.size(); ++i) {
        int v = values[i];

        if (skipNext > 0) { --skipNext; continue; }  // skipped line

        if (v == 0) {
            locked = !locked;
            continue;
        }

        if (locked) {
            if (v < 0) result -= v;     // subtract a negative = add
            else        result += 0;    // locked: positive contributions blocked
            continue;
        }

        if (v == 2147483647) {          // INT_MAX sentinel
            inverted = !inverted;
            skipNext = 2;
            continue;
        }

        if (v < 0) {
            if (inverted) result += (-v);
            else          result -= 1;
            continue;
        }

        if (v % 7 == 0) {
            result += v * 2;
            continue;
        }

        if (inverted) result -= v;
        else          result += v;
    }

    return result;
}

// -----------------------------------------------------------------------
// 6. STRING CLASSIFIER WITH OVERLAPPING REGEX-LIKE RULES
//    Rules are checked in order; earlier matches shadow later ones.
//    Many strings look like they should match a later rule but are caught
//    by an earlier guard — the LLM must discover the shadowing.
// -----------------------------------------------------------------------
std::string classifyString(const std::string& s) {
    if (s.empty())                              return "empty";

    bool allDigits  = true;
    bool allAlpha   = true;
    bool hasUpper   = false;
    bool hasLower   = false;
    bool hasSpace   = false;
    bool hasPunct   = false;

    for (char c : s) {
        if (!isdigit(c))  allDigits = false;
        if (!isalpha(c))  allAlpha  = false;
        if (isupper(c))   hasUpper  = true;
        if (islower(c))   hasLower  = true;
        if (c == ' ')     hasSpace  = true;
        if (ispunct(c))   hasPunct  = true;
    }

    if (allDigits)                              return "numeric";
    if (allAlpha && hasUpper && !hasLower)      return "all-caps";
    if (allAlpha && !hasUpper && hasLower)      return "all-lower";
    if (allAlpha && hasUpper  && hasLower)      return "mixed-alpha";
    if (hasSpace && !hasPunct)                  return "sentence";
    if (hasSpace && hasPunct)                   return "punctuated-sentence";
    if (!hasSpace && hasPunct && !allDigits)    return "symbol-word";
    if (!hasSpace && !hasPunct && !allAlpha
        && !allDigits)                          return "alphanumeric";

    return "other";
}