CC= gcc
CFLAGS= -O2 -Iinclude -Wall
LDFLAGS= -lm

SRC= lib/em_field.c lib/aero.c lib/manifold_gravity.c lib/jones_thermal.c lib/badaos.c lib/omega_interp.c

all: bin/launcher

bin/launcher: bin/launcher.c $(SRC)
	$(CC) $(CFLAGS) -o bin/launcher bin/launcher.c $(SRC) $(LDFLAGS)

run: bin/launcher
	./bin/launcher boot

clean:
	rm -f lib/*.o bin/launcher
