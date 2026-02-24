#include <iostream>
#include <cmath>
#include "../src/fpga_systolic_array.h"

int main(void) {
    float A[MAX_SIZE][MAX_SIZE];
    float B[MAX_SIZE][MAX_SIZE];
    float C_hw[MAX_SIZE][MAX_SIZE]; // HLS output
    float C_sw[MAX_SIZE][MAX_SIZE]; // Software output

    // 1. Initialize matrices with test data
    for (int i = 0; i < MAX_SIZE; i++) {
        for (int j = 0; j < MAX_SIZE; j++) {
            A[i][j] = (float)(rand() % 1000);
            B[i][j] = (float)(rand() % 1000);
            C_hw[i][j] = 0.0f;
            C_sw[i][j] = 0.0f;
        }
    }

    // 2. Run the HLS Hardware Function
    systolic_mm(A, B, C_hw);

    // 3. Run a standard software matrix multiply for comparison
    for (int i = 0; i < MAX_SIZE; i++) {
        for (int j = 0; j < MAX_SIZE; j++) {
            float sum = 0.0f;
            for (int k = 0; k < MAX_SIZE; k++) {
                sum += A[i][k] * B[k][j];
            }
            C_sw[i][j] = sum;
        }
    }

    // 4. Compare the results
    int errors = 0;
    float epsilon = 1e-3f;
    for (int i = 0; i < MAX_SIZE; i++) {
        for (int j = 0; j < MAX_SIZE; j++) {
            if (std::abs(C_hw[i][j] - C_sw[i][j]) > epsilon) {
                errors++;
                std::cout << "Mismatch at [" << i << "][" << j << "]: ";
                std::cout << "HW: " << C_hw[i][j] << ", SW: " << C_sw[i][j] << '\n';
            }
        }
    }

    if (errors == 0) {
        std::cout << "Test Passed!" << '\n';
        return 0;
    } else {
        std::cout << "Test Failed with " << errors << " errors." << '\n';
        return 1; // 1 triggers a failure in the Vitis HLS GUI
    }
}
