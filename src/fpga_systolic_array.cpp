#include "fpga_systolic_array.h"

void systolic_mm(float A[MAX_SIZE][MAX_SIZE], 
                 float B[MAX_SIZE][MAX_SIZE], 
                 float C[MAX_SIZE][MAX_SIZE]) {
    
    // Standard BRAMs can only read 2 values per clock. 
    // Slice the memory into smaller registers so all the multipliers 
	// are used simultaneously without bottlenecking.
    #pragma HLS ARRAY_PARTITION variable=A cyclic factor=4 dim=2
    #pragma HLS ARRAY_PARTITION variable=B cyclic factor=4 dim=1

    row_loop: for (int i = 0; i < MAX_SIZE; i++) {
        
        col_loop: for (int j = 0; j < MAX_SIZE; j++) {
            
            // Force the accelerator to spit out a new C[i][j] value 
            // every single clock cycle, exactly like a systolic array flowing data.
            #pragma HLS PIPELINE II=1
            
            float sum = 0.0f;
            
            product_loop: for (int k = 0; k < MAX_SIZE; k++) {
                
                // A full 16x16 unroll takes 256 DSPs. 
                // Since Spartan-7 xc7s100 only has 160 DSPs, unroll by a factor of 4.
                // This builds 4 parallel MAC units that fits the pipeline
                #pragma HLS UNROLL factor=4
                
                sum += A[i][k] * B[k][j];
            }
            C[i][j] = sum;
        }
    }
}
