/*
 * paper.js — BadaGPT電信の「論文」「ビルド一式」「Claude (任意)」
 *
 *   writePaper   … 依頼 → 全体把握 → 設計 → 実装 → 検証 を学術論文の体裁で記述
 *   projectFiles … 生成アプリを Android APK / Windows 10・11 EXE / Linux AppImage・deb に
 *                  ビルドする一式 (Cordova + Electron + GitHub Actions)
 *   claudeRequest / sseFeed / extractHtml … API キーがあるときの Claude 生成
 */
"use strict";

var TYPE_JA = { string: "文字列", text: "長文", number: "数値", date: "日付", bool: "真偽", rating: "評価 (1–5)" };
var PLATFORM_JA = { android: "Android (APK)", windows: "Windows 10 / 11 (EXE)", linux: "Linux (AppImage / deb)" };

function mdCell(s) { return String(s == null ? "" : s).replace(/\|/g, "／").replace(/\n/g, " "); }

/* 論文 (Markdown) */
function writePaper(spec, gen, ver, meta) {
  meta = meta || {};
  var M = meta.metrics || telegraphMetrics(spec.input);
  var date = meta.date || new Date().toISOString().slice(0, 10);
  var author = meta.author || "BadaGPT電信 利用者";
  var engine = meta.engine || "BadaGPT電信 内蔵エンジン (オフライン・規則ベース)";
  var covered = spec.clauses.filter(function (c) { return c.hits.length; }).length;
  var passed = ver.checks.filter(function (c) { return c.ok; }).length;
  var modNames = spec.modules.map(function (m) { return m.id === "records" ? (spec.entity || "データ") + "の管理" : m.label; });
  var L = [];
  L.push("# " + spec.title + " — 思考入力からの全体把握に基づくアプリケーション生成");
  L.push("");
  L.push("**著者**: " + author + "　**日付**: " + date + "　**生成系**: " + engine + " (BadaGPT電信 v" + BGT_VERSION + ")");
  L.push("");
  L.push("## 要旨");
  L.push("");
  L.push("本稿は、自然言語で与えられた依頼 (思考入力) から、依頼の全体を取りこぼさずに捉えてアプリケーションを構成する手法を、" +
    "実際に生成したアプリケーション「" + spec.title + "」を通じて報告する。依頼文を " + spec.clauses.length + " 個の節に分解し、" +
    "その " + covered + " 個 (網羅率 " + Math.round(spec.coverage * 100) + "%) を仕様要素へ対応付けた。仕様から " + spec.modules.length +
    " 個のモジュール (" + modNames.join("・") + ") を組み合わせた自己完結 HTML アプリケーション (" + Math.round(gen.bytes / 1024) +
    " KB) を生成し、" + ver.checks.length + " 項目の検証のうち " + passed + " 項目に合格した。成果物は Android (APK)・Windows 10/11・Linux 向けに" +
    "同一のソースからパッケージ化できる。");
  L.push("");
  L.push("**キーワード**: 要求の全体把握, 節網羅率, アプリケーション自動生成, 自己完結 HTML, クロスプラットフォーム, Bada 言語");
  L.push("");
  L.push("## 1. 序論");
  L.push("");
  L.push("利用者が頭の中で思い描いたアプリケーションを言葉にしたとき、その文章には機能・扱うデータ・見た目・利用環境などの要求が混在する。" +
    "生成系がこのうち一部だけを拾い、残りを黙って捨てると、利用者は「言ったのに作られていない」部分を後から探すことになる。" +
    "本研究では、依頼文のすべての節を仕様のどれかの要素に対応付け、対応付けられなかった節も成果物と論文の双方に明記することを「全体把握」と定義する。");
  L.push("");
  L.push("本稿で扱った依頼 (思考入力) は次の通りである。");
  L.push("");
  String(spec.input || "").split("\n").forEach(function (l) { L.push("> " + l); });
  L.push("");
  L.push("## 2. 方法");
  L.push("");
  L.push("### 2.1 電信による入力");
  L.push("");
  L.push("依頼文は BADA グラビトン電信の送信プログラム (Bada 言語) によって符号化され、BadaGPT へ配信される。" +
    "符号化では依頼文のシャノンエントロピー H、ガンマ・ベータ関数による大域的部分積分多様体不変量 Ξ = β(H+1, M+1)/log(N+2)、" +
    "Jones 多項式の (2,n) トーラス結び目を算出する。これらは山口フレームワークに基づく思考実験の可視化であり、生成結果の正しさには用いない。");
  L.push("");
  L.push("| 指標 | 値 |");
  L.push("|---|---|");
  L.push("| エントロピー H | " + M.H.toFixed(3) + " bit |");
  L.push("| 多様体不変量 Ξ | " + M.xi.toFixed(4) + " |");
  L.push("| Jones 交差数 n | " + M.n + " |");
  L.push("| Kauffman 括弧 ⟨K⟩ (上位項) | " + M.bracket + " |");
  L.push("| V(2) | " + M.v2.toFixed(3) + " |");
  L.push("| テレポート忠実度 (思考実験) | " + (M.fidelity * 100).toFixed(2) + "% |");
  L.push("");
  L.push("### 2.2 全体把握");
  L.push("");
  L.push("依頼文を句点・改行で文に、読点で節に分ける (項目の列挙を含む文は 1 節として保つ)。各節を、モジュール辞書・記録対象と項目の抽出・" +
    "機能語・配色語・プラットフォーム語・題名・目的の規則に照合し、少なくとも 1 つの仕様要素に対応した節を「網羅された節」とする。" +
    "網羅率 = 網羅された節 / 全節 である。");
  L.push("");
  L.push("### 2.3 生成と検証");
  L.push("");
  L.push("仕様の各モジュールを、互いに独立した実行時コードとして組み合わせ、依存ライブラリを持たない単一の HTML ファイルを生成する。" +
    "データは端末内 (localStorage) に保存し、ネットワーク通信を行わない。生成後、HTML 骨格・JavaScript 構文・外部読み込みの有無・" +
    "依頼モジュールと項目の実装・題名の反映・網羅率・サイズを機械的に検証する。");
  L.push("");
  L.push("## 3. 結果");
  L.push("");
  L.push("### 3.1 依頼の全体把握");
  L.push("");
  L.push("| # | 節 (原文) | 対応付けた仕様要素 |");
  L.push("|---|---|---|");
  spec.clauses.forEach(function (c, i) { L.push("| " + (i + 1) + " | " + mdCell(c.text) + " | " + mdCell(c.hits.length ? c.hits.join(" / ") : "未解釈") + " |"); });
  L.push("");
  L.push("網羅率は **" + Math.round(spec.coverage * 100) + "%** (" + covered + " / " + spec.clauses.length + " 節) であった。");
  L.push("");
  L.push("### 3.2 設計");
  L.push("");
  L.push("| モジュール | 根拠 |");
  L.push("|---|---|");
  spec.modules.forEach(function (m) { L.push("| " + m.icon + " " + mdCell(m.id === "records" ? (spec.entity || "データ") + "の管理" : m.label) + " | " + mdCell(m.reason) + " |"); });
  L.push("");
  if (spec.fields && spec.fields.length && spec.modules.some(function (m) { return m.id === "records"; })) {
    L.push("記録対象「" + spec.entity + "」のデータモデルを次のように定めた。");
    L.push("");
    L.push("| キー | 項目 | 型 |");
    L.push("|---|---|---|");
    spec.fields.forEach(function (f) { L.push("| `" + f.key + "` | " + mdCell(f.name) + " | " + (TYPE_JA[f.type] || f.type) + " |"); });
    L.push("");
  }
  var fk = Object.keys(spec.features || {});
  L.push("機能: " + (fk.length ? fk.map(function (k) { return spec.features[k].label + (spec.features[k].assumed ? " (仮定)" : ""); }).join("、") : "なし") +
    "。配色: " + (spec.theme.mode === "light" ? "ライト" : "ダーク") + " / アクセント " + (spec.theme.accentName || "標準") + " (" + spec.theme.accent + ")。" +
    "対象: " + spec.platforms.map(function (p) { return PLATFORM_JA[p] || p; }).join("、") + "。");
  L.push("");
  L.push("### 3.3 実装");
  L.push("");
  L.push("生成物は単一ファイル `index.html` (" + gen.lines + " 行・" + Math.round(gen.bytes / 1024) + " KB) である。構成は次の通り。");
  L.push("");
  L.push("- 共通ランタイム: 端末内保存、CSV / JSON の書き出し、トースト通知、効果音、棒グラフ描画、タブ切り替え、ダーク / ライト切り替え");
  gen.modules.forEach(function (id) {
    var m = spec.modules.filter(function (x) { return x.id === id; })[0];
    L.push("- モジュール `" + id + "`: " + (m ? (id === "records" ? (spec.entity || "データ") + "の登録・編集・削除・一覧" : m.label) : id));
  });
  L.push("- 「この依頼について」画面: 原文・仮定・未解釈の節を利用者が確認できる");
  L.push("");
  L.push("同じ `index.html` を Cordova (Android APK) と Electron (Windows EXE / Linux AppImage・deb) に同梱し、3 種のプラットフォームへ配布する。");
  L.push("");
  L.push("### 3.4 検証");
  L.push("");
  L.push("| 検証項目 | 結果 | 詳細 |");
  L.push("|---|---|---|");
  ver.checks.forEach(function (c) { L.push("| " + mdCell(c.name) + " | " + (c.ok ? "合格" : "不合格") + " | " + mdCell(c.detail) + " |"); });
  if (meta.runtime) L.push("| 実行時エラー (プレビュー) | " + (meta.runtime.ok ? "合格" : "不合格") + " | " + mdCell(meta.runtime.detail) + " |");
  L.push("");
  L.push("## 4. 考察");
  L.push("");
  if (spec.assumptions.length) {
    L.push("依頼文に明示されていなかった点は、次の仮定で補った。");
    L.push("");
    spec.assumptions.forEach(function (a) { L.push("- " + a); });
    L.push("");
  }
  if (spec.unresolved.length) {
    L.push("次の節は仕様要素に対応付けられなかった。成果物の「この依頼について」画面に要望メモとして残し、今後の改訂で扱う。");
    L.push("");
    spec.unresolved.forEach(function (u) { L.push("- 「" + u + "」"); });
    L.push("");
  } else {
    L.push("すべての節が仕様要素に対応付けられ、取りこぼした要求はなかった。");
    L.push("");
  }
  L.push("**限界.** 内蔵エンジンは語彙と規則に基づく解析であり、辞書にない新しい種類の機能は既存モジュールの組み合わせでしか表現できない。" +
    "また「思考入力」は文章・音声・電信 (FSK 音) で与えられた依頼文を指し、脳の信号を読み取るものではない。" +
    "電信の物理量 (グラビトン↔電磁波変換・量子テレポーテーション) は思考実験の可視化である。");
  L.push("");
  L.push("## 5. 結論");
  L.push("");
  L.push("依頼文の全節を仕様要素へ対応付ける全体把握により、「" + spec.title + "」を網羅率 " + Math.round(spec.coverage * 100) + "% で構成し、" +
    "検証 " + passed + "/" + ver.checks.length + " 項目に合格する自己完結アプリケーションとして生成した。未解釈の節を成果物と論文に明記する設計は、" +
    "生成系が何を作り何を作らなかったかを利用者が確かめられるようにする。");
  L.push("");
  L.push("## 参考文献");
  L.push("");
  L.push("1. 山口 雅旭. Bada 言語と大域的部分積分多様体. Bada リポジトリ (masaaki-avnturle/Bada).");
  L.push("2. 山口 雅旭. BADA グラビトン電信 — Jones 多項式の量子テレポーテーションと FSK 音響通信.");
  L.push("3. V. F. R. Jones. A polynomial invariant for knots via von Neumann algebras. Bull. AMS 12 (1985) 103–111.");
  L.push("4. L. H. Kauffman. State models and the Jones polynomial. Topology 26 (1987) 395–407.");
  L.push("5. C. E. Shannon. A Mathematical Theory of Communication. Bell System Technical Journal 27 (1948).");
  L.push("6. Apache Cordova / Electron 公式ドキュメント (クロスプラットフォーム配布).");
  L.push("");
  return L.join("\n");
}

/* ── 生成アプリのビルド一式 (Android APK / Windows EXE / Linux) ── */
function appIdFor(slug) {
  var s = String(slug).toLowerCase().replace(/[^a-z0-9]+/g, "_").replace(/^_+|_+$/g, "");
  if (!/^[a-z]/.test(s)) s = "app_" + s;
  return "io.github.badagpt." + s;
}

function projectFiles(spec, html, paperMd) {
  var slug = slugify(spec.title), id = appIdFor(slug);
  var product = ("BadaGPT-" + slug).replace(/[^A-Za-z0-9-]/g, "");
  var desc = (spec.purpose || spec.title).slice(0, 200);
  var xmlEsc = function (s) { return escapeHtml(s).replace(/'/g, "&apos;"); };
  var pkg = {
    name: slug, productName: product, version: "1.0.0", description: desc, author: "BadaGPT Telegraph", license: "MIT",
    main: "main.js",
    scripts: { start: "electron .", dist: "electron-builder --win --x64", "dist:linux": "electron-builder --linux --x64" },
    devDependencies: { electron: "^31.0.0", "electron-builder": "^24.13.3" },
    build: {
      appId: id, productName: product, publish: null,
      files: ["main.js", "package.json"],
      extraResources: [{ from: "../www", to: "www" }],
      directories: { output: "dist" },
      win: { target: ["nsis", "portable"], artifactName: product + "-${version}-${arch}.${ext}" },
      nsis: { oneClick: false, allowToChangeInstallationDirectory: true },
      portable: { artifactName: product + "-${version}-portable.${ext}" },
      linux: { target: ["AppImage", "deb"], category: "Utility", artifactName: product + "-${version}-${arch}.${ext}", maintainer: "badagpt" }
    }
  };
  var main = [
    "/* Electron ラッパー (Windows 10/11 EXE / Linux AppImage・deb) — BadaGPT電信が生成 */",
    "const { app, BrowserWindow, shell } = require(\"electron\");",
    "const path = require(\"path\");",
    "function indexPath() {",
    "  return app.isPackaged ? path.join(process.resourcesPath, \"www\", \"index.html\") : path.join(__dirname, \"..\", \"www\", \"index.html\");",
    "}",
    "function createWindow() {",
    "  const win = new BrowserWindow({ width: 1100, height: 800, title: " + JSON.stringify(spec.title) + ", webPreferences: { contextIsolation: true, nodeIntegration: false } });",
    "  win.setMenuBarVisibility(false);",
    "  win.webContents.setWindowOpenHandler(({ url }) => { if (/^https?:\\/\\//i.test(url)) shell.openExternal(url); return { action: \"deny\" }; });",
    "  win.loadFile(indexPath());",
    "}",
    "app.whenReady().then(createWindow);",
    "app.on(\"window-all-closed\", () => { if (process.platform !== \"darwin\") app.quit(); });",
    "app.on(\"activate\", () => { if (BrowserWindow.getAllWindows().length === 0) createWindow(); });",
    ""
  ].join("\n");
  var config = [
    "<?xml version='1.0' encoding='utf-8'?>",
    "<widget id=\"" + id + "\" version=\"1.0.0\" xmlns=\"http://www.w3.org/ns/widgets\" xmlns:cdv=\"http://cordova.apache.org/ns/1.0\">",
    "  <name>" + xmlEsc(product) + "</name>",
    "  <description>" + xmlEsc(desc) + "</description>",
    "  <author href=\"https://github.com/masaaki-avnturle/Bada\">BadaGPT Telegraph</author>",
    "  <content src=\"index.html\" />",
    "  <allow-intent href=\"http://*/*\" />",
    "  <allow-intent href=\"https://*/*\" />",
    "  <preference name=\"android-minSdkVersion\" value=\"24\" />",
    "  <platform name=\"android\"><preference name=\"AndroidXEnabled\" value=\"true\" /></platform>",
    "</widget>",
    ""
  ].join("\n");
  var wf = [
    "name: Build " + product + " (Android APK + Windows EXE + Linux)",
    "",
    "# BadaGPT電信が生成したアプリ (www/index.html) を 3 種のプラットフォーム向けにビルドします。",
    "# このフォルダを GitHub リポジトリのルートに置いて push するか、Actions から手動実行してください。",
    "on:",
    "  workflow_dispatch:",
    "  push:",
    "    tags: ['v*']",
    "",
    "permissions:",
    "  contents: write",
    "",
    "jobs:",
    "  android-apk:",
    "    runs-on: ubuntu-latest",
    "    steps:",
    "      - uses: actions/checkout@v4",
    "      - uses: actions/setup-java@v4",
    "        with: { distribution: temurin, java-version: '17' }",
    "      - uses: actions/setup-node@v4",
    "        with: { node-version: 20 }",
    "      - uses: android-actions/setup-android@v3",
    "        with: { packages: '' }",
    "      - run: |",
    "          yes | sdkmanager --licenses > /dev/null 2>&1 || true",
    "          sdkmanager \"platform-tools\" \"platforms;android-33\" \"build-tools;33.0.2\"",
    "      - name: Pin Gradle 7.6.4 (cordova-android 12)",
    "        run: |",
    "          curl -sSL https://services.gradle.org/distributions/gradle-7.6.4-bin.zip -o \"$HOME/gradle.zip\"",
    "          unzip -q \"$HOME/gradle.zip\" -d \"$HOME/gradle-dist\"",
    "          echo \"$HOME/gradle-dist/gradle-7.6.4/bin\" >> \"$GITHUB_PATH\"",
    "          echo \"CORDOVA_ANDROID_GRADLE_DISTRIBUTION_URL=https://services.gradle.org/distributions/gradle-7.6.4-bin.zip\" >> \"$GITHUB_ENV\"",
    "      - name: Build debug APK (Cordova)",
    "        run: |",
    "          set -e",
    "          npm install -g cordova@12.0.0",
    "          cordova create cordova-build " + id + " " + product,
    "          rm -rf cordova-build/www && cp -r www cordova-build/www",
    "          cp cordova/config.xml cordova-build/config.xml",
    "          cd cordova-build",
    "          cordova platform add android@12.0.1",
    "          cordova plugin add cordova-plugin-file@8.1.0",
    "          cordova build android",
    "          mkdir -p ../out && cp platforms/android/app/build/outputs/apk/debug/*.apk ../out/" + slug + "-debug.apk",
    "      - uses: actions/upload-artifact@v4",
    "        with: { name: android-apk, path: out/*.apk }",
    "",
    "  windows-exe:",
    "    runs-on: windows-latest",
    "    steps:",
    "      - uses: actions/checkout@v4",
    "      - uses: actions/setup-node@v4",
    "        with: { node-version: 20 }",
    "      - working-directory: electron",
    "        run: |",
    "          npm install",
    "          npm run dist",
    "      - uses: actions/upload-artifact@v4",
    "        with: { name: windows-exe, path: electron/dist/*.exe }",
    "",
    "  linux-app:",
    "    runs-on: ubuntu-latest",
    "    steps:",
    "      - uses: actions/checkout@v4",
    "      - uses: actions/setup-node@v4",
    "        with: { node-version: 20 }",
    "      - working-directory: electron",
    "        run: |",
    "          npm install",
    "          npm run dist:linux",
    "      - uses: actions/upload-artifact@v4",
    "        with:",
    "          name: linux-app",
    "          path: |",
    "            electron/dist/*.AppImage",
    "            electron/dist/*.deb",
    ""
  ].join("\n");
  var readme = [
    "# " + spec.title, "",
    "BadaGPT電信 v" + BGT_VERSION + " が次の依頼 (思考入力) から生成したアプリケーションです。", "",
    String(spec.input || "").split("\n").map(function (l) { return "> " + l; }).join("\n"), "",
    "## 使い方", "",
    "- `www/index.html` をブラウザで開くだけで動きます (インストール不要・オフライン)。",
    "- `paper/paper.md` は、このアプリの生成過程をまとめた論文です。", "",
    "## Android (APK) / Windows 10・11 (EXE) / Linux (AppImage・deb) にする", "",
    "1. このフォルダの中身を GitHub の新しいリポジトリのルートに置いて push します。",
    "2. Actions タブ → 「Build " + product + "」→ **Run workflow**。",
    "3. 完了後、実行結果の Artifacts から `android-apk` / `windows-exe` / `linux-app` をダウンロードします。", "",
    "手元でビルドする場合: `cd electron && npm install && npm run dist` (Windows) / `npm run dist:linux` (Linux)。", ""
  ].join("\n");
  return [
    { path: "README.md", data: readme },
    { path: "www/index.html", data: html },
    { path: "paper/paper.md", data: paperMd || "" },
    { path: "electron/package.json", data: JSON.stringify(pkg, null, 2) + "\n" },
    { path: "electron/main.js", data: main },
    { path: "cordova/config.xml", data: config },
    { path: ".github/workflows/build.yml", data: wf }
  ];
}

/* ── Claude (任意): API キーがあるとき、仕様から HTML を Claude に書かせる ── */
var CLAUDE_MODELS = [
  { id: "claude-opus-5-5",   label: "Claude Opus 5.5 (既定)", fallback: true },
  { id: "claude-sonnet-5-5", label: "Claude Sonnet 5.5",      fallback: true },
  { id: "claude-haiku-5-5",  label: "Claude Haiku 5.5",       fallback: false }
];

function claudeSystemPrompt() {
  return [
    "You are BadaGPT, the application generator inside the BadaGPT Telegraph app.",
    "You receive a user's request (written in Japanese, possibly informal) and a structured spec that a rule-based analyzer extracted from it.",
    "Build exactly one complete, self-contained HTML file that implements the WHOLE request: every clause of the request must be reflected,",
    "including the ones the analyzer marked as unresolved — those are the parts most likely to be missed, so read them carefully and implement them when feasible.",
    "Constraints: no external scripts, stylesheets, fonts or network requests (the app runs offline inside Android WebView and Electron);",
    "persist user data with localStorage wrapped in try/catch; mobile-first responsive layout; Japanese UI text; use the spec's title and accent color.",
    "Include an 'この依頼について' dialog that shows the original request and lists any request you could not implement and why.",
    "Output only the HTML document, starting with <!DOCTYPE html> and ending with </html>, with no commentary before or after."
  ].join("\n");
}

function claudeUserContent(spec) {
  var brief = {
    title: spec.title, purpose: spec.purpose, modules: spec.modules.map(function (m) { return m.label; }), entity: spec.entity,
    fields: spec.fields.map(function (f) { return { name: f.name, type: f.type }; }),
    features: Object.keys(spec.features), theme: spec.theme, platforms: spec.platforms,
    clauses: spec.clauses.map(function (c) { return { text: c.text, analyzer: c.hits.length ? c.hits : "UNRESOLVED" }; })
  };
  return "<request>\n" + spec.input + "\n</request>\n\n<analyzer_spec>\n" + JSON.stringify(brief, null, 2) + "\n</analyzer_spec>";
}

function claudeRequest(opts) {
  var model = opts.model || "claude-opus-5-5";
  var info = CLAUDE_MODELS.filter(function (m) { return m.id === model; })[0];
  var headers = {
    "content-type": "application/json",
    "x-api-key": opts.apiKey,
    "anthropic-version": "2023-06-01",
    /* WebView / Electron から直接呼ぶため (キーは利用者自身のもの・端末内のみに保存) */
    "anthropic-dangerous-direct-browser-access": "true"
  };
  var body = {
    model: model, max_tokens: 64000, stream: true,
    thinking: { type: "adaptive" },
    output_config: { effort: opts.effort || "high" },
    system: claudeSystemPrompt(),
    messages: [{ role: "user", content: claudeUserContent(opts.spec) }]
  };
  if (info && info.fallback) {
    /* 安全分類器が拒否したときは既定の代替モデルへ自動で回す */
    headers["anthropic-beta"] = "server-side-fallback-2026-07-01";
    body.fallbacks = "default";
  }
  return { url: "https://api.anthropic.com/v1/messages", headers: headers, body: body };
}

function sseNew() { return { buf: "", text: "", stop: null, stopDetails: null, error: null, outTokens: 0 }; }
function sseFeed(state, chunk) {
  state.buf += chunk;
  var idx;
  while ((idx = state.buf.indexOf("\n\n")) >= 0) {
    var evt = state.buf.slice(0, idx); state.buf = state.buf.slice(idx + 2);
    var data = evt.split("\n").filter(function (l) { return l.indexOf("data:") === 0; }).map(function (l) { return l.slice(5).trim(); }).join("");
    if (!data) continue;
    var j; try { j = JSON.parse(data); } catch (e) { continue; }
    if (j.type === "content_block_delta" && j.delta && j.delta.type === "text_delta") state.text += j.delta.text;
    else if (j.type === "message_delta") {
      if (j.delta && j.delta.stop_reason) state.stop = j.delta.stop_reason;
      if (j.delta && j.delta.stop_details) state.stopDetails = j.delta.stop_details;
      if (j.usage && j.usage.output_tokens) state.outTokens = j.usage.output_tokens;
    } else if (j.type === "error") state.error = (j.error && j.error.message) || "stream error";
  }
  return state;
}

/* Claude の出力から HTML 文書を取り出す (```html フェンス付きでも可) */
function extractHtml(text) {
  var t = String(text || "");
  var f = t.match(/```html\s*\n([\s\S]*?)```/i);
  if (f) t = f[1];
  var s = t.search(/<!DOCTYPE html>/i), e = t.toLowerCase().lastIndexOf("</html>");
  if (s < 0 || e < s) return "";
  return t.slice(s, e + 7) + "\n";
}
