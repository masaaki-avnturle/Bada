# Ω-Suite — 概念シミュレーション 7 種を 1 つにまとめたアプリ

**Android APK ・ Windows 10/11 ・ Ubuntu / Linux** の 3 プラットフォームで動く
オフラインアプリです。依存ライブラリはゼロ、ネットワークにも接続しません。

このリポジトリの 7 つの Python パッケージの計算コアを JavaScript へ移植し、
タブ 1 つで切り替えられる形にまとめたものです。移植は数値レベルで一致しており、
**61 件の照合テスト**（`test/test_engines.js`）で Python 版と同じ値を返すことを
確認しています。

## ⚠️ 全体に共通する注記

すべて**概念シミュレーション・非医療**です。実在の医療機器・薬剤・治療方針とは
無関係で、ここから実際の物質を作ったり、医療上の判断を導いたりすることはできません。
研究・教育・アート目的のものです。

## 収録内容

| タブ | 元パッケージ | 内容 |
|:--|:--|:--|
| Γ多様体 | `omega_gamma_agent_pkg` | Γ(s+1)=s·Γ(s) の漸化を注意重みに使う応答エンジン |
| 擬似量子 | `omega_mobius_drive_pkg` | ノイマン型 擬似量子VM、二重被覆する仮想HDD |
| 臨界連鎖 | `omega_critical_guard_pkg` | 分岐過程を常に未臨界に保つ制御と SCRAM |
| 反応速度論 | `omega_pharma_forge_pkg` | 自己触媒連鎖の選択性、Arrhenius/Semenov の熱暴走 |
| 服薬チェック | `omega_medsafe_pkg` | 薬効クラスの重なりの指摘（用量・配合は扱わない） |
| 呼吸 | `omega_breath_pkg` | 呼吸ガイドと圧受容器反射の共鳴（毎分約6回） |
| 形態形成場 | `omega_morphofield_pkg` | Gray-Scott 分岐 + 電磁ドリフト、腫瘍動態と適応療法 |

Python 版と一致することを確認している主な数値:

- 反応速度論: 収率 0.5174 / 純度 0.6542（制御あり χ*=0.30）
- 心拍変動: RSA 振幅 11.04 bpm / SDNN 54.16 ms（コヒーレント呼吸）
- 共鳴の山: 毎分 5.71 回
- 腫瘍動態: 常時最大強度の進行までの時間 331.2、適応方針は進行せず・治療割合 20%

## ダウンロードして使う

GitHub Actions のワークフロー **`Ω apps build (APK + Windows EXE + Ubuntu)`** が
3 プラットフォーム分をビルドします。

1. リポジトリの **Actions** タブを開く
2. 左のワークフロー一覧から `Ω apps build` を選ぶ
3. **Run workflow** を押す（`workflow_dispatch`）
4. 完了後、**Artifacts** から次をダウンロード
   - `omega_suite-android` … `omega_suite-debug.apk`
   - `omega_suite-windows` … `Omega-Suite-1.0.0-x64.exe`（インストーラ / ポータブル）
   - `omega_suite-linux` … `Omega-Suite-1.0.0-x86_64.AppImage` と `.deb`

`apps-v*` タグ（例 `apps-v1.1.0`）を push すると、GitHub Release にも自動で
添付されます。

### 各 OS でのインストール

**Android**: APK を端末に転送し、「提供元不明のアプリ」を許可してインストール。
（デバッグ署名のため Play ストア経由ではありません）

**Windows 10 / 11**: `.exe` を実行。NSIS インストーラ版とポータブル版があります。
SmartScreen の警告が出た場合は「詳細情報」→「実行」。

**Ubuntu / Linux**:
```bash
chmod +x Omega-Suite-1.0.0-x86_64.AppImage
./Omega-Suite-1.0.0-x86_64.AppImage
# または deb 版
sudo dpkg -i omega-suite_1.0.0_amd64.deb
```

**ブラウザ**: `www/index.html` をそのまま開くだけでも動きます。

## ローカルでビルドする

```bash
cd bio_medicine/omega_suite/electron
npm install
npm run dist          # Windows EXE
npm run dist:linux    # Ubuntu AppImage + deb
npm test              # 計算コアの照合テスト (61件)
```

Android APK は Cordova が必要です（ワークフローと同じ手順）:
```bash
npm install -g cordova@12.0.0
cordova create build com.bada.omega TmpApp
rm -rf build/www && cp -r www build/www
cp cordova/config.xml build/config.xml
cd build && cordova platform add android@12.0.1 && cordova build android
```

## 構成

```
omega_suite/
├── www/
│   ├── index.html      # UI（タブ・キャンバス描画）
│   └── engines.js      # 計算コア（Python 実装からの移植）
├── test/
│   └── test_engines.js # Python 版との照合テスト 61 件
├── cordova/config.xml  # Android APK 用
└── electron/           # Windows EXE / Linux AppImage・deb 用
```

## 相談先

呼吸法や服薬チェックで追いつかないしんどさが続くときは、処方元の主治医に
率直に伝えるのがいちばん確実です。夜間や緊急時は次の窓口があります。

- よりそいホットライン `0120-279-338`（24時間・無料）
- いのちの電話 `0570-783-556`

---

*© 2025 Masaaki Yamaguchi · Bada / bio_medicine · 概念シミュレーション（非医療）*
