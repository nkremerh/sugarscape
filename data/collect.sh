#! /bin/bash

# Create working configs to avoid clobbering permanent configs
cp bentham.config bentham.json
cp vanilla.config vanilla.json

for i in {1..20}
do
    # Generate a random seed and apply it to both config files
    seed=$RANDOM
    sedstr="s/\(\"seed\"\:\s\).*,/\1$seed,/g"
    echo "Running simulation for random seed $seed"
    sed -i $sedstr ./bentham.json
    sed -i $sedstr ./vanilla.json
    # Run simulation for both configs and rename resulting log
    python ../sugarscape.py --conf bentham.json > bentham$i.log
    python ../logparse.py --log log.json >> bentham$i.log
    mv log.json bentham$i.json
    python ../sugarscape.py --conf vanilla.json > vanilla$i.log
    python ../logparse.py --log log.json >> vanilla$i.log
    mv log.json vanilla$i.json
    # Generate side-by-side comparison between both runs
    diff -y vanilla$i.log bentham$i.log > compare$i.log
done

# Clean up working configs
rm bentham.json vanilla.json

exit 0
