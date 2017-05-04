#!/usr/bin/python

import os
import sys
import csv
import xlwt
import optparse

def write_xls(path):

    #algorithm = ['math']
    algorithm = ['fft', 'blkvec', 'math', 'dct', 'qmf']
    backend = ['arm_float', 'arm_float_neon', 'arm_int', 'arm_int_neon', 'arndale_float', 'arndale_float_neon', 'arndale_int', 'arndale_int_neon', 'c674_float', 'c674_float_generic', 'cubie2_float', 'cubie2_float_neon', 'cubie2_int', 'cubie2_int_neon', 'sim_c64', 'sim_c64plus', 'sim_c674_float', 'sim_generic_float32', 'intel_core_linux_x86_gcc', 'intel_core_linux_x86_gcc_ipp', 'intel_core_linux_x86_icc', 'intel_core_linux_x86_icc_generic', 'intel_core_linux_amd64_gcc', 'intel_core_linux_amd64_gcc_ipp', 'intel_core_linux_amd64_icc', 'intel_core_linux_amd64_icc_generic']

    workbook = xlwt.Workbook()    
    length = len(backend)

    for item in algorithm:
        table = workbook.add_sheet(item)
        table.write(0, 0, 'Function Name')
        for i in range(length):
            filename = backend[i] + '_' + item + "_bench_test.csv"
            filename = os.path.join(path, item, filename)
            j = 1
            with open(filename, 'rb') as f:
                reader = csv.reader(f)
                table.write(0, i+1, backend[i])
                for row in reader:
                    if i==0:
                        table.write(j, i, row[0])
                        table.write(j, i+1, row[1].strip())
                        print row[1]
                    else:
                        table.write(j, i+1, row[1].strip()) 
                        print row[1]
                    j += 1
    workbook.save('Dolby_Intrinsics_Benchmarking_Results.xls')

def main():
    usage = "write_xls -p <path> \nExample: write_xls -p csv_path \n\
This program combines all the *_bench_test.csv to one .xls file. \n\
The csv_path should have five subfolders: fft, blkvec, math, dct and qmf. \n\
Each subfolder have the same files whose name start with the content of \n\
backend and end with _bench_test.csv. After generate the Dolby_Intrinsics_Benchmarking_Results.xls, \n\
it is need to add a 'ReadMe' worksheet and adjust the format of the .xls file to required standard." 
    parser = optparse.OptionParser(usage=usage)
    parser.add_option("-p", "--path", dest="path", metavar="NAME",
                      action="store", default='',
                      help='The path of the csv files') 
    options, args = parser.parse_args()

    write_xls(options.path) 
    
if __name__ == '__main__':
    sys.exit(main())
