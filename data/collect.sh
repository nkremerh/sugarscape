#! /bin/bash

configs=( benthamHalfLookaheadBinary egoisticHalfLookaheadBinary rawSugarscape )
files=( )

# Change to python3 (or other alias) if needed
py=python

# Number of seeds to run
n=100
# Number of parallel processes to run
N=1

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
    $py ../sugarscape.py --conf $f.config &
    if [[ $(jobs -r -p | wc -l) -ge $N ]]; then
        wait -n
    fi
    j=$((j+1))
done

echo "Waiting for jobs to finish up."
while [[ $(jobs -r -p | wc -l) -gt 0 ]];
do
    wait -n
done

# Clean up working configs
for f in "${files[@]}"
do
    rm $f.config
done

exit 0
