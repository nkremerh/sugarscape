#! /bin/bash

# Create working configs to avoid clobbering permanent configs
cp bentham.config bentham.json
cp default.config default.json
cp greedyBentham.config greedyBentham.json
cp rankedBentham.config rankedBentham.json
cp rankedDefault.config rankedDefault.json

n=10
for i in $( seq 1 $n )
do
    # Generate a random seed and apply it to config files
    seed=$RANDOM
    sedstr="s/\(\"seed\"\:\s\).*,/\1$seed,/g"
    echo "Running simulation for random seed $seed ($i/$n)"
    sed -i $sedstr ./bentham.json
    sed -i $sedstr ./default.json
    sed -i $sedstr ./greedyBentham.json
    sed -i $sedstr ./rankedBentham.json
    sed -i $sedstr ./rankedDefault.json

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

    python ../sugarscape.py --conf greedyBentham.json > greedyBentham$i.log
    python ../logparse.py --log log.json >> greedyBentham$i.log
    mv log.json greedyBentham$i.json

    python ../sugarscape.py --conf rankedBentham.json > rankedBentham$i.log
    python ../logparse.py --log log.json >> rankedBentham$i.log
    mv log.json rankedBentham$i.json

done

# Clean up working configs
rm bentham.json default.json greedyBentham.json rankedBentham.json rankedDefault.json

exit 0
