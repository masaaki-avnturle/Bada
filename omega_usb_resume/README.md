# Ω-USB Resume — 死んだUSBポートを Bada 言語で蘇生する

PC の USB コネクターが

- **許可なく**（カーネルが `authorized = 0` で拒否している）
- **プラグプレイ機能なく**（ドライバが再バインドされずホットプラグが発火しない）
- **接触不良**（チャタリングで制御転送の記述子バイトが化ける）

で使えなくなった状態を、**物理的な修理なしに** ソフト側から復旧（レジューム）する
アプリケーションです。**Bada 言語**で記述し、Bada フレームワークの
**複素回転体・特殊相対性理論のコマ幾何・可積分系**エラー訂正
（`Bada::ErrorCorrection`）をそのまま使います。

```
接触不良 = 機械語バイト列の "n進数のズレ"
     │  複素回転体 e^{iθ} の閉軌道で平均（可積分系のコマ幾何 → 大きさ保存）
     ▼
n進数のズレを訂正 → エントロピー不変量 Ξ が保存（= 復旧が正しい証明）
     │  authorize(0→1) → power/control=on → unbind→bind（プラグプレイ再列挙）
     ▼
デバイス RESUMED
```

---

## ⚠ 重要 — シミュレーション既定・非破壊

- 既定では**すべてシミュレーション**です（`/sys` には一切書き込みません）。
  CI・コンテナ・Mac/Windows でもそのまま動きます。
- Linux 実機で root 権限がある場合のみ `--apply` を付けると、選択した
  デバイスの実 sysfs（`authorized` / `power/control` / ドライバの
  `unbind`・`bind`）に同じ手順を書き込みます。**書けない場合は警告して
  シミュレーションに留まり、壊しません。**
- 記述子バイトの `n進数のズレ` はドライバの制御転送リトライを数理化した
  ものです。実際に効くのは「再認可・電源復帰・再列挙」であり、断線した
  ケーブルやもげた端子など**真の物理故障は直せません**（その場合は正直に
  `NOT resumed ⚠` を返します）。

---

## 使い方

Bada/Ruby ランタイム（外部依存なし・Ruby 3.0+）から動きます。

```bash
# アプリのラッパー（このフォルダ）
./usb_resume            # スキャン＋不良ポートを全部レジューム（simulation）
./usb_resume scan       # USB デバイス一覧だけ
./usb_resume --apply    # Linux/root で実 sysfs に反映
./usb_resume --base 8   # ズレを 8 進数でモデル化（既定 16）
./usb_resume --device 2-3   # 指定 id のデバイスだけ

# Bada 言語スクリプトとして（演算子代数で記述したもの）
cd ../bada_ruby
bin/bada run examples/usb_resume.bada
bin/bada usb            # 同じ復旧を実エンジンで実行
```

出力例（不良ポート `2-3`）:

```
── USB Mass Storage (faulted port)  (0x0781:0x5581  bus 2  id 2-3)
   ✓ measure          port state = UNAUTHORIZED
   ✓ n進数補正         base-16 digit drift: 10→0 bit errors, 18/18 bytes recovered in 17 reads, checksum OK
   ✓ 可積分認証         Ξ=0.948928 conserved=true residual=0.00e+00
   ✓ authorize        simulated
   ✓ power/control=on simulated
   ✓ rebind (plug&play) simulated
   ✓ verify           port state = RESUMED
   → RESUMED ✅  (UNAUTHORIZED → RESUMED)   [simulation]
```

---

## 中身

| ファイル | 役割 |
|:--|:--|
| `../bada_ruby/lib/bada/usb_resume.rb` | 中核エンジン `Bada::UsbResume`：デバイス列挙 / n進数ズレ模型・訂正 / 復旧ステートマシン |
| `../bada_ruby/examples/usb_resume.bada` | **Bada 言語**による記述（`<- / -< / >- / Ω::push`） |
| `../bada_ruby/bin/bada usb` | CLI サブコマンド |
| `../bada_ruby/test/test_usb_resume.rb` | テスト（8 件） |
| `./usb_resume` | このフォルダから直接動かすラッパー |

### 復旧アルゴリズム（`Bada::UsbResume`）

1. **測定** — ポート状態（`UNAUTHORIZED` / `UNBOUND` / `SUSPENDED`）を読む。
2. **n進数補正** — 接触不良で化けた記述子を、同じ記述子の複数読み取り（制御転送
   リトライ）として扱い、各読み取りを複素回転体 `e^{iθ}` 上のサンプルとみなす。
   `ErrorCorrection.correct`（相対論的な外れ値減衰＝コマの歳差）で閉軌道平均を
   取り真値を復元。base-n チェックサムが通るまでリトライ数を自動増加。
3. **可積分認証** — 復元後のエントロピー不変量 Ξ が回転軌道上で保存されることを
   `certify_invariant` で確認（可積分系の保存則＝復旧の証明）。
4. **レジューム** — `authorized`→1、`power/control`→on、ドライバ `unbind`→`bind`
   でプラグプレイ再列挙。
5. **記録** — 対話を `Ω::DATABASE`（アカシックレコード）へ push。

---

*© 2025 Masaaki Yamaguchi · 山口 雅旭 · Bada / TupleSpace framework*
