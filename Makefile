CLEAN = log.json \
		data/*[[:digit:]]*.config \
		data/*.json \
		plots/*.pdf \
		plots/*.dat

CONFIG = config.json

DATACHECK = data/data.complete

# Change to python3 (or other alias) if needed
PYTHON = python

SUGARSCAPE = sugarscape.py

$(DATACHECK):
	cd data && sh collect.sh
	touch $(DATACHECK)

all:

data: $(DATACHECK)

plots: $(DATACHECK)
	cd plots && sh generate_line_graphs.sh

test:
	$(PYTHON) $(SUGARSCAPE) --conf $(CONFIG)

clean:
	rm -rf $(CLEAN) $(DATACHECK) || true

.PHONY: all clean data plots

# vim: set noexpandtab tabstop=4:
