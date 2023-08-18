#! /bin/bash

configs=( benthamNoLookaheadBinary benthamNoLookaheadTop benthamHalfLookaheadBinary benthamHalfLookaheadTop egoisticHalfLookaheadTop rawSugarscape )
files=( )

# Number of seeds to run
n=100
# Number of parallel processes to run
N=10

echo "Generating configurations for random seeds"
for i in $( seq 1 $n )
do
    # Generate a random seed
    seed=$RANDOM
    sedstr="s/\(\"seed\"\:\s\).*,/\1$seed,/g"

    for c in "${configs[@]}"
    do
        cp $c.config $c$seed.config
        # Apply seed to config file
        sed -i $sedstr ./$c$seed.config
        logstr="s/\(\"logfile\"\:\s\).*,/\1\"$c$seed.json\",/g"
        # Apply logfile name to config file
        sed -i $logstr ./$c$seed.config
        files+=( $c$seed )
    done
done

j=1
m=${#files[@]}
for f in "${files[@]}"
do
    echo "Running decision model $f ($j/$m)"
    # Run simulation for config
    python ../sugarscape.py --conf $f.config &
    if [[ $(jobs -r -p | wc -l) -ge $N ]]; then
        wait -n
    fi
    j=$((j+1))
done

# Clean up working configs
for f in "${files[@]}"
do
    rm $f.config
done

exit 0
