#include <iostream>
#include <iomanip>
#include <cmath>
#include <chrono>
#include <cstdlib>
#include <fstream>
#include <vector>
#include <cblas.h>
#include "../src/fpga_systolic_array.h"

int main() {
    float A[MAX_SIZE][MAX_SIZE];
    float B[MAX_SIZE][MAX_SIZE];
    float C_hw[MAX_SIZE][MAX_SIZE];
    float C_sw[MAX_SIZE][MAX_SIZE];
    
    // 1D vectors required for OpenBLAS
    std::vector<float> A_1D(MAX_SIZE * MAX_SIZE);
    std::vector<float> B_1D(MAX_SIZE * MAX_SIZE);
    std::vector<float> C_ob(MAX_SIZE * MAX_SIZE, 0.0f);

    srand(42); 
    for (int i = 0; i < MAX_SIZE; i++) {
        for (int j = 0; j < MAX_SIZE; j++) {
            float valA = static_cast<float>(rand()) / static_cast<float>(RAND_MAX);
            float valB = static_cast<float>(rand()) / static_cast<float>(RAND_MAX);
            A[i][j] = valA;
            B[i][j] = valB;
            A_1D[i * MAX_SIZE + j] = valA;
            B_1D[i * MAX_SIZE + j] = valB;
            C_hw[i][j] = 0.0f;
            C_sw[i][j] = 0.0f;
        }
    }

    std::cout << "=================================================\n";
    std::cout << "   FPGA ACCELERATOR vs SOFTWARE BENCHMARK SUITE  \n";
    std::cout << "=================================================\n";

    int num_runs = 100;

    // 1. Hardware Simulation Benchmark (100 runs)
    double total_1d_duration = 0.0;
    for (int run = 0; run < num_runs; run++) {
        auto start_hw = std::chrono::high_resolution_clock::now();
        systolic_mm_1d(A, B, C_hw);
        auto end_hw = std::chrono::high_resolution_clock::now();
        total_1d_duration += std::chrono::duration<double, std::micro>(end_hw - start_hw).count();
    }
    double avg_1d_duration = total_1d_duration / static_cast<double>(num_runs);

    double total_2d_duration = 0.0;
    for (int run = 0; run < num_runs; run++) {
        auto start_hw = std::chrono::high_resolution_clock::now();
        systolic_mm_2d(A, B, C_hw);
        auto end_hw = std::chrono::high_resolution_clock::now();
        total_2d_duration += std::chrono::duration<double, std::micro>(end_hw - start_hw).count();
    }
    double avg_2d_duration = total_2d_duration / static_cast<double>(num_runs);

    // 2. Naive Software Benchmark (100 runs)
    double total_sw_duration = 0.0;
    for (int run = 0; run < num_runs; run++) {
        auto start_sw = std::chrono::high_resolution_clock::now();
        for (int i = 0; i < MAX_SIZE; i++) {
            for (int j = 0; j < MAX_SIZE; j++) {
                float sum = 0.0f;
                for (int k = 0; k < MAX_SIZE; k++) {
                    sum += A[i][k] * B[k][j];
                }
                C_sw[i][j] = sum;
            }
        }
        auto end_sw = std::chrono::high_resolution_clock::now();
        total_sw_duration += std::chrono::duration<double, std::micro>(end_sw - start_sw).count();
    }
    double avg_sw_duration = total_sw_duration / static_cast<double>(num_runs);

    // 3. OpenBLAS Benchmark (100 runs)
    double total_ob_duration = 0.0;
    for (int run = 0; run < num_runs; run++) {
        // Warmup / Reset Cache
        cblas_sgemm(CblasRowMajor, CblasNoTrans, CblasNoTrans, MAX_SIZE, MAX_SIZE, MAX_SIZE, 
                    1.0f, A_1D.data(), MAX_SIZE, B_1D.data(), MAX_SIZE, 0.0f, C_ob.data(), MAX_SIZE);
                    
        auto start_ob = std::chrono::high_resolution_clock::now();
        cblas_sgemm(CblasRowMajor, CblasNoTrans, CblasNoTrans, MAX_SIZE, MAX_SIZE, MAX_SIZE, 
                    1.0f, A_1D.data(), MAX_SIZE, B_1D.data(), MAX_SIZE, 0.0f, C_ob.data(), MAX_SIZE);
        auto end_ob = std::chrono::high_resolution_clock::now();
        
        total_ob_duration += std::chrono::duration<double, std::micro>(end_ob - start_ob).count();
    }
    double avg_ob_duration = total_ob_duration / static_cast<double>(num_runs);

    // Verify Correctness
    int errors = 0;
    const float EPSILON = 1e-3; 
    for (int i = 0; i < MAX_SIZE; i++) {
        for (int j = 0; j < MAX_SIZE; j++) {
            if (std::abs(C_hw[i][j] - C_ob[i * MAX_SIZE + j]) > EPSILON) errors++;
        }
    }

    std::cout << "Matrix Size        : " << MAX_SIZE << " x " << MAX_SIZE << "\n";
    std::cout << "Test Status        : " << (errors == 0 ? "PASSED" : "FAILED") << "\n";
    std::cout << "Avg. Naive C++ Time: " << avg_sw_duration << " us\n";
    std::cout << "Avg. OpenBLAS Time : " << avg_ob_duration << " us\n";
    std::cout << "Avg. HLS C-Sim Time (1D Array): " << avg_1d_duration << " us (Software Emulated)\n";
    std::cout << "Avg. HLS C-Sim Time (2D Array): " << avg_2d_duration << " us (Software Emulated)\n";
    
    // Export all three results as a comma-separated string for Python
    std::ofstream py_out("sw_avgs_temp.txt");
    py_out << avg_1d_duration << "," << avg_2d_duration << "," << avg_sw_duration << "," << avg_ob_duration;
    py_out.close();

    std::cout << "Results exported for Python parsing.\n";
    return !!errors;
}