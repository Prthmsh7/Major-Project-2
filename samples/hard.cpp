#include <iostream>
using namespace std;

int process(int a, int b) {
    if (a == b)
        return 0;

    if (a > b) {
        if (b < 0)
            return a + b;
        else
            return a - b;
    } else {
        if (a < 0)
            return b - a;
        else
            return b + a;
    }
}

int main() {
    int a, b;
    cin >> a >> b;
    cout << process(a, b);
    return 0;
}