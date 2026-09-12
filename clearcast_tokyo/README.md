# 🔑 クリアキャスト東京 — ClearCast Tokyo

**東京のテレビ・ラジオを、雑音・画像の乱れゼロの「公式デジタル配信」で視聴するクリーン視聴アプリ。**
単一 HTML・依存ゼロ。Android APK / Windows 10・11 EXE / Ubuntu AppImage・deb を GitHub Actions がビルドします。

## KeyHole TV との関係 (重要)

かつての **KeyHole TV** は、テレビ・ラジオ放送を P2P で**再送信**する仕組みでした。
放送の無許諾再送信は日本の著作権法(公衆送信権・送信可能化権)に抵触するため、
**本アプリは再送信・ストリーム抽出・録画再配信を一切行いません。**

代わりに、**放送局自身が公式に無料配信しているストリームだけ**を 1 画面にまとめ、
「1クリックで東京の放送へ」という KeyHole TV 的な使い勝手を合法に再現します。
そして公式配信はすべてデジタルなので、アナログ受信特有の**スノーノイズ・ゴースト・音声雑音は原理的に発生しません**。

## できること

| タブ | 内容 |
|:---|:---|
| 📡 **ライブ視聴** | 在京キー局系列の公式 YouTube 24 時間ニュースライブをアプリ内再生 — 日テレNEWS / ANN(テレビ朝日) / TBS NEWS DIG / テレ東BIZ / FNN(フジテレビ)。チャンネル ID・動画 URL の貼り付けで自分のカードも追加可能(端末内保存)。 |
| 📺 **テレビ公式** | TVer リアルタイム配信・見逃し配信 / NHKプラス / ABEMA / TOKYO MX / NHK ニュース・防災 をワンタップで公式プレーヤーへ。 |
| 📻 **ラジオ** | radiko (TBSラジオ・文化放送・ニッポン放送・TOKYO FM・J-WAVE・interfm・ラジオNIKKEI) と NHK らじる★らじる (R1・R2・FM) の公式プレーヤーへ。 |
| 📶 **回線診断** | クリーン・シグナル・エンジン — RTT を複数回計測してジッタを統計 (μ・σ)、**ITU-T G.107 E モデル** `R = 93.2 − Id(遅延) − Ie,eff(損失)` から **MOS** を推定、**推奨画質**(帯域しきい値)と**推奨バッファ** `clamp(3·(μ+4σ)/1000, 2s, 30s)` を算出。帯域不足によるブロックノイズ・再生停止を未然に防ぎます。 |

## 使い方 (ブラウザ版)

[`index.html`](index.html) を開き **「Download raw file」(⬇)** で保存 → ダブルクリックで起動。
インストール不要・オフラインでも UI は動作します(視聴には当然ネットが必要です)。

## ネイティブアプリ (APK / Windows / Ubuntu)

[Releases](https://github.com/masaaki-avnturle/Bada/releases) から:

| プラットフォーム | ファイル |
|:---|:---|
| **Android** (APK) | `clearcast-tokyo-debug.apk` |
| **Windows 10 / 11** | `ClearCastTokyo-*-x64.exe` (NSIS インストーラ / ポータブル) |
| **Ubuntu** | `ClearCastTokyo-*-x86_64.AppImage` / `ClearCastTokyo-*-amd64.deb` |

ビルドは [`clearcast-app-build.yml`](../.github/workflows/clearcast-app-build.yml) が実行します:

- `clearcast-v*` タグを push → 3 プラットフォームをビルドして **GitHub Release に添付**
- Actions の **workflow_dispatch** で手動実行 → Actions アーティファクトとして取得
  (`release_tag` を指定すれば Release にも添付)

ラッパーの方針: 公式 YouTube 埋め込みはアプリ内で再生し、TVer・radiko など
DRM/エリア判定のある公式サービスは**端末の既定ブラウザ・公式アプリ**で開きます
(各サービスが最良の画質・音質で再生されるため)。

## テスト

```
node clearcast_tokyo/tools/engine-test.js
```

ジッタ統計 / E モデル R 値・MOS(境界含む)/ 推奨画質・バッファの clamp /
YouTube URL 正規化 / **局カタログが公式配信ドメインのみを含むこと**(合法性の自動チェック)を検証します。

## 権利表記

各配信の権利は各放送局・配信事業者(日本テレビ、テレビ朝日、TBS、テレビ東京、フジテレビ、NHK、TOKYO MX、TVer、ABEMA、radiko ほか)に帰属します。本アプリは非公式のリンク集+公式埋め込みプレーヤーであり、各社とは無関係です。radiko・TVer・NHKプラスには日本国内のエリア・契約条件があります。MIT License (アプリ本体のコードのみ)。
