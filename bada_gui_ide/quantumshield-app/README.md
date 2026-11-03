# Bada QuantumShield — 侵入時 量子クレデンシャル自動変更

量子暗号アプリ (`quantumcrypto-app` の Jones 多項式量子暗号) の **防御応用**。
ハッキングしてくるハッカーが対象 PC に **接触** すると、量子システムが即座に
その **ポート番号・バインド IP・パスワードを量子鍵に同期して変更** し、
攻撃者を締め出します。**ムービング・ターゲット・ディフェンス (MTD)** です。

- **接触 = 侵入** … ポートスキャン / 総当たり / エクスプロイト / 不正接続、
  さらに「盗んだ資格情報での接続」も接触として検知します。
- **接触した瞬間にローテーション** … 攻撃者が今まさに使っている
  ポート・IP・パスワードが、接触と同時に新しい値へ変わり失効します。
- **量子鍵に同期** … 新しい資格情報は `jonesKey(結び目図)` + 世代番号 +
  サービス名から **決定論的に** 導出されます (ローリングコード)。
- **正規の持ち主だけが追従** … 持ち主は結び目 (量子鍵) を共有しているので
  次の資格情報を計算して再接続できます。量子鍵を知らない攻撃者は
  ローテーション後の値を予測できず、盗んだ古い資格情報も無効になります。

> ⚠️ **概念シミュレーションです。** 実機のファイアウォール・実際の
> パスワード・実ネットワークは変更しません (`qcrypto.js` の量子暗号を
> 使った数理とデモ表示のみ)。リポジトリの他アプリと同じ方針です。

## 仕組み (量子鍵同期ローリングコード)

```
資格情報(port, ip, password) = f( jonesKey(結び目図),  世代generation,  サービス名 )
                                    └ 量子鍵 ─┘   └ 接触のたびに +1 ─┘

seed = SHA256( jonesKey | service | field | generation | "BadaQShield1" )
  port     = 20000 + (seed[0..3] % 40000)     # エフェメラル ポート
  bind ip  = 10.42.(seed[4]).(seed[5])        # バインド IP プール
  password = Base32風16文字 (seed[6..21])
```

攻撃者が接触 → `generation += 1` → 全フィールド再導出 → 攻撃者の持つ
(スキャン済み/盗んだ) 値は現在値と不一致 → アクセス不能。
正規の持ち主は同じ `jonesKey` と現在の `generation` から同じ値を計算できます。

## ダウンロード / ビルド

### GitHub Actions アーティファクト (タグ不要)
`main` または作業ブランチへ push すると
[**QuantumShield app build**](../../../../actions/workflows/quantumshield-app-build.yml)
が走り、下記がアーティファクトとして出ます (手動実行 `workflow_dispatch` も可):

| アーティファクト | 中身 |
|---|---|
| `quantumshield-windows` | Windows 10/11 NSIS インストーラ + ポータブル EXE |
| `quantumshield-linux`   | Ubuntu 向け AppImage + deb |
| `quantumshield-android` | Android APK |

### GitHub Release に添付
`quantumshield-v*` タグ (例 `quantumshield-v1.0.0`) を push するか、
`workflow_dispatch` の `release_tag` に指定すると、その Release に
EXE / AppImage / deb / APK が添付されます。

### ローカルで動かす
```bash
# デスクトップ (Electron)
cd bada_gui_ide/quantumshield-app/electron
npm install && npm start

# ブラウザで直接
#   bada_gui_ide/quantumshield-app/www/index.html を開くだけ (完全自己完結)
```

## コア自己検査

```bash
node bada_gui_ide/quantumshield-app/test/qshield-test.js
# => ALL QUANTUMSHIELD TESTS PASSED
```

決定論的導出 / 世代でのローテーション / 侵入検知 / 接触時失効 /
盗難資格情報の無効化 / 正規持ち主の追従 / 偽持ち主の拒否 /
監査ログ (intrusion・rotate・block) を検証します。

## 構成

```
quantumshield-app/
├─ www/
│  ├─ index.html     # GUI (対象PC / 攻撃者コンソール / 正規持ち主 / 監査ログ)
│  ├─ qshield.js     # MTD コア (deriveCreds / attackerTouch / rotate / ownerConnect)
│  └─ qcrypto.js     # 量子暗号 (jonesKey / kauffman / sha256) — quantumcrypto-app と共有
├─ electron/         # Windows EXE / Ubuntu AppImage・deb ラッパー
├─ cordova/          # Android APK 設定
└─ test/qshield-test.js
```

MIT License — https://github.com/masaaki-avnturle/Bada
