cd ../

target_list="$@"
inifile="$2"
target_list=`find ../config/ -name $1* -type d| cut -d"/" -f 3`
algrithom_list="fft math dct qmf blkvec"

for target_run in $target_list; do

    export target=$target_run
    echo "::::::::The run target is: " $target

    for i in `ls config/$target/fft_split`; do
    echo $i "is generating."
    cmd="python test_reporter.py \
     -c config/$target/fft_split/$i \
     -t ${target}_fft_bench_test \
     -o pic/$target/fft_split/  \
     -b 2004328    \
     -s 5	\
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
     	 -b 2004328     \
         -s 5		\
         -T             \
         -d"
	 echo $cmd
         eval $cmd
        done
    done

done

find ../pic/$1*/ -name *.txt| xargs cat >> ../pic/$1_total_list 

cmd=`sort ../pic/$1_total_list -n | tail -n 1`

binary_search_param=`echo $cmd | cut -d";" -f 2`
section_param=`echo $cmd | cut -d";" -f 3`
cfgfile=`echo $cmd | cut -d";" -f 4`

#base_line_param
#thresh_hold

#18.8831003812;2071598,2004328;cubie2_int_blkvec_bench_test;DLB_vec_Labs_maxLU;5

echo $cmd 
echo $binary_search_param $section_param 
cd  frontend
pwd
echo 'python test.py -c $inifile -s $section_param -b ~/DI_TEST -e P4 -m 1 -T --binary-search ${binary_search_param} --exec-cmd-post "cd ../; python test_reporter.py -c $cfgfile -t $section_param -o test -b 2004328 -d -s 5 -i" '

