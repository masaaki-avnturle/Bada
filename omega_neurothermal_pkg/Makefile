# omega_neurothermal — Makefile
CC      ?= gcc
CFLAGS  ?= -std=c99 -O2 -Wall -Wextra -D_POSIX_C_SOURCE=200809L
LDFLAGS ?= -lm
BIN      = omega_neurothermal
SRC      = $(wildcard src/*.c)
OBJ      = $(SRC:.c=.o)

all: $(BIN)

$(BIN): $(OBJ)
	$(CC) $(CFLAGS) -o $@ $(OBJ) $(LDFLAGS)

src/%.o: src/%.c
	$(CC) $(CFLAGS) -c $< -o $@

run: $(BIN)
	./$(BIN) pipeline

clean:
	rm -f $(OBJ) $(BIN)

.PHONY: all run clean
