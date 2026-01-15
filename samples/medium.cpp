#include <iostream>
using namespace std;

int countEven(int n) {
    int count = 0;
    for (int i = 1; i <= n; i++) {
        if (i % 2 == 0) {
            count++;
        }
    }
    return count;
}

int main() {
    int n;
    cin >> n;
    cout << countEven(n);
    return 0;
}