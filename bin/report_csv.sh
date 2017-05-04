#!/bin/bash
cd ../
set +x

config_folder="$1"
inifile="$2"
#base_line="$3"
thresh_hold="$3"
target_list=`find config/ -type d -name ${config_folder}* | cut -d"/" -f 2`
algrithom_list="math dct qmf blkvec"

echo $inifile  $target_list  $algrithom_list

for target_run in $target_list; do

    export target=$target_run
    echo "::::::::The run target is: " $target

    for i in `ls config/$target/fft_split`; do
    echo $i "is generating."
    cmd="python test_reporter.py \
     -c config/$target/fft_split/$i \
     -t ${target}_fft_bench_test \
     -o csv/$target/fft_split/  \
     -s $thresh_hold	\
     -g fft
     -p"
     echo $cmd
     eval $cmd
    done

    for algrithom in $algrithom_list; do
        for i in `ls config/$target/$algrithom`; do
        echo $i "is generating."
        cmd="python test_reporter.py \
         -c config/$target/$algrithom/$i \
         -t ${target}_${algrithom}_bench_test \
         -o csv/$target/$algrithom/   \
         -s $thresh_hold		\
         -g $algrithom
	 -p
         "
        echo $cmd
        eval $cmd
        done
    done
    
    # the ranking list with -T, trigger bs cmd

done

#python test_reporter.py -c config/cubie2_float/blkvec/DLB_VLsquaredmagCLIU_strict.cfg -t cubie2_float_blkvec_bench_test -o pic/cubie2_float/blkvec/ -b 2004328 -s 5 -T -d
#python test_reporter.py -c config/c64plus_beagle/dct/DLB_Ldct4_unscaledLU_1920.cfg -t c64plus_beagle_dct_bench_test -o  pic/c64plus_beagle/dct/ -b 2004328 -d -s 5 -T
#python test_reporter.py -c config/c64plus_beagle/dct/DLB_Ldct4_scaled_shlLUU_960.cfg -t c64plus_beagle_dct_bench_test -o  pic/c64plus_beagle/dct/ -b 2004328 -d -s 5 -T

































