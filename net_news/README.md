# NET NEWS LIVE — インターネットTVニュース

**インターネットテレビ局の“実物のニュース動画”を、抽象加工なしでそのまま視聴できるビューア**

これまでの Bada アプリ群のように抽象的な演出（ホログラム/結び目レンズ等）で加工するのではなく、
**普通の動画プレーヤーで、各局が公式に無料公開しているニュースのライブ配信を、実映像のまま視聴**します。

> ⚠️ **フジテレビ・NHK（国内）の速報配信そのものは、著作権・配信規約上、本アプリには組み込めません**
> （正規許諾を確認できないため）。代わりに、各局が公式に無料公開しているライブ配信を収録し、
> **「URL追加」で、あなたが正規に利用できる配信（HLS .m3u8 / MP4）を自分で追加**できます
> （フジ/NHK 国内も、正規のソースをお持ちならここから）。

---

## 📺 収録チャンネル（各局公式の無料ライブ）

| チャンネル | 内容 |
|:---|:---|
| **NHK WORLD-JAPAN** | NHK 公式・無料の国際英語ニュース |
| **DW English** | ドイチェ・ヴェレ 公式無料ライブ |
| **France 24 English** | フランス24 公式無料ライブ |
| **Al Jazeera English** | アルジャジーラ 公式無料ライブ |
| **NASA TV** | NASA 宇宙・地球のライブ（実写） |
| **DEMO（実写サンプル）** | オフライン確認用の実写クリップ |

- **実映像プレーヤー** — 通常の `<video>` で全画面視聴（🔊 音声 / ⛶ 全画面）。
- **HLS 対応** — `.m3u8` はネイティブ（Safari/iOS）または hls.js（他ブラウザ）で再生。
- **URL追加** — 正規に利用できる HLS/MP4 を貼り付けると新チャンネルとして再生。
- **状態表示** — 「接続中…」「このチャンネルは現在再生できません」を明示。ネット接続が必要です。

> 各ライブ配信は各放送局が提供するものであり、URL は将来変更される場合があります。
> 再生できない場合は別チャンネル、または「URL追加」から正規の配信をお試しください。

---

## 📥 ダウンロード（アプリ本体）

ビルド済みの APK / EXE は **[Releases](../../releases)** および GitHub Actions の Artifacts から。

| プラットフォーム | ファイル |
|:---|:---|
| **Android** | `NetNewsLive-x.y.z-debug.apk` |
| **Windows 10/11** | `NetNewsLive Setup x.y.z.exe`（インストーラ） / `NetNewsLive-x.y.z-portable.exe`（ポータブル） |

Web 版は `www/index.html` をブラウザで開くだけでも動作します（視聴には各配信への接続が必要）。

---

## 🛠 自分でビルド

```bash
cd net_news
npm install
npm start
npm run dist:win
npx cap add android && npx cap sync android && cd android && ./gradlew assembleDebug
```

## 🤖 GitHub Actions

`Actions` → **Build Net News Live** → Run workflow で APK / EXE を自動生成。
タグ `netnews-v1.0.0` を push すると Releases に添付されます。

---

*© 2025 Masaaki Yamaguchi · 山口 雅旭 · Global Differential Manifold Research*
