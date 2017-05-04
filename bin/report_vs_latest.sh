#!/bin/bash
cd ../
set +x

config_folder="$1"
inifile="$2"
#base_line="$3"
thresh_hold="$3"
target_list=`find config/ -type d -name ${config_folder}* | cut -d"/" -f 2`
algrithom_list="fft math dct qmf blkvec"

echo $inifile  $target_list  $algrithom_list

for target_run in $target_list; do

    export target=$target_run
    echo "::::::::The run target is: " $target

    for i in `ls config/$target/fft_split`; do
    echo $i "is generating."
    cmd="python test_reporter.py \
     -c config/$target/fft_split/$i \
     -t ${target}_fft_bench_test \
     -o pic/$target/fft_split/  \
     -s $thresh_hold	\
     -T       \
     -d"
     echo $cmd
     eval $cmd
    done

    for algrithom in $algrithom_list; do
        for i in `ls config/$target/$algrithom`; do
        echo $i "is generating."
        cmd="python test_reporter.py \
         -c config/$target/$algrithom/$i \
         -t ${target}_${algrithom}_bench_test \
         -o pic/$target/$algrithom/   \
         -s $thresh_hold		\
         -T             \
         -d"
        echo $cmd
        eval $cmd
        done
    done
    
    # the ranking list with -T, trigger bs cmd

done

#python test_reporter.py -c config/cubie2_float/blkvec/DLB_VLsquaredmagCLIU_strict.cfg -t cubie2_float_blkvec_bench_test -o pic/cubie2_float/blkvec/ -b 2004328 -s 5 -T -d
#python test_reporter.py -c config/c64plus_beagle/dct/DLB_Ldct4_unscaledLU_1920.cfg -t c64plus_beagle_dct_bench_test -o  pic/c64plus_beagle/dct/ -b 2004328 -d -s 5 -T
#python test_reporter.py -c config/c64plus_beagle/dct/DLB_Ldct4_scaled_shlLUU_960.cfg -t c64plus_beagle_dct_bench_test -o  pic/c64plus_beagle/dct/ -b 2004328 -d -s 5 -T

find pic/$1*/ -name *.txt

find pic/$1*/ -name *.txt| xargs cat >> pic/$1_total_list 
cat pic/$1_total_list | sort -nr > /tmp/ranking_list.txt

#cmd=`cat pic/$1_total_list | sort -nr|head -n 1`

cmd_all=`cat /tmp/ranking_list.txt`

for cmd in $cmd_all; do


binary_search_param=`echo $cmd | cut -d";" -f 2`
section_param=`echo $cmd | cut -d";" -f 3`
cfgfile=`echo $cmd | cut -d";" -f 5`
picfile=`echo $cfgfile|sed s/config/pic/g|sed s/cfg/png/g`
echo  $picfile
cp $picfile /tmp/attach.png


echo $binary_search_param $section_param $cfgfile  $inifile

cd  frontend
pwd

echo 'python test.py -c tests_updates/$inifile -s $section_param -b ~/DI_TEST -e P4 -m 3 -T --binary-search $binary_search_param --exec-cmd-post "cd /mnt/DI_TEST/DI_Script/Compatibility_Tests; python test_reporter.py -c $cfgfile -t $section_param -o test -d -s $thresh_hold -i" '
python test.py -c tests_updates/$inifile -s $section_param -b ~/DI_TEST -e P4 -m 3 -T --binary-search $binary_search_param --exec-cmd-post "cd /mnt/DI_TEST/DI_Script/Compatibility_Tests; python test_reporter.py -c $cfgfile -t $section_param  -o test -d -s $thresh_hold -i"

cd ..
done

find pic/$1*/ -name "*.txt" | xargs rm -rf
rm -rf pic/$1_total_list
