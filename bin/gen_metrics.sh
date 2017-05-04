#!/bin/bash
tables="cubie2_int_fft_bench_test
cubie2_int_neon_fft_bench_test
cubie2_float_fft_bench_test
cubie2_float_neon_fft_bench_test
cubie2_int_blkvec_bench_test
cubie2_int_neon_blkvec_bench_test
cubie2_float_blkvec_bench_test
cubie2_float_neon_blkvec_bench_test
cubie2_int_math_bench_test
cubie2_int_neon_math_bench_test
cubie2_float_math_bench_test
cubie2_float_neon_math_bench_test
cubie2_int_qmf_bench_test
cubie2_int_neon_qmf_bench_test
cubie2_float_qmf_bench_test
cubie2_float_neon_qmf_bench_test
cubie2_int_dct_bench_test
cubie2_int_neon_dct_bench_test
cubie2_float_dct_bench_test
cubie2_float_neon_dct_bench_test
"
cmp=2544127
ref=2020610
thresh_hold=5

for i in $tables ; do
	echo $i
	echo $cmp
	echo $ref
	echo $thresh_hold

set -x
	python ../../test_reporter.py -t $i -p -i $cmp  -b $ref -s $thresh_hold  -c ../../config/arm_int/dct/DLB_Ldct4_unscaled_shlLUU_96.cfg --statistic -p

done
