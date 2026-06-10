# Ω-Apriori Core — 未知事前エンジン CPU
# 概念実証・教育用 (非医療)

CC      ?= cc
CFLAGS  ?= -O2 -Wall

.PHONY: all lib demo run clean

all: lib demo

# Python(ctypes) 用の共有ライブラリ (中核ファブリック)
lib: libaprioricpu.so
libaprioricpu.so: apriori_cpu.c apriori_cpu.h
	$(CC) $(CFLAGS) -fPIC -shared -o $@ apriori_cpu.c

# スタンドアロン C デモ
demo: apriori_demo
apriori_demo: apriori_cpu.c apriori_cpu.h
	$(CC) $(CFLAGS) -DAPRIORI_MAIN -o $@ apriori_cpu.c

# 進化を実行して run.json を出力 (HTML で読み込み可)
run: lib
	python3 apriori_engine.py --generations 150 --pop 80 --target popcount --out run.json

clean:
	rm -f libaprioricpu.so apriori_demo *.o run*.json
