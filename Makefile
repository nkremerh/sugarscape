REPO = nkremerh/sugarscape
BRANCH = master

CLEAN = log.json
CONFIG = config.json
SUGARSCAPE = sugarscape.py

all: 

install: /usr/bin/pip /usr/bin/python
	@echo "Installing Python dependencies using pip."
	@echo "If you want to use another method, please abort installation now."
	@sleep 5

test:
	python $(SUGARSCAPE) --conf $(CONFIG)

clean:
	rm -rf $(CLEAN) || true

.PHONY: all clean install

# vim: set noexpandtab tabstop=4:
