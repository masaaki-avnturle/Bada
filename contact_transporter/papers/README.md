# 論文 PDF の投稿先

このフォルダに論文の PDF を置いて push すると (GitHub の画面なら **Add file → Upload files**)、
GitHub Actions「Bada 3 apps build」の **paper-apps** ジョブが論文ごとに

| ファイル | 中身 |
|:--|:--|
| `<論文>.apk` | Android アプリ (Bada ランナー + 論文から作った Bada アプリ、JAR 署名) |
| `bada-<論文>_1.0.0_all.deb` | Linux (Debian / Ubuntu) パッケージ — `sudo apt install ./….deb` で入り、アプリ一覧から起動 |
| `<論文>.html` | 単体で動く HTML アプリ (どの端末のブラウザでも) |
| `<論文>.bada` | ContactGPT が Bada で書いたアプリのソース (UFO 版・輸送機版も同梱) |
| `<論文>_drawing.svg` | アプリが描いた A3 図面 |
| `<論文>.pdf` | 投稿した論文 PDF (原本) |
| `<論文>.json` | 論文の解析結果 (方程式・分類・数値パラメータ) |

を作り、Artifacts の **`PaperApps`** と Release `contact-transporter-latest` に置きます。
PDF が 1 つもない場合は、同梱の設計図書 `contact_blueprint.pdf` で作ります。

アプリ (ContactGPT / 輸送機 CAD / UFO 設計図面) の「📄 論文→アプリ」タブでも、
端末上で PDF を投稿して同じものをダウンロード フォルダへ保存できます。
