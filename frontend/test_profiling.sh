#!/bin/bash
set -x
Test_Section=`echo $BACKENDS`

#for i in `find cfg -name "$Test_Suite"_*.ini`; do

#echo "+++++++++++./test.sh $i"
#./test.sh $i

#done
source ~/.bashrc

./test.py -c linux32.ini -s $Test_Section -e P4 -b ~/DI_TEST -i /mnt/DI_TEST/Source/DLB_intrinsics -m 20
