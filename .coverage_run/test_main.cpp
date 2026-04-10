#include "math_ops.cpp"
#include <cassert>
#include <iostream>

void test_llm_gen_3() {
    // Cover lines 3, 4, 5 (addition)
    assert(calculate(5, 3, '+') == 8);

    // Cover lines 3, 6, 7 (subtraction)
    assert(calculate(10, 4, '-') == 6);

    // Cover lines 3, 8, 9 (multiplication)
    assert(calculate(2, 6, '*') == 12);

    // Cover lines 3, 10, 11, 12 (division, b != 0)
    assert(calculate(20, 5, '/') == 4);

    // Cover lines 3, 10, 13, 14, 15 (division by zero)
    // This will print "Division by zero!" to std::cout
    assert(calculate(10, 0, '/') == 0); 

    // Cover lines 3, 18, 19, 20 (unknown operation)
    // This will print "Unknown operation." to std::cout
    assert(calculate(7, 2, '%') == 0);
}

int main() {
    test_llm_gen_3();
    std::cout << "All tests passed successfully!\n";
    return 0;
}
