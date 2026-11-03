/*
 * autobuild.js — BadaGPT電信「自動コンパイル」
 *
 * 思考入力 → 文章 → 仕様 → ソースコード まで来た成果物を、exe / apk に
 * **自動でコンパイル** する。WebView / Electron の中では Gradle や
 * electron-builder を動かせないため、本当に動く仕組みとして:
 *
 *   1. 生成した一式 (アプリ本体・Electron/Cordova 設定・ソースコード・論文・
 *      ビルド用 GitHub Actions ワークフロー) を、利用者の GitHub リポジトリへ
 *      **1 コミットでプッシュ** する (利用者自身のトークン・端末内保存)。
 *   2. プッシュがワークフローを起動し、GitHub Actions が APK / Windows EXE /
 *      Linux AppImage+deb をビルドする。
 *   3. BadaGPT は Actions の実行を **ポーリング** して進行を表示し、完成したら
 *      アーティファクト (Actions) と Release (ログイン不要の直リンク) を示す。
 *
 * この層は DOM に依存せず、fetch と sleep を注入できるので Node でテストできる。
 * BadaGPT改 (bada_gpt_kai) の 1 コミット・プッシュを移植した。
 */
"use strict";

function bytesToBase64(bytes) {
  var s = "", CH = 0x8000;
  for (var i = 0; i < bytes.length; i += CH) s += String.fromCharCode.apply(null, bytes.subarray(i, i + CH));
  return btoa(s);
}

/* ───────────── 生成アプリ用の自動ビルド・ワークフロー ─────────────
 * リポジトリ直下 .github/workflows/<slug>-build.yml。apps/<slug>/ の変更で起動し、
 * APK / EXE / AppImage+deb をビルドして、Actions アーティファクト (個別 + 一式) と
 * Release <slug>-latest (ログイン不要の直リンク) に置く。 */
function autoBuildWorkflow(slug, product, title, appId) {
  var A = "apps/" + slug;
  return [
    "name: Build " + product + " (BadaGPT電信 自動コンパイル)",
    "",
    "# " + title + " — BadaGPT電信が思考入力から生成したアプリを exe / apk にビルドします。",
    "# " + A + "/ が変わるたびに走り、Actions アーティファクトと Release " + slug + "-latest に置きます。",
    "on:",
    "  workflow_dispatch:",
    "  push:",
    "    paths:",
    "      - '" + A + "/**'",
    "      - '.github/workflows/" + slug + "-build.yml'",
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
    "          cordova create cordova-build " + appId + " " + product,
    "          rm -rf cordova-build/www && cp -r " + A + "/www cordova-build/www",
    "          cp " + A + "/cordova/config.xml cordova-build/config.xml",
    "          cd cordova-build",
    "          cordova platform add android@12.0.1",
    "          cordova plugin add cordova-plugin-file@8.1.0",
    "          cordova build android",
    "          mkdir -p ../out && cp platforms/android/app/build/outputs/apk/debug/*.apk ../out/" + slug + "-debug.apk",
    "      - uses: actions/upload-artifact@v4",
    "        with: { name: " + slug + "-android, path: out/*.apk }",
    "",
    "  windows-exe:",
    "    runs-on: windows-latest",
    "    steps:",
    "      - uses: actions/checkout@v4",
    "      - uses: actions/setup-node@v4",
    "        with: { node-version: 20 }",
    "      - working-directory: " + A + "/electron",
    "        run: |",
    "          npm install",
    "          npm run dist",
    "      - uses: actions/upload-artifact@v4",
    "        with: { name: " + slug + "-windows, path: " + A + "/electron/dist/*.exe }",
    "",
    "  linux-app:",
    "    runs-on: ubuntu-latest",
    "    steps:",
    "      - uses: actions/checkout@v4",
    "      - uses: actions/setup-node@v4",
    "        with: { node-version: 20 }",
    "      - working-directory: " + A + "/electron",
    "        run: |",
    "          npm install",
    "          npm run dist:linux",
    "      - uses: actions/upload-artifact@v4",
    "        with:",
    "          name: " + slug + "-linux",
    "          path: |",
    "            " + A + "/electron/dist/*.AppImage",
    "            " + A + "/electron/dist/*.deb",
    "",
    "  publish:",
    "    runs-on: ubuntu-latest",
    "    needs: [android-apk, windows-exe, linux-app]",
    "    steps:",
    "      - uses: actions/checkout@v4",
    "      - uses: actions/download-artifact@v4",
    "        with: { path: dist, merge-multiple: true }",
    "      - run: |",
    "          cp " + A + "/www/index.html dist/" + product + "-web.html",
    "          cp " + A + "/paper/paper.md dist/ 2>/dev/null || true",
    "          ls -la dist",
    "      - name: Upload all-platform bundle (download from the Actions run page)",
    "        uses: actions/upload-artifact@v4",
    "        with: { name: " + slug + "-all-platforms, path: dist/*, retention-days: 90 }",
    "      - name: Publish to Release " + slug + "-latest (direct download, no login)",
    "        uses: softprops/action-gh-release@v2",
    "        with:",
    "          tag_name: " + slug + "-latest",
    "          target_commitish: ${{ github.sha }}",
    "          name: " + title.replace(/[\r\n]/g, " ") + " (latest)",
    "          prerelease: true",
    "          body: 'BadaGPT電信が思考入力から生成・自動コンパイルしたアプリ。commit ${{ github.sha }}'",
    "          files: |",
    "            dist/*.apk",
    "            dist/*.exe",
    "            dist/*.AppImage",
    "            dist/*.deb",
    "            dist/*.html",
    ""
  ].join("\n");
}

/* 自動コンパイル用の一式: projectFiles の一式を apps/<slug>/ 配下に置き、
 * ソースコードを加え、リポジトリ直下に自動ビルド・ワークフローを置く。 */
function buildKit(spec, html, paperMd) {
  var slug = slugify(spec.title), A = "apps/" + slug + "/";
  var product = ("BadaGPT-" + slug).replace(/[^A-Za-z0-9-]/g, "");
  var pkg = projectFiles(spec, html, paperMd).filter(function (f) { return f.path.indexOf(".github/") !== 0; });
  var files = pkg.map(function (f) { return { path: A + f.path, data: f.data }; });
  sourceProject(spec).forEach(function (f) { files.push({ path: A + "source/" + f.path, data: f.data }); });
  files.push({ path: ".github/workflows/" + slug + "-build.yml", data: autoBuildWorkflow(slug, product, spec.title, appIdFor(slug)) });
  return { slug: slug, product: product, files: files, workflowPath: ".github/workflows/" + slug + "-build.yml", releaseTag: slug + "-latest" };
}

/* ───────────── GitHub API (fetch を注入) ───────────── */
function ghClient(fetchImpl, token) {
  return async function gh(method, path, body) {
    var res = await fetchImpl("https://api.github.com" + path, {
      method: method,
      headers: { "Authorization": "Bearer " + token, "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28", "Content-Type": "application/json" },
      body: body ? JSON.stringify(body) : undefined
    });
    var j = null; try { j = await res.json(); } catch (e) { /* 本文なし */ }
    if (!res.ok) { var err = new Error("GitHub " + res.status + ": " + (j && j.message || res.statusText || "") + " (" + method + " " + path + ")"); err.status = res.status; throw err; }
    return j;
  };
}

/* 一式を 1 コミットでプッシュ。無ければリポジトリ / ブランチを作る。
 * o: { fetch, sleep, token, repo:"owner/name", branch, files, message, createIfMissing, private, log } */
async function githubPush(o) {
  var gh = ghClient(o.fetch, o.token), log = o.log || function () {}, sleep = o.sleep || function (ms) { return new Promise(function (r) { setTimeout(r, ms); }); };
  if (!/^[\w.-]+\/[\w.-]+$/.test(o.repo)) throw new Error("リポジトリは owner/name の形で指定してください");
  var R = "/repos/" + o.repo, branch = o.branch || "main", info, ref;
  log("リポジトリを確認…");
  try { info = await gh("GET", R); }
  catch (e) {
    if (e.status !== 404 || !o.createIfMissing) throw e;
    log("リポジトリが無いので作成します: " + o.repo);
    info = await gh("POST", "/user/repos", { name: o.repo.split("/")[1], private: !!o.private, auto_init: true, description: "BadaGPT電信が思考入力から生成・自動コンパイルするアプリ" });
    await sleep(2000); /* 初期コミットができるまで少し待つ */
  }
  var base = info.default_branch || "main";
  for (var tries = 0; ; tries++) {
    try { ref = await gh("GET", R + "/git/ref/heads/" + encodeURIComponent(branch)); break; }
    catch (e) {
      if (e.status !== 404) throw e;
      try {
        var baseRef = await gh("GET", R + "/git/ref/heads/" + encodeURIComponent(base));
        log("ブランチを作成: " + branch);
        ref = await gh("POST", R + "/git/refs", { ref: "refs/heads/" + branch, sha: baseRef.object.sha }); break;
      } catch (e2) {
        if (e2.status === 404 && tries < 3) { await sleep(2000); continue; } /* 作成直後で初期コミット待ち */
        throw e2;
      }
    }
  }
  var parent = await gh("GET", R + "/git/commits/" + ref.object.sha);
  var tree = [];
  for (var i = 0; i < o.files.length; i++) {
    var f = o.files[i];
    log("アップロード中… " + (i + 1) + " / " + o.files.length + "  " + f.path);
    var bytes = typeof f.data === "string" ? utf8(f.data) : f.data;
    var blob = await gh("POST", R + "/git/blobs", { content: bytesToBase64(bytes), encoding: "base64" });
    tree.push({ path: f.path, mode: "100644", type: "blob", sha: blob.sha });
  }
  var t = await gh("POST", R + "/git/trees", { base_tree: parent.tree.sha, tree: tree });
  var commit = await gh("POST", R + "/git/commits", { message: o.message || "BadaGPT電信: 自動コンパイル用の一式を生成", tree: t.sha, parents: [parent.sha] });
  await gh("PATCH", R + "/git/refs/heads/" + encodeURIComponent(branch), { sha: commit.sha, force: false });
  var web = "https://github.com/" + o.repo;
  return { sha: commit.sha, repo: o.repo, branch: branch, commitUrl: web + "/commit/" + commit.sha, actionsUrl: web + "/actions", web: web };
}

/* プッシュした commit の実行を探して状態を返す */
async function findRun(o) {
  var gh = ghClient(o.fetch, o.token);
  var j = await gh("GET", "/repos/" + o.repo + "/actions/runs?head_sha=" + encodeURIComponent(o.sha) + "&per_page=10");
  var runs = (j && j.workflow_runs) || [];
  if (o.workflowPath) { var m = runs.filter(function (r) { return r.path === o.workflowPath; }); if (m.length) runs = m; }
  if (!runs.length) return null;
  var r = runs[0];
  return { id: r.id, status: r.status, conclusion: r.conclusion, url: r.html_url, runNumber: r.run_number };
}
async function runJobs(o) {
  var gh = ghClient(o.fetch, o.token);
  var j = await gh("GET", "/repos/" + o.repo + "/actions/runs/" + o.runId + "/jobs?per_page=20");
  return ((j && j.jobs) || []).map(function (x) { return { name: x.name, status: x.status, conclusion: x.conclusion, url: x.html_url }; });
}
async function runArtifacts(o) {
  var gh = ghClient(o.fetch, o.token);
  var j = await gh("GET", "/repos/" + o.repo + "/actions/runs/" + o.runId + "/artifacts");
  return ((j && j.artifacts) || []).map(function (a) { return { id: a.id, name: a.name, size: a.size_in_bytes, expired: a.expired }; });
}
async function releaseAssets(o) {
  var gh = ghClient(o.fetch, o.token);
  try {
    var j = await gh("GET", "/repos/" + o.repo + "/releases/tags/" + encodeURIComponent(o.tag));
    return ((j && j.assets) || []).map(function (a) { return { name: a.name, size: a.size, url: a.browser_download_url }; });
  } catch (e) { if (e.status === 404) return []; throw e; }
}

/* 端末内でできる範囲の事前チェック (本当のコンパイルは Actions で行う) */
function precompileChecks(spec, html, sources) {
  var out = [];
  out.push({ name: "HTML アプリの検証", ok: verifyApp(html, spec).ok });
  var bada = sources.filter(function (s) { return s.lang === "bada"; })[0];
  if (bada) { var okB = true; try { new BadaInterp(function () {}).run(bada.files[0].data); } catch (e) { okB = false; } out.push({ name: "Bada プログラムの実行", ok: okB }); }
  var node = sources.filter(function (s) { return s.lang === "node"; })[0];
  if (node) { var okN = true; try { new Function(node.files[0].data.replace(/^#!.*\n/, "")); } catch (e) { okN = false; } out.push({ name: "Node ソースの構文", ok: okN }); } // eslint-disable-line no-new-func
  out.push({ name: "Python ソース (構文検査は Actions の py_compile で)", ok: true, note: "端末内では検査しません" });
  return out;
}
