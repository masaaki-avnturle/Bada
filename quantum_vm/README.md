# BadaVM Pro — 量子ハイパーバイザ + BadaOS + BadaX Server

**すべて量子プログラミング言語 Bada で書かれた 3 点セット**です(教育目的の非公式オマージュ):

| # | コンポーネント | 風 (オマージュ元) | Bada ソース |
|:--|:--|:--|:--|
| ① | **BadaVM Pro** — デスクトップ・ハイパーバイザ | VMware Workstation Pro | [`bada/vmpro.bada`](bada/vmpro.bada) |
| ② | **BadaOS 12.0** — ゲスト OS (NetBSD 風ベース + **Ubuntu 風 apt**) | NetBSD + Ubuntu | [`bada/badabsd.bada`](bada/badabsd.bada) |
| ③ | **BadaX Server** — Windows ホスト側の外部 X サーバー | ASTEC-X | [`bada/badax.bada`](bada/badax.bada) |

ダウンロードは 1 ファイルだけ: **[`dist/bada-vm-pro.html`](dist/bada-vm-pro.html)** を保存してブラウザで開くだけで動きます(インストール不要・依存なし・オフライン可)。Windows 10 / 11 向けのインストール型 EXE も [Releases](https://github.com/masaaki-avnturle/Bada/releases) からダウンロードできます。

---

## 何ができるか

1. **▶ 起動** すると、仮想マシンが `BadaOS-12.0-amd64-quantum.iso` (CD) から起動し、
   NetBSD の sysinst 風フルスクリーン・インストーラが立ち上がります。同時に
   **1 画面セットアップダイアログ**が開き、**「CUI の英語 / 日本語」「GUI おまかせ /
   CUI 手動」「実ハードディスク rd0 / 仮想ディスク wd0」+ root パスワード・ホスト名を
   一度に選んで、ボタン 1 つで最後まで自動インストール**できます(日本語を選ぶと
   sysinst の画面も日本語になります)。「閉じる」を押せば従来どおり CUI を手動操作。
2. インストール先は **仮想ディスク wd0 (.qvmdk)** か、VMware Pro の Raw Device Mapping 風の
   **実ディスク rd0 (パススルー)** を選択。GPT/MBR を選んだあと、**ブートローダ工程**で
   **LILO をマスターブートレコードへ (`lilo -M` がセクタ 0 に 446 byte のブートコードを書き込み)、
   GRUB 2 メニューモードでチェイン**する構成 (推奨)、GRUB 単体、LILO 単体を選べます。
   `newfs -O 2` FFSv2 → `base.tgz` 〜 `apt-quantum.tgz` / `xserver-badax.tgz` のセット展開 →
   root パスワード → ホスト名 → DHCP で完了。
3. 再起動すると **LILO(MBR) → BadaOS Commander (System Commander 風 OS 選択メニュー,
   GRUB メニューモード) → カーネル dmesg → `/etc/rc` → `login:`**。
   **vim・emacs・sshd・xinetd・curl・wget は最初からインストール済み**で、sshd と xinetd は
   初回起動から `/etc/rc` が自動起動します (`netstat` で *.22 ほかが即 LISTEN)。
   インストーラは root と一緒に**最初の一般ユーザー `bada`** も作ります (Ubuntu 流)。
4. **Ubuntu 風コマンドライン + NAT 経由のインターネット**:
   ```
   ping www.badaos.or.jp                     # NAT (10.0.2.2 / DNS 10.0.2.3) 越しに外へ
   curl http://www.badaos.or.jp/             # 外部サイトを取得
   wget http://www.badaos.or.jp/             # ~/index.html に保存
   apt update                                # 外部ミラー http://archive.badaos.or.jp から取得
   apt install zsh tcsh bash                 # 追加パッケージも NAT 越しにダウンロード
   apt install gcc python3 cowsay ...        # ★ アーカイブは Ubuntu 級 (74,362 パッケージ):
                                             #   任意のパッケージ名が導入・実行・削除可能
   apt search NAME / apt remove NAME         # 検索・削除も Ubuntu 同様
   vim /etc/motd  /  emacs /etc/rc.conf      # プリインストール済みエディタ
   grub-install / update-grub                # ブートローダ工具も最初から入っています
                                             #   (update-grub は os-prober 流に Ubuntu /
                                             #    Windows 10 / Windows 11 もメニューに登録)
   lsusb / bluetoothctl                      # USB コネクタと Bluetooth も認識済み
   su - bada                                 # root → 一般ユーザー (プロンプトが $ に)
   sudo apt update                           # 一般ユーザーから root 権限で 1 コマンド
   su                                        # 一般ユーザー → root (パスワード入力)
   adduser NAME / passwd [NAME] / chsh -s /bin/zsh / whoami / id / exit
   ssh localhost                             # Bell 対 QKD ハンドシェイクの ssh
   ```
5. `xclock &` `xeyes &` `xterm &` を実行すると、X クライアントが NAT 越しに
   `DISPLAY=10.0.2.2:0` — **Windows ホスト側の BadaX Server ウィンドウ** — に表示されます。
   ASTEC-X と同じ「計算は UNIX 側、表示は Windows 側」のワークフローです。
   **`w9wm &` で BadaX のウィンドウ管理が Plan 9 スタイルの w9wm になります**:
   タイトルバー無しの素朴なボーダー、**仮想デスクトップ 4 面**(ルート左上の
   w9wm ボックスバーで切替)、ウィンドウ右クリックで Hide / To desk / Delete、
   ルート右クリックで New xterm / unhide。`afterstep &` で NeXT 風の AfterStep
   (グラデーションタイトルバー + 右端の Wharf ドックから xterm / mlterm / xclock /
   xeyes をワンクリック起動)、**`wmaker &` で Window Maker**(NeXTSTEP ワークスペース、
   同じドック付き)にも切替でき、`twm &` で元の見た目に戻ります
   (WM の状態も OS 状態としてイベント台帳にリプレイされます)。
   `mlterm &` は **日本語対応の mlterm ウィンドウ**(UTF-8 バナー + ライブシェル)、
   `xcalc &` は **実際に計算できる電卓ウィンドウ**(x11-apps)です。
   `udisksctl` で **USB メモリの認識とマウント**(`udisksctl mount -b /dev/sd0i`)、
   `apt install nautilus` も NAT 越しにそのまま入ります。
   `nmcli` は **NetworkManager**(NAT 自動接続の管理。GUI は nm-connection-editor /
   `badaos-network`)で、起動時に DHCP で自動的にインターネットへ接続します。
   **DNS は NetworkManager 自身が `/etc/resolv.conf` を書きます**(systemd-resolved の
   スタブ経由にはしません ― 実機で「ルーティングは通るのに名前解決だけ失敗=ネットに
   繋がらない」の最大の原因なので廃止)。公開 DNS(9.9.9.9 / 1.1.1.1 / 8.8.8.8)を
   プロファイルにフォールバックとして焼き込み、`ifupdown` に載った NIC も
   NetworkManager が管理(`managed=true`)、起動時の自己修復サービス
   `badaos-net.service` が上がらなかった NIC を DHCP で繋ぎ直します。
   **もしインターネットに繋がらない時は `badaos-net-fix` を実行**すると、
   NetworkManager を再起動 → 全 NIC を DHCP → DNS を修復 → ルーティングと名前解決を
   検証し、どの段階(リンク/IP/DNS/経路)で失敗したかまで表示します。
   **外部ルーターの USB アダプタ**を PC(BadaOS)の USB コネクタに挿すだけで、
   **コマンドもパスワードも要らず、自動で NAT 越しにインターネットへ接続**します:
   udev が新しい net インターフェース(CDC-ECM の `usb0`)を検出 →
   `usb_modeswitch` で NIC モード確認 → NetworkManager が
   **プロファイル無し・パスワード無しで自動 DHCP**(`no-auto-default=` で全有線/USB を
   自動接続)→ NAT のリースを取得してオンライン、という流れが `badaos-usbnet-up`
   udev ルールで全自動で走ります(手動確認は `badaos-router plug`)。
   Wi-Fi / LTE アダプタなど**パスコード(暗証番号)が要る場合**は
   `badaos-router`(検出・スキャン)→ `badaos-router connect "SSID"` を実行すると
   **パスコードの入力を求められ**、確実に接続します:入力したパスコードを
   **8〜63 文字か検証**(短すぎ・打ち間違いを即エラー表示。接続失敗の一番の原因)し、
   **WPA ハンドシェイクを最大 3 回リトライ**、接続後に**リンク・DNS・ping で疎通確認**
   してから「接続成功(Connected)」と表示します(パスコードは
   `badaos-router connect "SSID" "パスコード"` のように直接渡すことも可能。実 ISO では
   usb-modeswitch / ModemManager / wpasupplicant + ファームウェア同梱、
   `nmcli device wifi connect` でも可)。
   `timedatectl` で **Windows / Ubuntu / BadaOS の時計を同期**できます:
   `timedatectl sync`(NTP を NAT 越しに引いて 3 つの OS の時計を合わせる。
   Bell 対 QKD 署名付き)、`timedatectl set-local-rtc 1`(Windows デュアルブート用に
   共有 RTC をローカル時刻に)、`timedatectl`(状態表示)。
   開発ツールも同梱: `git` / `curl` / `gcc`・`make`(build-essential)=
   **Xcode Command Line Tools 相当**、`screen` / `tmux` / `texlive`(日本語)も同梱。
   **重量級(clang・texlive-full など)は NAT 経由でワンコマンド導入**できます:
   `badaos-extras clang` / `badaos-extras texlive-full` / `badaos-extras dev|media|all`
   (2GB の ISO には焼けない大きなものはインターネットから取得。`xcode-select --install`
   や `brew install <formula>` でも入ります)。
7. **BadaApache — Bada 言語で書いた Apache** が **ウルトラネットワークに取り込まれます**:
   ```
   apachectl start                 # DocumentRoot を zone://url.or.jp/ に公開
   zone zone://url.or.jp/apache    # リング DHT からその Apache ページを取得
   curl http://localhost/          # mod_zone が http を zone:// へブリッジ
   zonebrowser zone://url.or.jp/ & # ZoneBrowser で表示
   apachectl status / stop / configtest
   ```
   従来の Apache が TCP:80 で待ち受けるのに対し、BadaApache は **zone://url.or.jp
   というゾーンに bind** します(mod_zone)。各ページは Jones 多項式量子鍵で封緘され、
   Bell 対 QKD でセッション鍵を合意して P2P リングで配送 — サーバも DNS も無しで
   世界中のピアから取得できます。停止すると url.or.jp は組み込みの既定サイトに戻ります。
   実装は `quantum_vm/bada/badapache.bada`(全て Bada 言語)。
   **xterm ウィンドウの中も本物のコマンドラインです**: 各 xterm は BadaOS 上の
   ライブな pty セッション (ttyp&lt;n&gt;) で、ウィンドウ内を直接クリックして
   `apt` や `zsh` などのコマンドを打てます (シェルスタックはウィンドウごとに独立、
   最下段で `exit` すると実物の xterm と同じくウィンドウが閉じます)。VM コンソールと
   xterm は同じ OS 状態を共有します。
6. **zone:// ウルトラネットワークが OS 内で使えます** — ZoneBrowser と同じ
   zone ランタイム (`bada_gui_ide/browser/zone-lib.bada`: P2P リング DHT +
   Kauffman/Jones 鍵 + Bell 対 QKD + AEAD) を OS に同梱:
   ```
   zone zone://url.or.jp/            # CLI で取得 (DHT 経路・Jones 鍵・AEAD タグ表示)
   curl zone://url.or.jp/security    # curl も zone:// を話します
   zone put zone://url.or.jp/mypage こんにちは   # 自分のページをリングへ封緘・公開
   zonebrowser &                     # ZoneBrowser を X クライアントとして BadaX に表示
   ```
   ZoneBrowser ウィンドウはアドレスバー・リンク遷移・セキュリティ表示
   (ノード / 経路 / DHT キー / Jones 鍵 / AEAD タグ) 付きです。
   さらに **MigemoInsta** — リング上の写真フィード (zone://insta.or.jp/) を
   **migemo 検索**(ローマ字で日本語をインクリメンタル検索: `sakura` が
   さくら/サクラ/桜 に当たる)できる Instagram 風アプリ:
   ```
   migemoinsta sakura        # CLI 検索 (romaji → ひらがな/カタカナ/漢字よみ)
   migemoinsta post 今日の空  # 自分の投稿をリングへ封緘・公開
   migemoinsta &             # X クライアント: 検索バー + フィード + ♥
   ```
   migemo エンジン (ローマ字→かな展開・促音・拗音対応) も Bada 言語製です。
7. **📷 スナップショット / ⤺ 復元** — マシンの全状態 (apt でインストールしたパッケージ含む) は
   追記専用イベント台帳 (Akashic machine tape) の決定論的リプレイなので、スナップショットは
   台帳のプレフィックスそのものです。

### 量子要素

- **vCPU** は 8 qubit (Hilbert 次元 256) の量子レジスタを持ち、`qstat` で Bell 対の
  **零保存** (禁制状態 |01>,|10> が厳密に 0 のまま) を確認できます。
- 仮想ネットワークと `ssh` は **Bell 対 QKD** で守られ、X サーバーの認証は
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
| **実機起動 ISO** 🖥️ | [Releases](https://github.com/masaaki-avnturle/Bada/releases) の `BadaOS-12.0-live-amd64.iso` — **本物の PC の GRUB メニューに BadaOS が表示され単独起動**。USB 起動・**Ubuntu 風の親切な GUI インストーラ**(日本語ウィザード + パーティションバー)・**実ディスクの空きスペースへの本インストール(既存 OS を消さず GRUB メニューに共存)**・ディスク全体インストール・既存 GRUB へのエントリ追加に対応。詳細は [`live/README.md`](live/README.md) |

### ダウンロード方法は 2 通り

**A. Releases から(おすすめ・ログイン不要・保存無期限)** —
[Releases ページ](https://github.com/masaaki-avnturle/Bada/releases)の最新リリースを開き、
Assets の一覧からダウンロードします。名前が変わらないファイルは**固定リンク**も使えます:

- 最新の単一 HTML: <https://github.com/masaaki-avnturle/Bada/releases/latest/download/bada-vm-pro.html>
- 最新の実機起動 ISO: <https://github.com/masaaki-avnturle/Bada/releases/latest/download/BadaOS-12.0-live-amd64.iso>

(EXE / deb / AppImage はファイル名にバージョンが入るため、Releases ページから選んでください)

**B. Actions から(GitHub にログインした状態で)** — リポジトリの
[Actions タブ](https://github.com/masaaki-avnturle/Bada/actions/workflows/quantumvm-app-build.yml)
→ 一番上の緑 ✓ の実行を開く → ページ下部の **Artifacts** からダウンロード:

| Artifact 名 | 中身 |
|:--|:--|
| `badavmpro-windows` | Windows 10/11 EXE(NSIS インストーラ + ポータブル) |
| `badaos-live-iso` | 実機起動 ISO (`BadaOS-12.0-live-amd64.iso`) |
| `badavmpro-html` | 単一 HTML (`bada-vm-pro.html`) |
| `badavmpro-linux` | Ubuntu 用 AppImage + deb |

Actions の Artifact は **zip** で落ちるので、解凍して中のファイルを使ってください
(保存期間 90 日)。ビルドは main / master への push・`quantumvm-v*` タグ・
このブランチへの push のたびに自動実行され、マージ後は Actions タブの
「Run workflow」ボタンでも手動実行できます。

ビルドは [`quantumvm-app-build.yml`](../.github/workflows/quantumvm-app-build.yml) が実行します
(`quantumvm-v*` タグで Release へ添付 / `workflow_dispatch` で Actions アーティファクト)。

## 開発

```
node quantum_vm/tools/build-vm.js
```

で `dist/bada-vm-pro.html` と Electron 用 `app/www/index.html` を再生成します。
ビルド前に、実 Bada インタープリタで **電源オン → sysinst インストール (実ディスク rd0 +
LILO→MBR + GRUB メニュー) → 再起動 → ログイン → `apt install ssh xinetd zsh tcsh bash` →
シェル切替 → QKD ssh → BadaX への X クライアント表示 → xterm 内ライブシェル →
zone:// / MigemoInsta → Ubuntu 級 apt → grub-install / update-grub** の
ライフサイクル全体 (55 イベント) をセルフチェックし、失敗すると生成しません。

```
quantum_vm/
├── bada/
│   ├── vmpro.bada     ① ハイパーバイザ: 量子 vCPU / .qvmx / BIOS / スナップショット
│   │                     + 共有量子サービス (Kauffman/Jones 鍵, Bell 対 QKD)
│   ├── badax.bada     ③ X サーバー: JONES-KNOT-COOKIE-1 認証, ウィンドウ管理,
│   │                     カスケード配置, xdpyinfo
│   └── badabsd.bada   ② BadaOS: sysinst (ディスク選択 wd0/rd0・ブートローダ工程) /
│                         LILO→MBR + GRUB メニュー / FFS 風 FS / dmesg / rc / login /
│                         apt (openssh・xinetd・bash・zsh・tcsh ほか) / service /
│                         chsh・which・dpkg / QKD ssh / シェル (echo リダイレクト,
│                         ps, df, ifconfig, netstat, sysctl, qstat, xclock…)
├── tools/
│   ├── template.html  ホスト UI (VMware 風クローム + BadaX ウィンドウ)
│   └── build-vm.js    セルフチェック + 単一 HTML 生成
├── dist/bada-vm-pro.html  ★ 配布物 (コミット済み)
└── app/electron/          Windows 10/11 EXE / Ubuntu 用ラッパー
```

> ※ VMware, NetBSD, Ubuntu, ASTEC-X, GRUB, LILO の各名称はそれぞれの権利者の商標・成果物です。
> 本フォルダはそれらとは無関係の、Bada 言語による教育目的の再構成 (オマージュ) です。
> アプリ内 sysinst の rd0「実ディスク」はシミュレーションで、ホストのディスクには書き込みません。
> **実機の実ディスクに本当にインストールして GRUB から起動**したい場合は
> [`live/README.md`](live/README.md) の BadaOS Live ISO (`BadaOS-12.0-live-amd64.iso` +
> `badaos-install`) を使ってください — こちらは本物の GRUB を本物の MBR/ESP に書き込みます。
> 既定モードは**ディスクの空きスペースへのインストール**で、既存の OS・パーティションは
> 消さずに GRUB メニューへ並べます(全体消去は明示的な別モード)。
