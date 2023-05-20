CLEAN = log.json
CONFIG = config.json
SUGARSCAPE = sugarscape.py

all: 

test:
	python $(SUGARSCAPE) --conf $(CONFIG)

clean:
	rm -rf $(CLEAN) || true

.PHONY: all clean install

# vim: set noexpandtab tabstop=4:
