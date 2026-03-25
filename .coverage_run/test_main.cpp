#include "math_ops.cpp"
#include <cassert>
#include <iostream>

#include <cassert>
#include <iostream> // Required for std::cout in the original function

// Assuming calculate function is available in the scope, e.g., via an include or direct definition.
// For this exercise, we assume it's linked or included.

void test_llm_gen_1() {
    // Test case for addition (covers lines 3, 4, 5)
    assert(calculate(5, 3, '+') == 8);

    // Test case for subtraction (covers lines 3, 4(false), 6, 7)
    assert(calculate(10, 4, '-') == 6);

    // Test case for multiplication (covers lines 3, 4(false), 6(false), 8, 9)
    assert(calculate(2, 6, '*') == 12);

    // Test case for division with non-zero denominator (covers lines 3, 4(false), 6(false), 8(false), 10, 11, 12)
    assert(calculate(15, 3, '/') == 5);

    // Test case for division by zero (covers lines 3, 4(false), 6(false), 8(false), 10, 11(false), 14, 15)
    // Note: This will print "Division by zero!" to std::cout.
    assert(calculate(20, 0, '/') == 0);

    // Test case for unknown operation (covers lines 3, 4(false), 6(false), 8(false), 10(false), 18, 19, 20)
    // Note: This will print "Unknown operation." to std::cout.
    assert(calculate(7, 2, '%') == 0);
}

int main() {
    test_llm_gen_1();
    std::cout << "All tests passed successfully!\n";
    return 0;
}
