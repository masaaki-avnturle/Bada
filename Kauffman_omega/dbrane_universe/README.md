# D-brane 宇宙図

`Kauffman_omega/reports` のレポートの内容をもとに、D-brane を柱とした宇宙と
異次元空間、そこから生まれる子宇宙の形を描いたインタラクティブな 3D 図です
（Three.js 0.147、ブラウザで `index.html` を開きます）。

| 図の要素 | 元のレポート |
|---|---|
| 無（ζ）→ ガンマ関数（父）→ Jones 多項式（母・三葉結び目） | `output_file.tex` dazanier あらまし |
| ゼータ関数を Z 軸に束ねた D-brane の柱（ねじれ＝Seifert 第5次元） | `output_file.tex` 「Assembile-D-braneのシリンダー」節 |
| 我々の宇宙＝無限の D-brane、有限の anti-D-brane（鏡映曲率 R′=−R） | `output_file.tex` AdS5 節, `Kalabi-Yau.tex` |
| AdS5 バルク：歪み因子 e^(−2πT‖ψ‖) | `AdS5.tex`, `Kalabi-Yau.tex` |
| 各点のカラビ・ヤウ（5次フェルマー曲面、Hanson 射影） | `Kalabi-Yau.tex` |
| 8つの子宇宙（サーストンの8幾何）→ 2つずつ 4 宇宙 → 統一宇宙 | `output_file.tex` 「８種類のサーストンの幾何化予想」 |

スライダーでブレーン張力 T（バルクの歪み・anti-D-brane の大きさ）と
カラビ・ヤウの射影角 α を変えられます。レポートの記述を図像化したもので、
物理シミュレーションではありません。

注: このファイルは Artifact として公開するために `<!doctype html>` /
`<head>` を省いた形で書いています。ローカルではそのままブラウザで開けます。
