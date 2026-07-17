# JONES LENS — ホログラフィック・アイウェア

**Jones多項式 × 特殊相対性理論のレンズ焦点で、アイウェアのレンズにインターネットTVの動画を投影**

これまでの Bada アプリ群（ガンマ関数 大域的部分積分多様体・熱エントロピー、インターネットTV動画、
visionOS 参考の空間UI）を使い、**スマートグラス（アイウェア）のレンズに、インターネットTVの本当の動画を
ホログラム投影**するアプリです。投影の**焦点**を、**Jones多項式（結び目）**と
**特殊相対性理論のレンズ焦点原理（相対論的光行差・ドップラー）**で制御します。

> ⚠️ **ニュース速報について**：フジテレビ・NHK（国内）の速報配信は著作権・配信規約上、本アプリに組み込めません。
> 代わりに、**合法に自由視聴できる公式の無料ニュースライブ**（**NHK WORLD-JAPAN**〔NHK公式の無料国際ニュース〕・
> **DW** ・**France 24** ・**Al Jazeera English** ・**NASA**）を収録し、**「URL追加」であなたが正規に利用できる
> 配信（HLS .m3u8 / MP4）を貼り付け**られます（フジ/NHK 国内も、正規のソースをお持ちならここから）。
> ストリーム不達時はエンジン映像に自動フォールバック。汎用アイウェアのコンセプト（実在の眼鏡店とは無関係）。

---

## 🕶 原理と操作

### 特殊相対性理論のレンズ焦点
- **相対論的光行差**：`cosθ′ = (cosθ + β) / (1 + β·cosθ)`（β = v/c）で、視線方向の光が前方へ集束。
  β を上げるとレンズ中心へ強く集束（前方集束）し、焦点円が締まります。
- **相対論的ドップラー色収差**：焦点中心＝青方偏移（近づく）／周縁＝赤方偏移（遠ざかる）を色で表現。
- **焦点 f**：レンズ焦点の位置を水平に移動。

### Jones多項式（結び目）で焦点変調
- **(2,n) トーラス結び目**の **Kauffman 括弧**を Temperley–Lieb 代数 TL₂ で計算し、
  **Jones多項式 V(t)** を求めます（n=3 で三葉結び目 = 正しい Jones 多項式を再現）。
- レンズ上には (2,n) 結び目の**ホログラム・ブレイド**を重畳。
- 焦点リングの強度を **|V(e^{iθ})|** で変調（＝Jones多項式が焦点を制御）。
- HUD に **交差数 n・Kauffman 括弧 ⟨K⟩・V(2)・|V|** を表示。

### インターネットTV / visionOS 参考
- **本当の動画**（無料/CC 配信）をレンズにホログラム投影。◀▶ でチャンネル切替、
  「📺 実映像/エンジン」「🔊 音声」。
- **立体視 / VR（SBS）**：左右2眼でカードボード/VR ゴーグル対応。**ジャイロ**で端末の傾き＝視点移動。
- 視線レティクル・空間の床グリッド・浮遊ダスト・ホームインジケータ（visionOS 参考の空間UI）。

---

## 📥 ダウンロード（アプリ本体）

ビルド済みの APK / EXE は **[Releases](../../releases)** および GitHub Actions の Artifacts から。

| プラットフォーム | ファイル |
|:---|:---|
| **Android** | `JonesLens-x.y.z-debug.apk` |
| **Windows 10/11** | `JonesLens Setup x.y.z.exe`（インストーラ） / `JonesLens-x.y.z-portable.exe`（ポータブル） |

Web 版は `www/index.html` をブラウザで開くだけでも動作します。

---

## 🛠 自分でビルド

```bash
cd jones_lens
npm install
npm start              # デスクトップ起動
npm run dist:win       # Windows 10/11 EXE を dist/ に生成

npx cap add android
npx cap sync android
cd android && ./gradlew assembleDebug   # app-debug.apk
```

## 🤖 GitHub Actions

`Actions` → **Build Jones Lens** → Run workflow で APK / EXE を自動生成。
タグ `jones-v1.0.0` を push すると Releases に添付されます。

---

*© 2025 Masaaki Yamaguchi · 山口 雅旭 · Global Differential Manifold Research*
*visionOS / Apple Vision Pro の空間UIを参考にしたデザインです（Apple とは無関係）。*
