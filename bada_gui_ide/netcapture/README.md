# QuantumShark — 量子暗号つきパケット アナライザ

Wireshark 風のパケット解析ツールに、以前作った **Jones 多項式量子暗号** を
付けたアプリです。**自分のマシンの通信**をキャプチャして、キャプチャ ファイル
(`.qcap`)を量子暗号で**暗号化して保存**し、マスターパスワードで復号して
解析します(保存時暗号化。誤ったマスターでは開けません)。防御的な自己分析用途です。

## 構成

```
netcapture/
  cli/qshark-capture.js   tshark / tcpdump で自分のIFをキャプチャし、
                          Jones 量子暗号で暗号化した .qcap を書き出す (Node)
```
- 復号ビューア(単一HTML): `../dist/quantum-shark.html`
  (`node ../tools/build-quantum-shark.js` で生成。マスター `demo` のデモ内蔵)
- 暗号コアは `../modemvault/modemvault-lib.bada`(Jones 鍵 AEAD)を再利用。

## 使い方

```sh
# 1) 自分のIFをキャプチャして暗号化 .qcap を作る (要 tshark か tcpdump / 権限)
node bada_gui_ide/netcapture/cli/qshark-capture.js --master 'あなたの鍵' --count 300 -o mycap.qcap
#    キャプチャツールが無い環境の確認用:
node bada_gui_ide/netcapture/cli/qshark-capture.js --master demo --demo -o demo.qcap

# 2) ビューアで開く
#    bada_gui_ide/dist/quantum-shark.html をブラウザで開き、
#    マスターを入れて「.qcap を選択」→ mycap.qcap を開く
```

主なオプション: `--iface <if>` `--count <n>` `--filter <bpf>` `-o <out.qcap>`
`--master <pw>`(または環境変数 `QSHARK_MASTER`)。

## セキュリティと範囲

- `.qcap` は **Jones 量子暗号 AEAD** で暗号化されて保存されます。鍵はマスター
  パスワードから結び目→Jones 多項式で導出。**誤ったマスターはタグ照合に失敗**し
  復号できません(改ざんも検知)。マスターはファイルに保存されません。
- キャプチャは **自分が管理するインターフェース** に対して行うものです
  (tshark/tcpdump 実行には通常 root/管理者権限が必要)。他者の通信の傍受を
  目的とするものではありません。
