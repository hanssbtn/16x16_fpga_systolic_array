import os
import re
import subprocess
import csv
# import matplotlib.pyplot as plt
# import pandas as pd
# import matplotlib.ticker as ticker

# Parameters
matrix_sizes = [16, 32, 64, 128, 256, 512]
cpp_file_path = "src/fpga_systolic_array.cpp"
header_file_path = "src/fpga_systolic_array.h"
config_file_path = "hls_config.cfg"
results_csv = "dse_results.csv"

# Spartan-7 xc7s100 Limits
MAX_DSP = 160
MAX_LUT = 64000
MAX_FF = 128000

def set_top_function(func_name):
    """Dynamically switch the Vitis Top Function to build 1D or 2D."""
    with open(config_file_path, 'r') as file:
        content = file.read()
    
    # Change syn.top=systolic_mm_1d to the target function
    pattern = r'(syn\.top=)\w+'
    new_content = re.sub(pattern, rf'\g<1>{func_name}', content)
    

# Spartan-7 xc7s100 Limits
MAX_DSP = 160
MAX_LUT = 64000
MAX_FF = 128000

def set_top_function(func_name):
    """Dynamically switch the Vitis Top Function to build 1D or 2D."""
    with open(config_file_path, 'r') as file:
        content = file.read()
    
    pattern = r'(syn\.top=)\w+'
    new_content = re.sub(pattern, rf'\g<1>{func_name}', content)
    
    with open(config_file_path, 'w') as file:
        file.write(new_content)

def set_hardware_factors(factor):
    """Update both the unroll factor AND the BRAM partition factor (1D Only)."""
    with open(cpp_file_path, 'r') as file:
        content = file.read()
    
    pattern_unroll = r'(#pragma HLS UNROLL factor=)\d+( // UNROLL)'
    content = re.sub(pattern_unroll, rf'\g<1>{factor}\g<2>', content)
    
    pattern_part_a = r'(#pragma HLS ARRAY_PARTITION variable=A_local cyclic factor=)\d+( dim=2 // PARTITION_A)'
    content = re.sub(pattern_part_a, rf'\g<1>{factor}\g<2>', content)
    
    pattern_part_b = r'(#pragma HLS ARRAY_PARTITION variable=B_local cyclic factor=)\d+( dim=1 // PARTITION_B)'
    content = re.sub(pattern_part_b, rf'\g<1>{factor}\g<2>', content)
    
    with open(cpp_file_path, 'w') as file:
        file.write(content)

def set_matrix_size(size):
    """Change the matrix size in the header file."""
    with open(header_file_path, 'r') as file:
        content = file.read()
    
    pattern = r'(#define MAX_SIZE )\d+( // SIZE)'
    new_content = re.sub(pattern, rf'\g<1>{size}\g<2>', content)
    
    with open(header_file_path, 'w') as file:
        file.write(new_content)

def extract_hardware_metrics(work_dir, top_function):
    """Parses Latency and Utilization from a specific build directory."""
    report_path = f"{work_dir}/hls/syn/report/{top_function}_csynth.rpt"
    metrics = {'cycles': None, 'bram': 0, 'dsp': 0, 'ff': 0, 'lut': 0}
    
    try:
        with open(report_path, 'r') as file:
            lines = file.readlines()
            
        for i, line in enumerate(lines):
            if "Latency (cycles)" in line:
                metrics['cycles'] = int(lines[i+3].split('|')[2].strip())
                break
                
        in_util = False
        for i, line in enumerate(lines):
            if "== Utilization Estimates" in line:
                in_util = True
            if in_util and line.startswith("|Total"):
                parts = [p.strip() for p in line.split('|')]
                metrics['bram'] = int(parts[2])
                metrics['dsp'] = int(parts[3])
                metrics['ff'] = int(parts[4])
                metrics['lut'] = int(parts[5])
                break
    except FileNotFoundError:
        pass
    return metrics

def plot_per_size_graphs(size, current_unrolls):
    """Generates graphs plotting EVERYTHING from the CSV for a specific Matrix Size."""
    df = pd.read_csv(results_csv)
    df_1d = df[(df['Matrix_Size'] == size) & (df['Architecture'] == '1D')].copy()
    df_2d = df[(df['Matrix_Size'] == size) & (df['Architecture'] == '2D')].copy()
        
    if df_1d.empty:
        return
        
    df_1d['Unroll_Factor'] = pd.to_numeric(df_1d['Unroll_Factor'])
    
    x_min = df_1d['Unroll_Factor'].min()
    x_max = df_1d['Unroll_Factor'].max()
    
    plt.style.use('dark_background')
    
    fig1, ax1 = plt.subplots(figsize=(12, 7))
    
    ax1.plot(df_1d['Unroll_Factor'], df_1d['FPGA_Time_us'], marker='o', color="#4ecdc4", linewidth=2, label='1D FPGA Latency')
    ax1.plot(df_1d['Unroll_Factor'], df_1d['HLS_Sim_Avg_us'], marker='v', color='#bd93f9', linewidth=2, linestyle='-.', label='1D HLS C-Sim (Emulation)')
    ax1.plot(df_1d['Unroll_Factor'], df_1d['Naive_Avg_us'], marker='x', color='#ffbe0b', linewidth=2, linestyle='--', label='Naive C++ Latency')
    ax1.plot(df_1d['Unroll_Factor'], df_1d['OpenBLAS_Avg_us'], marker='s', color='#ff6b6b', linewidth=2, linestyle=':', label='OpenBLAS Latency')
    
    if not df_2d.empty:
        time_2d = df_2d['FPGA_Time_us'].iloc[0]
        csim_2d = df_2d['HLS_Sim_Avg_us'].iloc[0]
        ax1.plot([x_min, x_max], [time_2d, time_2d], color='#ff9ff3', linestyle='-.', linewidth=2, label=f'2D Systolic FPGA ({time_2d:.1f} us)')
        ax1.plot([x_min, x_max], [csim_2d, csim_2d], color='#fd79a8', linestyle=':', linewidth=2, label=f'2D HLS C-Sim ({csim_2d:.1f} us)')

    for idx, row in df_1d.iterrows():
        ax1.annotate(f"{row['FPGA_Time_us']:.1f}", (row['Unroll_Factor'], row['FPGA_Time_us']), textcoords="offset points", xytext=(0, -15), ha='center', fontsize=8, color='#4ecdc4')
        ax1.annotate(f"{row['HLS_Sim_Avg_us']:.1f}", (row['Unroll_Factor'], row['HLS_Sim_Avg_us']), textcoords="offset points", xytext=(0, 10), ha='center', fontsize=8, color='#bd93f9')
        ax1.annotate(f"{row['Naive_Avg_us']:.1f}", (row['Unroll_Factor'], row['Naive_Avg_us']), textcoords="offset points", xytext=(0, 10), ha='center', fontsize=8, color='#ffbe0b')
        ax1.annotate(f"{row['OpenBLAS_Avg_us']:.1f}", (row['Unroll_Factor'], row['OpenBLAS_Avg_us']), textcoords="offset points", xytext=(0, 10), ha='center', fontsize=8, color='#ff6b6b')

    def time_to_cycles(x): return x * 100
    def cycles_to_time(x): return x / 100
    secax = ax1.secondary_yaxis('right', functions=(time_to_cycles, cycles_to_time))
    secax.set_ylabel('FPGA Clock Cycles (100MHz)', fontsize=12, color='#4ecdc4')

    ax1.set_xscale('log', base=2)
    ax1.set_yscale('log', base=10)
    ax1.set_xticks(current_unrolls)
    ax1.get_xaxis().set_major_formatter(ticker.ScalarFormatter())
    ax1.set_title(f'Execution Time vs. Unroll Factor ({size}x{size} Matrix)', fontsize=14, fontweight='bold')
    ax1.set_xlabel('Unroll Factor (Log2 Scale)', fontsize=12)
    ax1.set_ylabel('Time (Microseconds)', fontsize=12)
    ax1.grid(True, linestyle='--', alpha=0.3)
    ax1.legend(loc='upper right', fontsize=9)
    fig1.tight_layout()
    fig1.savefig(f'graph_latency_{size}x{size}.png', dpi=300)
    
    fig2, ax2 = plt.subplots(figsize=(12, 7))
    ax2.plot(df_1d['Unroll_Factor'], df_1d['DSP'], marker='D', color='#ffe66d', linewidth=2, label='1D DSP Slices')
    ax2.plot(df_1d['Unroll_Factor'], df_1d['BRAM'], marker='^', color='#6b5b95', linewidth=2, label='1D BRAM_18K')
    
    if not df_2d.empty:
        dsp_2d = df_2d['DSP'].iloc[0]
        bram_2d = df_2d['BRAM'].iloc[0]
        ax2.plot([x_min, x_max], [dsp_2d, dsp_2d], color='#ffe66d', linestyle='-.', alpha=0.5, label=f'2D DSP Required ({int(dsp_2d)})')
        ax2.plot([x_min, x_max], [bram_2d, bram_2d], color='#6b5b95', linestyle='-.', alpha=0.5, label=f'2D BRAM Required ({int(bram_2d)})')

    ax2.plot([x_min, x_max], [MAX_DSP, MAX_DSP], color='red', linestyle='--', alpha=0.7, label=f'Spartan-7 Max DSP Limit ({MAX_DSP})')

    for _, row in df_1d.iterrows():
        ax2.annotate(f"{int(row['DSP'])}", (row['Unroll_Factor'], row['DSP']), textcoords="offset points", xytext=(0, 10), ha='center', fontsize=9, color='#ffe66d')
        ax2.annotate(f"{int(row['BRAM'])}", (row['Unroll_Factor'], row['BRAM']), textcoords="offset points", xytext=(0, -15), ha='center', fontsize=9, color='#6b5b95')

    ax2.set_xscale('log', base=2)
    ax2.set_yscale('log', base=10)
    ax2.set_xticks(current_unrolls)
    ax2.get_xaxis().set_major_formatter(ticker.ScalarFormatter())
    ax2.set_title(f'Macro Utilization vs. Unroll Factor ({size}x{size} Matrix)', fontsize=14, fontweight='bold')
    ax2.set_xlabel('Unroll Factor (Log2 Scale)', fontsize=12)
    ax2.set_ylabel('Resource Count (Log Scale)', fontsize=12)
    ax2.grid(True, linestyle='--', alpha=0.3)
    ax2.legend()
    fig2.tight_layout()
    fig2.savefig(f'graph_macro_util_{size}x{size}.png', dpi=300)

    fig3, ax3 = plt.subplots(figsize=(12, 7))
    ax3.plot(df_1d['Unroll_Factor'], df_1d['LUT'], marker='*', color='#ff9ff3', linewidth=2, label='1D LUTs')
    ax3.plot(df_1d['Unroll_Factor'], df_1d['FF'], marker='p', color='#54a0ff', linewidth=2, label='1D FFs')
    
    if not df_2d.empty:
        lut_2d = df_2d['LUT'].iloc[0]
        ff_2d = df_2d['FF'].iloc[0]
        ax3.plot([x_min, x_max], [lut_2d, lut_2d], color='#ff9ff3', linestyle='-.', alpha=0.5, label=f'2D LUT Required ({int(lut_2d)})')
        ax3.plot([x_min, x_max], [ff_2d, ff_2d], color='#54a0ff', linestyle='-.', alpha=0.5, label=f'2D FF Required ({int(ff_2d)})')

    ax3.plot([x_min, x_max], [MAX_LUT, MAX_LUT], color='#ff9ff3', linestyle='--', alpha=0.5, label=f'Spartan-7 Max LUT ({MAX_LUT})')
    ax3.plot([x_min, x_max], [MAX_FF, MAX_FF], color='#54a0ff', linestyle='--', alpha=0.5, label=f'Spartan-7 Max FF ({MAX_FF})')

    for _, row in df_1d.iterrows():
        ax3.annotate(f"{int(row['LUT'])}", (row['Unroll_Factor'], row['LUT']), textcoords="offset points", xytext=(0, 10), ha='center', fontsize=9, color='#ff9ff3')
        ax3.annotate(f"{int(row['FF'])}", (row['Unroll_Factor'], row['FF']), textcoords="offset points", xytext=(0, -15), ha='center', fontsize=9, color='#54a0ff')
    
    ax3.set_xscale('log', base=2)
    ax3.set_yscale('log', base=10)
    ax3.set_xticks(current_unrolls)
    ax3.get_xaxis().set_major_formatter(ticker.ScalarFormatter())
    ax3.set_title(f'Logic Gate Utilization vs. Unroll Factor ({size}x{size} Matrix)', fontsize=14, fontweight='bold')
    ax3.set_xlabel('Unroll Factor (Log2 Scale)', fontsize=12)
    ax3.set_ylabel('Resource Count (Log Scale)', fontsize=12)
    ax3.grid(True, linestyle='--', alpha=0.3)
    ax3.legend()
    fig3.tight_layout()
    fig3.savefig(f'graph_logic_util_{size}x{size}.png', dpi=300)

    plt.close(fig1)
    plt.close(fig2)
    plt.close(fig3)

def plot_global_resource_scalability():
    """Plots how resources (DSP, BRAM, LUT) scale as Matrix Size (N) and Unroll Factor increases."""
    df = pd.read_csv(results_csv)
    df['Unroll_Factor_Num'] = pd.to_numeric(df['Unroll_Factor'], errors='coerce')
    
    df_1d = df[(df['Architecture'] == '1D') & (df['Unroll_Factor_Num'] == df['Matrix_Size'])]
    df_2d = df[df['Architecture'] == '2D']
    
    if df_1d.empty and df_2d.empty:
        return

    x_min = df_1d['Matrix_Size'].min()
    x_max = df_1d['Matrix_Size'].max()

    plt.style.use('dark_background')
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 12))

    ax1.plot(df_1d['Matrix_Size'], df_1d['DSP'], marker='o', color='#ffe66d', linewidth=2, label='1D DSP (Unroll Factor = N)')
    ax1.plot(df_1d['Matrix_Size'], df_1d['BRAM'], marker='^', color='#6b5b95', linewidth=2, linestyle='--', label='1D BRAM (Unroll Factor = N)')
    
    for _, row in df_1d.iterrows():
        ax1.annotate(f"{row['DSP']:.2f}", (row['Matrix_Size'], row['DSP']), textcoords="offset points", xytext=(0, 15), ha='center', fontsize=8, color='#4ecdc4')
        ax1.annotate(f"{row['BRAM']:.2f}", (row['Matrix_Size'], row['BRAM']), textcoords="offset points", xytext=(0, -15), ha='center', fontsize=8, color='#bd93f9')
    
    if not df_2d.empty:
        ax1.scatter(df_2d['Matrix_Size'], df_2d['DSP'], marker='D', color='#ff9ff3', s=150, zorder=5, label='2D DSP (16x16 only)')
        ax1.scatter(df_2d['Matrix_Size'], df_2d['BRAM'], marker='v', color='#54a0ff', s=150, zorder=5, label='2D BRAM (16x16 only)')
        ax1.annotate(f"2D DSP: {int(df_2d['DSP'].iloc[0])}", (16, df_2d['DSP'].iloc[0]), textcoords="offset points", xytext=(15, 0), fontsize=10, color='#ff9ff3')

    ax1.plot([x_min, x_max], [MAX_DSP, MAX_DSP], color='red', linestyle=':', alpha=0.8, label=f'Spartan-7 Limit ({MAX_DSP})')
    
    ax1.set_xscale('log', base=2)
    ax1.set_yscale('log', base=10)
    ax1.set_title('Global Macro Resource Scaling', fontsize=14, fontweight='bold')
    ax1.set_ylabel('Resource Count (Log Scale)')
    ax1.grid(True, which="both", ls="--", alpha=0.2)
    ax1.legend()

    ax2.plot(df_1d['Matrix_Size'], df_1d['LUT'], marker='*', color='#4ecdc4', linewidth=2, label='1D LUTs')
    ax2.plot(df_1d['Matrix_Size'], df_1d['FF'], marker='p', color='#a29bfe', linewidth=2, label='1D FFs')
    
    if not df_2d.empty:
        ax2.scatter(df_2d['Matrix_Size'], df_2d['LUT'], marker='h', color='#fab1a0', s=150, zorder=5, label='2D LUTs (Unroll Factor = N)')
        ax2.scatter(df_2d['Matrix_Size'], df_2d['FF'], marker='X', color='#e84393', s=150, zorder=5, label='2D FFs (Unroll Factor = N)')
        
    for _, row in df_1d.iterrows():
        ax2.annotate(f"{int(row['LUT'])}", (row['Matrix_Size'], row['LUT']), textcoords="offset points", xytext=(0, -15), ha='center', fontsize=9, color='#ff9ff3')
        ax2.annotate(f"{int(row['FF'])}", (row['Matrix_Size'], row['FF']), textcoords="offset points", xytext=(0, 15), ha='center', fontsize=9, color='#54a0ff')
        
    ax2.plot([x_min, x_max], [MAX_LUT, MAX_LUT], color='#4ecdc4', linestyle=':', alpha=0.5, label='Max LUTs')
    
    ax2.set_xscale('log', base=2)
    ax2.set_yscale('log', base=10)
    ax2.set_title('Global Logic Resource Scaling', fontsize=14, fontweight='bold')
    ax2.set_xlabel('Matrix Size (N x N)')
    ax2.set_ylabel('Gate Count (Log Scale)')
    ax2.grid(True, which="both", ls="--", alpha=0.2)
    ax2.legend()

    fig.tight_layout()
    fig.savefig('graph_global_resource_scalability.png', dpi=300)
    plt.close(fig)

def plot_global_scalability():
    """Plots a fully annotated Log-Log graph comparing algorithmic scalability."""
    df = pd.read_csv(results_csv)
    df['Unroll_Factor_Num'] = pd.to_numeric(df['Unroll_Factor'], errors='coerce')
    
    df_1d = df[(df['Architecture'] == '1D') & (df['Unroll_Factor_Num'] == df['Matrix_Size'])]

    df_2d = df[df['Architecture'] == '2D']
    
    if df_1d.empty:
        return

    sizes = df_1d['Matrix_Size'].tolist()
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(12, 8))
    
    ax.plot(df_1d['Matrix_Size'], df_1d['Naive_Avg_us'], marker='x', color='#ffbe0b', linewidth=2, linestyle='--', label='Sequential CPU (O(N³))')
    ax.plot(df_1d['Matrix_Size'], df_1d['OpenBLAS_Avg_us'], marker='s', color='#ff6b6b', linewidth=3, linestyle=':', label='OpenBLAS CPU (O(N³))')
    ax.plot(df_1d['Matrix_Size'], df_1d['FPGA_Time_us'], marker='o', color='#4ecdc4', linewidth=3, label='1D FPGA - Unroll=N (O(N²))')
    
    if not df_2d.empty:
        ax.scatter(df_2d['Matrix_Size'], df_2d['FPGA_Time_us'], marker='*', color='#ff9ff3', s=300, zorder=5, label='2D Systolic (16x16 only)')
        ax.annotate(f"2D: {df_2d['FPGA_Time_us'].iloc[0]:.2f} us", (16, df_2d['FPGA_Time_us'].iloc[0]), textcoords="offset points", xytext=(15, -15), fontsize=10, color='#ff9ff3', fontweight='bold')
    
    for _, row in df_1d.iterrows():
        ax.annotate(f"{row['Naive_Avg_us']:.2f}", (row['Matrix_Size'], row['Naive_Avg_us']), textcoords="offset points", xytext=(0, 15), ha='center', fontsize=8, color='#ffbe0b')
        ax.annotate(f"{row['OpenBLAS_Avg_us']:.2f}", (row['Matrix_Size'], row['OpenBLAS_Avg_us']), textcoords="offset points", xytext=(0, 15), ha='center', fontsize=8, color='#ff6b6b')
        ax.annotate(f"{row['FPGA_Time_us']:.2f}", (row['Matrix_Size'], row['FPGA_Time_us']), textcoords="offset points", xytext=(0, 15), ha='center', fontsize=8, color='#4ecdc4')

    ax.set_xscale('log', base=2)
    ax.set_yscale('log', base=10)
    ax.set_xticks(sizes)
    ax.get_xaxis().set_major_formatter(ticker.ScalarFormatter())

    ax.set_title('Algorithmic Scalability: Spatial FPGA vs. Temporal CPU', fontsize=16, fontweight='bold')
    ax.set_xlabel('Matrix Size (N x N)', fontsize=14)
    ax.set_ylabel('Execution Time (Microseconds, Log10 Scale)', fontsize=14)
    ax.grid(True, which="both", ls="--", alpha=0.2)
    ax.legend(fontsize=12)
    
    fig.tight_layout()
    fig.savefig('graph_global_scalability.png', dpi=300)
    plt.close(fig)

def main():
    with open(results_csv, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Matrix_Size', 'Architecture', 'Unroll_Factor', 'HLS_Sim_Avg_us', 'Naive_Avg_us', 'OpenBLAS_Avg_us', 'FPGA_Cycles', 'FPGA_Time_us', 'DSP', 'BRAM', 'LUT', 'FF'])
    
    for matrix_size in matrix_sizes:
        print(f"\n=======================================================")
        print(f"MATRIX SIZE SWEEP: {matrix_size}x{matrix_size}")
        print(f"=======================================================")
        
        set_matrix_size(matrix_size)
        current_unrolls = [1 << i for i in range(matrix_size.bit_length())]

        latest_hw_2d_sim = 0
        latest_naive = 0
        latest_ob = 0
        
        for factor in current_unrolls:
            set_top_function("systolic_mm_1d")
            set_hardware_factors(factor)
            
            try:
                subprocess.run(["vitis-run", "--mode", "hls", "--csim", "--config", "hls_config.cfg", "--work_dir", "./build_csim"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
                with open("build_csim/hls/csim/build/sw_avgs_temp.txt", "r") as f:
                    data = f.read().strip().split(',')
                    hw_1d_sim = float(data[0])
                    latest_hw_2d_sim = float(data[1])
                    latest_naive = float(data[2])
                    latest_ob = float(data[3])
            except Exception as e:
                print(f"     [!] Failed to run/read benchmarks: {e}")
                continue
            
            try:
                subprocess.run(["v++", "-c", "--mode", "hls", "--config", "hls_config.cfg", "--work_dir", "./build_1d"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
                metrics = extract_hardware_metrics("./build_1d", "systolic_mm_1d")
                
                if metrics['cycles'] is not None:
                    fpga_time_us = (metrics['cycles'] * 10) / 1000.0 
                    print(f"     [+] FPGA Time: {fpga_time_us:.3f} us | DSPs: {metrics['dsp']}")
                    
                    with open(results_csv, 'a', newline='') as csvfile:
                        writer = csv.writer(csvfile)
                        writer.writerow([matrix_size, '1D', factor, hw_1d_sim, latest_naive, latest_ob, metrics['cycles'], fpga_time_us, metrics['dsp'], metrics['bram'], metrics['lut'], metrics['ff']])
            except subprocess.CalledProcessError:
                print("     [!] 1D Hardware synthesis failed.")

        if matrix_size == 16:
            set_top_function("systolic_mm_2d")
            
            try:
                subprocess.run(["v++", "-c", "--mode", "hls", "--config", "hls_config.cfg", "--work_dir", "./build_2d"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
                metrics = extract_hardware_metrics("./build_2d", "systolic_mm_2d")
                
                if metrics['cycles'] is not None:
                    fpga_time_us = (metrics['cycles'] * 10) / 1000.0 
                    print(f"     [+] FPGA Time: {fpga_time_us:.3f} us | DSPs: {metrics['dsp']}")
                    
                    with open(results_csv, 'a', newline='') as csvfile:
                        writer = csv.writer(csvfile)
                        writer.writerow([matrix_size, '2D', 'Full', latest_hw_2d_sim, latest_naive, latest_ob, metrics['cycles'], fpga_time_us, metrics['dsp'], metrics['bram'], metrics['lut'], metrics['ff']])
            except subprocess.CalledProcessError:
                print("     [!] 2D Hardware synthesis failed (Likely OOM due to massive grid size).")

        plot_per_size_graphs(matrix_size, current_unrolls)

    plot_global_scalability()
    plot_global_resource_scalability()

if __name__ == "__main__":
    import resource
    try:
        resource.setrlimit(resource.RLIMIT_STACK, (resource.RLIM_INFINITY, resource.RLIM_INFINITY))
    except Exception:
        pass
    main()