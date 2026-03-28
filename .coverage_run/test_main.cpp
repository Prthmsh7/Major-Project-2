#include "advanced_logic.cpp"
#include <cassert>
#include <iostream>

#include <cassert>
#include <vector>
#include <string>

void test_llm_gen_1() {
    // Test adjustScore function
    // Covers lines: 4, 5, 7, 12, 25 (basic path)
    assert(adjustScore(50, {10}, false) == 60);
    // Covers lines: 8, 9 (delta == 0 continue)
    assert(adjustScore(50, {0, 10}, false) == 60);
    // Covers lines: 14, 15, 16 (score < 0, break)
    assert(adjustScore(10, {-20}, false) == 0);
    // Covers lines: 19, 20, 21 (capToHundred && score > 100, break)
    assert(adjustScore(90, {20}, true) == 100);
    // Test a combination to ensure other paths are hit
    assert(adjustScore(70, {10, 0, 30, -5}, true) == 100); // 70+10=80, 0 skip, 80+30=110 -> 100 (break)

    // Test classifyScore function
    // Covers lines: 28, 29, 30 (score < 0)
    assert(classifyScore(-1) == "invalid");
    // Covers lines: 32, 33 (score < 40)
    assert(classifyScore(0) == "fail");
    assert(classifyScore(39) == "fail");
    // Covers lines: 35, 36 (score < 75)
    assert(classifyScore(40) == "pass");
    assert(classifyScore(74) == "pass");
    // Covers lines: 38, 39 (score <= 100)
    assert(classifyScore(75) == "distinction");
    assert(classifyScore(100) == "distinction");
    // Covers lines: 41, 42 (score > 100)
    assert(classifyScore(101) == "overflow");

    // Test isStrictlyIncreasing function
    // Covers lines: 44, 45, 46 (empty vector)
    assert(isStrictlyIncreasing({}) == false);
    // Covers lines: 44, 49, 55, 56 (single element, loop not entered)
    assert(isStrictlyIncreasing({5}) == true);
    // Covers lines: 49, 50, 51 (not strictly increasing, values[i] <= values[i-1])
    assert(isStrictlyIncreasing({1, 1}) == false);
    assert(isStrictlyIncreasing({1, 0}) == false);
    assert(isStrictlyIncreasing({1, 2, 1}) == false);
    // Covers lines: 44, 49, 53, 55, 56 (strictly increasing)
    assert(isStrictlyIncreasing({1, 2, 3}) == true);
}

int main() {
    test_llm_gen_1();
    std::cout << "All tests passed successfully!\n";
    return 0;
}
