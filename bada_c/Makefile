# Makefile for Bada-in-C (interpreter + compiler)
CC      ?= cc
CFLAGS  ?= -O2 -std=c11
LDLIBS  ?= -lm
PREFIX  ?= /usr/local

bada: bada.c
	$(CC) $(CFLAGS) bada.c $(LDLIBS) -o bada

.PHONY: test clean install
test: bada
	./test.sh

clean:
	rm -f bada

install: bada
	install -d $(PREFIX)/bin
	install -m755 bada $(PREFIX)/bin/bada
	install -d $(PREFIX)/share/bada
	install -m644 bada.c $(PREFIX)/share/bada/bada.c
	@echo "Set BADA_HOME=$(PREFIX)/share/bada to enable 'bada build'."
