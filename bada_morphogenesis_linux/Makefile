# Bada Morphogenesis — Linux native build
CC      ?= gcc
CFLAGS  ?= -std=c11 -O2 -Wall
LDLIBS  ?= -lm
BIN      = bin/bada_morphogenesis

all: $(BIN)

$(BIN): bada_morphogenesis.c
	@mkdir -p bin
	$(CC) $(CFLAGS) -o $@ $< $(LDLIBS)

run: $(BIN)
	./$(BIN)

clean:
	rm -f $(BIN)
	@rmdir bin 2>/dev/null || true

.PHONY: all run clean
