# YamaguchiHealth -- build file
# Native (Linux/macOS):  make
# Run:                   make run
# Clean:                 make clean

CC      ?= cc
CFLAGS  ?= -O2 -Wall -Wextra -std=c11
TARGET   = yamaguchi_health
SRC      = yamaguchi_health.c

.PHONY: all run clean

all: $(TARGET)

$(TARGET): $(SRC)
	$(CC) $(CFLAGS) -o $(TARGET) $(SRC)

run: $(TARGET)
	./$(TARGET)

clean:
	rm -f $(TARGET)
