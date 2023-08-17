#! /bin/bash

files=( benthamNoLookaheadBinary benthamHalfLookaheadBinary benthamHalfLookaheadTop egoisticHalfLookaheadTop rawSugarscape )

# Create working configs to avoid clobbering permanent configs
for f in "${files[@]}"
do
    cp $f.config $f.json
done

# Number of seeds to run
n=100
# Number of decision models to run per seed
m=${#files[@]}
for i in $( seq 1 $n )
do
    # Generate a random seed
    seed=$RANDOM
    sedstr="s/\(\"seed\"\:\s\).*,/\1$seed,/g"
    echo "Running simulations for random seed $seed ($i/$n)"

    j=1
    for f in "${files[@]}"
    do
        echo "Running decision model $f ($j/$m)"
        # Apply seed to config file
        sed -i $sedstr ./$f.json
        logstr="s/\(\"logfile\"\:\s\).*,/\1\"$f$i.json\",/g"
        # Apply logfile name to config file
        sed -i $logstr ./$f.json
        # Run simulation for configs and rename resulting log
        python ../sugarscape.py --conf $f.json &
        (( j % 5 )) || wait
        j=$((j+1))
    done
done

# Clean up working configs
for f in "${files[@]}"
do
    rm $f.json
done

exit 0
