# 🛡️ Bada RDP Guard — 端末間 相互デジタル署名で RDP 乗っ取りを防ぐ

RDP(リモートデスクトップ)の弱点である**なりすまし・セッション乗っ取り**を防ぐ
**防御**ソフトです。RDP セッションを許可する前に、接続する 2 つの端末が互いに
**デジタル署名のチャレンジ・レスポンス**で身元を証明し合います。秘密鍵を持たない
攻撃者はどちらの端末にもなりすませないため、**盗んだ資格情報だけでは RDP に入れません**
(端末そのものを鍵にする多要素認証)。Bada 言語・PHP・Web アプリケーションで実装。

> ⚠️ **防御の概念実装です。** 実際の RDP パケットや mstsc は操作しません。
> RDP ゲートウェイ/プロキシが接続受付時にこのライブラリの `verify` を呼び、
> 認証に失敗したら RDP を張らせない、という使い方を想定した参照実装です。

## 仕組み

### 1. ハッシュの不可逆性だけに依存するデジタル署名
日本語で言えば「一方通行の計算」です。鍵の安全性は、ハッシュ関数が
**非可逆(一方向)**であること — 出力から入力(原像)を戻せないこと — だけに依存します。

- **Lamport 一回署名 (OTS)**: 秘密鍵は乱数の原像、公開鍵はその SHA-256 ハッシュ。
  署名はメッセージのビットに応じて原像を公開する。公開鍵から秘密鍵は戻せない。
- **Merkle 署名方式**: 複数の Lamport 公開鍵を 1 本の木にまとめ、**根 (root)** を
  端末の安定した**指紋 (fingerprint)** として相手に**ピン留め**する。各セッションは
  1 枚の葉を使い、認証パスで指紋に結びつける(XMSS 系の縮小版)。
- **順序依存(非可換)性**: Merkle パスと Reviser のタプル辞書式順序で、合成の順番が
  結果を変える(順序を変えると検証が通らない)。

### 2. 相互認証ハンドシェイク — なりすまし・リプレイを阻止
両端末が「セッション ID ∥ 自分→相手 ∥ 相手のノンス」に署名し、相手の**既知の指紋**で
検証します。

- **なりすまし拒否**: 攻撃者が端末名を詐称しても、本物の秘密鍵を持たないため署名が
  相手の指紋で検証に失敗 → RDP 乗っ取りを阻止。
- **リプレイ拒否**: 署名はセッション ID とノンスに束縛されるため、盗んだ古い署名を
  別セッションで再送しても無効(反射・再送攻撃対策)。

### 3. Reviser — tuple-network の辞書式順序でポリシーにパッチ
誰が・どこから・どこへ・何を、を表すタプル `[zone, src, dst, user, …]` を鍵に、
ベース方針へパッチを**辞書式順序**で適用します。同じタプルは辞書順で**後のパッチが
上書き**し、接続には**最も具体的(最長一致)**なルールを、既定は**拒否**を適用します。
決定論的なので監査・再現が可能です(例: インシデント対応で admin を一時 deny に改訂)。

## 構成

```
rdp_guard/
├─ core/rdpguard.js     # コア (UMD, Node/ブラウザ共通): SHA-256 / Lamport / Merkle /
│                       #   相互ハンドシェイク / Reviser
├─ web/
│  ├─ index.html        # ブラウザ デモ (正規認証・なりすまし・リプレイ・Reviser)
│  └─ rdpguard.js       # core と同一コピー (CI が byte 一致を検証)
├─ php/
│  ├─ RdpGuard.php      # PHP 版コア (JS と相互運用: 同じ seed → 同じ指紋・署名)
│  └─ server.php        # RDP ゲートウェイ API / デモ配信 (php -S)
├─ bada/rdpguard.bada   # Bada 言語 参照 (Lamport ハッシュ連鎖 S/KEY で防御を実演)
├─ tools/
│  ├─ test-rdpguard.js  # Node 自己検査
│  └─ test-rdpguard.php # PHP 自己検査 (+ JS 相互運用)
└─ README.md
```

## 使い方

### ブラウザ デモ(依存ゼロ)
`rdp_guard/web/index.html` を開くだけ。2 端末の相互認証、攻撃者のなりすまし/リプレイ
拒否、Reviser の方針判定を体験できます。

### PHP サーバ / RDP ゲートウェイ API
```bash
php -S 127.0.0.1:8080 rdp_guard/php/server.php
#  GET  /                … デモ UI
#  POST /api/handshake   … 相互認証   {"seed":"...","impostor":false}
#  POST /api/revise      … 方針改訂+判定 {"base":[...],"patches":[...],"conn":[...]}
```
実運用では、RDP ゲートウェイが接続受付時に `/api/handshake` 相当を呼び、
`ok=false` なら RDP を張らせません。

### Bada 言語 参照
```bash
node bada_gui_ide/cli/bada-cli.js run rdp_guard/bada/rdpguard.bada
```

## テスト

```bash
node rdp_guard/tools/test-rdpguard.js     # => ALL RDPGUARD TESTS PASSED
php  rdp_guard/tools/test-rdpguard.php     # => ALL RDPGUARD PHP TESTS PASSED
```

- **SHA-256** を既知ベクタおよび Node `crypto` と突き合わせ。
- **Lamport / Merkle**: 正しい署名は検証を通り、改ざん・原像を知らない偽造は失敗。
- **相互認証**: 正規端末は成功、なりすまし(別鍵)とリプレイ(別ノンス)は拒否。
- **Reviser**: 辞書式順序の後勝ち・最長一致・既定拒否・決定論性。
- **相互運用**: 同じ seed から JS と PHP が**同一の指紋**を生成(byte 一致)。
- ブラウザ UI は Playwright/Chromium スモークで、正規認証→なりすまし拒否→
  リプレイ拒否→Reviser 判定まで確認済み。

ビルド/検証は [`rdpguard-build.yml`](../.github/workflows/rdpguard-build.yml) が
Actions で自動実行し、Web 一式を**アーティファクト**として配布します。

MIT License — https://github.com/masaaki-avnturle/Bada
