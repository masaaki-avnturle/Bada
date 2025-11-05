CC = gcc
CFLAGS = -O2 -std=c11 -Iinclude -Wall -Wextra
LIBS = -lm

.PHONY: all tools pygen clean

all: tools

tools:
	@echo "Building demo tools..."
	@if [ -f bin/tools.c ]; then \
	  $(CC) $(CFLAGS) -o bin/tools bin/tools.c lib/jones.c lib/markov.c lib/entropy.c lib/bnf.c lib/manifold.c $(LIBS) || echo "compile failed (continuing)"; \
	else \
	  echo "No bin/tools.c found; skipping C build."; \
	fi

pygen:
	@echo "Running python codegen (if available)..."
	@if [ -x usr/python_codegen.py ] || [ -f usr/python_codegen.py ]; then \
	  if [ -f out_ast.json ]; then \
	    python3 usr/python_codegen.py out_ast.json py generated.py >/dev/null 2>&1 || echo "python codegen failed"; \
	  else \
	    echo "No out_ast.json found; run bnf parse first."; \
	  fi; \
	else \
	  echo "No python codegen present; skipping."; \
	fi

clean:
	@echo "Cleaning..."
	-rm -f bin/tools generated.py out_ast.json
