#include <iostream>
using namespace std;

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