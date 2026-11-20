# vendor — 同梱ライブラリ (BadaCineVim の PDF 表示・編集用)

| ライブラリ | 版 | ライセンス | 用途 |
|:--|:--|:--|:--|
| [pdf.js](https://github.com/mozilla/pdf.js) (`pdfjs/`) | 3.11.174 | Apache-2.0 | PDF をページとして描画 |
| [pdf-lib](https://github.com/Hopding/pdf-lib) (`pdf-lib/`) | 1.17.1 | MIT | 注釈を PDF に書き込む |

`pdfjs/cmaps.bundle.js` と `pdfjs/standard_fonts.bundle.js` は、pdf.js 付属の CMap / 標準フォントを
`file://` でも読めるよう 1 本の JS にまとめたものです (`tools/build-pdf-assets.js` で再生成)。

pdf.js 3.11.174 には、フォント経由で任意の JavaScript が実行される脆弱性 (CVE-2024-4367) があります。
`pdfview.js` は公式の回避策どおり **`isEvalSupported: false`** で開くため、この経路は無効です
(この指定を外さないでください)。
