# omega_neurothermal — Makefile
CC      ?= gcc
CFLAGS  ?= -std=c99 -O2 -Wall -Wextra -D_POSIX_C_SOURCE=200809L
LDFLAGS ?= -lm

CLI      = omega_neurothermal
GUI      = omega_neurothermal_gui

# shared computation library (no main())
LIBSRC   = src/gamma_thermal.c src/basal_ganglia.c src/sensors.c \
           src/imaging.c src/labanalysis.c
LIBOBJ   = $(LIBSRC:.c=.o)

all: $(CLI) $(GUI)

$(CLI): src/main.o $(LIBOBJ)
	$(CC) $(CFLAGS) -o $@ $^ $(LDFLAGS)

$(GUI): src/gui_server.o $(LIBOBJ)
	$(CC) $(CFLAGS) -o $@ $^ $(LDFLAGS)

src/%.o: src/%.c
	$(CC) $(CFLAGS) -c $< -o $@

# CLI demo
run: $(CLI)
	./$(CLI) pipeline

# launch the GUI (open http://localhost:8080 in a browser)
gui: $(GUI)
	./$(GUI) 8080 ./web

clean:
	rm -f src/*.o $(CLI) $(GUI)

.PHONY: all run gui clean
