# biofeedback_audio - Makefile
#
# ターゲット:
#   biofeedback_audio : CLI 版
#   bfa_tui           : ncurses GUI 版 (端末で動作)
#   bfa_gui           : X11 GUI 版 (Xディスプレイのあるデスクトップ)
#   bfa_gtk           : GTK+3 GUI 版 (要 gtk+-3.0)
#
# リアルタイム音声(ALSA)は libasound が見つかれば自動で有効化される
# (-DBFA_HAVE_ALSA + -lasound -lpthread)。無い環境では WAV 生成に
# フォールバックし、GUI は普通にビルド・動作する。
CC      ?= gcc
CFLAGS  ?= -std=c99 -O2 -Wall -Wextra
LDM     := -lm

# ---- ALSA 自動検出 ----
HAVE_ALSA := $(shell pkg-config --exists alsa && echo 1 || echo 0)
ifeq ($(HAVE_ALSA),1)
  CFLAGS  += -DBFA_HAVE_ALSA $(shell pkg-config --cflags alsa)
  ALSA_LIBS := $(shell pkg-config --libs alsa) -lpthread
else
  ALSA_LIBS :=
endif

# ---- GTK 検出 ----
HAVE_GTK := $(shell pkg-config --exists gtk+-3.0 && echo 1 || echo 0)
GTK_CFLAGS := $(shell pkg-config --cflags gtk+-3.0 2>/dev/null)
GTK_LIBS   := $(shell pkg-config --libs gtk+-3.0 2>/dev/null)

# ---- Xft(fontconfig) 検出 ----
# X11 GUI の日本語表示に使う。無ければ旧来の XDrawString にフォールバック。
HAVE_XFT := $(shell pkg-config --exists xft && echo 1 || echo 0)
ifeq ($(HAVE_XFT),1)
  XFT_CFLAGS := -DBFA_HAVE_XFT $(shell pkg-config --cflags xft 2>/dev/null)
  XFT_LIBS   := $(shell pkg-config --libs xft 2>/dev/null)
else
  XFT_CFLAGS :=
  XFT_LIBS   :=
endif

# ---- ncurses(ワイド文字版) 検出 ----
# 日本語など UTF-8 を正しく表示するため、ワイド対応の ncursesw を優先する。
NCURSES_CFLAGS := $(shell pkg-config --cflags ncursesw 2>/dev/null)
NCURSES_LIBS   := $(shell pkg-config --libs ncursesw 2>/dev/null)
ifeq ($(strip $(NCURSES_LIBS)),)
  NCURSES_LIBS := -lncursesw
endif

CORE := audio_core.c sensors.c rt_audio.c biosignal.c
HDRS := audio_core.h sensors.h rt_audio.h biosignal.h

.PHONY: all cli tui gui gtk clean demo selftest info

all: biofeedback_audio bfa_tui bfa_gui gtk

cli: biofeedback_audio
tui: bfa_tui
gui: bfa_gui

biofeedback_audio: biofeedback_audio.c $(CORE) $(HDRS)
	$(CC) $(CFLAGS) -o $@ biofeedback_audio.c $(CORE) $(ALSA_LIBS) $(LDM)

bfa_tui: gui_ncurses.c $(CORE) $(HDRS)
	$(CC) $(CFLAGS) $(NCURSES_CFLAGS) -o $@ gui_ncurses.c $(CORE) $(NCURSES_LIBS) $(ALSA_LIBS) $(LDM)

bfa_gui: gui_x11.c $(CORE) $(HDRS)
	$(CC) $(CFLAGS) $(XFT_CFLAGS) -o $@ gui_x11.c $(CORE) -lX11 $(XFT_LIBS) $(ALSA_LIBS) $(LDM)

# GTK 版(gtk+-3.0 がある場合のみビルド)
gtk: bfa_gtk

# gtk+-3.0 が無い環境では直接 'make bfa_gtk' を叩いても
# fatal error(gtk/gtk.h not found)にせず、案内を出して安全にスキップする。
# 導入するには: sudo apt-get install libgtk-3-dev
bfa_gtk: gui_gtk.c $(CORE) $(HDRS)
ifeq ($(HAVE_GTK),1)
	$(CC) $(CFLAGS) $(GTK_CFLAGS) -o $@ gui_gtk.c $(CORE) $(GTK_LIBS) $(ALSA_LIBS) $(LDM)
else
	@echo "[skip] gtk+-3.0 が見つからないため bfa_gtk はビルドしません。"
	@echo "       GTK GUI を使うには: sudo apt-get install libgtk-3-dev"
	@echo "       (CLI/TUI/X11 は make all でそのまま使えます)"
endif

# GUI を開かずに内部ロジック(センサー+音合成)を検証
selftest: bfa_tui bfa_gui
	./bfa_tui --selftest
	./bfa_gui --selftest
ifeq ($(HAVE_GTK),1)
	$(MAKE) bfa_gtk && ./bfa_gtk --selftest
endif

demo: biofeedback_audio
	./biofeedback_audio gen all 10 ./out

info:
	@echo "ALSA(libasound): $(HAVE_ALSA)   GTK(gtk+-3.0): $(HAVE_GTK)   Xft: $(HAVE_XFT)"

clean:
	rm -f biofeedback_audio bfa_tui bfa_gui bfa_gtk
	rm -rf ./out
