# biofeedback_audio - Makefile
# ターゲット:
#   biofeedback_audio : CLI 版
#   bfa_tui           : ncurses GUI 版 (端末で動作)
#   bfa_gui           : X11 GUI 版 (Xディスプレイのあるデスクトップで動作)
CC      ?= gcc
CFLAGS  ?= -std=c99 -O2 -Wall -Wextra
LDM     := -lm

CORE := audio_core.c sensors.c

.PHONY: all cli tui gui clean demo selftest

all: biofeedback_audio bfa_tui bfa_gui

cli: biofeedback_audio
tui: bfa_tui
gui: bfa_gui

biofeedback_audio: biofeedback_audio.c audio_core.c audio_core.h
	$(CC) $(CFLAGS) -o $@ biofeedback_audio.c audio_core.c $(LDM)

bfa_tui: gui_ncurses.c $(CORE) audio_core.h sensors.h
	$(CC) $(CFLAGS) -o $@ gui_ncurses.c $(CORE) -lncurses $(LDM)

bfa_gui: gui_x11.c $(CORE) audio_core.h sensors.h
	$(CC) $(CFLAGS) -o $@ gui_x11.c $(CORE) -lX11 $(LDM)

# GUI を開かずに内部ロジック(センサー+音合成)を検証
selftest: bfa_tui bfa_gui
	./bfa_tui --selftest
	./bfa_gui --selftest

# 全プリセットを 10 秒で ./out に生成
demo: biofeedback_audio
	./biofeedback_audio gen all 10 ./out

clean:
	rm -f biofeedback_audio bfa_tui bfa_gui
	rm -rf ./out
