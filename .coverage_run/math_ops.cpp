#include <iostream>

int calculate(int a, int b, char op) {
    if (op == '+') {
        return a + b;
    } else if (op == '-') {
        return a - b;
    } else if (op == '*') {
        return a * b;
    } else if (op == '/') {
        if (b != 0) {
            return a / b;
        } else {
            std::cout << "Division by zero!" << std::endl;
            return 0;
        }
    }
    std::cout << "Unknown operation." << std::endl;
    return 0;
}
