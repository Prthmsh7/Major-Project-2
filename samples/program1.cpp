#include <iostream>
using namespace std;
/*
 We're writing a code for testing purposes.
 We use this snippet because it has multiple branches and easy to reason about.
 We can use it for statement coverage
*/

int classify(int x) {
    if (x > 0)
        return 1;
    else if (x == 0)
        return 0;
    else
        return -1;
}

int main() {
    int x;
    cin >> x;
    cout << classify(x);
    return 0;
}