# 🎼 BADA Compose — 作曲スタジオ

**Piano Concerto BADA のコード進行を動かしているエンジンを、そのまま操作できる作曲アプリにしたもの。**
[`bada_fuga/`](../bada_fuga/) の Python 作曲エンジン (`compose.py` の対位法生成、`compose_pconcerto.py` のピアノ協奏曲) を JavaScript に移植し、
小節ごとに和音・役割・テンポ・主題を編集すると、その場で 4 声が作り直されて、ピアノと管弦楽の合成音で鳴ります。依存ゼロ・単一 HTML・完全オフライン動作。

## ✨ できること

- **Piano Concerto BADA を開いて操作** — 起動すると 3 楽章 123 小節 (嘆きのパッサカリア → 主題 I のフーガ → カデンツァ → Adagio Lamento → 三重フーガ → D 長調のコーダ) がそのまま読み込まれます。楽章ごとのひな形、8 小節の新規曲からも始められます
- **小節の編集** — 和音 (1・2・4 個、転回 `A7/C#` も可)、役割 (ソロ = ピアノ / トゥッティ = 管弦楽 / 合奏 / カデンツァ)、テンポ、強弱、奏法、休む声部、和音の保持、金管、ティンパニ、見出し。和音パレットをタップして書き込めます
- **形式の編集** — 小節の挿入・複製・削除、末尾に 4 小節の循環を足す。置いた主題は一緒にずれます
- **主題** — 組み込みの主題 I 〈MOTHER〉 / 主題 II 〈トラック18〉 / 主題 III 〈B-A-D-A〉 / 嘆きのバス / カデンツァの走句、自分で書いた主題 (`D4:3 E4:1 F4:2 …`)、選んだ小節の和音から作る旋律を、好きな声部・小節・拍・移調で置けます
- **対位法エンジン** — 置いた主題に合わせて、自由声部を規則ベースで生成 (和音構成音の選択、平行 5 度・8 度 / 声部交差 / 半音衝突の回避、経過音・隣接音の装飾)。🎲 で乱数を変えて作り直し、平行進行と強拍の不協和の数を表示
- **様式** — 協奏曲 (ピアノ + 弦 5 部・木管・ホルン・トランペット・トロンボーン・ティンパニ) / ピアノ独奏 / 弦楽合奏。出力の調 (±6 半音) とテンポ (50–150%)
- **書き出し** — WAV (オフライン合成) / MIDI (楽器ごとのトラック・テンポ・見出し) / 動画 (ピアノロールを録画、MP4 または WebM) / score.json (Python 版 `synth.py`・`video.py` でそのまま高音質の音声・mp4 に) / プロジェクト (.json)

## 🔁 Python 版との一致

`tools/engine-test.js` が、アプリのひな形を Python 版の出力 `bada_fuga/score_pconcerto.json` と照合します:
和声 492 拍、テンポ・マップ、主題の音 327 個 (拍・音高・名前・声部)、最上声の B-A-D-A、小節ごとの役割・強弱・奏法、見出し、主題の入り がすべて一致。
自由声部は乱数の実装が違うため Python 版とは別の (同じ規則に従う) 4 声になります。

```bash
node bada_compose/tools/engine-test.js
```

## 🚀 使い方

1. [`index.html`](index.html) を保存してダブルクリック (インストール不要)、または下のネイティブアプリ
2. ▶ で選んだ小節から再生。下の小節の列をタップして選び、「🎹 小節」タブで編集
3. 「🎵 主題」タブで主題を書いて保存 → 「小節」タブで声部と位置を選んで置く
4. 「💾 書き出し」で範囲を選んで WAV / MIDI / 動画 / score.json

## 📱💻 ネイティブ アプリ

| プラットフォーム | ファイル |
|:---|:---|
| **Android** (APK) | `bada-compose-debug.apk` |
| **Windows 10 / 11** | `BadaCompose-*-x64.exe` (NSIS インストーラ) / `BadaCompose-*-portable.exe` |
| **Linux** (Ubuntu ほか) | `BadaCompose-*-x86_64.AppImage` / `BadaCompose-*-amd64.deb` |

ビルドは [`compose-app-build.yml`](../.github/workflows/compose-app-build.yml) が実行します
(`bada_compose/` を変えた push で Actions アーティファクト、`compose-v*` タグで Release へ添付)。

- `app/cordova/config.xml` — Android (Cordova 12, SAF の保存ダイアログ)
- `app/electron/` — Windows / Linux (Electron 31 + electron-builder)

## 💾 保存

1. **Android (APK)** — 保存ダイアログ (SAF) で保存先を選ぶ (`cordova-plugin-save-dialog`)
2. **Windows / Linux / Chrome / Edge** — ネイティブの保存ダイアログ (`showSaveFilePicker`)
3. **それ以外のブラウザ** — 通常のダウンロード

編集中のプロジェクトは端末内 (localStorage) に自動保存されます。
