#ifndef FPGA_SYSTOLIC_ARRAY
#define FPGA_SYSTOLIC_ARRAY

// Define the maximum matrix size
#define MAX_SIZE 512 // SIZE

void systolic_mm_1d(float A[MAX_SIZE][MAX_SIZE], 
                 float B[MAX_SIZE][MAX_SIZE], 
                 float C[MAX_SIZE][MAX_SIZE]);
void systolic_mm_2d(float A[MAX_SIZE][MAX_SIZE], 
                 float B[MAX_SIZE][MAX_SIZE], 
                 float C[MAX_SIZE][MAX_SIZE]);
#endif
