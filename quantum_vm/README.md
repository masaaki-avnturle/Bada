# BadaVM Pro — 量子ハイパーバイザ + BadaBSD + BadaX Server

**すべて量子プログラミング言語 Bada で書かれた 3 点セット**です(教育目的の非公式オマージュ):

| # | コンポーネント | 風 (オマージュ元) | Bada ソース |
|:--|:--|:--|:--|
| ① | **BadaVM Pro** — デスクトップ・ハイパーバイザ | VMware Workstation Pro | [`bada/vmpro.bada`](bada/vmpro.bada) |
| ② | **BadaBSD 11.0** — ゲスト OS (インストールして使う) | NetBSD | [`bada/badabsd.bada`](bada/badabsd.bada) |
| ③ | **BadaX Server** — Windows ホスト側の外部 X サーバー | ASTEC-X | [`bada/badax.bada`](bada/badax.bada) |

ダウンロードは 1 ファイルだけ: **[`dist/bada-vm-pro.html`](dist/bada-vm-pro.html)** を保存してブラウザで開くだけで動きます(インストール不要・依存なし・オフライン可)。Windows 10 / 11 向けのインストール型 EXE も [Releases](https://github.com/masaaki-avnturle/Bada/releases) からダウンロードできます。

---

## 何ができるか

1. **▶ 起動** すると、仮想マシンが `BadaBSD-11.0-amd64-quantum.iso` (CD) から起動し、
   NetBSD の sysinst 風フルスクリーン・インストーラが立ち上がります。
2. メニューキー **a → a → a → a → a** で仮想ディスク wd0 へインストール
   (GPT/MBR 選択 → `newfs -O 2` FFSv2 → `base.tgz` 〜 `xserver-badax.tgz` のセット展開)。
   root パスワードとホスト名を設定し、DHCP で `10.0.2.15` を取得して完了。
3. 再起動するとブートローダ → カーネル autoconf dmesg → `/etc/rc` → **login:**。
   `root` でログインすると Bourne 風シェルが使えます (`help` で一覧)。
4. `xclock &` `xeyes &` `xterm &` を実行すると、X クライアントが NAT 越しに
   `DISPLAY=10.0.2.2:0` — **Windows ホスト側の BadaX Server ウィンドウ** — に表示されます。
   ASTEC-X と同じ「計算は UNIX 側、表示は Windows 側」のワークフローです。
5. **📷 スナップショット / ⤺ 復元** — マシンの全状態は追記専用イベント台帳
   (Akashic machine tape) の決定論的リプレイなので、スナップショットは台帳の
   プレフィックスそのものです。

### 量子要素

- **vCPU** は 8 qubit (Hilbert 次元 256) の量子レジスタを持ち、`qstat` で Bell 対の
  **零保存** (禁制状態 |01>,|10> が厳密に 0 のまま) を確認できます。
- 仮想ネットワークは **Bell 対 QKD** で守られ、X サーバーの認証は
  MIT-MAGIC-COOKIE-1 ならぬ **JONES-KNOT-COOKIE-1** — 三葉結び目の
  Kauffman ブラケット / Jones 多項式標本から導出した鍵です
  (`omega_jones_crypto_pkg` の Bada 移植、`zone.bada` と同じ構成)。

すべてのキー入力・コマンドは、同梱の Bada 言語コア (`bada_gui_ide/www/bada.js`)
がその場で **Bada プログラムとして実行**します。ホスト側 HTML は `@@` で始まる
機械可読行 (zone-lib と同じ流儀) を描画するだけです。

---

## 入手方法

| 形態 | 入手 |
|:--|:--|
| **単一 HTML** ★ | [`dist/bada-vm-pro.html`](dist/bada-vm-pro.html) を「Download raw file」で保存して開くだけ |
| **Windows 10 / 11** (EXE) | [Releases](https://github.com/masaaki-avnturle/Bada/releases) の `BadaVMPro-*-x64.exe` (NSIS インストーラ) / `BadaVMPro-*-portable.exe` |
| **Ubuntu** | [Releases](https://github.com/masaaki-avnturle/Bada/releases) の `BadaVMPro-*.AppImage` / `.deb` |

ビルドは [`quantumvm-app-build.yml`](../.github/workflows/quantumvm-app-build.yml) が実行します
(`quantumvm-v*` タグで Release へ添付 / `workflow_dispatch` で Actions アーティファクト)。

## 開発

```
node quantum_vm/tools/build-vm.js
```

で `dist/bada-vm-pro.html` と Electron 用 `app/www/index.html` を再生成します。
ビルド前に、実 Bada インタープリタで **電源オン → sysinst インストール → 再起動 →
ログイン → シェル → BadaX への X クライアント表示** のライフサイクル全体を
セルフチェックし、失敗すると生成しません。

```
quantum_vm/
├── bada/
│   ├── vmpro.bada     ① ハイパーバイザ: 量子 vCPU / .qvmx / BIOS / スナップショット
│   │                     + 共有量子サービス (Kauffman/Jones 鍵, Bell 対 QKD)
│   ├── badax.bada     ③ X サーバー: JONES-KNOT-COOKIE-1 認証, ウィンドウ管理,
│   │                     カスケード配置, xdpyinfo
│   └── badabsd.bada   ② OS: sysinst / FFS 風 FS / ブート / dmesg / rc / login /
│                         シェル (uname, ls, cat, ps, df, ifconfig, sysctl,
│                         qstat, echo リダイレクト, xclock, xeyes, xterm …)
├── tools/
│   ├── template.html  ホスト UI (VMware 風クローム + BadaX ウィンドウ)
│   └── build-vm.js    セルフチェック + 単一 HTML 生成
├── dist/bada-vm-pro.html  ★ 配布物 (コミット済み)
└── app/electron/          Windows 10/11 EXE / Ubuntu 用ラッパー
```

> ※ VMware, NetBSD, ASTEC-X の各名称はそれぞれの権利者の商標です。本フォルダは
> それらとは無関係の、Bada 言語による教育目的の再構成 (オマージュ) です。
