plots=( population.plg meanttl.plg wealth.plg wealth_normalized.plg starvation_combat.plg )

# Change to python3 (or other alias) if needed
py=python

$py parselogs.py -p ../data/ -t 5000 > data.dat

for ((i=0; i<"${#plots[@]}"; i++))
do
    gnuplot -c ${plots[$i]} 'data.dat'
done
