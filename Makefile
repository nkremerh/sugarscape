CONFIG = config.json
DATACHECK = data/data.complete
PLOTCHECK = plots/plots.complete

DATASET = $(DATACHECK) \
		data/*[[:digit:]]*.config \
		data/*.json \
		data/*.sh

PLOTS = $(PLOTCHECK) \
		plots/*.dat \
		plots/*.pdf \
		plots/*.plg

CLEAN = log.json \
		$(DATASET) \
		$(PLOTS)

# Change to python3 (or other alias) if needed
PYTHON = python
SUGARSCAPE = sugarscape.py

# Check for local Bash and Python aliases
BASHCHECK = $(shell which bash > /dev/null; echo $$?)
PYCHECK = $(shell which python > /dev/null; echo $$?)
PY3CHECK = $(shell which python3 > /dev/null; echo $$?)

$(DATACHECK):
	cd data && $(PYTHON) run.py --conf ../$(CONFIG)
	touch $(DATACHECK)

$(PLOTCHECK): $(DATACHECK)
	cd plots && $(PYTHON) plot.py --path ../data/ --conf ../$(CONFIG) --outf data.dat
	touch $(PLOTCHECK)

all: $(DATACHECK) $(PLOTCHECK)

data: $(DATACHECK)

plots: $(PLOTCHECK)

seeds:
	cd data && $(PYTHON) run.py --conf ../$(CONFIG) --seeds

setup:
	@echo "Checking for local Bash and Python installations."
ifneq ($(BASHCHECK), 0)
	@echo "Could not find a local Bash installation."
	@echo "Please update the Makefile and configuration file manually."
else
	@echo "Found alias for Bash."
endif
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
