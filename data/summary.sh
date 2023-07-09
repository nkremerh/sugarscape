#! /bin/bash

files=( altruist bentham default egoist modified topAltruist topBentham topEgoist topModified rankedAltruist rankedBentham rankedDefault rankedEgoist rankedModified )

for f in "${files[@]}"
do
    tail $f*.log > $f.logs
done


for f in "${files[@]}"
do
    for g in "${files[@]}"
    do
        diff -y $f.logs $g.logs > $f.$g.diff
    done
done

exit 0
