# Ω-DrugForge — 形態形成場 薬剤製造シミュレーション

> ⚠ **概念実証・教育用シミュレーション／非医療**  
> 実在の薬剤製造・医療とは無関係の概念シミュレーションです。

## 概要

ガンマ関数における**大域的微分多様体の相加相乗平均(AGM)方程式**に基づき、**形態形成場(Morphogenetic Field)**で還元剤の新薬を設計・製造シミュレーションするアプリケーション。

### 対象
- **HIV-1/HIV-2**: 酸性エンベロープ環境(pH 4.8–6.5)
- **癌(RAS変異/p53欠損/HER2陽性)**: 腫瘍微小環境(pH 6.0–6.9)

### 薬剤ベース
- セレネース(ハロペリドール)改良型
- ヌクレオシド逆転写酵素阻害剤ベース
- プロテアーゼ阻害剤ベース
- 免疫チェックポイント阻害ベース

## 数学基盤

| 方程式 | 概要 |
|---|---|
| AGM(a,b) | a_{n+1}=(a_n+b_n)/2, b_{n+1}=√(a_n·b_n) — 相加相乗平均 |
| Γ(s) | ∫₀^∞ t^{s-1} e^{-t} dt — ガンマ関数 |
| 形態形成場 | ∂φ/∂t = D∇²φ + ρφ(1-φ/K) - μφ + S(x,t) |
| 還元電位 | E_red = E₀ - (RT/nF)ln(Q) · Γ-AGM変調 |

## 使い方

### ブラウザで直接開く
`www/index.html` をブラウザで開くだけで動作します。

### ダウンロード (GitHub Releases)
- **Windows 10 / 11**: `Omega-DrugForge-1.0.0-x64.exe` — NSIS インストーラ / ポータブル
- **Ubuntu**: `Omega-DrugForge-1.0.0-x86_64.AppImage` / `.deb`
- **Android**: `omega_drug_forge-debug.apk`

### ローカル実行 (Electron)
```bash
cd electron
npm install
npm start
```

## ライセンス

MIT — Masaaki Yamaguchi / Bada
