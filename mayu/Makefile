# 窓使いの憂鬱 (mayu) — 開発用ターゲット

PY ?= python3

.PHONY: test demo check keys install run help

help:
	@echo "make test    - テストを実行"
	@echo "make demo    - 主要な変換例を表示"
	@echo "make check   - 同梱 example 設定を検証"
	@echo "make keys    - 既知のキー名一覧"
	@echo "make install - pip でローカルインストール (mayu コマンド)"
	@echo "make run     - (Linux) 実キーフックを開始 (要 sudo)"

test:
	$(PY) -m pytest tests/ -q

demo:
	@echo "=== Emacs 風カーソル移動 ==="
	$(PY) -m mayu.cli simulate examples/emacs.mayu --keys "C-b C-f C-n C-p C-a C-e C-k"
	@echo ""
	@echo "=== CapsLock <-> LeftControl 入れ替え ==="
	$(PY) -m mayu.cli simulate examples/swap-ctrl-caps.mayu --keys "CapsLock LeftControl a"
	@echo ""
	@echo "=== Windows + hjkl で矢印 (vi 風) ==="
	$(PY) -m mayu.cli simulate examples/vi-nav.mayu --keys "W-h W-j W-k W-l"

check:
	$(PY) -m mayu.cli check examples/emacs.mayu
	$(PY) -m mayu.cli check examples/swap-ctrl-caps.mayu
	$(PY) -m mayu.cli check examples/vi-nav.mayu

keys:
	$(PY) -m mayu.cli keys

install:
	$(PY) -m pip install -e .

run:
	sudo $(PY) -m mayu.cli run examples/emacs.mayu
