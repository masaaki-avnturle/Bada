# omega_vim_bada — Ω-Vim, the Vim editor written in the Bada language.
# Pure Ruby (stdlib only) + the sibling bada_ruby library. No gems to build.

APP      := omega-vim
VERSION  := 1.0.0
RUBY     ?= ruby
PREFIX   ?= /usr/local

# Bada language host library (sibling in the repo, or vendored copy).
BADA_LIB := $(firstword $(wildcard ../bada_ruby/lib vendor/bada_ruby/lib))

BINDIR   := $(DESTDIR)$(PREFIX)/bin
LIBDIR   := $(DESTDIR)$(PREFIX)/share/$(APP)
DOCDIR   := $(DESTDIR)$(PREFIX)/share/doc/$(APP)

.PHONY: all test demo install uninstall clean dist check

all: check

check:
	@$(RUBY) -c lib/bada/code_fix.rb >/dev/null
	@$(RUBY) -c lib/bada/omega_vim.rb >/dev/null
	@$(RUBY) -c lib/bada/vim_interpreter.rb >/dev/null
	@$(RUBY) -c bin/omega-vim >/dev/null
	@echo "syntax OK"

test: check
	$(RUBY) -Ilib -I$(BADA_LIB) tests/test_omega_vim.rb

demo:
	$(RUBY) -Ilib -I$(BADA_LIB) bin/omega-vim demo

install: all
	install -d $(BINDIR) $(LIBDIR)/lib $(LIBDIR)/src $(LIBDIR)/examples $(LIBDIR)/bin $(DOCDIR)
	cp -r lib/* $(LIBDIR)/lib/
	cp -r src/* $(LIBDIR)/src/
	cp -r examples/* $(LIBDIR)/examples/ 2>/dev/null || true
	cp README.md $(DOCDIR)/README.md
	install -m 0644 bin/omega-vim $(LIBDIR)/bin/omega-vim
	# vendor the Bada host library so the installed app is self-sufficient
	@if [ -n "$(BADA_LIB)" ]; then \
	  install -d $(LIBDIR)/vendor/bada_ruby/lib; \
	  cp -r $(BADA_LIB)/* $(LIBDIR)/vendor/bada_ruby/lib/; \
	fi
	# thin launcher on PATH
	printf '#!/bin/sh\nexec %s "%s/bin/omega-vim" "$$@"\n' "$(RUBY)" "$(PREFIX)/share/$(APP)" > $(BINDIR)/$(APP)
	chmod 0755 $(BINDIR)/$(APP)
	@echo "installed $(APP) to $(BINDIR)/$(APP)"

uninstall:
	rm -f $(BINDIR)/$(APP)
	rm -rf $(LIBDIR) $(DOCDIR)

dist: all
	@sh packaging/build-deb.sh

clean:
	rm -rf dist
