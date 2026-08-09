# omega_quantum_decrypted — Makefile
# Self-contained: needs only a C compiler + libm. No OpenSSL, no third-party libs.

APP      := omega_quantum_decrypted
VERSION  := 1.0.0
CC       ?= cc
CFLAGS   ?= -O2 -Wall -Wextra -std=c11
CPPFLAGS += -Isrc -DOQD_APP_VERSION='"$(VERSION)"'
LDLIBS   := -lm

PREFIX   ?= /usr/local
BINDIR   := $(DESTDIR)$(PREFIX)/bin
DATADIR  := $(DESTDIR)$(PREFIX)/share/$(APP)
DOCDIR   := $(DESTDIR)$(PREFIX)/share/doc/$(APP)

SRC := src/main.c src/oqd.c src/jones.c src/qphase.c src/sha256.c
OBJ := $(SRC:.c=.o)
BIN := build/$(APP)

.PHONY: all clean test install uninstall dist

all: $(BIN)

$(BIN): $(OBJ)
	@mkdir -p build
	$(CC) $(CFLAGS) $(CPPFLAGS) -o $@ $(OBJ) $(LDLIBS)

%.o: %.c
	$(CC) $(CFLAGS) $(CPPFLAGS) -c $< -o $@

test: $(BIN)
	./$(BIN) selftest
	@sh tests/roundtrip.sh ./$(BIN)

install: $(BIN)
	install -d $(BINDIR) $(DATADIR)/examples $(DOCDIR)
	install -m 0755 $(BIN) $(BINDIR)/$(APP)
	install -m 0644 examples/*.knot examples/*.txt $(DATADIR)/examples/ 2>/dev/null || true
	install -m 0644 README.md $(DOCDIR)/README.md

uninstall:
	rm -f $(BINDIR)/$(APP)
	rm -rf $(DATADIR) $(DOCDIR)

clean:
	rm -f $(OBJ)
	rm -rf build dist

dist: all
	@sh packaging/build-deb.sh
