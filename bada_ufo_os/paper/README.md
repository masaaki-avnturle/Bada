# 論文 — BadaUFO-OS

**反重力場の補空間エネルギーに基づく UFO オペレーティングシステムと生成AI操縦士の設計と実装**
— Bada 言語・大域的微分積分多様体理論による BadaUFO-OS —

山口 雅旭 (Masaaki Yamaguchi) · Global Differential Manifold Research

- 📄 **`BadaUFO_OS_paper.pdf`** — 組版済み論文（A4・5 ページ・日本語）
- 🐍 **`make_paper.py`** — PDF ジェネレータ（reportlab）

## 概要

上位ディレクトリの実装 [`bada_ufo_os/`](../) を学術論文としてまとめたもの。三本柱を扱う。

1. **重力方程式の補空間 = 反重力場エネルギー** `E_ag = U_grav · cosh(x log x)`
2. **特殊相対性理論の補空間** `E_⊥ = mc² − ½mv²`
3. **無尽蔵の真空エネルギー体** `E_vac = ρ · x^x`（ダランヴァージアン `□_dal`）

論文中の数値（表 1・表 2・揚力比 L=2.125 など）は、すべて実装
`../lib/badaufo/*.rb` から得た実測値である。

## 論文 PDF の再生成

```bash
pip install reportlab           # 日本語は組込 CID フォント（HeiseiMin/HeiseiKakuGo）を使用
python3 make_paper.py           # -> BadaUFO_OS_paper.pdf
```

外部フォントは不要（reportlab の Adobe-Japan1 CID フォントを埋め込む）。
