#include "fpga_systolic_array.h"

void systolic_mm_1d(float A[MAX_SIZE][MAX_SIZE], 
                 float B[MAX_SIZE][MAX_SIZE], 
                 float C[MAX_SIZE][MAX_SIZE]) {
    
    // Enable task-level pipelining
    #pragma HLS DATAFLOW

    float A_local[MAX_SIZE][MAX_SIZE];
    float B_local[MAX_SIZE][MAX_SIZE];
    float C_local[MAX_SIZE][MAX_SIZE];

    // Partition BRAMs to feed the unrolled DSPs simultaneously
    #pragma HLS ARRAY_PARTITION variable=A_local cyclic factor=512 dim=2 // PARTITION_A
    #pragma HLS ARRAY_PARTITION variable=B_local cyclic factor=512 dim=1 // PARTITION_B

    // ==========================================
    // STAGE 1: LOAD DATA
    // ==========================================
    Read_A_B: for (int i = 0; i < MAX_SIZE; i++) {
        for (int j = 0; j < MAX_SIZE; j++) {
            #pragma HLS PIPELINE II=1
            A_local[i][j] = A[i][j];
            B_local[i][j] = B[i][j];
        }
    }

    // ==========================================
    // STAGE 2: COMPUTE
    // ==========================================
    Compute_Row: for (int i = 0; i < MAX_SIZE; i++) {
        Compute_Col: for (int j = 0; j < MAX_SIZE; j++) {
            float sum = 0.0f;
            
            Compute_Dot: for (int k = 0; k < MAX_SIZE; k++) {
                // Pipeline the innermost loop to allow partial unrolling
                #pragma HLS PIPELINE
                #pragma HLS UNROLL factor=512 // UNROLL
                sum += A_local[i][k] * B_local[k][j];
            }
            C_local[i][j] = sum;
        }
    }

    // ==========================================
    // STAGE 3: STORE DATA
    // ==========================================
    Write_C: for (int i = 0; i < MAX_SIZE; i++) {
        for (int j = 0; j < MAX_SIZE; j++) {
            #pragma HLS PIPELINE II=1
            C[i][j] = C_local[i][j];
        }
    }
}

// ==========================================
// 2D SYSTOLIC ARRAY (Fully Unrolled Grid)
// ==========================================
void systolic_mm_2d(float A[MAX_SIZE][MAX_SIZE], float B[MAX_SIZE][MAX_SIZE], float C[MAX_SIZE][MAX_SIZE]) {
    
    #pragma HLS ARRAY_PARTITION variable=A cyclic factor=MAX_SIZE dim=1
    #pragma HLS ARRAY_PARTITION variable=B cyclic factor=MAX_SIZE dim=2

    float PE_sum[MAX_SIZE][MAX_SIZE];
    float A_reg[MAX_SIZE][MAX_SIZE];
    float B_reg[MAX_SIZE][MAX_SIZE];

    for (int i = 0; i < MAX_SIZE; i++) {
        #pragma HLS UNROLL
        for (int j = 0; j < MAX_SIZE; j++) {
            #pragma HLS UNROLL
            PE_sum[i][j] = 0.0f;
            A_reg[i][j] = 0.0f;
            B_reg[i][j] = 0.0f;
        }
    }

    int total_cycles = 3 * MAX_SIZE - 2;
    
    Systolic_Pump: for (int t = 0; t < total_cycles; t++) {
        #pragma HLS PIPELINE II=1 

        for (int i = MAX_SIZE - 1; i >= 0; i--) {
            #pragma HLS UNROLL
            for (int j = MAX_SIZE - 1; j >= 0; j--) {
                #pragma HLS UNROLL
                if (j > 0) A_reg[i][j] = A_reg[i][j-1];
                if (i > 0) B_reg[i][j] = B_reg[i-1][j];
            }
        }

        for (int i = 0; i < MAX_SIZE; i++) {
            #pragma HLS UNROLL
            int a_col = t - i;
            if (a_col >= 0 && a_col < MAX_SIZE) A_reg[i][0] = A[i][a_col];
            else A_reg[i][0] = 0.0f; 
            
            int b_row = t - i;
            if (b_row >= 0 && b_row < MAX_SIZE) B_reg[0][i] = B[b_row][i];
            else B_reg[0][i] = 0.0f; 
        }

        for (int i = 0; i < MAX_SIZE; i++) {
            #pragma HLS UNROLL
            for (int j = 0; j < MAX_SIZE; j++) {
                #pragma HLS UNROLL
                PE_sum[i][j] += A_reg[i][j] * B_reg[i][j];
            }
        }
    }

    for (int i = 0; i < MAX_SIZE; i++) {
        for (int j = 0; j < MAX_SIZE; j++) {
            #pragma HLS PIPELINE
            C[i][j] = PE_sum[i][j];
        }
    }
}