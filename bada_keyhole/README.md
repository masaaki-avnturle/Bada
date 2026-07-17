# BADA KEYHOLE — P2P インターネットTV

**KeyHole TV（P2P インターネットTV）の仕組みを参考にしたオリジナルアプリ。**
チャンネルを**視聴**し、自分のカメラを **P2P で放送**し、他の端末の放送を **P2P で受信**できます。
配信ロジックは **Bada 言語**で駆動します。

> ℹ️ 「BADA KEYHOLE」は KeyHole TV の**名称・ロゴ・ソフトウェアを使用しておらず、無関係**です。
> P2P ライブ配信という**概念**のみを参考にしたオリジナル実装です。

---

## 📺 3つのモード

| モード | 内容 |
|:---|:---|
| **📺 視聴** | 各局公式・無料のライブ配信（HLS）をチャンネルグリッドから視聴。NHK WORLD / DW / France 24 / Al Jazeera English / NASA TV ＋「URL追加」。実写のインターネットTV。 |
| **📡 放送する** | 自分の**カメラ/マイク**を **WebRTC で P2P 放送**。低ビットレート（KeyHole TV 同様に細い回線向け）対応。**招待コード**を生成して視聴者に渡します。 |
| **🔗 P2P受信** | 放送者の**招待コード**を貼り付けると**応答コード**を生成。それを放送者に返すと、**サーバーを介さず端末どうしが直接**（インターネット/NTT回線を介して）つながり、放送を受信します。 |

### P2P の接続手順（サーバー不要のシグナリング）
1. 放送者：**📡 放送開始** → カメラ起動 → **招待コード**が生成される → 視聴者へ渡す。
2. 視聴者：**🔗 P2P受信**に招待コードを貼付 → **接続** → **応答コード**が生成される → 放送者へ返す。
3. 放送者：応答コードを貼付 → **接続を確立** → P2P 映像が流れます。

NAT 越えのため STUN（`stun.l.google.com:19302`）を利用。同一 LAN では STUN 不要で直結します。

---

## 🅱 Bada 言語で書いた制御（`www/keyhole.bada`）

`bada_ruby` の `Interpreter` と同じ文法（`set / <- / -< / >- / Omega::push / print`）を移植した内蔵
インタプリタが実行します。`Ch::` はチャンネル/配信の拡張命令です。

```bada
node <- "peer to peer internet television relay"   # 左作用 π(χ,x)
node -< 1.0                                         # 多様体積分 ∬1/(x·log x)²
Omega::push node as relay_node                       # Akashic TupleSpace へ
Ch::tune channel     # 選局      Ch::broadcast  # P2P 放送
Ch::connect          # 受信      Ch::accept     # 応答取り込み   Ch::stop
```

画面下の **BADA コンソール**に実行された Bada 命令が表示されます。

---

## 📥 ダウンロード（アプリ本体）

ビルド済みの APK / EXE は **[Releases](../../releases)** および GitHub Actions の Artifacts から。

| プラットフォーム | ファイル |
|:---|:---|
| **Android** | `BadaKeyhole-x.y.z-debug.apk` |
| **Windows 10/11** | `BadaKeyhole Setup x.y.z.exe`（インストーラ） / `BadaKeyhole-x.y.z-portable.exe`（ポータブル） |

Web 版は `www/index.html` をブラウザで開くだけでも動作します（視聴/放送には接続・カメラ許可が必要）。

> 放送（カメラ配信）は**カメラ/マイクの許可**が必要です。Windows/Electron・ブラウザで動作します。
> Android APK にはカメラ/マイク権限を含めています（初回に許可してください）。視聴のみなら権限は不要です。

---

## 🛠 自分でビルド

```bash
cd bada_keyhole
npm install
npm start                 # Electron でデスクトップ起動
npm run dist:win          # Windows 10/11 用 EXE
npx cap add android && npx cap sync android && cd android && ./gradlew assembleDebug
```

## 🤖 GitHub Actions

`Actions` → **Build Bada Keyhole** → Run workflow で APK / EXE を自動生成。
タグ `keyhole-v1.0.0` を push すると Releases に添付されます。

---

*© 2025 Masaaki Yamaguchi · 山口 雅旭 · Global Differential Manifold Research*
