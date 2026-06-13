CC      = gcc
CFLAGS  = -O2 -std=c11 -Wall -Wextra -Iinclude
LDFLAGS = -lm

all: bin/resonance_dialog lib/libbada_resonance.a

bin/resonance_dialog: bin/resonance_dialog.c lib/libbada_resonance.a
	$(CC) $(CFLAGS) -o $@ bin/resonance_dialog.c lib/libbada_resonance.a $(LDFLAGS)

lib/libbada_resonance.a: lib/bada_resonance.o
	ar rcs $@ $^

lib/bada_resonance.o: lib/bada_resonance.c include/bada_resonance.h
	$(CC) $(CFLAGS) -c -o $@ lib/bada_resonance.c

demo: bin/resonance_dialog
	./bin/resonance_dialog --demo

clean:
	rm -f lib/*.o lib/*.a bin/resonance_dialog

.PHONY: all demo clean
