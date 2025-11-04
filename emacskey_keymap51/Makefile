PYTHON = python3
.PHONY: install gen test
install:
	@echo "This package is run via python -m emacskeys.runner --config-file mymap.json"
gen:
	@$(PYTHON) -c "import importlib, pkgutil, sys; print('emacskeys runner module available')"
test:
	@echo "To test on Windows: copy package to Windows and run: python -m emacskeys.runner --config-file mymap.json"
