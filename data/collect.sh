#! /bin/bash

# Create working configs to avoid clobbering permanent configs
cp bentham.config bentham.json
cp default.config default.json
cp rankedBentham.config rankedBentham.json
cp rankedDefault.config rankedDefault.json

n=1000
for i in $( seq 1 $n )
do
    # Generate a random seed and apply it to config files
    seed=$RANDOM
    sedstr="s/\(\"seed\"\:\s\).*,/\1$seed,/g"
    echo "Running simulation for random seed $seed ($i/$n)"
    sed -i $sedstr ./bentham.json
    sed -i $sedstr ./default.json
    sed -i $sedstr ./rankedDefault.json
    sed -i $sedstr ./rankedBentham.json

    # Run simulation for configs and rename resulting log
    python ../sugarscape.py --conf bentham.json > bentham$i.log
    python ../logparse.py --log log.json >> bentham$i.log
    mv log.json bentham$i.json

    python ../sugarscape.py --conf default.json > default$i.log
    python ../logparse.py --log log.json >> default$i.log
    mv log.json default$i.json

    python ../sugarscape.py --conf rankedDefault.json > rankedDefault$i.log
    python ../logparse.py --log log.json >> rankedDefault$i.log
    mv log.json rankedDefault$i.json

    python ../sugarscape.py --conf rankedBentham.json > rankedBentham$i.log
    python ../logparse.py --log log.json >> rankedBentham$i.log
    mv log.json rankedBentham$i.json

    # Generate side-by-side comparison between runs
    diff -y default$i.log bentham$i.log > compare$i.log
    diff -y rankedDefault$i.log rankedBentham$i.log > compareRanked$i.log
done

# Clean up working configs
rm bentham.json default.json rankedBentham.json rankedDefault.json

exit 0
