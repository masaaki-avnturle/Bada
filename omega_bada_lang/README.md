# Ω-Bada Studio — Bada 言語 コンパイラ＋インタープリタ（＋量子）

今までの集大成として、**Bada 言語**を字句解析→構文解析→AST→**インタープリタ**と
**バイトコード・コンパイラ＋スタックVM**の両方で実装し、さらに**量子バックエンド**
（状態ベクトルシミュレータ＋OpenQASM 2.0 生成）を載せた統合実装です。1 つの
エンジン（`www/bada.js`・純粋・外部依存なし）が **ブラウザ / Node / Windows /
Ubuntu / Android** で同じように動きます。

```
ソース → Lexer → Parser → AST ┬─▶ Interpreter (tree-walk)        ─┐
                              └─▶ Compiler → Bytecode → Stack VM ─┴▶ 出力（両者一致を検証）
                                        └─▶ Quantum lib → OpenQASM 2.0 + 状態ベクトル
```

## 言語仕様（Bada v4）

```bada
# 変数・算術・文字列
set a = 2 + 3 * 4
print "a = " + a

# 制御構文と関数（再帰）
fn fact(n) {
  if n <= 1 { return 1 }
  return n * fact(n - 1)
}
print fact(10)

while a > 0 { a = a - 1 }

# Bada 多様体演算子（山口フレームワーク）
set g = 2.5
g <- "global differential manifold"   # 左作用  π(χ,x)=π·|χ|·ln(x+1)
g -< 3                                 # 多様体積分 ∬1/(x log x)²
g >- g                                 # 量子右作用 e^{-x log x}
Omega::push g as node1                 # アカシック TupleSpace へ記録

# 組み込み: sqrt log exp sin cos pow min max floor round len str
#           gamma beta xi entropy zeta xlogx  （山口フレームワークの特殊関数）

# 量子標準ライブラリ（「量子コンピューターの Bada 言語」）
set q = qreg(2)      # 2 量子ビット
h(q, 0)              # アダマール
cnot(q, 0, 1)        # CNOT → Bell もつれ
print probs(q)       # |00>=0.5, |11>=0.5
measure(q)           # 測定（回路は OpenQASM に落とせる）
```

| 演算子 / 構文 | 意味 |
|:--|:--|
| `set x = e` / `x = e` | 代入 |
| `print e` | 出力 |
| `if e { } else { }` / `while e { }` | 制御構文 |
| `fn f(a,b){ … return e }` | 関数（再帰可） |
| `<-` `-<` `>-` | Bada 多様体演算子（π作用 / 多様体積分 / 量子右作用） |
| `Ω::push e as name` | アカシック TupleSpace へ記録 |
| `qreg H X Z RY CNOT measure probs prob` | 量子標準ライブラリ |

## 使い方

### GUI（Ω-Bada Studio）
`www/index.html` を開くと IDE が起動します（EXE/APK/AppImage/deb にも同梱）。
- **▶ Interpret** … tree-walk インタープリタで実行
- **⚙ Compile + VM** … バイトコードにコンパイル→VM 実行（逆アセンブルを表示）
- **⚛ Quantum** … 量子命令を OpenQASM 2.0 回路に落とし、状態（確率）を表示
- ヘッダに **インタープリタと VM の出力一致**（✓ interp==VM）を常時検証表示

### CLI（Ubuntu/Linux, Node 18+）
```bash
./bada run  prog.bada     # インタープリタ実行
./bada vm   prog.bada     # バイトコードにコンパイル→VM 実行
./bada dis  prog.bada     # バイトコード（逆アセンブル）表示
./bada qasm prog.bada     # 量子回路 OpenQASM 2.0 を出力
./bada check prog.bada    # インタープリタと VM の一致を検証
echo 'print 2+2' | ./bada run -
```

### テスト
```bash
node test_bada.js         # 34 件（interp==VM 差分テスト・量子・コンパイラ・エラー）
```

## 📦 ダウンロード — Windows 10/11・Ubuntu/Linux・Android 12

GUI 版を各プラットフォームのネイティブアプリとして配布します（中身は同じ `www/`）。

| プラットフォーム | 形態 | 形式 | ビルド元 |
|:--|:--|:--|:--|
| **Windows 10 / 11** | GUI（IDE） | `.exe`（NSIS インストーラ + portable） | `electron/`（`npm run dist`） |
| **Ubuntu / Linux** | **CLI（コンパイラ/インタープリタ）** | `bada-cli-linux-x64`（単体実行）+ `bada-cli_*_amd64.deb`（`sudo dpkg -i` → `/usr/bin/bada`） | `cli/build-linux-cli.sh`（Node SEA） |
| **Android 12+** | GUI（IDE） | `.apk`（minSdk 24 / target 33） | `cordova/config.xml` + `www/` |

> **Ubuntu は GUI ではなく CLI** です。`bada-cli-linux-x64` は Node を含む**単体実行
> ファイル**（依存なし）で、`bada run|vm|dis|qasm|check` がそのまま使えます。
> `.deb` を入れると `bada` コマンドが `/usr/bin` に入ります。

### 入手方法

1. **GitHub Release（恒久リンク・推奨）** — バージョンごとに Windows EXE・Ubuntu
   AppImage/deb・Android APK を添付した Release
   **`bada-lang-latest`** を公開します。リポジトリの **Releases** ページから
   直接ダウンロードできます。
2. **GitHub Actions アーティファクト** — **Actions → 「Ω apps build (APK + Windows
   EXE)」→ Run workflow**（このブランチを選択）。完了後、成果物
   `omega_bada_lang-windows` / `omega_bada_lang-linux` / `omega_bada_lang-android`
   をダウンロード。
3. **単一ファイル（ビルド不要）** — `www/index.html` と `www/bada.js` を保存すれば
   ブラウザだけで IDE が動きます。

各プラットフォームでの起動:
- **Windows**: `.exe` を実行（インストーラ or portable）→ IDE。
- **Ubuntu（CLI）**:
  ```bash
  chmod +x bada-cli-linux-x64
  ./bada-cli-linux-x64 run  prog.bada     # インタープリタ
  ./bada-cli-linux-x64 vm   prog.bada     # コンパイル→VM
  ./bada-cli-linux-x64 qasm prog.bada     # 量子回路 OpenQASM
  # または deb をインストール:
  sudo dpkg -i bada-cli_1.0.0_amd64.deb   # → bada コマンド
  bada check prog.bada
  ```
- **Android 12+**: `.apk` をインストール（提供元不明のアプリを許可）→ IDE。

---

## ⚠ 注意 — 量子はシミュレータ

「量子」は**状態ベクトルのシミュレータ**（最大 12 量子ビット）で、実機の量子
コンピュータではありません。生成される OpenQASM 2.0 は実機/他シミュレータへの
橋渡しに使えますが、本アプリ内の実行は古典計算による厳密シミュレーションです。

## 中身

| ファイル | 役割 |
|:--|:--|
| `www/bada.js` | 言語エンジン：Lexer / Parser / AST / **Interpreter** / **Compiler+VM** / 量子ランタイム / OpenQASM |
| `www/index.html` | IDE（GUI・EXE/APK/AppImage/deb 共通の画面） |
| `bada` | CLI ランナー（run / vm / dis / qasm / check） |
| `test_bada.js` | テスト（34 件・interp==VM 差分テスト含む） |
| `electron/` | Windows EXE ＋ Ubuntu AppImage/deb 化（Electron） |
| `cordova/config.xml` | Android 12+ APK 化（Cordova） |

*© 2025 Masaaki Yamaguchi · 山口 雅旭 · Bada / TupleSpace framework · omega_bada_lang*
