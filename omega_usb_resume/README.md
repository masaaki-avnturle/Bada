# Ω-USB Resume — 死んだUSBポートを Bada 言語で蘇生する

PC の USB コネクターが

- **許可なく**（カーネルが `authorized = 0` で拒否している）
- **プラグプレイ機能なく**（ドライバが再バインドされずホットプラグが発火しない）
- **接触不良**（チャタリングで制御転送の記述子バイトが化ける）

で使えなくなった状態を、**物理的な修理なしに** ソフト側から復旧（レジューム）する
アプリケーションです。**Bada 言語**で記述し、Bada フレームワークの
**複素回転体・特殊相対性理論のコマ幾何・可積分系**エラー訂正
（`Bada::ErrorCorrection`）をそのまま使います。

```
接触不良 = 機械語バイト列の "n進数のズレ"
     │  複素回転体 e^{iθ} の閉軌道で平均（可積分系のコマ幾何 → 大きさ保存）
     ▼
n進数のズレを訂正 → エントロピー不変量 Ξ が保存（= 復旧が正しい証明）
     │  authorize(0→1) → power/control=on → unbind→bind（プラグプレイ再列挙）
     ▼
デバイス RESUMED
```

---

## ⚠ 重要 — シミュレーション既定・非破壊

- 既定では**すべてシミュレーション**です（`/sys` には一切書き込みません）。
  CI・コンテナ・Mac/Windows でもそのまま動きます。
- Linux 実機で root 権限がある場合のみ `--apply` を付けると、選択した
  デバイスの実 sysfs（`authorized` / `power/control` / ドライバの
  `unbind`・`bind`）に同じ手順を書き込みます。**書けない場合は警告して
  シミュレーションに留まり、壊しません。**
- 記述子バイトの `n進数のズレ` はドライバの制御転送リトライを数理化した
  ものです。実際に効くのは「再認可・電源復帰・再列挙」であり、断線した
  ケーブルやもげた端子など**真の物理故障は直せません**（その場合は正直に
  `NOT resumed ⚠` を返します）。

---

## 使い方

Bada/Ruby ランタイム（外部依存なし・Ruby 3.0+）から動きます。

```bash
# アプリのラッパー（このフォルダ）
./usb_resume            # スキャン＋不良ポートを全部レジューム（simulation）
./usb_resume scan       # USB デバイス一覧だけ
./usb_resume --apply    # Linux/root で実 sysfs に反映
./usb_resume --base 8   # ズレを 8 進数でモデル化（既定 16）
./usb_resume --device 2-3   # 指定 id のデバイスだけ

# Bada 言語スクリプトとして（演算子代数で記述したもの）
cd ../bada_ruby
bin/bada run examples/usb_resume.bada
bin/bada usb            # 同じ復旧を実エンジンで実行
```

出力例（不良ポート `2-3`）:

```
── USB Mass Storage (faulted port)  (0x0781:0x5581  bus 2  id 2-3)
   ✓ measure          port state = UNAUTHORIZED
   ✓ n進数補正         base-16 digit drift: 10→0 bit errors, 18/18 bytes recovered in 17 reads, checksum OK
   ✓ 可積分認証         Ξ=0.948928 conserved=true residual=0.00e+00
   ✓ authorize        simulated
   ✓ power/control=on simulated
   ✓ rebind (plug&play) simulated
   ✓ verify           port state = RESUMED
   → RESUMED ✅  (UNAUTHORIZED → RESUMED)   [simulation]
```

---

## 📦 ダウンロード — Windows 10/11 EXE ＆ Android APK

GUI 版（同じ復旧を可視化・アニメーションするアプリ）を **Windows の EXE** と
**Android の APK** として配布します。中身は `www/index.html`（Bada エンジンの
JavaScript 移植）で、Electron が Windows 実行ファイルに、Cordova が Android
パッケージに包みます。

| プラットフォーム | 形式 | ビルド元 |
|:--|:--|:--|
| **Windows 10 / 11** | `.exe`（NSIS インストーラ + portable） | `electron/`（`npm run dist`） |
| **Android** | `.apk`（debug） | `cordova/config.xml` + `www/` |

### 入手方法（3 通り）

**① いますぐ・ビルド不要 — 単一 HTML をそのままダウンロード**
GUI は完全に自己完結した 1 ファイル（外部依存なし）です。GitHub 上で
[`omega_usb_resume/www/index.html`](www/index.html) を開き **「Download raw file」**
で保存 → そのままブラウザ（Windows / Android / どれでも）で開けば動くオフライン
アプリになります。インストール不要。

**② GitHub Actions アーティファクト（ネイティブ EXE / APK・ビルド環境不要）**
リポジトリの **Actions → 「Ω apps build (APK + Windows EXE)」→ Run workflow**
（`Use workflow from` にこのブランチを選択）。完了後、成果物
`omega_usb_resume-windows`（EXE）と `omega_usb_resume-android`（APK）を
ダウンロードできます。

**③ GitHub Release（恒久リンクで EXE + APK を公開）**
バージョンタグを push すると、専用ワークフロー `build-usb-resume.yml` が EXE と
APK を付けた Release を自動作成します（Releases ページから誰でもダウンロード可）。

   ```bash
   git push origin usb-resume-v1.0.0    # ← タグは用意済み。これで Release 発行
   ```

   ※ ③ は既定ブランチにワークフローが必要です。このブランチを `main` に取り込むか、
   `git tag` を push できる環境から実行してください（自動セッションはタグを push
   できないため、この 1 手だけ手元で実行が必要です）。

### 自分でビルドする

```bash
# Windows EXE (要 Windows + Node 20)
cd omega_usb_resume/electron
npm install
npm run dist          # dist/Omega-USB-Resume-1.0.0-x64.exe

# Android APK (要 JDK17 + Android SDK + Cordova 12)
npm install -g cordova@12.0.0
cordova create build com.bada.omega TmpApp
cp -r omega_usb_resume/www build/www
cp omega_usb_resume/cordova/config.xml build/config.xml
cd build && cordova platform add android@12.0.1 && cordova build android
```

> APK/EXE の GUI はホスト/端末の**実 USB には触れません**（表示・数理シミュレーション）。
> 実機の再認可・再列挙は Linux 版 CLI `bin/bada usb --apply` が行います。

---

## 中身

| ファイル | 役割 |
|:--|:--|
| `../bada_ruby/lib/bada/usb_resume.rb` | 中核エンジン `Bada::UsbResume`：デバイス列挙 / n進数ズレ模型・訂正 / 復旧ステートマシン |
| `../bada_ruby/examples/usb_resume.bada` | **Bada 言語**による記述（`<- / -< / >- / Ω::push`） |
| `../bada_ruby/bin/bada usb` | CLI サブコマンド |
| `../bada_ruby/test/test_usb_resume.rb` | テスト（9 件） |
| `./usb_resume` | このフォルダから直接動かすラッパー（CLI） |
| `www/index.html` | GUI（Bada エンジンの JavaScript 移植・EXE/APK 共通の画面） |
| `electron/` | Windows 10/11 EXE 化（Electron） |
| `cordova/config.xml` | Android APK 化（Cordova） |

### 復旧アルゴリズム（`Bada::UsbResume`）

1. **測定** — ポート状態（`UNAUTHORIZED` / `UNBOUND` / `SUSPENDED`）を読む。
2. **n進数補正** — 接触不良で化けた記述子を、同じ記述子の複数読み取り（制御転送
   リトライ）として扱う。各バイトを **base-n の桁に分解し、桁ごとに独立して**
   複素回転体 `e^{iθ}` 上で `ErrorCorrection.correct`（相対論的な外れ値減衰＝コマの
   歳差）の閉軌道平均を取り、真の桁へ収束させて再合成する（＝機械語の n進数のズレを
   直接直す）。base-n チェックサムが通るまでリトライ数を自動増加。桁単位なので
   二進〜十六進のどの基数でも完全復元します。
3. **可積分認証** — 復元後のエントロピー不変量 Ξ が回転軌道上で保存されることを
   `certify_invariant` で確認（可積分系の保存則＝復旧の証明）。
4. **レジューム** — `authorized`→1、`power/control`→on、ドライバ `unbind`→`bind`
   でプラグプレイ再列挙。
5. **記録** — 対話を `Ω::DATABASE`（アカシックレコード）へ push。

---

*© 2025 Masaaki Yamaguchi · 山口 雅旭 · Bada / TupleSpace framework*
