AntiGravity OS for Ubuntu / Linux
=================================

反重力発生器OS風の生成AI (量子プログラミング Bada 言語) の Ubuntu 版です。

.deb でのインストール (Ubuntu 22.04 / 24.04)
--------------------------------------------
  sudo apt install ./AntiGravityOS-1.0.0-amd64.deb
  antigravity-os          # OS init プロセス (PID 1) をブート

アプリ一覧にも「AntiGravity OS」として登録されます (端末で起動)。

tar.gz での利用 (インストール不要)
----------------------------------
  tar xzf AntiGravityOS-1.0.0-linux-x64.tar.gz
  cd antigravity-os
  ./bada run agos.bada           # OS init プロセス (PID 1)
  ./bada run sys/agkernel.bada   # 場カーネル
  ./bada run lib/aglift.bada     # 生成AI揚力制御
  ./bada run lib/agfield.bada    # 場の命令セット + ゼータ・バラスト
  ./bada run lib/agsafe.bada     # 安全インターロック
  ./build.sh                     # ソースから再ビルド + 4不変量の認証

注意
----
本ソフトウェアは計算的シミュレーション/思考実験であり、
実際の反重力・推進装置を主張するものではありません。
