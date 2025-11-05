CC=gcc
CFLAGS=-O2 -Iinclude

all: bin/launcher lib/tools

lib/tools: lib/data_io.c lib/transform.c lib/id_map.c lib/db.c lib/predict.c lib/omega_interp.c
	$(CC) $(CFLAGS) -c lib/data_io.c lib/transform.c lib/id_map.c lib/db.c lib/predict.c lib/omega_interp.c
	$(CC) $(CFLAGS) -o lib/tools data.o transform.o id_map.o db.o predict.o omega_interp.o 2>/dev/null || true

bin/launcher: bin/launcher.c lib/omega_interp.c lib/data_io.c lib/transform.c lib/id_map.c lib/db.c lib/predict.c
	$(CC) $(CFLAGS) -o bin/launcher bin/launcher.c lib/data_io.c lib/transform.c lib/id_map.c lib/db.c lib/predict.c lib/omega_interp.c -lm

clean:
	rm -f lib/*.o bin/launcher data/raw.csv data/db/*.jsonl
