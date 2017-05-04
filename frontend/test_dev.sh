#!/bin/bash

bash
set -x

DIR_SRC=/local3/Kit_For_DI_Compatibility
#DIR_WORKSPACE=/local3
DIR_WORK=`pwd`

Test_Section=`echo $BACKENDS`

#for i in `find cfg -name "$Test_Suite"_*.ini`; do

#echo "+++++++++++./test.sh $i"
#./test.sh $i

#done

# To modify the hard-coded path to find the zip packages
#sed -i 's/zip_repos\ \=\ \/mnt\/DI_TEST\/Source/zip_repos\ \=\ \/local3\/Kit_For_DI_Compatibility/g' ../kit_cfg/linux32.ini
# To run itaf tests based on the variable "BACKENDS" setted in jenkins jobs
python ./../../../../compatibility_tests/frontend/test.py -c linux32.ini -s $Test_Section -e zip -b $DIR_WORK/DI_TEST -i $DIR_SRC/DLB_intrinsics/ -K $DIR_SRC/KL_File -L $DIR_SRC/Logs/kit_logs/

