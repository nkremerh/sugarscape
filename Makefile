CLEAN = log.json \
		data/*.json \
		data/*.log
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

.PHONY: all clean data generate

# vim: set noexpandtab tabstop=4:
