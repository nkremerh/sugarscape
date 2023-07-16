#! /bin/bash

files=( altruist altruistModified bentham default egoist egoistModified modified topAltruist topAltruistModified topBentham topEgoist topEgoistModified topModified rankedAltruist rankedAltruistModified rankedBentham rankedDefault rankedEgoist rankedEgoistModified rankedModified )

for f in "${files[@]}"
do
    tail $f*.log > $f.logs
done

for f in "${files[@]}"
do
    for g in "${files[@]}"
    do
        if [ $f != $g ]
        then
            diff -y $f.logs $g.logs > $f.$g.diff
        fi
    done
done

exit 0
