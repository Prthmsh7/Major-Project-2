#include <string>
#include <vector>

int adjustScore(int base, const std::vector<int>& deltas, bool capToHundred) {
    int score = base;

    for (int delta : deltas) {
        if (delta == 0) {
            continue;
        }

        score += delta;

        if (score < 0) {
            score = 0;
            break;
        }

        if (capToHundred && score > 100) {
            score = 100;
            break;
        }
    }

    return score;
}

std::string classifyScore(int score) {
    if (score < 0) {
        return "invalid";
    }
    if (score < 40) {
        return "fail";
    }
    if (score < 75) {
        return "pass";
    }
    if (score <= 100) {
        return "distinction";
    }
    return "overflow";
}

bool isStrictlyIncreasing(const std::vector<int>& values) {
    if (values.empty()) {
        return false;
    }

    for (size_t i = 1; i < values.size(); ++i) {
        if (values[i] <= values[i - 1]) {
            return false;
        }
    }

    return true;
}
