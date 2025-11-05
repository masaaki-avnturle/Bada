CC= gcc
CFLAGS= -O2 -Iinclude
LDFLAGS= -lcrypto -lm

all: bin/launcher

lib: lib/jones_key.c lib/crypto.c lib/omega_interp.c
	$(CC) $(CFLAGS) -c lib/jones_key.c lib/crypto.c lib/omega_interp.c
	$(CC) $(CFLAGS) -o bin/launcher bin/launcher.c lib/jones_key.o lib/crypto.o lib/omega_interp.o $(LDFLAGS)

bin/launcher: bin/launcher.c lib/jones_key.c lib/crypto.c lib/omega_interp.c
	$(CC) $(CFLAGS) -o bin/launcher bin/launcher.c lib/jones_key.c lib/crypto.c lib/omega_interp.c $(LDFLAGS)

clean:
	rm -f lib/*.o bin/launcher
