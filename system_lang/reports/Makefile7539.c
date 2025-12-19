以下は、先に生成したパッケージ（omega_www_pkg）向けの安全に動作する Makefile です。タブ文字が必要な行はそのまま保存してください（エディタがスペースに変換しないよう注意）。

保存先: omega_www_pkg/Makefile

内容:

```make
PY = python3
BIN = bin/run_server
SCRIPTS = bin/run_server
WEB_DIR = web
DATA_DIR = data
LIB = lib/server.py

  .PHONY: all run install clean prepare

  all: prepare

  prepare: $(DATA_DIR) $(SCRIPTS)
  @echo "Package prepared. Use 'make run' to start server."

  $(DATA_DIR):
  mkdir -p $(DATA_DIR)

  $(SCRIPTS):
  chmod +x $(SCRIPTS) || true
  chmod +x $(LIB) || true

  run: $(SCRIPTS)
  @echo "Starting local server..."
  $(PY) $(LIB)

  install: $(SCRIPTS)
  @echo "No global install step defined. Files are ready in current directory."

  clean:
  @echo "Cleaning generated runtime files..."
  # do not remove user data by default
  -rm -f $(WEB_DIR)/*.pyc
		     -find $(DATA_DIR) -name '*.tmp' -type f -delete || true

help:
@echo "Available targets:"
@echo "  make        - prepare (alias: make prepare)"
@echo "  make run    - start local server (requires python3)"
@echo "  make install- placeholder (no-op)"
@echo "  make clean  - remove temporary artifacts"

```

注意点
- Python サーバ起動は `make run`（内部で `python3 lib/server.py` を実行）します。環境に python3 がないとエラーになります。
- 実行権限設定で失敗しても make は続行するよう `|| true` を使用しています。
- デフォルトの clean ではユーザデータ（data/ 内のファイル）は削除しないため安全です。必要なら削除ルールを追加してください。
