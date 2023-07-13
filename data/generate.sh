#! /bin/bash

# Create working config to avoid clobbering permanent config
cp template.config template.json

for i in {1..20}
do
    # Generate a random seed and apply it to config file
    seed=$RANDOM
    sedstr="s/\(\"seed\"\:\s\).*,/\1$seed,/g"
    echo "Generating template with random seed $seed"
    sed -i $sedstr ./template.json
    cp ./template.json ./$seed.json
done

# Clean up working config
rm template.json

exit 0
