CC= gcc
CFLAGS= -O2 -Iinclude -Wall
LDFLAGS= -lm

SRC= lib/manifold_entropy.c lib/jones_thermal.c lib/codegen.c \
     lib/viz_env.c lib/viz_sound.c lib/badaev_os.c lib/omega_interp.c

all: bin/launcher

bin/launcher: bin/launcher.c $(SRC)
	$(CC) $(CFLAGS) -o bin/launcher bin/launcher.c $(SRC) $(LDFLAGS)

run: bin/launcher
	./bin/launcher boot

clean:
	rm -f lib/*.o bin/launcher
