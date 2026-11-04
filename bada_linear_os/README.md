# 🚄 BadaLinear-OS — 反重力リニア新幹線 オペレーティングシステム

> リニア新幹線（超電導リニア L0系）の **超伝導磁石による浮上** を論文集の
> **反重力（重力方程式の補空間エネルギー）** に、**空気抵抗** を **補空間包絡による
> ゼロ抗力** に置き換え、BadaUFO-OS を **生成AI車掌つきの鉄道 OS** として
> Bada 言語で作り換えたもの。

`Bada/bada_linear_os/` — 純 Ruby。物理コアと生成AIは `../bada_ufo_os` を再利用。

---

## 何を置き換えたか

| 超電導リニア L0系 | BadaLinear（論文集による置き換え） |
|:--|:--|
| **浮上**：NbTi 超伝導磁石・液体ヘリウム 4.2 K・電磁誘導（EDS）。150 km/h 未満はゴムタイヤ走行 | 重力方程式の**補空間**＝反重力場 `E_ag = U_grav·cosh(x log x)`。揚力比 `L = 2.125 > 1` は速度に依らず、**停車中も浮上**・極低温不要 |
| **抗力**：`F_d = ½ρC_dAv²`。500 km/h で走行エネルギーの大半 | 車体を**補空間包絡**（真空エネルギー体 `x^x` のコホモロジー切断）で包み、抗力を `σ = 1/cosh(x_env log x_env)²` で切断。`x_env=4` で残存 **6×10⁻⁵ ≈ ゼロ** |
| **動力**：地上コイル リニア同期モータ（変電所給電） | 相対論の補空間 `E⊥ = mc² − ½mv²` を `α_ag` で増幅、**無尽蔵の真空リザーバ** `ρ·x^x` が裏付け。巡航の変電所給電が不要 |
| 運転士・車掌 | **生成AI車掌**（`Bada::Generator`）。放送・運行判断を生成し `Ω::DATABASE`（アカシック）に記録 |

### 比較（実装の計算値）

| 区間 | L0（500 km/h） | BadaLinear（1000 km/h・抗力ゼロ） |
|:--|:--|:--|
| 品川–名古屋 285.6 km | 36.6 分・抗力 3.12 MWh | **21.8 分**・抗力 7.6×10⁻⁴ MWh |
| 品川–新大阪 438.0 km | 54.9 分・抗力 4.78 MWh | **30.9 分**・抗力 1.2×10⁻³ MWh |

（無停車の台形速度プロファイル、快適加速度 1.0 m/s²。実運行計画の 40 分／67 分は途中停車・速度制限込み）

---

## 構成

| ファイル | 内容 |
|:--|:--|
| `lib/badalinear/guideway.rb` | 超伝導→反重力浮上・空気抵抗→補空間包絡・推進・時刻表・L0 比較 |
| `lib/badalinear/os.rb` | `Conductor`（生成AI車掌）・`OS` カーネル |
| `bin/badalinear` | ランチャ（REPL / demo / Bada 言語スクリプト実行） |
| `linear_boot.bada` | **Bada 言語**のブートシーケンス（実インタプリタで動作） |
| `test/test_linear.rb` | テスト 10 件 |

## 実行

```bash
cd bada_linear_os
ruby -Ilib test/test_linear.rb        # テスト
ruby bin/badalinear demo              # ブート→比較→物理→出発→AI車掌
ruby bin/badalinear run linear_boot.bada
ruby bin/badalinear                   # 対話コンソール
```

### コンソール コマンド

| コマンド | 動作 |
|:--|:--|
| `status` / `physics` | 運行状態・物理レポート（浮上力・抗力・動力） |
| `depart [km/h]` | 次駅へ出発（品川→…→新大阪、8 駅） |
| `route [km/h]` | 時刻表 |
| `compare` | 超電導リニア L0 との比較 |
| `envelope <x>` | 補空間包絡 `x_env` を設定（抗力抑制の強さ） |
| `ask <質問>` / `akashic <語>` | 生成AI車掌 ／ 運行記録検索 |

## Bada 言語ブート（`linear_boot.bada`）

```
levitation <- "超伝導磁石を反重力場の補空間エネルギーに置き換える"   # 浮上を反重力へ
drag -< 4.0                                                    # 補空間包絡を多様体積分
vacuum >- vacuum                                               # 無尽蔵の真空へ量子右作用
Omega::push levitation as antigravity_levitation               # アカシックへ記録
```

---

*本 OS は山口フレームワーク（論文集第九巻・BadaUFO-OS 応用篇）に基づく理論的・思弁的シミュレーションであり、実在の超電導リニアの設計・安全性を評価するものではありません。*

---

## 論文 · 3D シミュレータ · ネイティブ配布

| 成果物 | 場所 |
|:--|:--|
| 論文（日本語／英語） | [`paper/BadaLinear_OS_paper.pdf`](paper/BadaLinear_OS_paper.pdf) · [`paper/BadaLinear_OS_paper_EN.pdf`](paper/BadaLinear_OS_paper_EN.pdf) |
| 3D 運行シミュレータ＋設計図（Three.js） | [`app/badalinear_3d.html`](app/badalinear_3d.html)（Artifact 版・CDN） |
| Windows / Ubuntu / Android パッケージ | [`linear-app/`](linear-app/)（Electron・Cordova）＋ [`tools/build-linear-www.js`](tools/build-linear-www.js) |
| CI（Release 添付） | [`.github/workflows/badalinear-app-build.yml`](../.github/workflows/badalinear-app-build.yml) — `badalinear-v*` タグ push または手動実行 |

```bash
node tools/build-linear-www.js          # オフライン www/index.html を生成（three.min.js 同梱）
cd linear-app/electron && npm install && npm run dist        # Windows EXE
                                        npm run dist:linux   # Ubuntu AppImage + deb
```
Release 生成物：`BadaLinear-1.0.0-x64.exe` / `BadaLinear-1.0.0-x64.AppImage` / `.deb` / `badalinear-debug.apk`
