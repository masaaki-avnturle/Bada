CC = gcc
CFLAGS = -O2 -std=c11 -Wall -Wextra -Iinclude
LDFLAGS = -lm

all: bin/finpred lib/libfinpred.a

bin/finpred: bin/finpred.c lib/libfinpred.a
	$(CC) $(CFLAGS) -o $@ bin/finpred.c lib/libfinpred.a $(LDFLAGS)

lib/libfinpred.a: lib/finpred.o
	ar rcs $@ $^

lib/finpred.o: lib/finpred.c include/finpred.h
	$(CC) $(CFLAGS) -c -o $@ lib/finpred.c

clean:
	rm -f lib/*.o lib/*.a bin/finpred

.PHONY: all clean
