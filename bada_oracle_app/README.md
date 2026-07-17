# Bada Oracle — `bada_oracle_app/` (Android) + `bada_oracle_desktop/` (Windows)

Bada / Omega の「Akashic」モチーフに沿った **手続き的な託宣（オラクル）ジェネレーター**。
ガンマ関数と熱エントロピーで駆動する決定論的ハッシュで詩的フラグメントを合成し、
バイオフィードバックの柔らかいチャイム音とともに提示します。

> ## ⚠️ 重要な免責事項 / Disclaimer
> **これはアカシックレコードへのアクセスでも、未来の予知でもありません。**
> 出力は乱数的に合成された **娯楽・内省用の生成アート** です。健康・お金・進路・
> 人間関係など、実生活の重要な判断の根拠には**使わないでください**。
> 「対象者が未来の情報を受信する」ような本物の予知機能は、技術的に存在せず、
> 本アプリも提供しません。

---

## 2つの配布形態

| プラットフォーム | 形式 | ソース |
|:--|:--|:--|
| Android | **APK** (Jetpack Compose) | `bada_oracle_app/` |
| Windows 10 / 11 | **.exe** (Python + Tkinter, PyInstaller `--onefile`) | `bada_oracle_desktop/` |

どちらも同じ生成エンジン（ガンマ関数 Lanczos 近似 + Shannon エントロピー +
splitmix 系ハッシュ）を各言語で実装しています。

---

## ダウンロード（GitHub Release）

GitHub Actions の `Build Bada Oracle (APK + Windows EXE)` が両方をビルドします。

- **タグを push**（例 `oracle-v1`）するか、Actions から **手動実行 (workflow_dispatch)** すると、
  APK と EXE が **Release の添付ファイル**として公開され、リポジトリからダウンロードできます。
- 各 push 後の成果物(artifact)としても `bada-oracle-apk` / `bada-oracle-exe` からダウンロード可能です。

```bash
# 例: ダウンロード可能なリリースを切る
git tag oracle-v1
git push origin oracle-v1
```

---

## エンジン概要

- Android: `app/src/main/java/com/bada/oracle/OracleEngine.kt`, `MainActivity.kt`,
  フラグメント `app/src/main/assets/oracle/fragments.json`
- Windows: `bada_oracle_desktop/bada_oracle.py`（フラグメント同梱）

`generate(question, nonce)` は、入力文字列とユーザー操作由来の nonce（タップ回数など）から
決定論的に言葉を選びます。**同じ入力・同じ操作なら同じ結果**＝乱数的アートであって、
外部の未来情報を参照していないことを示します。

---

## ローカルビルド

Android:
```bash
cd bada_oracle_app && gradle assembleDebug   # JDK17 / Gradle 8.7 / Android SDK 34
```
Windows EXE（Windows 上で）:
```bat
cd bada_oracle_desktop
pip install -r requirements.txt
pyinstaller --onefile --windowed --name BadaOracle bada_oracle.py
```

---

© Masaaki Yamaguchi · 山口雅旭 · Bada Language
