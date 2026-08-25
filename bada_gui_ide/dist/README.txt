zone:// — 安全なウルトラネットワーク WWW (Bada v1.1.0 + Jones 量子暗号)
================================================================

同梱ファイル:
  bada-zone.html  この 1 ファイルだけで完結。ブラウザで開くと暗号化 zone:// が
                  動きます (オフライン可・依存なし)。
  zone.bada       zone:// スキームの Bada ソース。
  bada.js         Bada 言語コア (インタープリタ + Bada->C トランスパイラ)。
  bada-cli.js     Node.js 用 CLI ランナー。

実行方法:
  1) ブラウザ:  bada-zone.html をダブルクリックして開くだけ。
  2) CLI     :  node bada-cli.js run zone.bada
                (bada-cli.js と bada.js を同じ階層に置いてください)
  3) C へ    :  node bada-cli.js emit zone.bada -o zone.c
                gcc -O2 -o zone zone.c -lm && ./zone

セキュリティ:
  - 各ゾーンの鍵は結び目図の Kauffman ブラケット/Jones 多項式標本から導出。
  - Bell 対 QKD (H+CNOT+Measure) がセッションソルトを合意、零の保存が
    チャネル改ざんの証拠。
  - 本文は (Jones 鍵, ソルト) をシードにした鍵ストリームで暗号化し、鍵付き
    認証タグで封緘。改ざん・誤った結び目は 409 zone-guard-reject。

(c) Masaaki Yamaguchi — Bada / Ultra Network
