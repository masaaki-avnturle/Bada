PREFIX ?= /usr/local
BINDIR = $(PREFIX)/bin
.PHONY: all install uninstall clean
all:
	@echo "Nothing to build. Use 'make install' to install the hypothesis engine."
install:
	install -d "$(DESTDIR)$(BINDIR)"
	install -m 755 usr/bin/toy_hypothesis_engine.py "$(DESTDIR)$(BINDIR)/toy_hypothesis_engine"
	@echo "Installed $(DESTDIR)$(BINDIR)/toy_hypothesis_engine"
uninstall:
	-rm -f "$(DESTDIR)$(BINDIR)/toy_hypothesis_engine"
clean:
	@echo "clean: nothing to do"
