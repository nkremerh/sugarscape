REPO = nkremerh/sugarscape
BRANCH = master

all: 

install: /usr/bin/pip /usr/bin/python
	@echo "Installing Python dependencies using pip."
	@echo "If you want to use another method, please abort installation now."
	@sleep 5

clean:
	echo "Nothing to clean up"

.PHONY: all clean install

# vim: set noexpandtab tabstop=4:
