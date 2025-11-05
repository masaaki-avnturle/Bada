# toy_chatgpt_pkg

このパッケージは、提供されたレポート群の概念（タプルスペース、多様体、カタストロフィー等）を
参照した「ChatGPT-like」教育用トイ実装一式を生成します。実運用を意図したものではなく、概念の
プロトタイプとパッケージ化手順を示すためのものです。

構成:
- src/toy_chatbot.py: ミニマルTransformerベースの実装（学習/対話可）
- src/omega_modules/: Omegaスクリプト風モジュール例（概念表現）
- setup/install.sh: 依存インストールとセットアップスクリプト
- bin/run.sh: 起動用ラッパースクリプト

使い方（UNIX系）:
  bash setup/install.sh
  bash bin/run.sh

ライセンス: MIT
