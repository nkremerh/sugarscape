CONFIG = config.json
DATACHECK = data/data.complete
PLOTCHECK = plots/plots.complete

DATASET = $(DATACHECK) \
		data/*[[:digit:]]*.config \
		data/*.json

PLOTS = $(PLOTCHECK) \
		plots/*.dat \
		plots/*.pdf \
		plots/*.plg

CLEAN = log.json \
		$(DATASET) \
		$(PLOTS)

# Change to python3 (or other alias) if needed
PYTHON = python
SH = bash
SUGARSCAPE = sugarscape.py

$(DATACHECK):
	cd data && $(SH) collect.sh
	touch $(DATACHECK)

$(PLOTCHECK): $(DATACHECK)
	cd plots && $(SH) make_plots.sh
	touch $(PLOTCHECK)

all: $(DATACHECK) $(PLOTCHECK)

data: $(DATACHECK)

plots: $(PLOTCHECK)

test:
	$(PYTHON) $(SUGARSCAPE) --conf $(CONFIG)

clean:
	rm -rf $(CLEAN) || true

lean:
	rm -rf $(PLOTS) || true

.PHONY: all clean data lean plots

# vim: set noexpandtab tabstop=4:
