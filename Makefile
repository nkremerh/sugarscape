CONFIG = config.json
DATACHECK = data/data.complete
LOGS = log.csv log.json
PLOTCHECK = plots/plots.complete
SCREENSHOTS = *.ps

DATASET = $(DATACHECK) \
		data/*[[:digit:]]*.config \
		data/*.csv \
		data/*.json \
		data/*.sh

PLOTS = $(PLOTCHECK) \
		plots/*.pdf

CLEAN = $(DATASET) \
		$(LOGS) \
		$(PLOTS) \
		$(SCREENSHOTS)

# Change to python3 (or other alias) if needed
PYTHON = python
SUGARSCAPE = sugarscape.py

# Check for local Python aliases
PYCHECK = $(shell which python > /dev/null; echo $$?)
PY3CHECK = $(shell which python3 > /dev/null; echo $$?)

$(DATACHECK):
	cd data && $(PYTHON) run.py --conf ../$(CONFIG) --mode csv
	touch $(DATACHECK)

$(PLOTCHECK): $(DATACHECK)
	cd plots && $(PYTHON) plot.py --path ../data/ --conf ../$(CONFIG)
	touch $(PLOTCHECK)

all: $(DATACHECK) $(PLOTCHECK)

data: $(DATACHECK)

plots: $(PLOTCHECK)

seeds:
	cd data && $(PYTHON) run.py --conf ../$(CONFIG) --mode csv --seeds

setup:
	@echo "Checking for local Python installation."
ifeq ($(PY3CHECK), 0)
	@echo "Found alias for Python."
	sed -i 's/PYTHON = python$$/PYTHON = python3/g' Makefile
	sed -i 's/"python"/"python3"/g' $(CONFIG)
else ifneq ($(PYCHECK), 0)
	@echo "Could not find a local Python installation."
	@echo "Please update the Makefile and configuration file manually."
else
	@echo "This message should never be reached."
endif

test:
	$(PYTHON) $(SUGARSCAPE) --conf $(CONFIG)

clean:
	rm -rf $(CLEAN) || true

lean:
	rm -rf $(PLOTS) || true

.PHONY: all clean data lean plots setup

# vim: set noexpandtab tabstop=4:
