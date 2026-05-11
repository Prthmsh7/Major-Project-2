#include <iostream>
using namespace std;

bool validate(int arr[], int n) {
    if (n <= 0)
        return false;

    bool hasPositive = false;
    bool hasNegative = false;

    for (int i = 0; i < n; i++) {
        if (arr[i] > 0)
            hasPositive = true;
        else if (arr[i] < 0)
            hasNegative = true;

        if (hasPositive && hasNegative)
            return true;
    }

    return false;
}

int main() {
    int n;
    cin >> n;

    int arr[100];
    for (int i = 0; i < n; i++)
        cin >> arr[i];

    cout << validate(arr, n);
    return 0;
}