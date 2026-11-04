# 論文 — BadaLinear-OS

**超伝導磁石と空気抵抗を反重力の補空間で置き換えるリニア新幹線オペレーティングシステム BadaLinear-OS の設計と実装**
（英語版：*Replacing Superconducting Magnets and Air Drag by the Complementary Space of Antigravity — BadaLinear-OS*）

山口 雅旭 (Masaaki Yamaguchi) · Global Differential Manifold Research

- 📄 `BadaLinear_OS_paper.pdf` — 日本語版（A4・3ページ）
- 📄 `BadaLinear_OS_paper_EN.pdf` — English edition (A4, 3 pages)
- 🐍 `make_paper.py` — 両版を生成する reportlab ジェネレータ

数値（表 1〜3・揚力比 L=2.125・抗力 157.1 kN→9.6 N・所要 36.6→21.8 分）は、
すべて実装 `../lib/badalinear/guideway.rb` からの実測値。

```bash
pip install reportlab
python3 make_paper.py     # -> BadaLinear_OS_paper.pdf, BadaLinear_OS_paper_EN.pdf
```
日本語は reportlab 組込 CID フォント、英語は FreeSerif／DejaVu（システム TTF）を使用。
