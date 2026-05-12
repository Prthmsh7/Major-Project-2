#include <string>
#include <vector>

// -----------------------------------------------------------------------
// 1. GRADE CALCULATOR WITH INTERDEPENDENT BONUSES
//    The final grade depends on the interaction between attendance and
//    score — not just individual thresholds. Easy to miss edge paths.
// -----------------------------------------------------------------------
std::string calculateGrade(int score, int attendance, bool extraCredit) {
    if (score < 0 || score > 100 || attendance < 0 || attendance > 100)
        return "invalid";

    int effective = score;

    if (attendance >= 90 && effective < 100)
        effective += 5;

    if (extraCredit && effective < 100)
        effective += 3;

    if (effective > 100)
        effective = 100;

    if (effective >= 90) return "A";
    if (effective >= 75) return "B";
    if (effective >= 60) return "C";
    if (effective >= 40) return "D";
    return "F";
}

// -----------------------------------------------------------------------
// 2. RUN-LENGTH ENCODER
//    Edge cases: single char, all same, alternating, empty string.
//    The LLM tends to miss the final flush after the loop ends.
// -----------------------------------------------------------------------
std::string runLengthEncode(const std::string& s) {
    if (s.empty()) return "";

    std::string result;
    int count = 1;

    for (size_t i = 1; i < s.size(); ++i) {
        if (s[i] == s[i - 1]) {
            ++count;
        } else {
            result += s[i - 1];
            if (count > 1)
                result += std::to_string(count);
            count = 1;
        }
    }

    // Flush last group
    result += s.back();
    if (count > 1)
        result += std::to_string(count);

    return result;
}

// -----------------------------------------------------------------------
// 3. VECTOR STATS WITH SENTINEL BEHAVIOUR
//    Returns different codes based on content.
//    The -3 path (all equal) is easily confused with the normal path.
// -----------------------------------------------------------------------
int describeVector(const std::vector<int>& v) {
    if (v.empty())        return -1;
    if (v.size() == 1)    return -2;

    bool allEqual = true;
    bool hasDup   = false;
    int  minVal   = v[0];
    int  maxVal   = v[0];

    for (size_t i = 1; i < v.size(); ++i) {
        if (v[i] != v[0])     allEqual = false;
        if (v[i] == v[i - 1]) hasDup   = true;
        if (v[i] < minVal)    minVal = v[i];
        if (v[i] > maxVal)    maxVal = v[i];
    }

    if (allEqual)              return -3;
    if (maxVal - minVal == 1)  return -4;  // all values in a range of 1
    if (hasDup)                return -5;
    return maxVal - minVal;
}

// -----------------------------------------------------------------------
// 4. SIMPLE LOAN CLASSIFIER
//    Three independent inputs produce many interacting branches.
//    The "borderline" path is hit only when score is exactly 650–699
//    AND amount is above 50000 — a conjunction the LLM often misses.
// -----------------------------------------------------------------------
std::string classifyLoan(int creditScore, double amount, int termYears) {
    if (creditScore < 300 || creditScore > 850)  return "invalid";
    if (amount <= 0 || termYears <= 0)           return "invalid";

    if (creditScore >= 750) {
        if (amount <= 100000)  return "approved-standard";
        if (termYears <= 15)   return "approved-short";
        return "approved-long";
    }

    if (creditScore >= 700) {
        if (amount <= 50000)   return "approved-limited";
        return "review";
    }

    if (creditScore >= 650) {
        if (amount > 50000)    return "borderline";
        return "approved-small";
    }

    return "denied";
}