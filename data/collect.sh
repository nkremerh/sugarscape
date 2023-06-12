#! /bin/bash

for i in {1..20}
do
    # Generate a random seed and apply it to both config files
    seed=$RANDOM
    sedstr="s/\(\"seed\"\:\s\).*,/\1$seed,/g"
    echo "Running simulation for random seed $seed"
    sed -i $sedstr ./benthamconfig.json
    sed -i $sedstr ./vanillaconfig.json
    # Run simulation for both configs and rename resulting log
    python ../sugarscape.py --conf benthamconfig.json > bentham$i.log
    mv log.json bentham$i.json
    python ../sugarscape.py --conf vanillaconfig.json > vanilla$i.log
    mv log.json vanilla$i.json
    # Generate side-by-side comparison between both runs
    diff -y vanilla$i.log bentham$i.log > compare$i.log
done
exit 0