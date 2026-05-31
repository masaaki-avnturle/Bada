# biofeedback_audio - Makefile
CC      ?= gcc
CFLAGS  ?= -std=c99 -O2 -Wall -Wextra
LDLIBS  := -lm
TARGET  := biofeedback_audio

.PHONY: all clean demo

all: $(TARGET)

$(TARGET): biofeedback_audio.c
	$(CC) $(CFLAGS) -o $@ $< $(LDLIBS)

# サンプル: 全プリセットを 10 秒で ./out に生成
demo: $(TARGET)
	./$(TARGET) gen all 10 ./out

clean:
	rm -f $(TARGET)
	rm -rf ./out
