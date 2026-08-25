# LAN → zone:// — 自分のLAN IPをウルトラネットワークに取り込む

自分のPC/LANのIPアドレスを、ウルトラネットワークの **`zone://url.or.jp/lan/`**
に**暗号化して取り込む**アプリです。各IPは zone:// ページとして UltraDatabase
クォーラム(4複製)に公開され、**Jones 多項式量子暗号**で封緘されます。
読み戻すと `200 zone-delivered` + `quorum` + `Jones-AEAD verified` を確認できます。

## 構成

```
zoneimport/
  cli/lan-to-zone.js   自分のIPv4とゲートウェイを検出し、zone://url.or.jp/lan/<IP>
                       として暗号化公開→読み戻し確認 (Node)
```
- ブラウザ アプリ(単一HTML): `../dist/lan-to-zone.html`
  (`node ../tools/build-zoneimport.js` で生成)
- zone:// ランタイムは `../browser/zone-lib.bada`(P2P DHT + UltraDB + Jones暗号)を再利用。

## 使い方

```sh
# CLI: 自分のLAN IPを検出して zone:// に取り込む
node bada_gui_ide/zoneimport/cli/lan-to-zone.js

# ブラウザ: dist/lan-to-zone.html を開き、
#   「自分のIPを検出 (WebRTC)」または手動追加 → 「取り込む」
#   → zone://url.or.jp/lan/<IP> として暗号化公開され、内容と
#     セキュリティ(quorum / Jones鍵 / AEADタグ)が表示されます。
```

## 範囲

- 取り込むのは **自分のPC/LANのIP** です。各ページは自分で入力/検出した内容だけを
  含みます。ページは Jones 量子暗号で暗号化され、UltraDatabase の複数ピアに複製
  (改ざんは自己修復)されます。
- ローカル・オフライン(ブラウザ内 zone:// ランタイム)で動作します。
