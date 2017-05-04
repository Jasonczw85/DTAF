
i=`ls *.csv`

for j in $i; do

echo $j
awk -F ',' '{print $1","$3}' $j > /tmp/1
cp /tmp/1  $j

done
