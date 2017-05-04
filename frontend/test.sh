#!/bin/bash

bash
set -x
Test_Section=`echo $BACKENDS`

#for i in `find cfg -name "$Test_Suite"_*.ini`; do

#echo "+++++++++++./test.sh $i"
#./test.sh $i

#done


#python test.py -c linux32.ini -s $Test_Section -e zip -b ~/DI_TEST -i /mnt/DI_TEST/Source/DLB_intrinsics_1.8_rc04/
python test.py -c linux32.ini -s $Test_Section -e zip -b ~/DI_TEST -i /mnt/DI_TEST/Source/DLB_intrinsics/

