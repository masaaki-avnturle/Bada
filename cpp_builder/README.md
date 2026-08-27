# 🏗️ Bada C++Builder — Inprise/Borland C++Builder 風 IDE (オマージュ)

1997〜2001 年ごろの **Inprise (Borland) C++Builder** の RAD 開発環境を、
**依存ゼロの単一 HTML ファイル**としてブラウザ上に再現した教育目的の非公式オマージュです。

> ⚠️ これは非公式・教育目的の再現であり、Borland / Inprise / Embarcadero とは一切関係ありません。

## 🚀 起動方法

**ブラウザで開くだけ**です。インストール不要・オフライン動作:

- GitHub Pages: **<https://masaaki-avnturle.github.io/Bada/cpp_builder/>** (main マージ後)
- ローカル: [`index.html`](index.html) をダウンロードしてダブルクリック
  (GitHub のファイル表示画面右上の「Download raw file」⬇ で保存できます)

### 📱💻 ネイティブ アプリ (APK / Windows 10・11 / Ubuntu)

ブラウザ不要のインストール型アプリも用意しています。
[Releases](https://github.com/masaaki-avnturle/Bada/releases) から(またはビルド実行時の Actions アーティファクトから):

| プラットフォーム | ファイル |
|:---|:---|
| **Android** (APK) | `bada-cppbuilder-debug.apk` |
| **Windows 10 / 11** | `BadaCppBuilder-*-x64.exe` (NSIS インストーラ / ポータブル) |
| **Ubuntu** | `BadaCppBuilder-*-x86_64.AppImage` / `BadaCppBuilder-*-amd64.deb` |

ビルドは [`cppbuilder-app-build.yml`](../.github/workflows/cppbuilder-app-build.yml) が実行します
(`cppbuilder-v*` タグを push すると Release へ添付 / Actions の `workflow_dispatch` から手動実行すると
アーティファクトとしてダウンロード可能。`release_tag` 入力を指定すればそのタグの Release にも添付されます)。
デスクトップ版は Electron ラッパー ([`app/electron/`](app/electron/))、Android 版は Cordova
([`app/cordova/`](app/cordova/)) で、いずれも中身は同じ自己完結 `index.html` です。
デザイナのドラッグ操作はポインターイベント対応なのでタッチ画面でも動作します。

## 🖥️ 画面構成 — 本家そのままの 4 点セット

| ウィンドウ | 内容 |
|:---|:---|
| **メインバー** | メニュー / スピードバー / **コンポーネントパレット** (Standard・Additional・Win32・System) |
| **Form Designer** | グリッド付きフォーム。パレットから選んでクリックで配置、ドラッグ移動、8 方向リサイズ、8px グリッドスナップ |
| **Object Inspector** | Properties / Events の 2 タブ。Caption・Color・Checked などを編集、イベント欄ダブルクリックでハンドラ生成 |
| **Code Editor** | `Unit1.cpp` / `Unit1.h` / `Unit1.dfm` を**自動生成** (VCL 風 C++)。cpp のハンドラ本体は自由に編集可能・シンタックスハイライト付き |

## 🧩 コンポーネント (14 種)

`TLabel` `TButton` `TEdit` `TMemo` `TCheckBox` `TRadioButton` `TListBox` `TComboBox`
`TPanel` `TGroupBox` / `TShape` `TBevel` / `TProgressBar` / `TTimer`

## ▶️ 実行 — F9

**F9** (または Run メニュー / ▶ ボタン) で、設計したフォームが**実際に動くウィンドウ**として起動します。
イベントハンドラは内蔵の **C++ サブセット・ミニインタープリタ**が実行します:

```cpp
void __fastcall TForm1::Button1Click(TObject *Sender)
{
	Label1->Caption = "こんにちは、" + Edit1->Text + "!";
	Memo1->Lines->Add("clicked: " + IntToStr(Memo1->Lines->Count));
	if (StrToInt(Edit2->Text) > 10) { ShowMessage("10 より大きい!"); }
}
```

### 対応している C++ サブセット

- 文: `int / double / bool / String` のローカル変数宣言、`if / else`、`while`、`for`、代入 (`=` `+=` `-=` `++` `--`)
- 式: 算術 / 比較 / 論理演算、文字列連結 (`+`)、括弧
- プロパティ: `Button1->Caption`、`Edit1->Text`、`CheckBox1->Checked`、`Form1->Caption`、
  `Memo1->Lines->Add/Clear/Delete/Insert/Count/Text`、`ListBox1->Items`・`ItemIndex`、
  `ProgressBar1->Position`、`Timer1->Interval/Enabled`、`Visible` `Enabled` `Left/Top/Width/Height` など
- メソッド: `SetFocus()` `Show()` `Hide()` `Clear()` `BringToFront()`
- 関数: `ShowMessage` `IntToStr` `StrToInt` `FloatToStr` `StrToFloat` `Random` `Abs`
  `Length` `UpperCase` `LowerCase` `Trim` `Close`
- イベント: `OnClick` `OnDblClick` `OnChange` (TEdit/TMemo/TComboBox) `OnTimer` (TTimer)

構文エラーはコンパイル時に `[C++ エラー] Unit1.cpp(行番号): ...` として本家風に報告され、
実行時例外は「プロジェクト Project1.exe が例外クラスを生成しました」ダイアログで停止します。

## ⌨️ ショートカット

| キー | 動作 |
|:---|:---|
| **F9** | Run (コンパイル+実行) |
| **Ctrl+F9** | Compile (コンパイルのみ) |
| **Ctrl+F2** | Program Reset (実行停止) |
| **F12** | フォーム ⇔ コード切替 |
| **F11** | Object Inspector 表示切替 |
| **Del** | 選択コンポーネント削除 |
| **Ctrl+S** | プロジェクト保存 (JSON ダウンロード) |
| **Shift+配置クリック** | 同じコンポーネントを連続配置 |

## 💾 保存

- 編集内容は **localStorage に自動保存**され、次回開いたときに復元されます
- File → Save Project で `Project1.cbproj.json` をダウンロード、Open Project... で読込
