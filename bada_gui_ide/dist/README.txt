zone:// — 安全なウルトラネットワーク WWW (Bada v1.1.0 + Jones 量子暗号)
================================================================

同梱ファイル:
  zone-browser.html  ★ ウルトラネットワーク専用ブラウザ。アドレスバーに
                     zone:// を入力すると P2P DHT でページを解決し、Jones
                     量子暗号で復号して表示します (1 ファイル完結・オフライン可)。
  bada-zone.html     zone.bada を実行するだけの単一ページ ランナー。
  zone.bada          zone:// スキームの Bada ソース。
  bada.js            Bada 言語コア (インタープリタ + Bada->C トランスパイラ)。
  bada-cli.js        Node.js 用 CLI ランナー。

実行方法:
  1) 専用ブラウザ: zone-browser.html をダブルクリックして開くだけ。
  2) ランナー    : bada-zone.html をダブルクリックして開くだけ。
  3) CLI         : node bada-cli.js run zone.bada
                   (bada-cli.js と bada.js を同じ階層に置いてください)
  4) C へ        : node bada-cli.js emit zone.bada -o zone.c
                   gcc -O2 -o zone zone.c -lm && ./zone

セキュリティ:
  - 各ゾーンの鍵は結び目図の Kauffman ブラケット/Jones 多項式標本から導出。
  - Bell 対 QKD (H+CNOT+Measure) がセッションソルトを合意、零の保存が
    チャネル改ざんの証拠。
  - 本文は (Jones 鍵, ソルト) をシードにした鍵ストリームで暗号化し、鍵付き
    認証タグで封緘。改ざん・誤った結び目は 409 zone-guard-reject。

(c) Masaaki Yamaguchi — Bada / Ultra Network
