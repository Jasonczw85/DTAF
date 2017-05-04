#!/bin/bash


i=`find . -name *fft*.csv`

for j in $i; do
   cp $j ../renew/fft/
done


i=`find . -name *qmf*.csv`

for j in $i; do

   cp $j ../renew/qmf/

done



i=`find . -name *dct*.csv`

for j in $i; do

   cp $j ../renew/dct/

done


i=`find . -name *math*.csv`

for j in $i; do

   cp $j ../renew/math/

done


i=`find . -name *blkvec*.csv`

for j in $i; do

   cp $j ../renew/blkvec/

done

