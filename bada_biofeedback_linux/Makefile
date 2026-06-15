# Bada Biofeedback — Linux native build
CC      ?= gcc
CFLAGS  ?= -std=c11 -O2 -Wall
LDLIBS  ?= -lm
BIN      = bin/bada_biofeedback

all: $(BIN)

$(BIN): bada_biofeedback.c
	@mkdir -p bin
	$(CC) $(CFLAGS) -o $@ $< $(LDLIBS)

run: $(BIN)
	./$(BIN)

clean:
	rm -f $(BIN) bada_soundscape.wav
	@rmdir bin 2>/dev/null || true

.PHONY: all run clean
