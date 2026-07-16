# Bada Foundry — アプリを作るアプリ

**方程式ネットワーク → 未知事前予知エンジン → 生成アプリ**

山口フレームワークの**方程式同士のネットワーク**を入力に取り、アプリ自身の
**未知事前予知エンジン**（Thurston–Perelman 幾何配置 ＋ カタストロフィ分岐 ＝
`Bada::InfoEngine` の前段）で、各方程式に対応する**ソースコードを意味付け**し、
そこから**動作するアプリケーション（子アプリ）を自動生成**する、
**Bada 言語製の「アプリを作るアプリ」**です。

生成された子アプリ自体も、その場で **ダウンロード**できます。

---

## 🔩 何をするアプリか

1. **方程式ネットワークを構成** — 左パネルで方程式を選ぶと、共有する記号
   （β, Γ, ζ, π, □, ∇, ⊗, ∫ …）で自動的にエッジが張られ、中央にネットワーク
   グラフが描かれます。
2. **未知事前予知エンジンで意味付け** — 各方程式を
   - `Ξ`（大域的部分積分多様体エントロピー不変量 `β(H+1,M+1)/log(N+1)`）
   - サーストンの 8 幾何のどれに落ちるか（`place_entropy`）
   - カタストロフィ分岐数（cusp の実根数）
   で解析し、幾何 → アプリのモジュール原型（共鳴コア / 双曲網 / 対数螺旋 …）へ写像します。
3. **ソースコードを生成** — 意味付け結果から
   - **Bada 言語プログラム**（`.bada`, `<- -< >- Omega::push` 演算子で記述）
   - **実行可能な子アプリ**（自己完結 HTML, 各モジュールが Ξ・曲率・分岐数で駆動される描画）
   を生成します。
4. **ダウンロード** — 生成アプリ `.html`・Bada ソース `.bada`・仕様 `.json` を保存できます。

エンジンの数理は `bada_ruby/lib/bada`（`Manifold` / `Thurston` / `Catastrophe` /
`Foundry`）と同一で、ブラウザ版はその忠実な JS 移植です。

---

## 📥 ダウンロード（アプリ本体）

ビルド済みの APK / EXE は本リポジトリの **[Releases](../../releases)** および
GitHub Actions の Artifacts から入手できます。

| プラットフォーム | ファイル | 説明 |
|:---|:---|:---|
| **Android** | `BadaFoundry-x.y.z-debug.apk` | 端末にそのままインストール可 |
| **Windows 10/11** | `BadaFoundry Setup x.y.z.exe` | インストーラ版 |
| **Windows 10/11** | `BadaFoundry-x.y.z-portable.exe` | ポータブル版（単体EXE） |

Web 版は `www/index.html` をブラウザで開くだけでも動作します。

---

## 🖥 Bada 言語 CLI からも生成できる

`bada_ruby` の Bada 言語処理系にも Foundry を組み込みました（外部依存なし・Ruby 3.0+）:

```bash
cd bada_ruby
ruby -Ilib test/test_foundry.rb           # テスト
bin/bada foundry \
  "β(p,q) = Γ(p)Γ(q)/Γ(p+q)" \
  "ζ(s) = β(p,q)/logx = x·logx" \
  "□ = cos(ix·logx) - i·sin(ix·logx)" \
  --name "Bada::MyApp" --out out/
# → out/Bada_MyApp.bada   (生成された Bada プログラム)
#   out/Bada_MyApp.html   (ダウンロード可能な生成アプリ本体)
#   out/Bada_MyApp.spec.json
# さらに生成された Bada プログラムを実行し、意味の実行証跡を表示します。
```

---

## 🛠 自分でビルド

```bash
cd bada_foundry
npm install
npm start              # デスクトップ起動
npm run dist:win       # Windows 10/11 EXE を dist/ に生成

npx cap add android    # Android プロジェクト生成
npx cap sync android
cd android && ./gradlew assembleDebug   # → app-debug.apk
```

## 🤖 GitHub Actions（推奨）

`Actions` → **Build Bada Foundry** → Run workflow で APK / EXE を自動生成。
タグ `foundry-v1.0.0` を push すると Releases に添付されます。

---

## 📂 構成

```
bada_foundry/
├── www/index.html          # アプリ本体（方程式ネットワーク + 未知事前予知 + 生成器）
├── electron/main.js        # Windows/デスクトップ用 Electron
├── package.json            # electron-builder / Capacitor 設定
├── capacitor.config.json   # Android 設定
├── resources/icon.ico|png  # ネットワークモチーフ アイコン
└── README.md
bada_ruby/lib/bada/foundry.rb   # Bada 言語版エンジン（同一数理）
.github/workflows/build-foundry.yml
```

*© 2025 Masaaki Yamaguchi · 山口 雅旭 · Global Differential Manifold Research*
