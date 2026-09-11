#!/usr/bin/env node
/* 小槌の家計簿 — エンジンテスト
   index.html からレシート解析・簿記計算のコア関数を抽出して検証します。
   実行: node kozuchi_kakeibo/tools/engine-test.js */
"use strict";
const fs = require("fs");
const path = require("path");
const vm = require("vm");

const html = fs.readFileSync(path.join(__dirname, "..", "index.html"), "utf8");
const m = html.match(/<script>([\s\S]*)<\/script>/);
if (!m) { console.error("inline <script> not found"); process.exit(1); }
const src = m[1];

function slice(from, to) {
  const a = src.indexOf(from), b = src.indexOf(to);
  if (a < 0 || b < 0 || b <= a) { console.error(`slice failed: ${from} .. ${to}`); process.exit(1); }
  return src.slice(a, b);
}

/* DOM 非依存のコア部分だけを切り出して実行 */
const core =
  "const today = () => new Date().toISOString().slice(0,10);\n" +
  slice("const ACCOUNTS", "/* ---------- データ層") +          // 勘定科目 + 判定ルール
  slice("function z2h", "/* ---------- 確認フォーム") +        // レシート解析
  slice("function accountBalance", "function renderReports");  // 簿記計算

const ctx = { console };
vm.createContext(ctx);
/* const/let は vm グローバルに載らないため、同一スクリプト末尾でまとめて返す */
const { parseReceipt, guessCategory, accountBalance, ACCOUNTS } = vm.runInContext(
  core + "\n;({ parseReceipt, guessCategory, accountBalance, ACCOUNTS });", ctx);

let failed = 0;
function t(name, cond) {
  if (!cond) { console.error("FAIL:", name); failed = 1; }
  else console.log("ok:", name);
}

/* ---- テスト1: スーパーのレシート (¥表記・カンマ・税・預り/釣り除外) ---- */
let r = parseReceipt(`スーパーライフ 田町店
東京都港区1-2-3 TEL:03-1234-5678
2025年9月10日(水) 18:42
食パン           ¥158
牛乳 1000ml      ¥238
豚こま切れ       ¥458
シャンプー詰替   ¥398
小計            ¥1,252
消費税(8%)       ¥68
合計            ¥1,252
お預り          ¥2,000
お釣り            ¥748`);
t("date", r.date === "2025-09-10");
t("store", r.store.includes("ライフ"));
t("total", r.total === 1252);
t("tax", r.tax === 68);
t("items4", r.items.length === 4);
t("cat-food", r.items[0].cat === "食費");
t("cat-daily", r.items[3].cat === "日用品費");

/* ---- テスト2: コンビニ (令和・全角数字・円表記) ---- */
r = parseReceipt(`セブン-イレブン 港南口店
令和7年9月11日 08:15
おにぎり ツナマヨ  １４０円
ホットコーヒーR    １２０円
合計 ２６０円
現金 ３００円
お釣 ４０円`);
t("reiwa-date", r.date === "2025-09-11");
t("cvs-total", r.total === 260);
t("cvs-items", r.items.length === 2);
t("cvs-cat", r.items.every(i => i.cat === "食費"));

/* ---- テスト3: 品目が読めず合計のみ → 店名から科目を補完 ---- */
r = parseReceipt(`マツモトキヨシ
2025/08/03
合計 ¥1,980`);
t("dr-total", r.total === 1980);
t("dr-fallback-item", r.items.length === 1 && r.items[0].amount === 1980);
t("dr-store-cat", r.items[0].cat === "日用品費");

/* ---- テスト4: 勘定科目の自動判定 ---- */
t("cat-medicine", guessCategory("目薬", "") === "医療費");
t("cat-restaurant", guessCategory("", "マクドナルド 品川店") === "外食費");
t("cat-default", guessCategory("謎の品", "謎の店") === "雑費");

/* ---- テスト5: 複式簿記 — 残高計算と貸借対照表の均衡 ---- */
const E = [
  { date: "2025-09-01", debit: "現金",       credit: "元入金",           amount: 50000 },
  { date: "2025-09-02", debit: "食費",       credit: "現金",             amount: 1252 },
  { date: "2025-09-03", debit: "日用品費",   credit: "クレジット未払金", amount: 398 },
  { date: "2025-09-25", debit: "普通預金",   credit: "給与収入",         amount: 200000 },
];
t("bal-cash", accountBalance("現金", E) === 50000 - 1252);
t("bal-food", accountBalance("食費", E) === 1252);
t("bal-liab", accountBalance("クレジット未払金", E) === 398);
t("bal-capital", accountBalance("元入金", E) === 50000);
t("bal-income", accountBalance("給与収入", E) === 200000);
const byType = ty => Object.keys(ACCOUNTS).filter(a => ACCOUNTS[a].type === ty);
const assets = byType("資産").reduce((s, a) => s + accountBalance(a, E), 0);
const liab   = byType("負債").reduce((s, a) => s + accountBalance(a, E), 0);
const cap    = byType("純資産").reduce((s, a) => s + accountBalance(a, E), 0);
const profit = byType("収益").reduce((s, a) => s + accountBalance(a, E), 0)
             - byType("費用").reduce((s, a) => s + accountBalance(a, E), 0);
t("balance-sheet-balances", assets === liab + cap + profit);

if (failed) { console.error("engine tests FAILED"); process.exit(1); }
console.log("engine tests OK");
