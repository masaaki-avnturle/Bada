# InstantOn — 瞬間起動 (APK / Windows / Ubuntu)

**電源を切ると状態をディスクに保存し、次に電源を入れると通常のブート準備を
飛ばして、いきなり前回の状態から立ち上がる**ように設定するアプリです
(復帰起動 / 高速スタートアップ)。SafePower の応用で、**あなた自身の PC**
が対象です。

```
電源OFF → 状態をディスクに保存(ハイバネート) → 電源ON → ブートを飛ばして即復帰
```

## アクション

| アクション | Linux | Windows | 内容 |
|---|---|---|---|
| **状態確認** | `cat /sys/power/state` + `swapon --show` | `powercfg /a` + 高速起動フラグ | 休止/高速起動が有効か、swap があるかを表示(読み取りのみ) |
| **有効化** | logind: `HandlePowerKey=hibernate` | `powercfg /hibernate on` + `HiberbootEnabled=1` + 電源ボタン=休止 | 以後、電源オフで状態保存→次回ブートを飛ばして即復帰 |
| **いま休止** | `sync && systemctl hibernate` | `shutdown /h` | いま状態を保存して電源断。次回そのまま復帰 |
| **無効化** | 設定削除 | `HiberbootEnabled=0` | 通常のシャットダウン/起動に戻す |

> **Windows** は「高速スタートアップ(ハイブリッドブート)」を有効化します。
> シャットダウン時にカーネル セッションを休止状態として保存するため、次回の
> 電源投入がほぼ瞬時になります。**Linux/macOS** はハイバネート(suspend-to-disk)
> からの復帰で同等の即起動を実現します(要 swap 領域, RAM 以上)。

## 実行と権限

- **デスクトップ版(Electron)**: ボタン→**確認**→実際に設定/実行(`main.js`)。
  設定には Linux は sudo、Windows は管理者権限が必要な場合があります。
- **ブラウザ/Android APK**: **表示のみ**(実行コマンドをコピー可)。Android で
  実機設定には root/system 権限が必要。
- **CLI**: `node cli/instanton.js <status|enable|hibernate-now|disable> [--dry-run] [--yes]`

## 構成 / 入手

```
instanton-app/
  www/index.html   InstantOn 本体 (自己完結・ビルド時に生成)
  electron/        Windows EXE / Ubuntu AppImage・deb (実行ブリッジ)
  cordova/         Android APK 設定 (表示のみ)
  cli/instanton.js
```

| プラットフォーム | ファイル |
|---|---|
| Windows 10 / 11 | `InstantOn-*-x64.exe` |
| Ubuntu | `InstantOn-*-x86_64.AppImage` / `InstantOn-*-amd64.deb` |
| Android | `instanton-debug.apk` (表示のみ) |

ビルドは [`instanton-app-build.yml`](../../.github/workflows/instanton-app-build.yml)。
ブランチ/`main` への push で自動ビルドされ、Actions の Artifacts から取得できます。
`instanton-v*` タグ / `workflow_dispatch` で Release に添付。
