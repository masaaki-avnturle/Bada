# Ω-Biofeedback Oracle — 生成的バイオフィードバック・サウンドアート

未知事前エンジン（Γ大域的部分積分多様体の LUT ファブリック）が、入力（意図テキスト・基音・
バイノーラル差）から**決定論的に音・映像・生成詩**を生み出す、瞑想向けの**サウンドアート作品**です。
Android **APK** と Windows 10/11 **EXE** を、あなたのリポジトリの **GitHub Actions** でビルドし、
**Releases からダウンロード**できます。

---

## ⚠⚠ 重要 — アート/娯楽・非医療・非予知

- 本アプリは**アカシックレコードにアクセスしません**。
- **未来を予知しません**。誰かに未来情報を送受信することもありません。
- 出力（音・マンダラ・リーディング詩）はすべてエンジンの**決定論的な生成物（アート）**です。
- **医療・健康・投資・意思決定には使用できません**。娯楽・瞑想目的でお楽しみください。

これは占い風の演出を持つ**生成アート／エンターテインメント**であり、本物の予知・霊的情報アクセスを
主張するものではありません。

## できること
- **共鳴再生**: バイノーラル風の2音＋倍音レイヤを Web Audio で生成。エンジン出力が倍音の抑揚を変調。
- **マンダラ可視化**: 8秒の呼吸ペーサに同期した花弁アニメーション。
- **生成リーディング**: 意図テキストを種に、語彙合成で詩を決定論生成（同じ種→同じ詩）。

## 動かす（ブラウザ）
```bash
cd www && python3 -m http.server 8000    # http://localhost:8000/
# または www/index.html を直接開く
```

## APK / EXE をダウンロードする（本物のビルド）

**偽のバイナリはリポジトリに置いていません。** 実際の APK/EXE は CI がビルドします。

1. GitHub の **Actions** タブ → 「Ω-Biofeedback build (APK + Windows EXE)」→ **Run workflow**（手動実行）。
   完了後、Actions の成果物（Artifacts）から `omega-biofeedback-android`(APK) と
   `omega-biofeedback-windows`(EXE) をダウンロードできます。
2. リリースに添付したい場合はタグを push:
   ```bash
   git tag biofeedback-v1.0.0 && git push origin biofeedback-v1.0.0
   ```
   ワークフローが APK と EXE を **Releases** に添付します（Releases ページからダウンロード可能）。

ビルドの内訳:
- **Windows EXE**: `electron/`（Electron + electron-builder, `windows-latest` で nsis/portable を生成）
- **Android APK**: `cordova/config.xml` ＋ `www/` を Cordova でパッケージ（debug APK）

> 注: Windows EXE は未署名（SmartScreen 警告が出ることがあります）。Android debug APK は
> 「提供元不明のアプリ」を許可してインストールします。いずれも配布時はご自身の署名鍵で
> 署名することを推奨します。

## ファイル
| パス | 役割 |
|:--|:--|
| `www/index.html` | アプリ本体（依存なし・Web Audio） |
| `electron/main.js`, `electron/package.json` | Windows EXE ラッパー（Electron） |
| `cordova/config.xml` | Android APK パッケージ設定（Cordova） |
| `../../.github/workflows/omega-biofeedback-build.yml` | APK＋EXE ビルド＆Release添付ワークフロー |

---

*© 2025 Masaaki Yamaguchi · 山口 雅旭 · Bada / bio_medicine · アート/娯楽・非医療・非予知*
