#ifndef FPGA_SYSTOLIC_ARRAY
#define FPGA_SYSTOLIC_ARRAY

// Define the maximum matrix size
#define MAX_SIZE 16

void systolic_mm(float A[MAX_SIZE][MAX_SIZE], 
                 float B[MAX_SIZE][MAX_SIZE], 
                 float C[MAX_SIZE][MAX_SIZE]);

#endif
