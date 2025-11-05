PY = python3
BIN = bin/run_server
SCRIPTS = bin/run_server
WEB_DIR = web
DATA_DIR = data
LIB = lib/server.py

  .PHONY: all run install clean prepare

  all: prepare

  prepare: $(DATA_DIR) $(SCRIPTS)
  @echo "Package prepared. Use 'make run' to start server."

  $(DATA_DIR):
  mkdir -p $(DATA_DIR)

  $(SCRIPTS):
  chmod +x $(SCRIPTS) || true
  chmod +x $(LIB) || true

  run: $(SCRIPTS)
  @echo "Starting local server..."
  $(PY) $(LIB)

  install: $(SCRIPTS)
  @echo "No global install step defined. Files are ready in current directory."

  clean:
  @echo "Cleaning generated runtime files..."
  # do not remove user data by default
  -rm -f $(WEB_DIR)/*.pyc
		     -find $(DATA_DIR) -name '*.tmp' -type f -delete || true

help:
@echo "Available targets:"
@echo "  make        - prepare (alias: make prepare)"
@echo "  make run    - start local server (requires python3)"
@echo "  make install- placeholder (no-op)"
@echo "  make clean  - remove temporary artifacts"

