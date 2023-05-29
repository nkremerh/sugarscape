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

clean:
	rm -rf $(CLEAN) || true

.PHONY: all clean data install

# vim: set noexpandtab tabstop=4:
