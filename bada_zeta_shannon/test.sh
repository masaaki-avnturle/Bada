#!/bin/sh
# 認証テスト: Bada インタープリタで zeta_shannon.bada を実行し、
# 13 項目すべての PASS と対話ドライバの動作を確認する。
set -e
cd "$(dirname "$0")"
CLI=../bada_gui_ide/cli/bada-cli.js

out=$(node "$CLI" run zeta_shannon.bada)
echo "$out" | sed -n '1,20p'
echo "$out" | grep -q "certified 13 / 13  ALL PASS" || { echo "FAIL: certification"; exit 1; }
echo "$out" | grep -q "標識 無知" || { echo "FAIL: honest ignorance"; exit 1; }
echo "$out" | grep -q "標識 学習" || { echo "FAIL: learning"; exit 1; }

chat=$(printf 'リーマン予想は証明されましたか\n/learn テスト用の事実として、青い鯨は第九十九巻に登場する。\n青い鯨はどこに登場しますか\n今日の夕食は何がいいですか\n/zeta 0.5 14.134725\n' | node chat.js)
echo "$chat" | grep -q "リーマン予想は未解決である" || { echo "FAIL: chat grounded answer"; exit 1; }
echo "$chat" | grep -q "青い鯨は第九十九巻に登場する" || { echo "FAIL: chat learning"; exit 1; }
echo "$chat" | grep -q "わかりません" || { echo "FAIL: chat ignorance"; exit 1; }
echo "$chat" | grep -q "|zeta_NS| = 0.0000" || { echo "FAIL: chat zeta"; exit 1; }
echo "chat driver: OK"
echo "ALL TESTS PASS"
