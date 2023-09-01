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

setup:
	@echo "Attempting to find local Python 3 installation."
	eval "type -P 'python3' && python3 setup.py || python setup.py" && mv setup.json $(CONFIG)

test:
	$(PYTHON) $(SUGARSCAPE) --conf $(CONFIG)

clean:
	rm -rf $(CLEAN) || true

lean:
	rm -rf $(PLOTS) || true

.PHONY: all clean data lean plots setup

# vim: set noexpandtab tabstop=4:
