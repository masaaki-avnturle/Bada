ACPI — 原子の臨界期の強度シミュレータ
Atomic Critical-Period Intensity simulator (Bada / Ω)
================================================================

同梱ファイル:
  atom-critical.html      ★ シミュレータ本体。単一 HTML・依存なし・オフライン可。
                          ダブルクリックしてブラウザで開くだけで動きます。
  atom-critical-cli.js    Node.js 用 CLI (要約 / CSV / JSON / スイープ / 元素スキャン)。
  atom_critical.js        モデルコア (物理層 + Ω 作用素層)。CLI が読み込みます。
  atom_critical.bada      同じモデルを Bada 言語で書いたリファレンス実装。
  bada.js                 Bada 言語コア。
  bada-cli.js             Bada の CLI ランナー。

ネイティブ アプリ (インストール型) も Releases から入手できます:
  Android          acpi-debug.apk
  Windows 10 / 11  ACPI-1.0.0-x64.exe   (NSIS インストーラ / ポータブル)
  Ubuntu           ACPI-1.0.0-x86_64.AppImage / ACPI-1.0.0-amd64.deb
  https://github.com/masaaki-avnturle/Bada/releases

使い方:
  1) GUI  : atom-critical.html をダブルクリック。
            元素・波長・ピーク強度・パルス幅・CEP を動かすと臨界期が即時に
            再計算され、4 枚の図と数値パネルが更新されます。
            CSV / JSON / PNG のダウンロードボタン付き。
  2) CLI  : node atom-critical-cli.js run   -e Ar -I 6e14 -l 800 -f 8
            node atom-critical-cli.js scan  -I 4e14
            node atom-critical-cli.js sweep -e Xe --points 30
            node atom-critical-cli.js csv   out.csv -e Ne -I 2e15
            node atom-critical-cli.js selftest
            (atom-critical-cli.js と atom_critical.js を同じ階層に置いてください)
  3) Bada : node bada-cli.js run atom_critical.bada
  4) アプリ: Windows / Ubuntu 版では CSV・JSON・PNG が「名前を付けて保存」
            ダイアログで書き出せます。Android 版は WebView がファイル保存を
            扱えないため、同じボタンで内容を表示するパネルが開きます
            (テキストはクリップボードへコピー、図は長押しで保存)。

何を計算しているか:
  「臨界期」= 強レーザー場のなかで原子のクーロン障壁が完全に抑制され
  (over-the-barrier)、束縛状態がもはや保護されない時間窓。原子単位系で

      F_cr = I_p^2 / (4 Z_c)  [a.u.]      I_cr = F_cr^2 * I_a
      I_a  = 3.5094e16 W/cm^2             (原子単位の強度)

  「強度」= その窓の内側での I(t) = |E(t)|^2 * I_a。水素では
  I_cr = 1.37e14 W/cm^2 という既知の障壁抑制強度を再現します。

  物理層 : 障壁抑制場、ADK トンネル電離率 (水素で厳密解
           w = (4/F) e^{-2/(3F)} に一致)、Keldysh パラメータ γ、
           ポンデロモーティブエネルギー U_p、瞬時場の時間積分。
  Ω 層   : 山口フレームワーク (Bada / omega_llm) の作用素層 —
           ζ(s)=β(p,q)/log x, ζ_n=(x log x)^n, Γ-deprivation e^{-x log x},
           Dalanversian Λ=cos(ix log x)-i sin(ix log x),
           均衡余裕 2e^{-x log x}, Euler 極均衡 x^n+y^n-nxyz=0,
           Kauffman ブラケット <D>(A), 臨界強度指数
           E(σ) = K(σ) × H(σ) / (4 (π_n, e_n))。

(c) Masaaki Yamaguchi — Bada / Global Differential Manifold Research
