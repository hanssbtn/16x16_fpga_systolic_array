# Group Members
- Hans Sebastian
- Ady Syamsuri
- Rambanang Sidan Lanang
- Dicky Aditrianza

# Contributions

|         Member         |                Contributions                  |
|         :---:          |                    :---                       |
| Hans Sebastian         | Coding, Bug fixing, Report drafting + editing |
| Ady Syamsuri           | Report Drafting, Coding, Bug fixing           |
| Rambanang Sidan Lanang | Testing, Report drafting, Presentation        |
| Dicky Aditrianza       | Report Drafting, Coding, Presentation         |

# How to use
1. Run `source <Vitis Install Directory>/settings64.sh`.
2. Ensure Python3, `matplotlib` and `pandas` Python module are installed.
3. Run `cd <Root Project Directory>`.
4. Extract the `hls_config.cfg` file from the `hls.zip` file to the root project directory.
5. Run `mkdir src tb` if any of the folders are missing.
6. Extract `fpga_systolic_array.h`, and `fpga_systolic_array.cpp` from the `hls.zip` file to the `<Root Project Directory>/src` directory.
7. Extract `test_bench.cpp` and `graph.py` from the `original_code.zip` file to the `<Root Project Directory>/tb` directory.
8. Ensure the terminal is in the root project directory, then run `python3 tb/graph.py`.