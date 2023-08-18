CLEAN = log.json \
		data/*.json \
		plots/*.pdf \
		plots/*.dat
CONFIG = config.json
SUGARSCAPE = sugarscape.py

all: 

test:
	python $(SUGARSCAPE) --conf $(CONFIG)

data:
	cd data && sh collect.sh

generate:
	cd data && sh generate.sh

clean:
	rm -rf $(CLEAN) || true

plots:
	cd plots && sh generate_line_graphs.sh

.PHONY: all clean data generate plots

# vim: set noexpandtab tabstop=4:
