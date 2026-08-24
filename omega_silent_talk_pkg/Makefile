CC      = gcc
CFLAGS  = -O2 -std=c11 -Iinclude -Wall -Wextra
LIBS    = -lm
SRC     = lib/gamma_manifold.c lib/zeta_shannon.c lib/markov_morpho.c \
          lib/jones_thermal.c lib/transformer.c lib/silent_decode.c
BIN     = bin/silent_talk

.PHONY: all demo frame clean pyviz bada

all: $(BIN)

$(BIN): bin/silent_talk.c $(SRC) include/omega_silent.h
	@echo "Building omega_silent_talk..."
	$(CC) $(CFLAGS) -o $(BIN) bin/silent_talk.c $(SRC) $(LIBS)

demo: $(BIN)
	./$(BIN) --demo

frame: $(BIN)
	@python3 usr/gen_signal.py > examples/neuro.txt 2>/dev/null || \
	  awk 'BEGIN{for(i=0;i<24;i++) print sin(i*0.6)}' > examples/neuro.txt
	./$(BIN) --frame examples/neuro.txt generated/thought_frame.pgm

pyviz: $(BIN)
	python3 usr/pipeline.py

bada:
	ruby bada/run_silent_talk.rb

clean:
	@echo "Cleaning..."
	-rm -f $(BIN) generated/*.pgm generated/*.json examples/neuro.txt
