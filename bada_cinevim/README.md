# 🎬 Bada CineVim — 映画カウントダウンの VIM エディタ

**量子プログラミング言語 Bada 用の、映画的な VIM エディタ。**
映画のカウントダウン場面に出てくるエディタのように、**画面内の文章がどアップにフォーカス**され、
**ポイントされた文章が浮き上がるクラッシュ効果**とともに秒読みが進みます。

依存ゼロ・単一 HTML・オフライン動作。`index.html` をダブルクリックするだけで起動します。

---

## ⬇️ ダウンロード

### インストール不要 (単一 HTML)

👉 [**bada_cinevim/index.html をダウンロード**](index.html) → 「Download raw file」(⬇) で保存 → ダブルクリック。

### ネイティブ アプリ — ⚙️ Actions からダウンロード

**👉 [Actions › Bada CineVim app build](https://github.com/masaaki-avnturle/Bada/actions/workflows/cinevim-app-build.yml)**

1. 上のリンクを開き、**一番上の緑チェック ✅ の実行**をクリック
2. ページ下部の **「Artifacts」** に 3 つ並んでいます
3. クリックすると **zip** で落ちてくるので、展開して中身を使います

| アーティファクト | 中身 | プラットフォーム | zip サイズ |
|:---|:---|:---|---:|
| **`cinevim-android`** | `bada-cinevim-debug.apk` | Android | 約 2.9 MB |
| **`cinevim-windows`** | `BadaCineVim-1.0.0-x64.exe`(NSIS インストーラ)<br>`BadaCineVim-1.0.0-portable.exe`(ポータブル) | Windows 10 / 11 | 約 149 MB |
| **`cinevim-linux`** | `BadaCineVim-1.0.0-x86_64.AppImage`<br>`BadaCineVim-1.0.0-amd64.deb` | Ubuntu | 約 173 MB |

> ✅ [**実行 #1**](https://github.com/masaaki-avnturle/Bada/actions/runs/35145305960) で
> 4 ジョブ (`test-core` / `android-apk` / `windows-exe` / `linux-app`) すべて成功し、
> 上記 3 アーティファクトの生成を確認済みです。

> **アーティファクトの保存期間は 90 日**です。期限が切れていたら、Actions のページで
> **「Re-run all jobs」** を押すか、下記の手動実行でビルドし直してください。

#### 各プラットフォームでの導入

```sh
# Android — 「提供元不明のアプリ」を許可してから APK を開く (デバッグ署名です)
adb install bada-cinevim-debug.apk

# Windows 10 / 11 — インストーラ、またはポータブル版をそのまま実行
#   SmartScreen が出たら「詳細情報」→「実行」(コード署名はしていません)
BadaCineVim-1.0.0-x64.exe

# Ubuntu — AppImage は実行権をつけるだけ
chmod +x BadaCineVim-1.0.0-x86_64.AppImage
./BadaCineVim-1.0.0-x86_64.AppImage
# もしくは deb でインストール
sudo apt install ./BadaCineVim-1.0.0-amd64.deb
```

#### ビルドの起動方法

ビルドは [`cinevim-app-build.yml`](../.github/workflows/cinevim-app-build.yml) が実行します。

| きっかけ | 成果物の置き場所 |
|:---|:---|
| `bada_cinevim/` を含むブランチへの **push** | Actions の **Artifacts**(自動) |
| Actions ページの **「Run workflow」**(`workflow_dispatch`) | Actions の **Artifacts**(手動)※ボタンはデフォルトブランチ上の workflow にのみ表示 |
| **`cinevim-v*` タグ**の push | Actions の Artifacts + [**Releases**](https://github.com/masaaki-avnturle/Bada/releases) に添付 |

3 つのジョブは共通の `test-core`(エンジン単体テスト 228 件)に依存しているため、
**テストが落ちると APK も EXE も AppImage も作られません**。

---

## 🎥 三つの映画的演出

### 1. どアップ フォーカス (被写界深度)

カーソル行 — **ポイントされた文章** — が最大 **2.6 倍**に拡大され、離れた行ほど
ガウス核 `k = exp(-d²/2σ²)` で **縮小・ぼかし・減光**されます。映画のレンズが
一行だけにピントを合わせ、前後がボケて流れる、あの画です。

| コマンド | 効果 |
|:---|:---|
| `:focus` | どアップの ON / OFF |
| `:set peak=3.2` | 最大倍率 (既定 2.6) |
| `:set spread=1.4` | 焦点の狭さ = 被写界深度の浅さ (既定 2.2) |
| `:set maxBlur=5` | 背景のぼかし量 (既定 3.2) |
| `:set depth=0.5` | 演出全体の強さ 0〜1 |

拡大した行が重ならないよう、行の占有高さは `baseH × scale` で再計算され、
カーソル行の中心が常に画面中央に来るようドキュメント全体が追従します。

### 2. クラッシュ効果 (浮き上がり)

**`Space`** を押す、行をタップする、`:slam` を撃つ、あるいはカウントダウンが刻むたび、
ポイントされた行が **3D で浮き上がり** (`translateZ` + `translateY`)、同時に:

- 画面全体が **揺れる** (減衰振動 + わずかな傾き)
- 文字が **色収差で割れる** (マゼンタとシアンに分離)
- **衝撃波リング**が楕円で広がる
- **破片**が決定的な擬似乱数で飛散する
- **重低音**が鳴る (Web Audio で合成、音声ファイルなし)

浮上量は `lift = mag · 54 · sin(π · t^0.45)` — 立ち上がりが速く、ゆっくり着地します。

### 3. 映画のカウントダウン

`:countdown 5` または **⏱ カウントダウン** ボタンで、**アカデミー・リーダー**が起動します。
同心円・十字の走査線・掃引する指針・フィルムグレイン・縦キズつき。
**1 秒刻むたびにクラッシュが強くなり、T-0 で最大の衝撃**がポイント行に落ちます。

---

## ⌨ VIM キーバインド

本物のモーダル編集です。`:help` でアプリ内に全一覧が出ます。

### モード
`i` `a` `I` `A` `o` `O` 挿入 ・ `v` ビジュアル ・ `V` ビジュアル行 ・ `R` 置換 ・ `Esc` で戻る

### 移動
`h j k l` ・ `w W b B e E` ・ `0 ^ $` ・ `gg` `G` `42G` ・ `{ }` 段落 ・ `%` 対応括弧 ・
`f t F T` + `; ,` ・ `/pat` `?pat` `n` `N` ・ `Ctrl-D` `Ctrl-U` `Ctrl-F` `Ctrl-B`

### 編集
`x X` ・ `r{char}` ・ `d{motion}` `dd` `D` ・ `c{motion}` `cc` `C` ・ `y{motion}` `yy` `Y` ・
`p P` ・ `>> <<` ・ `J` ・ `~` ・ `3dd` `2dw` のようなカウント ・ `"a yy` 名前付きレジスタ ・
`u` `Ctrl-R` 取り消し/やり直し ・ `.` 直前の変更を繰り返し (挿入したテキストごと)

### Ex コマンド
`:w [name]` `:wq` `:q` `:q!` ・ `:e` 開く ・ `:42` 行ジャンプ ・
`:%s/pat/rep/g` `:3,9s/pat/rep/` ・ `:set number` `:set nonumber` `:set shiftwidth=4` ・
`:run` `:countdown 5` `:slam` `:focus` `:crash` `:demo` `:new` `:noh` `:help`

### 📱 タッチ操作 (APK / タブレット)
画面下にキーバーが出ます (`Esc` `i` `:` `hjkl` `dd` `yy` `p` `u` `💥` など)。
**⌨** ボタンでソフトキーボードを呼び出せます。行をタップするとそこへ焦点が移り、
同じ行をもう一度タップすると最大クラッシュが起きます。

---

## ⚛ 量子 Bada ランタイム

`:run` または **▶ 実行** でバッファを量子 Bada として実行します。
**状態ベクトルシミュレータ**(最大 14 量子ビット)を内蔵しています。

```bada
qubit q[3];

H q[0];              // 重ね合わせ  |0⟩ → (|0⟩+|1⟩)/√2
CNOT q[0], q[1];     // もつれ      → ベル状態 Φ+
X q[2];
RY q[2], 0.7;        // 回転ゲート (RX / RY / RZ)

let shot = measure q;   // 観測して collapse
print shot;

let zeta = 4.0 <- 2.0;  // 非可換左作用 π(χ,x)
let area = 2.0 -< 12.0; // 多様体積分 ∬1/(x·log x)²
let grad = 1.0 >- 0.5;  // 量子作用素右作用 ⊕(iℏ∇)^⊕L
print beta(2, 3);       // β(p,q) = Γ(p)Γ(q)/Γ(p+q)
```

実行後は終状態 |ψ⟩ の確率分布が出力パネルに並びます。

### 三つの非可換オペレータの数値意味論

| 演算子 | 数学的対応 | 実装 |
|:---|:---|:---|
| `<-` | `π(χ,x) = [iπ, f(x)]` | `a·cos(b) − b·sin(a)` — 交換子の実数表現 (非可換) |
| `-<` | `∬ 1/(x·log x)² dx` | 区間 `[a,b]` のシンプソン則による数値積分 (向きで符号反転) |
| `>-` | `⊕(iℏ∇)^⊕L` | `ℏ · (sin(a+b) − sin(a)) / b` — ℏ 倍の数値勾配 |

`Γ(s)` は Lanczos 近似、`β(p,q) = Γ(p)Γ(q)/Γ(p+q)`、`ζ(s) = β(p,q)/log x`。
ゲートは `H X Y Z S T` / `CNOT CZ SWAP` / `RX RY RZ`。
観測は種つき擬似乱数 (mulberry32) なので、同じ種なら結果が完全に再現します。

---

## 🧪 テスト

```sh
node bada_cinevim/tools/engine-test.js
```

`index.html` のインライン `<script>` を Node の `vm` で読み込み、**228 件**を検証します —
トークナイザ、Γ/β/ζ、三つのオペレータ、量子シミュレータ (ベル状態・ユニタリ性・collapse)、
式パーサの優先順位、プログラム実行、VIM のモーション・オペレータ・`.` リピート・
ビジュアル・Ex コマンド、そしてシネマ数理 (フォーカス減衰の単調性、行が重ならない
レイアウト、クラッシュ包絡の境界、カウントダウンの単調減少)。

---

## 📁 構成

```
bada_cinevim/
├── index.html              アプリ本体 (依存ゼロ・単一 HTML)
├── app/
│   ├── cordova/config.xml  Android APK のラッパー設定
│   └── electron/           Windows EXE / Ubuntu AppImage・deb のラッパー
└── tools/engine-test.js    エンジン単体テスト (Node)
```

アプリ本体は `index.html` ただ一つです。各プラットフォーム版は、この HTML を
`www/` として同梱するだけの薄いラッパーで、ロジックは完全に共有されています。
