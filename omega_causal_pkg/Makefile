PKGDIR ?= omega_causal_pkg
PY = $(shell command -v python3 2>/dev/null || command -v python 2>/dev/null || echo python3)
BIN = $(PKGDIR)/bin
.PHONY: all build run test clean
all: build
build:
	@echo "Package skeleton created under $(PKGDIR)"
run: build
	@cd $(BIN) && $(PY) chat_assistant.py --interactive || true
test: build
	@echo "Basic checks" 
clean:
	rm -rf $(PKGDIR) || true
