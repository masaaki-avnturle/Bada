# SafePower — 安全オフ + rehalt (APK / Windows / Ubuntu)

電源スイッチをいきなり切っても壊れないように状態を保存して電源を落とす
**安全オフ**と、再起動せずに OS を再ロードする **rehalt** を、**Windows
10/11・Ubuntu・Android** のアプリとしてパッケージします。**あなた自身の PC**
が対象です。

## 何をするか

| アクション | Linux | Windows | 意味 |
|---|---|---|---|
| **安全オフ** | `sync && systemctl hibernate` | `shutdown /h` | バッファを書き出し、状態をディスクに保存(ハイバネート)して電源断。**以後いきなり電源を切っても破損・誤作動しない**。次回そのまま復帰。 |
| **サスペンド** | `sync && systemctl suspend` | `SetSuspendState` | RAM保存の省電力。復帰は速いが電源を完全に切ると失われる。 |
| **シャットダウン** | `sync && systemctl poweroff` | `shutdown /s /t 0` | sync してからクリーンに電源断。 |
| **rehalt** | `systemctl soft-reboot`(→ `kexec` → `reboot`) | `explorer` 再起動 | **再起動せずに OS を再ロード**。Linux は実行中カーネルを保ったままユーザ空間を再起動(soft-reboot)、または `kexec` で POST を飛ばす高速再起動。zsh の `rehalt` 相当。 |

> **RAM保存 vs ハイバネート**: 「電源スイッチをいきなり切っても安全」にするには、
> RAM だけのサスペンドでは不十分です(電源を切ると RAM の内容は消えます)。
> 状態を**ディスクに保存するハイバネート**が「安全オフ」の正解で、本アプリの
> 既定アクションです。

## 実行の仕組みと権限

- **デスクトップ版(Electron)**: ボタンを押すと**確認のうえ実際に実行**します
  (`main.js` が OS コマンドを起動)。Linux は polkit/sudo、Windows は管理者
  権限が必要な場合があります。
- **ブラウザ単体・Android**: OS の電源操作は行えません(**表示のみ**。Android
  で実機を制御するには root/system 権限が必要)。実行コマンドをコピーして端末で
  使えます。
- **CLI**: `node cli/safepower.js <safe-off|suspend|shutdown|rehalt> [--dry-run] [--yes]`
  / `./cli/rehalt [--dry-run] [--yes]`。

## 構成

```
safepower-app/
  www/index.html   SafePower 本体 (自己完結・ビルド時に生成)
  electron/        Windows EXE / Ubuntu AppImage・deb (実行ブリッジ)
  cordova/         Android APK 設定 (表示のみ)
  cli/             safepower.js / rehalt
```

## 入手 (Releases / Actions)

| プラットフォーム | ファイル |
|---|---|
| Windows 10 / 11 | `SafePower-*-x64.exe` |
| Ubuntu | `SafePower-*-x86_64.AppImage` / `SafePower-*-amd64.deb` |
| Android | `safepower-debug.apk` (表示のみ) |

ビルドは [`safepower-app-build.yml`](../../.github/workflows/safepower-app-build.yml)。
ブランチ/`main` への push で自動ビルドされ、Actions の Artifacts から取得できます。
`safepower-v*` タグ / `workflow_dispatch` で Release に添付。

```sh
node bada_gui_ide/tools/build-safepower.js
cd bada_gui_ide/safepower-app/electron && npm install && npm start
npm run dist         # Windows EXE
npm run dist:linux   # Ubuntu AppImage / deb
```
